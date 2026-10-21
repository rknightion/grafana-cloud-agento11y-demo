import test from 'node:test';
import assert from 'node:assert/strict';
import { createAgentService, createAgentHttpServer } from '../src/service.mjs';
import { localGuard } from '../src/agent-client.mjs';
import { MeterProvider, PeriodicExportingMetricReader, InMemoryMetricExporter, AggregationTemporality } from '@opentelemetry/sdk-metrics';
import { trace } from '@opentelemetry/api';
const client = { shutdown: async () => {}, startToolExecution: async (_, cb) => cb({ setResult() {} }), startGeneration: async (_, cb) => cb({ setResult() {} }), evaluateHook: async ({ input }) => localGuard(JSON.parse(input.messages[0].content)) };
test('HTTP pipeline exports actual per-generation cost by document/section without aggregate double counting', { timeout: 10000 }, async () => {
  const exporter = new InMemoryMetricExporter(AggregationTemporality.CUMULATIVE);
  const provider = new MeterProvider({ readers: [new PeriodicExportingMetricReader({ exporter, exportIntervalMillis: 3600000 })] });
  const telemetry = { meter: provider.getMeter('regulatory-cost-test'), tracer: trace.getTracer('cost-test'), shutdown: async () => {} };
  const urls = {}, servers = [], services = [];
  const profile = 'eu.anthropic.claude-sonnet-4-6';
  try {
    for (const role of ['source', 'drafter', 'reviewer', 'readability', 'orchestrator']) {
      const service = createAgentService({ role, env: { AWS_REGION: 'eu-west-1', MODEL_NAME: profile, CONTENT_CAPTURE: 'false' }, client, telemetry, log() {}, model: { shutdown() {}, async generate() { return { text: role === 'reviewer' ? '{"review_state":"approved"}' : 'This is fictional. You can leave.', usage: { inputTokens: 1000, outputTokens: 200 } }; } }, fetchImpl: async (url, options) => fetch(urls[/dossier-([^:]+)/.exec(String(url))[1]], options) });
      const server = createAgentHttpServer(service); await new Promise((r) => server.listen(0, '127.0.0.1', r)); urls[role] = `http://127.0.0.1:${server.address().port}/v1/agent`; services.push(service); servers.push(server);
    }
    async function send(payload, url = urls.orchestrator) { const response = await fetch(url, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(payload) }); assert.equal(response.status, 200); return response.json(); }
    assert.equal((await send({ document_type: 'csr', study_id: 'XQZ-301', section: 'synopsis' })).review_state, 'approved');
    assert.equal((await send({ document_type: 'icf', study_id: 'XQZ-204', section: 'purpose' })).review_state, 'approved');
    await provider.forceFlush();
    const metrics = exporter.getMetrics().at(-1).scopeMetrics.flatMap((scope) => scope.metrics);
    const cost = metrics.find((metric) => metric.descriptor.name === 'regulatory_estimated_cost_usd_total'); assert.ok(cost, 'Cost metric exported');
    const unpriced = metrics.find((metric) => metric.descriptor.name === 'regulatory_unpriced_generations_total');
    assert.equal(cost.dataPoints.length, 5); assert.deepEqual(cost.dataPoints.filter((p) => p.attributes.document_type === 'csr').map((p) => p.attributes.agent_role).sort(), ['drafter', 'reviewer']);
    assert.deepEqual(cost.dataPoints.filter((p) => p.attributes.document_type === 'icf').map((p) => p.attributes.agent_role).sort(), ['drafter', 'readability', 'reviewer']);
    for (const point of cost.dataPoints) { assert.ok(Math.abs(point.value - 0.0066) < 1e-12); assert.equal(point.attributes.model_name, profile); assert.ok(['synopsis', 'purpose'].includes(point.attributes.section)); assert.deepEqual(Object.keys(point.attributes).sort(), ['agent_role', 'document_type', 'model_name', 'section']); }
    assert.ok(unpriced.dataPoints.every((point) => point.value === 0));
    // The model is a process configuration value, never an unbounded request attribute.
    const unknown = createAgentService({ role: 'drafter', env: { AWS_REGION: 'eu-west-1', MODEL_NAME: 'unpriced-model' }, client, telemetry, log() {}, model: { shutdown() {}, async generate() { return { text: 'Fictional.', usage: { inputTokens: 500, outputTokens: 100 } }; } } }); services.push(unknown);
    await unknown.run({ document_type: 'csr', study_id: 'XQZ-301', section: 'synopsis' }); await provider.forceFlush();
    const final = exporter.getMetrics().at(-1).scopeMetrics.flatMap((scope) => scope.metrics);
    assert.ok(!final.find((m) => m.descriptor.name === 'regulatory_estimated_cost_usd_total').dataPoints.some((point) => point.attributes.model_name === 'unpriced-model'));
    assert.equal(final.find((m) => m.descriptor.name === 'regulatory_unpriced_generations_total').dataPoints.find((point) => point.attributes.model_name === 'unpriced-model').value, 1);
  } finally { for (const s of servers) { s.closeAllConnections(); await new Promise((r) => s.close(r)); } for (const s of services) await s.shutdown(); await provider.shutdown(); }
});

test('pricing is exact to verified model/region and rejects unsupported usage without recording fake zero spend', async () => {
  const { estimatedGenerationCost, createCostRecorder } = await import('../src/cost.mjs');
  const input = { modelName: 'eu.anthropic.claude-haiku-4-5-20251001-v1:0', region: 'eu-west-1', usage: { inputTokens: 1000000, outputTokens: 1000000 } };
  assert.equal(estimatedGenerationCost(input), 6.6);
  for (const override of [{ region: 'us-east-1' }, { modelName: 'global.anthropic.claude-haiku-4-5-20251001-v1:0' }, { modelName: 'claude-haiku-4-5' }, { usage: { inputTokens: -1, outputTokens: 1 } }, { usage: { inputTokens: 1, outputTokens: NaN } }, { usage: { inputTokens: 1, outputTokens: 1, cacheReadInputTokens: 2 } }, { usage: undefined }]) assert.equal(estimatedGenerationCost({ ...input, ...override }), undefined);
  const exporter = new InMemoryMetricExporter(AggregationTemporality.CUMULATIVE);
  const provider = new MeterProvider({ readers: [new PeriodicExportingMetricReader({ exporter, exportIntervalMillis: 3600000 })] });
  try {
    const record = createCostRecorder(provider.getMeter('stub-cost'), { STUB_MODEL: '1', AWS_REGION: input.region }, 'drafter');
    record({ document_type: 'csr', section: 'synopsis' }, input.modelName, input.usage);
    await provider.forceFlush();
    assert.ok(exporter.getMetrics().every((resource) => resource.scopeMetrics.flatMap((scope) => scope.metrics).length === 0), 'Stub tokens never become real estimated spend or unpriced counts');
  } finally { await provider.shutdown(); }
});
