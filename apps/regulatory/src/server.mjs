const role = process.env.AGENT_ROLE ?? 'orchestrator';
if (role === 'loadgen') {
  const { runLoadgen } = await import('./loadgen.mjs'); const controller = new AbortController();
  process.once('SIGTERM', () => controller.abort()); process.once('SIGINT', () => controller.abort());
  console.log(JSON.stringify({ event: 'loadgen_finished', ...await runLoadgen({ signal: controller.signal }) }));
  const { telemetry } = await import('./telemetry.mjs'); await telemetry()?.shutdown();
} else {
  const { createAgentService, createAgentHttpServer } = await import('./service.mjs');
  const service = createAgentService({ role }), server = createAgentHttpServer(service);
  server.listen(Number(process.env.PORT ?? 8080), '0.0.0.0');
  let stopping = false;
  async function stop() { if (stopping) return; stopping = true; const timeout = setTimeout(() => { server.closeAllConnections(); process.exit(1); }, 10000); timeout.unref(); await new Promise((resolve) => server.close(resolve)); await service.shutdown(); clearTimeout(timeout); }
  process.once('SIGTERM', () => void stop()); process.once('SIGINT', () => void stop());
}
