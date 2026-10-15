// Paid provider process edge for the real pinned CLI boundary test.
import { AssistantMessageEventStream } from '@earendil-works/pi-ai';

export default function (pi) {
  pi.registerProvider('fixture', {
    baseUrl: 'http://127.0.0.1/unused-fixture-provider',
    api: 'fixture-api',
    apiKey: 'fixture',
    models: [{ id: 'profile-route', name: 'Claude fixture', reasoning: false, input: ['text'],
      cost: { input: 1, output: 5, cacheRead: 0.1, cacheWrite: 1.25 }, contextWindow: 200000, maxTokens: 1000 }],
    streamSimple(model) {
      const stream = new AssistantMessageEventStream();
      const message = { role: 'assistant', api: 'fixture-api', provider: 'fixture', model: model.id,
        content: [{ type: 'text', text: 'hello\u2028world' }], stopReason: 'stop', timestamp: Date.now(),
        usage: { input: 10000, output: 3000, cacheRead: 0, cacheWrite: 0, totalTokens: 13000,
          cost: { input: 0.01, output: 0.015, cacheRead: 0, cacheWrite: 0, total: 0.025 } } };
      queueMicrotask(() => {
        stream.push({ type: 'done', reason: 'stop', message });
        stream.end();
      });
      return stream;
    },
  });
}
