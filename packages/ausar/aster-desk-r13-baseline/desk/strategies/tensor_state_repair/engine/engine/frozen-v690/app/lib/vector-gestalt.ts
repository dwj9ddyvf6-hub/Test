import {
  buildAnnaReplica,
  type AnnaReplica,
  type AnnaReplicaBar,
  type TensorForecastContext,
} from "../../lib/anna-replica.mjs";
import {
  exchangeClock,
  exchangeDateTimeUtc,
  exchangeSessionBounds,
  exchangeSessionProfile,
  isExchangeMarketDate,
  nextExchangeMarketDate,
  type SessionPolicy,
} from "./session-policy.ts";
import { TENSOR_CHART_DISPLAY_BARS } from "../../lib/tensor-chart-window.mjs";

/**
 * This module is deliberately a reconstruction layer, not a claim about
 * Anna's private implementation.  It turns the observable chart fields into
 * a causal state machine: the current bar can read prior bars, but no bar can
 * read a future bar.  The higher-frame views are derived from the same
 * completed source history and are labelled as derived rather than treated as
 * independent evidence.
 */

export const VECTOR_GESTALT_VERSION =
  "vector-gestalt/1.3.0-integrity";

// The external reconstruction does not disclose a reliable invalidation
// policy. Vector therefore stops treating an inherited event as forecast
// authority after a finite completed-bar window while preserving the raw
// marker and replica episode unchanged.
export const VECTOR_FORECAST_EPISODE_MAX_AGE_BARS = 12;
export const VECTOR_CONTEXT_MINIMUM_BARS = 50;

export type GestaltDirection = "bullish" | "bearish" | "mixed" | "neutral";

export type GestaltPhase =
  | "unavailable"
  | "neutral"
  | "forming"
  | "fast-reversal"
  | "confirmed"
  | "active"
  | "exhausting"
  | "reversal-window"
  | "conflict";

export type GestaltEvidenceStrength =
  | "strong"
  | "moderate"
  | "limited"
  | "insufficient";

export type GestaltFrameRole = "timing" | "swing" | "higher-horizon";

export type VectorForecastDirection =
  | "higher-continuation"
  | "higher-reversal"
  | "range"
  | "crosscurrents"
  | "lower-reversal"
  | "lower-continuation";

export type VectorForecastMagnitude = "quiet" | "normal" | "large" | "extreme";

export type VectorForecastConviction = "low" | "moderate" | "high";

export type VectorForecastTimeframe =
  | "current-session"
  | "next-session"
  | "next-2-5-sessions"
  | "next-1-4-weeks"
  | "longer-regime";

export type VectorForecast = {
  direction: VectorForecastDirection;
  directionLabel: string;
  magnitude: VectorForecastMagnitude;
  conviction: VectorForecastConviction;
  timeframe: VectorForecastTimeframe;
  timeframeLabel: string;
  summary: string;
  basis: string[];
  context?: TensorForecastContext;
};

/**
 * Compact forecast publication used by the watchlist/dashboard surfaces.
 * The forecast is derived from completed bars only; the full gestalt object
 * remains private to the Vector detail surface.
 */
export type Vector10mForecast = VectorForecast & {
  interval: "10m";
  asOf: string;
  completedBarAt: string;
  exchange?: string | null;
  timezone?: string | null;
  instrumentType?: string | null;
};

const VECTOR_FORECAST_DIRECTIONS = new Set<VectorForecastDirection>([
  "higher-continuation",
  "higher-reversal",
  "range",
  "crosscurrents",
  "lower-reversal",
  "lower-continuation",
]);
const VECTOR_FORECAST_MAGNITUDES = new Set<VectorForecastMagnitude>([
  "quiet",
  "normal",
  "large",
  "extreme",
]);
const VECTOR_FORECAST_CONVICTIONS = new Set<VectorForecastConviction>([
  "low",
  "moderate",
  "high",
]);
const VECTOR_FORECAST_TIMEFRAMES = new Set<VectorForecastTimeframe>([
  "current-session",
  "next-session",
  "next-2-5-sessions",
  "next-1-4-weeks",
  "longer-regime",
]);
const VECTOR_FORECAST_LABEL_MAX_LENGTH = 64;
const VECTOR_FORECAST_SUMMARY_MAX_LENGTH = 256;
const VECTOR_FORECAST_BASIS_MAX_ITEMS = 6;
const VECTOR_FORECAST_BASIS_ITEM_MAX_LENGTH = 256;

function boundedForecastText(value: unknown, maximum = 2_000) {
  return typeof value === "string" &&
    value.trim().length > 0 &&
    value.length <= maximum;
}

/** Runtime trust boundary for persisted and API forecast payloads. */
export function isVector10mForecast(
  value: unknown,
): value is Vector10mForecast {
  if (!value || typeof value !== "object" || Array.isArray(value))
    return false;
  const forecast = value as Record<string, unknown>;
  const asOf = Date.parse(String(forecast.asOf || ""));
  const completedBarAt = Date.parse(
    String(forecast.completedBarAt || ""),
  );
  const basis = forecast.basis;
  return (
    forecast.interval === "10m" &&
    VECTOR_FORECAST_DIRECTIONS.has(
      forecast.direction as VectorForecastDirection,
    ) &&
    boundedForecastText(
      forecast.directionLabel,
      VECTOR_FORECAST_LABEL_MAX_LENGTH,
    ) &&
    VECTOR_FORECAST_MAGNITUDES.has(
      forecast.magnitude as VectorForecastMagnitude,
    ) &&
    VECTOR_FORECAST_CONVICTIONS.has(
      forecast.conviction as VectorForecastConviction,
    ) &&
    VECTOR_FORECAST_TIMEFRAMES.has(
      forecast.timeframe as VectorForecastTimeframe,
    ) &&
    boundedForecastText(
      forecast.timeframeLabel,
      VECTOR_FORECAST_LABEL_MAX_LENGTH,
    ) &&
    boundedForecastText(
      forecast.summary,
      VECTOR_FORECAST_SUMMARY_MAX_LENGTH,
    ) &&
    Array.isArray(basis) &&
    basis.length > 0 &&
    basis.length <= VECTOR_FORECAST_BASIS_MAX_ITEMS &&
    basis.every(item =>
      boundedForecastText(
        item,
        VECTOR_FORECAST_BASIS_ITEM_MAX_LENGTH,
      )
    ) &&
    Number.isFinite(asOf) &&
    Number.isFinite(completedBarAt) &&
    completedBarAt - asOf === 10 * 60_000
  );
}

/** Compare serialized timestamps by their UTC instant, never text format. */
export function sameUtcInstant(
  left: string | null | undefined,
  right: string | null | undefined,
) {
  const leftTime = Date.parse(String(left || ""));
  const rightTime = Date.parse(String(right || ""));
  return Number.isFinite(leftTime) &&
    Number.isFinite(rightTime) &&
    leftTime === rightTime;
}

/** A current after-hours publication must describe the requested close. */
export function isVector10mForecastForTarget(
  value: unknown,
  targetBarAt: string | null,
): value is Vector10mForecast {
  if (!isVector10mForecast(value) || !targetBarAt) return false;
  return sameUtcInstant(value.completedBarAt, targetBarAt);
}

/**
 * A saved forecast must come from the final complete derived bucket of the
 * listing-venue session. Most venues land exactly on the official close; a
 * session such as NSE's 09:15–15:30 window leaves a final complete 10-minute
 * bucket at 15:25, so accepting only the official bell would discard valid
 * foreign-market evidence.
 */
export function isVector10mRegularSessionCloseForecast(
  value: unknown,
): value is Vector10mForecast {
  if (!isVector10mForecast(value)) return false;
  const completed = Date.parse(value.completedBarAt);
  if (!Number.isFinite(completed)) return false;
  const forecast = value as Vector10mForecast;
  const policy: SessionPolicy = {
    instrumentType: forecast.instrumentType || "EQUITY",
    // Forecasts written before venue metadata was added are legacy U.S.
    // Tensor payloads. Preserve that contract while newer foreign payloads
    // resolve from their explicit exchange/timezone metadata.
    exchange: forecast.exchange || (!forecast.timezone ? "NASDAQ" : undefined),
    exchangeTimezone: forecast.timezone || undefined,
  };
  const profile = exchangeSessionProfile(policy);
  if (!profile || (profile.kind !== "us-security" && profile.kind !== "foreign-security"))
    return false;
  const clock = exchangeClock(new Date(completed), policy);
  if (!isExchangeMarketDate(clock.dateKey, policy)) return false;
  const canonicalClose = Date.parse(
    exchangeDateTimeUtc(clock.dateKey, profile.regularCloseMinutes, policy) || "",
  );
  const lastFullCloseMinutes = profile.regularOpenMinutes +
    Math.floor(
      (profile.regularCloseMinutes - profile.regularOpenMinutes) / 10,
    ) * 10;
  const lastCompleteBucketClose = Date.parse(
    exchangeDateTimeUtc(clock.dateKey, lastFullCloseMinutes, policy) || "",
  );
  return completed === canonicalClose || completed === lastCompleteBucketClose;
}

export type VectorGestaltFrame = {
  interval: string;
  label: string;
  role: GestaltFrameRole;
  source: "selected chart" | "derived from selected history";
  asOf: number | null;
  bars: number;
  direction: GestaltDirection;
  phase: GestaltPhase;
  evidenceStrength: GestaltEvidenceStrength;
  alignment: "selected" | "aligned" | "opposes" | "mixed" | "unavailable";
  basis: string;
};

export type VectorGestaltTransition = {
  time: number;
  direction: GestaltDirection;
  event: string;
  from: GestaltPhase;
  to: GestaltPhase;
  reason: string;
};

/**
 * A compact, result-only chart read.  The wording is deliberately
 * deterministic: it is generated from the completed-bar state and the
 * observable chart fields, while the reconstruction rules remain internal.
 */
export type VectorChartRead = {
  signal: string;
  trend: string;
  health: string;
  momentum: string;
  structure: string;
  participation: string;
  expectation: string;
  bottomLine: string;
  statement: string;
  framing: "constructive" | "defensive" | "watch" | "neutral";
};

export type VectorGestaltState = {
  version: typeof VECTOR_GESTALT_VERSION;
  /** Internal evidence state retained for marker lineage and diagnostics. */
  phase: GestaltPhase;
  /** Internal directional state; the public conclusion is `prediction`. */
  direction: GestaltDirection;
  summary: string;
  prediction: VectorForecast;
  chartRead: VectorChartRead;
  evidenceStrength: GestaltEvidenceStrength;
  manualReviewRequired: boolean;
  reviewReason: string | null;
  selectedFrame: VectorGestaltFrame;
  fast: {
    direction: GestaltDirection;
    event: string;
    ageBars: number | null;
    persistenceBars: number;
    source: string;
  };
  slow: {
    direction: GestaltDirection;
    regime: "bullish" | "bearish" | "mixed";
    persistenceBars: number;
    source: string;
  };
  episode: {
    direction: "bullish" | "bearish" | null;
    lifecycle: AnnaReplicaBar["callLifecycle"];
    id: string | null;
    ageBars: number | null;
    lastPrimaryEventAge: number | null;
    repeatOrdinal: number;
  };
  benchmark: {
    bullishVotes: number;
    bearishVotes: number;
    totalVotes: number;
    alignedShare: number | null;
    participation: "expanding" | "normal" | "weak" | "unavailable";
    volatility: "compression" | "release" | "expansion" | "neutral" | "unknown";
    location: "bullish" | "bearish" | "neutral" | "unavailable";
  };
  timeframe: {
    selected: VectorGestaltFrame;
    contexts: VectorGestaltFrame[];
    agreement: "aligned" | "conflicted" | "partial" | "unavailable";
    basis: string;
  };
  policy: {
    status:
      | "no-call"
      | "forming"
      | "local-confirmation"
      | "active-episode"
      | "review-gated"
      | "insufficient-evidence";
    primaryEvent: string;
    abstains: boolean;
    reason: string | null;
  };
  qualityValidator: {
    source: "Vector native four-family quality";
    relationship: "supports" | "opposes" | "mixed" | "unavailable";
    state:
      | "VECTOR_BUY"
      | "VECTOR_SELL"
      | "SETUP_FORMING"
      | "REVERSAL_WINDOW"
      | "CONFLICT"
      | "NEUTRAL"
      | null;
    direction: GestaltDirection | null;
    resultant: number | null;
    coherence: number | null;
    reason: string;
  };
  reasons: string[];
  vetoes: string[];
  transitions: VectorGestaltTransition[];
};

export type VectorGestaltSourceBar = {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
};

type SourceBar = VectorGestaltSourceBar;

type SourceHistory = {
  symbol?: string;
  currency?: string;
  exchange?: string | null;
  instrumentType?: string | null;
  bars: VectorGestaltSourceBar[];
  interval: string;
  intervalLabel?: string;
  timezone?: string | null;
  latestBarOpen?: boolean;
};

type DerivedReplicaMetadata = Pick<
  AnnaReplica,
  "symbol" | "currency" | "exchange" | "timezone"
>;

type FramePoint = {
  bar: AnnaReplicaBar;
  index: number;
  direction: GestaltDirection;
  phase: GestaltPhase;
  evidenceStrength: GestaltEvidenceStrength;
  fastDirection: GestaltDirection;
  slowDirection: GestaltDirection;
  event: string;
  slowPersistenceBars: number;
  fastPersistenceBars: number;
  fastEventAge: number | null;
  episodeAge: number | null;
  episodeExpired: boolean;
  reasons: string[];
  vetoes: string[];
};

type NativeQuality = NonNullable<AnnaReplica["structure"]>["nativeQuality"];
type NativeQualityValidator = VectorGestaltState["qualityValidator"];

type FrameSpec = {
  interval: string;
  label: string;
  role: GestaltFrameRole;
};

const FRAME_HIERARCHY: Record<string, readonly FrameSpec[]> = {
  "2m": [
    { interval: "1h", label: "1-hour", role: "swing" },
    { interval: "4h", label: "4-hour", role: "swing" },
    { interval: "1d", label: "Daily", role: "higher-horizon" },
  ],
  "5m": [
    { interval: "1h", label: "1-hour", role: "swing" },
    { interval: "4h", label: "4-hour", role: "swing" },
    { interval: "1d", label: "Daily", role: "higher-horizon" },
  ],
  "10m": [
    { interval: "1h", label: "1-hour", role: "swing" },
    { interval: "4h", label: "4-hour", role: "swing" },
    { interval: "1d", label: "Daily", role: "higher-horizon" },
  ],
  "1h": [
    { interval: "4h", label: "4-hour", role: "swing" },
    { interval: "1d", label: "Daily", role: "higher-horizon" },
    { interval: "1wk", label: "Weekly", role: "higher-horizon" },
  ],
  "2h": [
    { interval: "4h", label: "4-hour", role: "swing" },
    { interval: "1d", label: "Daily", role: "higher-horizon" },
    { interval: "1wk", label: "Weekly", role: "higher-horizon" },
  ],
  "4h": [
    { interval: "1d", label: "Daily", role: "higher-horizon" },
    { interval: "1wk", label: "Weekly", role: "higher-horizon" },
  ],
  "1d": [{ interval: "1wk", label: "Weekly", role: "higher-horizon" }],
  "1wk": [],
};

const FRAME_SECONDS: Record<string, number> = {
  "2m": 120,
  "5m": 300,
  "10m": 600,
  "1h": 3_600,
  "2h": 7_200,
  "4h": 14_400,
  "1d": 86_400,
  "1wk": 604_800,
};
const INTRADAY_SOURCE_INTERVALS = new Set([
  "2m",
  "5m",
  "10m",
  "1h",
  "2h",
  "4h",
]);

function finite(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

function opposite(left: GestaltDirection, right: GestaltDirection) {
  return (
    (left === "bullish" && right === "bearish") ||
    (left === "bearish" && right === "bullish")
  );
}

function markerDirection(
  markers: AnnaReplicaBar["primaryMarkers"],
): GestaltDirection {
  const bullish = markers.some((marker) => marker.startsWith("buy"));
  const bearish = markers.some((marker) => marker.startsWith("sell"));
  if (bullish && bearish) return "mixed";
  if (bullish) return "bullish";
  if (bearish) return "bearish";
  return "neutral";
}

function stateDirection(value: string | null | undefined): GestaltDirection {
  return value === "bullish" || value === "bearish" ? value : "mixed";
}

function eventLabel(bar: AnnaReplicaBar): string {
  if (bar.primaryMarkers.length) {
    return bar.primaryMarkers
      .map((marker) => marker.replaceAll("-", " "))
      .join(" + ");
  }
  if (bar.warningMarker) return "fast/slow warning";
  if (bar.dcbMarker) return `DCB ${bar.dcbMarker} candidate`;
  if (bar.weakMarker === "B") return "weak buy candidate";
  if (bar.weakMarker === "W1") return "watch candidate";
  if (bar.utEvent) return bar.utEvent.replaceAll("_", " ");
  if (bar.waveTrendEvent) return bar.waveTrendEvent.replaceAll("_", " ");
  return "no new event";
}

function benchmarkDirection(bar: AnnaReplicaBar): GestaltDirection {
  if (bar.totalVotes <= 0) return "neutral";
  if (bar.bullishVotes > bar.bearishVotes) return "bullish";
  if (bar.bearishVotes > bar.bullishVotes) return "bearish";
  return "mixed";
}

function participationState(
  bar: AnnaReplicaBar,
): "expanding" | "normal" | "weak" | "unavailable" {
  if (!finite(bar.rvol)) return "unavailable";
  if (bar.rvol >= 1.2) return "expanding";
  if (bar.rvol < 0.75) return "weak";
  return "normal";
}

function normalizedSqueezeMomentum(bar: AnnaReplicaBar) {
  const momentum = finite(bar.squeezeMomentum)
    ? Math.abs(bar.squeezeMomentum)
    : null;
  if (!finite(momentum)) return null;
  const atr = bar.vectorStructuralLocation?.atr;
  if (!finite(atr) || atr <= 0) return null;
  return momentum / atr;
}

function volatilityState(
  bar: AnnaReplicaBar,
  previous: AnnaReplicaBar | undefined,
): "compression" | "release" | "expansion" | "neutral" | "unknown" {
  if (bar.squeezeOn === null) return "unknown";
  if (bar.squeezeOn) return "compression";
  if (previous?.squeezeOn === true) return "release";
  const normalizedMomentum = normalizedSqueezeMomentum(bar);
  if (finite(bar.squeezeMomentum) && finite(normalizedMomentum) && normalizedMomentum >= 0.65)
    return "expansion";
  return "neutral";
}

function persistence(
  bars: AnnaReplicaBar[],
  index: number,
  direction: GestaltDirection,
  read: (bar: AnnaReplicaBar) => GestaltDirection,
) {
  if (direction === "mixed" || direction === "neutral") return 0;
  let count = 0;
  for (let cursor = index; cursor >= 0; cursor -= 1) {
    if (read(bars[cursor]) !== direction) break;
    count += 1;
  }
  return count;
}

function lastPrimaryAge(
  bars: AnnaReplicaBar[],
  index: number,
): number | null {
  for (let cursor = index; cursor >= 0; cursor -= 1) {
    if (bars[cursor].primaryMarkers.length) return index - cursor;
  }
  return null;
}

function episodeAge(
  bars: AnnaReplicaBar[],
  index: number,
): number | null {
  const episode = bars[index]?.callEpisode;
  if (!episode) return null;
  let count = 0;
  for (let cursor = index; cursor >= 0; cursor -= 1) {
    if (bars[cursor].callEpisode !== episode) break;
    count += 1;
  }
  return count;
}

function inheritedEpisodeExpired(bar: AnnaReplicaBar) {
  return Boolean(
    bar.activeCall &&
      !bar.primaryMarkers.length &&
      finite(bar.lastPrimaryEventAge) &&
      bar.lastPrimaryEventAge > VECTOR_FORECAST_EPISODE_MAX_AGE_BARS,
  );
}

function primaryDirection(bar: AnnaReplicaBar) {
  return markerDirection(bar.primaryMarkers);
}

function phaseFor(
  bar: AnnaReplicaBar,
  fast: GestaltDirection,
  slow: GestaltDirection,
  benchmark: GestaltDirection,
): { phase: GestaltPhase; reasons: string[]; vetoes: string[] } {
  const reasons: string[] = [];
  const vetoes: string[] = [];
  const primary = primaryDirection(bar);
  const primaryOpposesSlow =
    primary !== "neutral" && primary !== "mixed" && opposite(primary, slow);
  const benchmarkOpposesPrimary =
    primary !== "neutral" &&
    primary !== "mixed" &&
    benchmark !== "neutral" &&
    benchmark !== "mixed" &&
    opposite(primary, benchmark) &&
    Math.max(bar.bullishVotes, bar.bearishVotes) >= 4;
  const fastSlowConflict = opposite(fast, slow);

  if (bar.warningMarker || primaryOpposesSlow || fastSlowConflict) {
    if (bar.warningMarker) reasons.push("A fast component is warning against the slow state.");
    if (primaryOpposesSlow) reasons.push("The primary event does not agree with the slow state.");
    if (fastSlowConflict) reasons.push("Fast and slow directions are opposed.");
    vetoes.push("Do not collapse a fast reversal into a clean directional state.");
    return { phase: "conflict", reasons, vetoes };
  }

  if (inheritedEpisodeExpired(bar)) {
    reasons.push(
      "The inherited primary event has aged beyond Tensor's forecast window.",
    );
    vetoes.push("Require a new completed primary event before restoring forecast authority.");
    return { phase: "neutral", reasons, vetoes };
  }

  if (benchmarkOpposesPrimary) {
    reasons.push("The seven-part benchmark is majority-opposed to the primary event.");
    vetoes.push("Benchmark disagreement prevents a clean reconstruction.");
    return { phase: "conflict", reasons, vetoes };
  }

  if (bar.dcbMarker || bar.dcbActive || bar.weakMarker === "W1") {
    reasons.push("A reversal or dead-cat-bounce candidate is active without primary confirmation.");
    vetoes.push("A reversal candidate is watch-only until the later state resolves it.");
    return { phase: "reversal-window", reasons, vetoes };
  }

  if (primary !== "neutral" && primary !== "mixed") {
    if (
      primary === slow &&
      benchmark === primary &&
      bar.totalVotes >= 5 &&
      Math.max(bar.bullishVotes, bar.bearishVotes) / bar.totalVotes >= 0.71
    ) {
      reasons.push("Primary event, slow state and benchmark majority agree on a completed bar.");
      return { phase: "confirmed", reasons, vetoes };
    }
    reasons.push("A primary event exists, but the full confirmation gate is incomplete.");
    vetoes.push("Wait for slow-state and benchmark agreement before treating it as resolved.");
    return { phase: "forming", reasons, vetoes };
  }

  if (bar.activeCall) {
    if (opposite(stateDirection(bar.fastState), bar.activeCall)) {
      reasons.push("The active episode persists while fast momentum begins to oppose it.");
      vetoes.push("Treat the episode as exhausting until a completed opposite event appears.");
      return { phase: "exhausting", reasons, vetoes };
    }
    reasons.push("The prior primary event persists as one evolving episode.");
    return { phase: "active", reasons, vetoes };
  }

  if (bar.utEvent || bar.waveTrendEvent) {
    reasons.push("A fast component changed state without a primary marker.");
    vetoes.push("Fast timing alone is not a primary call.");
    return { phase: "fast-reversal", reasons, vetoes };
  }

  if (
    bar.weakMarker === "B" ||
    (fast === slow &&
      (fast === "bullish" || fast === "bearish") &&
      bar.totalVotes >= 4)
  ) {
    reasons.push("Directional evidence is forming without a primary event.");
    vetoes.push("The primary marker gate has not fired.");
    return { phase: "forming", reasons, vetoes };
  }

  return { phase: "neutral", reasons, vetoes };
}

function directionFor(
  bar: AnnaReplicaBar,
  fast: GestaltDirection,
  slow: GestaltDirection,
  benchmark: GestaltDirection,
): GestaltDirection {
  const primary = primaryDirection(bar);
  if (primary !== "neutral") return primary;
  if (bar.activeCall && !inheritedEpisodeExpired(bar)) return bar.activeCall;
  if (bar.warningMarker) return "mixed";
  if (fast === slow && fast !== "mixed" && fast !== "neutral") return fast;
  if (benchmark !== "mixed" && benchmark !== "neutral") return benchmark;
  if (fast !== "neutral" && fast !== "mixed") return fast;
  return "neutral";
}

function evidenceFor(
  bar: AnnaReplicaBar,
  phase: GestaltPhase,
  timeframeAgreement: "aligned" | "conflicted" | "partial" | "unavailable" = "unavailable",
): GestaltEvidenceStrength {
  if (bar.totalVotes < 4 || phase === "unavailable") return "insufficient";
  if (phase === "conflict" || timeframeAgreement === "conflicted") return "limited";
  const share = Math.max(bar.bullishVotes, bar.bearishVotes) / bar.totalVotes;
  if (phase === "confirmed" && share >= 0.85 && timeframeAgreement !== "partial")
    return "strong";
  if (
    (phase === "confirmed" || phase === "active" || phase === "forming") &&
    share >= 0.71
  )
    return "moderate";
  return "limited";
}

function buildPoint(bars: AnnaReplicaBar[], index: number): FramePoint {
  const bar = bars[index];
  const fast = stateDirection(bar.fastState);
  const slow = stateDirection(bar.slowState);
  const benchmark = benchmarkDirection(bar);
  const classification = phaseFor(bar, fast, slow, benchmark);
  return {
    bar,
    index,
    direction: directionFor(bar, fast, slow, benchmark),
    phase: classification.phase,
    evidenceStrength: evidenceFor(bar, classification.phase),
    fastDirection: fast,
    slowDirection: slow,
    event: eventLabel(bar),
    slowPersistenceBars: persistence(bars, index, slow, (item) =>
      stateDirection(item.slowState),
    ),
    fastPersistenceBars: persistence(bars, index, fast, (item) =>
      stateDirection(item.fastState),
    ),
    fastEventAge: bar.primaryMarkers.length
      ? 0
      : bar.lastPrimaryEventAge ?? lastPrimaryAge(bars, index),
    episodeAge: episodeAge(bars, index),
    episodeExpired: inheritedEpisodeExpired(bar),
    reasons: classification.reasons,
    vetoes: classification.vetoes,
  };
}

function frameRole(interval: string): GestaltFrameRole {
  if (["2m", "5m", "10m"].includes(interval)) return "timing";
  if (["1h", "2h", "4h"].includes(interval)) return "swing";
  return "higher-horizon";
}

function frameLabel(interval: string, fallback?: string) {
  if (fallback) return fallback;
  return (
    {
      "2m": "2-minute",
      "5m": "5-minute",
      "10m": "10-minute",
      "1h": "1-hour",
      "2h": "2-hour",
      "4h": "4-hour",
      "1d": "Daily",
      "1wk": "Weekly",
    }[interval] ?? interval
  );
}

function alignmentFor(
  selected: GestaltDirection,
  direction: GestaltDirection,
): VectorGestaltFrame["alignment"] {
  if (direction === "mixed" || direction === "neutral") return "mixed";
  if (selected === direction) return "aligned";
  if (opposite(selected, direction)) return "opposes";
  return "mixed";
}

function frameFromReplica(
  replica: AnnaReplica,
  source: VectorGestaltFrame["source"],
  selectedDirection: GestaltDirection | null = null,
): VectorGestaltFrame {
  const bars = replica.bars.filter((bar) => bar.barFinality === "closed");
  const latest = bars.at(-1);
  if (!latest) {
    return {
      interval: replica.interval,
      label: frameLabel(replica.interval, replica.intervalLabel),
      role: frameRole(replica.interval),
      source,
      asOf: null,
      bars: 0,
      direction: "neutral",
      phase: "unavailable",
      evidenceStrength: "insufficient",
      alignment: "unavailable",
      basis: "No completed bars were available for this frame.",
    };
  }
  if (
    source === "derived from selected history" &&
    bars.length < VECTOR_CONTEXT_MINIMUM_BARS
  ) {
    return {
      interval: replica.interval,
      label: frameLabel(replica.interval, replica.intervalLabel),
      role: frameRole(replica.interval),
      source,
      asOf: latest.timestamp,
      bars: bars.length,
      direction: "neutral",
      phase: "unavailable",
      evidenceStrength: "insufficient",
      alignment: "unavailable",
      basis: `Derived frame has ${bars.length} completed bars; ${VECTOR_CONTEXT_MINIMUM_BARS} are required before it can qualify the forecast.`,
    };
  }
  const point = buildPoint(bars, bars.length - 1);
  return {
    interval: replica.interval,
    label: frameLabel(replica.interval, replica.intervalLabel),
    role: frameRole(replica.interval),
    source,
    asOf: latest.timestamp,
    bars: bars.length,
    direction: point.direction,
    phase: point.phase,
    evidenceStrength: point.evidenceStrength,
    alignment:
      selectedDirection === null
        ? "selected"
        : alignmentFor(selectedDirection, point.direction),
    basis:
      source === "selected chart"
        ? "Selected completed chart frame."
        : "Derived from completed source bars; not an independent feed.",
  };
}

function timeframeAgreement(
  selected: VectorGestaltFrame,
  contexts: VectorGestaltFrame[],
): "aligned" | "conflicted" | "partial" | "unavailable" {
  const observed = contexts.filter(
    (frame) =>
      frame.asOf !== null &&
      frame.phase !== "unavailable" &&
      frame.evidenceStrength !== "insufficient",
  );
  if (!observed.length) return "unavailable";
  if (selected.direction === "neutral" || selected.direction === "mixed")
    return "partial";
  if (observed.some((frame) => frame.alignment === "opposes")) return "conflicted";
  if (observed.every((frame) => frame.alignment === "aligned")) return "aligned";
  return "partial";
}

function eventDirectionForForecast(bar: AnnaReplicaBar): GestaltDirection | null {
  const primary = primaryDirection(bar);
  if (primary === "bullish" || primary === "bearish") return primary;
  if (bar.dcbMarker === "buy") return "bullish";
  if (bar.dcbMarker === "sell") return "bearish";
  if (bar.utEvent === "buy_flip" || bar.waveTrendEvent === "bull_cross")
    return "bullish";
  if (bar.utEvent === "sell_flip" || bar.waveTrendEvent === "bear_cross")
    return "bearish";
  if (bar.fastState === "bullish" || bar.fastState === "bearish")
    return bar.fastState;
  return null;
}

function forecastDirectionFor(
  point: FramePoint,
  bar: AnnaReplicaBar,
  previous: AnnaReplicaBar | undefined,
  agreement: "aligned" | "conflicted" | "partial" | "unavailable",
): VectorForecastDirection {
  if (
    point.phase === "conflict" ||
    agreement === "conflicted" ||
    point.direction === "mixed" ||
    bar.warningMarker
  )
    return "crosscurrents";
  if (point.episodeExpired) return "range";

  const eventDirection = eventDirectionForForecast(bar);
  const reversalCandidate =
    point.phase === "reversal-window" ||
    point.phase === "exhausting" ||
    (point.phase === "fast-reversal" &&
      eventDirection !== null &&
      opposite(eventDirection, point.slowDirection)) ||
    bar.callLifecycle === "reversed" ||
    (eventDirection !== null &&
      previous?.activeCall !== null &&
      previous?.activeCall !== undefined &&
      opposite(eventDirection, previous.activeCall)) ||
    (eventDirection !== null &&
      previous?.slowState !== undefined &&
      opposite(eventDirection, stateDirection(previous.slowState)));

  if (reversalCandidate) {
    const reversalDirection =
      point.phase === "exhausting" &&
      (point.fastDirection === "bullish" || point.fastDirection === "bearish")
        ? point.fastDirection
        : eventDirection;
    if (reversalDirection === "bullish") return "higher-reversal";
    if (reversalDirection === "bearish") return "lower-reversal";
    return "crosscurrents";
  }

  const projected =
    eventDirection === "bullish" || eventDirection === "bearish"
      ? eventDirection
      : point.direction;
  if (projected === "bullish") return "higher-continuation";
  if (projected === "bearish") return "lower-continuation";
  return "range";
}

function forecastDirectionLabel(direction: VectorForecastDirection) {
  return {
    "higher-continuation": "Higher · continuation",
    "higher-reversal": "Higher · reversal attempt",
    range: "Range-bound",
    crosscurrents: "Crosscurrents",
    "lower-reversal": "Lower · reversal attempt",
    "lower-continuation": "Lower · continuation",
  }[direction];
}

function forecastTimeframeLabel(timeframe: VectorForecastTimeframe) {
  return {
    "current-session": "Current / extended session",
    "next-session": "Next session",
    "next-2-5-sessions": "Next 2–5 sessions",
    "next-1-4-weeks": "Next 1–4 weeks",
    "longer-regime": "Longer regime",
  }[timeframe];
}

function forecastTimeframeFor(
  selected: VectorGestaltFrame,
  contexts: VectorGestaltFrame[],
  agreement: "aligned" | "conflicted" | "partial" | "unavailable",
  phase: GestaltPhase,
): VectorForecastTimeframe {
  if (selected.interval === "1wk") return "longer-regime";
  if (selected.interval === "1d") return "next-1-4-weeks";
  if (["1h", "2h", "4h"].includes(selected.interval))
    return "next-2-5-sessions";
  if (selected.interval === "10m") return "next-session";
  const alignedSwingContext = contexts.some(
    (frame) =>
      frame.role === "swing" &&
      frame.alignment === "aligned" &&
      frame.evidenceStrength !== "insufficient",
  );
  if (
    agreement === "aligned" &&
    alignedSwingContext &&
    (phase === "confirmed" || phase === "active")
  )
    return "next-session";
  return "current-session";
}

function percentileRank(values: number[], value: number | null) {
  if (!finite(value) || !values.length) return null;
  const valid = values.filter(finite).sort((left, right) => left - right);
  if (!valid.length) return null;
  return valid.filter((candidate) => candidate <= value).length / valid.length;
}

function forecastMagnitudeFor(
  bars: AnnaReplicaBar[],
  direction: VectorForecastDirection,
): VectorForecastMagnitude {
  const latest = bars.at(-1)!;
  const previous = bars.at(-2);
  const volatility = volatilityState(latest, previous);
  const atr = latest.vectorStructuralLocation?.atr;
  const atrRatio =
    finite(atr) && atr > 0 && finite(latest.close) && latest.close > 0
      ? atr / latest.close
      : null;
  const atrRatios = bars
    .slice(-60)
    .map((bar) => {
      const value = bar.vectorStructuralLocation?.atr;
      return finite(value) && value > 0 && finite(bar.close) && bar.close > 0
        ? value / bar.close
        : null;
    })
    .filter((value): value is number => finite(value));
  const atrRank = percentileRank(atrRatios, atrRatio);
  const ribbonWidths = bars
    .slice(-60)
    .map((bar) => bar.ribbonWidth)
    .filter((value): value is number => finite(value));
  const ribbonRank = percentileRank(
    ribbonWidths,
    finite(latest.ribbonWidth) ? latest.ribbonWidth : null,
  );
  const momentumAtr =
    finite(latest.squeezeMomentum) && finite(atr) && atr > 0
      ? Math.abs(latest.squeezeMomentum) / atr
      : null;
  let score =
    volatility === "release"
      ? 2.5
      : volatility === "expansion"
        ? 1.5
        : volatility === "compression"
          ? -2
          : 0;

  if (finite(atrRank)) {
    if (atrRank >= 0.85) score += 2;
    else if (atrRank >= 0.65) score += 1;
    else if (atrRank <= 0.25) score -= 1;
  }
  if (finite(momentumAtr)) {
    if (momentumAtr >= 1.25) score += 2;
    else if (momentumAtr >= 0.65) score += 1;
  }
  if (finite(latest.rvol)) {
    if (latest.rvol >= 1.6) score += 2;
    else if (latest.rvol >= 1.2) score += 1;
    else if (latest.rvol < 0.75) score -= 1;
  }
  if (finite(latest.adx)) {
    if (latest.adx >= 45) score += 1.5;
    else if (latest.adx >= 30) score += 1;
    else if (latest.adx < 18) score -= 0.5;
  }
  if (finite(ribbonRank)) {
    if (ribbonRank >= 0.85) score += 1;
    else if (ribbonRank <= 0.25) score -= 0.5;
  }
  if (latest.stratType === "3") score += 1;
  if (latest.stratType === "1") score -= 0.5;

  const location = latest.vectorStructuralLocation;
  const room =
    direction === "higher-continuation" || direction === "higher-reversal"
      ? location?.roomToSupplyAtr
      : direction === "lower-continuation" || direction === "lower-reversal"
        ? location?.roomToDemandAtr
        : null;
  const breakingRange =
    location?.trigger === "range-breakout" ||
    location?.trigger === "range-breakdown";
  if (finite(room)) {
    if (room >= 2.5) score += 0.5;
    else if (room < 0.5 && !breakingRange) score -= 1;
  }
  if (direction === "range" && volatility === "compression") score -= 0.5;

  if (score >= 7) return "extreme";
  if (score >= 3.5) return "large";
  if (score <= -1.5) return "quiet";
  return "normal";
}

function forecastDirectionalBias(
  direction: VectorForecastDirection,
): "bullish" | "bearish" | null {
  if (direction === "higher-continuation" || direction === "higher-reversal")
    return "bullish";
  if (direction === "lower-continuation" || direction === "lower-reversal")
    return "bearish";
  return null;
}

function nativeQualityValidatorFor(
  direction: VectorForecastDirection,
  nativeQuality: NativeQuality | null | undefined,
): NativeQualityValidator {
  const source = "Vector native four-family quality" as const;
  if (!nativeQuality)
    return {
      source,
      relationship: "unavailable",
      state: null,
      direction: null,
      resultant: null,
      coherence: null,
      reason: "The additive native quality read is unavailable.",
    };
  const common = {
    source,
    state: nativeQuality.state,
    direction: nativeQuality.direction,
    resultant: nativeQuality.resultant,
    coherence: nativeQuality.coherence,
  };
  const forecastBias = forecastDirectionalBias(direction);
  if (!forecastBias)
    return {
      ...common,
      relationship: "mixed",
      reason:
        "The native quality read is retained as context because this forecast has no one-way directional bias.",
    };
  if (
    (nativeQuality.direction !== "bullish" &&
      nativeQuality.direction !== "bearish") ||
    !finite(nativeQuality.resultant) ||
    Math.abs(nativeQuality.resultant) < 15 ||
    !finite(nativeQuality.coherence) ||
    nativeQuality.coherence < 0.55
  )
    return {
      ...common,
      relationship: "mixed",
      reason:
        "The native quality families do not resolve a sufficiently coherent directional check.",
    };
  if (nativeQuality.direction === forecastBias)
    return {
      ...common,
      relationship: "supports",
      reason:
        "The native trend, momentum, location, and participation quality check points the same way.",
    };
  return {
    ...common,
    relationship: "opposes",
    reason:
      "The native trend, momentum, location, and participation quality check opposes the forecast path.",
  };
}

function forecastConvictionFor(
  bar: AnnaReplicaBar,
  point: FramePoint,
  direction: VectorForecastDirection,
  evidenceStrength: GestaltEvidenceStrength,
  agreement: "aligned" | "conflicted" | "partial" | "unavailable",
  volatility: ReturnType<typeof volatilityState>,
  policyAbstains: boolean,
  qualityValidator: NativeQualityValidator,
): VectorForecastConviction {
  let score =
    evidenceStrength === "strong"
      ? 4
      : evidenceStrength === "moderate"
        ? 3
        : evidenceStrength === "limited"
          ? 1
          : 0;
  const crosscurrents = direction === "crosscurrents";
  const range = direction === "range";

  if (crosscurrents) {
    if (point.phase === "conflict") score += 2;
    if (agreement === "conflicted") score += 2;
    if (bar.warningMarker) score += 1;
  } else {
    if (point.phase === "confirmed") score += 2;
    else if (point.phase === "active") score += 1;
    else if (point.phase === "neutral" && range) score += 1;
    if (agreement === "aligned") score += 2;
    else if (agreement === "unavailable") score -= 1;
  }

  const directionalBias = forecastDirectionalBias(direction);
  const alignedShare =
    bar.totalVotes > 0 && directionalBias
      ? (directionalBias === "bullish"
          ? bar.bullishVotes
          : bar.bearishVotes) / bar.totalVotes
      : null;
  if (finite(alignedShare)) {
    if (alignedShare >= 0.85) score += 1;
    else if (alignedShare < 0.5) score -= 2;
    else if (alignedShare < 0.57) score -= 0.5;
  }
  if (bar.primaryMarkers.length) score += 1;
  if (finite(bar.rvol)) {
    if (bar.rvol >= 1.2) score += 0.5;
    else if (bar.rvol < 0.75) score -= 0.5;
  }
  if (range && volatility === "compression") score += 2;

  const location = bar.vectorStructuralLocation?.bias;
  if (directionalBias && location === directionalBias) score += 0.5;
  else if (directionalBias && location && location !== "neutral") score -= 1;

  const scored = score >= 7 ? "high" : score >= 4 ? "moderate" : "low";
  // Abstention and an opposing additive quality check can reduce authority,
  // but the native layer never replaces or suppresses the raw marker.
  if (
    policyAbstains ||
    crosscurrents ||
    qualityValidator.relationship === "opposes"
  ) return "low";
  return scored;
}

function forecastBasis(
  prediction: Pick<VectorForecast, "direction" | "magnitude" | "conviction">,
  point: FramePoint,
  selected: VectorGestaltFrame,
  agreement: "aligned" | "conflicted" | "partial" | "unavailable",
  volatility: ReturnType<typeof volatilityState>,
  qualityValidator: NativeQualityValidator,
) {
  const direction =
    prediction.direction === "crosscurrents"
      ? "Fast, slow, structural, or higher-frame evidence is opposed."
      : prediction.direction === "range"
        ? "No completed-bar directional expansion has cleared the evidence gate."
        : prediction.direction.includes("reversal")
          ? "Fast timing is turning against the prior slower path."
          : "Completed-bar timing and the slower path point the same way.";
  const magnitude =
    prediction.magnitude === "quiet"
      ? "Volatility and participation imply a contained move."
      : prediction.magnitude === "normal"
        ? "Volatility and participation remain near their ordinary range."
        : prediction.magnitude === "large"
          ? "Expansion, participation, or available structural room supports a larger move."
          : "Several expansion measures are simultaneously elevated.";
  const conviction = `${titleCase(prediction.conviction)} conviction reflects ${point.evidenceStrength} local evidence and ${agreement} higher-frame agreement.`;
  const horizon = `${selected.label} timing sets the forecast horizon; derived higher frames qualify it rather than override it.`;
  const volatilityNote =
    volatility === "unknown" ? "Volatility state is still warming." : null;
  return [
    direction,
    magnitude,
    conviction,
    horizon,
    qualityValidator.reason,
    volatilityNote,
  ].filter((value): value is string => Boolean(value));
}

function forecastContextFor(
  bar: AnnaReplicaBar,
  agreement: "aligned" | "conflicted" | "partial" | "unavailable",
): TensorForecastContext {
  const context = bar.tensorContext;
  const pattern = context?.primaryPattern ?? null;
  return {
    cycleState: context?.cycle.state ?? "UNAVAILABLE",
    cycleDirection: context?.cycle.direction ?? "neutral",
    cycleAgeBars: context?.cycle.ageBars ?? null,
    patternLabel: pattern?.label ?? null,
    patternDirection: pattern?.direction ?? null,
    patternSampleCount: pattern?.stats.sampleCount ?? null,
    patternEdge10: pattern?.stats.edgePct ?? null,
    patternUpRate10: pattern?.stats.upRatePct ?? null,
    patternEvidence: pattern?.stats.status ?? "unavailable",
    timeframeAgreement: agreement,
  };
}

function forecastContextBasis(
  bar: AnnaReplicaBar,
  context: TensorForecastContext,
) {
  const basis: string[] = [];
  if (context.cycleState === "BULL_SHIFT")
    basis.push("The targeted cycle lane just shifted bullish on the completed bar.");
  else if (context.cycleState === "BEAR_SHIFT")
    basis.push("The targeted cycle lane just shifted bearish on the completed bar.");
  else if (context.cycleState === "BULL_STRONG")
    basis.push("The targeted cycle lane is bullish with momentum agreement.");
  else if (context.cycleState === "BEAR_STRONG")
    basis.push("The targeted cycle lane is bearish with momentum agreement.");
  else if (context.cycleState === "BULL_WEAK" || context.cycleState === "BEAR_WEAK")
    basis.push("The targeted cycle lane is directional but momentum is diverging.");

  const pattern = bar.tensorContext?.primaryPattern;
  if (pattern) {
    const edge = pattern.stats.edgePct;
    if (pattern.stats.status === "usable" && finite(edge)) {
      const sign = edge >= 0 ? "+" : "";
      basis.push(
        `${pattern.label} has a ${sign}${edge.toFixed(2)}% historical ${pattern.stats.horizonBars}-bar edge versus baseline (n=${pattern.stats.sampleCount}).`,
      );
    } else {
      basis.push(
        `${pattern.label} is present; historical edge is still warming (n=${pattern.stats.sampleCount}).`,
      );
    }
  }
  if (context.timeframeAgreement === "conflicted")
    basis.push("Higher-frame context remains conflicted; this lane does not override it.");
  return basis;
}

function buildForecast(
  bars: AnnaReplicaBar[],
  point: FramePoint,
  selected: VectorGestaltFrame,
  contexts: VectorGestaltFrame[],
  agreement: "aligned" | "conflicted" | "partial" | "unavailable",
  evidenceStrength: GestaltEvidenceStrength,
  policyAbstains: boolean,
  nativeQuality: NativeQuality | null | undefined,
) {
  const latest = bars.at(-1)!;
  const previous = bars.at(-2);
  const direction = forecastDirectionFor(point, latest, previous, agreement);
  const magnitude = forecastMagnitudeFor(bars, direction);
  const volatility = volatilityState(latest, previous);
  const qualityValidator = nativeQualityValidatorFor(
    direction,
    nativeQuality,
  );
  const conviction = forecastConvictionFor(
    latest,
    point,
    direction,
    evidenceStrength,
    agreement,
    volatility,
    policyAbstains,
    qualityValidator,
  );
  const timeframe = forecastTimeframeFor(selected, contexts, agreement, point.phase);
  const directionLabel = forecastDirectionLabel(direction);
  const timeframeLabel = forecastTimeframeLabel(timeframe);
  const context = forecastContextFor(latest, agreement);
  const contextBasis = forecastContextBasis(latest, context);
  const path =
    direction === "crosscurrents"
      ? "crosscurrents rather than a clean one-way move"
      : direction === "range"
        ? "a range-bound path"
        : directionLabel.toLowerCase();
  const baseSummary = `The completed-bar evidence favors ${path} over the ${timeframeLabel.toLowerCase()}, with ${magnitude} expected magnitude and ${conviction} conviction.`;
  const summary = `${baseSummary}${contextBasis[0] ? ` ${contextBasis[0]}` : ""}`.slice(0, 256);
  const partial = { direction, magnitude, conviction };
  return {
    prediction: {
      direction,
      directionLabel,
      magnitude,
      conviction,
      timeframe,
      timeframeLabel,
      summary,
      basis: [
        ...forecastBasis(
          partial,
          point,
          selected,
          agreement,
          volatility,
          qualityValidator,
        ).slice(0, 4),
        ...contextBasis,
      ].slice(0, 6),
      context,
    } satisfies VectorForecast,
    qualityValidator,
  };
}

function reviewReasons(
  point: FramePoint,
  replica: AnnaReplica,
  agreement: "aligned" | "conflicted" | "partial" | "unavailable",
) {
  const reasons: string[] = [];
  if (point.phase === "conflict") reasons.push("fast/slow or event-state conflict");
  if (point.phase === "reversal-window" || point.phase === "exhausting")
    reasons.push("reversal or exhaustion candidate");
  if (agreement === "conflicted") reasons.push("higher timeframe conflict");
  if (agreement === "partial" || agreement === "unavailable")
    reasons.push("incomplete timeframe arbitration");
  if (replica.read.epochBasis === "pre-evidence backcast")
    reasons.push("epoch is a pre-evidence backcast");
  if (point.evidenceStrength === "insufficient") reasons.push("benchmark still warming");
  return reasons;
}

function policyFor(
  point: FramePoint,
  manualReviewRequired: boolean,
): VectorGestaltState["policy"] {
  const abstains =
    manualReviewRequired ||
    ["unavailable", "neutral", "conflict", "reversal-window", "exhausting"].includes(
      point.phase,
    );
  if (point.evidenceStrength === "insufficient") {
    return {
      status: "insufficient-evidence",
      primaryEvent: point.event,
      abstains: true,
      reason: "The benchmark is not sufficiently warmed to resolve the state.",
    };
  }
  if (manualReviewRequired) {
    return {
      status: "review-gated",
      primaryEvent: point.event,
      abstains: true,
      reason: "A reconstruction conflict or missing hierarchy evidence requires human review.",
    };
  }
  if (point.phase === "confirmed") {
    return {
      status: "local-confirmation",
      primaryEvent: point.event,
      abstains,
      reason: null,
    };
  }
  if (point.phase === "active") {
    return {
      status: "active-episode",
      primaryEvent: point.event,
      abstains,
      reason: "The episode persists, but the latest bar is not a new primary event.",
    };
  }
  if (point.phase === "forming" || point.phase === "fast-reversal") {
    return {
      status: "forming",
      primaryEvent: point.event,
      abstains: true,
      reason: "Components are developing without a resolved primary event.",
    };
  }
  return {
    status: "no-call",
    primaryEvent: point.event,
    abstains,
    reason: "No resolved primary event is present on the latest completed bar.",
  };
}

function titleCase(value: string) {
  return value.length ? `${value[0].toUpperCase()}${value.slice(1)}` : value;
}

function chartSignalFor(bar: AnnaReplicaBar) {
  const buys = bar.primaryMarkers.filter((marker) => marker.startsWith("buy"));
  const sells = bar.primaryMarkers.filter((marker) => marker.startsWith("sell"));
  const context: string[] = [];
  const markerColors = (markers: typeof buys) =>
    markers
      .map((marker) =>
        marker === "buy-cyan"
          ? "cyan"
          : marker === "buy-green"
            ? "green"
            : marker === "sell-magenta"
              ? "magenta"
              : "red",
      )
      .join(" + ");
  let primary = "No fresh signal";
  if (buys.length && sells.length) primary = "Buy and sell signals are colliding";
  else if (buys.length) {
    primary =
      buys.length === 1
        ? `Fresh buy signal · ${markerColors(buys)} diamond`
        : `${buys.length} buy signals are clustered · ${markerColors(buys)} diamonds`;
  } else if (sells.length) {
    primary =
      sells.length === 1
        ? `Fresh sell signal · ${markerColors(sells)} diamond`
        : `${sells.length} sell signals are clustered · ${markerColors(sells)} diamonds`;
  } else if (bar.weakMarker === "B") primary = "Weak buy candidate (B)";
  else if (bar.weakMarker === "W1") primary = "Watch candidate (W1) · not a buy yet";
  else if (bar.dcbMarker === "buy") primary = "Bounce buy signal · green star";
  else if (bar.dcbMarker === "sell") primary = "Bounce sell signal · red star";
  else if (bar.activeCall === "bullish") primary = "Existing bullish signal remains active";
  else if (bar.activeCall === "bearish") primary = "Existing bearish signal remains active";
  else if (bar.utEvent === "buy_flip") primary = "Fresh bullish timing turn";
  else if (bar.utEvent === "sell_flip") primary = "Fresh bearish timing turn";
  else if (bar.waveTrendEvent === "bull_cross") primary = "Bullish momentum cross";
  else if (bar.waveTrendEvent === "bear_cross") primary = "Bearish momentum cross";

  if (bar.warningMarker) context.push("gold conflict warning");
  if (bar.dcbMarker === "buy" && !primary.startsWith("Bounce buy"))
    context.push("green bounce-start star");
  if (bar.dcbMarker === "sell" && !primary.startsWith("Bounce sell"))
    context.push("red bounce-end star");
  if (bar.dcbActive && !bar.dcbMarker) context.push("bounce signal remains active");
  if (bar.openCipherEvents?.length) {
    const cipherLabels: Record<AnnaReplicaBar["openCipherEvents"][number], string> = {
      "green-dot": "bullish dot",
      "blue-triangle": "bullish triangle",
      "red-x": "bearish X",
      "red-diamond": "bearish diamond",
      "yellow-x": "mixed X",
      "blood-diamond": "bearish blood diamond",
    };
    context.push(`secondary timing: ${bar.openCipherEvents.map((event) => cipherLabels[event]).join(" + ")}`);
  }
  if (bar.stratType) context.push(`STRAT ${bar.stratType}`);
  return context.length ? `${primary}; ${context.join("; ")}` : primary;
}

function chartTrendFor(bar: AnnaReplicaBar, point: FramePoint) {
  const regime =
    bar.candleRegime === "bullish" || bar.candleRegime === "bearish"
      ? bar.candleRegime
      : point.slowDirection === "bullish" || point.slowDirection === "bearish"
        ? point.slowDirection
        : null;
  if (!regime) return "Trend is mixed";
  const color = regime === "bullish" ? "blue" : "yellow";
  const clauses = [`${titleCase(regime)} (${color} candles)`];
  if (bar.ribbonOrder && bar.ribbonOrder !== "mixed")
    clauses.push(`EMA ribbon is ${bar.ribbonOrder}`);
  if (point.direction !== "neutral" && point.direction !== regime)
    clauses.push(`${point.direction} pressure is active`);
  return clauses.join("; ");
}

function chartHealthFor(bar: AnnaReplicaBar) {
  const bullish = finite(bar.bullishVotes) ? bar.bullishVotes : 0;
  const bearish = finite(bar.bearishVotes) ? bar.bearishVotes : 0;
  const total = finite(bar.totalVotes) ? bar.totalVotes : bullish + bearish;
  if (total <= 0) return "Health is unavailable";
  const clauses =
    bullish > bearish
      ? [`Upward alignment · ${bullish} of ${total} indicators point up`]
      : bearish > bullish
        ? [`Downward alignment · ${bearish} of ${total} indicators point down`]
        : [`Balanced alignment · ${bullish} up and ${bearish} down`];
  if (finite(bar.aroonUp) && finite(bar.aroonDown)) {
    if (bar.aroonUp - bar.aroonDown >= 20) clauses.push("Aroon favors up");
    else if (bar.aroonDown - bar.aroonUp >= 20) clauses.push("Aroon favors down");
    else clauses.push("Aroon is mixed");
  }
  if (finite(bar.adx)) {
    if (bar.adx >= 35) clauses.push("trend strength is strong");
    else if (bar.adx >= 20) clauses.push("trend strength is established");
    else clauses.push("trend strength is weak");
  }
  if (finite(bar.plusDi) && finite(bar.minusDi)) {
    if (bar.plusDi > bar.minusDi) clauses.push("+DI leads");
    else if (bar.minusDi > bar.plusDi) clauses.push("−DI leads");
  }
  return clauses.join("; ");
}

function chartMomentumFor(bar: AnnaReplicaBar, point: FramePoint) {
  const clauses: string[] = [];
  if (bar.waveTrendZone === "overbought" || bar.waveTrendZone === "upper")
    clauses.push("momentum is extended to the upside");
  if (bar.waveTrendZone === "oversold" || bar.waveTrendZone === "lower")
    clauses.push("momentum is depressed and trying to turn");
  if (bar.waveTrendEvent === "bull_cross") clauses.push("a bullish momentum cross is present");
  if (bar.waveTrendEvent === "bear_cross") clauses.push("a bearish momentum cross is present");
  if (finite(bar.stochK) && bar.stochK >= 80)
    clauses.push("stochastic is elevated");
  else if (finite(bar.stochK) && bar.stochK <= 20)
    clauses.push("stochastic is depressed");
  if (finite(bar.macdHistogram)) {
    if (bar.macdHistogram > 0) clauses.push("MACD pressure is positive");
    if (bar.macdHistogram < 0) clauses.push("MACD pressure is negative");
  }
  if (bar.dotBuyTiers > 0) clauses.push(`${bar.dotBuyTiers} buy-dot tier${bar.dotBuyTiers === 1 ? "" : "s"}`);
  if (bar.dotSellTiers > 0) clauses.push(`${bar.dotSellTiers} sell-dot tier${bar.dotSellTiers === 1 ? "" : "s"}`);
  if (bar.squeezeOn === true) clauses.push("Squeeze is on · volatility is compressed");
  else if (bar.squeezeOn === false) clauses.push("Squeeze is off");
  const normalizedMomentum = normalizedSqueezeMomentum(bar);
  if (finite(bar.squeezeMomentum) && finite(normalizedMomentum) && normalizedMomentum >= 0.65)
    clauses.push(
      bar.squeezeMomentum > 0
        ? "squeeze momentum is expanding upward"
        : "squeeze momentum is expanding downward",
    );
  if (clauses.length) return clauses.join("; ");
  if (point.fastDirection === "bullish") return "Short-term momentum is constructive";
  if (point.fastDirection === "bearish") return "Short-term momentum is defensive";
  return "Short-term momentum is mixed";
}

function chartStructureFor(bar: AnnaReplicaBar) {
  const clauses: string[] = [];
  const trigger = bar.vectorStructuralLocation?.trigger;
  const locationText: Record<NonNullable<typeof trigger>, string> = {
    "demand-bounce": "Price is bouncing from nearby support",
    "demand-hold": "Price is holding nearby support",
    "demand-reclaim": "Price is reclaiming nearby support",
    "supply-breakout": "Price is clearing nearby resistance",
    "supply-rejection": "Price is rejecting nearby resistance",
    "supply-loss": "Price is losing nearby support",
    "demand-breakdown": "Price is breaking below nearby support",
    "range-breakout": "Price is breaking out of range",
    "range-breakdown": "Price is breaking down from range",
    "near-demand": "Price is near nearby support",
    "near-supply": "Price is near nearby resistance",
    none: "",
  };
  if (trigger && locationText[trigger]) clauses.push(locationText[trigger]);

  if (
    finite(bar.close) &&
    finite(bar.bbUpper) &&
    finite(bar.bbLower) &&
    bar.bbUpper > bar.bbLower
  ) {
    const bandWidth = bar.bbUpper - bar.bbLower;
    const upperPosition = (bar.bbUpper - bar.close) / bandWidth;
    const lowerPosition = (bar.close - bar.bbLower) / bandWidth;
    if (upperPosition <= 0.12) clauses.push("price is testing the upper band");
    else if (lowerPosition <= 0.12) clauses.push("price is testing the lower band");
  }

  if (finite(bar.close) && finite(bar.ema200) && bar.ema200 !== 0) {
    if (bar.close < bar.ema200 * 0.995) clauses.push("price is under EMA 200");
    else if (bar.close > bar.ema200 * 1.005) clauses.push("price is above EMA 200");
  }

  const avwap = finite(bar.eventAvwap)
    ? bar.eventAvwap
    : finite(bar.calendarAvwap)
      ? bar.calendarAvwap
      : null;
  if (finite(bar.close) && finite(avwap) && avwap !== 0) {
    if (bar.close > avwap * 1.005) clauses.push("price is above anchored VWAP");
    else if (bar.close < avwap * 0.995) clauses.push("price is below anchored VWAP");
  }

  if (bar.stratType) {
    const stratText: Record<NonNullable<AnnaReplicaBar["stratType"]>, string> = {
      "1": "structure is balanced",
      "2U": "structure is attempting an upward expansion",
      "2D": "structure is attempting a downward expansion",
      "3": "structure is in two-sided expansion",
    };
    clauses.push(stratText[bar.stratType]);
  }
  return clauses.length ? clauses.join("; ") : "No decisive structural level is active";
}

function chartParticipationFor(bar: AnnaReplicaBar) {
  const clauses: string[] = [];
  if (finite(bar.rvol)) {
    if (bar.rvol >= 1.2) clauses.push("relative volume is expanding");
    else if (bar.rvol < 0.75) clauses.push("relative volume is running thin");
    else clauses.push("relative volume is normal");
  }
  if (bar.obvDivergence === "bullish") clauses.push("OBV shows bullish divergence");
  if (bar.obvDivergence === "bearish") clauses.push("OBV shows bearish divergence");
  const mcdxValues = [bar.mcdxProfit, bar.mcdxLocked, bar.mcdxRock];
  if (mcdxValues.every(finite)) {
    const largest = Math.max(...mcdxValues);
    if (largest === bar.mcdxProfit) clauses.push("MCDX is profit-led");
    else if (largest === bar.mcdxLocked) clauses.push("MCDX is locked-led");
    else clauses.push("MCDX is rock-led");
  }
  if (finite(bar.mcdxVolumeRatio)) {
    if (bar.mcdxVolumeRatio >= 1.2) clauses.push("MCDX volume is elevated");
    else if (bar.mcdxVolumeRatio < 0.75) clauses.push("MCDX volume is thin");
  }
  if (clauses.length) return clauses.join("; ");
  return "Participation is unavailable";
}

function chartReadFor(
  bar: AnnaReplicaBar,
  point: FramePoint,
  prediction: VectorForecast,
  agreement: "aligned" | "conflicted" | "partial" | "unavailable",
  latestBarOpen: boolean,
): VectorChartRead {
  const signal = chartSignalFor(bar);
  const trend = chartTrendFor(bar, point);
  const health = chartHealthFor(bar);
  const momentum = chartMomentumFor(bar, point);
  const structure = chartStructureFor(bar);
  const participation = chartParticipationFor(bar);
  const bearishHealth = bar.bearishVotes > bar.bullishVotes;
  const bullishHealth = bar.bullishVotes > bar.bearishVotes;
  const bearishDivergence = bar.obvDivergence === "bearish";
  const bullishDivergence = bar.obvDivergence === "bullish";
  const resistance = /resistance|upper band|above anchored vwap/i.test(structure);
  const support = /support|lower band|below anchored vwap/i.test(structure);

  let expectation: string;
  if (prediction.direction === "crosscurrents") {
    expectation =
      "Expect two-sided movement until the completed-bar evidence and higher frames resolve their disagreement";
  } else if (prediction.direction === "range") {
    expectation =
      prediction.magnitude === "quiet"
        ? "Expect contained, range-bound movement while volatility remains compressed"
        : "Expect price to rotate inside the current range until an expansion clears it";
  } else if (prediction.direction === "higher-reversal") {
    expectation =
      "An upward turn is developing against the prior path; continuation needs completed-bar follow-through";
  } else if (prediction.direction === "lower-reversal") {
    expectation =
      "A downward turn is developing against the prior path; continuation needs completed-bar follow-through";
  } else if (prediction.direction === "higher-continuation") {
    expectation =
      bearishDivergence || bearishHealth || resistance
        ? "The path still favors higher prices, but weakening health or nearby resistance may limit follow-through"
        : "The path favors continued movement higher while the present alignment holds";
  } else if (prediction.direction === "lower-continuation") {
    expectation =
      bullishDivergence || bullishHealth || support
        ? "The path still favors lower prices, but improving health or nearby support may limit follow-through"
        : "The path favors continued movement lower unless the structure repairs";
  } else {
    expectation = "Wait for the completed-bar evidence to resolve";
  }

  if (agreement === "partial")
    expectation += "; higher-timeframe context is incomplete";
  if (agreement === "unavailable")
    expectation += "; higher-timeframe context is unavailable";
  if (latestBarOpen)
    expectation += "; the last candle is tentative and the signal is not locked until it closes";

  const bottomLine = `${prediction.directionLabel} · ${titleCase(prediction.magnitude)} expected magnitude · ${titleCase(prediction.conviction)} conviction · ${prediction.timeframeLabel}`;

  const framing =
    prediction.direction === "higher-continuation" ||
    prediction.direction === "higher-reversal"
      ? "constructive"
      : prediction.direction === "lower-continuation" ||
          prediction.direction === "lower-reversal"
        ? "defensive"
        : prediction.direction === "crosscurrents"
          ? "watch"
          : "neutral";
  const statement = [
    `Current signal: ${signal}.`,
    `Trend: ${trend}.`,
    `Health: ${health}.`,
    `Momentum: ${titleCase(momentum)}.`,
    `Structure: ${titleCase(structure)}.`,
    `Participation: ${titleCase(participation)}.`,
    `What to expect: ${titleCase(expectation)}.`,
    `Bottom line: ${bottomLine}.`,
  ].join("\n");
  return {
    signal,
    trend,
    health,
    momentum,
    structure,
    participation,
    expectation,
    bottomLine,
    statement,
    framing,
  };
}

function transitionReason(point: FramePoint) {
  return point.reasons[0] ?? point.vetoes[0] ?? "State changed on completed-bar evidence.";
}

function buildTransitions(points: FramePoint[]): VectorGestaltTransition[] {
  const transitions: VectorGestaltTransition[] = [];
  points.forEach((point, index) => {
    const prior = points[index - 1];
    const eventChanged = point.event !== "no new event";
    if (!prior || point.phase !== prior.phase || eventChanged) {
      transitions.push({
        time: point.bar.timestamp,
        direction: point.direction,
        event: point.event,
        from: prior?.phase ?? "unavailable",
        to: point.phase,
        reason: transitionReason(point),
      });
    }
  });
  return transitions.slice(-16);
}

// Session aggregation can visit hundreds or thousands of bars for the same
// timezone. Intl formatters are immutable but expensive to construct, so keep
// a bounded formatter set and reuse it across chart builds. The bound prevents
// unusual provider timezone values from growing isolate memory indefinitely.
const VECTOR_DATE_FORMATTER_LIMIT = 32;
const vectorDateFormatters = new Map<string, Intl.DateTimeFormat>();

function vectorDateFormatter(locale: "en-CA" | "en-US", timezone: string) {
  const key = `${locale}\u0000${timezone}`;
  const cached = vectorDateFormatters.get(key);
  if (cached) return cached;
  const formatter = new Intl.DateTimeFormat(locale, {
    timeZone: timezone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });
  if (vectorDateFormatters.size >= VECTOR_DATE_FORMATTER_LIMIT)
    vectorDateFormatters.delete(vectorDateFormatters.keys().next().value!);
  vectorDateFormatters.set(key, formatter);
  return formatter;
}

function sessionDateKey(timestamp: number, timezone: string) {
  try {
    return vectorDateFormatter("en-CA", timezone).format(
      new Date(timestamp * 1_000),
    );
  } catch {
    return new Date(timestamp * 1_000).toISOString().slice(0, 10);
  }
}

function dateParts(timestamp: number, timezone: string) {
  try {
    const parts = vectorDateFormatter("en-US", timezone).formatToParts(
      new Date(timestamp * 1_000),
    );
    const output = Object.fromEntries(
      parts
        .filter((part) => part.type !== "literal")
        .map((part) => [part.type, Number(part.value)]),
    );
    if (output.year && output.month && output.day) return output;
  } catch {
    // Fall through to UTC.
  }
  const date = new Date(timestamp * 1_000);
  return {
    year: date.getUTCFullYear(),
    month: date.getUTCMonth() + 1,
    day: date.getUTCDate(),
  };
}

function weekKey(timestamp: number, timezone: string) {
  const parts = dateParts(timestamp, timezone);
  const date = new Date(Date.UTC(parts.year, parts.month - 1, parts.day));
  const weekday = date.getUTCDay() || 7;
  date.setUTCDate(date.getUTCDate() - weekday + 1);
  return date.toISOString().slice(0, 10);
}

type SourceAggregationOptions = {
  includeCompletedSessionTail?: boolean;
  symbol?: string | null;
  exchange?: string | null;
  instrumentType?: string | null;
};

function sourceSessionPolicy(
  timezone: string,
  options: SourceAggregationOptions,
): SessionPolicy {
  return {
    instrumentType: options.instrumentType || "EQUITY",
    // Bare symbols remain US-compatible for legacy callers. A suffixed symbol
    // or a provider timezone still resolves its own venue through the shared
    // session policy.
    exchange: options.exchange || (options.symbol ? undefined : "NASDAQ"),
    symbol: options.symbol,
    exchangeTimezone: timezone,
  };
}

function aggregateSourceBars(
  sourceBars: SourceBar[],
  sourceInterval: string,
  targetInterval: string,
  timezone: string,
  options: SourceAggregationOptions = {},
) {
  const sourceSeconds = FRAME_SECONDS[sourceInterval];
  const targetSeconds = FRAME_SECONDS[targetInterval];
  if (!sourceSeconds || !targetSeconds || targetSeconds <= sourceSeconds)
    return [];
  const resolvedTimezone = timezone || "America/New_York";
  const policy = sourceSessionPolicy(resolvedTimezone, options);
  const profile = exchangeSessionProfile(policy);
  if (!profile) return [];
  const securitySession =
    profile.kind === "us-security" || profile.kind === "foreign-security";
  const venueClockedSource =
    securitySession && INTRADAY_SOURCE_INTERVALS.has(sourceInterval);
  const eligibleBars =
    venueClockedSource
      ? sourceBars.filter(bar => {
          const clock = exchangeClock(new Date(bar.timestamp * 1_000), policy);
          const bounds = exchangeSessionBounds(clock.dateKey, policy);
          return Boolean(
            bounds &&
            isExchangeMarketDate(clock.dateKey, policy) &&
            clock.minutes >= bounds.regularOpenMinutes &&
            clock.minutes < bounds.regularCloseMinutes,
          );
        })
      : sourceBars;
  const groups = new Map<string, SourceBar[]>();
  const sessionStarts = new Map<string, number>();
  const sourceDateTimezone = venueClockedSource ? resolvedTimezone : "UTC";
  for (const bar of eligibleBars) {
    const session = sessionDateKey(bar.timestamp, sourceDateTimezone);
    if (!sessionStarts.has(session)) {
      const sessionOpen = venueClockedSource
        ? exchangeDateTimeUtc(
            session,
            profile.regularOpenMinutes,
            policy,
          )
        : null;
      sessionStarts.set(
        session,
        sessionOpen ? Date.parse(sessionOpen) / 1_000 : bar.timestamp,
      );
    }
    let bucket: string;
    if (targetInterval === "1d") bucket = session;
    else if (targetInterval === "1wk") bucket = weekKey(bar.timestamp, sourceDateTimezone);
    else {
      // A halt or missing opening print must not shift every higher-frame
      // candle for that session. Security bars anchor to the venue's regular
      // open; continuous instruments retain the first observed timestamp.
      const elapsedSeconds =
        bar.timestamp - (sessionStarts.get(session) ?? bar.timestamp);
      const bucketIndex = Math.floor(
        elapsedSeconds / targetSeconds,
      );
      bucket = `${session}:${bucketIndex}`;
    }
    const existing = groups.get(bucket);
    if (existing) existing.push(bar);
    else groups.set(bucket, [bar]);
  }

  const ordered = [...groups.entries()].sort((left, right) =>
    left[1][0].timestamp - right[1][0].timestamp,
  );
  const output: SourceBar[] = [];
  ordered.forEach(([key, bars], index) => {
    if (!bars.length) return;
    const last = bars.at(-1)!;
    const lastClock = venueClockedSource
      ? exchangeClock(new Date(last.timestamp * 1_000), policy)
      : null;
    const lastBounds = lastClock
      ? exchangeSessionBounds(lastClock.dateKey, policy)
      : null;
    const completesSession = lastClock
      ? Boolean(
          lastBounds &&
          isExchangeMarketDate(lastClock.dateKey, policy) &&
          lastClock.minutes + sourceSeconds / 60 >=
            lastBounds.regularCloseMinutes,
        )
      : true;
    const contiguous = bars.every(
      (bar, barIndex) =>
        barIndex === 0 ||
        bar.timestamp - bars[barIndex - 1].timestamp === sourceSeconds,
    );
    const expectedBars = Math.max(1, Math.ceil(targetSeconds / sourceSeconds));
    if (targetInterval !== "1d" && targetInterval !== "1wk") {
      const completeBucket = bars.length === expectedBars;
      // A 13:30–16:00 US-equity tail is not a completed four-hour bar.
      // Retain only duration-complete buckets as higher-frame evidence unless
      // the caller is explicitly building a user-facing higher-frame chart.
      // A completed session tail is valid chart evidence even though the
      // regular equity session is shorter than a nominal 4h bucket.
      if (
        !contiguous ||
        (!completeBucket &&
          !(options.includeCompletedSessionTail && completesSession && bars.length > 0))
      ) return;
    } else {
      if (!completesSession) return;
      if (targetInterval === "1wk" && index === ordered.length - 1) {
        // Daily inputs already represent completed sessions. Unlike intraday
        // inputs they have no lastClock, but their final week can still close.
        const lastSessionDate = lastClock?.dateKey ?? (
          sourceInterval === "1d"
            ? sessionDateKey(last.timestamp, sourceDateTimezone)
            : null
        );
        if (!lastSessionDate || !isExchangeMarketDate(lastSessionDate, policy)) return;
        const nextSession = nextExchangeMarketDate(lastSessionDate, policy);
        // Continuous and crypto markets use the next UTC midnight as their
        // session boundary. Their profile stores that boundary as 24:00 for
        // comparison purposes, but the civil-time converter intentionally
        // accepts minutes only in the 00:00–23:59 range.
        const nextSessionClose =
          profile.kind === "crypto" || profile.kind === "continuous"
            ? `${nextSession}T00:00:00.000Z`
            : exchangeDateTimeUtc(
                nextSession,
                profile.regularCloseMinutes,
                policy,
              );
        const nextSessionTimestamp = nextSessionClose
          ? Date.parse(nextSessionClose) / 1_000
          : Number.NaN;
        if (
          weekKey(nextSessionTimestamp, sourceDateTimezone) ===
          weekKey(last.timestamp, sourceDateTimezone)
        ) return;
      }
    }
    output.push({
      timestamp: bars[0].timestamp,
      open: bars[0].open,
      high: Math.max(...bars.map((bar) => bar.high)),
      low: Math.min(...bars.map((bar) => bar.low)),
      close: bars.at(-1)!.close,
      volume: bars.reduce((sum, bar) => sum + bar.volume, 0),
    });
    void key;
  });
  return output;
}

/**
 * Canonical completed-bar aggregation shared by the chart replica and the
 * always-on Tensor runner. Keeping this boundary public prevents the service
 * from growing a second, subtly different 2H/4H/Weekly clock.
 */
export function deriveVectorSourceBars(
  sourceBars: VectorGestaltSourceBar[],
  sourceInterval: string,
  targetInterval: string,
  timezone = "America/New_York",
  options: SourceAggregationOptions = {},
) {
  return aggregateSourceBars(
    sourceBars,
    sourceInterval,
    targetInterval,
    timezone,
    options,
  );
}

function historyForDerived(
  replica: DerivedReplicaMetadata,
  source: SourceHistory,
  spec: FrameSpec,
  bars: SourceBar[],
  displayBars = TENSOR_CHART_DISPLAY_BARS,
) {
  return {
    symbol: replica.symbol,
    currency: replica.currency,
    exchange: replica.exchange,
    timezone: source.timezone ?? replica.timezone,
    interval: spec.interval,
    intervalLabel: spec.label,
    displayBars,
    latestBarOpen: false,
    instrumentType: source.instrumentType ?? null,
    bars,
  };
}

function aggregationOptionsFor(
  replica: DerivedReplicaMetadata,
  source: SourceHistory,
  options: SourceAggregationOptions = {},
): SourceAggregationOptions {
  return {
    ...options,
    symbol: source.symbol ?? replica.symbol,
    exchange: source.exchange ?? replica.exchange,
    instrumentType: source.instrumentType,
  };
}

/**
 * Build one completed derived frame from a source history.  This is separate
 * from the higher-timeframe context list because the 10m dashboard forecast
 * is a selected timing frame, not a vote that should alter the native 5m
 * forecast.
 */
export function buildDerivedVectorTimeframeReplica(
  replica: AnnaReplica,
  sourceHistory: SourceHistory | undefined,
  targetInterval: string,
  options?: { includeCompletedSessionTail?: boolean },
): AnnaReplica | null;
export function buildDerivedVectorTimeframeReplica(
  replica: DerivedReplicaMetadata,
  sourceHistory: SourceHistory,
  targetInterval: string,
  options?: { includeCompletedSessionTail?: boolean },
): AnnaReplica | null;
export function buildDerivedVectorTimeframeReplica(
  replica: AnnaReplica | DerivedReplicaMetadata,
  sourceHistory: SourceHistory | undefined,
  targetInterval: string,
  options: { includeCompletedSessionTail?: boolean } = {},
) {
  let source: SourceHistory;
  if (sourceHistory) {
    source = sourceHistory;
  } else if ("bars" in replica) {
    source = {
      bars: replica.bars
        .filter((bar) => bar.barFinality === "closed")
        .map((bar) => ({
          timestamp: bar.timestamp,
          open: bar.open,
          high: bar.high,
          low: bar.low,
          close: bar.close,
          volume: bar.volume,
        })),
      interval: replica.interval,
      intervalLabel: replica.intervalLabel,
      timezone: replica.timezone,
      latestBarOpen: false,
    };
  } else {
    return null;
  }
  const closedSource = source.bars
    .filter(
      (bar) =>
        finite(bar.timestamp) &&
        finite(bar.open) &&
        finite(bar.high) &&
        finite(bar.low) &&
        finite(bar.close) &&
        finite(bar.volume),
    )
    .sort((left, right) => left.timestamp - right.timestamp);
  if (source.latestBarOpen) closedSource.pop();
  const spec: FrameSpec = {
    interval: targetInterval,
    label: frameLabel(targetInterval),
    role: frameRole(targetInterval),
  };
  const bars = aggregateSourceBars(
    closedSource,
    source.interval,
    targetInterval,
    source.timezone ?? replica.timezone,
    aggregationOptionsFor(replica, source, options),
  );
  if (bars.length < VECTOR_CONTEXT_MINIMUM_BARS) return null;
  return buildAnnaReplica(
    historyForDerived(replica, source, spec, bars, bars.length),
  );
}

export function buildDerivedVectorTimeframeReplicas(
  replica: AnnaReplica,
  sourceHistory?: SourceHistory,
) {
  const source: SourceHistory = sourceHistory ?? {
    bars: replica.bars
      .filter((bar) => bar.barFinality === "closed")
      .map((bar) => ({
        timestamp: bar.timestamp,
        open: bar.open,
        high: bar.high,
        low: bar.low,
        close: bar.close,
        volume: bar.volume,
      })),
    interval: replica.interval,
    intervalLabel: replica.intervalLabel,
    timezone: replica.timezone,
    latestBarOpen: false,
  };
  const closedSource = source.bars
    .filter(
      (bar) =>
        finite(bar.timestamp) &&
        finite(bar.open) &&
        finite(bar.high) &&
        finite(bar.low) &&
        finite(bar.close) &&
        finite(bar.volume),
    )
    .sort((left, right) => left.timestamp - right.timestamp);
  if (source.latestBarOpen) closedSource.pop();
  return (FRAME_HIERARCHY[replica.interval] ?? [])
    .map((spec) => {
      const bars = aggregateSourceBars(
        closedSource,
        source.interval,
        spec.interval,
        source.timezone ?? replica.timezone,
        aggregationOptionsFor(replica, source),
      );
      if (bars.length < VECTOR_CONTEXT_MINIMUM_BARS) return null;
      return buildAnnaReplica(historyForDerived(replica, source, spec, bars));
    })
    .filter((value): value is AnnaReplica => Boolean(value));
}

export function buildVectorGestaltState(
  replica: AnnaReplica,
  contextReplicas: AnnaReplica[] = [],
): VectorGestaltState | null {
  const closedBars = replica.bars.filter((bar) => bar.barFinality === "closed");
  const latest = closedBars.at(-1);
  if (!latest) return null;
  const points = closedBars.map((_, index) => buildPoint(closedBars, index));
  const point = points.at(-1)!;
  const selected = frameFromReplica(replica, "selected chart");
  const contexts = contextReplicas.map((context) =>
    frameFromReplica(context, "derived from selected history", point.direction),
  );
  const agreement = timeframeAgreement(selected, contexts);
  const evidenceStrength = evidenceFor(latest, point.phase, agreement);
  const review = reviewReasons(point, replica, agreement);
  const manualReviewRequired = review.length > 0;
  const previous = closedBars.at(-2);
  const fast = stateDirection(latest.fastState);
  const slow = stateDirection(latest.slowState);
  const location = latest.vectorStructuralLocation?.bias ?? "unavailable";
  const frame = {
    ...selected,
    evidenceStrength,
  };
  const reasons = [...point.reasons];
  if (agreement === "conflicted")
    reasons.push("Higher timeframe context disagrees; no universal timeframe override is assumed.");
  const vetoes = [...point.vetoes];
  if (agreement === "conflicted") vetoes.push("Higher-frame conflict requires review.");
  const policy = policyFor(point, manualReviewRequired);
  const forecast = buildForecast(
    closedBars,
    point,
    frame,
    contexts,
    agreement,
    evidenceStrength,
    policy.abstains,
    replica.structure?.nativeQuality,
  );
  const prediction = forecast.prediction;
  const chartRead = chartReadFor(
    latest,
    point,
    prediction,
    agreement,
    replica.bars.at(-1)?.barFinality === "open",
  );
  return {
    version: VECTOR_GESTALT_VERSION,
    phase: point.phase,
    direction: point.direction,
    summary: prediction.summary,
    prediction,
    chartRead,
    evidenceStrength,
    manualReviewRequired,
    reviewReason: review.length ? review.join(" · ") : null,
    selectedFrame: frame,
    fast: {
      direction: fast,
      event: point.event,
      ageBars: point.fastEventAge,
      persistenceBars: point.fastPersistenceBars,
      source: "UT regime, WaveTrend timing and visible primary-marker candidates",
    },
    slow: {
      direction: slow,
      regime: latest.candleRegime === "bullish" || latest.candleRegime === "bearish"
        ? latest.candleRegime
        : "mixed",
      persistenceBars: point.slowPersistenceBars,
      source: "EMA 8/13/21/34/48 ordering with persistent candle regime",
    },
    episode: {
      direction: point.episodeExpired ? null : latest.activeCall,
      lifecycle: point.episodeExpired ? "stale" : latest.callLifecycle,
      id: latest.callEpisode,
      ageBars: point.episodeAge,
      lastPrimaryEventAge: latest.lastPrimaryEventAge,
      repeatOrdinal: latest.repeatOrdinal,
    },
    benchmark: {
      bullishVotes: latest.bullishVotes,
      bearishVotes: latest.bearishVotes,
      totalVotes: latest.totalVotes,
      alignedShare:
        latest.totalVotes > 0
          ? Math.max(latest.bullishVotes, latest.bearishVotes) / latest.totalVotes
          : null,
      participation: participationState(latest),
      volatility: volatilityState(latest, previous),
      location,
    },
    timeframe: {
      selected: frame,
      contexts,
      agreement,
      basis:
        "Selected-frame timing is retained; higher contexts are derived from completed source history and are review gates, not automatic overrides.",
    },
    policy,
    qualityValidator: forecast.qualityValidator,
    reasons,
    vetoes,
    transitions: buildTransitions(points),
  };
}

export type { SourceHistory as VectorGestaltSourceHistory };
