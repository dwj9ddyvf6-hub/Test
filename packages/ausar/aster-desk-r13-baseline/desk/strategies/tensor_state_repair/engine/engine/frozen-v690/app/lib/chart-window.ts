export function chartBarGlyph(point: {
  open: number | null;
  high: number | null;
  low: number | null;
  close: number;
}) {
  return [point.open, point.high, point.low].every(Number.isFinite)
    ? ({
        kind: "candle" as const,
        open: Number(point.open),
        high: Number(point.high),
        low: Number(point.low),
        close: point.close,
      })
    : ({ kind: "close-only" as const, close: point.close });
}

export function emaSeries(values: number[], period: number) {
  const output = Array<number | null>(values.length).fill(null);
  if (values.length < period) return output;
  let seed =
    values.slice(0, period).reduce((sum, value) => sum + value, 0) /
    period;
  output[period - 1] = seed;
  const multiplier = 2 / (period + 1);
  for (let index = period; index < values.length; index++) {
    seed = (values[index] - seed) * multiplier + seed;
    output[index] = seed;
  }
  return output;
}

export function rsiSeries(values: number[], period = 14) {
  const output = Array<number | null>(values.length).fill(null);
  if (values.length <= period) return output;
  let gains = 0;
  let losses = 0;
  for (let index = 1; index <= period; index++) {
    const change = values[index] - values[index - 1];
    if (change >= 0) gains += change;
    else losses -= change;
  }
  let averageGain = gains / period;
  let averageLoss = losses / period;
  const calculate = () =>
    averageLoss === 0
      ? averageGain > 0
        ? 100
        : 50
      : 100 - 100 / (1 + averageGain / averageLoss);
  output[period] = calculate();
  for (let index = period + 1; index < values.length; index++) {
    const change = values[index] - values[index - 1];
    averageGain =
      (averageGain * (period - 1) + Math.max(change, 0)) / period;
    averageLoss =
      (averageLoss * (period - 1) + Math.max(-change, 0)) / period;
    output[index] = calculate();
  }
  return output;
}

export function macdSeries(
  values: number[],
  fastPeriod = 12,
  slowPeriod = 26,
  signalPeriod = 9,
) {
  const fast = emaSeries(values, fastPeriod);
  const slow = emaSeries(values, slowPeriod);
  const line = values.map((_, index) =>
    fast[index] != null && slow[index] != null
      ? Number(fast[index]) - Number(slow[index])
      : null,
  );
  const compact = line.filter((value): value is number => value != null);
  const compactSignal = emaSeries(compact, signalPeriod);
  const signal = Array<number | null>(values.length).fill(null);
  let compactIndex = 0;
  line.forEach((value, index) => {
    if (value == null) return;
    signal[index] = compactSignal[compactIndex] ?? null;
    compactIndex += 1;
  });
  return {
    line,
    signal,
    histogram: line.map((value, index) =>
      value != null && signal[index] != null
        ? value - Number(signal[index])
        : null,
    ),
  };
}

export function simpleMovingAverage(
  values: Array<number | null>,
  period: number,
) {
  return values.map((_, index) => {
    if (index + 1 < period) return null;
    const window = values.slice(index + 1 - period, index + 1);
    if (window.some((value) => value == null)) return null;
    return (
      window.reduce<number>((sum, value) => sum + Number(value), 0) / period
    );
  });
}

export function chartWindow(length: number, zoom: number, pan: number) {
  const safeLength = Math.max(0, Math.floor(length));
  const safeZoom = Math.max(1, Math.min(6, zoom));
  const visibleCount = Math.min(
    safeLength,
    Math.max(20, Math.ceil(safeLength / safeZoom)),
  );
  const maxPan = Math.max(0, safeLength - visibleCount);
  const safePan = Math.max(0, Math.min(maxPan, Math.floor(pan)));
  const end = Math.max(visibleCount, safeLength - safePan);
  return {
    start: Math.max(0, end - visibleCount),
    end,
    visibleCount,
    maxPan,
  };
}

type PriceDomainPoint = {
  high?: number | null;
  low?: number | null;
  close: number;
};

export type PriceDomainOptions = {
  /** Focus a long-history axis on the current regime when old prices are extreme. */
  focusRecentRegime?: boolean;
};

/** Number of completed weekly bars used for a readable recent-regime display axis. */
export const WEEKLY_PRICE_FOCUS_BARS = 26;

function percentile(sorted: number[], fraction: number) {
  if (!sorted.length) return 0;
  const index = Math.max(
    0,
    Math.min(sorted.length - 1, Math.floor((sorted.length - 1) * fraction)),
  );
  return sorted[index];
}

/**
 * Builds an axis-only candle population that resists isolated stale,
 * split-distorted, or malformed bars. The complete series is still drawn;
 * this only controls which values are allowed to flatten the useful scale.
 */
export function robustPriceDomainValues(
  points: PriceDomainPoint[],
  options: PriceDomainOptions = {},
) {
  const validPoints = points.filter(point =>
    Number.isFinite(point.close) && point.close > 0,
  );
  const allValues = validPoints.flatMap(point =>
    [point.high, point.low, point.close].filter(
      (value): value is number => Number.isFinite(value) && Number(value) > 0,
    ),
  );
  if (validPoints.length < 8 || allValues.length < 16) return allValues;

  const trailingPoints = validPoints.slice(-Math.min(20, validPoints.length));
  const trailingValues = trailingPoints.flatMap(point =>
    [point.high, point.low, point.close].filter(
      (value): value is number => Number.isFinite(value) && Number(value) > 0,
    ),
  );
  const trailingMaximum = Math.max(...trailingValues);
  const trailingMinimum = Math.min(...trailingValues);
  const globalMaximum = Math.max(...allValues);
  const globalMinimum = Math.min(...allValues);
  const recentHighRegime = globalMaximum > trailingMaximum * 6;
  const recentLowRegime = options.focusRecentRegime === true &&
    trailingMinimum > globalMinimum * 6;
  if (recentHighRegime || recentLowRegime) {
    // This is an axis-only regime fence. The complete history remains in the
    // replica and the renderer still draws every bar; old prices outside this
    // fence are allowed to leave the viewport instead of flattening the
    // current weekly price action.
    const regimeFloor = Math.max(0, trailingMinimum / 4);
    const regimeCeiling = trailingMaximum * 1.6;
    return allValues.filter(value => value >= regimeFloor && value <= regimeCeiling);
  }

  const sortedCloses = validPoints.map(point => point.close)
    .sort((left, right) => left - right);
  const lowerCenter = percentile(sortedCloses, 0.1);
  const upperCenter = percentile(sortedCloses, 0.9);
  const centerSpan = Math.max(upperCenter - lowerCenter, upperCenter * 0.05, 0.01);
  const lowerFence = Math.max(0, lowerCenter - Math.max(centerSpan * 3, upperCenter * 0.5));
  const upperFence = upperCenter + Math.max(centerSpan * 3, upperCenter * 1.5);
  const recent = new Set(validPoints.slice(-5));
  const bounded = validPoints.flatMap(point =>
    [point.high, point.low, point.close].filter(
      (value): value is number => Number.isFinite(value) && Number(value) > 0 &&
        (recent.has(point) || (Number(value) >= lowerFence && Number(value) <= upperFence)),
    ),
  );
  return bounded.length >= allValues.length * 0.6 ? bounded : allValues;
}

/**
 * Returns the bar range represented by the current horizontal chart viewport.
 * The axis can follow that range as the user scrolls, keeping older history
 * available without allowing it to create empty vertical space in the active
 * view.
 */
export function chartAxisWindow(
  totalBars: number,
  scrollLeft = 0,
  viewportWidth = 0,
  contentWidth = 0,
  fallbackBars = 80,
) {
  const total = Math.max(0, Math.floor(totalBars));
  if (total === 0) return { start: 0, end: 0 };

  const fallback = Math.min(
    total,
    Math.max(1, Math.floor(fallbackBars)),
  );
  if (
    !Number.isFinite(viewportWidth) ||
    !Number.isFinite(contentWidth) ||
    viewportWidth <= 0 ||
    contentWidth <= 0
  ) {
    return { start: total - fallback, end: total };
  }
  if (contentWidth <= viewportWidth) return { start: 0, end: total };

  const maximumScroll = Math.max(0, contentWidth - viewportWidth);
  const left = Math.max(
    0,
    Math.min(
      maximumScroll,
      Number.isFinite(scrollLeft) ? scrollLeft : 0,
    ),
  );
  const start = Math.max(
    0,
    Math.min(total - 1, Math.floor((left / contentWidth) * total)),
  );
  const end = Math.max(
    start + 1,
    Math.min(
      total,
      Math.ceil(((left + viewportWidth) / contentWidth) * total),
    ),
  );
  return { start, end };
}

export function indicatorWindow(
  values: number[],
  period: number,
  start: number,
  end: number,
) {
  return emaSeries(values, period).slice(start, end);
}

export function timestampAlignedIndicator(
  visible: TimedClose[],
  source: TimedClose[],
  indicator: Array<number | null>,
) {
  if (!visible.length || !source.length || source.length !== indicator.length)
    return visible.map(() => null);
  const valueByTimestamp = new Map(
    source
      .map((point, index) => [point.time, indicator[index]] as const)
      .filter(([time]) => Number.isFinite(time)),
  );
  return visible.map((point) => valueByTimestamp.get(point.time) ?? null);
}

export function chartAxisValue(
  min: number,
  max: number,
  index: number,
  steps = 4,
  logarithmic = false,
) {
  const ratio = Math.max(0, Math.min(1, index / Math.max(steps, 1)));
  if (!logarithmic) return max - (max - min) * ratio;
  const safeMin = Math.max(min, 0.0001);
  const safeMax = Math.max(max, safeMin + 0.0001);
  return Math.exp(Math.log(safeMax) - (Math.log(safeMax) - Math.log(safeMin)) * ratio);
}

export function nicePriceAxis(
  minimum: number,
  maximum: number,
  targetTickCount = 6,
  clampPositive = true,
) {
  const lower = Math.min(minimum, maximum);
  const upper = Math.max(minimum, maximum);
  if (!Number.isFinite(lower) || !Number.isFinite(upper))
    return { min: 0, max: 1, ticks: [1, 0] };
  const span = Math.max(
    upper - lower,
    Math.abs(upper) * 0.02,
    0.0001,
  );
  const rawStep =
    span / Math.max(2, Math.floor(targetTickCount) - 1);
  const magnitude = 10 ** Math.floor(Math.log10(rawStep));
  const fraction = rawStep / magnitude;
  const normalizedStep =
    fraction < 1.5
      ? 1
      : fraction < 2.25
        ? 2
        : fraction < 3.5
          ? 2.5
          : fraction < 7.5
            ? 5
            : 10;
  const step = normalizedStep * magnitude;
  let axisMin = Math.floor(lower / step) * step;
  const axisMax = Math.ceil(upper / step) * step;
  if (clampPositive && lower >= 0)
    axisMin = Math.max(0, axisMin);
  const tickTotal = Math.max(
    1,
    Math.round((axisMax - axisMin) / step),
  );
  const ticks = Array.from(
    { length: tickTotal + 1 },
    (_, index) => {
      const value = axisMax - index * step;
      return Math.abs(value) < step / 1_000_000 ? 0 : value;
    },
  );
  return {
    min: axisMin,
    max: axisMax > axisMin ? axisMax : axisMin + step,
    ticks,
  };
}

export function niceLogPriceTicks(
  minimum: number,
  maximum: number,
  targetTickCount = 5,
) {
  const lower = Math.min(minimum, maximum);
  const upper = Math.max(minimum, maximum);
  if (
    !Number.isFinite(lower) ||
    !Number.isFinite(upper) ||
    lower <= 0 ||
    upper <= lower
  )
    return [];
  const multipliers = [1, 1.25, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10];
  const startExponent = Math.floor(Math.log10(lower)) - 1;
  const endExponent = Math.ceil(Math.log10(upper)) + 1;
  const candidates = new Set<number>();
  for (
    let exponent = startExponent;
    exponent <= endExponent;
    exponent += 1
  ) {
    const magnitude = 10 ** exponent;
    for (const multiplier of multipliers) {
      const value = multiplier * magnitude;
      if (value >= lower && value <= upper)
        candidates.add(value);
    }
  }
  const ordered = [...candidates].sort((left, right) => right - left);
  if (ordered.length <= targetTickCount) return ordered;
  const selected = new Set<number>();
  const logLower = Math.log(lower);
  const logUpper = Math.log(upper);
  const tickCount = Math.max(3, Math.floor(targetTickCount));
  for (let index = 0; index < tickCount; index += 1) {
    const target =
      logUpper -
      (index / Math.max(1, tickCount - 1)) *
        (logUpper - logLower);
    let best = ordered[0];
    let bestDistance = Number.POSITIVE_INFINITY;
    for (const candidate of ordered) {
      const distance = Math.abs(Math.log(candidate) - target);
      if (distance < bestDistance) {
        best = candidate;
        bestDistance = distance;
      }
    }
    selected.add(best);
  }
  return [...selected].sort((left, right) => right - left);
}

/**
 * Extreme price ranges are easier to read as percentage moves. This is a
 * display decision only; the underlying bars and indicator calculations stay
 * unchanged.
 */
export function shouldUseLogPriceScale(
  values: number[],
  minimumRatio = 12,
) {
  const positive = values.filter(
    (value) => Number.isFinite(value) && value > 0,
  );
  if (positive.length < 2) return false;
  const minimum = Math.min(...positive);
  const maximum = Math.max(...positive);
  return maximum / minimum >= Math.max(2, minimumRatio);
}

export function priceAxisTickStep(ticks: number[]) {
  if (ticks.length < 2) return 0;
  for (let index = 1; index < ticks.length; index += 1) {
    const step = Math.abs(ticks[index] - ticks[index - 1]);
    if (Number.isFinite(step) && step > 0) return step;
  }
  return 0;
}

function priceAxisFractionDigits(step: number) {
  const absoluteStep = Math.abs(step);
  if (!Number.isFinite(absoluteStep) || absoluteStep <= 0) return 2;
  for (let digits = 0; digits <= 8; digits += 1) {
    const scaled = absoluteStep * 10 ** digits;
    if (Math.abs(scaled - Math.round(scaled)) < 1e-8) return digits;
  }
  return Math.max(
    0,
    Math.min(8, Math.ceil(-Math.log10(absoluteStep))),
  );
}

export function formatPriceAxisTick(
  value: number,
  step: number,
  currency = "USD",
  symbol = "",
) {
  if (!Number.isFinite(value)) return "—";
  const digits = symbol === "^TNX"
    ? Math.max(2, priceAxisFractionDigits(step))
    : priceAxisFractionDigits(step);
  if (symbol === "^TNX") return `${value.toFixed(digits)}%`;
  try {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency,
      minimumFractionDigits: digits,
      maximumFractionDigits: digits,
    }).format(value);
  } catch {
    return value.toLocaleString("en-US", {
      minimumFractionDigits: digits,
      maximumFractionDigits: digits,
    });
  }
}

export function chartPlotFraction(
  clientX: number,
  boundsLeft: number,
  boundsWidth: number,
  plotLeft = 20,
  plotRight = 675,
  viewBoxWidth = 800,
) {
  if (!(boundsWidth > 0) || !(plotRight > plotLeft) || !(viewBoxWidth > 0))
    return 0;
  const viewBoxX = ((clientX - boundsLeft) / boundsWidth) * viewBoxWidth;
  return Math.max(0, Math.min(1, (viewBoxX - plotLeft) / (plotRight - plotLeft)));
}

export type PriceLabelInput = {
  key: string;
  anchorY: number;
};

export function layoutPriceLabels(
  inputs: PriceLabelInput[],
  top = 20,
  bottom = 338,
  gap = 18,
) {
  if (!inputs.length) return new Map<string, number>();
  const ordered = [...inputs]
    .map(input => ({
      ...input,
      anchorY: Math.max(top, Math.min(bottom, input.anchorY)),
      labelY: Math.max(top, Math.min(bottom, input.anchorY)),
    }))
    .sort((left, right) => left.anchorY - right.anchorY);
  for (let index = 1; index < ordered.length; index++)
    ordered[index].labelY = Math.max(
      ordered[index].labelY,
      ordered[index - 1].labelY + gap,
    );
  if (ordered.at(-1)!.labelY > bottom) {
    ordered[ordered.length - 1].labelY = bottom;
    for (let index = ordered.length - 2; index >= 0; index--)
      ordered[index].labelY = Math.min(
        ordered[index].labelY,
        ordered[index + 1].labelY - gap,
      );
  }
  if (ordered[0].labelY < top) {
    ordered[0].labelY = top;
    for (let index = 1; index < ordered.length; index++)
      ordered[index].labelY = Math.max(
        ordered[index].labelY,
        ordered[index - 1].labelY + gap,
      );
  }
  return new Map(ordered.map(item => [item.key, item.labelY]));
}

export type TimedClose = { time: number; close: number };

export function timestampAlignedComparison(
  primary: TimedClose[],
  benchmark: TimedClose[],
) {
  if (primary.length < 2 || benchmark.length < 2) return [];
  const benchmarkByTime = new Map(
    benchmark
      .filter((point) => Number.isFinite(point.time) && Number.isFinite(point.close))
      .map((point) => [point.time, point.close]),
  );
  const shared = primary
    .map((point) => ({ primary: point, benchmark: benchmarkByTime.get(point.time) }))
    .filter((point): point is { primary: TimedClose; benchmark: number } =>
      Number.isFinite(point.benchmark),
    );
  if (shared.length < 2) return primary.map(() => null);
  const primaryBase = shared[0].primary.close;
  const benchmarkBase = shared[0].benchmark;
  if (!(primaryBase > 0) || !(benchmarkBase > 0)) return primary.map(() => null);
  return primary.map((point) => {
    const value = benchmarkByTime.get(point.time);
    return Number.isFinite(value)
      ? primaryBase * (Number(value) / benchmarkBase)
      : null;
  });
}
