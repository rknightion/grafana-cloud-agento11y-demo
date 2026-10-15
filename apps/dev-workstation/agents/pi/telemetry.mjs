// Keep routing ARNs in Pi's provider/session; give Grafana canonical model names only.
import { readFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';

export function canonicalObserver(pi, names) {
  const messageView = (message) => message?.role === 'assistant' && names.has(message.model)
    ? { ...message, model: names.get(message.model) } : message;
  return {
    ...pi,
    on(kind, handler) {
      pi.on(kind, (event, ctx) => {
        const view = event.message ? { ...event, message: messageView(event.message) } : event;
        const context = ctx?.model && names.has(ctx.model.id)
          ? { ...ctx, model: { ...ctx.model, id: names.get(ctx.model.id) } } : ctx;
        return handler(view, context);
      });
    },
  };
}

export default async function (pi) {
  const config = JSON.parse(readFileSync(process.env.PI_AGENT_CONFIG_FILE, 'utf8'));
  const names = new Map([[config.model.id, config.model.name]]);
  const budget = Number(process.env.PI_TURN_BUDGET_USD);
  if (!(budget > 0) || !Number.isFinite(budget)) throw new Error('Pi requires a positive turn budget');
  let spent = 0;
  pi.on('message_end', (event, ctx) => {
    if (event.message?.role !== 'assistant') return;
    const cost = event.message.usage?.cost?.total;
    if (!Number.isFinite(cost) || cost < 0) {
      ctx.abort();
      return;
    }
    spent += cost;
    // The current call can exceed this budget; stop additional model/tool rounds.
    // IAM/team spend controls remain the external enforcement boundary.
    if (spent >= budget) ctx.abort();
  });
  const module = pathToFileURL(`${process.env.PI_INSTALL_DIR}/node_modules/@grafana/agento11y-pi/dist/index.js`);
  const { default: official } = await import(module.href);
  await official(canonicalObserver(pi, names));
}
