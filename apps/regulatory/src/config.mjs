// Runtime-only configuration; no deployment endpoints or credentials are embedded here.
export const ROLES = ['orchestrator', 'source', 'drafter', 'reviewer', 'readability'];
const TEAMS = { orchestrator: 'medical-writing', source: 'clinical-science', drafter: 'medical-writing', reviewer: 'regulatory-affairs', readability: 'medical-writing' };
export function boolEnv(value, fallback) {
  if (value === undefined || value === '') return fallback;
  const normal = String(value).trim().toLowerCase();
  if (['1', 'true', 'yes', 'on'].includes(normal)) return true;
  if (['0', 'false', 'no', 'off'].includes(normal)) return false;
  throw new Error('Invalid boolean configuration');
}
export function serviceNamespace(env = process.env) { return (env.SERVICE_NAMESPACE || 'dossier').trim(); }
export function agentName(role, env = process.env) { return `${serviceNamespace(env)}-${role}`; }
export function selfAgentName(role, env = process.env) { return (env.OTEL_SERVICE_NAME || agentName(role, env)).trim(); }
export function agentTeam(role, env = process.env) { return (env.AGENT_TEAM || TEAMS[role]).trim(); }
export function agentVersion(env = process.env) { return (env.AGENT_VERSION || 'v2').trim(); }
export function captureMode(env = process.env) {
  // The regulatory switch is authoritative: an inherited SDK override cannot re-enable content.
  if (!boolEnv(env.CONTENT_CAPTURE, true)) return 'metadata_only';
  const mode = env.AGENTO11Y_CONTENT_CAPTURE_MODE?.trim().toLowerCase();
  if (!mode) return 'full';
  if (mode === 'none') return 'metadata_only';
  if (!['default', 'full', 'no_tool_content', 'metadata_only', 'full_with_metadata_spans'].includes(mode)) throw new Error('Invalid content capture mode');
  return mode;
}
export function specialistUrl(role, env = process.env) {
  return (env.SPECIALIST_URL_TEMPLATE || 'http://{name}:8080/v1/agent').replaceAll('{name}', agentName(role, env)).replaceAll('{role}', role);
}
export function validateProfileArn(arn) {
  if (!/^arn:aws[a-z-]*:bedrock:[a-z0-9-]+:\d{12}:application-inference-profile\/[a-z0-9]+$/.test(arn ?? '')) throw new Error('MODEL_PROFILE_ARN must be a Bedrock application inference profile ARN');
  return arn;
}
export function modelConfig(env = process.env) {
  const defaultKey = env.MODEL_KEY || 'default';
  return { defaultKey, profiles: { [defaultKey]: { arn: env.MODEL_PROFILE_ARN || '', name: env.MODEL_NAME || defaultKey } } };
}
