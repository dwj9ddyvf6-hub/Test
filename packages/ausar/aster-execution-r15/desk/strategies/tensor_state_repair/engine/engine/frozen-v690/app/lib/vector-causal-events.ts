import {
  analyzeVectorBars,
  type VectorAnalysis,
  type VectorBar,
  type VectorCausalLocationEvent,
  type VectorCausalTrigger,
} from "./vector-engine.ts";
import {
  newYorkClock,
  usMarketSessionBounds,
} from "./session-policy.ts";

export const VECTOR_CAUSAL_EVENT_VERSION =
  "vector-causal-event/1.1.0-action-events" as const;
export const VECTOR_CAUSAL_EVENTS_PER_FRAME = 16;
export const VECTOR_CAUSAL_EVENT_TAPE_LIMIT = 32;
const VECTOR_CAUSAL_ANALYSIS_BARS = 480;

export type VectorCausalInterval = "5m" | "10m";

export type VectorCausalEvent = Omit<VectorCausalLocationEvent, "id"> & {
  id: string;
  eventVersion: typeof VECTOR_CAUSAL_EVENT_VERSION;
  symbol: string;
  interval: VectorCausalInterval;
  completedAt: number;
  derived: boolean;
  finality: "confirmed";
};

const FRAME_SECONDS: Record<VectorCausalInterval, number> = {
  "5m": 5 * 60,
  "10m": 10 * 60,
};

function finite(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

function cleanSymbol(value: string) {
  return String(value || "")
    .trim()
    .toUpperCase()
    .replace(/[^A-Z0-9.^=/-]/g, "")
    .slice(0, 24);
}

function validBar(bar: VectorBar) {
  return (
    finite(bar.time) &&
    finite(bar.open) &&
    finite(bar.high) &&
    finite(bar.low) &&
    finite(bar.close) &&
    finite(bar.volume) &&
    bar.open > 0 &&
    bar.high >= Math.max(bar.open, bar.close) &&
    bar.low <= Math.min(bar.open, bar.close) &&
    bar.low > 0 &&
    bar.volume >= 0
  );
}

/**
 * Derives only duration-complete regular-session 10-minute candles from the
 * already verified 5-minute tape. Missing prints and partial buckets are
 * omitted rather than fabricated.
 */
export function deriveCompletedRegularTenMinuteBars(
  fiveMinuteBars: VectorBar[],
): VectorBar[] {
  const buckets = new Map<string, VectorBar[]>();
  const ordered = [...fiveMinuteBars]
    .filter(validBar)
    .sort((left, right) => left.time - right.time);

  for (const bar of ordered) {
    const clock = newYorkClock(new Date(bar.time * 1_000));
    const regularClose = usMarketSessionBounds(
      clock.dateKey,
    ).regularCloseMinutes;
    if (clock.minutes < 9 * 60 + 30 || clock.minutes >= regularClose)
      continue;
    const elapsed = clock.minutes - (9 * 60 + 30);
    if (elapsed % 5 !== 0) continue;
    const bucketIndex = Math.floor(elapsed / 10);
    const key = `${clock.dateKey}:${bucketIndex}`;
    const bucket = buckets.get(key);
    if (bucket) bucket.push(bar);
    else buckets.set(key, [bar]);
  }

  return [...buckets.values()]
    .sort((left, right) => left[0].time - right[0].time)
    .flatMap(bucket => {
      const bars = [...bucket].sort((left, right) => left.time - right.time);
      if (
        bars.length !== 2 ||
        bars[1].time - bars[0].time !== FRAME_SECONDS["5m"]
      )
        return [];
      const firstClock = newYorkClock(new Date(bars[0].time * 1_000));
      const elapsed = firstClock.minutes - (9 * 60 + 30);
      if (elapsed < 0 || elapsed % 10 !== 0) return [];
      return [{
        time: bars[0].time,
        open: Number(bars[0].open),
        high: Math.max(Number(bars[0].high), Number(bars[1].high)),
        low: Math.min(Number(bars[0].low), Number(bars[1].low)),
        close: bars[1].close,
        volume: Number(bars[0].volume) + Number(bars[1].volume),
      }];
    });
}

function eventId({
  symbol,
  interval,
  completedAt,
  trigger,
  zoneId,
}: {
  symbol: string;
  interval: VectorCausalInterval;
  completedAt: number;
  trigger: VectorCausalTrigger;
  zoneId: string;
}) {
  return [
    VECTOR_CAUSAL_EVENT_VERSION,
    symbol,
    interval,
    completedAt,
    trigger,
    zoneId,
  ].join(":");
}

function frameEvents({
  symbol,
  interval,
  analysis,
  derived,
}: {
  symbol: string;
  interval: VectorCausalInterval;
  analysis: VectorAnalysis;
  derived: boolean;
}) {
  if (analysis.status !== "ready") return [];
  const seconds = FRAME_SECONDS[interval];
  return analysis.causalLocationEvents
    .slice(-VECTOR_CAUSAL_EVENTS_PER_FRAME)
    .map(event => {
      const completedAt = event.time + seconds;
      return {
        ...event,
        id: eventId({
          symbol,
          interval,
          completedAt,
          trigger: event.trigger,
          zoneId: event.zone?.id || "range",
        }),
        eventVersion: VECTOR_CAUSAL_EVENT_VERSION,
        symbol,
        interval,
        completedAt,
        derived,
        finality: "confirmed" as const,
      } satisfies VectorCausalEvent;
    });
}

export function buildVectorCausalEventTape({
  symbol: rawSymbol,
  fiveMinuteBars,
  fiveMinuteAnalysis,
  limit = VECTOR_CAUSAL_EVENT_TAPE_LIMIT,
}: {
  symbol: string;
  fiveMinuteBars: VectorBar[];
  fiveMinuteAnalysis: VectorAnalysis;
  limit?: number;
}): VectorCausalEvent[] {
  const symbol = cleanSymbol(rawSymbol);
  if (!symbol || fiveMinuteAnalysis.status !== "ready") return [];
  const tenMinuteBars = deriveCompletedRegularTenMinuteBars(fiveMinuteBars);
  // The event tape needs EMA-200 warm-up plus ample structural context, not a
  // second full 60-day reconstruction. Bounding the derived frame keeps the
  // scheduled watchlist sweep inside its existing CPU/provider envelope.
  const tenMinuteAnalysis = analyzeVectorBars(
    tenMinuteBars.slice(-VECTOR_CAUSAL_ANALYSIS_BARS),
  );
  const events = [
    ...frameEvents({
      symbol,
      interval: "5m",
      analysis: fiveMinuteAnalysis,
      derived: false,
    }),
    ...frameEvents({
      symbol,
      interval: "10m",
      analysis: tenMinuteAnalysis,
      derived: true,
    }),
  ].sort((left, right) =>
    left.completedAt - right.completedAt ||
    left.interval.localeCompare(right.interval) ||
    left.trigger.localeCompare(right.trigger) ||
    (left.zone?.id || "range").localeCompare(
      right.zone?.id || "range",
    ),
  );
  const bounded = Math.max(
    0,
    Math.min(
      VECTOR_CAUSAL_EVENT_TAPE_LIMIT,
      Math.floor(Number(limit) || 0),
    ),
  );
  return bounded ? events.slice(-bounded) : [];
}
