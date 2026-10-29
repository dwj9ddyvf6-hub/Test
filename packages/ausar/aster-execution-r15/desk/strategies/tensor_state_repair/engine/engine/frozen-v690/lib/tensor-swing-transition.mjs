export const SWING_TRANSITION_VERSION = "swing-transition-1h/1.0.0";
export const SWING_TRANSITION_PRIMARY = Object.freeze(["AG", "CMG", "CRDO", "FLY", "LTBR", "UAMY", "VRT", "XPEV"]);
export const SWING_TRANSITION_SECONDARY = Object.freeze(["WYFI", "BLDP", "CLS", "CRML", "ERIE", "EXK", "OKLO", "REMX", "SMG", "URA", "WT", "AEHR", "NBIS", "ASAN", "FIVN", "GTLB", "LITE", "SOXL"]);
// Frozen engineering translation of the visual feature families, not fitted cutoffs.
export const SWING_TRANSITION_PARAMETERS = Object.freeze({ baseBars: 24, slopeBars: 5, floorToleranceAtr: 0.5, minimumTapSeparationBars: 3, maximumFloorAgeBars: 12, reclaimAgeBars: 3 });
const finite = value => typeof value === "number" && Number.isFinite(value);
const mean = values => values.reduce((sum, value) => sum + value, 0) / values.length;
export function swingTransitionBasketTier(symbol) {
  const ticker = String(symbol || "").trim().toUpperCase();
  return SWING_TRANSITION_PRIMARY.includes(ticker) ? "primary" : SWING_TRANSITION_SECONDARY.includes(ticker) ? "secondary" : "unlisted";
}

/** Bounded, as-of-only classifier; native Swing confirmation is supplied by its parent. */
export function buildSwingTransition({ bars = [], index = bars.length - 1, symbol = "", confirmed = false } = {}) {
  const p = SWING_TRANSITION_PARAMETERS;
  const bar = bars[index];
  const basketTier = swingTransitionBasketTier(symbol);
  const empty = { version: SWING_TRANSITION_VERSION, qualifies: false, eligible: false, basketTier, usesFutureData: false, confirmationBarTimestamp: null, factors: [], context: null };
  if (!bar || !Number.isInteger(index) || index < p.baseBars || bar.barFinality !== "closed" || !confirmed) return empty;
  const prior = bars.slice(index - p.baseBars, index);
  const atr = bar.vectorStructuralLocation?.atr;
  if (!finite(atr) || atr <= 0 || !finite(bar.close) || bar.close <= 0 || !finite(bar.low) ||
      prior.some(item => item.barFinality !== "closed" || !finite(item.low) || !finite(item.high) || !finite(item.close))) return empty;
  const slopes = prior.slice(-p.slopeBars * 2).map(item => item.ribbonSlope);
  if (!slopes.every(finite) || !finite(bar.ema8) || !finite(bar.ema21)) return empty;
  const earlierSlope = mean(slopes.slice(0, p.slopeBars));
  const recentSlope = mean(slopes.slice(p.slopeBars));
  const decelerating = earlierSlope < 0 && recentSlope > earlierSlope;
  const floor = Math.min(...prior.map(item => item.low));
  const tolerance = atr * p.floorToleranceAtr;
  const taps = [];
  for (let i = 1; i < prior.length - 1; i += 1) {
    if (prior[i].low <= floor + tolerance && prior[i].low <= prior[i - 1].low && prior[i].low <= prior[i + 1].low &&
        (!taps.length || i - taps.at(-1) >= p.minimumTapSeparationBars)) taps.push(i);
  }
  const floorAgeBars = taps.length ? prior.length - taps.at(-1) : null;
  const floorIntact = taps.length >= 2 && floorAgeBars <= p.maximumFloorAgeBars && bar.low >= floor - tolerance;
  let reclaimAgeBars = null;
  for (let age = 0; age <= p.reclaimAgeBars; age += 1) {
    const current = bars[index - age], previous = bars[index - age - 1];
    if (current?.barFinality === "closed" && previous?.barFinality === "closed" && finite(current.ema21) && finite(previous.ema21) &&
        previous.close <= previous.ema21 && current.close > current.ema21) { reclaimAgeBars = age; break; }
  }
  const reclaim = reclaimAgeBars !== null && bar.close > bar.ema21 && bar.close >= bar.ema8;
  const yellow = bar.candleRegime === "bearish";
  const broadRepair = bar.ribbonOrder === "bearish" || bar.ribbonOrder === "mixed";
  const ribbon = Array.isArray(bar.emaRibbon) ? bar.emaRibbon.filter(finite) : [];
  const supply = bar.vectorStructuralLocation?.nearestSupply?.low;
  const overhead = [...ribbon.filter(value => value > bar.close), ...(finite(supply) && supply > bar.close ? [supply] : [])];
  const nearestOverhead = overhead.length ? Math.min(...overhead) : null;
  const factors = [yellow && "yellow regime", decelerating && "decline decelerating", floorIntact && "repeated floor intact", reclaim && "fast ribbon reclaim", broadRepair && "broad ribbon repairing"].filter(Boolean);
  const qualifies = yellow && decelerating && floorIntact && reclaim && broadRepair;
  return { ...empty, qualifies, eligible: qualifies && basketTier === "primary", confirmationBarTimestamp: bar.timestamp, factors,
    context: { floor, floorTapCount: taps.length, floorAgeBars, floorDistanceAtr: (bar.close - floor) / atr, atr,
      earlierRibbonSlope: earlierSlope, recentRibbonSlope: recentSlope, reclaimAgeBars, nearestOverhead,
      runwayPct: nearestOverhead === null ? null : (nearestOverhead / bar.close - 1) * 100,
      runwayAtr: nearestOverhead === null ? null : (nearestOverhead - bar.close) / atr,
      rvol: finite(bar.rvol) ? bar.rvol : null, squeezeOn: typeof bar.squeezeOn === "boolean" ? bar.squeezeOn : null,
      primaryMarkers: Array.isArray(bar.primaryMarkers) ? [...bar.primaryMarkers] : [],
      fastState: bar.fastState || null, slowState: bar.slowState || null, broadRibbonOrder: bar.ribbonOrder || null } };
}

/** Validate the bounded subtype identity at payload and notification boundaries. */
export function isPrimarySwingTransition(value, symbol, timestamp) {
  return Boolean(value && value.version === SWING_TRANSITION_VERSION && value.usesFutureData === false &&
    value.qualifies === true && value.eligible === true && value.basketTier === "primary" &&
    swingTransitionBasketTier(symbol) === "primary" && finite(timestamp) && value.confirmationBarTimestamp === timestamp);
}
