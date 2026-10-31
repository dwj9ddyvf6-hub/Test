import { createHash } from "node:crypto";
import { APERTURE_UNIVERSE_COUNT, APERTURE_UNIVERSE_HASH, APERTURE_UNIVERSE_ID } from "./aperture-universe.ts";
import { classifyDiscovery, type DiscoveryPolicyInput } from "./discovery-policy.ts";
import { LIVE_TRIGGER_REGISTRY } from "./live-defaults.ts";
import type {
  ApertureFreshness,
  ApertureSession,
  LiveDecisionAction,
  LiveDiscoveryDecision,
  LiveDiscoveryView,
} from "./live-contracts.ts";

export type MarketBar = {
  t: string;
  o: number;
  h: number;
  l: number;
  c: number;
  v: number;
};

export type LiveSymbolInput = {
  symbol: string;
  company?: string;
  sector?: string;
  daily: MarketBar[];
  intraday: MarketBar[];
  currentDailyVolume?: number;
  providerEligible?: boolean;
  qualityFlags?: string[];
};

export type LiveScanInput = {
  provider: string;
  feed: string;
  generatedAt: string;
  barEndAt: string;
  session: ApertureSession;
  sessionLabel: string;
  marketNextTransitionAt?: string | null;
  decisionWindowOpen?: boolean;
  freshness: ApertureFreshness;
  elapsedMs: number;
  symbols: LiveSymbolInput[];
  eligibleCount: number;
  coveredCount: number;
  unsupportedCount: number;
};

function finite(values: number[]) {
  return values.filter(Number.isFinite);
}

function mean(values: number[]) {
  const clean = finite(values);
  return clean.length ? clean.reduce((sum, value) => sum + value, 0) / clean.length : 0;
}

function median(values: number[]) {
  const clean = finite(values).sort((left, right) => left - right);
  if (!clean.length) return 0;
  const middle = Math.floor(clean.length / 2);
  return clean.length % 2 ? clean[middle] : (clean[middle - 1] + clean[middle]) / 2;
}

function ema(values: number[], period: number): number[] {
  if (!values.length) return [];
  const alpha = 2 / (period + 1);
  const output = [values[0]];
  for (let index = 1; index < values.length; index += 1) {
    output.push(values[index] * alpha + output[index - 1] * (1 - alpha));
  }
  return output;
}

function rsi(values: number[], period = 14): number[] {
  if (values.length < 2) return values.map(() => 50);
  const output = Array(values.length).fill(50) as number[];
  let averageGain = 0;
  let averageLoss = 0;
  for (let index = 1; index <= Math.min(period, values.length - 1); index += 1) {
    const change = values[index] - values[index - 1];
    averageGain += Math.max(change, 0);
    averageLoss += Math.max(-change, 0);
  }
  averageGain /= period;
  averageLoss /= period;
  for (let index = period; index < values.length; index += 1) {
    if (index > period) {
      const change = values[index] - values[index - 1];
      averageGain = (averageGain * (period - 1) + Math.max(change, 0)) / period;
      averageLoss = (averageLoss * (period - 1) + Math.max(-change, 0)) / period;
    }
    output[index] = averageLoss === 0 ? 100 : 100 - 100 / (1 + averageGain / averageLoss);
  }
  return output;
}

function atr(bars: MarketBar[], period = 14): number[] {
  const ranges = bars.map((bar, index) => {
    if (!index) return bar.h - bar.l;
    const previous = bars[index - 1].c;
    return Math.max(bar.h - bar.l, Math.abs(bar.h - previous), Math.abs(bar.l - previous));
  });
  return ema(ranges, period);
}

function macd(values: number[]) {
  const fast = ema(values, 12);
  const slow = ema(values, 26);
  const line = values.map((_, index) => (fast[index] ?? 0) - (slow[index] ?? 0));
  const signal = ema(line, 9);
  return line.map((value, index) => value - (signal[index] ?? 0));
}

function percentChange(from: number, to: number) {
  return from ? ((to - from) / from) * 100 : 0;
}

export function deriveStructureTarget(current: number, risk: number, atrValue: number, priorResistance: number) {
  const target = Math.min(priorResistance, current + atrValue * 3.2);
  return {
    target,
    rewardRisk: risk > 0 ? Math.max(0, (target - current) / risk) : 0,
    targetAlreadyTraded: current >= target,
  };
}

function money(value: number) {
  if (!Number.isFinite(value)) return "—";
  return `$${value >= 100 ? value.toFixed(2) : value >= 1 ? value.toFixed(2) : value.toFixed(4)}`;
}

function signed(value: number, suffix = "") {
  return `${value >= 0 ? "+" : ""}${value.toFixed(2)}${suffix}`;
}

function last<T>(values: T[], offset = 0): T | undefined {
  return values[values.length - 1 - offset];
}

function closingLocation(bar: MarketBar) {
  const range = Math.max(bar.h - bar.l, Number.EPSILON);
  return (bar.c - bar.l) / range;
}

const ET_DATE = new Intl.DateTimeFormat("en-CA", {
  timeZone: "America/New_York",
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
});

const ET_SLOT = new Intl.DateTimeFormat("en-US", {
  timeZone: "America/New_York",
  hour: "2-digit",
  minute: "2-digit",
  hourCycle: "h23",
});

function etDate(value: string) {
  return ET_DATE.format(new Date(value));
}

function etSlot(value: string) {
  return ET_SLOT.format(new Date(value));
}

function validMarketBar(bar: MarketBar) {
  const timestamp = new Date(bar.t).getTime();
  return Number.isFinite(timestamp)
    && [bar.o, bar.h, bar.l, bar.c].every((value) => Number.isFinite(value) && value > 0)
    && Number.isFinite(bar.v)
    && bar.v >= 0
    && bar.l <= Math.min(bar.o, bar.c)
    && bar.h >= Math.max(bar.o, bar.c)
    && bar.h >= bar.l;
}

function validSeries(bars: MarketBar[]) {
  const timestamps = bars.map((bar) => new Date(bar.t).getTime());
  return bars.every(validMarketBar)
    && new Set(timestamps).size === timestamps.length
    && timestamps.every((timestamp, index) => index === 0 || timestamp > timestamps[index - 1]);
}

function sessionVwap(bars: MarketBar[]) {
  const sessionDate = last(bars) ? etDate(last(bars)!.t) : null;
  const current = bars.filter((bar) => sessionDate && etDate(bar.t) === sessionDate);
  const volume = current.reduce((sum, bar) => sum + bar.v, 0);
  return volume
    ? current.reduce((sum, bar) => sum + ((bar.h + bar.l + bar.c) / 3) * bar.v, 0) / volume
    : last(bars)?.c ?? 0;
}

function historicalProof(daily: MarketBar[]) {
  const closes = daily.map((bar) => bar.c);
  const rsiSeries = rsi(closes);
  const histogram = macd(closes);
  const ema20 = ema(closes, 20);
  const atr14 = atr(daily);
  const outcomes: number[] = [];
  let lastAcceptedIndex = -100;
  for (let index = 35; index < daily.length - 10; index += 1) {
    const curl = rsiSeries[index] > rsiSeries[index - 1]
      && histogram[index] > histogram[index - 1]
      && histogram[index - 1] >= histogram[index - 2];
    const nearSupport = Math.abs(closes[index] - ema20[index]) <= Math.max(atr14[index], closes[index] * 0.01);
    if (curl && nearSupport && rsiSeries[index] <= 58 && index - lastAcceptedIndex >= 10) {
      // Non-overlapping ten-session episodes; 35 bps is a conservative
      // round-trip friction allowance, not a fill simulation.
      outcomes.push(percentChange(closes[index], closes[index + 10]) - 0.35);
      lastAcceptedIndex = index;
    }
  }
  const split = Math.max(1, Math.floor(outcomes.length * 0.67));
  const train = outcomes.slice(0, split);
  const holdout = outcomes.slice(split);
  const hitRate = outcomes.length ? outcomes.filter((value) => value > 0).length / outcomes.length : 0;
  const medianReturn = median(outcomes);
  const trainHitRate = train.length ? train.filter((value) => value > 0).length / train.length : 0;
  const holdoutHitRate = holdout.length ? holdout.filter((value) => value > 0).length / holdout.length : 0;
  const holdoutMedian = median(holdout);
  if (outcomes.length >= 10 && train.length >= 6 && holdout.length >= 4
    && trainHitRate >= 0.55 && median(train) >= 0.75
    && holdoutHitRate >= 0.6 && holdoutMedian >= 1) {
    return { state: "SUPPORTED" as const, count: outcomes.length, hitRate, medianReturn, holdoutCount: holdout.length, holdoutHitRate, holdoutMedian };
  }
  if (outcomes.length >= 6) return { state: "MIXED" as const, count: outcomes.length, hitRate, medianReturn, holdoutCount: holdout.length, holdoutHitRate, holdoutMedian };
  return { state: "OBSERVING" as const, count: outcomes.length, hitRate, medianReturn, holdoutCount: holdout.length, holdoutHitRate, holdoutMedian };
}

function classifyOne(input: LiveSymbolInput, benchmark: LiveSymbolInput | undefined, scan: LiveScanInput): LiveDiscoveryDecision | null {
  const daily = [...input.daily].sort((left, right) => left.t.localeCompare(right.t));
  const intraday = [...input.intraday].sort((left, right) => left.t.localeCompare(right.t));
  const expectedBarStart = new Date(new Date(scan.barEndAt).getTime() - 5 * 60_000).toISOString();
  const lastIntradayAt = last(intraday) ? new Date(last(intraday)!.t).toISOString() : null;
  if (input.providerEligible === false
    || input.qualityFlags?.length
    || daily.length < 80
    || intraday.length < 3
    || !validSeries(daily)
    || !validSeries(intraday)
    || lastIntradayAt !== expectedBarStart) return null;

  const closes = daily.map((bar) => bar.c);
  const latest = last(intraday) ?? last(daily);
  if (!latest || !Number.isFinite(latest.c) || latest.c <= 0) return null;
  const currentSessionDate = etDate(scan.barEndAt);
  const lastDailyIsCurrent = etDate(last(daily)!.t) === currentSessionDate;
  const previousDay = lastDailyIsCurrent ? last(daily, 1) : last(daily);
  if (!previousDay) return null;

  const indicatorCloses = lastDailyIsCurrent ? [...closes.slice(0, -1), latest.c] : [...closes, latest.c];
  const completedCloses = lastDailyIsCurrent ? closes.slice(0, -1) : closes;
  const ema20Series = ema(indicatorCloses, 20);
  const ema50Series = ema(indicatorCloses, 50);
  const completedEma20 = last(ema(completedCloses, 20)) ?? latest.c;
  const completedEma50 = last(ema(completedCloses, 50)) ?? completedEma20;
  const rsiSeries = rsi(indicatorCloses);
  const macdHistogram = macd(indicatorCloses);
  const atrSeries = atr(daily);
  const ema20Value = last(ema20Series) ?? latest.c;
  const ema50Value = last(ema50Series) ?? ema20Value;
  const rsiNow = last(rsiSeries) ?? 50;
  const rsiCurl = rsiNow > (last(rsiSeries, 1) ?? rsiNow) && (last(rsiSeries, 1) ?? rsiNow) >= (last(rsiSeries, 2) ?? rsiNow);
  const macdNow = last(macdHistogram) ?? 0;
  const macdCurl = macdNow > (last(macdHistogram, 1) ?? macdNow) && (last(macdHistogram, 1) ?? macdNow) >= (last(macdHistogram, 2) ?? macdNow);
  const atrValue = Math.max(last(atrSeries) ?? latest.c * 0.03, latest.c * 0.005);
  const vwap = sessionVwap(intraday);
  const recentLow = Math.min(...daily.slice(-60).map((bar) => bar.l));
  const priorResistanceBars = (lastDailyIsCurrent ? daily.slice(0, -1) : daily).slice(-20);
  const recentHigh = Math.max(...priorResistanceBars.map((bar) => bar.h));
  const priorPivot = (previousDay.h + previousDay.l + previousDay.c) / 3;
  // Entry geometry is frozen to completed-session structure so a rising
  // intraday VWAP cannot ratchet the chase line upward after ignition.
  const candidateSupports = [completedEma20, completedEma50, previousDay.l, priorPivot]
    .filter((value) => Number.isFinite(value) && value > 0 && value <= latest.c)
    .sort((left, right) => right - left);
  const support = candidateSupports[0] ?? Number.NaN;
  const distanceAtr = (latest.c - support) / atrValue;
  const extensionAtr = (latest.c - ema20Value) / atrValue;
  const run10 = percentChange(daily.at(-11)?.c ?? closes[0], latest.c);
  const distanceFromLow = percentChange(recentLow, latest.c);
  const entryLow = support - atrValue * 0.12;
  const entryHigh = support + atrValue * 0.45;
  const invalidation = support - atrValue * 0.7;
  const chaseLine = support + atrValue * 1.2;
  const risk = Math.max(latest.c - invalidation, atrValue * 0.25);
  // The target is bounded by actual prior overhead structure. It is never
  // manufactured from a desired reward/risk multiple.
  const targetGeometry = deriveStructureTarget(latest.c, risk, atrValue, recentHigh);
  const { target, rewardRisk } = targetGeometry;
  const belowChaseLine = latest.c < chaseLine;
  const insideEntryZone = latest.c >= entryLow && latest.c <= entryHigh;

  const lastBar = last(intraday) ?? latest;
  const previousBar = last(intraday, 1) ?? lastBar;
  const sweepReclaim = lastBar.l < support && lastBar.c > support && closingLocation(lastBar) >= 0.6;
  const structuralHold = Math.min(previousBar.l, lastBar.l) <= support + atrValue * 0.25
    && previousBar.c >= support
    && lastBar.c >= support
    && lastBar.c > previousBar.c;
  const confirmedRotation = rsiCurl && macdCurl && lastBar.c > previousBar.h;
  const triggerState: DiscoveryPolicyInput["triggerState"] = sweepReclaim || structuralHold || confirmedRotation
    ? "CONFIRMED"
    : rsiCurl && macdCurl
      ? "SEED"
      : distanceAtr <= 0.8
        ? "APPROACH"
        : "NONE";
  const triggerFamily = sweepReclaim ? "sweep-reclaim" : structuralHold ? "structural-hold" : "rotation-ignition";
  const triggerLabel = sweepReclaim ? "Liquidity sweep / reclaim" : structuralHold ? "Structural hold" : "RSI / MACD rotation ignition";

  const anchor: DiscoveryPolicyInput["anchor"] = distanceAtr <= 0.5 && extensionAtr <= 1
    ? "PASS"
    : distanceAtr <= 1 && extensionAtr <= 1.5
      ? "WATCH"
      : distanceFromLow > 25 || extensionAtr > 2
        ? "HARD AVOID"
        : "WATCH";
  const formation: DiscoveryPolicyInput["formation"] = rsiCurl && macdCurl
    ? latest.c <= ema20Value ? "REVERSAL SEED" : latest.c <= ema50Value * 1.04 ? "ROTATION SEED" : "BUILDING"
    : run10 > 18 || distanceFromLow > 30
      ? "MATURE"
      : "ESTABLISHED";

  const benchmarkCloses = benchmark?.daily.map((bar) => bar.c) ?? [];
  const benchmark5d = benchmarkCloses.length > 6 ? percentChange(benchmarkCloses.at(-6) ?? 0, benchmarkCloses.at(-1) ?? 0) : 0;
  const relative5d = percentChange(daily.at(-6)?.c ?? latest.c, latest.c) - benchmark5d;
  const benchmarkEma20 = benchmarkCloses.length ? last(ema(benchmarkCloses, 20)) ?? 0 : 0;
  const benchmarkTailwind = Boolean(benchmarkCloses.length && (last(benchmarkCloses) ?? 0) >= benchmarkEma20);
  const topology: DiscoveryPolicyInput["topology"] = relative5d >= 1.5
    ? benchmarkTailwind ? "TAILWIND" : "IDIOSYNCRATIC LEADER"
    : relative5d <= -4
      ? "HEADWIND"
      : "NEUTRAL";

  const sameSlot = intraday.slice(0, -1).filter((bar) => etSlot(bar.t) === etSlot(lastBar.t)).map((bar) => bar.v);
  const relativeVolume = mean(sameSlot) > 0 ? lastBar.v / mean(sameSlot) : 1;
  const pressure = closingLocation(lastBar);
  const participation: DiscoveryPolicyInput["participation"] = relativeVolume >= 1.4 && pressure <= 0.35
    ? "DISTRIBUTION"
    : relativeVolume >= 1.25 && pressure >= 0.6
    ? "CONFIRMED"
    : pressure >= 0.55 || relativeVolume >= 1.1
      ? "EARLY"
      : "MIXED";

  const proof = historicalProof(daily);
  const hardVetoes: string[] = [];
  const medianDollarVolume20 = median(daily.slice(-20).map((bar) => bar.c * bar.v));
  if (distanceFromLow > 25) hardVetoes.push("TOO_FAR_FROM_60D_LOW");
  if (run10 > 18) hardVetoes.push("TEN_DAY_RUN_EXCESSIVE");
  if (latest.c < invalidation) hardVetoes.push("INVALIDATION_BREACHED");
  if (latest.c < 1) hardVetoes.push("PRICE_BELOW_1_USD");
  if (medianDollarVolume20 < 5_000_000) hardVetoes.push("MEDIAN_DOLLAR_VOLUME_BELOW_5M");

  const levelsComplete = [support, entryLow, entryHigh, invalidation, chaseLine, target].every((value) => Number.isFinite(value) && value > 0)
    && invalidation < entryLow
    && entryLow <= entryHigh
    && entryHigh < chaseLine;
  // Data can still be useful outside the regular session, but it is never an
  // entry authority there. Keep the observation lane live for premarket,
  // after-hours, and the final closed-session bar; stale/lagging data still
  // fails closed and cannot produce a planning record.
  const actionWindowOpen = scan.freshness === "LIVE"
    && scan.session === "REGULAR"
    && scan.decisionWindowOpen !== false;
  const observationWindowOpen = ((scan.freshness === "LIVE" || scan.freshness === "BASELINE")
    && (scan.session === "PREMARKET" || scan.session === "REGULAR" || scan.session === "AFTERHOURS"))
    || (scan.freshness === "CLOSED" && scan.session === "CLOSED");
  const planningOnly = observationWindowOpen && !actionWindowOpen;
  const qualityBlockers = [...(input.qualityFlags ?? [])];
  if (!levelsComplete) qualityBlockers.push("INVALID_LEVEL_GEOMETRY");
  if (!observationWindowOpen) qualityBlockers.push(`DATA_WINDOW_${scan.session}_${scan.freshness}`);

  const policy = classifyDiscovery({
    quality: levelsComplete && observationWindowOpen ? "VALID" : "INVALID",
    qualityBlockers,
    hardVetoes,
    triggerState,
    triggerFresh: observationWindowOpen,
    insideEntryZone,
    anchor,
    formation,
    topology,
    participation,
    rewardRisk,
    belowChaseLine,
    levelsComplete,
    targetAlreadyTraded: targetGeometry.targetAlreadyTraded,
    proof: proof.state,
    shadowOnly: true,
    executionAuthority: "NONE",
  });

  // Never emit S/BUY outside regular hours: the live contract rejects that
  // combination even when the underlying setup is structurally strong.
  const displayTier: LiveDiscoveryDecision["tier"] = planningOnly && policy.tier === "S" ? "A" : policy.tier;
  const displayVerdict: LiveDiscoveryDecision["verdict"] = displayTier === "S"
    ? "BUY NOW"
    : displayTier === "AVOID"
      ? "AVOID"
      : displayTier === "NO VIEW"
        ? "NO VIEW"
        : "WAIT";
  const decisionUsable = actionWindowOpen && displayTier !== "NO VIEW";
  let nonOwnerAction: LiveDecisionAction = displayTier === "S" ? "BUY" : displayTier === "AVOID" ? "AVOID" : displayTier === "NO VIEW" ? "NO VIEW" : "WAIT";
  let ownerAction: LiveDecisionAction = latest.c < invalidation ? "SELL" : displayTier === "AVOID" || latest.c >= target * 0.98 ? "TRIM" : "HOLD";
  if (!actionWindowOpen) {
    nonOwnerAction = displayTier === "AVOID" ? "AVOID" : displayTier === "NO VIEW" ? "NO VIEW" : "WAIT";
    ownerAction = "NO VIEW";
  } else if (!decisionUsable) {
    nonOwnerAction = "NO VIEW";
    ownerAction = "NO VIEW";
  }

  const now = new Date(scan.generatedAt);
  const barAt = new Date(scan.barEndAt);
  const ageSeconds = Math.max(0, Math.round((now.getTime() - barAt.getTime()) / 1000));
  const validUntil = new Date(barAt.getTime() + 6.5 * 60_000).toISOString();
  const inputHash = createHash("sha256").update(JSON.stringify({
    symbol: input.symbol,
    barEndAt: scan.barEndAt,
    provider: scan.provider,
    daily: daily.slice(-80),
    intraday: intraday.slice(-40),
    support,
    target,
    policy,
  })).digest("hex");
  const policyHash = createHash("sha256").update("aperture-discovery@3.0.0").digest("hex");
  const triggerEvidence = sweepReclaim
    ? `Low swept ${money(support)} and reclaimed with ${Math.round(pressure * 100)}% closing location.`
    : structuralHold
      ? `Two completed bars held ${money(support)}; the latest close advanced.`
      : `RSI ${rsiNow.toFixed(1)} and MACD histogram ${signed(macdNow)} are curling from support.`;
  const action = nonOwnerAction === "BUY"
    ? `Inside the entry zone. Buy only below ${money(chaseLine)}; invalidate below ${money(invalidation)}.`
    : nonOwnerAction === "AVOID"
      ? `Do not initiate. ${policy.blockers.join(" · ") || "A hard risk gate failed."}`
      : nonOwnerAction === "NO VIEW"
        ? "No new entry. A mandatory live input is unavailable or expired."
        : planningOnly
          ? `Planning only outside the regular session. Watch ${money(entryLow)}–${money(entryHigh)}; revalidate on the next regular-session completed bar.`
        : `Wait for a fresh completed-bar confirmation inside ${money(entryLow)}–${money(entryHigh)}.`;

  return {
    id: `aperture-${input.symbol}-${scan.barEndAt.replaceAll(/[-:.TZ]/g, "")}-${triggerFamily}-v2`,
    symbol: input.symbol,
    company: input.company ?? input.symbol,
    sector: input.sector ?? "Aperture universe",
    tier: displayTier,
    verdict: displayVerdict,
    origin: "APERTURE ONLY",
    reason: `${triggerEvidence} Anchor ${anchor}; ${topology.toLowerCase()} context; ${participation.toLowerCase()} participation.`,
    action,
    price: money(latest.c),
    entry: `${money(entryLow)} — ${money(entryHigh)}`,
    invalidation: money(invalidation),
    chaseLine: money(chaseLine),
    target: money(target),
    dataMode: "live",
    provider: scan.provider,
    barEndAt: scan.barEndAt,
    generatedAt: scan.generatedAt,
    freshness: scan.freshness,
    decisionUsable,
    nonOwnerAction,
    ownerAction,
    chaseBuffer: belowChaseLine
      ? `${money(chaseLine - latest.c)} · ${Math.abs(percentChange(latest.c, chaseLine)).toFixed(2)}% below line`
      : `BREACHED BY ${money(latest.c - chaseLine)} · ${Math.abs(percentChange(chaseLine, latest.c)).toFixed(2)}%`,
    indicators: {
      rsi14: rsiNow.toFixed(1),
      rsiState: rsiCurl ? "CURLING UP" : "NOT CONFIRMED",
      macdHistogram: signed(macdNow),
      macdState: macdCurl ? "CURLING UP" : "NOT CONFIRMED",
      atr14: money(atrValue),
      vwap: money(vwap),
      distanceFrom60dLow: `${distanceFromLow.toFixed(1)}%`,
    },
    trigger: {
      family: triggerFamily,
      label: triggerLabel,
      state: triggerState === "NONE" ? "APPROACH" : triggerState,
      age: `${ageSeconds}s`,
      eventId: `aperture:${input.symbol}:${triggerFamily}:${scan.barEndAt}:v2`,
      seedBar: scan.barEndAt,
      expiresAt: validUntil,
      lifecycle: triggerState === "CONFIRMED" ? ["APPROACH", "SEED", "CONFIRMED"] : triggerState === "SEED" ? ["APPROACH", "SEED"] : ["APPROACH"],
      evidence: triggerEvidence,
    },
    packet: {
      schema: "aperture-decision.v2",
      policy: "aperture-discovery@3.0.0",
      decisionAt: scan.generatedAt,
      validUntil,
      shadowOnly: true,
      executionEligible: false,
      policyEligible: actionWindowOpen && policy.policyEligible,
      decisionUsable,
      orderExecutable: false,
      authority: "NONE · decision support only",
      reasonCodes: policy.reasonCodes,
      blockers: [...new Set([
        ...policy.blockers,
        ...(planningOnly ? [`OBSERVATION_ONLY_${scan.session}`, "NO_REGULAR_SESSION_AUTHORITY"] : []),
      ])],
      inputHash,
      policyHash,
      supersedesDecisionId: null,
    },
    tensor: {
      grade: "—",
      family: "independent Aperture scan",
      age: "—",
      eventAt: "No Tensor dependency",
      receiptAt: "No Tensor dependency",
      eventKey: "none",
      freshness: `${scan.freshness} · completed 5m bar`,
    },
    anchor: {
      state: anchor,
      tone: anchor === "PASS" ? "positive" : anchor === "HARD AVOID" ? "danger" : "neutral",
      evidence: `Frozen support ${money(support)} from completed-session EMA/pivot candidates`,
      support: money(support),
      distance: `${distanceAtr.toFixed(2)} ATR`,
      extension: `${extensionAtr.toFixed(2)} ATR`,
      run: `${signed(run10, "%")} / 10 sessions`,
      rewardRisk: `${rewardRisk.toFixed(1)}×`,
    },
    formation: {
      state: formation,
      tone: rsiCurl && macdCurl ? "positive" : formation === "MATURE" ? "danger" : "neutral",
      evidence: `RSI ${rsiCurl ? "curling" : "flat"}; MACD ${macdCurl ? "curling" : "unconfirmed"}`,
      micro: `${lastBar.c > previousBar.c ? "+" : "−"} completed 5m path`,
      meso: `${signed(percentChange(daily.at(-6)?.c ?? latest.c, latest.c), "%")} / 5 sessions`,
      macro: `${signed(percentChange(daily.at(-21)?.c ?? latest.c, latest.c), "%")} / 20 sessions`,
    },
    topology: {
      state: topology,
      tone: topology === "TAILWIND" || topology === "IDIOSYNCRATIC LEADER" ? "positive" : topology === "HEADWIND" ? "danger" : "neutral",
      evidence: `Five-session relative return versus QQQ: ${signed(relative5d, "%")}`,
      market: benchmarkTailwind ? "QQQ above EMA20" : "QQQ below EMA20",
      sector: input.sector ?? "declared universe",
      relative: `${signed(relative5d, "%")} vs QQQ`,
    },
    participation: {
      state: participation,
      tone: participation === "CONFIRMED" ? "positive" : participation === "DISTRIBUTION" ? "danger" : "neutral",
      evidence: `Same-slot volume and completed-bar closing pressure are evaluated independently`,
      relativeVolume: `${relativeVolume.toFixed(2)}× same-slot`,
      pressure: `${signed(pressure * 100, "%")} CLV`,
      breadth: `Coverage ${scan.coveredCount}/${scan.eligibleCount}`,
    },
    proof: {
      state: proof.state,
      tone: proof.state === "SUPPORTED" ? "positive" : proof.state === "MIXED" ? "warning" : "neutral",
      evidence: `${proof.count} non-overlapping historical analogs after 35 bps friction; holdout n=${proof.holdoutCount}, ${(proof.holdoutHitRate * 100).toFixed(0)}% positive, ${signed(proof.holdoutMedian, "%")} median`,
      sample: `n = ${proof.count}`,
      span: `${daily.length} sessions`,
      coverage: "chronological train / holdout · historical, not prospective",
      version: "pullback-curl-holdout@2",
    },
  };
}

function tierOrder(tier: LiveDiscoveryDecision["tier"]) {
  return ({ S: 0, A: 1, B: 2, FORMING: 3, AVOID: 4, "NO VIEW": 5 } as const)[tier];
}

export function buildLiveDiscoveryView(input: LiveScanInput): LiveDiscoveryView {
  const expectedBarStart = new Date(new Date(input.barEndAt).getTime() - 5 * 60_000).toISOString();
  const benchmarkCandidate = input.symbols.find((symbol) => symbol.symbol === "QQQ") ?? input.symbols.find((symbol) => symbol.symbol === "SPY");
  const benchmarkReady = Boolean(benchmarkCandidate
    && benchmarkCandidate.providerEligible !== false
    && !benchmarkCandidate.qualityFlags?.length
    && last(benchmarkCandidate.intraday)
    && new Date(last(benchmarkCandidate.intraday)!.t).toISOString() === expectedBarStart);
  const benchmark = benchmarkReady ? benchmarkCandidate : undefined;
  const all = benchmark
    ? input.symbols.map((symbol) => classifyOne(symbol, benchmark, input)).filter((value): value is LiveDiscoveryDecision => Boolean(value))
    : [];
  const ranked = all.sort((left, right) => {
    const tierDelta = tierOrder(left.tier) - tierOrder(right.tier);
    if (tierDelta) return tierDelta;
    return Number.parseFloat(left.anchor.distance) - Number.parseFloat(right.anchor.distance);
  });
  const actionable = ranked.filter((decision) => decision.tier === "S" || decision.tier === "A" || decision.tier === "B");
  const supportQueue = ranked.filter((decision) => decision.tier === "FORMING").slice(0, 6);
  const riskQueue = ranked.filter((decision) => decision.tier === "AVOID" || decision.tier === "NO VIEW").slice(0, 4);
  const decisions = [...actionable.slice(0, 10), ...supportQueue, ...riskQueue].slice(0, 16);
  const count = (tier: LiveDiscoveryDecision["tier"]) => decisions.filter((decision) => decision.tier === tier).length;
  const triggerCounts = new Map<string, number>();
  for (const decision of all) triggerCounts.set(decision.trigger.family, (triggerCounts.get(decision.trigger.family) ?? 0) + 1);
  const etagHash = createHash("sha256").update(JSON.stringify({ barEndAt: input.barEndAt, decisions: decisions.map((decision) => [decision.id, decision.tier, decision.packet.inputHash]) })).digest("hex").slice(0, 24);
  const validUntil = new Date(new Date(input.barEndAt).getTime() + 6.5 * 60_000).toISOString();
  const coveragePct = input.eligibleCount ? (input.coveredCount / input.eligibleCount) * 100 : 0;
  const marketDecision = benchmark ? all.find((decision) => decision.symbol === benchmark.symbol) : undefined;
  const positiveBreadth = all.filter((decision) => decision.topology.tone === "positive").length;
  return {
    schema: "aperture-live-view.v1",
    dataMode: "live",
    provider: input.provider,
    feed: input.feed,
    connection: (input.freshness === "LIVE" || input.freshness === "BASELINE") && coveragePct >= 95 ? "CONNECTED" : coveragePct >= 75 ? "DEGRADED" : "OFFLINE",
    freshness: input.freshness,
    session: input.session,
    sessionLabel: input.sessionLabel,
    marketNextTransitionAt: input.marketNextTransitionAt ?? null,
    generatedAt: input.generatedAt,
    inputWatermarkAt: input.barEndAt,
    barEndAt: input.barEndAt,
    validUntil,
    etag: `W/"aperture-live-${etagHash}"`,
    authority: { decisionSupport: true, orderRoute: false, tensorWrite: false, galathWrite: false, folioTendWrite: false },
    universe: {
      id: APERTURE_UNIVERSE_ID,
      count: APERTURE_UNIVERSE_COUNT,
      hash: APERTURE_UNIVERSE_HASH,
      eligible: input.eligibleCount,
      covered: input.coveredCount,
      unsupported: input.unsupportedCount,
    },
    scan: {
      state: "COMPLETE",
      elapsedMs: input.elapsedMs,
      harvested: input.coveredCount,
      deepCandidates: all.length,
      decisions: decisions.length,
      executable: 0,
      stages: [
        { label: "Bar sealed", value: input.barEndAt, note: `${input.freshness.toLowerCase()} completed 5m`, tone: input.freshness === "LIVE" || input.freshness === "BASELINE" ? "cyan" : "amber" },
        { label: "Universe", value: `${input.coveredCount} / ${input.eligibleCount}`, note: `${coveragePct.toFixed(1)}% eligible coverage`, tone: coveragePct >= 95 ? "cyan" : "amber" },
        { label: "Deep pass", value: String(all.length), note: "location + curl + context", tone: "default" },
        { label: "Decisions", value: String(decisions.length), note: "deterministic Gestalt", tone: "default" },
        { label: "Orders", value: "0", note: "no order route", tone: "amber" },
      ],
    },
    summary: [
      { label: "Buy now", value: String(count("S")), note: "fresh supported S", tone: "cyan" },
      { label: "Wait / watch", value: String(count("A") + count("B") + count("FORMING")), note: "A / B / forming", tone: "default" },
      { label: "Avoid", value: String(count("AVOID")), note: "anti-chase / hard veto", tone: "amber" },
      { label: "No view", value: String(Math.max(0, APERTURE_UNIVERSE_COUNT - decisions.filter((decision) => decision.tier !== "NO VIEW").length)), note: "not selected / missing current bar / unsupported", tone: "default" },
    ],
    backdrop: [
      { label: "Market", value: marketDecision?.topology.state ?? "NO VIEW", detail: marketDecision?.topology.market ?? "benchmark unavailable", tone: marketDecision?.topology.tone === "positive" ? "positive" : "neutral" },
      { label: "Breadth", value: all.length ? `${Math.round((positiveBreadth / all.length) * 100)}% constructive` : "NO VIEW", detail: `${positiveBreadth}/${all.length} deep candidates`, tone: positiveBreadth / Math.max(all.length, 1) >= 0.55 ? "positive" : "warning" },
      { label: "Freshness", value: input.freshness, detail: input.barEndAt, tone: input.freshness === "LIVE" || input.freshness === "BASELINE" || input.freshness === "CLOSED" ? "positive" : "warning" },
      { label: "Authority", value: "DECISION SUPPORT", detail: "no broker or system write route", tone: "neutral" },
    ],
    triggers: LIVE_TRIGGER_REGISTRY.map((trigger) => ({ ...trigger, active: triggerCounts.get(trigger.id) ?? 0 })),
    decisions,
    quality: {
      flags: [input.freshness, "ELIGIBILITY_DAILY80_PRICE1_MDV5M", coveragePct < 95 ? "PARTIAL_PROVIDER_COVERAGE" : "FULL_PROVIDER_COVERAGE", benchmarkReady ? "BENCHMARK_CURRENT" : "BENCHMARK_UNAVAILABLE_CURRENT_WATERMARK", "ORDER_ROUTE_ABSENT"],
      missingInputs: [...input.symbols.flatMap((symbol) => symbol.qualityFlags ?? []), ...(benchmarkReady ? [] : ["CURRENT_QQQ_OR_SPY_BAR"])],
      coveragePct,
    },
  };
}
