import type {
  AnnaReplica,
  AnnaReplicaBar,
  VectorStructuralLocation,
  VectorStructuralZone,
  VectorStructuralZoneReference,
  VectorStructureSnapshot,
} from "../../lib/anna-replica.mjs";
import {
  analyzeVectorBars,
  type VectorAnalysis,
  type VectorBar,
  type VectorActionSignalTrigger,
  type VectorBarResult,
  type VectorState,
  type VectorZone,
} from "./vector-engine.ts";
import {
  buildDerivedVectorTimeframeReplica,
  buildDerivedVectorTimeframeReplicas,
  buildVectorGestaltState,
  type Vector10mForecast,
  type VectorGestaltSourceHistory,
} from "./vector-gestalt.ts";
import {
  evaluateGoldDiamond,
  type GoldDiamondEvaluation,
} from "./vector-gold-diamond.ts";

export const VECTOR_STRUCTURE_VERSION = "vector-structure/1.4.0-quality";

const VECTOR_ACTION_SIGNAL_TRIGGERS = new Set<VectorActionSignalTrigger>([
  "demand-bounce",
  "supply-breakout",
  "demand-breakdown",
]);

/**
 * Derive the dashboard's after-hours forecast from the same verified 5m
 * source tape already loaded by the watchlist scanner.  This avoids a second
 * provider fan-out and keeps the 10m forecast on the completed regular
 * session, while the live 5m signal path remains unchanged.
 */
export function buildVector10mForecast(
  replica: AnnaReplica,
  sourceHistory?: VectorGestaltSourceHistory,
): Vector10mForecast | null {
  if (replica.interval !== "5m") return null;
  const derived = buildDerivedVectorTimeframeReplica(
    replica,
    sourceHistory,
    "10m",
  );
  if (!derived) return null;
  const derivedHistory: VectorGestaltSourceHistory = {
    symbol: derived.symbol,
    currency: derived.currency,
    exchange: derived.exchange,
    instrumentType: sourceHistory?.instrumentType ?? null,
    timezone: derived.timezone,
    interval: "10m",
    intervalLabel: "10-minute",
    latestBarOpen: false,
    bars: derived.bars.map((bar) => ({
      timestamp: bar.timestamp,
      open: bar.open,
      high: bar.high,
      low: bar.low,
      close: bar.close,
      volume: bar.volume,
    })),
  };
  const decorated = decorateVectorReplica(derived, derivedHistory);
  const prediction = decorated.gestalt?.prediction;
  const latest = decorated.bars
    .filter((bar) => bar.barFinality === "closed")
    .at(-1);
  if (!prediction || !latest || !Number.isFinite(latest.timestamp))
    return null;
  return {
    ...prediction,
    interval: "10m",
    asOf: new Date(latest.timestamp * 1_000).toISOString(),
    completedBarAt: new Date(
      (latest.timestamp + 10 * 60) * 1_000,
    ).toISOString(),
    exchange: derived.exchange,
    timezone: derived.timezone,
    instrumentType: sourceHistory?.instrumentType ?? null,
  };
}

function finite(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

function distanceToZone(price: number, zone: Pick<VectorZone, "low" | "high">) {
  if (price < zone.low) return zone.low - price;
  if (price > zone.high) return price - zone.high;
  return 0;
}

function directionalDistance(
  price: number,
  zone: Pick<VectorZone, "low" | "high">,
  polarity: VectorZone["polarity"],
) {
  if (polarity === "demand") {
    if (price >= zone.low && price <= zone.high) return 0;
    return zone.high <= price ? price - zone.high : Number.POSITIVE_INFINITY;
  }
  if (price >= zone.low && price <= zone.high) return 0;
  return zone.low >= price ? zone.low - price : Number.POSITIVE_INFINITY;
}

function nearestZone(
  zones: VectorZone[],
  price: number,
  polarity: VectorZone["polarity"],
) {
  const candidates = zones.filter(zone => zone.polarity === polarity);
  if (!candidates.length) return null;
  return [...candidates].sort((left, right) => {
    const leftDirectional = directionalDistance(price, left, polarity);
    const rightDirectional = directionalDistance(price, right, polarity);
    const leftRank = Number.isFinite(leftDirectional)
      ? leftDirectional
      : distanceToZone(price, left) + Math.abs(price - left.center) * 0.01;
    const rightRank = Number.isFinite(rightDirectional)
      ? rightDirectional
      : distanceToZone(price, right) + Math.abs(price - right.center) * 0.01;
    return leftRank - rightRank || right.strength - left.strength;
  })[0];
}

function zoneReference(
  zone: VectorZone | null,
  price: number,
  atr: number | null,
): VectorStructuralZoneReference | null {
  if (!zone) return null;
  return {
    polarity: zone.polarity,
    low: zone.low,
    high: zone.high,
    strength: zone.strength,
    touches: zone.touches,
    dualConfirmed: zone.dualConfirmed,
    distanceAtr:
      finite(atr) && atr > 0
        ? distanceToZone(price, zone) / atr
        : null,
  };
}

function triggerBias(
  trigger: VectorBarResult["locationTrigger"],
): VectorStructuralLocation["bias"] {
  if (
    [
      "demand-bounce",
      "demand-hold",
      "demand-reclaim",
      "supply-breakout",
      "range-breakout",
      "near-demand",
    ].includes(trigger)
  )
    return "bullish";
  if (
    [
      "supply-rejection",
      "supply-loss",
      "demand-breakdown",
      "range-breakdown",
      "near-supply",
    ].includes(trigger)
  )
    return "bearish";
  return "neutral";
}

function triggerLabel(trigger: VectorBarResult["locationTrigger"]) {
  const labels: Record<VectorBarResult["locationTrigger"], string> = {
    "demand-bounce": "Demand bounce",
    "demand-hold": "Demand hold",
    "demand-reclaim": "Demand reclaim",
    "supply-breakout": "Supply cleared",
    "supply-rejection": "Supply rejection",
    "supply-loss": "Supply loss",
    "demand-breakdown": "Demand failed",
    "range-breakout": "Range breakout",
    "range-breakdown": "Range breakdown",
    "near-demand": "Near demand",
    "near-supply": "Near supply",
    none: "Neutral location",
  };
  return labels[trigger];
}

function structuralLocation(
  result: VectorBarResult,
  zones: VectorZone[],
  includeReferences: boolean,
): VectorStructuralLocation {
  const price = result.close;
  const demand = includeReferences
    ? nearestZone(zones, price, "demand")
    : null;
  const supply = includeReferences
    ? nearestZone(zones, price, "supply")
    : null;
  const atr = finite(result.atr) && result.atr > 0 ? result.atr : null;
  const roomToSupplyAtr =
    supply && finite(atr) && atr > 0 && supply.low >= price
      ? Math.max(0, supply.low - price) / atr
      : supply && finite(atr) && atr > 0 && price >= supply.low && price <= supply.high
        ? 0
        : null;
  const roomToDemandAtr =
    demand && finite(atr) && atr > 0 && demand.high <= price
      ? Math.max(0, price - demand.high) / atr
      : demand && finite(atr) && atr > 0 && price >= demand.low && price <= demand.high
        ? 0
        : null;
  return {
    trigger: result.locationTrigger,
    bias: triggerBias(result.locationTrigger),
    label: triggerLabel(result.locationTrigger),
    value: result.families.location,
    atr,
    trend: result.families.trend,
    momentum: result.families.momentum,
    participation: result.families.participation,
    volatilityReadiness: result.families.volatilityReadiness,
    roomToSupplyAtr,
    roomToDemandAtr,
    nearestDemand: zoneReference(demand, price, atr),
    nearestSupply: zoneReference(supply, price, atr),
  };
}

function toInputBar(bar: AnnaReplicaBar): VectorBar {
  return {
    time: bar.timestamp,
    open: bar.open,
    high: bar.high,
    low: bar.low,
    close: bar.close,
    volume: bar.volume,
  };
}

function publicZone(zone: VectorZone, bars: VectorBar[]): VectorStructuralZone {
  return {
    id: zone.id,
    polarity: zone.polarity,
    model: zone.model,
    modelSource: zone.modelSource,
    low: zone.low,
    high: zone.high,
    center: zone.center,
    createdAt: zone.createdAt,
    knownAt: zone.knownAt,
    lastSeenAt: bars[zone.lastSeenIndex]?.time ?? zone.knownAt,
    state: zone.state === "broken" ? "break-pending" : zone.state,
    touches: zone.touches,
    strength: zone.strength,
    dualConfirmed: zone.dualConfirmed,
    contextOnly: zone.contextOnly,
  };
}

export function decorateVectorReplica(
  replica: AnnaReplica,
  sourceHistory?: VectorGestaltSourceHistory,
  precomputedAnalysis?: VectorAnalysis,
  {
    includeGestalt = true,
    latestOnly = false,
  }: { includeGestalt?: boolean; latestOnly?: boolean } = {},
): AnnaReplica {
  const closedBars = replica.bars.filter(bar => bar.barFinality === "closed");
  const sourceBars = Array.isArray(sourceHistory?.bars)
    ? sourceHistory.bars
        .slice(
          0,
          sourceHistory.latestBarOpen
            ? Math.max(0, sourceHistory.bars.length - 1)
            : sourceHistory.bars.length,
        )
        .filter(
          bar =>
            finite(bar.timestamp) &&
            finite(bar.open) &&
            finite(bar.high) &&
            finite(bar.low) &&
            finite(bar.close) &&
            finite(bar.volume) &&
            bar.high >= Math.max(bar.open, bar.close) &&
            bar.low <= Math.min(bar.open, bar.close),
        )
        .map(bar => ({
          time: bar.timestamp,
          open: bar.open,
          high: bar.high,
          low: bar.low,
          close: bar.close,
          volume: bar.volume,
        }))
    : [];
  const inputBars = sourceBars.length >= closedBars.length
    ? sourceBars
    : closedBars.map(toInputBar);
  const precomputedMatches = Boolean(
    precomputedAnalysis &&
      precomputedAnalysis.evidence.completedBars === inputBars.length &&
      precomputedAnalysis.evidence.lastTime === inputBars.at(-1)?.time,
  );
  const analysis = precomputedMatches && precomputedAnalysis
    ? precomputedAnalysis
    : analyzeVectorBars(inputBars, { summaryOnly: latestOnly });
  const resultByTime = new Map(
    analysis.bars.map(result => [result.time, result]),
  );
  const replicaBarByTime = new Map(
    replica.bars.map(bar => [bar.timestamp, bar]),
  );
  const goldDiamondByTime = new Map<number, GoldDiamondEvaluation>();
  const evaluationBars = latestOnly ? inputBars.slice(-1) : inputBars;
  const evaluationOffset = inputBars.length - evaluationBars.length;
  for (const [localIndex, inputBar] of evaluationBars.entries()) {
    const index = localIndex + evaluationOffset;
    const replicaBar = replicaBarByTime.get(inputBar.time);
    if (!replicaBar || replicaBar.barFinality !== "closed") continue;
    goldDiamondByTime.set(
      inputBar.time,
      evaluateGoldDiamond({
        index,
        bars: inputBars,
        analysis,
        greenBase: replicaBar.primaryMarkers.includes("buy-green"),
      }),
    );
  }
  const currentResult = analysis.current;
  const actionSignalByTime = new Map<number, VectorActionSignalTrigger>();
  for (const event of analysis.causalLocationEvents) {
    if (VECTOR_ACTION_SIGNAL_TRIGGERS.has(event.trigger as VectorActionSignalTrigger)) {
      actionSignalByTime.set(
        event.time,
        event.trigger as VectorActionSignalTrigger,
      );
    }
  }
  const zones = (analysis.displayZones ?? analysis.zones).map(zone =>
    publicZone(zone, inputBars),
  );
  const current = currentResult
    ? structuralLocation(currentResult, analysis.zones, true)
    : null;
  const bars = (latestOnly ? replica.bars.slice(-1) : replica.bars).map(bar => {
      const result = resultByTime.get(bar.timestamp);
      const actionSignal = actionSignalByTime.get(bar.timestamp);
      return {
        ...bar,
        vectorStructuralLocation: result
          ? {
              ...structuralLocation(
                result,
                result.time === currentResult?.time ? analysis.zones : [],
                result.time === currentResult?.time,
              ),
              ...(actionSignal ? { actionSignal } : {}),
            }
          : null,
        goldDiamond: goldDiamondByTime.get(bar.timestamp) ?? null,
      };
    });
  const structure: VectorStructureSnapshot = {
    version: VECTOR_STRUCTURE_VERSION,
    status: analysis.status,
    completedBars: inputBars.length,
    latestBarAt: currentResult?.time ?? null,
    zones,
    current,
    nativeQuality: currentResult
      ? {
          modelVersion: analysis.modelVersion,
          state: currentResult.state,
          direction: currentResult.direction,
          resultant: currentResult.resultant,
          coherence: currentResult.coherence,
          families: { ...currentResult.families },
          reasons: [...currentResult.reasons],
          vetoes: [...currentResult.vetoes],
          nextConfirmation: currentResult.nextConfirmation,
        }
      : null,
  };
  const structuredReplica = {
    ...replica,
    bars,
    structuralZones: zones,
    structure,
  };
  // Notification routing needs the exact marker plus native structural
  // readiness, but not the derived timeframe/forecast context. Keeping that
  // optional avoids spending the live bar-close budget on non-routing work.
  if (!includeGestalt) return structuredReplica;
  const contextReplicas = buildDerivedVectorTimeframeReplicas(
    structuredReplica,
    sourceHistory,
  );
  const gestalt = buildVectorGestaltState(structuredReplica, contextReplicas);
  return {
    ...structuredReplica,
    ...(gestalt ? { gestalt } : {}),
  };
}

export function structuralLocationOpposesState(
  state: VectorState,
  location: VectorStructuralLocation | null | undefined,
) {
  if (!location) return false;
  return (
    (state === "VECTOR_BUY" && location.bias === "bearish") ||
    (state === "VECTOR_SELL" && location.bias === "bullish")
  );
}

export function structuralConflictReason(
  state: VectorState,
  location: VectorStructuralLocation | null | undefined,
) {
  if (!structuralLocationOpposesState(state, location)) return null;
  if (state === "VECTOR_BUY")
    return "Bullish marker conflicts with overhead supply or bearish structural location.";
  if (state === "VECTOR_SELL")
    return "Bearish marker conflicts with underlying demand or bullish structural location.";
  return null;
}
