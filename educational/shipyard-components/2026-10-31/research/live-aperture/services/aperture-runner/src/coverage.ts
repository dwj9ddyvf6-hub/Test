import type { ApertureFreshness, ApertureSession } from "../../../lib/live-contracts.ts";
import type { MarketBar } from "../../../lib/live-scan-engine.ts";

export const APERTURE_MIN_DAILY_BARS = 80;
export const APERTURE_MIN_PRICE = 1;
export const APERTURE_MIN_MEDIAN_DOLLAR_VOLUME = 5_000_000;

function median(values: number[]) {
  const sorted = values.filter(Number.isFinite).sort((left, right) => left - right);
  if (!sorted.length) return 0;
  const middle = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[middle] : (sorted[middle - 1] + sorted[middle]) / 2;
}

function validDailyBar(bar: MarketBar) {
  return Number.isFinite(new Date(bar.t).getTime())
    && [bar.o, bar.h, bar.l, bar.c].every((value) => Number.isFinite(value) && value > 0)
    && Number.isFinite(bar.v)
    && bar.v >= 0
    && bar.l <= Math.min(bar.o, bar.c)
    && bar.h >= Math.max(bar.o, bar.c)
    && bar.h >= bar.l;
}

/**
 * Provider coverage is measured only against names the live engine could
 * legally classify. These gates intentionally mirror the engine's adequate
 * history, $1 price floor, and $5M 20-session median dollar-volume veto.
 */
export function isScannerEligible(daily: MarketBar[]) {
  if (daily.length < APERTURE_MIN_DAILY_BARS || !daily.every(validDailyBar)) return false;
  const latest = daily.at(-1);
  if (!latest || latest.c < APERTURE_MIN_PRICE) return false;
  const medianDollarVolume = median(daily.slice(-20).map((bar) => bar.c * bar.v));
  return medianDollarVolume >= APERTURE_MIN_MEDIAN_DOLLAR_VOLUME;
}

export function buildEligibilityCoverage(input: {
  equitySymbols: readonly string[];
  totalUniverseCount: number;
  dailyBySymbol: ReadonlyMap<string, MarketBar[]>;
  currentSymbols: ReadonlySet<string>;
}) {
  const eligibleSymbols = new Set(
    input.equitySymbols.filter((symbol) => isScannerEligible(input.dailyBySymbol.get(symbol) ?? [])),
  );
  let coveredCount = 0;
  for (const symbol of eligibleSymbols) if (input.currentSymbols.has(symbol)) coveredCount += 1;
  const eligibleCount = eligibleSymbols.size;
  return {
    eligibleSymbols,
    eligibleCount,
    coveredCount,
    unsupportedCount: Math.max(0, input.totalUniverseCount - eligibleCount),
  };
}

export function classifyRunnerFreshness(input: {
  session: ApertureSession;
  eligibleCount: number;
  coveredCount: number;
  deepRequiredCount: number;
  deepCoveredCount: number;
  benchmarkCurrent: boolean;
  benchmarkSealed: boolean;
}): ApertureFreshness {
  if (input.session === "CLOSED") return "CLOSED";
  if (!input.benchmarkCurrent
    || !input.benchmarkSealed
    || input.eligibleCount < 1
    || input.deepRequiredCount < 1) return "WARMING";

  const currentCoverage = input.coveredCount / input.eligibleCount;
  const deepCoverage = input.deepCoveredCount / input.deepRequiredCount;
  if (currentCoverage >= 0.75 && deepCoverage >= 0.75) return "LIVE";
  if (currentCoverage >= 0.4 && deepCoverage >= 0.4) return "LAGGING";
  return "WARMING";
}
