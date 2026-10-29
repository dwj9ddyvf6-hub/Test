import {
  buildAnnaReplica,
  type AnnaReplicaBar,
} from "../../lib/anna-replica.mjs";
import {
  buildVector10mForecast,
  decorateVectorReplica,
  structuralConflictReason,
} from "./vector-structure.ts";
import type { VectorGestaltState } from "./vector-gestalt.ts";
import type { Vector10mForecast } from "./vector-gestalt.ts";
import {
  buildVectorCausalEventTape,
  type VectorCausalEvent,
} from "./vector-causal-events.ts";
import type {
  VectorBar,
  VectorBarResult,
  VectorEvent,
  VectorFib,
  VectorState,
} from "./vector-engine.ts";
import { analyzeVectorBars } from "./vector-engine.ts";
import { VECTOR_REPLICA_MODEL_VERSION } from "./vector-watchlist-contract.ts";
import type { GoldDiamondEvaluation } from "./vector-gold-diamond.ts";

export { VECTOR_REPLICA_MODEL_VERSION };
export const VECTOR_REPLICA_MINIMUM_BARS = 200;
export const VECTOR_REPLICA_MINIMUM_BARS_BY_INTERVAL = {
  "5m": VECTOR_REPLICA_MINIMUM_BARS,
  "10m": VECTOR_REPLICA_MINIMUM_BARS,
  "1h": 200,
  "2h": VECTOR_REPLICA_MINIMUM_BARS,
  "4h": VECTOR_REPLICA_MINIMUM_BARS,
  "1d": 100,
  "1wk": 60,
} as const;

export function vectorReplicaMinimumBars(
  interval: keyof typeof VECTOR_REPLICA_MINIMUM_BARS_BY_INTERVAL,
) {
  return VECTOR_REPLICA_MINIMUM_BARS_BY_INTERVAL[interval];
}

export type VectorReplicaAnalysis = {
  modelVersion: typeof VECTOR_REPLICA_MODEL_VERSION;
  status: "ready" | "warming" | "unavailable";
  current: VectorBarResult | null;
  events: VectorEvent[];
  causalEvents: VectorCausalEvent[];
  activeStateStartedAt: number | null;
  notificationEventAt: number | null;
  fib?: VectorFib | null;
  gestalt?: VectorGestaltState;
  forecast10m?: Vector10mForecast;
};

function explicitState(bar: AnnaReplicaBar): VectorState | null {
  if (
    bar.primaryMarkers.includes("sell-red") ||
    bar.primaryMarkers.includes("sell-magenta")
  )
    return "VECTOR_SELL";
  if (
    bar.primaryMarkers.includes("buy-cyan") ||
    bar.primaryMarkers.includes("buy-green")
  )
    return "VECTOR_BUY";
  if (bar.warningMarker) return "CONFLICT";
  if (bar.dcbMarker === "sell" || bar.dcbMarker === "buy")
    return "REVERSAL_WINDOW";
  if (bar.weakMarker === "B") return "SETUP_FORMING";
  if (bar.weakMarker === "W1") return "REVERSAL_WINDOW";
  return null;
}

function activeState(bar: AnnaReplicaBar): VectorState {
  // The replica core intentionally carries an episode direction forward until
  // an opposite marker appears.  That is useful chart context, but it is not a
  // fresh watchlist call.  Dashboard BUY/SELL states require an explicit
  // marker on the latest completed bar.
  return explicitState(bar) || "NEUTRAL";
}

function directionForState(
  state: VectorState,
  bar: AnnaReplicaBar,
): VectorBarResult["direction"] {
  if (state === "VECTOR_BUY" || state === "SETUP_FORMING")
    return "bullish";
  if (state === "VECTOR_SELL") return "bearish";
  if (state === "CONFLICT" || state === "REVERSAL_WINDOW")
    return "mixed";
  if (bar.fastState === "bullish" && bar.slowState === "bullish")
    return "bullish";
  if (bar.fastState === "bearish" && bar.slowState === "bearish")
    return "bearish";
  return "neutral";
}

function nextConfirmation(
  state: VectorState,
  bar: AnnaReplicaBar,
  intervalLabel = "five-minute",
) {
  if (state === "VECTOR_BUY")
    return `A new bullish Tensor marker printed on the latest completed ${intervalLabel} bar.`;
  if (state === "VECTOR_SELL")
    return `A new bearish Tensor marker printed on the latest completed ${intervalLabel} bar.`;
  if (state === "SETUP_FORMING")
    return "Early buy conditions only; wait for a confirmed Tensor diamond.";
  if (state === "REVERSAL_WINDOW")
    return "Watch only; wait for a confirmed Tensor marker.";
  if (state === "CONFLICT")
    return bar.vectorStructuralLocation?.bias === "bearish"
      ? "Wait for price to reclaim demand or clear overhead supply before treating the bullish marker as actionable."
      : bar.vectorStructuralLocation?.bias === "bullish"
        ? "Wait for demand to fail or for the bearish marker to regain structural room."
        : "Fast and slow states conflict; wait for completed-bar resolution.";
  return "No active completed-bar Tensor call.";
}

function toBarResult(
  bar: AnnaReplicaBar & {
    goldDiamond?: GoldDiamondEvaluation | null;
  },
  index: number,
  intervalLabel = "five-minute",
): VectorBarResult {
  const rawState = activeState(bar);
  const structuralVeto = structuralConflictReason(
    rawState,
    bar.vectorStructuralLocation,
  );
  // Anna's explicit marker is the authoritative dashboard state. Native
  // structure may qualify that state through a veto, but must never rename a
  // raw BUY/SELL event to CONFLICT or make the event disappear.
  const state = rawState;
  const voteDifference = bar.bullishVotes - bar.bearishVotes;
  const resultant = bar.totalVotes
    ? 100 * (voteDifference / bar.totalVotes)
    : null;
  const coherence = bar.totalVotes
    ? Math.max(bar.bullishVotes, bar.bearishVotes) / bar.totalVotes
    : null;
  const reasons = [
    ...bar.markerEvidence,
    ...bar.eventEvidence.map(item => item.basis),
    ...(bar.vectorStructuralLocation?.label
      ? [`Structural location: ${bar.vectorStructuralLocation.label}.`]
      : []),
  ].filter((value, itemIndex, values) =>
    Boolean(value) && values.indexOf(value) === itemIndex
  );
  return {
    index,
    time: bar.timestamp,
    close: bar.close,
    finality: "closed",
    primaryMarkers: [...bar.primaryMarkers],
    structuralActionSignal: typeof bar.vectorStructuralLocation?.actionSignal === "string"
      ? bar.vectorStructuralLocation.actionSignal
      : (bar.vectorStructuralLocation?.actionSignal as unknown as { trigger?: "demand-bounce" | "supply-breakout" | "demand-breakdown" } | null)?.trigger ?? null,
    goldDiamond: bar.goldDiamond ?? null,
    state,
    direction: directionForState(state, bar),
    resultant,
    coherence,
    regime:
      state === "CONFLICT"
        ? "balanced"
        : bar.candleRegime === "bullish"
          ? "constructive"
          : "defensive",
    families: {
      trend: bar.vectorStructuralLocation?.trend ?? null,
      momentum: bar.vectorStructuralLocation?.momentum ?? null,
      location: bar.vectorStructuralLocation?.value ?? null,
      participation: bar.vectorStructuralLocation?.participation ?? null,
      volatilityReadiness: null,
    },
    atr: bar.vectorStructuralLocation?.atr ?? null,
    rsi: null,
    macdHistogram: bar.macdHistogram,
    relativeVolume: bar.rvol,
    locationTrigger:
      bar.vectorStructuralLocation?.trigger ?? "none",
    reasons,
    vetoes: [
      ...(state === "CONFLICT"
        ? ["fast/slow state conflict"]
        : []),
      ...(structuralVeto ? [structuralVeto] : []),
    ],
    nextConfirmation: nextConfirmation(state, bar, intervalLabel),
    tensorContext: bar.tensorContext ?? null,
  };
}

function verifiedInputBars(bars: VectorBar[]) {
  let priorTime = 0;
  return bars.every(bar => {
    const verified =
      Number.isFinite(bar.time) &&
      bar.time > priorTime &&
      Number.isFinite(bar.open) &&
      Number.isFinite(bar.high) &&
      Number.isFinite(bar.low) &&
      Number.isFinite(bar.close) &&
      Number.isFinite(bar.volume) &&
      Number(bar.open) > 0 &&
      Number(bar.high) > 0 &&
      Number(bar.low) > 0 &&
      bar.close > 0 &&
      Number(bar.volume) >= 0 &&
      Number(bar.high) >= Math.max(Number(bar.open), bar.close) &&
      Number(bar.low) <= Math.min(Number(bar.open), bar.close);
    priorTime = bar.time;
    return verified;
  });
}

function activeStateStart(
  bars: AnnaReplicaBar[],
  currentState: VectorState,
) {
  if (currentState === "NEUTRAL" || !bars.length) return null;
  // Consecutive same-direction markers are distinct completed-bar events,
  // not one indefinitely carried chart episode.
  return bars.at(-1)?.timestamp ?? null;
}

function explicitEvents(bars: AnnaReplicaBar[], intervalLabel = "five-minute") {
  const events: VectorEvent[] = [];
  bars.forEach((bar, index) => {
    const result = toBarResult(bar, index, intervalLabel);
    const state = result.state;
    if (state === "NEUTRAL") return;
    events.push({
      id: `${VECTOR_REPLICA_MODEL_VERSION}:${bar.timestamp}:${state}`,
      index,
      time: bar.timestamp,
      price: bar.close,
      state,
      direction: result.direction,
      resultant: result.resultant,
    });
  });
  return events;
}

export function analyzeVectorReplicaBars({
  symbol,
  bars,
  signalOnly = false,
  interval = "5m",
  exchange = null,
  timezone = "America/New_York",
  instrumentType = "EQUITY",
  intervalLabel = interval === "10m" ? "ten-minute" : interval === "1h"
    ? "one-hour"
    : interval === "2h"
      ? "two-hour"
      : interval === "4h"
        ? "four-hour"
        : interval === "1d"
          ? "one-day"
          : interval === "1wk"
            ? "one-week"
            : "five-minute",
}: {
  symbol: string;
  bars: VectorBar[];
  signalOnly?: boolean;
  interval?: "5m" | "10m" | "1h" | "2h" | "4h" | "1d" | "1wk";
  exchange?: string | null;
  timezone?: string | null;
  instrumentType?: string | null;
  intervalLabel?: string;
}): VectorReplicaAnalysis {
  const minimumBars = vectorReplicaMinimumBars(interval);
  // Higher-frame readiness follows the amount of information represented by
  // each bar. Long-lookback fields such as EMA-200 remain null until their own
  // mathematical input exists; no value is backfilled or fabricated.
  if (bars.length < minimumBars)
    return {
      modelVersion: VECTOR_REPLICA_MODEL_VERSION,
      status: "warming",
      current: null,
      events: [],
      causalEvents: [],
      activeStateStartedAt: null,
      notificationEventAt: null,
    };
  if (!verifiedInputBars(bars))
    return {
      modelVersion: VECTOR_REPLICA_MODEL_VERSION,
      status: "unavailable",
      current: null,
      events: [],
      causalEvents: [],
      activeStateStartedAt: null,
      notificationEventAt: null,
    };
  const history = {
    symbol,
    exchange,
    instrumentType: instrumentType || "EQUITY",
    timezone: timezone || "America/New_York",
    interval,
    intervalLabel,
    // Signal consumers need only the latest decorated bar; the full source
    // tape remains available to the deterministic indicator core above.
    displayBars: signalOnly ? 1 : bars.length,
    latestBarOpen: false,
    bars: bars.map(bar => ({
      timestamp: bar.time,
      open: Number(bar.open),
      high: Number(bar.high),
      low: Number(bar.low),
      close: bar.close,
      volume: Number(bar.volume),
    })),
  };
  const authoritativeAnalysis = analyzeVectorBars(bars, {
    summaryOnly: signalOnly,
    minimumBars,
    requireEma200: minimumBars >= VECTOR_REPLICA_MINIMUM_BARS,
  });
  // The causal tape and 10m forecast are specialist 5m products. Higher
  // timeframe decisions still use the same deterministic analysis core, but
  // never relabel daily/weekly bars as five-minute observations.
  const fiveMinuteAnalysis = interval === "5m"
    ? authoritativeAnalysis
    : undefined;
  const replica = buildAnnaReplica(history, { latestOnly: signalOnly });
  const decorated = replica
      ? decorateVectorReplica(replica, history, authoritativeAnalysis, {
        includeGestalt: !signalOnly,
        latestOnly: signalOnly,
      })
    : null;
  const latest = decorated?.bars.at(-1);
  if (!decorated || !latest)
    return {
      modelVersion: VECTOR_REPLICA_MODEL_VERSION,
      status: "unavailable",
      current: null,
      events: [],
      causalEvents: [],
      activeStateStartedAt: null,
      notificationEventAt: null,
    };
  // A bar count alone is not sufficient authority. Flat/degenerate inputs
  // can contain 200 rows while ATR and the directional resultant remain
  // undefined. Do not expose Anna markers until the independently decorated
  // EMA-200/structure calculation is genuinely ready.
  if (decorated.structure?.status !== "ready")
    return {
      modelVersion: VECTOR_REPLICA_MODEL_VERSION,
      status: "warming",
      current: null,
      events: [],
      causalEvents: [],
      activeStateStartedAt: null,
      notificationEventAt: null,
    };
  const current = toBarResult(
    latest,
    decorated.bars.length - 1,
    intervalLabel,
  );
  const activeStateStartedAt = activeStateStart(
    decorated.bars,
    current.state,
  );
  const notificationEventAt =
    (current.state === "VECTOR_BUY" ||
      current.state === "VECTOR_SELL") &&
    activeStateStartedAt !== null
      ? activeStateStartedAt + 5 * 60
      : null;
  // The runner needs the exact marker, structural readiness, and latest
  // result before it can route an alert. Forecast/event tapes do not affect
  // that decision and roughly double full-roster boundary latency, so the
  // signal path stops here while using the identical authoritative core.
  if (signalOnly)
    return {
      modelVersion: VECTOR_REPLICA_MODEL_VERSION,
      status: "ready",
      current,
      events: [],
      causalEvents: [],
      activeStateStartedAt,
      notificationEventAt,
      fib: fiveMinuteAnalysis?.fib ?? null,
      ...(decorated.gestalt ? { gestalt: decorated.gestalt } : {}),
    };
  const forecast10m = interval === "5m"
    ? buildVector10mForecast(decorated, {
        symbol,
        exchange,
        instrumentType,
        interval: "5m",
        intervalLabel: "5-minute",
        timezone: timezone || "America/New_York",
        latestBarOpen: false,
        bars: history.bars,
      })
    : undefined;
  return {
    modelVersion: VECTOR_REPLICA_MODEL_VERSION,
    status: "ready",
    current,
    events: explicitEvents(decorated.bars, intervalLabel),
    causalEvents: fiveMinuteAnalysis
      ? buildVectorCausalEventTape({
          symbol,
          fiveMinuteBars: bars,
          fiveMinuteAnalysis,
        })
      : [],
    activeStateStartedAt,
    notificationEventAt,
    fib: fiveMinuteAnalysis?.fib ?? null,
    ...(decorated.gestalt ? { gestalt: decorated.gestalt } : {}),
    ...(forecast10m ? { forecast10m } : {}),
  };
}
