import type {
  VectorAnalysis,
  VectorBar,
  VectorZone,
} from "./vector-engine.ts";

/**
 * Gold is an additive classifier. It can only be true when the existing
 * literal buy-green marker is already true. Nothing in this module changes
 * primaryMarkers, VECTOR_BUY/VECTOR_SELL state, or notification routing.
 */
export const VECTOR_GOLD_DIAMOND_VERSION = "gold-diamond/1.0.0-causal";

type SupportGroup =
  | "demand-zone"
  | "ema-stack"
  | "ema200"
  | "anchored-vwap"
  | "fibonacci";

type SupportLevel = {
  group: SupportGroup;
  label: string;
  value: number;
  zone: VectorZone | null;
  anchor: boolean;
};

type SupportReference = {
  group: SupportGroup;
  label: string;
  value: number;
  distanceAtr: number;
  confluenceGroups: SupportGroup[];
  anchorPresent: boolean;
};

type ParticipationEvidence = {
  rvol: number | null;
  rvolPass: boolean;
  obvSlope5: number | null;
  obvPass: boolean;
  cmf20: number | null;
  previousCmf20: number | null;
  cmfPass: boolean;
  upVolumeShare10: number | null;
  upVolumePass: boolean;
  passed: number;
  required: 3;
};

export type GoldDiamondEvaluation = {
  version: typeof VECTOR_GOLD_DIAMOND_VERSION;
  status: "qualified" | "rejected" | "warming";
  qualifies: boolean;
  baseGreen: boolean;
  structuralSupportPass: boolean;
  supportHoldOrReclaim: boolean;
  smartMoneyPass: boolean;
  noDistribution: boolean;
  noBreakdown: boolean;
  extensionPass: boolean;
  supportReference: SupportReference | null;
  extensionAtr: number | null;
  confluenceGroups: SupportGroup[];
  participation: ParticipationEvidence;
  reasons: string[];
  vetoes: string[];
};

const finite = (value: unknown): value is number =>
  typeof value === "number" && Number.isFinite(value);

const highOf = (bar: VectorBar) => (finite(bar.high) ? bar.high : bar.close);
const lowOf = (bar: VectorBar) => (finite(bar.low) ? bar.low : bar.close);
const openOf = (bar: VectorBar) => (finite(bar.open) ? bar.open : bar.close);

function emptyParticipation(): ParticipationEvidence {
  return {
    rvol: null,
    rvolPass: false,
    obvSlope5: null,
    obvPass: false,
    cmf20: null,
    previousCmf20: null,
    cmfPass: false,
    upVolumeShare10: null,
    upVolumePass: false,
    passed: 0,
    required: 3,
  };
}

function rejectedEvaluation(
  baseGreen: boolean,
  status: GoldDiamondEvaluation["status"] = "rejected",
  reasons: string[] = [],
  vetoes: string[] = [],
): GoldDiamondEvaluation {
  return {
    version: VECTOR_GOLD_DIAMOND_VERSION,
    status,
    qualifies: false,
    baseGreen,
    structuralSupportPass: false,
    supportHoldOrReclaim: false,
    smartMoneyPass: false,
    noDistribution: true,
    noBreakdown: true,
    extensionPass: false,
    supportReference: null,
    extensionAtr: null,
    confluenceGroups: [],
    participation: emptyParticipation(),
    reasons,
    vetoes,
  };
}

function linearSlope(values: number[]) {
  if (values.length < 2 || values.some(value => !finite(value))) return null;
  const xMean = (values.length - 1) / 2;
  const yMean = values.reduce((sum, value) => sum + value, 0) / values.length;
  let numerator = 0;
  let denominator = 0;
  values.forEach((value, index) => {
    numerator += (index - xMean) * (value - yMean);
    denominator += (index - xMean) ** 2;
  });
  return denominator === 0 ? 0 : numerator / denominator;
}

function obvSeries(bars: VectorBar[]) {
  const output = Array<number>(bars.length).fill(0);
  for (let index = 1; index < bars.length; index += 1) {
    const volume = finite(bars[index].volume) ? Number(bars[index].volume) : 0;
    output[index] = output[index - 1] +
      (bars[index].close > bars[index - 1].close
        ? volume
        : bars[index].close < bars[index - 1].close
          ? -volume
          : 0);
  }
  return output;
}

function relativeVolume(bars: VectorBar[], index: number) {
  if (index < 20 || !finite(bars[index].volume) || bars[index].volume <= 0)
    return null;
  const prior = bars
    .slice(index - 20, index)
    .map(bar => bar.volume)
    .filter(finite);
  if (prior.length !== 20) return null;
  const mean = prior.reduce((sum, value) => sum + value, 0) / prior.length;
  return mean > 0 ? Number(bars[index].volume) / mean : null;
}

function cmf(bars: VectorBar[], endIndex: number, length = 20) {
  if (endIndex < length - 1) return null;
  const window = bars.slice(endIndex - length + 1, endIndex + 1);
  if (window.some(bar => !finite(bar.volume) || bar.volume <= 0)) return null;
  let moneyFlowVolume = 0;
  let volumeTotal = 0;
  for (const bar of window) {
    const high = highOf(bar);
    const low = lowOf(bar);
    const range = high - low;
    const multiplier = range > 0
      ? ((bar.close - low) - (high - bar.close)) / range
      : 0;
    moneyFlowVolume += multiplier * Number(bar.volume);
    volumeTotal += Number(bar.volume);
  }
  return volumeTotal > 0 ? moneyFlowVolume / volumeTotal : null;
}

function upVolumeShare(bars: VectorBar[], endIndex: number, length = 10) {
  if (endIndex < length) return null;
  const window = bars.slice(endIndex - length + 1, endIndex + 1);
  if (window.some(bar => !finite(bar.volume) || bar.volume < 0)) return null;
  let total = 0;
  let up = 0;
  window.forEach((bar, offset) => {
    const index = endIndex - length + 1 + offset;
    const volume = Number(bar.volume);
    total += volume;
    if (bar.close > bars[index - 1].close) up += volume;
  });
  return total > 0 ? up / total : null;
}

function causalAnchoredVwap(
  bars: VectorBar[],
  index: number,
  zones: VectorZone[],
) {
  const usableAnchors = zones
    .filter(zone =>
      zone.model === "A" &&
      !zone.contextOnly &&
      zone.state !== "broken" &&
      zone.knownAtIndex < index &&
      zone.createdIndex < index,
    )
    .sort((left, right) => right.knownAtIndex - left.knownAtIndex);
  const anchorIndex = Math.min(
    index - 1,
    usableAnchors[0]?.createdIndex ?? Math.max(0, index - 63),
  );
  if (anchorIndex < 0) return null;
  let weightedPrice = 0;
  let volumeTotal = 0;
  for (let cursor = anchorIndex; cursor < index; cursor += 1) {
    const bar = bars[cursor];
    const volume = finite(bar.volume) && bar.volume > 0 ? bar.volume : 0;
    if (volume <= 0) continue;
    weightedPrice += ((highOf(bar) + lowOf(bar) + bar.close) / 3) * volume;
    volumeTotal += volume;
  }
  return volumeTotal > 0 ? weightedPrice / volumeTotal : null;
}

function causalFibSupportLevels(bars: VectorBar[], index: number) {
  const end = index - 1;
  if (end < 1) return [] as number[];
  const start = Math.max(0, end - 62);
  let low = Number.POSITIVE_INFINITY;
  let high = Number.NEGATIVE_INFINITY;
  let lowIndex = start;
  let highIndex = start;
  for (let cursor = start; cursor <= end; cursor += 1) {
    const barLow = lowOf(bars[cursor]);
    const barHigh = highOf(bars[cursor]);
    if (barLow < low) {
      low = barLow;
      lowIndex = cursor;
    }
    if (barHigh > high) {
      high = barHigh;
      highIndex = cursor;
    }
  }
  if (!(high > low) || !finite(low) || !finite(high)) return [];
  const rising = lowIndex <= highIndex;
  return [0.236, 0.382, 0.5, 0.618, 0.786].map(ratio =>
    rising
      ? high - (high - low) * ratio
      : low + (high - low) * ratio,
  );
}

function supportLevels(
  bars: VectorBar[],
  index: number,
  analysis: VectorAnalysis,
  atr: number,
) {
  const result = analysis.bars[index];
  const zones = analysis.causalZonesByIndex?.[index] ??
    analysis.zones.filter(zone => zone.knownAtIndex < index);
  const levels: SupportLevel[] = [];
  for (const zone of zones) {
    if (zone.polarity !== "demand" || zone.state === "broken") continue;
    if (
      !zone.dualConfirmed &&
      zone.strength < 0.48
    ) continue;
    levels.push({
      group: "demand-zone",
      label: `${zone.model} demand ${zone.id}`,
      value: zone.high,
      zone,
      anchor: true,
    });
  }
  const series = analysis.series;
  const ema21 = series.ema21[index];
  const ema55 = series.ema55[index];
  const ema200 = series.ema200[index];
  if (finite(ema21))
    levels.push({
      group: "ema-stack",
      label: "EMA21",
      value: ema21,
      zone: null,
      anchor: false,
    });
  if (finite(ema55))
    levels.push({
      group: "ema-stack",
      label: "EMA55",
      value: ema55,
      zone: null,
      anchor: false,
    });
  if (finite(ema200))
    levels.push({
      group: "ema200",
      label: "EMA200",
      value: ema200,
      zone: null,
      anchor: true,
    });
  const avwap = causalAnchoredVwap(bars, index, zones);
  if (finite(avwap))
    levels.push({
      group: "anchored-vwap",
      label: "causal anchored VWAP",
      value: avwap,
      zone: null,
      anchor: true,
    });
  for (const value of causalFibSupportLevels(bars, index)) {
    levels.push({
      group: "fibonacci",
      label: "63-bar Fibonacci retracement",
      value,
      zone: null,
      anchor: false,
    });
  }
  return {
    result,
    zones,
    levels: levels.filter(level =>
      Math.abs(bars[index].close - level.value) <= 2 * atr,
    ),
  };
}

function supportTest(
  bar: VectorBar,
  level: SupportLevel,
  atr: number,
) {
  const range = Math.max(highOf(bar) - lowOf(bar), atr * 0.01);
  const body = Math.abs(bar.close - openOf(bar));
  const closeLocation = (bar.close - lowOf(bar)) / range;
  const lowerWick = Math.min(openOf(bar), bar.close) - lowOf(bar);
  const lower = level.zone?.low ?? level.value;
  const upper = level.zone?.high ?? level.value;
  return (
    lowOf(bar) <= upper + 0.08 * atr &&
    lowOf(bar) >= lower - 0.2 * atr &&
    bar.close >= upper + 0.03 * atr &&
    bar.close > openOf(bar) &&
    lowerWick >= Math.max(0.15 * atr, 0.65 * body) &&
    closeLocation >= 0.68
  );
}

function supportReferenceFor(
  bars: VectorBar[],
  index: number,
  analysis: VectorAnalysis,
  atr: number,
) {
  const { levels } = supportLevels(bars, index, analysis, atr);
  const tested = levels.filter(level => supportTest(bars[index], level, atr));
  if (!tested.length) return null;
  const best = tested
    .map(level => {
      const confluenceGroups = [...new Set(
        levels
          .filter(candidate =>
            Math.abs(candidate.value - level.value) <= 0.5 * atr,
          )
          .map(candidate => candidate.group),
      )];
      return {
        level,
        confluenceGroups,
        anchorPresent:
          confluenceGroups.includes("demand-zone") ||
          confluenceGroups.includes("ema200") ||
          confluenceGroups.includes("anchored-vwap"),
      };
    })
    .sort((left, right) =>
      Number(right.anchorPresent) - Number(left.anchorPresent) ||
      right.confluenceGroups.length - left.confluenceGroups.length ||
      Math.abs(bars[index].close - left.level.value) -
        Math.abs(bars[index].close - right.level.value),
    )[0];
  if (!best) return null;
  return {
    group: best.level.group,
    label: best.level.label,
    value: best.level.zone?.high ?? best.level.value,
    distanceAtr: (bars[index].close - (best.level.zone?.high ?? best.level.value)) / atr,
    confluenceGroups: best.confluenceGroups,
    anchorPresent: best.anchorPresent,
  } satisfies SupportReference;
}

function smartMoneyEvidence(bars: VectorBar[], index: number): ParticipationEvidence {
  const rvol = relativeVolume(bars, index);
  const obv = obvSeries(bars);
  const obvWindow = index >= 4 ? obv.slice(index - 4, index + 1) : [];
  const obvSlope5 = obvWindow.length === 5 ? linearSlope(obvWindow) : null;
  const cmf20 = cmf(bars, index, 20);
  const previousCmf20 = cmf(bars, index - 1, 20);
  const upVolumeShare10Value = upVolumeShare(bars, index, 10);
  const rvolPass = finite(rvol) && rvol >= 1.1;
  const obvPass = finite(obvSlope5) && obvSlope5 > 0;
  const cmfPass = finite(cmf20) &&
    (cmf20 >= 0 || (finite(previousCmf20) && cmf20 > previousCmf20));
  const upVolumePass = finite(upVolumeShare10Value) && upVolumeShare10Value >= 0.55;
  const passed = [rvolPass, obvPass, cmfPass, upVolumePass]
    .filter(Boolean).length;
  return {
    rvol,
    rvolPass,
    obvSlope5,
    obvPass,
    cmf20,
    previousCmf20,
    cmfPass,
    upVolumeShare10: upVolumeShare10Value,
    upVolumePass,
    passed,
    required: 3,
  };
}

function hasSupplyRejection(
  bar: VectorBar,
  atr: number,
  zones: VectorZone[],
) {
  const range = Math.max(highOf(bar) - lowOf(bar), atr * 0.01);
  const body = Math.abs(bar.close - openOf(bar));
  const closeLocation = (bar.close - lowOf(bar)) / range;
  const upperWick = highOf(bar) - Math.max(openOf(bar), bar.close);
  const nearSupply = zones.some(zone =>
    zone.polarity === "supply" &&
    zone.state !== "broken" &&
    highOf(bar) >= zone.low - 0.1 * atr &&
    highOf(bar) <= zone.high + 0.75 * atr,
  );
  return (
    nearSupply &&
    bar.close <= openOf(bar) &&
    closeLocation <= 0.55 &&
    upperWick >= Math.max(0.15 * atr, 0.65 * body)
  );
}

function demandBreakdown(
  bar: VectorBar,
  atr: number,
  zones: VectorZone[],
) {
  return zones.some(zone =>
    zone.polarity === "demand" &&
    zone.state !== "broken" &&
    bar.close < zone.low - 0.2 * atr,
  );
}

export function evaluateGoldDiamond({
  index,
  bars,
  analysis,
  greenBase,
}: {
  index: number;
  bars: VectorBar[];
  analysis: VectorAnalysis;
  greenBase: boolean;
}): GoldDiamondEvaluation {
  if (!greenBase)
    return rejectedEvaluation(false, "rejected", [
      "Existing Tensor green marker is absent; Gold is never an independent signal.",
    ]);
  const bar = bars[index];
  const result = analysis.bars[index];
  const atr = analysis.series.atr14[index];
  if (!bar || !result || !finite(atr) || atr <= 0 || index <= 0)
    return rejectedEvaluation(true, "warming", [], [
      "Causal structural or ATR evidence is still warming.",
    ]);

  const { zones } = supportLevels(bars, index, analysis, atr);
  const supportReference = supportReferenceFor(bars, index, analysis, atr);
  const supportHoldOrReclaim = Boolean(supportReference) ||
    ["demand-bounce", "demand-hold", "demand-reclaim"].includes(
      result.locationTrigger,
    );
  const confluenceGroups = supportReference?.confluenceGroups ?? [];
  const structuralSupportPass =
    confluenceGroups.length >= 2 &&
    Boolean(supportReference?.anchorPresent);
  const participation = smartMoneyEvidence(bars, index);
  const smartMoneyPass = participation.passed >= participation.required;

  const range = Math.max(highOf(bar) - lowOf(bar), atr * 0.01);
  const closeLocation = (bar.close - lowOf(bar)) / range;
  const highVolumeWeakClose =
    finite(participation.rvol) &&
    participation.rvol >= 1.25 &&
    bar.close <= openOf(bar) &&
    closeLocation <= 0.45;
  const flowDistribution =
    finite(participation.obvSlope5) &&
    participation.obvSlope5 < 0 &&
    finite(participation.cmf20) &&
    participation.cmf20 < 0;
  const noDistribution = !(
    highVolumeWeakClose ||
    flowDistribution ||
    hasSupplyRejection(bar, atr, zones)
  );
  const noBreakdown =
    result.locationTrigger !== "demand-breakdown" &&
    !demandBreakdown(bar, atr, zones);
  const extensionAtr = supportReference
    ? (bar.close - supportReference.value) / atr
    : null;
  const extensionPass =
    finite(extensionAtr) && extensionAtr >= 0 && extensionAtr <= 1.5;
  const qualifies =
    structuralSupportPass &&
    supportHoldOrReclaim &&
    smartMoneyPass &&
    noDistribution &&
    noBreakdown &&
    extensionPass;

  const reasons = [
    ...(structuralSupportPass
      ? [`${confluenceGroups.length} independent support groups within 0.50 ATR.`]
      : []),
    ...(supportHoldOrReclaim
      ? ["The completed candle held or reclaimed the causal support reference."]
      : []),
    ...(smartMoneyPass
      ? [`${participation.passed}/4 participation tests passed.`]
      : []),
    ...(extensionPass
      ? [`Extension is ${extensionAtr?.toFixed(2)} ATR from support.`]
      : []),
  ];
  const vetoes = [
    ...(!structuralSupportPass
      ? ["Fewer than two independent support groups or no hard anchor."]
      : []),
    ...(!supportHoldOrReclaim
      ? ["No completed-bar support hold/reclaim candle."]
      : []),
    ...(!smartMoneyPass
      ? [`Only ${participation.passed}/4 participation tests passed.`]
      : []),
    ...(!noDistribution ? ["Distribution or supply rejection veto."] : []),
    ...(!noBreakdown ? ["Demand breakdown veto."] : []),
    ...(!extensionPass ? ["Price is absent from, below, or more than 1.50 ATR above support."] : []),
  ];
  return {
    version: VECTOR_GOLD_DIAMOND_VERSION,
    status: qualifies ? "qualified" : "rejected",
    qualifies,
    baseGreen: true,
    structuralSupportPass,
    supportHoldOrReclaim,
    smartMoneyPass,
    noDistribution,
    noBreakdown,
    extensionPass,
    supportReference,
    extensionAtr,
    confluenceGroups,
    participation,
    reasons,
    vetoes,
  };
}
