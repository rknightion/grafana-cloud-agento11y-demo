import test from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { NodeHttpHandler } from '@smithy/node-http-handler';
import { BedrockRuntimeClient } from '@aws-sdk/client-bedrock-runtime';
import { trace } from '@opentelemetry/api';
import { MeterProvider, PeriodicExportingMetricReader, InMemoryMetricExporter, AggregationTemporality } from '@opentelemetry/sdk-metrics';
import { createModel } from '../src/models.mjs';
import { createAgentService } from '../src/service.mjs';
import { createAgento11yClient } from '@grafana/agento11y';
import { localGuard } from '../src/agent-client.mjs';
const request = { document_type: 'csr', study_id: 'XQZ-301', section: 'synopsis', variant: 'grounded' };
test('Bedrock HTTP response preserves truncated usage and service records it before escalating', { timeout: 10000 }, async () => {
  const seen = [], recorded = [], exported = [];
  let response = { output: { message: { role: 'assistant', content: [{ text: '{"review_state":' }] } }, stopReason: 'max_tokens', usage: { inputTokens: 1200, outputTokens: 600, totalTokens: 1800 } };
  const server = createServer(async (req, res) => { let body = ''; for await (const chunk of req) body += chunk; seen.push(JSON.parse(body)); res.setHeader('content-type', 'application/json'); res.end(JSON.stringify(response)); });
  await new Promise((r) => server.listen(0, '127.0.0.1', r));
  const bedrock = new BedrockRuntimeClient({ region: 'eu-west-1', endpoint: `http://127.0.0.1:${server.address().port}`, credentials: { accessKeyId: 'synthetic-access-key', secretAccessKey: 'synthetic-secret' }, maxAttempts: 1, requestHandler: new NodeHttpHandler() });
  const env = { AWS_REGION: 'eu-west-1', MODEL_NAME: 'eu.anthropic.claude-sonnet-4-6', MODEL_PROFILE_ARN: `arn:aws:bedrock:eu-west-1:${'0'.repeat(12)}:application-inference-profile/synthetic` };
  const model = createModel(env, { client: bedrock });
  const exporter = new InMemoryMetricExporter(AggregationTemporality.CUMULATIVE), provider = new MeterProvider({ readers: [new PeriodicExportingMetricReader({ exporter, exportIntervalMillis: 3600000 })] });
  const telemetry = { meter: provider.getMeter('completion-test'), tracer: trace.getTracer('completion-test'), shutdown: async () => {} };
  const sdk = createAgento11yClient({ tracer: telemetry.tracer, meter: telemetry.meter, hooks: { enabled: false }, generationExporter: { async exportGenerations(batch) { exported.push(...batch.generations); return { results: batch.generations.map((g) => ({ generationId: g.id, accepted: true })) }; } } });
  const client = { shutdown: async () => sdk.shutdown(), evaluateHook: async ({ input }) => localGuard(JSON.parse(input.messages[0].content)), startToolExecution: async (_, cb) => cb({ setResult() {} }), startGeneration: async (seed, cb) => sdk.startGeneration(seed, (recorder) => cb({ setResult(value) { recorded.push(value); recorder.setResult(value); } })) };
  const service = createAgentService({ role: 'reviewer', env, model, telemetry, client, log() {} });
  try {
    const output = await model.generate({ role: 'reviewer', request, evidence: {} });
    assert.equal(output.stopReason, 'max_tokens'); assert.deepEqual(output.usage, { inputTokens: 1200, outputTokens: 600, totalTokens: 1800 });
    const result = await service.run({ ...request, draft: 'Fictional findings.' }); assert.equal(result.review_state, 'escalated'); assert.equal(result.text, ''); assert.equal(result.usage[0].outputTokens, 600);
    assert.equal(recorded[0].stopReason, 'max_tokens'); assert.equal(recorded[0].usage.inputTokens, 1200); assert.equal(recorded[0].usage.outputTokens, 600);
    await provider.forceFlush(); const metrics = exporter.getMetrics().at(-1).scopeMetrics.flatMap((s) => s.metrics); assert.ok(Math.abs(metrics.find((m) => m.descriptor.name === 'regulatory_estimated_cost_usd_total').dataPoints[0].value - 0.01386) < 1e-12);
    response = { output: { message: { role: 'assistant', content: [{ text: '{"review_state":"approved"}' }] } }, stopReason: 'end_turn' };
    const unknown = await service.run({ ...request, draft: 'Fictional findings.' }); assert.equal(unknown.review_state, 'escalated'); assert.equal(recorded[1].usage, undefined);
    await provider.forceFlush(); assert.equal(exporter.getMetrics().at(-1).scopeMetrics.flatMap((s) => s.metrics).find((m) => m.descriptor.name === 'regulatory_unpriced_generations_total').dataPoints[0].value, 1);
    await sdk.flush(); assert.equal(exported.length, 2); assert.equal(exported[0].stopReason, 'max_tokens'); assert.equal(exported[0].usage.outputTokens, 600); assert.equal(exported[1].usage, undefined);
  } finally { await service.shutdown(); await provider.shutdown(); server.closeAllConnections(); await new Promise((r) => server.close(r)); }
});
