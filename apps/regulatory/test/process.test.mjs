import test from 'node:test';
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { createServer } from 'node:http';
import { setTimeout as delay } from 'node:timers/promises';
async function port() { const s = createServer(); await new Promise((r) => s.listen(0, '127.0.0.1', r)); const p = s.address().port; await new Promise((r) => s.close(r)); return p; }
test('production preload starts five child roles, carries traces and stops cleanly', { timeout: 25000 }, async () => {
  const children = [], ports = {}, logs = [];
  try {
    for (const role of ['source', 'drafter', 'reviewer', 'readability', 'orchestrator']) ports[role] = await port();
    // URL pathname carries the role into the local routing proxy, retaining the real HTTP calls.
    const proxy = createServer(async (req, res) => { try { const chunks = []; for await (const c of req) chunks.push(c); const upstream = await fetch(`http://127.0.0.1:${ports[req.url.split("/").at(-1)]}/v1/agent`, { method: 'POST', headers: req.headers, body: Buffer.concat(chunks), signal: AbortSignal.timeout(10000) }); res.writeHead(upstream.status); res.end(await upstream.text()); } catch { res.writeHead(502); res.end('{}'); } });
    await new Promise((r) => proxy.listen(0, '127.0.0.1', r));
    try {
      for (const role of Object.keys(ports)) {
        const child = spawn(process.execPath, ['--experimental-loader=@opentelemetry/instrumentation/hook.mjs', '--import', './src/instrumentation.mjs', 'src/server.mjs'], { cwd: new URL('..', import.meta.url), env: { ...process.env, AGENT_ROLE: role, STUB_MODEL: '1', PORT: String(ports[role]), SPECIALIST_URL_TEMPLATE: `http://127.0.0.1:${proxy.address().port}/v1/agent/{role}`, OTEL_EXPORTER_OTLP_ENDPOINT: 'http://127.0.0.1:1', OTEL_METRIC_EXPORT_INTERVAL: '3600000', OTEL_EXPORTER_OTLP_TIMEOUT: '1000' }, stdio: ['ignore', 'pipe', 'pipe'] });
        child.stdout.on('data', (chunk) => logs.push(String(chunk))); child.stderr.resume(); children.push(child);
      }
      for (const [role, p] of Object.entries(ports)) { let healthy = false; for (let i = 0; i < 80; i++) { try { healthy = (await fetch(`http://127.0.0.1:${p}/healthz`)).ok; } catch {} if (healthy) break; await delay(50); } assert.ok(healthy, `${role} started`); }
      const response = await fetch(`http://127.0.0.1:${ports.orchestrator}/v1/agent`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ document_type: 'icf', study_id: 'XQZ-204', section: 'purpose' }), signal: AbortSignal.timeout(10000) });
      const result = await response.json(); assert.notEqual(result.review_state, 'escalated'); assert.ok(Number.isFinite(result.metrics.reading_grade));
      const entries = logs.join('').trim().split('\n').map((line) => JSON.parse(line)); const requests = entries.filter((e) => e.event === 'regulatory_request'); assert.equal(requests.length, 5); assert.equal(new Set(requests.map((e) => e.trace_id)).size, 1);
    } finally { proxy.closeAllConnections(); await new Promise((r) => proxy.close(r)); }
  } finally { await Promise.all(children.map((child) => new Promise((resolve, reject) => { const timer = setTimeout(() => { child.kill('SIGKILL'); reject(new Error('Shutdown timed out')); }, 8000); child.once('exit', (code) => { clearTimeout(timer); if (code === 0) resolve(); else reject(new Error(`Child exit ${code}`)); }); child.kill('SIGTERM'); }))); }
});
