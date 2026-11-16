/**
 * Tensor context sidecar.
 *
 * This module deliberately does not create, suppress, or rename a Tensor
 * primary signal. It calculates two completed-bar context lanes:
 *
 * 1. Trading Candles-style cycle state: DiNapoli fractional-EMA MACD plus
 *    8/3/3 stochastic agreement.
 * 2. A small, focused reversal-pattern vocabulary with point-in-time
 *    historical forward-return context.
 *
 * The pattern statistics are causal: when a bar is evaluated, only pattern
 * outcomes that were already complete before that bar are eligible. The
 * current event's future return is never used to describe the current event.
 */

export const TENSOR_CONTEXT_VERSION = "tensor-context/1.0.0";
export const TENSOR_PATTERN_HORIZON_BARS = 10;
export const TENSOR_PATTERN_MIN_SAMPLES = 20;

const FAST_ALPHA = 0.213;
const SLOW_ALPHA = 0.108;
const SIGNAL_ALPHA = 0.199;
const STOCH_LENGTH = 8;
const STOCH_K_SMOOTH = 3;
const STOCH_D_SMOOTH = 3;

const CYCLE_STATES = Object.freeze([
  "BULL_SHIFT",
  "BULL_STRONG",
  "BULL_WEAK",
  "BEAR_SHIFT",
  "BEAR_STRONG",
  "BEAR_WEAK",
  "WARMING",
]);

const PATTERN_DEFINITIONS = Object.freeze([
  { id: "bullish-engulfing", label: "Bullish Engulfing", shortLabel: "ENG↑", glyph: "E↑", direction: "bullish" },
  { id: "bearish-engulfing", label: "Bearish Engulfing", shortLabel: "ENG↓", glyph: "E↓", direction: "bearish" },
  { id: "morning-star", label: "Morning Star", shortLabel: "MS↑", glyph: "MS↑", direction: "bullish" },
  { id: "evening-star", label: "Evening Star", shortLabel: "ES↓", glyph: "ES↓", direction: "bearish" },
  { id: "three-outside-up", label: "Three Outside Up", shortLabel: "3OU↑", glyph: "3OU↑", direction: "bullish" },
  { id: "three-outside-down", label: "Three Outside Down", shortLabel: "3OD↓", glyph: "3OD↓", direction: "bearish" },
]);

const finite = value => typeof value === "number" && Number.isFinite(value);

function safeBar(bar) {
  return Boolean(
    bar &&
      finite(bar.timestamp) &&
      finite(bar.open) &&
      finite(bar.high) &&
      finite(bar.low) &&
      finite(bar.close) &&
      bar.close > 0 &&
      bar.high >= Math.max(bar.open, bar.close) &&
      bar.low <= Math.min(bar.open, bar.close),
  );
}

function emaAlpha(values, alpha) {
  const output = Array(values.length).fill(null);
  let previous = null;
  values.forEach((value, index) => {
    if (!finite(value)) return;
    previous = previous === null
      ? value
      : alpha * value + (1 - alpha) * previous;
    output[index] = previous;
  });
  return output;
}

function sma(values, index, length) {
  if (index < length - 1) return null;
  const window = values.slice(index - length + 1, index + 1);
  if (window.length !== length || window.some(value => !finite(value))) return null;
  return window.reduce((sum, value) => sum + value, 0) / length;
}

function highest(values, index, length) {
  if (index < length - 1) return null;
  const window = values.slice(index - length + 1, index + 1);
  return window.length === length && window.every(finite)
    ? Math.max(...window)
    : null;
}

function lowest(values, index, length) {
  if (index < length - 1) return null;
  const window = values.slice(index - length + 1, index + 1);
  return window.length === length && window.every(finite)
    ? Math.min(...window)
    : null;
}

function stochasticSeries(bars) {
  const highs = bars.map(bar => bar.high);
  const lows = bars.map(bar => bar.low);
  const raw = bars.map((bar, index) => {
    const high = highest(highs, index, STOCH_LENGTH);
    const low = lowest(lows, index, STOCH_LENGTH);
    if (!finite(high) || !finite(low) || high === low) return null;
    return 100 * (bar.close - low) / (high - low);
  });
  const slowK = raw.map((_, index) => sma(raw, index, STOCH_K_SMOOTH));
  const slowD = slowK.map((_, index) => sma(slowK, index, STOCH_D_SMOOTH));
  return { raw, slowK, slowD };
}

function tradingCandleCycleSeries(bars) {
  const closes = bars.map(bar => bar.close);
  const fast = emaAlpha(closes, FAST_ALPHA);
  const slow = emaAlpha(closes, SLOW_ALPHA);
  const macd = fast.map((value, index) =>
    finite(value) && finite(slow[index]) ? value - slow[index] : null,
  );
  const signal = emaAlpha(macd, SIGNAL_ALPHA);
  const stochastic = stochasticSeries(bars);
  let lastShiftIndex = null;

  return bars.map((_, index) => {
    const currentMacd = macd[index];
    const currentSignal = signal[index];
    const currentK = stochastic.slowK[index];
    const currentD = stochastic.slowD[index];
    const priorMacd = index > 0 ? macd[index - 1] : null;
    const priorSignal = index > 0 ? signal[index - 1] : null;
    const ready = [currentMacd, currentSignal, currentK, currentD].every(finite);
    if (!ready) {
      return {
        state: "WARMING",
        direction: "neutral",
        momentum: "warming",
        momentumAgreement: null,
        ageBars: null,
        glyph: null,
        macd: finite(currentMacd) ? currentMacd : null,
        signal: finite(currentSignal) ? currentSignal : null,
        slowK: finite(currentK) ? currentK : null,
        slowD: finite(currentD) ? currentD : null,
      };
    }

    const bullish = currentMacd > currentSignal;
    const momentumUp = currentK > currentD;
    const bullShift =
      index > 0 &&
      finite(priorMacd) &&
      finite(priorSignal) &&
      priorMacd <= priorSignal &&
      currentMacd > currentSignal;
    const bearShift =
      index > 0 &&
      finite(priorMacd) &&
      finite(priorSignal) &&
      priorMacd >= priorSignal &&
      currentMacd < currentSignal;

    if (bullShift || bearShift) lastShiftIndex = index;
    const state = bullShift
      ? "BULL_SHIFT"
      : bearShift
        ? "BEAR_SHIFT"
        : bullish && momentumUp
          ? "BULL_STRONG"
          : bullish
            ? "BULL_WEAK"
            : momentumUp
              ? "BEAR_WEAK"
              : "BEAR_STRONG";
    const momentumAgreement = bullish ? momentumUp : !momentumUp;
    return {
      state,
      direction: bullish ? "bullish" : "bearish",
      momentum: momentumAgreement ? "aligned" : "diverging",
      momentumAgreement,
      ageBars: lastShiftIndex === null ? null : index - lastShiftIndex,
      glyph: bullShift ? "↗" : bearShift ? "↘" : null,
      macd: currentMacd,
      signal: currentSignal,
      slowK: currentK,
      slowD: currentD,
    };
  });
}

function parts(bars, index) {
  const bar = bars[index];
  if (!safeBar(bar)) return null;
  const body = Math.abs(bar.close - bar.open);
  const range = Math.max(0, bar.high - bar.low);
  return {
    open: bar.open,
    high: bar.high,
    low: bar.low,
    close: bar.close,
    body,
    range,
    upperWick: bar.high - Math.max(bar.open, bar.close),
    lowerWick: Math.min(bar.open, bar.close) - bar.low,
    bullish: bar.close > bar.open,
    bearish: bar.close < bar.open,
  };
}

function averageBody(bars, index, length = 14) {
  const start = Math.max(0, index - length);
  const values = bars
    .slice(start, index)
    .map((_, offset) => parts(bars, start + offset)?.body)
    .filter(finite);
  return values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : null;
}

function priorTrend(bars, index, direction) {
  const lookback = 5;
  if (index < lookback + 1) return true;
  const current = bars[index - 1]?.close;
  const prior = bars[index - 1 - lookback]?.close;
  if (!finite(current) || !finite(prior)) return true;
  return direction === "bullish" ? current <= prior : current >= prior;
}

function engulfing(bars, index, direction) {
  const previous = parts(bars, index - 1);
  const current = parts(bars, index);
  if (!previous || !current || previous.body <= 0 || current.body <= 0) return false;
  if (direction === "bullish") {
    return previous.bearish && current.bullish &&
      current.open <= previous.close && current.close >= previous.open &&
      current.body >= previous.body * 0.9 && priorTrend(bars, index, direction);
  }
  return previous.bullish && current.bearish &&
    current.open >= previous.close && current.close <= previous.open &&
    current.body >= previous.body * 0.9 && priorTrend(bars, index, direction);
}

function star(bars, index, direction) {
  const first = parts(bars, index - 2);
  const middle = parts(bars, index - 1);
  const current = parts(bars, index);
  const typicalBody = averageBody(bars, index - 2);
  if (!first || !middle || !current || !finite(typicalBody) || first.body <= 0) return false;
  const smallMiddle = middle.body <= Math.max(typicalBody * 0.65, first.body * 0.55);
  if (!smallMiddle) return false;
  if (direction === "bullish") {
    return first.bearish && current.bullish && priorTrend(bars, index - 1, direction) &&
      current.close >= first.open - first.body * 0.05;
  }
  return first.bullish && current.bearish && priorTrend(bars, index - 1, direction) &&
    current.close <= first.open + first.body * 0.05;
}

function threeOutside(bars, index, direction) {
  const first = parts(bars, index - 2);
  const second = parts(bars, index - 1);
  const current = parts(bars, index);
  if (!first || !second || !current) return false;
  if (direction === "bullish") {
    return engulfing(bars, index - 1, "bullish") && current.bullish &&
      current.close > second.close && first.bearish && priorTrend(bars, index - 1, direction);
  }
  return engulfing(bars, index - 1, "bearish") && current.bearish &&
    current.close < second.close && first.bullish && priorTrend(bars, index - 1, direction);
}

function detectPatternEvents(bars, index) {
  const matches = [];
  if (engulfing(bars, index, "bullish")) matches.push(PATTERN_DEFINITIONS[0]);
  if (engulfing(bars, index, "bearish")) matches.push(PATTERN_DEFINITIONS[1]);
  if (star(bars, index, "bullish")) matches.push(PATTERN_DEFINITIONS[2]);
  if (star(bars, index, "bearish")) matches.push(PATTERN_DEFINITIONS[3]);
  if (threeOutside(bars, index, "bullish")) matches.push(PATTERN_DEFINITIONS[4]);
  if (threeOutside(bars, index, "bearish")) matches.push(PATTERN_DEFINITIONS[5]);
  return matches;
}

function mean(values) {
  return values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : null;
}

function patternStatsAt({ bars, eventsByIndex, patternId, index, horizon, minSamples }) {
  // The outcome must be fully known before the current bar opens. The
  // pattern itself may have occurred at any earlier start index, provided
  // its horizon has completed by index - 1.
  const maxOutcomeIndex = index - 1;
  const eligible = [];
  for (let outcomeIndex = horizon; outcomeIndex <= maxOutcomeIndex; outcomeIndex += 1) {
    const start = outcomeIndex - horizon;
    const startClose = bars[start]?.close;
    const endClose = bars[outcomeIndex]?.close;
    if (!finite(startClose) || !finite(endClose) || startClose <= 0) continue;
    eligible.push({
      index: start,
      returnPct: ((endClose - startClose) / startClose) * 100,
      isPattern: eventsByIndex[start]?.some(event => event.id === patternId) === true,
    });
  }
  const patternReturns = eligible.filter(item => item.isPattern).map(item => item.returnPct);
  const baselineReturns = eligible.map(item => item.returnPct);
  const forwardReturnPct = mean(patternReturns);
  const baselineReturnPct = mean(baselineReturns);
  const edgePct = finite(forwardReturnPct) && finite(baselineReturnPct)
    ? forwardReturnPct - baselineReturnPct
    : null;
  const upRatePct = patternReturns.length
    ? (patternReturns.filter(value => value > 0).length / patternReturns.length) * 100
    : null;
  return {
    horizonBars: horizon,
    sampleCount: patternReturns.length,
    forwardReturnPct,
    baselineReturnPct,
    edgePct,
    upRatePct,
    status: patternReturns.length >= minSamples ? "usable" : patternReturns.length ? "warming" : "unavailable",
  };
}

function copyDefinition(definition, stats) {
  return {
    id: definition.id,
    label: definition.label,
    shortLabel: definition.shortLabel,
    glyph: definition.glyph,
    direction: definition.direction,
    stats,
  };
}

/**
 * Build causal context for every raw bar. This is intentionally independent
 * of Tensor's primary marker calculation.
 */
export function buildTensorContextSeries(
  bars,
  {
    horizon = TENSOR_PATTERN_HORIZON_BARS,
    minSamples = TENSOR_PATTERN_MIN_SAMPLES,
    latestOnly = false,
  } = {},
) {
  if (!Array.isArray(bars) || bars.some(bar => !safeBar(bar))) return [];
  const cycleSeries = tradingCandleCycleSeries(bars);
  const eventsByIndex = bars.map((_, index) => detectPatternEvents(bars, index));
  const buildAt = index => {
    const cycle = cycleSeries[index];
    const patterns = eventsByIndex[index].map(definition =>
      copyDefinition(
        definition,
        patternStatsAt({ bars, eventsByIndex, patternId: definition.id, index, horizon, minSamples }),
      ),
    );
    return {
      version: TENSOR_CONTEXT_VERSION,
      status: cycle.state === "WARMING" ? "warming" : "ready",
      usesFutureData: false,
      cycle,
      patterns,
      primaryPattern: patterns[0] ?? null,
    };
  };
  if (latestOnly) {
    const latest = [];
    if (bars.length) latest[bars.length - 1] = buildAt(bars.length - 1);
    return latest;
  }
  return bars.map((_, index) => buildAt(index));
}

export function currentTensorContext(bars, options) {
  const series = buildTensorContextSeries(bars, options);
  return series.at(-1) ?? null;
}

export { CYCLE_STATES, PATTERN_DEFINITIONS };
