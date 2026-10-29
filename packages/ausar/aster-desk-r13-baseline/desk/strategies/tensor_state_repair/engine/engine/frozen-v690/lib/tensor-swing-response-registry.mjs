export const TENSOR_SWING_RESPONSE_REGISTRY_VERSION = "tensor-swing-response-registry/0.1.0-shadow";

/**
 * This registry is research metadata only. It is never an alert eligibility
 * gate: live swing alerts are enabled for every symbol that is actually on a
 * user's watchlist. Historical tiers remain useful context in the chart and
 * audit output without restricting the product.
 */
const PRIOR_ONLY_SYMBOLS = [
  "AAOI", "AG", "ARM", "CDE", "CENX", "CIEN", "CLS", "CORZ", "CRML",
  "DGXX", "DPRO", "FTRE", "HUT", "IONQ", "IREN", "MU", "SGML", "SILJ",
  "SCCO", "TSSI", "TMQ", "TSEM", "TWST", "URG", "WULF",
];

export const PRIOR_ONLY_TENSOR_SWING_REGISTRY = Object.freeze(
  Object.fromEntries(PRIOR_ONLY_SYMBOLS.map(symbol => [symbol, {
    tier: "CANDIDATE",
    status: "shadow",
    source: "train-validation-only",
  }])),
);

export function resolveTensorSwingResponse(symbol, registry = PRIOR_ONLY_TENSOR_SWING_REGISTRY) {
  const key = String(symbol || "").trim().toUpperCase();
  if (!key) return { tier: "UNRANKED", status: "unranked", symbol: key };
  const row = registry instanceof Map ? registry.get(key) : registry?.[key];
  return row
    ? { symbol: key, ...row }
    : { symbol: key, tier: "UNRANKED", status: "unranked" };
}
