import type { AnnaReplica, AnnaReplicaBar } from "../../lib/anna-replica.mjs";
import { buildTensorEnrichmentSignals } from "../../lib/tensor-enrichment-signals.mjs";

export const TENSOR_PREDICTIVE_GESTALT_VERSION = "tensor-predictive-gestalt/1.0.0";

type Direction = "bullish" | "bearish" | "mixed" | "unresolved";
type Decision = "BUY" | "WAIT" | "AVOID" | "HOLD" | "TRIM" | "SELL";

export type TensorPredictiveGestalt = {
  version: typeof TENSOR_PREDICTIVE_GESTALT_VERSION;
  provenance: "tensorContext";
  authority: "additive-projection";
  finality: "closed";
  usesFutureData: false;
  asOf: number;
  decision: Decision;
  ownerState: "owner" | "non-owner";
  direction: Direction;
  directionLabel: string;
  conviction: "low" | "moderate" | "high";
  magnitude: "quiet" | "normal" | "large" | "extreme";
  horizon: string;
  pattern: string;
  lifecycle: string;
  location: string;
  componentVector: string;
  timeframeAgreement: string;
  timeframeStack: Array<{ interval: string; role: string; direction: string; phase: string; alignment: string }>;
  nextTransition: string;
  expectedMove: { low: number; high: number; basis: string };
  levels: { support: number | null; resistance: number | null; target: number | null; invalidation: number | null };
  scenarios: Array<{ id: "base" | "bull" | "bear"; label: string; trigger: string; outcome: string; level: number | null }>;
  changesRead: string;
  summary: string;
  reasons: string[];
  vetoes: string[];
  enrichmentGlyphs: string[];
};

const finite = (value: unknown): value is number => typeof value === "number" && Number.isFinite(value);

function predictionDirection(value: string): Direction {
  if (value.startsWith("higher")) return "bullish";
  if (value.startsWith("lower")) return "bearish";
  if (value === "crosscurrents") return "mixed";
  return "unresolved";
}

function patternFor(bar: AnnaReplicaBar, direction: Direction) {
  const trigger = bar.vectorStructuralLocation?.trigger;
  const triggerLabels: Record<string, string> = {
    "demand-bounce": "Demand response",
    "demand-hold": "Demand hold",
    "demand-reclaim": "Demand reclaim",
    "supply-breakout": "Supply breakout",
    "supply-rejection": "Supply rejection",
    "supply-loss": "Supply loss",
    "demand-breakdown": "Demand breakdown",
    "range-breakout": "Range expansion",
    "range-breakdown": "Range failure",
    "near-demand": "Support approach",
    "near-supply": "Resistance approach",
  };
  if (trigger && trigger !== "none") return triggerLabels[trigger] || bar.vectorStructuralLocation?.label || "Structural transition";
  if (bar.squeezeOn) return direction === "unresolved" ? "Compression awaiting resolution" : "Compression with directional pressure";
  if (bar.obvDivergence === "bullish") return "Bullish participation divergence";
  if (bar.obvDivergence === "bearish") return "Bearish participation divergence";
  if (bar.fastState !== bar.slowState) return "Fast/slow regime transition";
  return direction === "bullish" ? "Trend continuation" : direction === "bearish" ? "Defensive continuation" : "Range and crosscurrents";
}

function lifecycleLabel(bar: AnnaReplicaBar, glyphs: string[]) {
  const state = glyphs.find(value => ["A", "P", "C", "D"].includes(value));
  if (state === "A") return "Accumulation";
  if (state === "P") return "Progression";
  if (state === "C") return "Caution";
  if (state === "D") return "Distribution";
  if (bar.callLifecycle === "fresh") return "Fresh event";
  if (bar.callLifecycle === "reinforced") return "Reinforced episode";
  if (bar.callLifecycle === "stale") return "Stale episode";
  return "Neutral transition";
}

function magnitudeMultiple(value: string) {
  if (value === "quiet") return 0.8;
  if (value === "large") return 2.4;
  if (value === "extreme") return 3.4;
  return 1.5;
}

function nextTransitionFor(lifecycle: string, pattern: string, direction: Direction) {
  if (lifecycle === "Accumulation") return "Accumulation → progression if demand survives the next completed-bar test.";
  if (lifecycle === "Progression") return "Progression → expansion while participation and structure remain aligned.";
  if (lifecycle === "Caution") return "Caution → renewed progression or distribution at the stated boundary.";
  if (lifecycle === "Distribution") return "Distribution → downside continuation unless supply is reclaimed.";
  if (/Compression/i.test(pattern)) return direction === "bullish"
    ? "Compression → upside expansion if resistance clears."
    : direction === "bearish"
      ? "Compression → downside expansion if demand fails."
      : "Compression → directional expansion at the first confirmed boundary break.";
  return direction === "bullish"
    ? "Continuation → exhaustion only if momentum and participation deteriorate."
    : direction === "bearish"
      ? "Defensive continuation → reversal only after supply is reclaimed."
      : "Range → expansion when either opposing boundary confirms.";
}

export function buildTensorPredictiveGestalt(
  replica: AnnaReplica,
  entered = false,
  quoteContext?: { price?: number | null; verifiedAt?: string | null; evaluatedAt?: string | number | Date },
): TensorPredictiveGestalt | null {
  const gestalt = replica.gestalt;
  const bar = replica.bars.filter(item => item.barFinality === "closed").at(-1);
  if (!gestalt || !bar) return null;
  const direction = predictionDirection(gestalt.prediction.direction);
  const enrichment = buildTensorEnrichmentSignals(bar);
  const glyphs = enrichment.signals.map(item => item.symbol);
  const location = bar.vectorStructuralLocation;
  const atr = finite(location?.atr) && location.atr > 0 ? location.atr : Math.max((bar.high - bar.low), bar.close * 0.01);
  const magnitude = gestalt.prediction.magnitude;
  const move = atr * magnitudeMultiple(magnitude);
  const demandHigh = location?.nearestDemand?.high;
  const supplyLow = location?.nearestSupply?.low;
  // A broken demand zone is not current support, and supply already below the
  // close is not current resistance. Keep the labels geometrically truthful.
  const support = finite(demandHigh) && demandHigh < bar.close ? demandHigh : null;
  const resistance = finite(supplyLow) && supplyLow > bar.close ? supplyLow : null;
  const bullishTarget = finite(resistance) && resistance > bar.close ? Math.min(bar.close + move, resistance) : bar.close + move;
  const bearishTarget = finite(support) && support < bar.close ? Math.max(bar.close - move, support) : bar.close - move;
  const target = direction === "bullish" ? bullishTarget : direction === "bearish" ? bearishTarget : null;
  const invalidation = direction === "bullish"
    ? (location?.nearestDemand?.low ?? bar.close - atr)
    : direction === "bearish"
      ? (finite(location?.nearestSupply?.high) && location.nearestSupply.high > bar.close ? location.nearestSupply.high : bar.close + atr)
      : (support ?? resistance);
  const extended = glyphs.includes("!") || (location?.roomToDemandAtr ?? 0) > 3;
  const canonicalBuy = bar.primaryMarkers.some(marker => marker.startsWith("buy"));
  const canonicalSell = bar.primaryMarkers.some(marker => marker.startsWith("sell"));
  let decision: Decision;
  if (entered) {
    decision = canonicalSell && direction === "bearish" ? "SELL" : extended || direction === "mixed" || gestalt.manualReviewRequired ? "TRIM" : "HOLD";
  } else {
    decision = canonicalSell || direction === "bearish" ? "AVOID" : canonicalBuy && direction === "bullish" && !extended && !gestalt.manualReviewRequired ? "BUY" : "WAIT";
  }
  const liveVetoes: string[] = [];
  if (!entered && decision === "BUY") {
    const evaluatedAt = quoteContext?.evaluatedAt instanceof Date
      ? quoteContext.evaluatedAt.getTime()
      : typeof quoteContext?.evaluatedAt === "number"
        ? quoteContext.evaluatedAt
        : Date.parse(String(quoteContext?.evaluatedAt || ""));
    const verifiedAt = Date.parse(String(quoteContext?.verifiedAt || ""));
    const livePrice = Number(quoteContext?.price);
    const quoteAge = evaluatedAt - verifiedAt;
    const quoteFresh = Number.isFinite(evaluatedAt) && Number.isFinite(verifiedAt) &&
      quoteAge >= -5 * 60_000 && quoteAge <= 5 * 60_000;
    if (!quoteFresh || !Number.isFinite(livePrice) || livePrice <= 0) {
      decision = "WAIT";
      liveVetoes.push("A fresh verified market price is required before a new entry.");
    } else if (finite(invalidation) && livePrice < invalidation) {
      decision = "AVOID";
      liveVetoes.push("The verified price is below bullish invalidation.");
    } else {
      const antiChaseThreshold = Math.max(bar.close * 0.005, atr * 0.75);
      if (livePrice > bar.close + antiChaseThreshold) {
        decision = "WAIT";
        liveVetoes.push("Location is extended; do not chase.");
      }
    }
  }
  const directionLabel = direction === "bullish" ? "Higher path favored" : direction === "bearish" ? "Lower path favored" : direction === "mixed" ? "Crosscurrents" : "Range unresolved";
  const pattern = patternFor(bar, direction);
  const lifecycle = lifecycleLabel(bar, glyphs);
  const low = Math.max(0, direction === "bearish" ? bearishTarget : bar.close - move * 0.55);
  const high = direction === "bullish" ? bullishTarget : bar.close + move * 0.55;
  const bullLevel = resistance ?? bar.close + atr;
  const bearLevel = support ?? bar.close - atr;
  const changesRead = direction === "bullish"
    ? `A completed ${replica.intervalLabel} close below ${formatLevel(invalidation)} weakens the higher path; clearing ${formatLevel(bullLevel)} opens the next upside leg.`
    : direction === "bearish"
      ? `A completed ${replica.intervalLabel} close above ${formatLevel(invalidation)} weakens the lower path; losing ${formatLevel(bearLevel)} opens the next downside leg.`
      : `A completed ${replica.intervalLabel} close above ${formatLevel(bullLevel)} favors expansion higher; below ${formatLevel(bearLevel)} favors expansion lower.`;
  return {
    version: TENSOR_PREDICTIVE_GESTALT_VERSION,
    provenance: "tensorContext",
    authority: "additive-projection",
    finality: "closed",
    usesFutureData: false,
    asOf: bar.timestamp,
    decision,
    ownerState: entered ? "owner" : "non-owner",
    direction,
    directionLabel,
    conviction: gestalt.prediction.conviction,
    magnitude,
    horizon: gestalt.prediction.timeframeLabel,
    pattern,
    lifecycle,
    location: location?.label ?? "Neutral location",
    componentVector: `${bar.bullishVotes}↑ ${bar.bearishVotes}↓ ${Math.max(0, bar.totalVotes - bar.bullishVotes - bar.bearishVotes)}·`,
    timeframeAgreement: gestalt.timeframe.agreement,
    timeframeStack: [gestalt.timeframe.selected, ...gestalt.timeframe.contexts].map(frame => ({
      interval: frame.interval,
      role: frame.role,
      direction: frame.direction,
      phase: frame.phase,
      alignment: frame.alignment,
    })),
    nextTransition: nextTransitionFor(lifecycle, pattern, direction),
    expectedMove: { low, high, basis: `${magnitude} ATR/structure-bounded path from the latest completed bar` },
    levels: { support, resistance, target, invalidation },
    scenarios: [
      { id: "base", label: "Base case", trigger: "Current completed-bar structure persists", outcome: directionLabel, level: target },
      { id: "bull", label: "Bull case", trigger: `Close above ${formatLevel(bullLevel)}`, outcome: "Acceptance above supply and upside continuation", level: bullishTarget },
      { id: "bear", label: "Bear case", trigger: `Close below ${formatLevel(bearLevel)}`, outcome: "Demand failure and downside continuation", level: bearishTarget },
    ],
    changesRead,
    summary: `${decision}: ${pattern}. ${gestalt.prediction.summary}`,
    reasons: [...gestalt.prediction.basis, ...gestalt.reasons].slice(0, 6),
    vetoes: [...gestalt.vetoes, ...(extended ? ["Location is extended; do not chase."] : []), ...liveVetoes]
      .filter((value,index,array)=>array.indexOf(value)===index).slice(0, 5),
    enrichmentGlyphs: glyphs,
  };
}

function formatLevel(value: number | null) {
  if (!finite(value)) return "the opposing boundary";
  return value >= 100 ? value.toFixed(2) : value >= 10 ? value.toFixed(2) : value.toFixed(3);
}
