import { createAgento11yClient } from '@grafana/agento11y';
import { SOURCE_NOTE_MARKERS } from './loadgen.mjs';
import { captureMode, selfAgentName, agentVersion } from './config.mjs';
export const IDENTIFIERS = /(?:SUBJECT-XQZ-\d{3}-\d{3}|SYNTHETIC-INVESTIGATOR-\d{2})/g;
export const INJECTION_MARKERS = SOURCE_NOTE_MARKERS;
export function localGuard(value) {
  const content = JSON.stringify(value);
  if (INJECTION_MARKERS.some((marker) => content.toLowerCase().includes(marker))) return { action: 'deny' };
  return { action: 'allow', transformedInput: { messages: [{ role: 'tool', content: content.replace(IDENTIFIERS, '[REDACTED]') }] } };
}
export function createAgentClient(role, telemetry, env = process.env) {
  if (env.STUB_MODEL === '1') return { evaluateHook: async ({ input }) => localGuard(JSON.parse(input.messages[0].content)), startGeneration: async (_, cb) => cb({ setResult() {} }), startToolExecution: async (_, cb) => cb({ setResult() {} }), shutdown: async () => {} };
  if (!env.AGENTO11Y_ENDPOINT || !env.AGENTO11Y_AUTH_TENANT_ID || !env.AGENTO11Y_AUTH_TOKEN) throw new Error('Agent Observability credentials required');
  return createAgento11yClient({ generationExport: { protocol: 'http', endpoint: env.AGENTO11Y_ENDPOINT, auth: { mode: 'basic', tenantId: env.AGENTO11Y_AUTH_TENANT_ID, basicPassword: env.AGENTO11Y_AUTH_TOKEN } }, api: { endpoint: new URL(env.AGENTO11Y_ENDPOINT).origin }, contentCapture: captureMode(env), hooks: { enabled: true, phases: ['preflight'], timeoutMs: 5000, failOpen: false }, agentName: selfAgentName(role, env), agentVersion: agentVersion(env), tracer: telemetry.tracer, meter: telemetry.meter });
}
