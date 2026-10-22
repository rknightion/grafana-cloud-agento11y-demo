import test from 'node:test';
import assert from 'node:assert/strict';
import { runLoadgen } from '../src/loadgen.mjs';

test('zero requests per minute sends no authoring requests', async () => {
  let calls = 0;
  const result = await runLoadgen({ env: { REQUESTS_PER_MINUTE: '0', MAX_REQUESTS: '1' }, fetchImpl: async () => { calls++; return new Response('{}'); } });
  assert.equal(calls, 0);
  assert.equal(result.sent, 0);
});

test('deployment traffic continues beyond 100 requests until shutdown', { timeout: 2000 }, async () => {
  const controller = new AbortController(); let calls = 0;
  const result = await runLoadgen({ env: {}, signal: controller.signal, sleepImpl: async () => {}, fetchImpl: async () => { if (++calls === 101) controller.abort(); return new Response('{}'); } });
  assert.equal(calls, 101);
  assert.equal(result.sent, 101);
});

test('each request is sent under its own CLIENT span with a traceparent', async () => {
  const { BasicTracerProvider, InMemorySpanExporter, SimpleSpanProcessor } = await import('@opentelemetry/sdk-trace-base');
  const { W3CTraceContextPropagator } = await import('@opentelemetry/core');
  const { AsyncLocalStorageContextManager } = await import('@opentelemetry/context-async-hooks');
  const { context, propagation, trace, SpanKind } = await import('@opentelemetry/api');
  const exporter = new InMemorySpanExporter();
  context.setGlobalContextManager(new AsyncLocalStorageContextManager().enable());
  propagation.setGlobalPropagator(new W3CTraceContextPropagator());
  trace.setGlobalTracerProvider(new BasicTracerProvider({ spanProcessors: [new SimpleSpanProcessor(exporter)] }));
  const headers = [];
  await runLoadgen({ env: { MAX_REQUESTS: '2' }, sleepImpl: async () => {}, fetchImpl: async (_, options) => { headers.push(options.headers); return new Response('{}'); } });
  const spans = exporter.getFinishedSpans();
  assert.equal(spans.filter((span) => span.kind === SpanKind.CLIENT).length, 2);
  assert.deepEqual(headers.map((h) => h.traceparent?.split('-')[2]), spans.map((span) => span.spanContext().spanId));
});
