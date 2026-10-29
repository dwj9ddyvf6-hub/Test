import { tensorDateFormatter } from "./tensor-date-format.mjs";
import { classifyAnnaTemplateEpoch } from "./anna-epochs.mjs";
import { buildTensorContextSeries } from "../app/lib/tensor-context.mjs";
import { TENSOR_CHART_DISPLAY_BARS } from "./tensor-chart-window.mjs";

export const ANNA_REPLICA_VERSION = "anna-replica/0.8.0-accuracy";
export const ANNA_LIVE_VERSION = "anna-live/1.0.0";

export const ANNA_REPLICA_COMPONENTS = Object.freeze([
  {
    id: "bb-kc-squeeze",
    label: "BB/KC Squeeze",
    status: "reconstructed",
    parameters: "20, 2, 2, 10, close",
    note: "The panel family and displayed tuples are observed: April appears to show 14, 2, 2, 9, close, while the May-current epoch shows 20, 2, 2, 10, close. Each historical bar uses the template profile available at that timestamp. The Lab’s classical BB/KC formula and May 22 change boundary are reconstructed rather than claimed as source-code identity.",
    source: "https://help.trendspider.com/kb/indicators/bb-slash-kc-squeeze",
  },
  {
    id: "phase2-red-event",
    label: "Red diamond · fast reversal",
    status: "reconstructed",
    parameters: "UT-style ATR state line; sensitivity 1; ATR 10",
    note: "Across ten bar-aligned red diamonds in the two visible daily histories, this ATR reversal is exact on 4/10 and within three completed bars on 7/10. It remains 2/2 on the originally selected active pair. The larger event inventory—not the selected pair—now governs the evidence label.",
    confidence:
      "Exact on 4/10 visible red events; active-pair fit 2/2; feed parity approximate",
    falsifier:
      "Freeze the rule and test additional untouched red diamonds against explicitly verified visible no-marker bars. Failure to remain enriched rejects it.",
    source: "https://www.tradingview.com/script/n8ss8BID-UT-Bot-Alerts/",
  },
  {
    id: "opencipher-comparator",
    label: "OpenCipher A · alternate red mechanism",
    status: "candidate",
    parameters:
      "WaveTrend 9/12/3; EMA 5/11/15/18/21/25/29/33; 60-bar candle-pressure average",
    note: "The source-pinned public mathematics is exact on 3/10 visible Anna red diamonds, within one completed bar on 7/10, and within three on 9/10, while emitting 13 events across the 115 eligible visible bars in the frozen comparison corpus. It is a fast timing and veto-layer probe—not evidence of lineage, an independent vote, or part of Anna's score.",
    confidence:
      "Exact on 3/10 visible red events; 7/10 within one bar; 9/10 within three",
    falsifier:
      "Freeze both the OpenCipher and UT-style hypotheses, then compare precision, recall and lead/lag on untouched Anna markers and explicitly verified visible no-marker bars.",
    source: "https://www.tradingview.com/script/rMNKOT6f-OpenCipher-A/",
  },
  {
    id: "strat-comparator",
    label: "The STRAT · price-structure comparator",
    status: "candidate",
    parameters: "1 / 2U / 2D / 3 from strict prior-high and prior-low breaks",
    note: "This is an exhaustive OHLC range taxonomy: contained, upward expansion, downward expansion or two-sided expansion. It can explain the price structure surrounding Anna events without importing another smoothed oscillator. A historical outside bar cannot reveal which side broke first, so that direction remains unknown without lower-timeframe sequence data.",
    confidence: "Exact deterministic classification; predictive value unproven",
    falsifier:
      "Do not promote it unless held-out tests improve direction or normalized excursion after controlling for Aroon, DI, squeeze and EMA state.",
    source:
      "https://www.newtraderu.com/2019/02/13/what-do-we-know-to-be-true-about-price-action/",
  },
  {
    id: "avwap-comparator",
    label: "Objective anchored VWAP · positional comparator",
    status: "candidate",
    parameters:
      "Typical-price × volume; fixed session/year boundary and last confirmed Anna-event anchors",
    note: "AVWAP is retained only as positional context: above, below or testing; distance; slope; and bars held. Fixed calendar anchors are independent. Anna-event anchors can measure post-call follow-through but cannot validate the original call. It stays descriptive and does not affect the distilled call.",
    confidence:
      "Formula exact for the supplied bars; source volume and anchor policy remain material",
    falsifier:
      "Preregister anchors with originAt and knownAt, then require prospective incremental value beyond Anna alone.",
    source:
      "https://www.tradingview.com/support/solutions/43000502018-volume-weighted-average-price-vwap/",
  },
  {
    id: "phase2-magenta-event",
    label: "Magenta diamond · slower confirmation",
    status: "reconstructed",
    parameters: "EMA 8 crossing EMA 21",
    note: "Across four bar-aligned pale-magenta sell diamonds, the raw EMA8/21 bearish transition is exact on 2/4, within one completed bar on 3/4, and within three on 4/4. It is closer to the observed color timing than OpenCipher's faster EMA5/11 red X, but the parameter set is not identified.",
    confidence:
      "Exact on 2/4 visible magenta events; 3/4 within one bar; 4/4 within three",
    falsifier:
      "Preregistered replication must reproduce additional untouched magenta markers better than the transition's ordinary background event rate.",
    source: "https://www.tradingview.com/script/I4VXGe18-Saty-Pivot-Ribbon/",
  },
  {
    id: "phase2-warning-event",
    label: "Gold warning · fast/slow conflict",
    status: "reconstructed",
    parameters: "Reduced proxy: WaveTrend bullish cross while the slow EMA state remains bearish",
    note: "POET's April 1 warning coincides with a fast bullish wave cross while slower EMA and trend states remain bearish. This reduced Lab proxy omits the still-unimplemented SuperTrend and EMA5/33 controls, so it is rendered as a gold warning star, never as a third primary sell.",
    confidence: "Exact-bar explanatory match in 1 reconstructed warning",
    falsifier:
      "Additional warnings that do not concentrate in fast/slow disagreement reject the rule.",
    source:
      "https://www.tradingview.com/script/2KE8wTuF-Indicator-WaveTrend-Oscillator-WT/",
  },
  {
    id: "stoch-rsi",
    label: "Stochastic RSI",
    status: "confirmed",
    parameters: "14, 14, 3, 3, 80, 20, close",
    note: "The oscillator and its displayed settings recur in the preserved chart corpus.",
    source: "https://help.trendspider.com/kb/indicators/stochastic-rsi",
  },
  {
    id: "aroon",
    label: "Aroon",
    status: "confirmed",
    parameters: "14",
    note: "Aroon (14) is explicitly visible on preserved charts.",
    source: "https://help.trendspider.com/kb/indicators/aroon",
  },
  {
    id: "adx-di",
    label: "ADX / DI",
    status: "confirmed",
    parameters: "14, 35, 20",
    note: "The displayed tuple matches TrendSpider’s ADX DI length and upper/lower guides.",
    source: "https://help.trendspider.com/kb/indicators/adx-di",
  },
  {
    id: "obv",
    label: "On-balance volume",
    status: "confirmed",
    parameters: "cumulative",
    note: "OBV is explicitly named in Anna’s lower panels. This build uses a five-bar OBV slope in its benchmark and a separate ten-bar price/OBV slope-disagreement overlay; neither is claimed as Libertus pivot logic.",
    source: "https://help.trendspider.com/kb/indicators/on-balance-volume",
  },
  {
    id: "obv-divergences-libertus",
    label: "OBV Divergences — Libertus",
    status: "candidate",
    parameters: "90 default, 55 daily, 40 weekly, 15 monthly",
    note: "The name, Pivot/Bull/Bear vocabulary and four lookbacks match the screenshot. Exact screenshot-value reproduction is still required.",
    confidence: "High family identification; numerical match pending",
    falsifier:
      "Run the public script on matched TrendSpider bars; repeated pivot-label or value disagreement rejects the identification.",
    source:
      "https://trendspider.com/trading-tools-store/indicators/68a350-obv-divergences-libertus/",
  },
  {
    id: "red-dragon-mcdx",
    label: "Red Dragon MCDX",
    status: "candidate",
    parameters: "100-bar range, 5-bar smoothing",
    note: "The OCR, red/green/yellow stack and 0–100 scale match. This build reproduces the public formula, but identification remains a candidate pending numerical screenshot matching.",
    confidence: "Low identification strength",
    falsifier:
      "Reject if it fails to outperform simpler OBV, CMF, MFI or accumulation/distribution proxies against frozen Anna flow narratives.",
    source:
      "https://trendspider.com/trading-tools-store/indicators/68ae72-red-dragon-mcdx/",
  },
  {
    id: "rvol",
    label: "Relative volume",
    status: "confirmed",
    parameters: "current volume ÷ prior 20-bar SMA reconstruction",
    note: "Vol, Avg Vol and RVol are visible. The prior-bar averaging rule follows TrendSpider documentation; the 20-bar length remains a screenshot-fit hypothesis.",
    source: "https://help.trendspider.com/kb/indicators/relative-volume",
  },
  {
    id: "ema200",
    label: "EMA 200",
    status: "confirmed",
    parameters: "200, close",
    note: "The long orange dotted average is repeatedly identified as EMA200 in Anna’s calls.",
    source: "https://help.trendspider.com/kb/indicators/exponential-moving-average",
  },
  {
    id: "ma-ribbon",
    label: "Moving Average Ribbon",
    status: "candidate",
    parameters: "8 EMA; likely initial 10, step 10",
    note: "The eight-strand rainbow is a strong visual match for TrendSpider’s native ribbon. The family identification is stronger than the exact lengths, so this build exposes 10–80 EMA as a testable candidate.",
    confidence: "High family strength · medium-high settings strength",
    falsifier:
      "Overlay native TrendSpider values on matched ICE bars; systematic strand divergence rejects the 10/10 parameter hypothesis.",
    source:
      "https://help.trendspider.com/kb/indicators/moving-average-ribbon",
  },
  {
    id: "gonogo-candidate",
    label: "GoNoGo Trend candle family",
    status: "candidate",
    parameters: "licensed five-state trend painter; palette remapped",
    note: "Its strong/weak bullish, neutral and strong/weak bearish bar states fit Anna’s persistence through pullbacks better than a one-factor painter. The formula is proprietary, so identification requires bar-for-bar comparison inside TrendSpider.",
    confidence: "Medium family strength · low exact-formula strength",
    falsifier:
      "After palette remapping, more than 5% unexplained closed-bar mismatch across multiple visual epochs rejects the candidate.",
    source: "https://help.trendspider.com/kb/indicators/go-no-go",
  },
  {
    id: "candle-regime",
    label: "Blue / pale-gold regime surrogate",
    status: "reconstructed",
    parameters: "persistent EMA 13/48 direction + close versus EMA21; hysteresis during mixed states",
    note: "Anna defines the colors but not their trigger. Phase 2 replaces the twitchier MACD-histogram painter with a transparent slow state that can remain blue through a sell event or gold through a countertrend buy.",
    source: null,
  },
  {
    id: "dots-candidate",
    label: "Dots Indicator family",
    status: "candidate",
    parameters: "three simultaneous RSI horizons; Anna settings unknown",
    note: "Stackable multi-horizon RSI extremes explain the countertrend dots and strength tiers. Stock settings miss known Anna dates, so Anna’s markers are not treated as an unmodified copy.",
    confidence: "Medium-high family strength · low exact-rule strength",
    falsifier:
      "Freeze fitted settings, then require strong precision and recall on unseen closed bars; failure rejects a pure multi-RSI explanation.",
    source:
      "https://help.trendspider.com/kb/indicators/using-dots-indicator-by-intromoto",
  },
  {
    id: "seven-vote",
    label: "Transparent seven-feature benchmark",
    status: "reconstructed",
    parameters: "StochRSI, Aroon, DI, OBV, squeeze momentum, EMA8/21, WaveTrend",
    note: "Votes are equal and visible bar by bar. This roster reflects recurring public chart components plus the Phase 2 event evidence. It is a falsifiable benchmark—not Anna’s undisclosed 7/7 roster.",
    source: null,
  },
  {
    id: "ribbon-gap-vote",
    label: "Contrarian 7/7 explanation",
    status: "candidate",
    parameters: "seven adjacent spreads among eight ribbon strands",
    note: "An eight-line ribbon mechanically creates seven pairwise gaps, so 7/7 could conceivably describe ordered/curving ribbon relationships rather than seven separate indicators. Anna’s 6/6 epochs and broader indicator language are adverse evidence.",
    confidence: "Low hypothesis strength",
    falsifier:
      "Compare every preserved 7/7 and 6/6 caption with ribbon ordering, slope and adjacent-gap direction; frequent disagreement rejects the idea.",
    source: "https://help.trendspider.com/kb/indicators/moving-average-ribbon",
  },
  {
    id: "vault-model",
    label: "Anna’s six/seven-input vault model",
    status: "unknown",
    parameters: null,
    note: "Anna publishes aggregate health counts but says the indicators used for her analysis are locked away. Membership, weights, gates and override rules remain latent.",
    source: null,
  },
  {
    id: "model-epochs",
    label: "Versioned signal epochs",
    status: "confirmed",
    parameters: "six evidence profiles: Apr 11, Apr 16, Apr 27, May 22 and Jul 26 boundaries",
    note: "Anna explicitly disclosed changes around Apr 11, Apr 16, Apr 27 and Jul 26; May 22 is the first observed seven-panel/20-2-2-10 template, not a proven source-code release date. The profile is selected from the run’s latest completed bar and applied to the full run rather than stitched bar by bar. Runs before the recovered evidence window are labeled backcasts, not Anna history.",
    source: "https://x.com/iamsohot2020/status/2042849417179349130",
  },
  {
    id: "manual-gate",
    label: "Discretionary validation layer",
    status: "confirmed",
    parameters: "green DCB stars manually validated; later calls can precede system markers",
    note: "Anna says JavaScript could not encode all of her invalidation logic and that some green stars had to be marked by hand. A purely automatic clone is therefore structurally incomplete.",
    source: "https://x.com/iamsohot2020/status/2048819297410040107",
  },
  {
    id: "timeframe-policy",
    label: "Goal-dependent timeframe policy",
    status: "confirmed",
    parameters: "daily = longer horizon; 4h = swing; default daily when monitoring is limited",
    note: "Anna explicitly assigns daily and 4-hour charts to different user horizons, while repeated daily-plus-10-minute agreement is treated as unusually strong confirmation. There is no universal single-timeframe override.",
    source: "https://x.com/iamsohot2020/status/2050346996322681051",
  },
  {
    id: "move-magnitude",
    label: "Move magnitude",
    status: "unknown",
    parameters: null,
    note: "No calibrated Anna magnitude formula has been recovered. The headline reports size only when expansion is mechanically hinted, and otherwise says it is not specified.",
    source: null,
  },
  {
    id: "primary-markers",
    label: "Primary diamonds",
    status: "reconstructed",
    parameters: "red = fast ATR sell; magenta = EMA8/21 sell transition; cyan = earlier buy candidate; green = later/stronger buy candidate; no black-square generator",
    note: "Placement and color semantics come from Anna’s legend. Sell-side red and magenta timing now follows the exact Phase 2 hypotheses. Buy-side formulas remain experiments because exact buy-marker dates have not yet been reconstructed; the cyan-then-green ordering follows Anna’s strongest public timing description rather than a false sell-side symmetry. Black squares remain semantically observed but are withheld because no defensible formula has been recovered.",
    source: null,
  },
  {
    id: "tensor-cycle-context",
    label: "Trading Candles-style cycle context",
    status: "reconstructed",
    parameters: "DiNapoli EMA MACD α=.213/.108/.199; stochastic 8/3/3",
    note: "A separate completed-bar context lane. Bull/bear cycle shifts and momentum agreement are displayed and recorded, but never create, suppress or rename a primary Tensor marker.",
    confidence: "Deterministic formula; incremental predictive value remains under validation",
    falsifier: "Remove the lane if walk-forward ablation shows no stable lift beyond Tensor's existing momentum family.",
    source: null,
  },
  {
    id: "tensor-pattern-context",
    label: "Focused reversal pattern context",
    status: "reconstructed",
    parameters: "Engulfing, Morning/Evening Star, Three Outside; 10-bar causal edge",
    note: "Pattern markers and prior completed-event expectancy are attached as context. Current-event forward returns are never used, and minimum samples remain visible rather than silently promoted.",
    confidence: "Deterministic OHLC taxonomy; historical edge remains shadow evidence until validated",
    falsifier: "Require prospective lift over the existing Tensor context after controlling for support, momentum and participation.",
    source: null,
  },
  {
    id: "current-call-episode",
    label: "Persistent call episode",
    status: "reconstructed",
    parameters: "primary direction persists until an opposite primary marker",
    note: "Anna repeatedly describes symbols as still under a prior buy or sell when no opposite primary marker has appeared. The Lab therefore ages the episode without inventing a six-bar expiry. An explicit invalidation rule remains unknown.",
    source: null,
  },
  {
    id: "weak-watch",
    label: "B / W1 surrogate",
    status: "reconstructed",
    parameters: "B: Stoch up-turn, K≤40, bullish share≥57%; W1: K≤30, bullish share 50–72%",
    note: "The glyph meanings are observed. These thresholds belong only to this build and are exposed so they can be falsified; W1 never counts as a buy call.",
    source: null,
  },
  {
    id: "dcb",
    label: "Dead-cat-bounce stars",
    status: "reconstructed",
    parameters: "bearish regime + Stoch K≤15 + ≥18% drawdown + bullish close-location reversal; explicit exit/expiry by bar 4",
    note: "The 1–4-bar lifecycle is explicit in Anna’s legend. The oversold, drawdown, reversal and exhaustion thresholds are this build’s disclosed countertrend surrogate—not Anna’s recovered formula. Expiry is tracked separately from a red exit.",
    source: null,
  },
  {
    id: "data-feed",
    label: "Market-data and session bridge",
    status: "reconstructed",
    parameters: "Yahoo chart bars; 5m uses completed premarket and regular-session bars with after-hours excluded; higher frames disable extended hours; 2h/4h group from each exchange calendar day",
    note: "This makes the Lab functional but not feed-identical. Disabling extended hours does not imply that every permitted futures or crypto symbol follows an equity regular session. Anna’s TrendSpider screenshots primarily use ICE-backed data, so volume, RVOL, OBV and any signal that consumes them can differ. Overnight futures can also split differently because multi-hour bars are anchored to exchange calendar days rather than a verified TrendSpider session template.",
    source: "https://trendspider.com/market-data-disclaimers/",
  },
  {
    id: "live-context",
    label: "Live-context bridge",
    status: "reconstructed",
    parameters:
      "Yahoo one-minute chart polling with extended hours enabled; the 5m signal tape uses completed premarket and regular-session bars and excludes after-hours",
    note: "The live-context strip is deliberately separate from Anna calculations. Yahoo says many exchange quotes stream in real time, but the chart endpoint used here has no published developer latency guarantee. The interface therefore displays the provider timestamp and age instead of claiming exchange-direct certainty.",
    source:
      "https://help.yahoo.com/kb/finance-for-web/check-real-time-data-yahoo-finance-web-sln2321.html",
  },
  {
    id: "white-stars",
    label: "White stars",
    status: "unknown",
    parameters: null,
    note: "They recur, but Anna’s supplied legend does not define them.",
    source: null,
  },
]);

const INTERVALS = Object.freeze({
  "2m": {
    label: "2-minute",
    providerInterval: "2m",
    range: "1mo",
    aggregate: 1,
    displayBars: TENSOR_CHART_DISPLAY_BARS,
  },
  "5m": {
    label: "5-minute",
    providerInterval: "5m",
    range: "60d",
    aggregate: 1,
    displayBars: TENSOR_CHART_DISPLAY_BARS,
  },
  "10m": {
    label: "10-minute",
    providerInterval: "5m",
    range: "60d",
    aggregate: 2,
    displayBars: TENSOR_CHART_DISPLAY_BARS,
  },
  "1h": {
    label: "1-hour",
    providerInterval: "60m",
    range: "1y",
    aggregate: 1,
    displayBars: TENSOR_CHART_DISPLAY_BARS,
  },
  "2h": {
    label: "2-hour",
    providerInterval: "60m",
    range: "1y",
    aggregate: 2,
    displayBars: TENSOR_CHART_DISPLAY_BARS,
  },
  "4h": {
    label: "4-hour",
    providerInterval: "60m",
    range: "1y",
    aggregate: 4,
    displayBars: TENSOR_CHART_DISPLAY_BARS,
  },
  "1d": {
    label: "Daily",
    providerInterval: "1d",
    range: "2y",
    aggregate: 1,
    displayBars: TENSOR_CHART_DISPLAY_BARS,
  },
  "1wk": {
    label: "Weekly",
    providerInterval: "1wk",
    range: "10y",
    aggregate: 1,
    displayBars: TENSOR_CHART_DISPLAY_BARS,
  },
});

export function normalizeReplicaRequest(symbolValue, intervalValue) {
  const symbol = String(symbolValue ?? "")
    .trim()
    .toUpperCase();
  const interval = String(intervalValue ?? "1d").trim().toLowerCase();
  if (
    !symbol ||
    symbol.length > 24 ||
    !/^[A-Z0-9^][A-Z0-9.^=/-]{0,23}$/.test(symbol)
  ) {
    return { ok: false, error: "Add a valid ticker or market symbol (up to 24 characters)." };
  }
  const configuration = INTERVALS[interval];
  if (!configuration) {
    return {
      ok: false,
      error: "Choose 2m, 5m, 10m, 1h, 2h, 4h, 1d or 1wk.",
    };
  }
  return {
    ok: true,
    symbol,
    interval,
    configuration,
  };
}

export function parseYahooReplicaHistory(
  payload,
  expectedSymbol,
  interval = "1d",
  nowSeconds = Math.floor(Date.now() / 1_000)
) {
  const chart = asRecord(payload)?.chart;
  const result = Array.isArray(asRecord(chart)?.result)
    ? asRecord(chart).result[0]
    : null;
  const row = asRecord(result);
  const meta = asRecord(row?.meta);
  if (!row || !meta) return null;
  const symbol = normalizeSymbol(meta.symbol);
  const expected = normalizeSymbol(expectedSymbol);
  if (!symbol || (expected && symbol !== expected)) return null;

  const timestamps = Array.isArray(row.timestamp) ? row.timestamp : [];
  const indicators = asRecord(row.indicators);
  const quotes = Array.isArray(indicators?.quote) ? indicators.quote : [];
  const quote = asRecord(quotes[0]);
  if (!quote) return null;
  const opens = Array.isArray(quote.open) ? quote.open : [];
  const highs = Array.isArray(quote.high) ? quote.high : [];
  const lows = Array.isArray(quote.low) ? quote.low : [];
  const closes = Array.isArray(quote.close) ? quote.close : [];
  const volumes = Array.isArray(quote.volume) ? quote.volume : [];

  const barsByTimestamp = new Map();
  for (let index = 0; index < timestamps.length; index += 1) {
    const timestamp = positiveInteger(timestamps[index]);
    const open = finitePositive(opens[index]);
    const high = finitePositive(highs[index]);
    const low = finitePositive(lows[index]);
    const close = finitePositive(closes[index]);
    if (
      timestamp === null ||
      open === null ||
      high === null ||
      low === null ||
      close === null ||
      high < Math.max(open, close) ||
      low > Math.min(open, close)
    ) {
      continue;
    }
    barsByTimestamp.set(timestamp, {
      timestamp,
      open,
      high,
      low,
      close,
      volume: finiteNonNegative(volumes[index]) ?? 0,
    });
  }

  const rawBars = [...barsByTimestamp.values()].sort(
    (left, right) => left.timestamp - right.timestamp
  );
  const configuration = INTERVALS[interval] ?? INTERVALS["1d"];
  const timezone =
    typeof meta.exchangeTimezoneName === "string"
      ? meta.exchangeTimezoneName
      : "America/New_York";
  const sessionTemplate = sessionTemplateForMetadata(meta, timezone, symbol);
  const bars =
    configuration.aggregate > 1
      ? aggregateBarsBySession(
          rawBars,
          configuration.aggregate,
          timezone,
          providerIntervalSeconds(configuration.providerInterval),
          sessionTemplate,
        )
      : rawBars;
  if (!bars.length) return null;
  const latestBarOpen = inferLatestBarOpen(
    meta,
    interval,
    bars[bars.length - 1].timestamp,
    nowSeconds,
    timezone
  );

  return {
    symbol,
    currency:
      typeof meta.currency === "string" && meta.currency
        ? meta.currency
        : "USD",
    exchange:
      typeof meta.fullExchangeName === "string"
        ? meta.fullExchangeName
        : typeof meta.exchangeName === "string"
          ? meta.exchangeName
          : null,
    instrumentType:
      typeof meta.instrumentType === "string" ? meta.instrumentType : null,
    timezone,
    interval,
    intervalLabel: configuration.label,
    displayBars: configuration.displayBars,
    latestBarOpen,
    bars,
  };
}

export function parseYahooLiveSnapshot(
  payload,
  expectedSymbol,
  nowSeconds = Math.floor(Date.now() / 1_000)
) {
  const chart = asRecord(payload)?.chart;
  const result = Array.isArray(asRecord(chart)?.result)
    ? asRecord(chart).result[0]
    : null;
  const row = asRecord(result);
  const meta = asRecord(row?.meta);
  if (!row || !meta) return null;
  const symbol = normalizeSymbol(meta.symbol);
  const expected = normalizeSymbol(expectedSymbol);
  if (!symbol || (expected && symbol !== expected)) return null;

  const timestamps = Array.isArray(row.timestamp) ? row.timestamp : [];
  const indicators = asRecord(row.indicators);
  const quotes = Array.isArray(indicators?.quote) ? indicators.quote : [];
  const quote = asRecord(quotes[0]);
  const closes = Array.isArray(quote?.close) ? quote.close : [];
  const phase = liveSession(meta, nowSeconds);
  const timezone =
    typeof meta.exchangeTimezoneName === "string"
      ? meta.exchangeTimezoneName
      : "America/New_York";
  const sessionTemplate = sessionTemplateForMetadata(
    meta,
    timezone,
    expectedSymbol,
  );
  const periodForTimestamp = (timestamp) => {
    const currentTradingPeriod = asRecord(meta.currentTradingPeriod);
    for (const [session, key] of [
      ["premarket", "pre"],
      ["regular", "regular"],
      ["after-hours", "post"],
    ]) {
      const period = asRecord(currentTradingPeriod?.[key]);
      const start = positiveInteger(period?.start);
      const end = positiveInteger(period?.end);
      if (
        start !== null &&
        end !== null &&
        timestamp >= start &&
        timestamp < end
      ) return session;
    }
    try {
      const parts = tensorDateFormatter("en-US", {
        timeZone: timezone,
        hour: "2-digit",
        minute: "2-digit",
        hourCycle: "h23",
      }).formatToParts(new Date(timestamp * 1_000));
      const hour = Number(parts.find((part) => part.type === "hour")?.value);
      const minute = Number(parts.find((part) => part.type === "minute")?.value);
      const clock = hour * 60 + minute;
      if (Number.isFinite(clock)) {
        if (sessionTemplate.kind === "continuous") return "regular";
        if (sessionTemplate.kind === "foreign-security") {
          return clock >= sessionTemplate.regularOpenMinutes &&
              clock < sessionTemplate.regularCloseMinutes
            ? "regular"
            : null;
        }
        if (clock >= 4 * 60 && clock < 9 * 60 + 30) return "premarket";
        if (clock >= 9 * 60 + 30 && clock < 16 * 60) return "regular";
        if (clock >= 16 * 60 && clock < 20 * 60) return "after-hours";
      }
    } catch {
      // An unclassifiable print is not relabeled into the active session.
    }
    return null;
  };
  const candidates = [];
  for (let index = 0; index < timestamps.length; index += 1) {
    const timestamp = positiveInteger(timestamps[index]);
    const price = finitePositive(closes[index]);
    if (
      timestamp !== null &&
      price !== null &&
      timestamp <= nowSeconds + 300
    ) {
      candidates.push({
        price,
        timestamp,
        session: periodForTimestamp(timestamp),
      });
    }
  }
  for (const [priceKey, timeKey, session] of [
    ["regularMarketPrice", "regularMarketTime", "regular"],
    ["postMarketPrice", "postMarketTime", "after-hours"],
    ["preMarketPrice", "preMarketTime", "premarket"],
  ]) {
    const price = finitePositive(meta[priceKey]);
    const timestamp = positiveInteger(meta[timeKey]);
    if (
      price !== null &&
      timestamp !== null &&
      timestamp <= nowSeconds + 300
    ) {
      candidates.push({ price, timestamp, session });
    }
  }
  const eligible = phase === "closed"
    ? candidates
    : candidates.filter(candidate => candidate.session === phase);
  const latest = eligible.sort(
    (left, right) => right.timestamp - left.timestamp
  )[0];
  if (!latest) return null;
  const { price, timestamp } = latest;

  const previousClose =
    finitePositive(meta.chartPreviousClose) ??
    finitePositive(meta.regularMarketPreviousClose) ??
    finitePositive(meta.previousClose);
  const session = phase;
  const change =
    previousClose === null ? null : price - previousClose;
  const changePct =
    previousClose === null || previousClose === 0
      ? null
      : change / previousClose;
  const ageSeconds = Math.max(0, nowSeconds - timestamp);
  return {
    version: ANNA_LIVE_VERSION,
    generatedAt: new Date(nowSeconds * 1_000).toISOString(),
    symbol,
    currency:
      typeof meta.currency === "string" && meta.currency
        ? meta.currency
        : "USD",
    exchange:
      typeof meta.fullExchangeName === "string"
        ? meta.fullExchangeName
        : typeof meta.exchangeName === "string"
          ? meta.exchangeName
          : null,
    timezone:
      typeof meta.exchangeTimezoneName === "string"
        ? meta.exchangeTimezoneName
        : "America/New_York",
    price,
    previousClose,
    change: nullableNumber(change),
    changePct: nullableNumber(changePct),
    timestamp: new Date(timestamp * 1_000).toISOString(),
    ageSeconds,
    session,
    finality: session === "closed" ? "latest" : "developing",
    source: "Yahoo Finance one-minute chart",
    feedMode: "15-second polling",
    latencyStatus: "provider timestamp shown; venue-dependent",
  };
}

export function buildAnnaReplica(history, { latestOnly = false } = {}) {
  const sourceBars = Array.isArray(history?.bars) ? history.bars : [];
  // The replica only reads source bars while building derived arrays; it does
  // not mutate them. Reusing the validated bar objects removes one full
  // 1,200-row clone from every signal-only symbol evaluation.
  const bars = sourceBars.filter(validBar);
  const minimumBars = history?.interval === "1wk" ? 4 : 35;
  if (bars.length < minimumBars) return null;

  const open = bars.map((bar) => bar.open);
  const close = bars.map((bar) => bar.close);
  const high = bars.map((bar) => bar.high);
  const low = bars.map((bar) => bar.low);
  const volume = bars.map((bar) => bar.volume);
  // Epoch-specific parameters are point-in-time properties. Selecting one
  // profile from the newest bar and backfilling it across history rewrites
  // earlier signals whenever a later bar crosses an epoch boundary.
  const epochProfiles = bars.map((bar) =>
    annaEpochForTimestamp(
      bar.timestamp,
      history.timezone ?? "America/New_York"
    )
  );
  const bbMid14 = sma(close, 14);
  const bbMid20 = sma(close, 20);
  const bbStd14 = rollingStd(close, 14);
  const bbStd20 = rollingStd(close, 20);
  const bbUpper14 = combine(
    bbMid14,
    bbStd14,
    (mid, deviation) => mid + 2 * deviation
  );
  const bbUpper20 = combine(
    bbMid20,
    bbStd20,
    (mid, deviation) => mid + 2 * deviation
  );
  const bbLower14 = combine(
    bbMid14,
    bbStd14,
    (mid, deviation) => mid - 2 * deviation
  );
  const bbLower20 = combine(
    bbMid20,
    bbStd20,
    (mid, deviation) => mid - 2 * deviation
  );
  const kcMid14 = ema(close, 14);
  const kcMid20 = ema(close, 20);
  const atr14 = wilderAtr(high, low, close, 14);
  const atr20 = wilderAtr(high, low, close, 20);
  const kcUpper14 = combine(
    kcMid14,
    atr14,
    (mid, atrValue) => mid + 2 * atrValue
  );
  const kcUpper20 = combine(
    kcMid20,
    atr20,
    (mid, atrValue) => mid + 2 * atrValue
  );
  const kcLower14 = combine(
    kcMid14,
    atr14,
    (mid, atrValue) => mid - 2 * atrValue
  );
  const kcLower20 = combine(
    kcMid20,
    atr20,
    (mid, atrValue) => mid - 2 * atrValue
  );
  const squeezeMomentum14 = squeezeMomentumSeries(
    high,
    low,
    close,
    bbMid14,
    14,
    9
  );
  const squeezeMomentum20 = squeezeMomentumSeries(
    high,
    low,
    close,
    bbMid20,
    20,
    10
  );
  const bbMid = selectEpochSeries(epochProfiles, bbMid14, bbMid20);
  const bbUpper = selectEpochSeries(epochProfiles, bbUpper14, bbUpper20);
  const bbLower = selectEpochSeries(epochProfiles, bbLower14, bbLower20);
  const kcUpper = selectEpochSeries(epochProfiles, kcUpper14, kcUpper20);
  const kcLower = selectEpochSeries(epochProfiles, kcLower14, kcLower20);
  const squeezeMomentum = selectEpochSeries(
    epochProfiles,
    squeezeMomentum14,
    squeezeMomentum20
  );
  const ema200 = ema(close, 200);
  const ema8 = ema(close, 8);
  const ema13 = ema(close, 13);
  const ema21 = ema(close, 21);
  const ema34 = ema(close, 34);
  const ema48 = ema(close, 48);
  const emaRibbon = [10, 20, 30, 40, 50, 60, 70, 80].map((length) =>
    ema(close, length)
  );
  const avgVolume = priorSma(volume, 20);
  const obv = onBalanceVolume(close, volume);
  const mcdx = redDragonMcdx(high, low, close, volume, 100, 5);
  const stoch = stochasticRsi(close, 14, 14, 3, 3);
  const dotRsiFast = rsiSeries(close, 11);
  const dotRsiMedium = rsiSeries(close, 12);
  const dotRsiSlow = rsiSeries(close, 22);
  const aroon = aroonSeries(high, low, 14);
  const directional = directionalMovement(high, low, close, 14);
  const macd = macdSeries(close, 12, 26, 9);
  const waveTrend = waveTrendSeries(high, low, close, 10, 21, 4);
  const openCipherWave = waveTrendSeries(high, low, close, 9, 12, 3);
  const openCipherEma5 = ema(close, 5);
  const openCipherEma11 = ema(close, 11);
  const openCipherEma15 = ema(close, 15);
  const openCipherEma18 = ema(close, 18);
  const openCipherEma21 = ema(close, 21);
  const openCipherEma25 = ema(close, 25);
  const openCipherEma29 = ema(close, 29);
  const openCipherEma33 = ema(close, 33);
  const openCipherPressure = smaNullable(
    close.map((value, index) => {
      const range = high[index] - low[index];
      return range === 0
        ? null
        : (175 * (value - open[index])) / range;
    }),
    60
  );
  const utBot = utBotSeries(high, low, close, 10, 1);
  // Context is calculated once from the full verified tape, then attached to
  // bars. It is deliberately not used by inferPrimaryMarkers or any native
  // signal eligibility rule.
  const tensorContextSeries = buildTensorContextSeries(bars, { latestOnly });
  const rawSlowStates = bars.map((bar, index) => {
    if (
      !finite(ema8[index]) ||
      !finite(ema13[index]) ||
      !finite(ema21[index]) ||
      !finite(ema34[index]) ||
      !finite(ema48[index])
    ) {
      return null;
    }
    if (
      ema8[index] > ema21[index] &&
      ema21[index] > ema34[index] &&
      ema13[index] > ema48[index] &&
      bar.close > ema21[index]
    ) {
      return "bullish";
    }
    if (
      ema8[index] < ema21[index] &&
      ema21[index] < ema34[index] &&
      ema13[index] < ema48[index] &&
      bar.close < ema21[index]
    ) {
      return "bearish";
    }
    return "mixed";
  });

  let priorCandleRegime = null;
  const enriched = bars.map((bar, index) => {
    const currentRibbon = new Array(emaRibbon.length);
    let completeRibbon = true;
    let completePriorRibbon = true;
    let bullishRibbonOrder = true;
    let bearishRibbonOrder = true;
    let ribbonMinimum = Infinity;
    let ribbonMaximum = -Infinity;
    let ribbonSlopeSum = 0;
    for (let ribbonIndex = 0; ribbonIndex < emaRibbon.length; ribbonIndex += 1) {
      const value = emaRibbon[ribbonIndex][index];
      const priorValue = index > 0 ? emaRibbon[ribbonIndex][index - 1] : undefined;
      currentRibbon[ribbonIndex] = nullableNumber(value);
      if (!finite(value)) completeRibbon = false;
      else {
        if (value < ribbonMinimum) ribbonMinimum = value;
        if (value > ribbonMaximum) ribbonMaximum = value;
      }
      if (ribbonIndex > 0) {
        const previousValue = emaRibbon[ribbonIndex - 1][index];
        if (!(previousValue > value)) bullishRibbonOrder = false;
        if (!(previousValue < value)) bearishRibbonOrder = false;
      }
      if (index > 0 && !finite(priorValue)) completePriorRibbon = false;
      ribbonSlopeSum += (value - priorValue) / bar.close;
    }
    const ribbonOrder = completeRibbon
      ? bullishRibbonOrder
        ? "bullish"
        : bearishRibbonOrder
          ? "bearish"
          : "mixed"
      : null;
    const ribbonWidth = completeRibbon
      ? (ribbonMaximum - ribbonMinimum) / bar.close
      : null;
    // The old empty prior ribbon at index zero passed Array.every and its
    // reduce produced NaN; preserve nullableNumber's resulting null output.
    const ribbonSlope = completeRibbon && completePriorRibbon
      ? index === 0 ? Number.NaN : ribbonSlopeSum / emaRibbon.length
      : null;
    const squeezeOn =
      finite(bbUpper[index]) &&
      finite(bbLower[index]) &&
      finite(kcUpper[index]) &&
      finite(kcLower[index])
        ? bbUpper[index] < kcUpper[index] && bbLower[index] > kcLower[index]
        : null;
    const rvol =
      finite(avgVolume[index]) && avgVolume[index] > 0
        ? bar.volume / avgVolume[index]
        : null;
    const obvSlope = slope(obv, index, 5);
    const momentum = squeezeMomentum[index];
    const momentumSlope =
      index > 0 && finite(momentum) && finite(squeezeMomentum[index - 1])
        ? momentum - squeezeMomentum[index - 1]
        : null;
    const macdHistogram = macd.histogram[index];
    const pivotRibbonOrder =
      finite(ema8[index]) && finite(ema21[index]) && finite(ema34[index])
        ? ema8[index] > ema21[index] && ema21[index] > ema34[index]
          ? "bullish_ordered"
          : ema8[index] < ema21[index] && ema21[index] < ema34[index]
            ? "bearish_ordered"
            : "mixed"
        : null;
    const slowBullish =
      rawSlowStates[index] === "bullish" &&
      rawSlowStates[index - 1] === "bullish";
    const slowBearish =
      rawSlowStates[index] === "bearish" &&
      rawSlowStates[index - 1] === "bearish";
    const candleRegime = slowBullish
      ? "bullish"
      : slowBearish
        ? "bearish"
        : priorCandleRegime ??
          (finite(ema21[index])
            ? bar.close >= ema21[index]
              ? "bullish"
              : "bearish"
            : bar.close >= bar.open
              ? "bullish"
              : "bearish");
    priorCandleRegime = candleRegime;

    const ema8BullCross = crossesAbove(ema8, ema21, index);
    const ema8BearCross = crossesBelow(ema8, ema21, index);
    const waveBullCross = waveTrend.events[index] === "bull_cross";
    const waveBearCross = waveTrend.events[index] === "bear_cross";
    const openCipherRedDiamond =
      openCipherWave.events[index] === "bear_cross";
    const openCipherGreenDot = crossesAbove(
      openCipherEma11,
      openCipherEma33,
      index
    );
    const openCipherRedX = crossesBelow(
      openCipherEma5,
      openCipherEma11,
      index
    );
    const openCipherBlueTriangle =
      crossesAbove(openCipherEma5, openCipherEma25, index) &&
      finite(openCipherEma29[index]) &&
      finite(openCipherEma33[index]) &&
      openCipherEma29[index] < openCipherEma33[index];
    const openCipherYellowX =
      openCipherRedDiamond &&
      finite(openCipherWave.wt2[index]) &&
      openCipherWave.wt2[index] < -40 &&
      finite(openCipherPressure[index]) &&
      openCipherPressure[index] < 0;
    const openCipherBloodDiamond =
      openCipherRedDiamond && openCipherRedX;
    const openCipherEvents = [
      ...(openCipherGreenDot ? ["green-dot"] : []),
      ...(openCipherBlueTriangle ? ["blue-triangle"] : []),
      ...(openCipherRedX ? ["red-x"] : []),
      ...(openCipherRedDiamond ? ["red-diamond"] : []),
      ...(openCipherYellowX ? ["yellow-x"] : []),
      ...(openCipherBloodDiamond ? ["blood-diamond"] : []),
    ];
    const openCipherBullishEvent =
      openCipherGreenDot || openCipherBlueTriangle;
    const openCipherBearishEvent =
      openCipherRedX || openCipherRedDiamond;
    const openCipherEventDirection =
      openCipherBullishEvent && openCipherBearishEvent
        ? "mixed"
        : openCipherBullishEvent
          ? "bullish"
          : openCipherBearishEvent
            ? "bearish"
            : "none";
    const openCipherState =
      finite(openCipherWave.wt1[index]) &&
      finite(openCipherWave.wt2[index]) &&
      finite(openCipherEma5[index]) &&
      finite(openCipherEma11[index])
        ? openCipherWave.wt1[index] > openCipherWave.wt2[index] &&
          openCipherEma5[index] > openCipherEma11[index]
          ? "bullish"
          : openCipherWave.wt1[index] < openCipherWave.wt2[index] &&
              openCipherEma5[index] < openCipherEma11[index]
            ? "bearish"
            : "mixed"
        : "warming";
    const stratType =
      index > 0 ? classifyStratBar(bar, bars[index - 1]) : null;
    const utBuyFlip = utBot.events[index] === "buy_flip";
    const utSellFlip = utBot.events[index] === "sell_flip";
    const recentUtBuy = hasPriorEvent(
      utBot.events,
      index,
      "buy_flip",
      1,
      6
    );
    const recentUtSell = hasPriorEvent(
      utBot.events,
      index,
      "sell_flip",
      1,
      6
    );
    const emaBullConfirmed = ema8BullCross && recentUtBuy;
    const emaBearConfirmed = ema8BearCross && recentUtSell;

    const voteStates = [
      stateVote(
        "stoch",
        "Stoch RSI",
        directionalVote(
        stoch.k[index],
        stoch.d[index],
        index > 0 ? stoch.k[index - 1] : null
        ),
        formatPair(stoch.k[index], stoch.d[index], "K", "D")
      ),
      stateVote(
        "aroon",
        "Aroon",
        comparisonVote(aroon.up[index], aroon.down[index]),
        formatPair(aroon.up[index], aroon.down[index], "Up", "Down")
      ),
      stateVote(
        "di",
        "Directional movement",
        comparisonVote(directional.plusDi[index], directional.minusDi[index]),
        formatPair(
          directional.plusDi[index],
          directional.minusDi[index],
          "+DI",
          "−DI"
        )
      ),
      stateVote(
        "obv",
        "OBV pressure",
        signedVote(obvSlope),
        finite(obvSlope) ? `5-bar slope ${formatSigned(obvSlope)}` : "warming"
      ),
      stateVote(
        "squeeze",
        "Squeeze momentum",
        signedVote(
          finite(momentumSlope) && momentumSlope !== 0 ? momentumSlope : momentum
        ),
        finite(momentum)
          ? `${momentum >= 0 ? "positive" : "negative"} · ${
              finite(momentumSlope) && momentumSlope > 0
                ? "rising"
                : finite(momentumSlope) && momentumSlope < 0
                  ? "falling"
                  : "flat"
            }`
          : "warming"
      ),
      stateVote(
        "pivot",
        "EMA 8/21",
        comparisonVote(ema8[index], ema21[index]),
        pivotRibbonOrder?.replace("_", " ") ?? "warming"
      ),
      stateVote(
        "wave",
        "WaveTrend",
        comparisonVote(waveTrend.wt1[index], waveTrend.wt2[index]),
        formatPair(
          waveTrend.wt1[index],
          waveTrend.wt2[index],
          "WT1",
          "WT2"
        )
      ),
    ];
    const votes = voteStates
      .map((state) => state.vote)
      .filter((vote) => vote !== null);
    const bullishVotes = votes.filter((vote) => vote === 1).length;
    const bearishVotes = votes.filter((vote) => vote === -1).length;
    const totalVotes = votes.length;
    const bullishShare = totalVotes ? bullishVotes / totalVotes : 0;
    const stochTurnUp =
      index > 0 &&
      finite(stoch.k[index]) &&
      finite(stoch.d[index]) &&
      finite(stoch.k[index - 1]) &&
      finite(stoch.d[index - 1]) &&
      stoch.k[index] > stoch.d[index] &&
      stoch.k[index - 1] <= stoch.d[index - 1];
    const primaryMarkers = inferPrimaryMarkers({
      bullishVotes,
      bearishVotes,
      totalVotes,
      utBuyFlip,
      utSellFlip,
      ema8BullCross: emaBullConfirmed,
      ema8BearCross: emaBearConfirmed,
    });
    const primaryMarker = primaryMarkers[0] ?? null;
    const warningMarker =
      waveBullCross && (slowBearish || pivotRibbonOrder === "bearish_ordered")
        ? "fast-bull-slow-bear"
        : null;
    const utState =
      utBot.regimes[index] === "bullish" ||
      utBot.regimes[index] === "bearish"
        ? utBot.regimes[index]
        : null;
    const waveState =
      finite(waveTrend.wt1[index]) && finite(waveTrend.wt2[index])
        ? waveTrend.wt1[index] > waveTrend.wt2[index]
          ? "bullish"
          : waveTrend.wt1[index] < waveTrend.wt2[index]
            ? "bearish"
            : null
        : null;
    const fastState =
      utState && waveState && utState !== waveState
        ? "mixed"
        : utState ?? waveState ?? "mixed";

    const fullBar = {
      ...bar,
      barFinality:
        index === bars.length - 1 && history.latestBarOpen
          ? "open"
          : "closed",
      epochId: epochProfiles[index].id,
      epochBasis: epochProfiles[index].basis,
      squeezeLength: epochProfiles[index].squeezeLength,
      squeezeMomentumLength: epochProfiles[index].squeezeMomentumLength,
      bbUpper: nullableNumber(bbUpper[index]),
      bbMid: nullableNumber(bbMid[index]),
      bbLower: nullableNumber(bbLower[index]),
      kcUpper: nullableNumber(kcUpper[index]),
      kcLower: nullableNumber(kcLower[index]),
      ema200: nullableNumber(ema200[index]),
      ema8: nullableNumber(ema8[index]),
      ema13: nullableNumber(ema13[index]),
      ema21: nullableNumber(ema21[index]),
      ema34: nullableNumber(ema34[index]),
      ema48: nullableNumber(ema48[index]),
      emaRibbon: currentRibbon,
      ribbonOrder,
      pivotRibbonOrder,
      ribbonWidth: nullableNumber(ribbonWidth),
      ribbonSlope: nullableNumber(ribbonSlope),
      avgVolume: nullableNumber(avgVolume[index]),
      rvol: nullableNumber(rvol),
      obv: nullableNumber(obv[index]),
      obvDivergence: inferObvDivergence(close, obv, index, 10),
      mcdxProfit: nullableNumber(mcdx.profit[index]),
      mcdxLocked: nullableNumber(mcdx.locked[index]),
      mcdxRock: nullableNumber(mcdx.rock[index]),
      mcdxVolumeRatio: nullableNumber(mcdx.volumeRatio[index]),
      stochK: nullableNumber(stoch.k[index]),
      stochD: nullableNumber(stoch.d[index]),
      dotRsiFast: nullableNumber(dotRsiFast[index]),
      dotRsiMedium: nullableNumber(dotRsiMedium[index]),
      dotRsiSlow: nullableNumber(dotRsiSlow[index]),
      dotBuyTiers: [
        finite(dotRsiFast[index]) && dotRsiFast[index] <= 20,
        finite(dotRsiMedium[index]) && dotRsiMedium[index] <= 16,
        finite(dotRsiSlow[index]) && dotRsiSlow[index] <= 22,
      ].filter(Boolean).length,
      dotSellTiers: [
        finite(dotRsiFast[index]) && dotRsiFast[index] >= 76,
        finite(dotRsiMedium[index]) && dotRsiMedium[index] >= 87,
        finite(dotRsiSlow[index]) && dotRsiSlow[index] >= 84,
      ].filter(Boolean).length,
      aroonUp: nullableNumber(aroon.up[index]),
      aroonDown: nullableNumber(aroon.down[index]),
      adx: nullableNumber(directional.adx[index]),
      plusDi: nullableNumber(directional.plusDi[index]),
      minusDi: nullableNumber(directional.minusDi[index]),
      squeezeOn,
      squeezeMomentum: nullableNumber(momentum),
      macdHistogram: nullableNumber(macdHistogram),
      waveTrendFast: nullableNumber(waveTrend.wt1[index]),
      waveTrendSlow: nullableNumber(waveTrend.wt2[index]),
      waveTrendSpread:
        finite(waveTrend.wt1[index]) && finite(waveTrend.wt2[index])
          ? waveTrend.wt1[index] - waveTrend.wt2[index]
          : null,
      waveTrendZone: waveTrend.zones[index],
      waveTrendEvent: waveTrend.events[index],
      openCipherWaveFast: nullableNumber(openCipherWave.wt1[index]),
      openCipherWaveSlow: nullableNumber(openCipherWave.wt2[index]),
      openCipherPressure: nullableNumber(openCipherPressure[index]),
      openCipherEma5: nullableNumber(openCipherEma5[index]),
      openCipherEma11: nullableNumber(openCipherEma11[index]),
      openCipherEma15: nullableNumber(openCipherEma15[index]),
      openCipherEma18: nullableNumber(openCipherEma18[index]),
      openCipherEma21: nullableNumber(openCipherEma21[index]),
      openCipherEma25: nullableNumber(openCipherEma25[index]),
      openCipherEma29: nullableNumber(openCipherEma29[index]),
      openCipherEma33: nullableNumber(openCipherEma33[index]),
      openCipherEvents,
      openCipherEventDirection,
      openCipherState,
      stratType,
      stratDirection:
        stratType === "2U"
          ? "bullish"
          : stratType === "2D"
            ? "bearish"
            : stratType === "1"
              ? "neutral"
              : stratType === "3"
                ? "two-sided"
                : null,
      utTrailingStop: nullableNumber(utBot.stop[index]),
      utRegime: utBot.regimes[index],
      utEvent: utBot.events[index],
      candleRegime,
      rawSlowState: rawSlowStates[index],
      slowState:
        rawSlowStates[index] === "bullish"
          ? "bullish"
          : rawSlowStates[index] === "bearish"
            ? "bearish"
            : "mixed",
      fastState,
      warningMarker,
      stateVotes: voteStates.map(({ vote, ...state }) => ({
        ...state,
        direction:
          vote === 1 ? "bullish" : vote === -1 ? "bearish" : "neutral",
      })),
      bullishVotes,
      bearishVotes,
      totalVotes,
      primaryMarker,
      primaryMarkers,
      provisionalPrimaryMarkers: [],
      markerEvidence: [
        ...(utBuyFlip || utSellFlip ? ["fast ATR reversal"] : []),
        ...(emaBullConfirmed || emaBearConfirmed
          ? ["EMA8/21 transition after fast reversal"]
          : []),
        ...(warningMarker ? ["fast/slow conflict"] : []),
        ...(waveBullCross || waveBearCross ? ["WaveTrend cross"] : []),
      ],
      eventEvidence: [
        ...primaryMarkers.map(eventEvidenceForPrimaryMarker),
        ...(warningMarker
          ? [
              {
                event: "gold-warning",
                direction: "watch",
                semanticStatus: "observed",
                formulaStatus: "provisional",
                basis:
                  "Reduced fast-bull/slow-bear proxy; one exact reconstructed warning",
              },
            ]
          : []),
      ],
      weakMarker:
        primaryMarker === null &&
        stochTurnUp &&
        bullishShare >= 0.57 &&
        (stoch.k[index] ?? 100) <= 40
          ? "B"
          : primaryMarker === null &&
              bullishShare >= 0.5 &&
              bullishShare < 0.72 &&
              (stoch.k[index] ?? 100) <= 30
            ? "W1"
            : null,
      dcbMarker: null,
      dcbActive: false,
      dcbAge: null,
      dcbState: "inactive",
      calendarAvwap: null,
      calendarAvwapAnchorAt: null,
      eventAvwap: null,
      eventAvwapAnchorAt: null,
      activeCall: null,
      callLifecycle: "inactive",
      callEpisode: null,
      repeatOrdinal: 0,
      lastPrimaryEventAge: null,
      tensorContext: tensorContextSeries[index] ?? null,
    };
    return latestOnly && index < bars.length - 1
      ? compactSignalHistoryBar(fullBar)
      : fullBar;
  });

  const openBar = enriched.at(-1);
  if (openBar?.barFinality === "open") {
    openBar.provisionalPrimaryMarkers = history.interval === "1wk"
      ? openBar.primaryMarkers.filter(
          (marker) => marker === "buy-cyan" || marker === "buy-green"
        )
      : [];
    openBar.primaryMarker = null;
    openBar.primaryMarkers = [];
    openBar.warningMarker = null;
    openBar.weakMarker = null;
    openBar.utEvent = null;
    openBar.waveTrendEvent = null;
    openBar.tensorContext = null;
    openBar.markerEvidence = [
      openBar.provisionalPrimaryMarkers.length
        ? "developing weekly buy candidate; not confirmed until the weekly bar closes"
        : "open bar excluded from confirmed event history",
    ];
    openBar.eventEvidence = [];
  }

  dedupeWeakMarkers(enriched);
  applyDeadCatBounceLifecycle(enriched);
  applyPrimarySignalLifecycle(enriched);
  if (!latestOnly) applyComparatorVwaps(enriched, history);
  const displayBars = latestOnly
    ? 1
    : Math.max(
        70,
        Math.min(Number(history.displayBars) || TENSOR_CHART_DISPLAY_BARS, enriched.length)
      );
  const visibleBars = enriched.slice(-displayBars);
  const closedBars = visibleBars.filter((bar) => bar.barFinality === "closed");
  const latest = closedBars.at(-1) ?? visibleBars.at(-1);
  const prior = closedBars.at(-2) ?? latest;
  if (!latest) return null;
  const recentActiveCall = latest.activeCall;
  const weakCallConflict =
    latest.weakMarker !== null && recentActiveCall !== null;
  const direction = recentActiveCall
    ? recentActiveCall
    : latest.warningMarker
      ? "watch"
      : latest.weakMarker === "B"
        ? "bullish"
        : latest.weakMarker === "W1"
          ? "watch"
          : "no-call";
  const squeezeJustFired =
    prior.squeezeOn === true && latest.squeezeOn === false;
  const move =
    squeezeJustFired &&
    (direction === "bullish" || direction === "bearish")
      ? "Expansion hinted; magnitude uncalibrated"
      : "Size not specified";
  const timeframe = `${history.intervalLabel ?? history.interval ?? "Chart"} chart; call horizon unspecified`;
  const voteDirection =
    direction === "bullish"
      ? latest.bullishVotes
      : direction === "bearish"
        ? latest.bearishVotes
        : Math.max(latest.bullishVotes, latest.bearishVotes);
  const primarySignal = latest.primaryMarkers
    .map(markerLabel)
    .filter(Boolean)
    .join(" + ");
  const eventSignal = [
    primarySignal,
    latest.warningMarker ? "fast/slow conflict warning" : "",
  ]
    .filter(Boolean)
    .join(" + ");
  const comparators = buildComparatorSummary({
    bars: visibleBars,
    direction,
    intervalLabel: history.intervalLabel ?? history.interval ?? "Chart",
  });
  const usesPremarketFiveMinuteTape = history.interval === "5m";

  return {
    version: ANNA_REPLICA_VERSION,
    generatedAt: new Date().toISOString(),
    symbol: history.symbol,
    currency: history.currency ?? "USD",
    exchange: history.exchange ?? null,
    timezone: history.timezone ?? "America/New_York",
    interval: history.interval,
    intervalLabel: history.intervalLabel,
    source: usesPremarketFiveMinuteTape
      ? "Yahoo chart bars with completed premarket and regular-session bars; after-hours excluded"
      : "Yahoo chart bars with extended hours disabled",
    modelStatus: "research reconstruction",
    runtime: {
      mode: "live on demand",
      dataCost: "no paid API required",
      chartRefreshSeconds: 60,
      liveRefreshSeconds: 15,
      signalBasis: usesPremarketFiveMinuteTape
        ? "completed premarket and regular-session bars; after-hours excluded"
        : "completed regular-session bars",
      corpusDependency: "none",
    },
    read: {
      direction,
      move,
      timeframe,
      conviction:
        latest.totalVotes >= 6
          ? `${voteDirection}/${latest.totalVotes} benchmark states aligned`
          : "Incomplete indicator warm-up",
      squeeze:
        latest.squeezeOn === true
          ? "Squeeze active"
          : squeezeJustFired
            ? "Squeeze firing"
            : "No active squeeze",
      candleRegime: latest.candleRegime,
      signal:
        eventSignal ||
        (weakCallConflict
          ? `${latest.weakMarker} conflicts with recent ${recentActiveCall} episode`
          : latest.weakMarker === "B"
            ? "weak buy"
            : latest.weakMarker === "W1"
              ? "watch · no call"
              : recentActiveCall
                ? `active ${recentActiveCall} episode · ${latest.lastPrimaryEventAge} bars since event`
                : latest.dcbMarker || latest.dcbActive
                  ? "DCB candidate · not a primary call"
                  : "no Anna-style call"),
      epoch: latest.epochId,
      epochBasis: latest.epochBasis,
      asOf: new Date(latest.timestamp * 1_000).toISOString(),
      finality: latest.barFinality,
    },
    bars: visibleBars,
    components: ANNA_REPLICA_COMPONENTS,
    comparators,
  };
}

export function getReplicaProviderRequest(intervalValue) {
  const interval = INTERVALS[intervalValue] ? intervalValue : "1d";
  const configuration = INTERVALS[interval];
  return {
    interval,
    providerInterval: configuration.providerInterval,
    range: configuration.range,
  };
}

export function classifyStratBar(current, previous) {
  if (!validBar(current) || !validBar(previous)) return null;
  const tookHigh = current.high > previous.high;
  const tookLow = current.low < previous.low;
  if (tookHigh && tookLow) return "3";
  if (tookHigh) return "2U";
  if (tookLow) return "2D";
  return "1";
}

function applyComparatorVwaps(bars, history) {
  const timezone = history.timezone ?? "America/New_York";
  const yearly =
    history.interval === "1d" || history.interval === "1wk";
  let calendarKey = null;
  let calendarNumerator = 0;
  let calendarVolume = 0;
  let calendarAnchorAt = null;
  let eventNumerator = 0;
  let eventVolume = 0;
  let eventAnchorAt = null;

  for (const bar of bars) {
    const sessionKey = sessionDateKey(bar.timestamp, timezone);
    const nextCalendarKey = yearly ? sessionKey.slice(0, 4) : sessionKey;
    if (nextCalendarKey !== calendarKey) {
      calendarKey = nextCalendarKey;
      calendarNumerator = 0;
      calendarVolume = 0;
      calendarAnchorAt = bar.timestamp;
    }
    const typicalPrice = (bar.high + bar.low + bar.close) / 3;
    if (bar.volume > 0) {
      calendarNumerator += typicalPrice * bar.volume;
      calendarVolume += bar.volume;
    }
    bar.calendarAvwap =
      calendarVolume > 0 ? calendarNumerator / calendarVolume : null;
    bar.calendarAvwapAnchorAt = calendarAnchorAt;

    if (
      bar.barFinality === "closed" &&
      Array.isArray(bar.primaryMarkers) &&
      bar.primaryMarkers.length
    ) {
      eventNumerator = 0;
      eventVolume = 0;
      eventAnchorAt = bar.timestamp;
    }
    if (eventAnchorAt !== null && bar.volume > 0) {
      eventNumerator += typicalPrice * bar.volume;
      eventVolume += bar.volume;
    }
    bar.eventAvwap =
      eventAnchorAt !== null && eventVolume > 0
        ? eventNumerator / eventVolume
        : null;
    bar.eventAvwapAnchorAt = eventAnchorAt;
  }
}

function buildComparatorSummary({ bars, direction, intervalLabel }) {
  const latest = bars.at(-1);
  const prior = bars.at(-2);
  if (!latest) {
    return {
      policy: "isolated research controls; excluded from Anna score",
      openCipher: null,
      strat: null,
      avwap: null,
    };
  }

  const latestCipherEventIndex = findLastIndex(
    bars,
    (bar) =>
      bar.barFinality === "closed" &&
      bar.openCipherEventDirection !== "none"
  );
  const latestCipherEvent =
    latestCipherEventIndex >= 0 ? bars[latestCipherEventIndex] : null;
  const latestReconstructedEventIndex = findLastIndex(
    bars,
    (bar) =>
      bar.barFinality === "closed" &&
      Array.isArray(bar.primaryMarkers) &&
      bar.primaryMarkers.length > 0
  );
  const latestReconstructedEvent =
    latestReconstructedEventIndex >= 0
      ? bars[latestReconstructedEventIndex]
      : null;
  const cipherRelationship = compareEventRelationship({
    firstIndex: latestCipherEventIndex,
    firstDirection: latestCipherEvent?.openCipherEventDirection,
    secondIndex: latestReconstructedEventIndex,
    secondDirection: markerDirection(
      latestReconstructedEvent?.primaryMarkers?.[0]
    ),
  });

  const stratSequence = bars
    .map((bar) => bar.stratType)
    .filter(Boolean)
    .slice(-3)
    .join("–");
  const stratMove =
    latest.stratType === "1"
      ? "Compression / contained range"
      : latest.stratType === "2U"
        ? "One-sided upward expansion"
        : latest.stratType === "2D"
          ? "One-sided downward expansion"
          : latest.stratType === "3"
            ? "Two-sided expansion; first break unknown"
            : "Warming";
  const stratRelationship =
    direction === "bullish" && latest.stratDirection === "bullish"
      ? "Confirms current Anna direction"
      : direction === "bearish" && latest.stratDirection === "bearish"
        ? "Confirms current Anna direction"
        : (direction === "bullish" &&
              latest.stratDirection === "bearish") ||
            (direction === "bearish" &&
              latest.stratDirection === "bullish")
          ? "Conflicts with current Anna direction"
          : "No directional relationship";

  const calendarPosition = avwapPosition(
    latest.close,
    latest.calendarAvwap
  );
  const eventPosition = avwapPosition(latest.close, latest.eventAvwap);
  const calendarDistancePct =
    finite(latest.calendarAvwap) && latest.calendarAvwap !== 0
      ? (latest.close - latest.calendarAvwap) / latest.calendarAvwap
      : null;
  const calendarSlope =
    finite(latest.calendarAvwap) && finite(prior?.calendarAvwap)
      ? latest.calendarAvwap > prior.calendarAvwap
        ? "rising"
        : latest.calendarAvwap < prior.calendarAvwap
          ? "falling"
          : "flat"
      : "warming";

  return {
    policy: "isolated research controls; excluded from Anna score",
    openCipher: {
      diagnosticState:
        latest.openCipherState === "warming"
          ? "no-call"
          : latest.openCipherState,
      diagnosticBasis:
        "Our composite of WaveTrend 9/12/3 and EMA5/11 agreement; not an official OpenCipher output",
      event:
        latest.openCipherEvents.length > 0
          ? latest.openCipherEvents.join(" + ")
          : latestCipherEvent
            ? latestCipherEvent.openCipherEvents.join(" + ")
            : "none",
      eventFinality:
        latest.openCipherEvents.length > 0
          ? latest.barFinality === "open"
            ? "developing"
            : "closed"
          : latestCipherEvent
            ? "closed"
            : "none",
      move: "Size not specified",
      timeframe: `${intervalLabel} chart; forecast horizon unspecified`,
      relationship: cipherRelationship,
    },
    strat: {
      direction: latest.stratDirection ?? "unresolved",
      state: latest.stratType ?? "warming",
      sequence: stratSequence || "warming",
      move: stratMove,
      timeframe: `${intervalLabel}; ${
        latest.barFinality === "open" ? "developing" : "closed"
      } bar`,
      relationship: stratRelationship,
    },
    avwap: {
      direction: calendarPosition,
      distancePct: nullableNumber(calendarDistancePct),
      slope: calendarSlope,
      calendarAnchor:
        historyIntervalAnchorLabel(intervalLabel),
      calendarValue: nullableNumber(latest.calendarAvwap),
      eventPosition,
      eventValue: nullableNumber(latest.eventAvwap),
      eventAnchorAt:
        latest.eventAvwapAnchorAt === null
          ? null
          : new Date(latest.eventAvwapAnchorAt * 1_000).toISOString(),
      move: "Positional context only; no projected size",
      timeframe: intervalLabel,
      relationship:
        latest.eventAvwap === null
          ? "No confirmed Anna-event anchor in view"
          : "Measures post-call acceptance only",
    },
  };
}

function compareEventRelationship({
  firstIndex,
  firstDirection,
  secondIndex,
  secondDirection,
}) {
  if (
    firstIndex < 0 ||
    secondIndex < 0 ||
    !["bullish", "bearish"].includes(firstDirection) ||
    !["bullish", "bearish"].includes(secondDirection)
  ) {
    return "Independent / insufficient paired events";
  }
  if (firstDirection !== secondDirection) {
    return "Conflicts with current reconstruction";
  }
  if (firstIndex === secondIndex) {
    return "Coincides with current reconstruction on the same closed bar";
  }
  const gap = Math.abs(firstIndex - secondIndex);
  return firstIndex < secondIndex
    ? `Leads current reconstruction by ${gap} closed bar${gap === 1 ? "" : "s"}`
    : `Follows current reconstruction by ${gap} closed bar${gap === 1 ? "" : "s"}`;
}

function markerDirection(marker) {
  return typeof marker === "string" && marker.startsWith("buy")
    ? "bullish"
    : typeof marker === "string" && marker.startsWith("sell")
      ? "bearish"
      : null;
}

function avwapPosition(price, value) {
  if (!finite(price) || !finite(value) || value === 0) return "unresolved";
  const distance = (price - value) / value;
  if (Math.abs(distance) <= 0.0025) return "testing";
  return distance > 0 ? "above" : "below";
}

function historyIntervalAnchorLabel(intervalLabel) {
  return intervalLabel === "Daily" || intervalLabel === "Weekly"
    ? "calendar-year boundary"
    : "exchange-session boundary";
}

function findLastIndex(values, predicate) {
  for (let index = values.length - 1; index >= 0; index -= 1) {
    if (predicate(values[index], index)) return index;
  }
  return -1;
}

const US_SESSION_VENUES = new Set([
  "NASDAQ",
  "NASDAQGS",
  "NASDAQGM",
  "NASDAQCM",
  "NMS",
  "NCM",
  "NGM",
  "NYSE",
  "NYQ",
  "NYSEAMERICAN",
  "NYSEMKT",
  "ASE",
  "NYSEARCA",
  "PCX",
  "OTC",
  "OTCQX",
  "OTCQB",
  "PNK",
  "OTHEROTC",
  "BATS",
  "BTS",
  "CBOE",
  "IEX",
]);

const FOREIGN_SESSION_TEMPLATES = Object.freeze({
  STOCKHOLM: [9 * 60, 17 * 60 + 30, "Europe/Stockholm"],
  STO: [9 * 60, 17 * 60 + 30, "Europe/Stockholm"],
  NASDAQSTOCKHOLM: [9 * 60, 17 * 60 + 30, "Europe/Stockholm"],
  XETRA: [9 * 60, 17 * 60 + 30, "Europe/Berlin"],
  XETR: [9 * 60, 17 * 60 + 30, "Europe/Berlin"],
  GERMANY: [9 * 60, 17 * 60 + 30, "Europe/Berlin"],
  FRANKFURT: [8 * 60, 20 * 60, "Europe/Berlin"],
  FWB: [8 * 60, 20 * 60, "Europe/Berlin"],
  TRADEGATE: [8 * 60, 22 * 60, "Europe/Berlin"],
  LSE: [8 * 60, 16 * 60 + 30, "Europe/London"],
  LONDON: [8 * 60, 16 * 60 + 30, "Europe/London"],
  SIX: [9 * 60, 17 * 60 + 30, "Europe/Zurich"],
  SWX: [9 * 60, 17 * 60 + 30, "Europe/Zurich"],
  EURONEXT: [9 * 60, 17 * 60 + 30, "Europe/Paris"],
  OSL: [9 * 60, 16 * 60 + 20, "Europe/Oslo"],
  OSLO: [9 * 60, 16 * 60 + 20, "Europe/Oslo"],
  OMXCOP: [9 * 60, 17 * 60, "Europe/Copenhagen"],
  OMXHEX: [10 * 60, 18 * 60 + 30, "Europe/Helsinki"],
  BME: [9 * 60, 17 * 60 + 30, "Europe/Madrid"],
  MIL: [9 * 60, 17 * 60 + 30, "Europe/Rome"],
  VIE: [9 * 60, 17 * 60 + 30, "Europe/Vienna"],
  ASX: [10 * 60, 16 * 60, "Australia/Sydney"],
  TSX: [9 * 60 + 30, 16 * 60, "America/Toronto"],
  TSXV: [9 * 60 + 30, 16 * 60, "America/Toronto"],
  HKEX: [9 * 60 + 30, 16 * 60, "Asia/Hong_Kong"],
  TSE: [9 * 60, 15 * 60 + 30, "Asia/Tokyo"],
  JPX: [9 * 60, 15 * 60 + 30, "Asia/Tokyo"],
  KRX: [9 * 60, 15 * 60 + 30, "Asia/Seoul"],
  KOSDAQ: [9 * 60, 15 * 60 + 30, "Asia/Seoul"],
  NSE: [9 * 60 + 15, 15 * 60 + 30, "Asia/Kolkata"],
  BSE: [9 * 60 + 15, 15 * 60 + 30, "Asia/Kolkata"],
  SSE: [9 * 60 + 30, 15 * 60, "Asia/Shanghai"],
  SZSE: [9 * 60 + 30, 15 * 60, "Asia/Shanghai"],
  NZX: [10 * 60, 16 * 60 + 45, "Pacific/Auckland"],
  TWSE: [9 * 60, 13 * 60 + 30, "Asia/Taipei"],
  TPEX: [9 * 60, 13 * 60 + 30, "Asia/Taipei"],
  B3: [10 * 60, 17 * 60, "America/Sao_Paulo"],
  JSE: [9 * 60, 17 * 60, "Africa/Johannesburg"],
  SGX: [9 * 60, 17 * 60, "Asia/Singapore"],
  SET: [10 * 60, 16 * 60 + 30, "Asia/Bangkok"],
  IDX: [9 * 60, 16 * 60, "Asia/Jakarta"],
  KLSE: [9 * 60, 17 * 60, "Asia/Kuala_Lumpur"],
  TASE: [10 * 60, 17 * 60 + 35, "Asia/Jerusalem"],
  BIST: [10 * 60, 18 * 60, "Europe/Istanbul"],
  MOEX: [9 * 60 + 50, 18 * 60 + 50, "Europe/Moscow"],
  WSE: [9 * 60, 17 * 60 + 5, "Europe/Warsaw"],
  BUD: [9 * 60, 17 * 60, "Europe/Budapest"],
  PSE: [9 * 60 + 30, 15 * 60 + 30, "Asia/Manila"],
});

function compactVenue(value) {
  return String(value || "").toUpperCase().replace(/[^A-Z0-9]/g, "");
}

function validTimezone(value) {
  const timezone = String(value || "").trim();
  if (!timezone) return null;
  try {
    tensorDateFormatter("en-US", { timeZone: timezone }).format();
    return timezone;
  } catch {
    return null;
  }
}

function sessionTemplateForMetadata(meta, timezone, symbol) {
  const instrumentType = compactVenue(meta?.instrumentType);
  const venue = compactVenue(meta?.fullExchangeName || meta?.exchangeName);
  const normalizedSymbol = compactVenue(symbol);
  if (
    instrumentType.includes("CRYPTO") ||
    (normalizedSymbol.endsWith("USD") && String(symbol || "").includes("-"))
  )
    return {
      kind: "continuous",
      timezone: "UTC",
      regularOpenMinutes: 0,
      regularCloseMinutes: 24 * 60,
    };
  if (
    instrumentType.includes("CURRENCY") ||
    instrumentType.includes("FUTURE") ||
    String(symbol || "").endsWith("=X") ||
    String(symbol || "").endsWith("=F")
  )
    return {
      kind: "continuous",
      timezone: "UTC",
      regularOpenMinutes: 0,
      regularCloseMinutes: 24 * 60,
    };
  if (
    US_SESSION_VENUES.has(venue) ||
    !timezone ||
    ["AMERICA/NEW_YORK", "US/EASTERN"].includes(String(timezone).toUpperCase())
  )
    return {
      kind: "us-security",
      timezone: "America/New_York",
      regularOpenMinutes: 9 * 60 + 30,
      regularCloseMinutes: 16 * 60,
    };
  const configured = FOREIGN_SESSION_TEMPLATES[venue];
  if (configured)
    return {
      kind: "foreign-security",
      regularOpenMinutes: configured[0],
      regularCloseMinutes: configured[1],
      timezone: configured[2],
    };
  return {
    kind: "foreign-security",
    timezone: validTimezone(timezone) || timezone,
    regularOpenMinutes: 9 * 60,
    regularCloseMinutes: 17 * 60,
  };
}

function localMinutes(timestamp, timezone) {
  try {
    const parts = tensorDateFormatter("en-US", {
      timeZone: timezone,
      hour: "2-digit",
      minute: "2-digit",
      hourCycle: "h23",
    }).formatToParts(new Date(timestamp * 1_000));
    const hour = Number(parts.find((part) => part.type === "hour")?.value);
    const minute = Number(parts.find((part) => part.type === "minute")?.value);
    if (Number.isFinite(hour) && Number.isFinite(minute)) return hour * 60 + minute;
  } catch {
    // Fall through to UTC only for an invalid provider timezone.
  }
  const date = new Date(timestamp * 1_000);
  return date.getUTCHours() * 60 + date.getUTCMinutes();
}

function aggregateBarsBySession(
  bars,
  size,
  timezone,
  baseDurationSeconds,
  template = sessionTemplateForMetadata({}, timezone, ""),
) {
  const eligibleBars =
    template.kind === "us-security" || template.kind === "foreign-security"
      ? bars.filter((bar) => {
          const minutes = localMinutes(bar.timestamp, template.timezone);
          return (
            minutes >= template.regularOpenMinutes &&
            minutes < template.regularCloseMinutes
          );
        })
      : bars;
  const output = [];
  let session = null;
  let sessionAnchor = null;
  let bucketIndex = null;
  let bucket = [];
  const flush = () => {
    if (!bucket.length) return;
    const expectedStart = sessionAnchor +
      bucketIndex * baseDurationSeconds * size;
    const contiguous =
      bucket[0].timestamp === expectedStart &&
      bucket.every(
        (bar, index) =>
          index === 0 ||
          bar.timestamp - bucket[index - 1].timestamp === baseDurationSeconds
      );
    // The shortened US-equity closing bucket is useful session context, but
    // it is not a duration-complete 2h/4h candle and must not be labeled or
    // scored as one.
    const complete = bucket.length === size;
    if (contiguous && complete) {
      output.push({
        timestamp: bucket[0].timestamp,
        open: bucket[0].open,
        high: Math.max(...bucket.map((bar) => bar.high)),
        low: Math.min(...bucket.map((bar) => bar.low)),
        close: bucket[bucket.length - 1].close,
        volume: bucket.reduce((sum, bar) => sum + bar.volume, 0),
      });
    }
    bucket = [];
  };
  for (const bar of eligibleBars) {
    const nextSession = sessionDateKey(bar.timestamp, template.timezone);
    if (session !== nextSession) {
      flush();
      session = nextSession;
      sessionAnchor = regularSessionAnchor(
        bar.timestamp,
        template.timezone,
        template.regularOpenMinutes,
      );
      bucketIndex = null;
    }
    const nextBucketIndex = Math.floor(
      (bar.timestamp - sessionAnchor) / (baseDurationSeconds * size)
    );
    if (bucketIndex !== nextBucketIndex) {
      flush();
      bucketIndex = nextBucketIndex;
    }
    bucket.push(bar);
  }
  flush();
  return output;
}

function regularSessionAnchor(timestamp, timezone, regularOpenMinutes = 9 * 60 + 30) {
  try {
    const parts = tensorDateFormatter("en-US", {
      timeZone: timezone,
      hour: "2-digit",
      minute: "2-digit",
      hourCycle: "h23",
    }).formatToParts(new Date(timestamp * 1_000));
    const hour = Number(parts.find((part) => part.type === "hour")?.value);
    const minute = Number(parts.find((part) => part.type === "minute")?.value);
    if (Number.isFinite(hour) && Number.isFinite(minute))
      return timestamp - (hour * 60 + minute - regularOpenMinutes) * 60;
  } catch {
    // Fall through to the source timestamp only for an invalid timezone.
  }
  return timestamp;
}

// Chart replicas for different symbols commonly contain the same completed
// bar timestamps. Reuse the deterministic exchange-date conversion across
// those charts so high-fanout reads do not repeat ICU formatting for every
// symbol. Keep the cache bounded because exchange metadata is data-driven.
const SESSION_DATE_KEY_CACHE_LIMIT = 4_096;
const sessionDateKeyCache = new Map();

function sessionDateKey(timestamp, timezone) {
  const timezoneKey = `${typeof timezone}:${String(timezone)}`;
  const timestampKey = `${typeof timestamp}:${String(timestamp)}`;
  const cacheKey = `${timezoneKey.length}:${timezoneKey}:${timestampKey}`;
  const cached = sessionDateKeyCache.get(cacheKey);
  if (cached !== undefined) return cached;

  let dateKey;
  try {
    dateKey = tensorDateFormatter("en-CA", {
      timeZone: timezone,
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    }).format(new Date(timestamp * 1_000));
  } catch {
    dateKey = new Date(timestamp * 1_000).toISOString().slice(0, 10);
  }
  if (sessionDateKeyCache.size >= SESSION_DATE_KEY_CACHE_LIMIT)
    sessionDateKeyCache.delete(sessionDateKeyCache.keys().next().value);
  sessionDateKeyCache.set(cacheKey, dateKey);
  return dateKey;
}

function exchangeWeekKey(timestamp, timezone) {
  try {
    const parts = tensorDateFormatter("en-US", {
      timeZone: timezone,
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      weekday: "short",
    }).formatToParts(new Date(timestamp * 1_000));
    const year = Number(parts.find((part) => part.type === "year")?.value);
    const month = Number(parts.find((part) => part.type === "month")?.value);
    const day = Number(parts.find((part) => part.type === "day")?.value);
    const weekday = parts.find((part) => part.type === "weekday")?.value;
    const weekdayIndex = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].indexOf(weekday);
    if (Number.isFinite(year) && Number.isFinite(month) && Number.isFinite(day) && weekdayIndex >= 0) {
      const mondayOffset = weekdayIndex === 0 ? 6 : weekdayIndex - 1;
      return new Date(Date.UTC(year, month - 1, day - mondayOffset)).toISOString().slice(0, 10);
    }
  } catch {
    // Fall through to a UTC week only for an invalid exchange timezone.
  }
  const date = new Date(timestamp * 1_000);
  const weekday = date.getUTCDay();
  date.setUTCDate(date.getUTCDate() - (weekday === 0 ? 6 : weekday - 1));
  return date.toISOString().slice(0, 10);
}

function inferLatestBarOpen(
  meta,
  interval,
  latestTimestamp,
  wallClockNow,
  timezone
) {
  const currentTradingPeriod = asRecord(meta.currentTradingPeriod);
  const regular = asRecord(currentTradingPeriod?.regular);
  const end = positiveInteger(regular?.end);
  const marketState =
    typeof meta.marketState === "string"
      ? meta.marketState.toUpperCase()
      : "";
  const duration =
    interval === "2m"
      ? 2 * 60
      : interval === "5m"
        ? 5 * 60
        : interval === "10m"
          ? 10 * 60
          : interval === "1h"
            ? 60 * 60
            : interval === "2h"
              ? 2 * 60 * 60
              : interval === "4h"
                ? 4 * 60 * 60
                : null;
  if (duration !== null) {
    const withinBar =
      wallClockNow >= latestTimestamp &&
      wallClockNow < latestTimestamp + duration;
    if (!withinBar) return false;
    // Extended-hours bars are still developing bars. Conversely, an
    // exchange-aligned 2h/4h final regular bucket must close at the regular
    // bell rather than remain nominally open into postmarket.
    if (
      end !== null &&
      wallClockNow >= end &&
      latestTimestamp < end &&
      ["POST", "POSTPOST", "CLOSED"].includes(marketState)
    ) return false;
    return true;
  }
  if (interval === "1wk") {
    const age = wallClockNow - latestTimestamp;
    if (age < 0 || age >= 7 * 24 * 60 * 60) return false;
    const instrumentType =
      typeof meta.instrumentType === "string"
        ? meta.instrumentType.toUpperCase()
        : "";
    const exchangeName =
      typeof meta.exchangeName === "string"
        ? meta.exchangeName.toUpperCase()
        : "";
    const continuous =
      instrumentType === "CRYPTOCURRENCY" || exchangeName === "CCC";
    if (continuous) return true;
    const exchangeTimezone =
      typeof meta.exchangeTimezoneName === "string"
        ? meta.exchangeTimezoneName
        : timezone;
    if (
      exchangeWeekKey(latestTimestamp, exchangeTimezone) !==
      exchangeWeekKey(wallClockNow, exchangeTimezone)
    ) return false;
    const day = weekdayInTimezone(
      wallClockNow,
      exchangeTimezone
    );
    if (day === "Sat" || day === "Sun") return false;
    if (day === "Fri" && end !== null && wallClockNow >= end) return false;
    return true;
  }
  if (interval !== "1d") return false;
  const sameExchangeDate =
    sessionDateKey(latestTimestamp, timezone) ===
    sessionDateKey(wallClockNow, timezone);
  if (!sameExchangeDate) return false;
  if (
    marketState === "POST" ||
    marketState === "POSTPOST" ||
    marketState === "CLOSED"
  ) {
    return false;
  }
  if (
    marketState === "REGULAR" ||
    marketState === "PRE" ||
    marketState === "PREPRE"
  ) {
    return true;
  }
  if (end !== null) return wallClockNow < end;
  return true;
}

function providerIntervalSeconds(providerInterval) {
  return providerInterval === "5m"
    ? 5 * 60
    : providerInterval === "60m"
      ? 60 * 60
      : providerInterval === "2m"
        ? 2 * 60
        : 60;
}

function liveSession(meta, nowSeconds) {
  const currentTradingPeriod = asRecord(meta.currentTradingPeriod);
  const periods = [
    ["premarket", asRecord(currentTradingPeriod?.pre)],
    ["regular", asRecord(currentTradingPeriod?.regular)],
    ["after-hours", asRecord(currentTradingPeriod?.post)],
  ];
  for (const [label, period] of periods) {
    const start = positiveInteger(period?.start);
    const end = positiveInteger(period?.end);
    if (
      start !== null &&
      end !== null &&
      nowSeconds >= start &&
      nowSeconds < end
    ) {
      return label;
    }
  }
  const marketState =
    typeof meta.marketState === "string"
      ? meta.marketState.toUpperCase()
      : "";
  if (marketState === "PRE" || marketState === "PREPRE") return "premarket";
  if (marketState === "REGULAR") return "regular";
  if (marketState === "POST" || marketState === "POSTPOST") {
    return "after-hours";
  }
  return "closed";
}

function weekdayInTimezone(timestamp, timezone) {
  try {
    return tensorDateFormatter("en-US", {
      timeZone: timezone,
      weekday: "short",
    }).format(new Date(timestamp * 1_000));
  } catch {
    return new Date(timestamp * 1_000).toUTCString().slice(0, 3);
  }
}

function annaEpochForTimestamp(timestamp, timezone) {
  const dateKey = sessionDateKey(timestamp, timezone);
  return classifyAnnaTemplateEpoch(dateKey);
}

function selectEpochSeries(epochProfiles, earlySeries, currentSeries) {
  return epochProfiles.map((profile, index) =>
    profile.squeezeLength === 14
      ? earlySeries[index]
      : currentSeries[index]
  );
}

function inferPrimaryMarkers({
  bullishVotes,
  bearishVotes,
  totalVotes,
  utBuyFlip,
  utSellFlip,
  ema8BullCross,
  ema8BearCross,
}) {
  const markers = [];
  if (utSellFlip) markers.push("sell-red");
  if (ema8BearCross) markers.push("sell-magenta");
  const mirroredBuyAlignment =
    totalVotes === 7 &&
    bullishVotes >= 5 &&
    bullishVotes - bearishVotes >= 4;
  if (utBuyFlip && mirroredBuyAlignment) markers.push("buy-cyan");
  if (ema8BullCross && mirroredBuyAlignment) markers.push("buy-green");
  return markers;
}

function dedupeWeakMarkers(bars) {
  let activeState = null;
  for (const bar of bars) {
    const nextState = bar.barFinality === "closed" ? bar.weakMarker : null;
    if (nextState === null) {
      activeState = null;
      continue;
    }
    if (nextState === activeState) bar.weakMarker = null;
    activeState = nextState;
  }
}

function applyDeadCatBounceLifecycle(bars) {
  let activeBuyIndex = null;
  for (let index = 20; index < bars.length; index += 1) {
    const bar = bars[index];
    if (bar.barFinality === "open") {
      bar.dcbActive = activeBuyIndex !== null;
      bar.dcbAge =
        activeBuyIndex === null ? null : Math.max(0, index - activeBuyIndex - 1);
      bar.dcbState = activeBuyIndex === null ? "inactive" : "active";
      continue;
    }
    const recentHigh = Math.max(
      ...bars.slice(index - 20, index).map((candidate) => candidate.high)
    );
    const drawdown = recentHigh > 0 ? (recentHigh - bar.close) / recentHigh : 0;
    const candleRange = bar.high - bar.low;
    const closeLocation =
      candleRange > 0 ? (bar.close - bar.low) / candleRange : 0.5;
    const oversold =
      finite(bar.stochK) && bar.stochK <= 15 && drawdown >= 0.18;
    const momentumRising =
      index > 0 &&
      finite(bar.squeezeMomentum) &&
      finite(bars[index - 1].squeezeMomentum) &&
      bar.squeezeMomentum > bars[index - 1].squeezeMomentum;
    const reversal =
      bar.close > bar.open && closeLocation >= 0.6 && momentumRising;
    if (
      activeBuyIndex === null &&
      bar.candleRegime === "bearish" &&
      oversold &&
      reversal
    ) {
      bar.dcbMarker = "buy";
      activeBuyIndex = index;
      bar.dcbActive = true;
      bar.dcbAge = 0;
      bar.dcbState = "active";
      bar.eventEvidence.push({
        event: "dcb-buy",
        direction: "bullish",
        semanticStatus: "confirmed",
        formulaStatus: "provisional",
        basis:
          "Anna's green-star semantics and 1–4-bar horizon; automated validation is a disclosed surrogate",
      });
      continue;
    }
    if (activeBuyIndex !== null) {
      const age = index - activeBuyIndex;
      bar.dcbAge = age;
      const exhausted =
        (bar.close < bar.open && closeLocation <= 0.4) ||
        bar.primaryMarker?.startsWith("sell") ||
        (finite(bar.stochK) && bar.stochK >= 75);
      if (age >= 1 && age <= 4 && exhausted) {
        bar.dcbMarker = "sell";
        bar.dcbState = "exit";
        bar.eventEvidence.push({
          event: "dcb-sell",
          direction: "bearish",
          semanticStatus: "confirmed",
          formulaStatus: "provisional",
          basis:
            "Anna's red-star semantics; automated exhaustion rule is a disclosed surrogate",
        });
        activeBuyIndex = null;
      } else if (age >= 4) {
        bar.dcbState = "expired";
        activeBuyIndex = null;
      } else {
        bar.dcbActive = true;
        bar.dcbState = "active";
      }
    }
  }
}

function applyPrimarySignalLifecycle(bars) {
  let activeCall = null;
  let episode = 0;
  let repeatOrdinal = 0;
  let lastPrimaryIndex = null;
  for (let index = 0; index < bars.length; index += 1) {
    const bar = bars[index];
    const markerDirection = bar.primaryMarker?.startsWith("buy")
      ? "bullish"
      : bar.primaryMarker?.startsWith("sell")
        ? "bearish"
        : null;
    if (markerDirection) {
      if (activeCall === null) {
        episode += 1;
        repeatOrdinal = 1;
        bar.callLifecycle = "fresh";
      } else if (activeCall === markerDirection) {
        repeatOrdinal += 1;
        bar.callLifecycle = "reinforced";
      } else {
        episode += 1;
        repeatOrdinal = 1;
        bar.callLifecycle = "reversed";
      }
      activeCall = markerDirection;
      lastPrimaryIndex = index;
    } else if (bar.weakMarker === "B") {
      bar.callLifecycle = "weak";
    } else if (activeCall) {
      bar.callLifecycle = "active";
    }
    const completedIndex =
      bar.barFinality === "open" ? Math.max(0, index - 1) : index;
    bar.lastPrimaryEventAge =
      lastPrimaryIndex === null
        ? null
        : Math.max(0, completedIndex - lastPrimaryIndex);
    bar.activeCall = activeCall;
    bar.callEpisode = activeCall ? `episode-${episode}` : null;
    bar.repeatOrdinal = markerDirection ? repeatOrdinal : 0;
  }
}

// Signal-only consumers need the complete latest bar, but historical bars are
// used only to establish marker de-duplication and lifecycle state. Keeping
// every chart comparator and indicator field on all historical bars makes the
// calculation worker retain a large object graph until the symbol finishes.
// Preserve the causal fields required by the lifecycle passes and discard the
// chart-only payload before it is retained in `enriched`.
function compactSignalHistoryBar(bar) {
  return {
    timestamp: bar.timestamp,
    open: bar.open,
    high: bar.high,
    low: bar.low,
    close: bar.close,
    volume: bar.volume,
    barFinality: bar.barFinality,
    stochK: bar.stochK,
    squeezeMomentum: bar.squeezeMomentum,
    candleRegime: bar.candleRegime,
    primaryMarker: bar.primaryMarker,
    primaryMarkers: bar.primaryMarkers,
    markerEvidence: bar.markerEvidence,
    eventEvidence: bar.eventEvidence,
    weakMarker: bar.weakMarker,
    dcbMarker: bar.dcbMarker,
    dcbActive: bar.dcbActive,
    dcbAge: bar.dcbAge,
    dcbState: bar.dcbState,
    activeCall: bar.activeCall,
    callLifecycle: bar.callLifecycle,
    callEpisode: bar.callEpisode,
    repeatOrdinal: bar.repeatOrdinal,
    lastPrimaryEventAge: bar.lastPrimaryEventAge,
  };
}

function stochasticRsi(close, rsiLength, stochLength, kLength, dLength) {
  const rsi = rsiSeries(close, rsiLength);
  const raw = close.map((_, index) => {
    if (index < stochLength - 1 || !finite(rsi[index])) return null;
    const window = rsi.slice(index - stochLength + 1, index + 1);
    if (window.some((value) => !finite(value))) return null;
    const lowest = Math.min(...window);
    const highest = Math.max(...window);
    return highest === lowest ? 50 : ((rsi[index] - lowest) / (highest - lowest)) * 100;
  });
  const k = smaNullable(raw, kLength);
  const d = smaNullable(k, dLength);
  return { rsi, raw, k, d };
}

function rsiSeries(values, length) {
  const output = Array(values.length).fill(null);
  if (values.length <= length) return output;
  let gains = 0;
  let losses = 0;
  for (let index = 1; index <= length; index += 1) {
    const change = values[index] - values[index - 1];
    gains += Math.max(change, 0);
    losses += Math.max(-change, 0);
  }
  let averageGain = gains / length;
  let averageLoss = losses / length;
  output[length] = rsiValue(averageGain, averageLoss);
  for (let index = length + 1; index < values.length; index += 1) {
    const change = values[index] - values[index - 1];
    averageGain =
      (averageGain * (length - 1) + Math.max(change, 0)) / length;
    averageLoss =
      (averageLoss * (length - 1) + Math.max(-change, 0)) / length;
    output[index] = rsiValue(averageGain, averageLoss);
  }
  return output;
}

function rsiValue(gain, loss) {
  if (loss === 0) return gain === 0 ? 50 : 100;
  return 100 - 100 / (1 + gain / loss);
}

function aroonSeries(high, low, length) {
  const up = Array(high.length).fill(null);
  const down = Array(high.length).fill(null);
  for (let index = length; index < high.length; index += 1) {
    let highOffset = 0;
    let lowOffset = 0;
    for (let offset = 1; offset <= length; offset += 1) {
      if (high[index - offset] > high[index - highOffset]) highOffset = offset;
      if (low[index - offset] < low[index - lowOffset]) lowOffset = offset;
    }
    up[index] = ((length - highOffset) / length) * 100;
    down[index] = ((length - lowOffset) / length) * 100;
  }
  return { up, down };
}

function directionalMovement(high, low, close, length) {
  const trueRange = Array(high.length).fill(null);
  const plusDm = Array(high.length).fill(null);
  const minusDm = Array(high.length).fill(null);
  for (let index = 1; index < high.length; index += 1) {
    trueRange[index] = Math.max(
      high[index] - low[index],
      Math.abs(high[index] - close[index - 1]),
      Math.abs(low[index] - close[index - 1])
    );
    const upMove = high[index] - high[index - 1];
    const downMove = low[index - 1] - low[index];
    plusDm[index] = upMove > downMove && upMove > 0 ? upMove : 0;
    minusDm[index] = downMove > upMove && downMove > 0 ? downMove : 0;
  }
  const atr = wilderAverage(trueRange, length);
  const plusAverage = wilderAverage(plusDm, length);
  const minusAverage = wilderAverage(minusDm, length);
  const plusDi = combine(plusAverage, atr, (value, range) =>
    range === 0 ? 0 : (100 * value) / range
  );
  const minusDi = combine(minusAverage, atr, (value, range) =>
    range === 0 ? 0 : (100 * value) / range
  );
  const dx = combine(plusDi, minusDi, (plus, minus) =>
    plus + minus === 0 ? 0 : (100 * Math.abs(plus - minus)) / (plus + minus)
  );
  const adx = wilderAverage(dx, length);
  return { plusDi, minusDi, adx };
}

function wilderAtr(high, low, close, length) {
  const ranges = high.map((value, index) =>
    index === 0
      ? value - low[index]
      : Math.max(
          value - low[index],
          Math.abs(value - close[index - 1]),
          Math.abs(low[index] - close[index - 1])
        )
  );
  return wilderAverage(ranges, length);
}

function wilderAverage(values, length) {
  const output = Array(values.length).fill(null);
  if (values.length < length) return output;
  let sum = 0;
  let count = 0;
  for (let index = 0; index < values.length; index += 1) {
    if (!finite(values[index])) continue;
    sum += values[index];
    count += 1;
    if (count === length) {
      output[index] = sum / length;
      for (let next = index + 1; next < values.length; next += 1) {
        if (!finite(values[next])) continue;
        output[next] =
          (output[next - 1] * (length - 1) + values[next]) / length;
      }
      break;
    }
  }
  return output;
}

function squeezeMomentumSeries(
  high,
  low,
  close,
  basis,
  length,
  momentumLength = length
) {
  const deviation = close.map((value, index) => {
    if (index < length - 1 || !finite(basis[index])) return null;
    const highest = Math.max(...high.slice(index - length + 1, index + 1));
    const lowest = Math.min(...low.slice(index - length + 1, index + 1));
    const center = ((highest + lowest) / 2 + basis[index]) / 2;
    return value - center;
  });
  return rollingLinearRegressionEndpoint(deviation, momentumLength);
}

function rollingLinearRegressionEndpoint(values, length) {
  const output = Array(values.length).fill(null);
  const xMean = (length - 1) / 2;
  const denominator = Array.from({ length }, (_, index) =>
    (index - xMean) ** 2
  ).reduce((sum, value) => sum + value, 0);
  for (let index = length - 1; index < values.length; index += 1) {
    const window = values.slice(index - length + 1, index + 1);
    if (window.some((value) => !finite(value))) continue;
    const yMean = window.reduce((sum, value) => sum + value, 0) / length;
    const numerator = window.reduce(
      (sum, value, offset) =>
        sum + (offset - xMean) * (value - yMean),
      0
    );
    const regressionSlope = denominator === 0 ? 0 : numerator / denominator;
    const intercept = yMean - regressionSlope * xMean;
    output[index] = intercept + regressionSlope * (length - 1);
  }
  return output;
}

function macdSeries(values, fast, slow, signalLength) {
  const fastEma = ema(values, fast);
  const slowEma = ema(values, slow);
  const macd = combine(fastEma, slowEma, (fastValue, slowValue) => fastValue - slowValue);
  const signal = emaNullable(macd, signalLength);
  const histogram = combine(macd, signal, (value, signalValue) => value - signalValue);
  return { macd, signal, histogram };
}

function waveTrendSeries(high, low, close, channelLength, averageLength, signalLength) {
  const averagePrice = close.map(
    (value, index) => (high[index] + low[index] + value) / 3
  );
  const esa = ema(averagePrice, channelLength);
  const absoluteDeviation = averagePrice.map((value, index) =>
    finite(esa[index]) ? Math.abs(value - esa[index]) : null
  );
  const deviation = emaNullable(absoluteDeviation, channelLength);
  const channelIndex = averagePrice.map((value, index) => {
    const denominator = finite(deviation[index])
      ? 0.015 * deviation[index]
      : null;
    return finite(denominator) && denominator !== 0
      ? (value - esa[index]) / denominator
      : null;
  });
  const wt1 = emaNullable(channelIndex, averageLength);
  const wt2 = smaNullable(wt1, signalLength);
  const events = close.map((_, index) =>
    crossesAbove(wt1, wt2, index)
      ? "bull_cross"
      : crossesBelow(wt1, wt2, index)
        ? "bear_cross"
        : null
  );
  const zones = close.map((_, index) => {
    if (!finite(wt1[index]) || !finite(wt2[index])) return null;
    if (wt1[index] >= 60 && wt2[index] >= 60) return "overbought";
    if (wt1[index] <= -60 && wt2[index] <= -60) return "oversold";
    if (wt1[index] >= 53 && wt2[index] >= 53) return "upper";
    if (wt1[index] <= -53 && wt2[index] <= -53) return "lower";
    return "neutral";
  });
  return { wt1, wt2, events, zones };
}

function utBotSeries(high, low, close, atrLength, sensitivity) {
  const atr = wilderAtr(high, low, close, atrLength);
  const stop = Array(close.length).fill(null);
  const firstReady = atr.findIndex(finite);
  if (firstReady >= 0) stop[firstReady] = 0;
  for (let index = firstReady + 1; index < close.length; index += 1) {
    const priorStop = stop[index - 1];
    if (!finite(atr[index]) || !finite(priorStop)) continue;
    const loss = sensitivity * atr[index];
    if (close[index] > priorStop && close[index - 1] > priorStop) {
      stop[index] = Math.max(priorStop, close[index] - loss);
    } else if (close[index] < priorStop && close[index - 1] < priorStop) {
      stop[index] = Math.min(priorStop, close[index] + loss);
    } else if (close[index] > priorStop) {
      stop[index] = close[index] - loss;
    } else {
      stop[index] = close[index] + loss;
    }
  }
  const events = close.map((_, index) =>
    crossesAbove(close, stop, index)
      ? "buy_flip"
      : crossesBelow(close, stop, index)
        ? "sell_flip"
        : null
  );
  const regimes = close.map((value, index) =>
    finite(stop[index])
      ? value > stop[index]
        ? "bullish"
        : value < stop[index]
          ? "bearish"
          : "neutral"
      : null
  );
  return { atr, stop, events, regimes };
}

function onBalanceVolume(close, volume) {
  const output = Array(close.length).fill(0);
  for (let index = 1; index < close.length; index += 1) {
    output[index] =
      output[index - 1] +
      (close[index] > close[index - 1]
        ? volume[index]
        : close[index] < close[index - 1]
          ? -volume[index]
          : 0);
  }
  return output;
}

function redDragonMcdx(high, low, close, volume, rangeLength, averageLength) {
  const profit = Array(close.length).fill(null);
  const locked = Array(close.length).fill(null);
  const rock = Array(close.length).fill(null);
  for (let index = rangeLength - 1; index < close.length; index += 1) {
    const highest = Math.max(
      ...high.slice(index - rangeLength + 1, index + 1)
    );
    const lowest = Math.min(
      ...low.slice(index - rangeLength + 1, index + 1)
    );
    const range = highest - lowest;
    if (range === 0) continue;
    const midpoint = (highest + lowest) / 2;
    const pc1 = ((close[index] - lowest) / range) * 100;
    const pc2 = ((close[index] - midpoint) / range) * 100;
    profit[index] = clamp((pc1 + pc2) / 2 + 25, 0, 100);
    const float = clamp(
      100 - ((highest - close[index]) / range) * 100 + 25,
      0,
      100
    );
    locked[index] = 100 - float;
    rock[index] = 100 - profit[index] - locked[index];
  }
  const averageVolume = sma(volume, averageLength);
  const volumeRatio = combine(volume, averageVolume, (value, average) =>
    average === 0 ? 0 : value / average
  );
  return {
    profit,
    locked,
    rock,
    averageProfit: smaNullable(profit, averageLength),
    averageLocked: smaNullable(locked, averageLength),
    averageRock: smaNullable(rock, averageLength),
    volumeRatio,
  };
}

function inferObvDivergence(close, obv, index, lookback) {
  if (index < lookback) return null;
  const priceSlope = slope(close, index, lookback);
  const volumeSlope = slope(obv, index, lookback);
  if (!finite(priceSlope) || !finite(volumeSlope)) return null;
  if (priceSlope < 0 && volumeSlope > 0) return "bullish";
  if (priceSlope > 0 && volumeSlope < 0) return "bearish";
  return "aligned";
}

function slope(values, endIndex, length) {
  if (endIndex < length - 1) return null;
  const window = values.slice(endIndex - length + 1, endIndex + 1);
  if (window.some((value) => !finite(value))) return null;
  const xMean = (length - 1) / 2;
  const yMean = window.reduce((sum, value) => sum + value, 0) / length;
  let numerator = 0;
  let denominator = 0;
  for (let index = 0; index < length; index += 1) {
    numerator += (index - xMean) * (window[index] - yMean);
    denominator += (index - xMean) ** 2;
  }
  return denominator === 0 ? 0 : numerator / denominator;
}

function sma(values, length) {
  const output = Array(values.length).fill(null);
  let sum = 0;
  for (let index = 0; index < values.length; index += 1) {
    sum += values[index];
    if (index >= length) sum -= values[index - length];
    if (index >= length - 1) output[index] = sum / length;
  }
  return output;
}

function priorSma(values, length) {
  const inclusive = sma(values, length);
  return values.map((_, index) =>
    index > 0 ? nullableNumber(inclusive[index - 1]) : null
  );
}

function smaNullable(values, length) {
  const output = Array(values.length).fill(null);
  for (let index = length - 1; index < values.length; index += 1) {
    const window = values.slice(index - length + 1, index + 1);
    if (window.some((value) => !finite(value))) continue;
    output[index] = window.reduce((sum, value) => sum + value, 0) / length;
  }
  return output;
}

function rollingStd(values, length) {
  const means = sma(values, length);
  return values.map((_, index) => {
    if (index < length - 1 || !finite(means[index])) return null;
    const window = values.slice(index - length + 1, index + 1);
    const variance =
      window.reduce(
        (sum, value) => sum + (value - means[index]) ** 2,
        0
      ) / length;
    return Math.sqrt(variance);
  });
}

function ema(values, length) {
  const output = Array(values.length).fill(null);
  if (values.length < length) return output;
  const seed = values.slice(0, length).reduce((sum, value) => sum + value, 0) / length;
  output[length - 1] = seed;
  const multiplier = 2 / (length + 1);
  for (let index = length; index < values.length; index += 1) {
    output[index] =
      (values[index] - output[index - 1]) * multiplier + output[index - 1];
  }
  return output;
}

function emaNullable(values, length) {
  const output = Array(values.length).fill(null);
  const first = values.findIndex((value) => finite(value));
  if (first < 0) return output;
  const seedWindow = values.slice(first, first + length);
  if (
    seedWindow.length < length ||
    seedWindow.some((value) => !finite(value))
  ) {
    return output;
  }
  const seed =
    seedWindow.reduce((sum, value) => sum + value, 0) / length;
  const seedIndex = first + length - 1;
  output[seedIndex] = seed;
  const multiplier = 2 / (length + 1);
  for (let index = seedIndex + 1; index < values.length; index += 1) {
    if (!finite(values[index])) continue;
    output[index] =
      (values[index] - output[index - 1]) * multiplier + output[index - 1];
  }
  return output;
}

function combine(left, right, callback) {
  return left.map((value, index) =>
    finite(value) && finite(right[index])
      ? callback(value, right[index])
      : null
  );
}

function directionalVote(k, d, priorK) {
  if (!finite(k) || !finite(d)) return null;
  if (k === d) {
    if (!finite(priorK) || k === priorK) return null;
    return k > priorK ? 1 : -1;
  }
  return k > d ? 1 : -1;
}

function comparisonVote(left, right) {
  if (!finite(left) || !finite(right) || left === right) return null;
  return left > right ? 1 : -1;
}

function signedVote(value) {
  if (!finite(value) || value === 0) return null;
  return value > 0 ? 1 : -1;
}

function stateVote(id, label, vote, value) {
  return {
    id,
    label,
    vote,
    value,
  };
}

function crossesAbove(left, right, index) {
  return (
    index > 0 &&
    finite(left[index]) &&
    finite(right[index]) &&
    finite(left[index - 1]) &&
    finite(right[index - 1]) &&
    left[index] > right[index] &&
    left[index - 1] <= right[index - 1]
  );
}

function crossesBelow(left, right, index) {
  return (
    index > 0 &&
    finite(left[index]) &&
    finite(right[index]) &&
    finite(left[index - 1]) &&
    finite(right[index - 1]) &&
    left[index] < right[index] &&
    left[index - 1] >= right[index - 1]
  );
}

function hasPriorEvent(events, index, event, minimumAge, maximumAge) {
  const start = Math.max(0, index - maximumAge);
  const end = index - minimumAge;
  for (let candidate = end; candidate >= start; candidate -= 1) {
    if (events[candidate] === event) return true;
  }
  return false;
}

function formatPair(left, right, leftLabel, rightLabel) {
  return finite(left) && finite(right)
    ? `${leftLabel} ${left.toFixed(1)} · ${rightLabel} ${right.toFixed(1)}`
    : "warming";
}

function formatSigned(value) {
  if (!finite(value)) return "—";
  if (Math.abs(value) >= 1_000_000) {
    return `${value >= 0 ? "+" : "−"}${(Math.abs(value) / 1_000_000).toFixed(1)}M`;
  }
  if (Math.abs(value) >= 1_000) {
    return `${value >= 0 ? "+" : "−"}${(Math.abs(value) / 1_000).toFixed(1)}K`;
  }
  return `${value >= 0 ? "+" : "−"}${Math.abs(value).toFixed(2)}`;
}

function eventEvidenceForPrimaryMarker(marker) {
  return {
    event: marker,
    direction: marker.startsWith("buy") ? "bullish" : "bearish",
    semanticStatus: "confirmed",
    formulaStatus: "provisional",
    basis:
      marker === "sell-red"
        ? "Anna legend semantics; UT-style timing is exact on 4/10 bar-aligned red events in two time-aligned charts"
        : marker === "sell-magenta"
          ? "Anna legend semantics; EMA8/21 timing is exact on 2/4 bar-aligned pale-magenta events in two time-aligned charts"
          : "Anna legend semantics; buy-side formula is a mirrored experiment",
  };
}

function markerLabel(value) {
  const labels = {
    "buy-cyan": "cyan early/weak-trend buy candidate",
    "buy-green": "green later/stronger buy candidate",
    "sell-magenta": "magenta confirmation sell",
    "sell-red": "red fast-reversal sell",
  };
  return labels[value] ?? null;
}

function validBar(bar) {
  const open = finitePositive(bar?.open);
  const high = finitePositive(bar?.high);
  const low = finitePositive(bar?.low);
  const close = finitePositive(bar?.close);
  return (
    positiveInteger(bar?.timestamp) !== null &&
    open !== null &&
    high !== null &&
    low !== null &&
    close !== null &&
    high >= Math.max(open, close) &&
    low <= Math.min(open, close)
  );
}

function normalizeSymbol(value) {
  const symbol = String(value ?? "")
    .trim()
    .toUpperCase();
  return /^[A-Z0-9^][A-Z0-9.^=/-]{0,23}$/.test(symbol) ? symbol : "";
}

function asRecord(value) {
  return value && typeof value === "object" && !Array.isArray(value)
    ? value
    : null;
}

function finite(value) {
  return typeof value === "number" && Number.isFinite(value);
}

function finitePositive(value) {
  const number = Number(value);
  return Number.isFinite(number) && number > 0 ? number : null;
}

function finiteNonNegative(value) {
  const number = Number(value);
  return Number.isFinite(number) && number >= 0 ? number : null;
}

function positiveInteger(value) {
  const number = Number(value);
  return Number.isSafeInteger(number) && number > 0 ? number : null;
}

function nullableNumber(value) {
  return finite(value) ? value : null;
}

function clamp(value, minimum, maximum) {
  return Math.max(minimum, Math.min(maximum, value));
}
