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
