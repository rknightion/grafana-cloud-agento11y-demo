#!/usr/bin/env node
// Dry-run by default. Execution records trials; HTTP success never substitutes for stored scores.
import { readFile } from 'node:fs/promises';
import { randomUUID } from 'node:crypto';
import { pathToFileURL } from 'node:url';
import { createAgento11yClient } from '@grafana/agento11y';
import { ExperimentsClient, Experiment } from '@grafana/agento11y/experiments';
import { get_table, get_section_rules, get_prior_approved_text } from '../src/fixtures.mjs';
import { withScheduledLease } from './lease.mjs';

const suiteNames = ['section-prompts', 'guard-policy'];
const prefix = (env) => (env.SERVICE_NAMESPACE ?? 'dossier').replaceAll('-', '_');

export async function loadSuite(name = 'section-prompts') {
  if (!suiteNames.includes(name)) throw new Error('unknown suite');
  const suite = JSON.parse(await readFile(new URL(`../config/suites/${name}.json`, import.meta.url), 'utf8'));
  if (!suite.cases.length || suite.cases.length > 20 || !suite.variants.length || suite.variants.length > 4) throw new Error('suite exceeds bounded trial budget');
  return suite;
}

export function guardRequest(testCase, env = process.env, conversationId = randomUUID()) {
  return { phase: 'preflight', context: { agentName: `${env.SERVICE_NAMESPACE ?? 'dossier'}-source`, conversationId, model: { provider: 'guard-policy', name: 'no-model-call' } },
    input: { messages: [{ role: 'tool', content: JSON.stringify(testCase.tool_result) }] } };
}

// Validate the actual transformed tool message and its structure, not just an allow decision.
export function guardPassed(testCase, decision, env = process.env) {
  if (!decision || decision.action !== testCase.expected.action) return false;
  if (testCase.expected.failed_rule_suffix && !decision.evaluations?.some((evaluation) =>
    evaluation.ruleId === `${prefix(env)}_${testCase.expected.failed_rule_suffix}` && evaluation.passed === false)) return false;
  if (testCase.expected.rule_suffix && decision.ruleId !== `${prefix(env)}_${testCase.expected.rule_suffix}`) return false;
  if (decision.action === 'deny') return true;
  const messages = decision.transformedInput?.messages;
  if (testCase.expected.absent && (!Array.isArray(messages) || messages.length !== 1 || messages[0].role !== 'tool')) return false;
  const message = messages?.[0];
  const content = message?.content ?? (message?.parts?.every((part) => part.type === 'text') ? message.parts.map((part) => part.text).join('') : undefined) ?? (testCase.expected.absent ? undefined : JSON.stringify(testCase.tool_result));
  if (typeof content !== 'string' || !content.trim()) return false;
  let transformed;
  try { transformed = JSON.parse(content); } catch { return false; }
  if (!transformed || typeof transformed !== 'object' || Array.isArray(transformed)) return false;
  for (const [key, value] of Object.entries(testCase.tool_result)) {
    if (!Object.hasOwn(transformed, key) || typeof value !== typeof transformed[key] ||
      (typeof value === 'string' && value && !transformed[key].trim())) return false;
  }
  return (testCase.expected.absent ?? []).every((value) => !content.includes(value)) &&
    (testCase.expected.retained ?? []).every((value) => content.includes(value));
}

export function hookClient(env) {
  const { AGENTO11Y_ENDPOINT: endpoint, AGENTO11Y_AUTH_TENANT_ID: tenantId, AGENTO11Y_AUTH_TOKEN: token } = env;
  if (!endpoint || !tenantId || !token) throw new Error('guard execution requires explicit Agent Observability endpoint and ingest auth');
  return createAgento11yClient({ generationExport: { protocol: 'http', endpoint, auth: { mode: 'basic', tenantId, basicPassword: token } },
    api: { endpoint: new URL(endpoint).origin }, hooks: { enabled: true, phases: ['preflight'], timeoutMs: 5000, failOpen: false } });
}

export async function storedScore(client, runId, trialId, evaluatorId) {
  let cursor;
  const seen = new Set();
  for (let page = 0; page < 20; page++) {
    const result = await client.listScores(runId, { limit: 100, ...(cursor ? { cursor } : {}) });
    if (!Array.isArray(result.items)) throw new Error('score readback missing items');
    const score = result.items.find((row) => (row.trial_id ?? row.trialId) === trialId &&
      (row.evaluator_id ?? row.evaluatorId) === evaluatorId && (row.score_key ?? row.scoreKey) === 'score');
    if (score) {
      const value = typeof score.value === 'number' ? score.value : score.value?.number;
      if (!Number.isFinite(value) || value < 0 || value > 1) throw new Error('stored evaluator score is invalid');
      return value;
    }
    if (!result.nextCursor) break;
    if (seen.has(result.nextCursor)) throw new Error('score pagination repeated a cursor');
    seen.add(result.nextCursor); cursor = result.nextCursor;
  }
  throw new Error(`evaluation protocol completed but no stored score exists for ${evaluatorId}/${trialId}`);
}

function scoreReader(env, client, fetchImpl) {
  if (!env.AGENTO11Y_GRAFANA_URL || !env.AGENTO11Y_SERVICE_ACCOUNT_TOKEN) return client;
  return { async listScores(runId, { limit, cursor }) {
    const query = new URLSearchParams({ limit: String(limit), ...(cursor ? { cursor } : {}) });
    const response = await fetchImpl(`${env.AGENTO11Y_GRAFANA_URL.replace(/\/$/, '')}/api/plugins/grafana-agento11y-app/resources/eval/experiments/${encodeURIComponent(runId)}/scores?${query}`, {
      headers: { Authorization: `Bearer ${env.AGENTO11Y_SERVICE_ACCOUNT_TOKEN}` }, signal: AbortSignal.timeout(10_000),
    });
    if (!response.ok) throw new Error(`score readback HTTP ${response.status}`);
    const body = await response.json();
    return { items: body.items, nextCursor: body.next_cursor };
  } };
}

export async function executeSuite(suite, { env = process.env, fetchImpl = fetch, client, guards, runId = `regulatory-${randomUUID()}` } = {}) {
  const localStub = env.STUB_MODEL === '1';
  const capture = env.CONTENT_CAPTURE !== 'false';
  if (!localStub && suite.target !== 'guards' && !capture) throw new Error('content-off mode cannot run content-judge experiments; use app operational metrics');
  if (!localStub && (!env.AGENTO11Y_ENDPOINT || !env.AGENTO11Y_AUTH_TENANT_ID || !env.AGENTO11Y_AUTH_TOKEN)) throw new Error('execution requires explicit Agent Observability endpoint and ingest auth');
  const base = new URL(env.ORCHESTRATOR_URL ?? `http://${env.SERVICE_NAMESPACE ?? 'dossier'}-orchestrator:8080`);
  if (!['http:', 'https:'].includes(base.protocol)) throw new Error('orchestrator URL must use HTTP');
  if (localStub && !['127.0.0.1', 'localhost', '[::1]'].includes(base.hostname)) throw new Error('stub execution requires a loopback orchestrator URL');
  if (!base.pathname.endsWith('/v1/agent')) base.pathname = `${base.pathname.replace(/\/$/, '')}/v1/agent`;
  client ??= localStub ? undefined : new ExperimentsClient({ env, timeoutMs: 10_000, retry: { maxRetries: 0 } });
  guards ??= suite.target === 'guards' && !localStub ? hookClient(env) : undefined;
  // Local stub runs validate the app protocol only. Guard policy needs its real hook endpoint.
  const experiment = localStub ? undefined : await Experiment.start(client, {
    experimentId: runId, name: `${prefix(env)}_${suite.name}`, plannedTrialCount: suite.cases.length * suite.variants.length,
    candidate: { agentName: `${env.SERVICE_NAMESPACE ?? 'dossier'}-orchestrator` },
    metadata: { suite: suite.name, content_capture: capture },
  });
  const results = [];
  try {
    for (const variant of suite.variants) for (const testCase of suite.cases) {
      const trial = experiment?.trial(`${testCase.id}-${variant}`);
      await trial?.start();
      try {
        if (suite.target === 'guards') {
          if (!guards) throw new Error('guard-policy requires the real preflight hook endpoint; stub mode cannot prove remote policy');
          const decision = await guards.evaluateHook(guardRequest(testCase, env));
          const passed = guardPassed(testCase, decision, env);
          trial?.finalScore(passed, { passed, evaluator: { evaluatorId: 'expected_preflight_transform', kind: 'deterministic' } });
          await trial?.close();
          results.push({ case: testCase.id, variant, passed, evidence: 'guard_decision_and_transform' });
          if (!passed) throw new Error(`guard case ${testCase.id} failed`);
          continue;
        }
        const conversationId = `${runId}-${testCase.id}-${variant}`;
        const response = await fetchImpl(base, { method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ ...testCase.input, variant, conversation_id: conversationId }), signal: AbortSignal.timeout(180_000) });
        if (!response.ok) throw new Error(`app returned HTTP ${response.status}`);
        const reply = await response.json();
        if (typeof reply.text !== 'string' || !reply.text.trim() || !['approved', 'needs_revision', 'escalated'].includes(reply.review_state) ||
          typeof reply.agent_version !== 'string' || !reply.metrics || !Number.isFinite(reply.metrics.number_grounding)) throw new Error('app returned an invalid or escalated-empty document');
        if (localStub) {
          results.push({ case: testCase.id, variant, evidence: 'local_stub_protocol_only', review_state: reply.review_state });
          continue;
        }
        trial.bindConversation(conversationId);
        trial.recordIO({ input: JSON.stringify({ request: testCase.input, source_evidence: { table: get_table(testCase.input), rules: get_section_rules(testCase.input), prior: get_prior_approved_text(testCase.input) } }), output: reply.text, agentName: `${env.SERVICE_NAMESPACE ?? 'dossier'}-orchestrator`, agentVersion: reply.agent_version });
        const scores = {};
        for (const suffix of suite.evaluators) {
          const evaluatorId = `${prefix(env)}_${suffix}`;
          const evaluation = await trial.evaluate(evaluatorId, { timeoutMs: 30_000 });
          if (evaluation.status !== 'success') throw new Error(`evaluator ${evaluatorId} returned ${evaluation.status}`);
          scores[suffix] = await storedScore(scoreReader(env, client, fetchImpl), runId, trial.trialId, evaluatorId);
        }
        const passed = Object.values(scores).every((score) => score >= 0.8);
        trial.finalScore(Math.min(...Object.values(scores)), { passed, evaluator: { evaluatorId: 'section_quality_minimum', kind: 'deterministic' } });
        await trial.close();
        results.push({ case: testCase.id, variant, passed, scores, evidence: 'stored_content_scores' });
      } catch (error) { await trial?.close({ error }); throw error; }
    }
    await experiment?.finalize('completed');
    return { runId, results, passed: results.every((item) => item.passed !== false), evidence: localStub ? 'local_stub_protocol_only' : 'recorded_trials' };
  } catch (error) { await experiment?.finalize('failed', { error: error.message }); throw error; }
  finally { await client?.shutdown(); await guards?.shutdown?.(); }
}

export async function main(args = process.argv.slice(2), env = process.env) {
  let name = 'section-prompts'; let execute = false; let scheduled = false;
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--suite') name = args[++i];
    else if (args[i] === '--execute') execute = true;
    else if (args[i] === '--scheduled') scheduled = true;
    else throw new Error(`unknown argument ${args[i]}`);
  }
  if (scheduled && !args.includes('--suite')) name = suiteNames[Math.floor(Math.random() * suiteNames.length)];
  const suite = await loadSuite(name);
  if (!execute) return { dry_run: true, scheduled, suite, planned_trials: suite.cases.length * suite.variants.length };
  if (scheduled && env.TRAFFIC_ENABLED !== 'true') return { skipped: true, reason: 'traffic disabled' };
  if (scheduled && suite.scheduled === false) return { skipped: true, reason: 'suite manual only' };
  if (scheduled && env.CONTENT_CAPTURE === 'false' && suite.target !== 'guards') return { skipped: true, reason: 'content-off mode cannot score content judges; app metrics remain available' };
  const run = () => executeSuite(suite, { env });
  return scheduled ? withScheduledLease(run, { name: env.EXPERIMENTS_LEASE_NAME ?? `${env.SERVICE_NAMESPACE ?? 'dossier'}-experiments` }) : run();
}
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().then((result) => { console.log(JSON.stringify(result, null, 2)); if (result.passed === false) process.exitCode = 1; })
    .catch((error) => { console.error(error.message); process.exitCode = 1; });
}
