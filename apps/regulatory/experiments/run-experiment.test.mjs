import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { ExperimentsClient } from '@grafana/agento11y/experiments';
import { loadSuite, main, guardRequest, guardPassed, hookClient, executeSuite, storedScore } from './run-experiment.mjs';

test('CLI is dry-run by default and refuses unknown suites and arguments', async () => {
  const result = await main(['--suite', 'guard-policy']);
  assert.equal(result.dry_run, true);
  assert.equal(result.planned_trials, 3);
  await assert.rejects(main(['--suite', '../secret']), /unknown suite/);
  await assert.rejects(main(['--paid']), /unknown argument/);
  assert.deepEqual(await main(['--scheduled', '--execute'], {}), { skipped: true, reason: 'traffic disabled' });
});

test('preflight tool-result transform must remove identifiers and retain clinical evidence', async () => {
  const suite = await loadSuite('guard-policy');
  const probe = suite.cases[0];
  const request = guardRequest(probe, { SERVICE_NAMESPACE: 'trial-demo' });
  assert.equal(request.phase, 'preflight');
  assert.equal(request.input.messages[0].role, 'tool');
  assert.equal(request.context.agentName, 'trial-demo-source');
  assert.equal(guardPassed(probe, { action: 'allow' }), false);
  assert.equal(guardPassed(probe, { action: 'allow', transformedInput: request.input }), false);
  const content = JSON.stringify({ subject: '[REDACTED]', investigator: '[REDACTED]', study: 'XQZ-301', enrolled: 240 });
  assert.equal(guardPassed(probe, { action: 'allow', transformedInput: { messages: [{ role: 'tool', content }] } }), true);
  assert.equal(guardPassed(probe, { action: 'allow', transformedInput: { messages: [{ role: 'tool', content: '{}' }] } }), false);
  assert.equal(guardPassed(suite.cases[1], { action: 'allow', evaluations: [{ ruleId: 'other_rule', passed: false }] }), false);
  assert.equal(guardPassed(suite.cases[1], { action: 'allow', evaluations: [{ ruleId: 'dossier_source_note_injection', passed: false }] }), true);
});

test('score readback requires an actual stored numeric evaluator result', async () => {
  let items = [];
  const client = new ExperimentsClient({ endpoint: 'http://127.0.0.1:1', tenantId: 'test', ingestToken: 'test', env: { AGENTO11Y_ENABLE_EXPERIMENTAL_FEATURES: 'true' },
    fetchImpl: async () => new Response(JSON.stringify({ items }), { status: 200 }), retry: { maxRetries: 0 } });
  await assert.rejects(storedScore(client, 'run', 'trial', 'dossier_number_grounding'), /no stored score/);
  items = [{ trial_id: 'trial', evaluator_id: 'dossier_number_grounding', score_key: 'score', value: { number: 0.9 } }];
  assert.equal(await storedScore(client, 'run', 'trial', 'dossier_number_grounding'), 0.9);
  await client.shutdown();
});

test('real SDK sends tool results preflight and fails closed on hook transport failure', async (t) => {
  let received; let fail = true;
  const server = createServer(async (req, res) => {
    const chunks = [];
    for await (const chunk of req) chunks.push(chunk);
    received = JSON.parse(Buffer.concat(chunks));
    if (fail) { res.writeHead(503, { 'Content-Type': 'application/json' }); res.end('{}'); }
    else { res.writeHead(200, { 'Content-Type': 'application/json' }); res.end(JSON.stringify({ action: 'allow', transformed_input: { messages: [{ role: 'tool', parts: [{ type: 'text', text: JSON.stringify({ subject: '[REDACTED]', investigator: '[REDACTED]', study: 'XQZ-301', enrolled: 240 }) }] }] } })); }
  });
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  t.after(() => server.close());
  const endpoint = `http://127.0.0.1:${server.address().port}`;
  const client = hookClient({ AGENTO11Y_ENDPOINT: endpoint, AGENTO11Y_AUTH_TENANT_ID: 'test', AGENTO11Y_AUTH_TOKEN: 'test' });
  t.after(() => client.shutdown());
  const suite = await loadSuite('guard-policy');
  await assert.rejects(client.evaluateHook(guardRequest(suite.cases[0])));
  assert.equal(received.phase, 'preflight');
  assert.ok(JSON.stringify(received).includes('SUBJECT-XQZ-301-001'));
  fail = false;
  assert.equal(guardPassed(suite.cases[0], await client.evaluateHook(guardRequest(suite.cases[0]))), true);
});

test('stub execution crosses app HTTP boundary, sends both prompt variants, and never claims scoring', async (t) => {
  const inputs = [];
  const server = createServer(async (req, res) => {
    assert.equal(req.url, '/v1/agent');
    const chunks = []; for await (const chunk of req) chunks.push(chunk);
    inputs.push(JSON.parse(Buffer.concat(chunks)));
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ text: 'Synthetic section.', review_state: 'approved', agent_version: 'v1', metrics: { number_grounding: 1 } }));
  });
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  t.after(() => server.close());
  const result = await executeSuite(await loadSuite(), { env: { STUB_MODEL: '1', ORCHESTRATOR_URL: `http://127.0.0.1:${server.address().port}` } });
  assert.equal(result.results.length, 4);
  assert.deepEqual(new Set(inputs.map((input) => input.variant)), new Set(['grounded', 'concise']));
  assert.equal(result.evidence, 'local_stub_protocol_only');
  assert.ok(result.results.every((item) => !Object.hasOwn(item, 'scores')));
  await assert.rejects(executeSuite(await loadSuite(), { env: { CONTENT_CAPTURE: 'false' } }), /content-off/);
});

test('section suite runs the actual stub app and all specialists over HTTP', async (t) => {
  const { createAgentService, createAgentHttpServer } = await import('../src/service.mjs');
  const env = { STUB_MODEL: '1', SERVICE_NAMESPACE: 'dossier', CONTENT_CAPTURE: 'false' };
  const addresses = new Map(); const resources = [];
  t.after(async () => { for (const { server, service } of resources) { server.closeAllConnections(); await new Promise((resolve) => server.close(resolve)); await service.shutdown(); } });
  for (const role of ['source', 'drafter', 'reviewer', 'readability', 'orchestrator']) {
    const service = createAgentService({ role, env, log: () => {}, fetchImpl: (url, options) => {
      const target = addresses.get(new URL(url).hostname);
      if (!target) throw new Error('unexpected specialist');
      return fetch(`${target}/v1/agent`, options);
    } });
    const server = createAgentHttpServer(service);
    await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
    resources.push({ service, server });
    addresses.set(`dossier-${role}`, `http://127.0.0.1:${server.address().port}`);
  }
  const result = await executeSuite(await loadSuite(), { env: { ...env, ORCHESTRATOR_URL: addresses.get('dossier-orchestrator') } });
  assert.equal(result.results.length, 4);
  assert.ok(result.results.every((item) => ['approved', 'needs_revision'].includes(item.review_state)));
  assert.equal(result.evidence, 'local_stub_protocol_only');
});

test('warn-first source-note probe requires an actual failed matching evaluation', async () => {
  const suite = await loadSuite('guard-policy');
  const probe = suite.cases.find((item) => item.id === 'detect-source-note');
  assert.equal(guardPassed(probe, { action: 'allow', evaluations: [] }), false);
  assert.equal(guardPassed(probe, { action: 'allow', evaluations: [{ ruleId: 'other_source_note_injection', passed: false }] }), false);
  assert.equal(guardPassed(probe, { action: 'allow', evaluations: [{ ruleId: 'dossier_source_note_injection', passed: true }] }), false);
  assert.equal(guardPassed(probe, { action: 'allow', evaluations: [{ ruleId: 'dossier_source_note_injection', passed: false }] }), true);
});
