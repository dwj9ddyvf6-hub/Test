import { buildTensorEnrichmentSignals } from "./tensor-enrichment-signals.mjs";
import { resolveTensorSwingResponse } from "./tensor-swing-response-registry.mjs";
import { buildSwingTransition } from "./tensor-swing-transition.mjs";

export const TENSOR_SWING_SIGNALS_VERSION = "tensor-swing-signals/0.2.0-watchlist-live";

const finite = value => typeof value === "number" && Number.isFinite(value);
const at = (value, fallback = null) => finite(value) ? value : fallback;

function enrichmentIds(bar) {
  return new Set(buildTensorEnrichmentSignals(bar).signals.map(item => item.id));
}

function isBlackSquare(bar) {
  return bar?.barFinality === "closed" && enrichmentIds(bar).has("monitor-buy");
}

function isGreenArrow(bar) {
  const ids = enrichmentIds(bar);
  // On a completed bar, the same enrichment can produce both the black-square
  // setup and green-arrow confirmation. That qualifies immediately at age 0.
  return bar?.barFinality === "closed" && ids.has("consensus-buy");
}

function atrFor(bar) {
  return at(bar?.vectorStructuralLocation?.atr) || Math.max(0, (at(bar?.high, 0) - at(bar?.low, 0))) || Math.max(0, at(bar?.close, 0) * 0.01);
}

function classifyPhenotype(bar, prior) {
  const trigger = String(bar?.vectorStructuralLocation?.trigger || "");
  if (/reclaim|bounce|near-demand|demand-hold/u.test(trigger)) return "REVERSAL";
  if (/breakout|range-breakout|supply-breakout/u.test(trigger)) return "BREAKOUT";
  if (finite(bar?.ema21) && finite(prior?.ema21) && at(prior?.close, 0) <= prior.ema21 && at(bar?.close, 0) > bar.ema21) return "RECLAIM";
  if (bar?.fastState === "bullish" && bar?.slowState !== "bullish") return "RECLAIM";
  return "TRANSITION";
}

function levelContext(bar) {
  const close = at(bar?.close);
  if (!finite(close)) return { target: null, invalidation: null, atr: null };
  const atr = atrFor(bar);
  const demandLow = at(bar?.vectorStructuralLocation?.nearestDemand?.low);
  const supplyLow = at(bar?.vectorStructuralLocation?.nearestSupply?.low);
  const target = finite(supplyLow) && supplyLow > close ? supplyLow : close + atr * 2;
  const invalidation = finite(demandLow) && demandLow < close ? demandLow : at(bar?.low, close - atr);
  return { target, invalidation, atr };
}

function scoreConfirmation(bar, prior) {
  const factors = [];
  const bull = Number(bar?.bullishVotes || 0);
  const bear = Number(bar?.bearishVotes || 0);
  if (isGreenArrow(bar)) factors.push("green consensus");
  if (bar?.fastState === "bullish") factors.push("fast bullish");
  if (bar?.slowState === "bullish") factors.push("slow bullish");
  if (finite(bar?.macdHistogram) && bar.macdHistogram > 0) factors.push("MACD positive");
  if (finite(bar?.plusDi) && finite(bar?.minusDi) && bar.plusDi > bar.minusDi) factors.push("directional participation");
  if (finite(bar?.rvol) && bar.rvol >= 1) factors.push("RVOL active");
  if (finite(bar?.ema21) && bar.close >= bar.ema21) factors.push("above EMA21");
  if (finite(bar?.bbUpper) && bar.close < bar.bbUpper * 0.985) factors.push("room to upper band");
  if (/demand|reclaim|breakout|range/u.test(String(bar?.vectorStructuralLocation?.trigger || ""))) factors.push("structural location");
  if (bull >= bear + 4) factors.push("bullish vote spread");
  if (bar?.tensorContext?.higherTimeframe?.direction === "bullish" || bar?.tensorContext?.higherTimeframe?.alignment === "aligned") factors.push("higher-timeframe alignment");
  const bearishConflict = Boolean(bar?.warningMarker) || bar?.activeCall === "bearish" || bear > bull;
  const score = factors.length;
  const confidence = bearishConflict ? "low" : score >= 8 ? "high" : score >= 6 ? "moderate" : "low";
  return { factors, score, confidence, bearishConflict, prior };
}

function simpleReason({ confirmed, age, phenotype, factors, tier }) {
  if (!confirmed) return "Black-square transition; waiting for green-arrow confirmation.";
  const evidence = factors.slice(0, 4).join(", ");
  const timing = age === 0 ? "on the same bar" : `in ${age} bar${age === 1 ? "" : "s"}`;
  return `Black square → green arrow ${timing}; ${phenotype.toLowerCase()}${evidence ? ` with ${evidence}` : ""}${tier !== "UNRANKED" ? `; ${tier.toLowerCase()} response candidate` : ""}.`;
}

/**
 * Computes the hourly sequence using only bars through `index`.  The function
 * is intentionally independent of React, storage, and notification code so
 * the same result can be used by chart rendering, replay, and watchlist alerts.
 */
export function buildTensorSwingSignal({ bars = [], index = bars.length - 1, symbol = "", registry } = {}) {
  const bar = bars[index];
  if (!bar || bar.barFinality !== "closed") {
    return {
      version: TENSOR_SWING_SIGNALS_VERSION,
      setup: false,
      confirmed: false,
      confirmationAgeBars: null,
      phenotype: "NONE",
      confidence: "low",
      target: null,
      invalidation: null,
      reason: "A completed hourly bar is required.",
      symbolResponseTier: resolveTensorSwingResponse(symbol, registry).tier,
      usesFutureData: false,
      factors: [],
      score: 0,
      setupBarTimestamp: null,
      confirmationBarTimestamp: null,
      transition: buildSwingTransition({ bars, index, symbol, confirmed: false }),
    };
  }
  const setupIndex = Math.max(0, index - 3);
  let blackIndex = null;
  for (let cursor = index; cursor >= setupIndex; cursor -= 1) {
    if (isBlackSquare(bars[cursor])) { blackIndex = cursor; break; }
  }
  const setup = blackIndex !== null;
  const age = setup ? index - blackIndex : null;
  const confirmed = setup && age !== null && isGreenArrow(bar);
  const prior = index > 0 ? bars[index - 1] : null;
  const response = resolveTensorSwingResponse(symbol, registry);
  const scored = confirmed ? scoreConfirmation(bar, prior) : { factors: [], score: 0, confidence: "low", bearishConflict: false };
  const phenotype = confirmed ? classifyPhenotype(bar, prior) : setup ? "PENDING" : "NONE";
  const levels = confirmed ? levelContext(bar) : { target: null, invalidation: null };
  return {
    version: TENSOR_SWING_SIGNALS_VERSION,
    setup,
    confirmed,
    confirmationAgeBars: confirmed ? age : null,
    phenotype,
    confidence: scored.confidence,
    target: levels.target,
    invalidation: levels.invalidation,
    reason: simpleReason({ confirmed, age, phenotype, factors: scored.factors, tier: response.tier }),
    symbolResponseTier: response.tier,
    responseStatus: response.status,
    usesFutureData: false,
    factors: scored.factors,
    score: scored.score,
    bearishConflict: scored.bearishConflict,
    setupBarTimestamp: blackIndex === null ? null : bars[blackIndex].timestamp,
    confirmationBarTimestamp: confirmed ? bar.timestamp : null,
    transition: buildSwingTransition({ bars, index, symbol, confirmed }),
  };
}
