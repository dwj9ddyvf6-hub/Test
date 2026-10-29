import {
  emaSeries,
  macdSeries,
  rsiSeries,
} from "./chart-window.ts";
import type { GoldDiamondEvaluation } from "./vector-gold-diamond.ts";
import type { TensorContext } from "../../lib/anna-replica.mjs";

export const VECTOR_MODEL_VERSION = "vector-engine/1.3.0-action-events";

export const VECTOR_ACTION_SIGNAL_GLYPHS = Object.freeze({
  "demand-bounce": "↥",
  "supply-breakout": "⇧",
  "demand-breakdown": "⇩",
} as const);

export type VectorActionSignalTrigger =
  keyof typeof VECTOR_ACTION_SIGNAL_GLYPHS;

export type VectorBar = {
  time: number;
  open: number | null;
  high: number | null;
  low: number | null;
  close: number;
  volume: number | null;
};

export type VectorState =
  | "VECTOR_BUY"
  | "VECTOR_SELL"
  | "SETUP_FORMING"
  | "REVERSAL_WINDOW"
  | "CONFLICT"
  | "NEUTRAL";

export type VectorRegime =
  | "constructive"
  | "defensive"
  | "balanced";

export type VectorZone = {
  id: string;
  polarity: "demand" | "supply";
  model: "A" | "C";
  modelSource: "pivot-band" | "cell-density";
  low: number;
  high: number;
  center: number;
  createdIndex: number;
  knownAtIndex: number;
  createdAt: number;
  knownAt: number;
  lastSeenIndex: number;
  state: "active" | "break-pending" | "broken";
  touches: number;
  strength: number;
  dualConfirmed: boolean;
  contextOnly: boolean;
};

export type VectorFamilies = {
  trend: number | null;
  momentum: number | null;
  location: number | null;
  participation: number | null;
  volatilityReadiness: number | null;
};

export type VectorPrimaryMarker =
  | "buy-cyan"
  | "buy-green"
  | "sell-magenta"
  | "sell-red";

export type VectorFib = {
  low: number;
  high: number;
  lowIndex: number;
  highIndex: number;
  levels: Array<{ ratio: number; value: number }>;
};

export type VectorBarResult = {
  index: number;
  time: number;
  close: number;
  finality: "closed";
  /** Literal Anna marker identity. Never infer color from VECTOR_BUY. */
  primaryMarkers: VectorPrimaryMarker[];
  structuralActionSignal?: "demand-bounce" | "supply-breakout" | "demand-breakdown" | null;
  /** Additive evidence; it never changes the literal marker identity. */
  goldDiamond?: GoldDiamondEvaluation | null;
  state: VectorState;
  direction: "bullish" | "bearish" | "mixed" | "neutral";
  resultant: number | null;
  coherence: number | null;
  regime: VectorRegime;
  families: VectorFamilies;
  atr: number | null;
  rsi: number | null;
  macdHistogram: number | null;
  relativeVolume: number | null;
  locationTrigger:
    | "demand-bounce"
    | "demand-hold"
    | "demand-reclaim"
    | "supply-breakout"
    | "supply-rejection"
    | "supply-loss"
    | "demand-breakdown"
    | "range-breakout"
    | "range-breakdown"
    | "near-demand"
    | "near-supply"
    | "none";
  reasons: string[];
  vetoes: string[];
  nextConfirmation: string;
  /** Optional sidecar context; never part of primary marker eligibility. */
  tensorContext?: TensorContext | null;
};

export type VectorEvent = {
  id: string;
  index: number;
  time: number;
  price: number;
  state: Exclude<VectorState, "NEUTRAL">;
  direction: VectorBarResult["direction"];
  resultant: number | null;
};

export type VectorCausalTrigger =
  | "demand-bounce"
  | "demand-hold"
  | "demand-reclaim"
  | "supply-breakout"
  | "supply-rejection"
  | "supply-loss"
  | "demand-breakdown"
  | "range-breakout"
  | "range-breakdown";

export type VectorCausalZoneSnapshot = Pick<
  VectorZone,
  | "id"
  | "polarity"
  | "model"
  | "modelSource"
  | "low"
  | "high"
  | "center"
  | "knownAtIndex"
  | "knownAt"
  | "state"
  | "touches"
  | "strength"
  | "dualConfirmed"
>;

/**
 * Completed-bar structural evidence evaluated against zone geometry frozen at
 * the end of the prior bar. This is intentionally separate from the chart's
 * descriptive location label, which may incorporate the current bar while it
 * updates density zones.
 */
export type VectorCausalLocationEvent = {
  id: string;
  index: number;
  time: number;
  price: number;
  trigger: VectorCausalTrigger;
  direction: "bullish" | "bearish";
  zone: VectorCausalZoneSnapshot | null;
  families: VectorFamilies;
  resultant: number | null;
  coherence: number | null;
  relativeVolume: number | null;
};

export type VectorAnalysis = {
  modelVersion: typeof VECTOR_MODEL_VERSION;
  status: "ready" | "warming" | "unavailable";
  bars: VectorBarResult[];
  zones: VectorZone[];
  /** Zone geometry frozen immediately before each bar opened. */
  causalZonesByIndex?: VectorZone[][];
  displayZones: VectorZone[];
  events: VectorEvent[];
  causalLocationEvents: VectorCausalLocationEvent[];
  current: VectorBarResult | null;
  series: {
    ema21: Array<number | null>;
    ema55: Array<number | null>;
    ema200: Array<number | null>;
    atr14: Array<number | null>;
    rsi14: Array<number | null>;
    macdHistogram: Array<number | null>;
    anchoredVwap: Array<number | null>;
  };
  fib: VectorFib | null;
  evidence: {
    completedBars: number;
    firstTime: number | null;
    lastTime: number | null;
    volumeAvailable: number;
    volumeTotal: number;
    pivotRadius: 3;
    zoneModels: ["A", "C"];
  };
};

type InternalZone = VectorZone & {
  breakCloses: number;
  inside: boolean;
  outsideBars: number;
};

const FAMILY_WEIGHTS = {
  trend: 0.34,
  momentum: 0.29,
  location: 0.25,
  participation: 0.12,
} as const;

const clamp = (value: number, low = -1, high = 1) =>
  Math.max(low, Math.min(high, value));

const finite = (value: unknown): value is number =>
  typeof value === "number" && Number.isFinite(value);

const highOf = (bar: VectorBar) =>
  finite(bar.high) ? bar.high : bar.close;

const lowOf = (bar: VectorBar) =>
  finite(bar.low) ? bar.low : bar.close;

const openOf = (bar: VectorBar) =>
  finite(bar.open) ? bar.open : bar.close;

function stableId(parts: Array<string | number>) {
  let hash = 2166136261;
  const value = parts.join("|");
  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return (hash >>> 0).toString(36);
}

export function atrSeries(bars: VectorBar[], period = 14) {
  const output = Array<number | null>(bars.length).fill(null);
  if (bars.length < period) return output;
  const trueRanges = bars.map((bar, index) => {
    const high = highOf(bar);
    const low = lowOf(bar);
    if (!index) return Math.max(0, high - low);
    const previousClose = bars[index - 1].close;
    return Math.max(
      high - low,
      Math.abs(high - previousClose),
      Math.abs(low - previousClose),
    );
  });
  let average =
    trueRanges
      .slice(0, period)
      .reduce((sum, value) => sum + value, 0) / period;
  output[period - 1] = average;
  for (let index = period; index < bars.length; index += 1) {
    average =
      (average * (period - 1) + trueRanges[index]) / period;
    output[index] = average;
  }
  return output;
}

function standardDeviation(values: number[]) {
  if (!values.length) return 0;
  const mean =
    values.reduce((sum, value) => sum + value, 0) / values.length;
  return Math.sqrt(
    values.reduce(
      (sum, value) => sum + (value - mean) ** 2,
      0,
    ) / values.length,
  );
}

function percentileRank(values: number[], value: number) {
  const valid = values.filter(finite);
  if (!valid.length) return 0.5;
  const below = valid.filter(candidate => candidate <= value).length;
  return below / valid.length;
}

function rollingVolatilityReadiness(
  bars: VectorBar[],
  atr: Array<number | null>,
  index: number,
  widthByIndex: number[],
) {
  if (index < 19 || !finite(atr[index]) || !(Number(atr[index]) > 0))
    return null;
  const start = Math.max(19, index - 99);
  const widths = widthByIndex.slice(start, index + 1);
  const rank = percentileRank(widths, widths.at(-1) || 0);
  const compression = 1 - rank;
  const rangeExpansion = clamp(
    (highOf(bars[index]) - lowOf(bars[index])) /
      Number(atr[index]) -
      0.8,
    0,
    1,
  );
  return clamp(0.7 * compression + 0.3 * rangeExpansion, 0, 1);
}

function volatilityWidths(bars: VectorBar[]) {
  const widths: number[] = [];
  for (let index = 19; index < bars.length; index += 1) {
    const closes = bars.slice(index - 19, index + 1).map(bar => bar.close);
    const mean = closes.reduce((sum, close) => sum + close, 0) / closes.length;
    widths[index] = mean > 0 ? (4 * standardDeviation(closes)) / mean : 0;
  }
  return widths;
}

function participationFamily(
  bars: VectorBar[],
  index: number,
) {
  if (index < 20) return { value: null, relativeVolume: null };
  const window = bars.slice(index - 20, index + 1);
  if (
    window.some(
      bar => !finite(bar.volume) || Number(bar.volume) <= 0,
    )
  )
    return { value: null, relativeVolume: null };
  const priorVolumes = window
    .slice(0, -1)
    .map(bar => Number(bar.volume));
  const meanVolume =
    priorVolumes.reduce((sum, value) => sum + value, 0) /
    priorVolumes.length;
  if (!(meanVolume > 0))
    return { value: null, relativeVolume: null };
  const relativeVolume =
    Number(bars[index].volume) / meanVolume;
  let obv = 0;
  const obvValues: number[] = [];
  for (let cursor = index - 20; cursor <= index; cursor += 1) {
    if (cursor > index - 20) {
      const change = bars[cursor].close - bars[cursor - 1].close;
      obv +=
        Math.sign(change) * Number(bars[cursor].volume);
    }
    obvValues.push(obv);
  }
  const obvSlope =
    (obvValues.at(-1)! - obvValues[obvValues.length - 11]) /
    (meanVolume * Math.sqrt(10));
  const candleDirection = Math.sign(
    bars[index].close - openOf(bars[index]),
  );
  const volumeImpulse =
    candleDirection * clamp(relativeVolume - 1);
  return {
    value: clamp(
      0.6 * Math.tanh(obvSlope) + 0.4 * volumeImpulse,
    ),
    relativeVolume,
  };
}

function overlaps(
  left: Pick<VectorZone, "low" | "high">,
  right: Pick<VectorZone, "low" | "high">,
) {
  return Math.max(left.low, right.low) <=
    Math.min(left.high, right.high);
}

function intersectsBar(zone: VectorZone, bar: VectorBar) {
  return highOf(bar) >= zone.low && lowOf(bar) <= zone.high;
}

function updateZoneLifecycle(
  zone: InternalZone,
  bar: VectorBar,
  atr: number,
  relativeVolume: number | null,
  index: number,
) {
  if (zone.state === "broken") return;
  const beyond =
    zone.polarity === "demand"
      ? bar.close < zone.low - 0.2 * atr
      : bar.close > zone.high + 0.2 * atr;
  zone.breakCloses = beyond ? zone.breakCloses + 1 : 0;
  if (beyond) zone.state = "break-pending";
  else if (zone.state === "break-pending") zone.state = "active";
  if (
    zone.breakCloses >= 2 ||
    (beyond && finite(relativeVolume) && relativeVolume >= 1.5)
  )
    zone.state = "broken";

  const touching = intersectsBar(zone, bar);
  if (touching && !zone.inside && zone.outsideBars >= 3) {
    zone.touches += 1;
    zone.strength = clamp(zone.strength + 0.08, 0, 1);
  }
  if (touching) {
    zone.inside = true;
    zone.outsideBars = 0;
    zone.lastSeenIndex = index;
  } else {
    zone.inside = false;
    const distance =
      bar.close < zone.low
        ? zone.low - bar.close
        : bar.close > zone.high
          ? bar.close - zone.high
          : 0;
    if (distance >= 0.5 * atr)
      zone.outsideBars += 1;
  }
}

function newInternalZone(
  bars: VectorBar[],
  index: number,
  sourceIndex: number,
  polarity: VectorZone["polarity"],
  model: VectorZone["model"],
  modelSource: VectorZone["modelSource"],
  low: number,
  high: number,
  strength: number,
): InternalZone {
  const orderedLow = Math.min(low, high);
  const orderedHigh = Math.max(low, high);
  const knownAt = bars[index]?.time || 0;
  const createdAt = bars[sourceIndex]?.time || knownAt;
  return {
    id: `${model}-${polarity}-${stableId([
      knownAt,
      createdAt,
      orderedLow.toFixed(6),
      orderedHigh.toFixed(6),
    ])}`,
    polarity,
    model,
    modelSource,
    low: orderedLow,
    high: orderedHigh,
    center: (orderedLow + orderedHigh) / 2,
    createdIndex: sourceIndex,
    knownAtIndex: index,
    createdAt,
    knownAt,
    lastSeenIndex: index,
    state: "active" as const,
    touches: 0,
    strength: clamp(strength, 0, 1),
    dualConfirmed: false,
    contextOnly: false,
    breakCloses: 0,
    inside: false,
    outsideBars: 3,
  } satisfies InternalZone;
}

function confirmedPivotAt(
  bars: VectorBar[],
  knownAtIndex: number,
  polarity: VectorZone["polarity"],
  radius = 3,
) {
  const pivotIndex = knownAtIndex - radius;
  if (pivotIndex < radius) return null;
  const start = pivotIndex - radius;
  const end = pivotIndex + radius;
  if (end > knownAtIndex) return null;
  const pivot =
    polarity === "demand"
      ? lowOf(bars[pivotIndex])
      : highOf(bars[pivotIndex]);
  const peers = bars
    .slice(start, end + 1)
    .map(bar =>
      polarity === "demand" ? lowOf(bar) : highOf(bar),
    );
  const extreme =
    polarity === "demand"
      ? Math.min(...peers)
      : Math.max(...peers);
  const unique = peers.filter(value => value === extreme).length === 1;
  return pivot === extreme && unique
    ? { pivotIndex, price: pivot }
    : null;
}

type RawDensityZone = {
  polarity: VectorZone["polarity"];
  low: number;
  high: number;
  strength: number;
  sourceIndex: number;
};

function densityZonesForPrefix(
  bars: VectorBar[],
  index: number,
  atr: number,
) {
  if (index < 29 || !(atr > 0)) return [] as RawDensityZone[];
  const start = Math.max(0, index - 149);
  const points = bars.slice(start, index + 1);
  const minimum = Math.min(...points.map(lowOf));
  const maximum = Math.max(...points.map(highOf));
  const cellWidth = Math.max(atr * 0.25, bars[index].close * 0.001);
  const cellCount = Math.min(
    240,
    Math.max(1, Math.ceil((maximum - minimum) / cellWidth) + 1),
  );
  const demand = Array(cellCount).fill(0) as number[];
  const supply = Array(cellCount).fill(0) as number[];
  const lastIndex = Math.max(1, points.length - 1);
  points.forEach((bar, localIndex) => {
    const age = lastIndex - localIndex;
    const weight = 0.5 ** (age / 75);
    const lowCell = Math.max(
      0,
      Math.min(
        cellCount - 1,
        Math.floor((lowOf(bar) - minimum) / cellWidth),
      ),
    );
    const highCell = Math.max(
      0,
      Math.min(
        cellCount - 1,
        Math.floor((highOf(bar) - minimum) / cellWidth),
      ),
    );
    demand[lowCell] += weight;
    supply[highCell] += weight;
  });

  const candidates: RawDensityZone[] = [];
  const extract = (
    weights: number[],
    polarity: VectorZone["polarity"],
  ) => {
    const positive = weights.filter(value => value > 0);
    if (!positive.length) return;
    const sorted = [...positive].sort((left, right) => left - right);
    const cutoff = sorted[Math.floor((sorted.length - 1) * 0.78)];
    const maximumWeight = Math.max(...positive);
    let cursor = 0;
    while (cursor < weights.length) {
      if (weights[cursor] < cutoff || weights[cursor] <= 0) {
        cursor += 1;
        continue;
      }
      const groupStart = cursor;
      let groupEnd = cursor;
      let groupWeight = weights[cursor];
      while (
        groupEnd + 1 < weights.length &&
        weights[groupEnd + 1] >= cutoff
      ) {
        groupEnd += 1;
        groupWeight += weights[groupEnd];
      }
      const rawLow = minimum + groupStart * cellWidth;
      const rawHigh =
        minimum + Math.min(cellCount, groupEnd + 1) * cellWidth;
      // Anna's visible bands are compact price clusters rather than the full
      // width of an unbounded histogram lobe. Keep the cluster evidence, but
      // cap its displayed span so a distant tail cannot distort the axis.
      const maximumBandWidth = Math.max(
        0.8 * atr,
        Math.min(1.35 * atr, bars[index].close * 0.018),
      );
      const rawCenter = (rawLow + rawHigh) / 2;
      const clippedLow =
        rawHigh - rawLow > maximumBandWidth
          ? rawCenter - maximumBandWidth / 2
          : rawLow;
      const clippedHigh =
        rawHigh - rawLow > maximumBandWidth
          ? rawCenter + maximumBandWidth / 2
          : rawHigh;
      candidates.push({
        polarity,
        low: clippedLow,
        high: clippedHigh,
        strength: clamp(
          groupWeight /
            Math.max(maximumWeight * Math.max(1, groupEnd - groupStart + 1), 1),
          0.18,
          1,
        ),
        sourceIndex: start,
      });
      cursor = groupEnd + 1;
    }
  };
  extract(demand, "demand");
  extract(supply, "supply");
  const close = bars[index].close;
  return candidates
    .sort((left, right) => {
      const leftDistance = Math.abs((left.low + left.high) / 2 - close);
      const rightDistance = Math.abs(
        (right.low + right.high) / 2 - close,
      );
      return leftDistance - rightDistance;
    })
    .filter((candidate, candidateIndex, all) =>
      all
        .slice(0, candidateIndex)
        .filter(peer => peer.polarity === candidate.polarity)
        .every(peer => !overlaps(peer, candidate)),
    )
    .filter(candidate =>
      candidate.polarity === "demand"
        ? candidate.low <= close + atr
        : candidate.high >= close - atr,
    )
    .filter(
      candidate =>
        Math.abs((candidate.low + candidate.high) / 2 - close) <=
        5 * atr,
    )
    .reduce<RawDensityZone[]>((selected, candidate) => {
      if (
        selected.filter(
          zone => zone.polarity === candidate.polarity,
        ).length < 3
      )
        selected.push(candidate);
      return selected;
    }, []);
}

function syncDensityZones(
  zones: InternalZone[],
  candidates: RawDensityZone[],
  bars: VectorBar[],
  index: number,
  atr: number,
) {
  const matched = new Set<string>();
  for (const candidate of candidates) {
    const center = (candidate.low + candidate.high) / 2;
    const existing = zones
      .filter(
        zone =>
          zone.model === "C" &&
          zone.polarity === candidate.polarity &&
          zone.state !== "broken",
      )
      .sort(
        (left, right) =>
          Math.abs(left.center - center) -
          Math.abs(right.center - center),
      )[0];
    if (existing && Math.abs(existing.center - center) <= 0.5 * atr) {
      existing.low = candidate.low;
      existing.high = candidate.high;
      existing.center = center;
      existing.lastSeenIndex = index;
      existing.strength = clamp(
        0.65 * existing.strength + 0.35 * candidate.strength,
        0,
        1,
      );
      matched.add(existing.id);
    } else {
      const created = newInternalZone(
        bars,
        index,
        candidate.sourceIndex,
        candidate.polarity,
        "C",
        "cell-density",
        candidate.low,
        candidate.high,
        candidate.strength,
      );
      zones.push(created);
      matched.add(created.id);
    }
  }
  for (const zone of zones) {
    if (
      zone.model === "C" &&
      zone.state !== "broken" &&
      !matched.has(zone.id) &&
      index - zone.lastSeenIndex > 15
    )
      zone.state = "broken";
  }
}

function addPivotZone(
  zones: InternalZone[],
  bars: VectorBar[],
  atr: number,
  knownAtIndex: number,
  polarity: VectorZone["polarity"],
) {
  const pivot = confirmedPivotAt(
    bars,
    knownAtIndex,
    polarity,
  );
  if (!pivot) return;
  const width = 0.55 * atr;
  const low =
    polarity === "demand" ? pivot.price : pivot.price - width;
  const high =
    polarity === "demand" ? pivot.price + width : pivot.price;
  const candidate = { low, high };
  const duplicate = zones.find(
    zone =>
      zone.model === "A" &&
      zone.polarity === polarity &&
      zone.state !== "broken" &&
      overlaps(zone, candidate),
  );
  if (duplicate) {
    duplicate.strength = clamp(duplicate.strength + 0.06, 0, 1);
    duplicate.lastSeenIndex = knownAtIndex;
    return;
  }
  zones.push(
    newInternalZone(
      bars,
      knownAtIndex,
      pivot.pivotIndex,
      polarity,
      "A",
      "pivot-band",
      low,
      high,
      0.48,
    ),
  );
}

function referenceZoneForMissingPolarity(
  bars: VectorBar[],
  atr: Array<number | null>,
  polarity: VectorZone["polarity"],
) {
  const latestIndex = bars.length - 1;
  const latestClose = bars.at(-1)?.close;
  if (latestIndex < 1 || !finite(latestClose)) return null;

  let best:
    | {
        pivotIndex: number;
        knownAtIndex: number;
        price: number;
        atr: number;
        score: number;
      }
    | null = null;
  const firstKnownAt = Math.max(3, latestIndex - 220);
  for (
    let knownAtIndex = latestIndex;
    knownAtIndex >= firstKnownAt;
    knownAtIndex -= 1
  ) {
    const currentAtr = atr[knownAtIndex];
    if (!finite(currentAtr) || !(currentAtr > 0)) continue;
    const pivot = confirmedPivotAt(
      bars,
      knownAtIndex,
      polarity,
    );
    if (!pivot) continue;
    const directionalPenalty =
      polarity === "demand"
        ? pivot.price > latestClose
          ? 2 * currentAtr
          : 0
        : pivot.price < latestClose
          ? 2 * currentAtr
          : 0;
    const distance = Math.abs(pivot.price - latestClose);
    const agePenalty =
      (latestIndex - knownAtIndex) * currentAtr * 0.0025;
    const score =
      (distance + directionalPenalty) / currentAtr + agePenalty;
    if (!best || score < best.score)
      best = {
        pivotIndex: pivot.pivotIndex,
        knownAtIndex,
        price: pivot.price,
        atr: currentAtr,
        score,
      };
  }
  if (!best) return null;
  const width = Math.max(
    0.4 * best.atr,
    Math.min(0.65 * best.atr, latestClose * 0.009),
  );
  const low =
    polarity === "demand" ? best.price : best.price - width;
  const high =
    polarity === "demand" ? best.price + width : best.price;
  const zone = newInternalZone(
    bars,
    best.knownAtIndex,
    best.pivotIndex,
    polarity,
    "A",
    "pivot-band",
    low,
    high,
    0.24,
  );
  zone.contextOnly = true;
  return zone;
}

function markDualConfirmation(zones: InternalZone[]) {
  for (const zone of zones) zone.dualConfirmed = false;
  const active = zones.filter(zone => zone.state !== "broken");
  for (const zone of active) {
    zone.dualConfirmed = active.some(
      peer =>
        peer.id !== zone.id &&
        peer.model !== zone.model &&
        peer.polarity === zone.polarity &&
        overlaps(zone, peer),
    );
    if (zone.dualConfirmed)
      zone.strength = clamp(zone.strength + 0.015, 0, 1);
  }
}

type VectorActionZone = Pick<
  VectorZone,
  "low" | "high" | "strength" | "dualConfirmed"
>;

/**
 * Classifies only the three scarce Vector action glyphs. The zone is supplied
 * from the prior-bar snapshot by the caller, so this helper cannot discover a
 * level using the candle it is judging.
 */
export function classifyVectorActionSignal({
  bar,
  previous,
  atr,
  relativeVolume,
  demand,
  supply,
}: {
  bar: VectorBar;
  previous: VectorBar | null;
  atr: number;
  relativeVolume: number | null;
  demand: VectorActionZone | null;
  supply: VectorActionZone | null;
}): VectorActionSignalTrigger | null {
  if (!previous || !finite(atr) || atr <= 0) return null;
  const range = Math.max(highOf(bar) - lowOf(bar), atr * 0.01);
  const body = Math.abs(bar.close - openOf(bar));
  const closeLocation = (bar.close - lowOf(bar)) / range;
  const lowerWick = Math.min(openOf(bar), bar.close) - lowOf(bar);
  const participationConfirmed =
    finite(relativeVolume) && relativeVolume >= 1.1;
  const zoneQualityConfirmed = (zone: VectorActionZone) =>
    zone.dualConfirmed || zone.strength >= 0.58;
  const evidenceConfirmed = (zone: VectorActionZone) =>
    participationConfirmed ||
    (!finite(relativeVolume) && zoneQualityConfirmed(zone));

  if (
    demand &&
    previous.close >= demand.high &&
    lowOf(bar) <= demand.high + 0.08 * atr &&
    lowOf(bar) >= demand.low - 0.2 * atr &&
    bar.close >= demand.high + 0.03 * atr &&
    bar.close > openOf(bar) &&
    lowerWick >= Math.max(0.15 * atr, 0.65 * body) &&
    closeLocation >= 0.68 &&
    zoneQualityConfirmed(demand) &&
    evidenceConfirmed(demand)
  )
    return "demand-bounce";
  if (
    supply &&
    previous.close <= supply.high + 0.03 * atr &&
    openOf(bar) <= supply.high + 0.05 * atr &&
    lowOf(bar) <= supply.high &&
    bar.close >= supply.high + 0.12 * atr &&
    body >= 0.3 * atr &&
    closeLocation >= 0.72 &&
    zoneQualityConfirmed(supply) &&
    evidenceConfirmed(supply)
  )
    return "supply-breakout";
  if (
    demand &&
    previous.close >= demand.low - 0.03 * atr &&
    openOf(bar) >= demand.low - 0.05 * atr &&
    highOf(bar) >= demand.low &&
    bar.close <= demand.low - 0.12 * atr &&
    body >= 0.3 * atr &&
    closeLocation <= 0.28 &&
    zoneQualityConfirmed(demand) &&
    evidenceConfirmed(demand)
  )
    return "demand-breakdown";
  return null;
}

function locationFamily(
  bars: VectorBar[],
  index: number,
  atr: number,
  zones: InternalZone[],
  relativeVolume: number | null,
): {
  value: number | null;
  trigger: VectorBarResult["locationTrigger"];
  zone: InternalZone | null;
} {
  const bar = bars[index];
  const previous = bars[index - 1];
  const active = zones.filter(
    zone =>
      zone.state !== "broken" &&
      zone.knownAtIndex <= index &&
      (zone.model !== "C" || index - zone.lastSeenIndex <= 15),
  );
  const demand = active
    .filter(zone => zone.polarity === "demand")
    .sort(
      (left, right) =>
        Math.abs(left.center - bar.close) -
        Math.abs(right.center - bar.close),
    )[0];
  const supply = active
    .filter(zone => zone.polarity === "supply")
    .sort(
      (left, right) =>
        Math.abs(left.center - bar.close) -
        Math.abs(right.center - bar.close),
    )[0];
  const priorHigh =
    index >= 20
      ? Math.max(...bars.slice(index - 20, index).map(highOf))
      : null;
  const priorLow =
    index >= 20
      ? Math.min(...bars.slice(index - 20, index).map(lowOf))
      : null;
  const actionTrigger = classifyVectorActionSignal({
    bar,
    previous: previous ?? null,
    atr,
    relativeVolume,
    demand: demand ?? null,
    supply: supply ?? null,
  });
  if (actionTrigger)
    return {
      value: actionTrigger === "demand-breakdown" ? -1 : 1,
      trigger: actionTrigger,
      zone: actionTrigger === "supply-breakout" ? supply : demand,
    };
  if (
    demand &&
    lowOf(bar) <= demand.high + 0.1 * atr &&
    bar.close >= demand.high &&
    previous &&
    previous.close < demand.high
  )
    return {
      value: 1,
      trigger: "demand-reclaim" as const,
      zone: demand,
    };
  if (
    demand &&
    lowOf(bar) <= demand.high + 0.1 * atr &&
    bar.close >= demand.center
  )
    return {
      value: 0.85,
      trigger: "demand-hold" as const,
      zone: demand,
    };
  if (
    supply &&
    highOf(bar) >= supply.low - 0.1 * atr &&
    bar.close <= supply.low &&
    previous &&
    previous.close > supply.low
  )
    return {
      value: -1,
      trigger: "supply-loss" as const,
      zone: supply,
    };
  if (
    supply &&
    highOf(bar) >= supply.low - 0.1 * atr &&
    bar.close <= supply.center
  )
    return {
      value: -0.85,
      trigger: "supply-rejection" as const,
      zone: supply,
    };
  if (finite(priorHigh) && bar.close > priorHigh)
    return {
      value: 0.5,
      trigger: "range-breakout" as const,
      zone: null,
    };
  if (finite(priorLow) && bar.close < priorLow)
    return {
      value: -0.5,
      trigger: "range-breakdown" as const,
      zone: null,
    };
  const demandDistance = demand
    ? Math.max(0, bar.close - demand.high, demand.low - bar.close)
    : Number.POSITIVE_INFINITY;
  const supplyDistance = supply
    ? Math.max(0, bar.close - supply.high, supply.low - bar.close)
    : Number.POSITIVE_INFINITY;
  if (demandDistance <= 0.6 * atr && demandDistance <= supplyDistance)
    return {
      value: 0.5,
      trigger: "near-demand" as const,
      zone: demand,
    };
  if (supplyDistance <= 0.6 * atr)
    return {
      value: -0.5,
      trigger: "near-supply" as const,
      zone: supply,
    };
  return { value: 0, trigger: "none" as const, zone: null };
}

function directionalResult(families: VectorFamilies) {
  let weighted = 0;
  let availableWeight = 0;
  (
    [
      ["trend", families.trend],
      ["momentum", families.momentum],
      ["location", families.location],
      ["participation", families.participation],
    ] as const
  ).forEach(([family, value]) => {
    if (!finite(value)) return;
    weighted += FAMILY_WEIGHTS[family] * value;
    availableWeight += FAMILY_WEIGHTS[family];
  });
  if (
    !finite(families.trend) ||
    !finite(families.momentum) ||
    !finite(families.location) ||
    availableWeight < 0.88
  )
    return { resultant: null, coherence: null, availableWeight };
  const resultant = 100 * (weighted / availableWeight);
  const direction = Math.sign(resultant);
  let aligned = 0;
  let directional = 0;
  (
    [
      ["trend", families.trend],
      ["momentum", families.momentum],
      ["location", families.location],
      ["participation", families.participation],
    ] as const
  ).forEach(([family, value]) => {
    if (!finite(value) || Math.abs(value) < 0.05) return;
    directional += FAMILY_WEIGHTS[family] * Math.abs(value);
    if (Math.sign(value) === direction)
      aligned += FAMILY_WEIGHTS[family] * Math.abs(value);
  });
  return {
    resultant,
    coherence: directional > 0 ? aligned / directional : 0,
    availableWeight,
  };
}

function trendFamily(
  close: number,
  atr: number,
  ema21: number,
  ema55: number,
  ema200: number | null,
) {
  const pieces = [
    {
      weight: 0.4,
      value: Math.tanh((close - ema55) / (1.5 * atr)),
    },
    {
      weight: 0.35,
      value: Math.tanh((ema21 - ema55) / atr),
    },
    ...(finite(ema200)
      ? [
          {
            weight: 0.25,
            value: Math.tanh((ema55 - ema200) / (1.5 * atr)),
          },
        ]
      : []),
  ];
  const weight = pieces.reduce((sum, piece) => sum + piece.weight, 0);
  return clamp(
    pieces.reduce(
      (sum, piece) => sum + piece.weight * piece.value,
      0,
    ) / weight,
  );
}

function momentumFamily(
  rsi: number,
  histogram: number,
  previousHistogram: number,
  atr: number,
) {
  return clamp(
    0.45 * clamp((rsi - 50) / 25) +
      0.35 * Math.tanh((8 * histogram) / atr) +
      0.2 *
        Math.tanh((8 * (histogram - previousHistogram)) / atr),
  );
}

function resultDirection(resultant: number | null) {
  if (!finite(resultant) || Math.abs(resultant) < 15)
    return "neutral" as const;
  return resultant > 0 ? "bullish" as const : "bearish" as const;
}

function classifyState(args: {
  bars: VectorBar[];
  index: number;
  families: VectorFamilies;
  resultant: number | null;
  coherence: number | null;
  resultHistory: Array<number | null>;
  locationTrigger: VectorBarResult["locationTrigger"];
  rsi: number;
  histogram: number;
  previousHistogram: number;
}) {
  const {
    bars,
    index,
    families,
    resultant,
    coherence,
    resultHistory,
    locationTrigger,
    rsi,
    histogram,
    previousHistogram,
  } = args;
  const reasons: string[] = [];
  const vetoes: string[] = [];
  if (!finite(resultant) || !finite(coherence))
    return {
      state: "NEUTRAL" as const,
      reasons,
      vetoes: ["Trend, momentum, and location require more closed bars."],
      nextConfirmation: "Wait for sufficient completed-bar evidence.",
    };
  const trend = Number(families.trend);
  const momentum = Number(families.momentum);
  const location = Number(families.location);
  const signConflict =
    Math.sign(trend) !== Math.sign(momentum) &&
    Math.abs(trend) >= 0.45 &&
    Math.abs(momentum) >= 0.45;
  const locationConflict =
    Math.abs(resultant) >= 45 &&
    Math.abs(location) >= 0.5 &&
    Math.sign(location) !== Math.sign(resultant);
  if (signConflict || locationConflict) {
    if (signConflict)
      vetoes.push("Trend and momentum point in opposite directions.");
    if (locationConflict)
      vetoes.push("Price location opposes the directional vector.");
    return {
      state: "CONFLICT" as const,
      reasons,
      vetoes,
      nextConfirmation:
        "Require trend, momentum, and location to regain directional agreement on a completed bar.",
    };
  }

  const recent = resultHistory.slice(Math.max(0, index - 3), index);
  const buyCross =
    resultant >= 68 &&
    recent.every(value => !finite(value) || value < 68);
  const sellCross =
    resultant <= -68 &&
    recent.every(value => !finite(value) || value > -68);
  const bullishTrigger = [
    "demand-bounce",
    "demand-hold",
    "demand-reclaim",
    "supply-breakout",
    "range-breakout",
  ].includes(locationTrigger);
  const bearishTrigger = [
    "supply-rejection",
    "supply-loss",
    "demand-breakdown",
    "range-breakdown",
  ].includes(locationTrigger);
  if (
    buyCross &&
    trend >= 0.35 &&
    momentum >= 0.35 &&
    location >= 0.5 &&
    coherence >= 0.72 &&
    bullishTrigger
  ) {
    reasons.push(
      "Trend, momentum, and location cleared the bullish threshold.",
      "A completed-bar price trigger confirmed the move.",
    );
    return {
      state: "VECTOR_BUY" as const,
      reasons,
      vetoes,
      nextConfirmation:
        "Watch for a completed close that preserves the reclaimed level.",
    };
  }
  if (
    sellCross &&
    trend <= -0.35 &&
    momentum <= -0.35 &&
    location <= -0.5 &&
    coherence >= 0.72 &&
    bearishTrigger
  ) {
    reasons.push(
      "Trend, momentum, and location cleared the bearish threshold.",
      "A completed-bar price trigger confirmed the move.",
    );
    return {
      state: "VECTOR_SELL" as const,
      reasons,
      vetoes,
      nextConfirmation:
        "Watch for a completed close that remains below the lost level.",
    };
  }

  const previous = bars[index - 1];
  const bullishReversal =
    rsi <= 32 &&
    histogram > previousHistogram &&
    ["demand-bounce", "demand-reclaim", "demand-hold"].includes(locationTrigger) &&
    previous &&
    bars[index].close > openOf(bars[index]);
  const bearishReversal =
    rsi >= 68 &&
    histogram < previousHistogram &&
    ["supply-rejection", "supply-loss", "demand-breakdown"].includes(locationTrigger) &&
    previous &&
    bars[index].close < openOf(bars[index]);
  if (bullishReversal || bearishReversal) {
    reasons.push(
      "An extreme oscillator reading turned at a measured price zone.",
    );
    return {
      state: "REVERSAL_WINDOW" as const,
      reasons,
      vetoes,
      nextConfirmation: bullishReversal
        ? "Require follow-through above the reversal bar."
        : "Require follow-through below the reversal bar.",
    };
  }

  const forming =
    Math.abs(resultant) >= 45 &&
    Math.abs(resultant) < 68 &&
    Math.sign(trend) === Math.sign(resultant) &&
    Math.sign(momentum) === Math.sign(resultant) &&
    (Math.abs(location) >= 0.5 ||
      Number(families.volatilityReadiness) >= 0.65);
  if (forming) {
    reasons.push(
      "The directional families are aligned but have not cleared the primary threshold.",
    );
    return {
      state: "SETUP_FORMING" as const,
      reasons,
      vetoes,
      nextConfirmation:
        resultant > 0
          ? "Require a completed demand hold, reclaim, or range breakout with Tensor at 68 or higher."
          : "Require a completed supply rejection, loss, or range breakdown with Tensor at -68 or lower.",
    };
  }

  if (Math.abs(resultant) >= 68 && coherence < 0.72)
    vetoes.push("Directional coherence is below 72%.");
  if (resultant > 0 && !bullishTrigger)
    vetoes.push("No completed bullish price trigger is present.");
  if (resultant < 0 && !bearishTrigger)
    vetoes.push("No completed bearish price trigger is present.");
  return {
    state: "NEUTRAL" as const,
    reasons,
    vetoes,
    nextConfirmation:
      "Wait for a completed bar that aligns trend, momentum, and location.",
  };
}

function anchoredVwapSeries(
  bars: VectorBar[],
  zones: VectorZone[],
) {
  const output = Array<number | null>(bars.length).fill(null);
  const anchors = zones
    .filter(
      zone =>
        zone.model === "A" &&
        zone.state !== "broken" &&
        !zone.contextOnly,
    )
    .sort((left, right) => right.knownAtIndex - left.knownAtIndex);
  const anchorIndex = anchors[0]?.createdIndex ?? Math.max(0, bars.length - 63);
  let weightedPrice = 0;
  let weight = 0;
  for (let index = anchorIndex; index < bars.length; index += 1) {
    const bar = bars[index];
    const typical = (highOf(bar) + lowOf(bar) + bar.close) / 3;
    const volume =
      finite(bar.volume) && bar.volume > 0 ? bar.volume : 1;
    weightedPrice += typical * volume;
    weight += volume;
    output[index] = weight > 0 ? weightedPrice / weight : null;
  }
  return output;
}

function fibForBars(bars: VectorBar[]) {
  if (bars.length < 2) return null;
  const start = Math.max(0, bars.length - 63);
  let low = Number.POSITIVE_INFINITY;
  let high = Number.NEGATIVE_INFINITY;
  let lowIndex = start;
  let highIndex = start;
  for (let index = start; index < bars.length; index += 1) {
    const barLow = lowOf(bars[index]);
    const barHigh = highOf(bars[index]);
    if (barLow < low) {
      low = barLow;
      lowIndex = index;
    }
    if (barHigh > high) {
      high = barHigh;
      highIndex = index;
    }
  }
  if (!finite(low) || !finite(high) || !(high > low)) return null;
  const rising = lowIndex <= highIndex;
  const ratios = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1];
  return {
    low,
    high,
    lowIndex,
    highIndex,
    levels: ratios.map(ratio => ({
      ratio,
      value: rising
        ? high - (high - low) * ratio
        : low + (high - low) * ratio,
    })),
  };
}

function sanitizeBars(input: VectorBar[]) {
  const byTime = new Map<number, VectorBar>();
  for (const bar of input) {
    if (
      !finite(bar.time) ||
      !finite(bar.close) ||
      !(bar.close > 0)
    )
      continue;
    const normalized = {
      time: Math.floor(bar.time),
      open: finite(bar.open) ? bar.open : null,
      high: finite(bar.high) ? bar.high : null,
      low: finite(bar.low) ? bar.low : null,
      close: bar.close,
      volume:
        finite(bar.volume) && bar.volume >= 0 ? bar.volume : null,
    };
    if (
      finite(normalized.high) &&
      finite(normalized.low) &&
      normalized.high < normalized.low
    )
      continue;
    byTime.set(normalized.time, normalized);
  }
  return [...byTime.values()].sort((left, right) => left.time - right.time);
}

export function analyzeVectorBars(
  input: VectorBar[],
  {
    summaryOnly = false,
    minimumBars = 200,
    requireEma200 = true,
  }: { summaryOnly?: boolean; minimumBars?: number; requireEma200?: boolean } = {},
): VectorAnalysis {
  const bars = sanitizeBars(input);
  const closes = bars.map(bar => bar.close);
  const ema21 = emaSeries(closes, 21);
  const ema55 = emaSeries(closes, 55);
  const ema200 = emaSeries(closes, 200);
  const atr14 = atrSeries(bars, 14);
  // Each 20-close width depends only on its own prefix. Compute it once;
  // rolling ranks below keep the original arithmetic and 100-bar window.
  const widthByIndex = volatilityWidths(bars);
  const rsi14 = rsiSeries(closes, 14);
  const macd = macdSeries(closes);
  const zones: InternalZone[] = [];
  const causalZonesByIndex: VectorZone[][] = [];
  const results: VectorBarResult[] = [];
  const resultantHistory: Array<number | null> = [];
  const causalLocationEvents: VectorCausalLocationEvent[] = [];
  let causalEpisodeKey: string | null = null;

  for (let index = 0; index < bars.length; index += 1) {
    const atr = atr14[index];
    const participation = participationFamily(bars, index);
    // Freeze eligible zone geometry before the current bar is allowed to add,
    // reshape, confirm, or break a zone. Strict `< index` is the causal alert
    // contract: the zone had to be knowable before this candle opened.
    const priorZones = zones
      .filter(
        zone =>
          zone.state !== "broken" &&
          zone.knownAtIndex < index,
      )
      .map(zone => ({ ...zone }));
    if (!summaryOnly) {
      causalZonesByIndex.push(
        priorZones.map(zone => ({
          id: zone.id,
          polarity: zone.polarity,
          model: zone.model,
          modelSource: zone.modelSource,
          low: zone.low,
          high: zone.high,
          center: zone.center,
          createdIndex: zone.createdIndex,
          knownAtIndex: zone.knownAtIndex,
          createdAt: zone.createdAt,
          knownAt: zone.knownAt,
          lastSeenIndex: zone.lastSeenIndex,
          state: zone.state,
          touches: zone.touches,
          strength: zone.strength,
          dualConfirmed: zone.dualConfirmed,
          contextOnly: zone.contextOnly,
        })),
      );
    }
    const causalLocation =
      finite(atr) && atr > 0
        ? locationFamily(
            bars,
            index,
            atr,
            priorZones,
            participation.relativeVolume,
          )
        : { value: null, trigger: "none" as const, zone: null };
    if (finite(atr) && atr > 0) {
      addPivotZone(zones, bars, atr, index, "demand");
      addPivotZone(zones, bars, atr, index, "supply");
      syncDensityZones(
        zones,
        densityZonesForPrefix(bars, index, atr),
        bars,
        index,
        atr,
      );
      for (const zone of zones)
        updateZoneLifecycle(
          zone,
          bars[index],
          atr,
          participation.relativeVolume,
          index,
        );
      markDualConfirmation(zones);
    }

    const trend =
      finite(atr) &&
      atr > 0 &&
      finite(ema21[index]) &&
      finite(ema55[index])
        ? trendFamily(
            bars[index].close,
            atr,
            Number(ema21[index]),
            Number(ema55[index]),
            finite(ema200[index]) ? Number(ema200[index]) : null,
          )
        : null;
    const histogram = macd.histogram[index];
    const previousHistogram = macd.histogram[index - 1];
    const momentum =
      finite(atr) &&
      atr > 0 &&
      finite(rsi14[index]) &&
      finite(histogram) &&
      finite(previousHistogram)
        ? momentumFamily(
            Number(rsi14[index]),
            Number(histogram),
            Number(previousHistogram),
            atr,
          )
        : null;
    const location =
      finite(atr) && atr > 0
        ? locationFamily(
            bars,
            index,
            atr,
            zones,
            participation.relativeVolume,
          )
        : { value: null, trigger: "none" as const, zone: null };
    const families: VectorFamilies = {
      trend,
      momentum,
      location: location.value,
      participation: participation.value,
      volatilityReadiness: rollingVolatilityReadiness(
        bars,
        atr14,
        index,
        widthByIndex,
      ),
    };
    const directional = directionalResult(families);
    const causalTrigger = causalLocation.trigger;
    const causalActionable = (
      [
        "demand-bounce",
        "demand-hold",
        "demand-reclaim",
        "supply-breakout",
        "supply-rejection",
        "supply-loss",
        "demand-breakdown",
        "range-breakout",
        "range-breakdown",
      ] as VectorCausalTrigger[]
    ).includes(causalTrigger as VectorCausalTrigger);
    const causalZoneValid =
      causalLocation.zone === null ||
      causalLocation.zone.knownAtIndex < index;
    if (causalActionable && causalZoneValid) {
      const trigger = causalTrigger as VectorCausalTrigger;
      const episodeKey = `${trigger}:${causalLocation.zone?.id || "range"}`;
      if (episodeKey !== causalEpisodeKey) {
        const causalFamilies: VectorFamilies = {
          ...families,
          location: causalLocation.value,
        };
        const causalDirectional = directionalResult(causalFamilies);
        const zone = causalLocation.zone;
        if (!summaryOnly || index === bars.length - 1) causalLocationEvents.push({
          id: `vector-causal-${stableId([
            VECTOR_MODEL_VERSION,
            bars[index].time,
            trigger,
            zone?.id || "range",
          ])}`,
          index,
          time: bars[index].time,
          price: bars[index].close,
          trigger,
          direction: trigger === "demand-bounce" ||
              trigger === "demand-hold" ||
              trigger === "demand-reclaim" ||
              trigger === "supply-breakout" ||
              trigger === "range-breakout"
            ? "bullish"
            : "bearish",
          zone: zone
            ? {
                id: zone.id,
                polarity: zone.polarity,
                model: zone.model,
                modelSource: zone.modelSource,
                low: zone.low,
                high: zone.high,
                center: zone.center,
                knownAtIndex: zone.knownAtIndex,
                knownAt: zone.knownAt,
                state: zone.state,
                touches: zone.touches,
                strength: zone.strength,
                dualConfirmed: zone.dualConfirmed,
              }
            : null,
          families: causalFamilies,
          resultant: causalDirectional.resultant,
          coherence: causalDirectional.coherence,
          relativeVolume: participation.relativeVolume,
        });
      }
      causalEpisodeKey = episodeKey;
    } else {
      causalEpisodeKey = null;
    }
    resultantHistory[index] = directional.resultant;
    const classified =
      finite(rsi14[index]) &&
      finite(histogram) &&
      finite(previousHistogram)
        ? classifyState({
            bars,
            index,
            families,
            resultant: directional.resultant,
            coherence: directional.coherence,
            resultHistory: resultantHistory,
            locationTrigger: location.trigger,
            rsi: Number(rsi14[index]),
            histogram: Number(histogram),
            previousHistogram: Number(previousHistogram),
          })
        : {
            state: "NEUTRAL" as const,
            reasons: [] as string[],
            vetoes: [
              "Momentum evidence is still warming.",
            ],
            nextConfirmation:
              "Wait for sufficient completed-bar evidence.",
          };
    const resultant = directional.resultant;
    const result: VectorBarResult = {
      index,
      time: bars[index].time,
      close: bars[index].close,
      finality: "closed",
      primaryMarkers: [],
      state: classified.state,
      direction:
        classified.state === "CONFLICT"
          ? "mixed"
          : resultDirection(resultant),
      resultant,
      coherence: directional.coherence,
      regime:
        finite(resultant) && resultant >= 22
          ? "constructive"
          : finite(resultant) && resultant <= -22
            ? "defensive"
            : "balanced",
      families,
      atr: finite(atr) ? atr : null,
      rsi: finite(rsi14[index]) ? Number(rsi14[index]) : null,
      macdHistogram: finite(histogram) ? Number(histogram) : null,
      relativeVolume: participation.relativeVolume,
      locationTrigger: location.trigger,
      reasons: classified.reasons,
      vetoes: classified.vetoes,
      nextConfirmation: classified.nextConfirmation,
    };
    if (!summaryOnly || index === bars.length - 1) results.push(result);
  }

  const events: VectorEvent[] = [];
  if (!summaryOnly) {
    for (let index = 0; index < results.length; index += 1) {
      const result = results[index];
      if (result.state === "NEUTRAL") continue;
      const previousState = results[index - 1]?.state || "NEUTRAL";
      if (result.state === previousState) continue;
      events.push({
        id: `vector-${stableId([
          VECTOR_MODEL_VERSION,
          result.time,
          result.state,
          result.close.toFixed(8),
        ])}`,
        index,
        time: result.time,
        price: result.close,
        state: result.state,
        direction: result.direction,
        resultant: result.resultant,
      });
    }
  }

  const toPublicZone = (zone: InternalZone): VectorZone => ({
    id: zone.id,
    polarity: zone.polarity,
    model: zone.model,
    modelSource: zone.modelSource,
    low: zone.low,
    high: zone.high,
    center: zone.center,
    createdIndex: zone.createdIndex,
    knownAtIndex: zone.knownAtIndex,
    createdAt: zone.createdAt,
    knownAt: zone.knownAt,
    lastSeenIndex: zone.lastSeenIndex,
    state: zone.state,
    touches: zone.touches,
    strength: zone.strength,
    dualConfirmed: zone.dualConfirmed,
    contextOnly: zone.contextOnly,
  });

  const publicZones = zones
    .filter(
      zone =>
        zone.state !== "broken" &&
        zone.knownAtIndex < bars.length &&
        (zone.model !== "C" ||
          bars.length - 1 - zone.lastSeenIndex <= 15),
    )
    .map(toPublicZone)
    .sort((left, right) => {
      if (left.polarity !== right.polarity)
        return left.polarity.localeCompare(right.polarity);
      return right.strength - left.strength;
    });
  const displayZones = [...publicZones];
  for (const polarity of ["demand", "supply"] as const) {
    if (displayZones.some(zone => zone.polarity === polarity))
      continue;
    const reference = referenceZoneForMissingPolarity(
      bars,
      atr14,
      polarity,
    );
    if (reference) displayZones.push(toPublicZone(reference));
  }
  displayZones.sort((left, right) => {
    if (left.polarity !== right.polarity)
      return left.polarity.localeCompare(right.polarity);
    return right.strength - left.strength;
  });
  const anchoredVwap = summaryOnly
    ? []
    : anchoredVwapSeries(bars, publicZones);
  const current = results.at(-1) || null;
  return {
    modelVersion: VECTOR_MODEL_VERSION,
    status:
      !bars.length
        ? "unavailable"
        : bars.length < minimumBars ||
            (requireEma200 && !finite(ema200.at(-1))) ||
            !finite(current?.resultant)
          ? "warming"
          : "ready",
    bars: results,
    zones: publicZones,
    causalZonesByIndex: summaryOnly ? [] : causalZonesByIndex,
    displayZones,
    events,
    causalLocationEvents: summaryOnly ? causalLocationEvents.slice(-1) : causalLocationEvents,
    current,
    series: {
      ema21: summaryOnly ? [] : ema21,
      ema55: summaryOnly ? [] : ema55,
      ema200: summaryOnly ? [] : ema200,
      atr14: summaryOnly ? [] : atr14,
      rsi14: summaryOnly ? [] : rsi14,
      macdHistogram: summaryOnly ? [] : macd.histogram,
      anchoredVwap,
    },
    fib: summaryOnly ? null : fibForBars(bars),
    evidence: {
      completedBars: bars.length,
      firstTime: bars[0]?.time || null,
      lastTime: bars.at(-1)?.time || null,
      volumeAvailable: bars.filter(bar => finite(bar.volume)).length,
      volumeTotal: bars.length,
      pivotRadius: 3,
      zoneModels: ["A", "C"],
    },
  };
}

export function vectorStateLabel(state: VectorState) {
  return {
    VECTOR_BUY: "Tensor Buy",
    VECTOR_SELL: "Tensor Sell",
    SETUP_FORMING: "Setup Forming",
    REVERSAL_WINDOW: "Reversal Window",
    CONFLICT: "Conflict",
    NEUTRAL: "Neutral",
  }[state];
}

export function vectorStateDescription(state: VectorState) {
  return {
    VECTOR_BUY:
      "Bullish threshold crossing confirmed by trend, momentum, location, and a completed price trigger.",
    VECTOR_SELL:
      "Bearish threshold crossing confirmed by trend, momentum, location, and a completed price trigger.",
    SETUP_FORMING:
      "Directional evidence is aligning, but the primary completed-bar threshold has not cleared.",
    REVERSAL_WINDOW:
      "A secondary exhaustion turn is present at a measured zone; follow-through is still required.",
    CONFLICT:
      "Strong evidence families disagree, so the model withholds a directional signal.",
    NEUTRAL:
      "No completed-bar Tensor condition is active.",
  }[state];
}
