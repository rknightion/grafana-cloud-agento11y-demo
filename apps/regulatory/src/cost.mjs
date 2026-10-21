// Estimate only, never a billing ledger. Verified 2026-10-21 against AWS's public price list:
// https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonBedrockFoundationModels/current/eu-west-1/index.json
// Publication 2026-10-12T08:40:08Z, feature On-demand Inference, usage types
// EU-MP:EU_InputTokenCount-Units / EU-MP:EU_OutputTokenCount-Units, USD / 1M tokens:
// Claude Haiku 4.5 1.10 / 5.50; Claude Sonnet 4.6 3.30 / 16.50.
// AWS documents geographic cross-region pricing as based on the invoking region:
// https://docs.aws.amazon.com/bedrock/latest/userguide/cross-region-inference.html
// Scope: standard uncached text Converse requests invoked in eu-west-1 through application
// profiles copied from these exact EU geographic profiles. Runtime currently sets no cachePoint
// or serviceTier. Global profiles, other regions/models, cache usage and synthetic STUB_MODEL
// tokens are NOT silently charged at these rates. Re-verify before extending this table.
const PRICES = new Map([
  ['eu.anthropic.claude-haiku-4-5-20251001-v1:0', { input: 1.10, output: 5.50 }],
  ['eu.anthropic.claude-sonnet-4-6', { input: 3.30, output: 16.50 }],
]);
export function estimatedGenerationCost({ modelName, region, usage }) {
  const price = region === 'eu-west-1' ? PRICES.get(modelName) : undefined;
  if (!price || !Number.isSafeInteger(usage?.inputTokens) || usage.inputTokens < 0 || !Number.isSafeInteger(usage?.outputTokens) || usage.outputTokens < 0) return undefined;
  // These counters are not currently produced by the runtime, but reject unexpected caching
  // rather than treating discounted reads or premium cache writes as ordinary input tokens.
  for (const key of ['cacheReadInputTokens', 'cacheWriteInputTokens', 'cacheReadInputTokenCount', 'cacheWriteInputTokenCount']) if (usage[key] !== undefined && usage[key] !== 0) return undefined;
  return (usage.inputTokens * price.input + usage.outputTokens * price.output) / 1_000_000;
}
export function createCostRecorder(meter, env, role) {
  // No unit suffix: the frozen Prometheus names already include usd and total.
  const cost = meter.createCounter('regulatory_estimated_cost_usd_total', { description: 'Estimated standard uncached Bedrock generation cost in USD; not billed spend' });
  const unpriced = meter.createCounter('regulatory_unpriced_generations_total', { description: 'Returned generations without verified model/region/token pricing; estimates are incomplete when nonzero' });
  return (request, modelName, usage) => {
    if (env.STUB_MODEL === '1') return;
    const attributes = { document_type: request.document_type, section: request.section, agent_role: role, model_name: modelName };
    const estimate = estimatedGenerationCost({ modelName, region: env.AWS_REGION, usage });
    if (estimate === undefined) unpriced.add(1, attributes);
    else { cost.add(estimate, attributes); unpriced.add(0, attributes); }
  };
}
