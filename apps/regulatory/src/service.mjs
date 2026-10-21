import { randomUUID } from 'node:crypto';
import { createServer } from 'node:http';
import { context, propagation, trace, SpanStatusCode } from '@opentelemetry/api';
import { ROLES, selfAgentName, agentTeam, agentVersion, captureMode, modelConfig, specialistUrl } from './config.mjs';
import { SECTIONS, STUDY_IDS, get_study, get_table, get_section_rules, get_prior_approved_text, readability_grade, numberGrounding } from './fixtures.mjs';
import { startTelemetry, withTeam } from './telemetry.mjs';
import { createAgentClient, IDENTIFIERS, INJECTION_MARKERS } from './agent-client.mjs';
import { createModel } from './models.mjs';
import { createCostRecorder } from './cost.mjs';
// Models can render an otherwise valid JSON object inside one Markdown code fence.
// Accept only that exact wrapper; explanatory text or malformed JSON still fails closed.
function parseReviewResult(text) {
  const value = text.trim();
  const fenced = /^```(?:json)?[ \t]*\r?\n([\s\S]*?)\r?\n```$/i.exec(value);
  const result = JSON.parse(fenced ? fenced[1] : value);
  if (!result || typeof result !== 'object' || Array.isArray(result)) throw new Error('Reviewer response invalid');
  return result;
}
export class HttpError extends Error { constructor(code, message) { super(message); this.statusCode = code; } }
export function validateRequest(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value) || !SECTIONS[value.document_type]?.includes(value.section) || !STUDY_IDS.includes(value.study_id)) throw new HttpError(400, 'Invalid fictional document, section or study');
  if (value.variant !== undefined && !['grounded', 'concise'].includes(value.variant)) throw new HttpError(400, 'Invalid prompt variant');
  for (const key of ['source_note', 'conversation_id']) if (value[key] !== undefined && (typeof value[key] !== 'string' || value[key].length > (key === 'source_note' ? 1000 : 128))) throw new HttpError(400, `Invalid ${key}`);
  if (value.draft !== undefined && (typeof value.draft !== 'string' || value.draft.length > 16000)) throw new HttpError(400, 'Invalid draft');
  if (value.evidence !== undefined && JSON.stringify(value.evidence).length > 24000) throw new HttpError(400, 'Evidence too large');
  return { ...value, variant: value.variant ?? 'grounded', conversation_id: value.conversation_id ?? randomUUID() };
}
export function createAgentService(options = {}) {
  const env = options.env ?? process.env, role = options.role ?? env.AGENT_ROLE ?? 'orchestrator';
  if (!ROLES.includes(role)) throw new Error('Invalid AGENT_ROLE');
  const telemetry = options.telemetry ?? startTelemetry(role), client = options.client ?? createAgentClient(role, telemetry, env), model = options.model ?? createModel(env);
  const name = selfAgentName(role, env), version = agentVersion(env), team = agentTeam(role, env), capture = captureMode(env);
  const recordCost = createCostRecorder(telemetry.meter, env, role);
  const metric = Object.fromEntries(['requests_total', 'request_duration_seconds', 'number_grounding_ratio', 'reading_grade', 'guard_events_total'].map((key) => [key, key.endsWith('_total') ? telemetry.meter.createCounter(`regulatory_${key}`) : telemetry.meter.createHistogram(`regulatory_${key}`, key.includes('seconds') ? { unit: 's' } : {})]));
  function log(event, fields) { const span = trace.getSpan(context.active())?.spanContext(); (options.log ?? ((entry) => console.log(JSON.stringify(entry))))({ event, trace_id: span?.traceId, span_id: span?.spanId, agent_version: version, ...fields }); }
  async function guard(value, request, toolName = 'specialist_evidence') {
    let safe;
    try {
      const result = await client.evaluateHook({ phase: 'preflight', context: { agentName: name, agentVersion: version, conversationId: request.conversation_id, model: { provider: 'anthropic', name: modelConfig(env).profiles[modelConfig(env).defaultKey].name } }, input: { messages: [{ role: 'tool', content: JSON.stringify(value) }] } });
      if (result?.action !== 'allow') throw new Error('Guard denied');
      const message = result.transformedInput?.messages?.[0];
      const transformed = typeof message?.content === 'string' ? message.content : Array.isArray(message?.parts) && message.parts.every((part) => part.type === 'text' && typeof part.text === 'string') ? message.parts.map((part) => part.text).join('') : undefined;
      if (result.transformedInput && transformed === undefined) throw new Error('Malformed guard transformation');
      safe = transformed === undefined ? JSON.stringify(value) : transformed;
      if (typeof safe !== 'string' || IDENTIFIERS.test(safe) || INJECTION_MARKERS.some((marker) => safe.toLowerCase().includes(marker))) throw new Error('Unsafe guard transformation');
      IDENTIFIERS.lastIndex = 0;
      safe = JSON.parse(safe);
    } catch { IDENTIFIERS.lastIndex = 0; metric.guard_events_total.add(1, { guard: INJECTION_MARKERS.some((marker) => JSON.stringify(value).toLowerCase().includes(marker)) ? 'source_note_injection' : 'patient_identifiers', outcome: 'denied' }); throw new Error('Guard unavailable or unsafe source'); }
    metric.guard_events_total.add(1, { guard: 'patient_identifiers', outcome: 'allowed' });
    await client.startToolExecution({ toolName, toolCallId: randomUUID(), conversationId: request.conversation_id, agentName: name, agentVersion: version, contentCapture: capture }, async (recorder) => { recorder.setResult({ arguments: { study_id: request.study_id, section: request.section }, result: safe }); });
    return safe;
  }
  async function generate(request, evidence, draft) {
    // This guard precedes generation creation too: neither model nor generation messages see raw evidence.
    const safe = await guard({ evidence, ...(draft ? { draft } : {}) }, request);
    const identity = { provider: 'anthropic', name: modelConfig(env).profiles[modelConfig(env).defaultKey].name };
    let output;
    await withTeam(team, () => client.startGeneration({ id: randomUUID(), conversationId: request.conversation_id, conversationTitle: 'Fictional regulatory document', agentName: name, agentVersion: version, model: identity, mode: 'SYNC', operationName: 'generateText', contentCapture: capture, metadata: { team, document_type: request.document_type, section: request.section }, tags: { team, document_type: request.document_type, section: request.section } }, async (recorder) => {
      output = await model.generate({ role, request, evidence: safe.evidence, draft: safe.draft });
      // Count each actual returned generation once, even if later validation/review escalates.
      // Orchestrator usage aggregates are never priced again.
      recordCost(request, identity.name, output.usage);
      const validText = typeof output.text === 'string' && output.text.length > 0 && output.text.length <= 16000;
      const validUsage = Number.isSafeInteger(output.usage?.inputTokens) && output.usage.inputTokens >= 0 && Number.isSafeInteger(output.usage?.outputTokens) && output.usage.outputTokens >= 0;
      recorder.setResult({ input: [{ role: 'user', content: JSON.stringify(safe) }], output: [{ role: 'assistant', content: validText ? output.text : '' }], responseModel: identity.name, usage: output.usage, stopReason: output.stopReason });
      if (!validText || !validUsage || output.stopReason !== 'end_turn') {
        const error = new Error('Incomplete model response');
        error.usage = [{ agent: name, ...output.usage, ...(output.stopReason ? { stopReason: output.stopReason } : {}) }];
        throw error;
      }
    }));
    return output;
  }
  async function specialist(target, request) {
    const headers = { 'content-type': 'application/json' }; propagation.inject(context.active(), headers);
    const response = await (options.fetchImpl ?? fetch)(specialistUrl(target, env), { method: 'POST', headers, body: JSON.stringify(request), signal: AbortSignal.timeout(45000) });
    if (!response.ok) throw new Error('Specialist unavailable');
    const text = await response.text(); if (text.length > 48000) throw new Error('Specialist response too large');
    const result = JSON.parse(text);
    if (result.document_type !== request.document_type || result.study_id !== request.study_id || result.section !== request.section || !['approved', 'needs_revision', 'escalated'].includes(result.review_state)) throw new Error('Invalid specialist response');
    return result;
  }
  async function run(payload) {
    const request = validateRequest(payload), began = performance.now();
    return telemetry.tracer.startActiveSpan(`regulatory.${role}`, async (span) => {
      span.setAttributes({ team, document_type: request.document_type, section: request.section, agent_version: version });
      const result = { request_id: randomUUID(), document_type: request.document_type, study_id: request.study_id, section: request.section, agent_version: version, review_state: 'escalated', text: '', metrics: {}, usage: [] };
      try {
        if (role === 'orchestrator') {
          const source = await specialist('source', request); result.usage.push(...source.usage); if (source.review_state === 'escalated') throw new Error('Source escalated');
          const draft = await specialist('drafter', { ...request, evidence: source.evidence }); result.usage.push(...draft.usage); if (draft.review_state === 'escalated') throw new Error('Draft escalated');
          const reviewed = await specialist('reviewer', { ...request, evidence: source.evidence, draft: draft.text }); result.usage.push(...reviewed.usage);
          const readable = request.document_type === 'icf' ? await specialist('readability', { ...request, evidence: source.evidence, draft: draft.text }) : undefined;
          result.text = draft.text; result.metrics = reviewed.metrics; result.review_state = [reviewed, readable].some((r) => r?.review_state === 'escalated') ? 'escalated' : [reviewed, readable].some((r) => r?.review_state === 'needs_revision') ? 'needs_revision' : 'approved';
          if (readable) result.metrics = { ...result.metrics, ...readable.metrics };
          if (readable) result.usage.push(...readable.usage);
          if (result.review_state === 'escalated') result.text = '';
        } else if (role === 'source') {
          result.evidence = {};
          for (const [key, tool] of Object.entries({ study: get_study, table: get_table, rules: get_section_rules, prior: get_prior_approved_text })) result.evidence[key] = await guard(tool(request), request, ({ study: 'get_study', table: 'get_table', rules: 'get_section_rules', prior: 'get_prior_approved_text' })[key]);
          result.text = 'Fictional evidence retrieved and guarded.'; result.review_state = 'approved';
        } else {
          const evidence = await guard(request.evidence ?? { study: get_study(request), table: get_table(request), rules: get_section_rules(request), prior: get_prior_approved_text(request) }, request);
          const generated = await generate(request, evidence, request.draft);
          result.text = role === 'drafter' ? generated.text : request.draft ?? generated.text;
          result.usage = [{ agent: name, ...generated.usage }];
          result.metrics.number_grounding = numberGrounding(result.text, evidence.table);
          result.review_state = result.metrics.number_grounding < 1 ? 'needs_revision' : 'approved';
          if (role === 'reviewer') { let reviewed; try { reviewed = parseReviewResult(generated.text); } catch { throw new Error('Reviewer response invalid'); } if (!['approved', 'needs_revision', 'escalated'].includes(reviewed.review_state)) throw new Error('Reviewer state invalid'); if (reviewed.review_state !== 'approved') result.review_state = reviewed.review_state; }
          if (request.document_type === 'icf') { result.metrics.reading_grade = readability_grade({ text: result.text }); if (result.metrics.reading_grade > 8 && result.review_state === 'approved') result.review_state = 'needs_revision'; }
        }
      } catch (error) { if (error.usage) result.usage.push(...error.usage); result.text = ''; result.review_state = 'escalated'; delete result.evidence; span.setStatus({ code: SpanStatusCode.ERROR, message: 'Regulatory request escalated' }); }
      finally {
        span.setAttribute('review_state', result.review_state);
        if (role === 'orchestrator') { const attrs = { document_type: request.document_type, section: request.section }; metric.requests_total.add(1, { ...attrs, review_state: result.review_state }); metric.request_duration_seconds.record((performance.now() - began) / 1000, attrs); if (Number.isFinite(result.metrics.number_grounding)) metric.number_grounding_ratio.record(result.metrics.number_grounding, attrs); if (Number.isFinite(result.metrics.reading_grade)) metric.reading_grade.record(result.metrics.reading_grade, attrs); }
        log('regulatory_request', { document_type: request.document_type, section: request.section, review_state: result.review_state, request_id: result.request_id }); span.end();
      }
      return result;
    });
  }
  return { role, run, async shutdown() { model.shutdown(); await client.shutdown(); await telemetry.shutdown(); } };
}
export function createAgentHttpServer(service) {
  const server = createServer(async (req, res) => {
    res.setHeader('content-type', 'application/json');
    if (req.url === '/healthz' && req.method === 'GET') { res.end(JSON.stringify({ ok: true, role: service.role })); return; }
    if (req.url !== '/v1/agent' || req.method !== 'POST') { res.writeHead(404); res.end('{}'); return; }
    try { let body = ''; for await (const chunk of req) { body += chunk; if (Buffer.byteLength(body) > 48000) throw new HttpError(413, 'Request too large'); } let payload; try { payload = JSON.parse(body); } catch { throw new HttpError(400, 'Invalid JSON'); } const result = await context.with(propagation.extract(context.active(), req.headers), () => service.run(payload)); res.end(JSON.stringify(result)); }
    catch (error) { res.writeHead(error.statusCode ?? 500); res.end(JSON.stringify({ error: error.statusCode ? error.message : 'Request failed' })); }
  });
  server.requestTimeout = 120000; server.headersTimeout = 10000; server.maxConnections = 32; return server;
}
