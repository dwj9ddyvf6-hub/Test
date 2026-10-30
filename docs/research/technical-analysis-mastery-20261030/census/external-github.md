# External Census — Public GitHub Code Canon of Chart Reading

Area: Public GitHub beyond the owner's estate
Date: 2026-10-30
Posture: Mastery study. Sources are inventoried for how they teach identification, drawing, and reading, not for debunking.
Method: browser.search for discovery across 11 queries (TA-Lib patterns, chart pattern recognition, head and shoulders, candlestick patterns Python, support/resistance/trendline algorithms, mplfinance, finplot/lightweight-charts/trendln, harmonic patterns, datasets, awesome lists), then browser.open to actually READ the strongest pages. Honesty marker per source: [READ] = full page opened and absorbed in this pass; [LISTED] = seen in search results / snippet only, not claimed as read.

Counts summary: 22 distinct sources inventoried. 9 read in depth via browser.open (TA-Lib R vignette with full settings tables, zeta-zetra pattern algorithms via DeepWiki, PatternPy PyPI page, TradingPatternScanner README raw, trendln PyPI/README full, TechnicalAnalysisAutomation DeepWiki overview, Harmonic XABCD DeepWiki full, finplot examples wiki). Others are listed with limits stated. PyPI pages for mplfinance and pandas-ta-classic returned a client-challenge block on open in this pass; their content here comes from search-result text only and is marked accordingly.

---

## 1. The Candlestick Canon — TA-Lib and Its Lineage

### 1.1 TA-Lib / ta-lib (C core)
- URL: https://github.com/TA-Lib/ta-lib (also https://github.com/TA-Lib — org, from search results)
- What it teaches: The de facto open-source definition of candlestick reading. 150+ indicators plus the Pattern Recognition group: 61 candlestick patterns. Every other library in this census either wraps it, re-implements it, or defines itself against it.
- Identification rules in brief: Each pattern is a C function named CDL* in `src/ta_func/`, e.g. CDLDOJI, CDLHAMMER, CDLENGULFING, CDLMORNINGSTAR, CDL3BLACKCROWS, CDL3WHITESOLDIERS, CDLABANDONEDBABY, CDLHARAMI, CDLSHOOTINGSTAR. Input is OHLC arrays; output is integer 100 / -100 / 0 (bullish / bearish / none), later wrappers normalize to 1 / -1 / 0. Patterns are grouped by candle count: single (Doji, Hammer, Shooting Star, Marubozu, Spinning Top, Long/Short Line), two (Engulfing, Harami, Harami Cross, Piercing, Dark Cloud Cover, Kicking), three (Morning/Evening Star, Three Inside/Outside, Three White Soldiers, Three Black Crows), four+ (Concealing Baby Swallow, Rising/Falling Three Methods, Mat Hold, Breakaway). Classification is not fixed thresholds: a candle's body/shadow is judged long/short/doji-like against an average of prior candles (see 1.3 for the exact N/alpha table, which is TA-Lib's own logic surfaced in the R port).
- Limits: C/C++ core is hard to read and hard to install (the perennial TA-Lib install pain is documented in almost every tutorial found); pattern functions check candle shape mostly, not preceding trend context, so a Hammer is shape-only unless the caller adds trend filtering. SourceForge 0.4.0 is stale; GitHub is the live home. [LISTED for the C repo itself; rules corroborated by READ sources 1.3 and multiple tutorials]

### 1.2 mrjbq7/ta-lib — Python wrapper
- URL: https://github.com/mrjbq7/ta-lib
- What it teaches: How practitioners actually access the canon in Python: `talib.get_function_groups()['Pattern Recognition']` returns the 61 names; loop `df[candle] = getattr(talib, candle)(open, high, low, close)`. The README enumerates the full 61-name list verbatim (CDL2CROWS through CDLKICKINGBYLENGTH etc.).
- Rules: Identical to 1.1; wrapper adds Cython speed (claimed 2-4x SWIG) and NumPy integration.
- Limits: Still requires the underlying C library installed first (TA_LIBRARY_PATH / TA_INCLUDE_PATH if custom prefix). [LISTED — README via Internet Archive copy and tutorial citations]

### 1.3 serkor1/ta-lib-R — {talib} R port, candlestick vignette [READ]
- URL: https://github.com/serkor1/ta-lib-R/ — vignette read at http://ftp.openbsd.dk/mirrors/pub/mirrors/pub/cran/web/packages/talib/vignettes/candlestick.Rmd
- What it teaches: The clearest written exposition of TA-Lib's internal reading protocol found in this pass. This is the mastery gold: it names the reference-average system behind every pattern.
- Identification / drawing rules in brief (exact, from the vignette):
  - Vocabulary: real body = Open to Close; upper shadow = body top to High; lower shadow = body bottom to Low. Patterns are comparisons of body/shadow size and position within one candle or across consecutive candles.
  - Return: 1 bullish / -1 bearish / 0 none; original TA-Lib 100/-100 restorable.
  - Penetration `eps`: 7 patterns take it (Morning Star, Evening Star, Morning/Evening Doji Star, Abandoned Baby, Dark Cloud Cover, Mat Hold); default 0; e.g. Evening Star with eps=0.3 requires 30% intrusion into the prior body.
  - Lookback: every pattern returns initial NAs; lookback = pattern length + the N used for reference averages.
  - Body settings (N, alpha): BodyLong (10, 1.0) body > average of prior 10 bodies; BodyVeryLong (10, 3.0) > 3x average; BodyShort (10, 1.0) < average; BodyDoji (10, 0.1) body < 10% of average high-low range.
  - Shadow settings: ShadowLong (0, 1.0) shadow > real body; ShadowVeryLong (0, 2.0) > 2x body; ShadowShort (10, 1.0) < half average shadow sum; ShadowVeryShort (10, 0.1) < 10% of average range.
  - Distance settings: Near (5, 0.2) <=20% of average range; Far (5, 0.6) >=60%; Equal (5, 0.05) <=5%.
  - Which settings drive which patterns: Doji family -> BodyDoji; Engulfing/Harami/Dark Cloud/Piercing -> BodyLong + BodyShort; Stars -> BodyShort/BodyLong + shadows; Hammer/Shooting Star/Inverted Hammer/Hanging Man -> ShadowLong + BodyShort; Kicking/Matching Low/Counterattack -> Near/Far/Equal.
  - Charting rule in this port: bullish markers below the candle, bearish above, neutral styled separately; multiple pattern layers stack on one chart.
- Limits: R wrapper itself described as early stage; underlying TA-Lib is the mature part.

### 1.4 pandas-ta (twopirllc) and pandas-ta-classic (xgboosted)
- URLs: https://github.com/twopirllc/pandas-ta ; https://github.com/xgboosted/pandas-ta-classic
- What they teach: The pandas-native workflow for the canon: `df.ta.cdl_pattern(name=...)` / strategy calls that append all patterns as columns. Classic fork claims 141-193 indicators + 62 TA-Lib candlestick patterns (counts vary by version in PyPI listings: 203-253 total), with newer Classic releases claiming all 62 CDL patterns re-implemented natively in Python so no C TA-Lib install is needed, plus 5 native extras (cdl_doji, cdl_inside, cdl_z, cdl_pattern, ha / Heikin-Ashi).
- Rules: Same CDL definitions as 1.1 when TA-Lib-backed; native versions are readable Python, which makes them a better study text than the C core for learning the geometry per pattern.
- Limits: Original pandas-ta repo was noted in a 2025 gist as no longer public/available and its maintainer warned support was unsustainable with a possible archive by 2026-07-01 (from PyPI text); the Classic community fork is the live route. PyPI page blocked on open in this pass (client challenge), so Classic's native-rule detail is [LISTED], not read line by line.

### 1.5 Tulip Indicators / tulipindicators + Tulipy + tulip-rs
- URLs: https://github.com/TulipCharts/tulipindicators ; Python bindings https://github.com/cirla/tulipy ; Rust/Python tulip-rs via PyPI (me60732/tulip-rs-python referenced)
- What they teach: A second, independent C canon: 104 indicators in ANSI C, uniform interface (`ti_<name>_start` / `ti_<name>`), no dependencies. tulip-rs adds 100+ indicators and 60+ candlestick patterns with explicit parameters that surface the reading rules, e.g. bullish_engulfing takes line_period, body_period, min_long_cdl_height, min_cdl_height_tolerance, doji_max_height=0.1.
- Rules: Pattern recognition parameterized rather than hidden: doji-ness is a max body/height ratio; long-candle-ness is a minimum height vs period average. Good contrast to TA-Lib's global settings table.
- Limits: Tulip's classic indicator set is indicator-heavy, pattern-light compared with TA-Lib; tulip-rs PyPI listing is newer/less proven. [LISTED]

### 1.6 finta (peerchemist/finta)
- URL: https://github.com/peerchemist/finta
- What it teaches: 71-80+ indicators in pure pandas (SMA/EMA/MACD/RSI/BBANDS/KC/DMI/STOCH/CCI/ICHIMOKU/PIVOTS etc.), each a readable `TA.<NAME>(ohlc)` method. Useful as geometry reading for indicators and pivot points, not as a candlestick-pattern canon (it has essentially no CDL pattern suite).
- Limits: Repo archived 2022-09-03 per awesome-quant note; README itself warns work in progress, results may not be correct. [LISTED]

### 1.7 bukosabino/ta
- URL: https://github.com/bukosabino/ta
- What it teaches: Another pandas TA library (momentum, trend, volatility, volume) commonly listed beside finta/pandas-ta in awesome-quant. No candlestick pattern canon; included to mark the boundary of the canon.
- Limits: [LISTED only, not opened in depth]

### 1.8 Sortefi / sortefi-ta [LISTED via announcement + search]
- URL: https://github.com/Sortefi/sortefi-ta (as named in the TradingQnA announcement: "GitHub - Sortefi/sortefi-ta")
- What it teaches: A modern, deliberately readable re-implementation: 121 indicators + 59 candlestick patterns + chart patterns VCP, Cup and Handle, High Tight Flag, NR7. Announcement stresses the pedagogy: "Each calculation lives in its own short file with its rule written out, so anyone can read exactly how it works." Pure numpy+pandas, no TA-Lib install, MIT.
- Rules: Per-file rules (not extracted line-by-line in this pass); the chart-pattern additions (VCP contraction sequence, cup-with-handle, high tight flag) extend beyond TA-Lib's candle-only world into Minervini-style price structure.
- Limits: Very new (announced ~10 days before census); small community; GitHub README not opened directly in this pass, announcement read via search text.

### 1.9 eminsk/yfinance-ta-patterns [LISTED]
- URL: https://github.com/eminsk/yfinance-ta-patterns (via PyPI / dev.to announcement)
- What it teaches: A practitioner lesson TA-Lib alone does not teach: confluence. Full 61-pattern scan (pure-Python fallback engine or TA-Lib acceleration) plus a deterministic confluence score 0.0-1.0 from EMA 20/50/200 alignment, zero-lookahead relative volume, Wilder RSI(14), and ATR expansion. Its framing: a Hammer mid-consolidation against a falling 200 EMA is not the same read as the same Hammer at 200 EMA support with 2.5x RVOL and oversold RSI rebound.
- Limits: New, single-author framing; confluence weights are the author's, not a community standard.

---

## 2. Geometric Chart Patterns — Pivots First, Then Shapes

Shared protocol across almost every repo in this section, and the single most transferable reading skill in the census: (1) reduce OHLC to pivot highs/lows, (2) sequence the pivots, (3) validate geometry (symmetry, slope, convergence, ratio), (4) draw the defining lines (neckline, trendlines), (5) confirm on break. The repos differ in pivot definition.

### 2.1 zeta-zetra/chart_patterns — "automate chart patterns" [READ via DeepWiki]
- URL: https://github.com/zeta-zetra/chart_patterns (install route in tutorials: git clone zeta-zetra/chart_patterns); DeepWiki read: https://deepwiki.com/zeta-zetra/code/3.1-pattern-types-and-detection-algorithms
- What it teaches: The cleanest open-source textbook for classical patterns: Head and Shoulders, Inverse H&S, Triple Top/Bottom, Wedge, Triangle (ascending/descending/symmetrical), Rounding Bottom, Rectangle, Support/Resistance.
- Identification rules in brief (exact from the read):
  - Core primitive `pivot_id(l, n1, n2)`: compare a bar to n1 bars left and n2 bars right; return 1 pivot low, 2 pivot high, 3 both, 0 none. Every detector reuses it.
  - H&S: find 3 pivot highs; validate middle (head) higher than both shoulders; check shoulder symmetry (similar height); neckline = line through the two troughs between shoulder-head-shoulder; store for visualization. Inverse uses pivot lows.
  - Triple Top/Bottom: 3 pivots at approximately the same level, with proper spacing validation.
  - Wedge: fit `scipy linregress` lines to pivot maxima and minima; both slopes same sign; lines converge (future intersection); slope ratio within 0.75-1.25.
  - Triangle: linregress on highs and lows; classify by slopes — ascending = rising lower + flat upper, descending = falling upper + flat lower, symmetrical = upper down + lower up; validate convergence at intersection point.
  - Rounding Bottom: pivot lows, fit 2nd-degree polynomial with polyfit, require positive 2nd derivative (upward curvature) and coefficient magnitudes consistent with a U, not a V.
  - Visualization protocol: crop around pattern, candlestick_ohlc plot, overlay pattern lines/curves, save image. Stack: pandas, numpy, scipy, matplotlib, mplfinance.
- Limits: Educational code, windows/thresholds need tuning per instrument/timeframe; DeepWiki is a generated mirror, so file-level truth is the repo itself.

### 2.2 PatternPy — keithorange/PatternPy, PyPI m-patternpy [READ PyPI page]
- URL: https://github.com/keithorange/PatternPy ; https://pypi.org/project/m-patternpy/
- What it teaches: The screener-shaped version of the same canon. One call per pattern adds a label column, e.g. `from patternpy.tradingpatterns import head_and_shoulders; df = head_and_shoulders(df)` creates `head_shoulder_pattern` with NaN / 'Head and Shoulder' / 'Inverse Head and Shoulder'.
- Pattern set / reading vocabulary: H&S and Inverse, Multiple Tops & Bottoms, Horizontal Support & Resistance, Ascending & Descending Triangles, Wedges, Channel Up & Down, Double Top & Bottom, Trend Line Support & Resistance, Higher-High & Lower-Low. The pattern list itself is a good lay taxonomy of what a human reader scans for, in order: reversal heads, repeated tests, horizontal levels, compression, channels, trend sequence.
- Limits: PyPI README is playful rather than precise (no thresholds stated); precision lives in the source functions, which were not line-read in this pass. Rolling-window sensitivity is the main knob (see 2.3 for the same lesson quantified).

### 2.3 TradingPatternScanner — white07S/TradingPatternScanner [READ full README raw]
- URL: https://github.com/white07S/TradingPatternScanner ; raw README read at https://raw.githubusercontent.com/juvu/TradingPatternScanner/main/README.md (mirror/fork path as returned); PyPI: tradingpattern
- What it teaches: Same pattern set as PatternPy (it is in that lineage) PLUS a denoising lesson no other repo here teaches as explicitly: raw rolling-window H&S detection vs the same detector after Savitzky-Golay filtering, Kalman filtering, and wavelet denoising.
- Identification rules / measured results (from README):
  - Basic: rolling window tracking highs/lows, head = highest point, shoulders = lower points either side (and inverse).
  - Savitzky-Golay version also checks head height to reject false heads. Kalman version treats price as a noisy state estimate. Wavelet version denoises while preserving features.
  - Synthetic-data accuracy reported: window 78.50%, filter 78.50%, Kalman 73.50%, wavelet 84.50%. README honestly states synthetic data is not the real market and users must test on their own data and pick the method that fits.
  - Window rule stated for practitioners: smaller window = more sensitive, more false positives; larger window = fewer, cleaner detections. README cross-checks a detected Inverse H&S on 2023-01-09 daily against Finviz's own pattern label.
  - Other patterns defined in one line each, which is itself a reading checklist: multiple tops/bottoms = range; horizontal S/R = levels price struggled to break; triangles = breakout with one trendline as S and the other as R; wedges = converging trendlines, reversal-leaning; channels = strong trend inside parallel lines; double top/bottom = two tests then reversal; trendline S/R = levels from historical price action; HH/LL = trend sequence.
  - Engineering: pandas+numpy only, vectorized.
- Limits: No visualization/unit tests yet (README future work); accuracy is synthetic-only.

### 2.4 TechnicalAnalysisAutomation — shuhanchang12 / neurotrader888 fork [READ DeepWiki overview + Harmonic page]
- URLs: https://github.com/shuhanchang12/TechnicalAnalysisAutomation ; fork documented as neurotrader888/technicalanalysisautomation on DeepWiki
- What it teaches: A full reading pipeline architecture, crypto-first (BTC/USDT): three competing ways to choose the points that matter, then patterns built on each.
  - Directional Change: turning points when price reverses by a threshold (sigma). Sigma granularity lesson (from Harmonic page): sigma 0.01 = many extremes, short-term; 0.02 = moderate; 0.03-0.04 = few major swings, long-term; the code ensembles across sigmas.
  - Perceptually Important Points (PIP): points that are visually significant — the closest code analogue to "what a human eye keeps when it glances at a chart."
  - Rolling Window: sliding local extrema (the PatternPy approach).
- Pattern systems: Harmonic XABCD on Directional Change; H&S on Rolling Window; Flags/Pennants on Rolling Window + trendlines; PIP pattern mining and walk-forward PIP mining (clustering recurring PIP shapes rather than naming classical patterns).
- Harmonic identification rules in brief (exact ratios read): XABCD = 5 points, 4 legs, validated by Fibonacci ratios XA_AB, AB_BC, BC_CD, XA_AD with a log-space error function (range = 0 error if inside, out-of-range penalized 2x, total error must be <= err_thresh, default 0.2; 0.1-0.2 strict, 0.5+ loose):
  - Gartley: 0.618 | 0.382-0.886 | 1.13-1.618 | 0.786
  - Bat: 0.382-0.50 | 0.382-0.886 | 1.618-2.618 | 0.886
  - Butterfly: 0.786 | 0.382-0.886 | 1.618-2.24 | 1.27-1.41
  - Crab: 0.382-0.618 | 0.382-0.886 | 2.618-3.618 | 1.618
  - Deep Crab: 0.886 | 0.382-0.886 | 2.0-3.618 | 1.618
  - Cypher: 0.382-0.618 | 1.13-1.41 | 1.27-2.00 | 0.786
  - Shark: none | 1.13-1.618 | 1.618-2.24 | 0.886-1.13
  - Point D rule: D must be a genuine new extreme since the last confirmed turning point (no interior-point patterns). Signal = one entry at D completion, held until next extreme confirmation. Drawing: white X-A-B-C-D lines, blue X-B/X-D/A-C/B-D references, orange actual-ratio labels, yellow pattern name + error, with pad bars of context.
- Limits: Pins numpy==1.23.1 because pyclustering breaks on newer numpy (stale dependency risk); DeepWiki crawl for the overview was ~355 days old at read time.

---

## 3. Support, Resistance, and Trendline Drawing

### 3.1 trendln — GregoryMorse/trendln [READ full PyPI/README]
- URL: https://github.com/GregoryMorse/trendln ; https://pypi.org/project/trendln/
- What it teaches: The most method-complete open-source answer to "which trendline is the right one?" `calc_support_resistance()` returns local extrema, the average best-fit line through all minima (support) and through all maxima (resistance), and ranked per-window trendlines with (slope, intercept, SSR, slopeErr, interceptErr, areaAvg — area between line and price, averaged per time unit).
- Drawing rules / methods (exact):
  - Extrema finders: METHOD_NAIVE (single-interval local min/max), METHOD_NAIVECONSEC (handles consecutive flat intervals), METHOD_NUMDIFF (default, numerical differentiation via findiff).
  - Line finders: METHOD_NCUBED (exhaustive 3-point, slowest), METHOD_NSQUAREDLOGN (default, 2-point sorted-slope search, fast), METHOD_HOUGHPOINTS (Hough transform on points), METHOD_HOUGHLINES / METHOD_PROBHOUGH (image Hough / probabilistic Hough, needs scikit-image, hough_scale = smallest price increment e.g. 0.01).
  - Defaults that encode practitioner judgment: window=125 bars searched then merged, errpct=0.005 max slope standard error, plotting draws the average line plus top 2 support and top 2 resistance (numbest=2), pctbound=0.1 keeps lines within 10% of the data range beyond high/low, sort by slope error or optionally by wrong-side area.
- Limits: Last PyPI release in the read page is 0.1.8 (2019) — venerable, not actively evolved; close-price based by default, so wick extremes need caller care.

### 3.2 Fractal S/R and the tutorial notebooks (gianlucamalato/machinelearning and others) [LISTED]
- URLs: https://github.com/gianlucamalato/machinelearning/blob/master/Support_and_resistance.ipynb (linked from the read-medium tutorial)
- Rules captured from tutorial text: a fractal is 5 candles where the middle candle has the lowest low (support) or highest high (resistance) of the five; the middle extreme is the level. Corollaries stated as reading rules: more tests of a level = more important; broken resistance becomes support and vice versa. Other tutorial methods catalogued in search: rolling midpoint range, Fibonacci retracement levels, swing highs/lows via `scipy argrelextrema(order=5)` with polyfit trendlines on the swings, pivot points, K-means price clustering, volume profile, regression channels; prominence-based peak/trough detection with `scipy.signal.find_peaks(distance=...)` and binning nearby levels to their mean.
- Multi-anchored regression channels (Entreprenerdly notebook, listed): draw three regression channels anchored at (a) most recent highest high (descending resistance), (b) most recent lowest low (ascending support), (c) flattest-slope segment (indecision/range); confluence = channels agreeing in slope/price region.
- Limits: Tutorial-grade, scattered, no shared test standard; each notebook is a starting point, not a canon.

### 3.3 support_resistance.py inside zeta-zetra (see 2.1)
- Noted separately because it pairs horizontal levels with the pivot system above: levels are pivot clusters, drawn on the same candlestick canvas as the patterns that use them. [READ as part of 2.1 file list]

---

## 4. Charting and Drawing Standards — How the Picture Itself Is Made

### 4.1 mplfinance — matplotlib/mplfinance [LISTED — PyPI open blocked by client challenge; content from search text + tutorials]
- URL: https://github.com/matplotlib/mplfinance
- What it teaches: The Python drawing standard most pattern repos plot with. One call `mpf.plot(df, type=...)` with types ohlc (default), candle, line, renko, pnf, hollow_candle; `mav=(3,6,9)` overlays moving averages; `volume=True` adds the volume pane; `hlines` / `vlines` / `tlines` and `alines` are the programmatic equivalents of a human drawing horizontals, event lines, trendlines, and anchored lines; `make_addplot()` adds any custom series (indicators, level lines as full-length arrays, markers) in the main or a sub-pane; 14+ named styles (charles, yahoo, binance, ibd, classic, etc.) encode house drawing conventions.
- Reading lesson: gaps on the x-axis for non-trading days are shown by default — the library's stance is that seeing weekends/holidays at a glance is part of reading the chart honestly.
- Limits: A plotting library, not a detector; it teaches presentation, not identification. Direct open failed in this pass, so treat parameter detail as search-sourced.

### 4.2 finplot — highfestiva/finplot [READ examples wiki]
- URL: https://github.com/highfestiva/finplot
- What it teaches: Interactive, high-performance financial plotting (pyqtgraph-based) built for eyeballing large history: `candlestick_ochl`, `volume_ocv` as an overlay on the price pane, multi-row `create_plot(rows=2)`, indicator examples for MACD, RSI, Bollinger Bands, Parabolic SAR, TD Sequential, Heikin-Ashi, Renko, accumulation/distribution, OBV, VWAP and volume profile, heatmaps, and cross-asset overlay correlation. A characteristic practitioner idiom from its featured example: compute lower-wick length as min(open,close) - low and mark the top 1% (`quantile(0.99)`) with '^' markers — wick extremes as events worth annotating.
- Drawing rules: view state restores across runs (`autoviewrestore()`), so a reader returns to the same zoom/pan — a small but real reading-protocol feature.
- Limits: README warns the API is clunky for real-time use (built for backtest review); examples are code, not prose explanations.

### 4.3 TradingView Lightweight Charts + lightweight-charts-python [LISTED]
- URLs: https://github.com/tradingview/lightweight-charts ; https://github.com/louisnw01/lightweight-charts-python
- What they teach: The web drawing standard: candlestick/line/area/histogram series, markers, and in the Python wrapper a Toolbox for hand-drawing trendlines, rays, and horizontal lines directly on the chart, multi-pane SubCharts, timeframe selectors and hotkeys — the closest open-source analogue to how practitioners actually draw in TradingView. Series primitives examples include interactive trendlines, S/R levels, price alerts, and text annotations as first-class chart objects.
- Limits: Rendering/drawing infrastructure; no pattern identification logic of its own.

---

## 5. Vision Models and Pattern Datasets — Reading the Picture as a Picture

### 5.1 foduucom/stockmarket-pattern-detection-yolov8 (Hugging Face, GitHub-adjacent) [LISTED via model cards]
- URL: https://huggingface.co/foduucom/stockmarket-pattern-detection-yolov8
- What it teaches: The object-detection approach to reading: train YOLOv8s on annotated chart images and detect patterns as bounding boxes with confidence, including on live screen capture / video. Classes: Head and shoulders bottom, Head and shoulders top, M_Head, StockLine, Triangle, W_Bottom. Dataset: ~9,000 training + ~800 validation annotated chart images (reported training accuracy 0.93 in tutorial use).
- Reading lesson: Pattern extent is a box — start, end, height — which forces the dataset builder to decide exactly where a pattern begins and ends, the question geometric code answers with pivots. Chart style, resolution, and unseen pattern types are stated failure modes.
- Limits: Hosted on Hugging Face, not GitHub proper (included because every GitHub/YOLO tutorial route leads here); labels are coarse (6 classes); performance claims are the publisher's.

### 5.2 Stock Chart Pattern Recognition with Deep Learning (arXiv 1608.07774 lineage) [LISTED]
- What it teaches: CNN recognition of head-and-shoulders, inverted H&S, rising/falling wedges (project summaries also list double/triple tops and bottoms) from chart images rendered from Yahoo Finance OHLCV, reporting ~86% average precision on a 3,000+ chart dataset in secondary summaries.
- Limits: Old (2016 paper), repos claiming it are described by later bloggers as outdated or broken; treat as method history, not runnable canon.

### 5.3 Object Detection Approach for Stock Chart Patterns Recognition (ICSCA 2023 paper + dataset) [LISTED]
- What it teaches: A purpose-built image dataset for four patterns (Head and Shoulder, Reverse H&S, Double Top, Double Bottom) with segmentation to reduce candlestick noise before detection; reports AP50 57.6% on raw candle images, improving with segmentation/variation generation — a quantified lesson that raw candle images are hard even for vision models, and preprocessing the picture (thinning, segmenting) is part of the reading craft.
- Limits: Academic PDF, dataset availability not verified on GitHub in this pass.

---

## 6. Curated Indexes and Educational Collections

### 6.1 wilsonfreitas/awesome-quant [LISTED]
- URL: https://github.com/wilsonfreitas/awesome-quant
- What it teaches: The map of the territory. Its Indicators section is the canonical reading list this census sampled: TA-Lib, pandas-ta, finta, Tulipy/tulipindicators, pandas_talib, bukosabino/ta, talipp (incremental TA), streaming_indicators, bta-lib, plus a separate chart-patterns entry (focus1691/chart-patterns — note: that one is Market/Volume Profile and high-volume nodes, not classical shapes despite the name).
- Limits: A list, not a teacher; last-push metadata in search was stale (2024), and it does not distinguish pattern-recognition depth, which is what this census adds.

### 6.2 Applied tutorial repos worth a reader's time [LISTED]
- CanerIrfanoglu/medium — recognize_candlestick: runs all TA-Lib patterns, collapses the sparse 61-column output to one best-pattern label per bar using Bulkowski's patternsite performance rankings as the priority order. Lesson: when patterns overlap, rank, don't stack.
- CharlieNestor/statistical_analysis_candlestick_patterns: candlestick definitions translated from visual concepts to programmable logic, with Plotly visualization, on US stocks.
- DataPatternX (m-sarabi): candlestick patterns as SQL queries (engulfing_bullish.sql, engulfing_bearish.sql, morning star, etc.) over Postgres OHLC with Plotly plotting — proof the same reading rules can live in SQL, useful for screener design.

---

## 7. Synthesis — What the Code Canon Teaches a Human Reader

1. Start with the candle vocabulary, quantified. Body vs shadows vs range, judged against the last 5-10 candles (TA-Lib N/alpha table, section 1.3), is the foundation every other rule stands on. "Long", "short", "doji-like", "near", "equal" all have numbers.
2. Penetration and symmetry are thresholds, not vibes: star patterns have an eps; H&S shoulders must be similar; wedge slopes must ratio within 0.75-1.25; harmonic legs must fit Fibonacci bands within an error budget.
3. Pivots before patterns. Three rival pivot definitions (n1/n2 window, directional-change threshold, perceptually important points) produce three different charts from the same data; choosing the pivot method is choosing the reading.
4. Denoise deliberately. Savitzky-Golay, Kalman, and wavelet versions of the same detector score differently (wavelet best on synthetic H&S, 84.5%); smoothing is a reading decision with a cost.
5. Lines are fitted and ranked, not eyeballed once. trendln's discipline (extrema -> candidate lines -> rank by slope error / wrong-side area -> draw average + top 2) is a complete protocol for S/R and trendlines.
6. Context completes the read. The newest repos (yfinance-ta-patterns confluence score, Sortefi's VCP/cup-and-handle) all add trend, volume, and volatility context around the shape; the shape alone is the beginning of the read, not the end.
7. Draw it to prove it. Every serious repo renders the detection back onto candles with its defining lines (neckline, trendlines, XABCD legs, ratio labels). A pattern you cannot draw the lines for is not identified yet.

## 8. Gaps and Limits of This Census
- GitHub star counts were not reliably returned by search in this pass, so popularity is described qualitatively (TA-Lib, mplfinance, finplot, pandas-ta are the widely adopted ones by tutorial ubiquity) rather than by invented numbers.
- Direct github.com repo pages were often reached via DeepWiki/PyPI/raw mirrors because those were the readable routes returned; where a README was read via a mirror, that is stated.
- mplfinance and pandas-ta-classic PyPI opens were blocked by a client challenge; their entries are search-sourced and marked [LISTED].
- No paywalls were encountered; the stale-source risks are finta (archived 2022), trendln (2019 release), pandas-ta original (availability/support warnings), and TechnicalAnalysisAutomation's pinned numpy.
