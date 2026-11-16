# LLM Chart Reading — GitHub Research Report

**Mission:** Find and analyze public GitHub repos for TA libraries, automated pattern detection, LLM/vision-model chart reading, multimodal trading agents, labeled chart-pattern datasets, and educational TA-in-code repos — for building an LLM-powered visual chart analyst.
**Research date:** 2026-10-07. Stars quoted are from pages read live that day ("verified live") or search-index crawls ("index"); mark as approximate.

---

## Summary

- **No single open-source library gives you "LLM reads chart images" out of the box**, but several repos implement the full loop: render chart → send image + indicators to a vision model → parse structured JSON → cross-check with deterministic rules. The best steal-able patterns come from `qrak/llm_trader` (chart vision architecture, falsification gate), `jazzi57/claude-trading-skills` (the best prompt-engineering artifact: vision + deterministic cross-check), and `aadisalhotra/llm-trading-lab` (multi-provider image-passing adapters).
- **For deterministic ground truth, the TA ecosystem is mature:** TA-Lib (~60 CDL candlestick functions, ~12.3k stars), pandas-ta-classic (284 indicators+patterns, all-native Python), bukosabino/ta (5.2k stars, 43 indicators). Algorithmic chart-pattern detection (H&S, triangles, double tops) is done via **pivot extraction + geometric constraints** (see `zeta-zetra/chart_patterns`).
- **Published evaluations are sobering:** FinChart-Bench (financial chart VQA) shows frontier models at ~76–84% avg with QA-reasoning stuck near ~60%; a candlestick-forecasting benchmark finds VLMs at ~coin-flip accuracy (~53% best) vs. an XGBoost numeric baseline at ~51%; an independent audit found 1/215 pattern names correct. The practical consensus across repos: **never let vision output be the final signal** — pair it with deterministic detection, require invalidation levels, and calibrate confidence.
- **Datasets for training:** 7,000-image 14-class CNN dataset (`li-dg/stock-pattern-recognition-`), synthetic generator recipes (~10.5k charts), ChartNet (1.7M aligned chart image+code+table+summary+QA — best fine-tuning resource), FinChart-Bench (1,200 real financial charts + 7,016 QA pairs).

---

## 1. TA Libraries and Pattern Detection Repos

### The libraries

| Repo | URL | Stars | What it does |
|---|---|---|---|
| TA-Lib/ta-lib-python | https://github.com/mrjbq7/ta-lib | ~12,274 | Cython wrapper of TA-Lib C. 150+ indicators incl. **~60 `CDL*` candlestick-pattern functions** (CDLENGULFING, CDLHAMMER, CDLDOJI, CDL3BLACKCROWS, CDLMORNINGSTAR…), returning -100/0/100. Groups: Overlap, Momentum, Volume, Cycle, Price Transform, Volatility, **Pattern Recognition**, Statistics. Binary wheels now ship on PyPI. Verified live. |
| bukosabino/ta | https://github.com/bukosabino/ta | ~5,235 | Pure pandas/numpy, 43 indicators for feature engineering (RSI, MACD, BB, ADX, Ichimoku, VWAP, KAMA, STC, Vortex…). MIT. Verified live. |
| peerchemist/finta | https://github.com/peerchemist/finta | ~2,264 | ~80 pandas-native indicators, clean `TA.SMA(ohlc, 42)` API. **Archived** (do not build new on it). Verified live. |
| xgboosted/pandas-ta-classic | https://github.com/xgboosted/pandas-ta-classic | ~449 | Active community fork of twopirllc/pandas-ta. **224 indicators + 62 native CDL patterns = 284 unique**, zero TA-Lib required for patterns. `df.ta.rsi()`, `df.ta.cdl_pattern(name="engulfing")`, `df.ta.strategy("CommonStrategy")`. Optional numba (6–230× speedup), backtesting.py/backtrader/vectorbt integrations, tutorials incl. "Candlestick Pattern Recognition". MIT. Verified live. |
| tulipindicators / cirla/tulipy | (index) | — | C indicator library + Python bindings; used as an oracle in pandas-ta-classic tests. |
| nardew/talipp | (index) | — | Incremental/streaming indicator computation. |
| gauthamastro/wickra | (index) | — | Rust core, 514 indicators, O(1)/tick streaming, multi-language. Newer entrant. |

**Insight for LLM analyst:** `pandas-ta-classic`'s 62 native CDL patterns are the natural **deterministic cross-check** for a vision model's claims (one repo to serve as ground-truth labeler — this is exactly what `claude-trading-skills` does with its own stdlib detector).

### How chart patterns are detected algorithmically (head & shoulders, triangles, etc.)

**`zeta-zetra/chart_patterns`** (verified live — `chart_patterns/head_and_shoulders.py`): the canonical textbook recipe:

1. **Pivot extraction** — find local extrema with left/right window counts at *two resolutions* (`pivot_interval` and a shorter one), so a candle only qualifies as a pivot under both.
2. **Collect pivot maxima/minima over a lookback** (e.g., 60 candles).
3. **Head candidate** = `argmax` of pivot maxima.
4. **Geometric constraints:** head-to-shoulder ratios within tolerance (`head_ratio_before/after ≈ 1.0002`), neckline slope bound (`abs(linregress(troughs).slope) ≤ upper_slmin`), and an ordering constraint (left trough after left-shoulder pivot, right trough before right-shoulder pivot).
5. Returns annotated DataFrame with pattern indexes and values for chart overlay.

**Triangles** (`kcenon/screener_system`, index): fit `np.polyfit` trendlines to swing highs and lows; converging (descending highs + ascending lows) = triangle. **Double tops/bottoms:** two peaks within a tolerance band + trough between.

**Key takeaway:** every algorithmic detector is a pile of hand-tuned tolerances (lookback, pivot window, ratio tolerances, slope bounds). This is precisely what `qrak/llm_trader` deleted (900 lines) after finding that a vision model reading a rendered chart beat programmatic rules at spotting geometry (support wick rejections, wedge breakouts).

---

## 2. LLM + Chart Reading Repos

### Vision-model chart analysis in the wild

**`qrak/llm_trader`** — https://github.com/qrak/llm_trader (verified live, read articles + AGENTS.md)
- Crypto trading bot, 9 months of dev. Phase 1 fed RSI/MACD as text floats to Claude/Gemini → hallucinated trends, lost 4.2%. **Phase 2: Plotly renders a 1080p 4-row chart (candles+SMA, RSI, Volume, CMF/OBV) and feeds the image to Gemini Flash**; 900 lines of hardcoded heuristics deleted. "The visual model spots pattern geometry (support wick rejections, wedge breakouts) far better than programmatic rules."
- Prompt/response architecture (in `src/analyzer/AGENTS.md`): **concise instruction demanding structured JSON**; base64 PNG (4K, 4-row layout) attached; provider `<think>...</think>` sections stripped before JSON parsing; **Pydantic-validated response schema** (`TradingAnalysisResponseModel`); BUY/SELL *requires* entry_price, stop_loss, take_profit, risk_reward_ratio, position_size; parsing fallback = HOLD neutral.
- Anti-hallucination stack around the vision call: deterministic `TrendValidator` (cross-check ADX), `PatternQualityScorer`, EV/Kelly math with min 1.5 R:R, and a **falsification gate** forcing the LLM to state a price invalidation trigger *before* any trade.
- Steal: chart layout spec (4-row stacked image), JSON-schema-forced output, falsification gate, vision-for-geometry + rules-for-numbers split.

**`aadisalhotra/llm-trading-lab`** (index — commit `cd53b8d`): full multimodal pipeline; renders all 21 universe tickers as **one composite candlestick PNG (20-SMA overlay)** per call to bound token cost (matplotlib Agg headless). `BaseAdapter.generate_decision(images=list[bytes])` with per-provider image passing: Anthropic = `image` content blocks (base64), OpenAI = `image_url` data URLs, Gemini = `inline_data` parts, xAI Grok = OpenAI-compatible, DeepSeek = text-only; `vision_capable` flag per model in config. Prompt builder returns `(system, user, version, images)` and includes an **intraday budget context block** (current ET time, market close, run number, trades used vs 30-day cap) so the model doesn't dump its whole trade budget on the first call.

**`HKUDS/vibe-trading` PR #464** (verified live): `analyze_image` tool — sends base64 image + question to chat model, steers LLM to prefer it over OCR for charts. **Adversarial verification**: they tested a chart titled "uptrend" whose data actually trended *down*; the model reported the downtrend — confirming genuine vision, not filename/OCR guessing. Steal: the adversarial self-test as a validation ritual.

**`ArgusOnline01/trading-ai-extension`** (verified live, 0 stars, MIT): Chrome extension + FastAPI; screenshot → GPT-4o/GPT-5 vision for Smart Money Concepts (liquidity, market structure) analysis. Notably: **hybrid vision→reasoning pipeline** (GPT-4o vision → GPT-5 reasoning, ~40% cost saving on multi-question sessions), MD5-hash image cache, `/prompt` endpoint exposing the system prompt, conversational session memory, auto trade logging with R-multiple extraction.

**`sunwasan/technical-analyst-agent`** (verified live, 0 stars): minimal template — yfinance → indicators (SMA20/50, RSI, MACD, volume) → `plot_stock_analysis.py` chart → Gemini vision → trading recommendation (entry/stop/target), plus **backtest loop**: random historical points → generate chart up to that point → Gemini call → 1-month forward trade sim. A complete vision-eval template in one notebook.

**`NeuroTinkerLab/crypto-analyzer-showcase`** (verified live, 3 stars): the *text* alternative — fetches Binance/Deribit, computes indicators + candlestick patterns + Fibonacci + multi-timeframe stats, emits a JSON report "designed to be parsed and interpreted by an LLM", with a full example system prompt (`LLM_SYSTEM_PROMPT_INSTRUCTIONS.md`) casting the LLM as "Algorithmic Multi-Timeframe Financial Analyst".

**`liyuan1234/image_agent`** (index): general-purpose screen/window capture → ChatGPT on visual change (e.g., a new 1-min candle) for live chart guidance.

### Prompt engineering strategies (the steal-ables)

From `jazzi57/claude-trading-skills` (SKILL.md, verified live — **the single best prompt artifact found**):

1. **Load a knowledge base before reading**: the skill makes the agent read `candlestick_pattern_catalog.md` (pattern geometry + reliability priors) and `signal_classification_framework.md` (trend/location/confirmation → signal) *before* looking at the chart. → Pre-pend your analyst with a compact pattern catalog with geometry definitions and base rates.
2. **Two-pass read**: (a) vision reading against the catalog, focusing on the **rightmost/most recent 1–3 candles**; (b) deterministic rule-based detector on the same OHLCV as an objective baseline (`detect_candlestick_patterns.py`, stdlib-only).
3. **Reconciliation rule**: if vision and rules agree → combined confidence; if they disagree → investigate explicitly (detector misses location/volume nuance; the eye misjudges body/shadow ratios), explain the discrepancy, **lower confidence**.
4. **Core principles** (verbatim from the skill): *"Patterns are hypotheses; location and confirmation make them signals — never call a direction from candle shape alone."* *"Latest bar is decisive."* *"State confidence honestly."* *"Always frame risk — every actionable signal includes an entry trigger, invalidation level, and target."*
5. **Quality standards**: cite actual price levels for entry/stop/target (never vague descriptions); report patterns that *conflict* with the headline call; ambiguous/low-res/volume-less charts → lower confidence stated plainly; every report ends with a disclaimer.
6. Report template saved to `reports/[SYMBOL]_pattern_scan_[YYYY-MM-DD].md` (and optional `.json`).

From `qrak/llm_trader` (verified live): concise system instruction + forced JSON schema + Pydantic validation + deterministic gates (ADX trend check, EV/Kelly, falsification gate) around the vision call. From `llm-trading-lab`: budget-awareness context block (time remaining, trades remaining). From `vibe-trading`: adversarial self-tests for genuine vision.

### Fine-tuning approaches

- **ChartNet (MIT-IBM)**: 1.7M synthetic charts generated by a **code-guided synthesis pipeline** — each sample has 5 aligned components (plotting code, rendered image, data table, summary, QA with reasoning), plus 94,643 human-verified charts and 2,000 human-verified test samples; 24 chart types, 6 plotting libraries. Fine-tuned Granite 4.0 3B Vision reportedly beats GPT-4o on chart tasks. Recipe to steal: generate aligned image+table+QA triples from *code* so supervision is exact.
- **FinGPT (AI4Finance-Foundation)**: LoRA/QLoRA domain fine-tuning on financial text; RLSP (reinforcement learning from stock prices). Text-only — relevant for the analyst's language side, not vision.
- **FinChart-Multimodal (CVPR 2026)**: 100,000 financial charts with pixel-level aligned OHLCV — announced, to be released on HF/GitHub; not yet available.

---

## 3. Trading Agent Repos With Chart Vision

| Repo | URL | How charts are fed | Notable mechanism |
|---|---|---|---|
| qrak/llm_trader | https://github.com/qrak/llm_trader | Plotly 1080p 4-row chart (SMA, RSI, volume, CMF/OBV) → Gemini Flash, base64 PNG | Vision for geometry; deterministic rules for numbers; EV/Kelly gates; falsification gate; ChromaDB memory of past trades; surprise ratio |
| aadisalhotra/llm-trading-lab | https://github.com/aadisalhotra/llm-trading-lab | One composite PNG per call (all tickers, 20-SMA overlay) → vision-capable adapters | Per-provider image formats (Anthropic/OpenAI/Gemini/Grok); vision_capable config flag; intraday budget context block |
| alex-jb/orallexa-ai-trading-agent | https://github.com/alex-jb/orallexa-ai-trading-agent | K-line chart attached to Quant Researcher on a sampled fraction of calls | `ORALLEXA_MULTIMODAL_SAMPLE` env + nightly **"Multimodal Lift — Vision vs Text Eval"**: vision-vs-text A/B rolled into a ship/reject verdict (vision costs ~5×/call) |
| HKUDS/vibe-trading | https://github.com/HKUDS/Vibe-Trading | `analyze_image` tool: base64 data URL + question via `ChatLLM().chat(...)` | Adversarial self-test (misleading title vs data) to verify genuine vision |
| ArgusOnline01/trading-ai-extension | https://github.com/ArgusOnline01/trading-ai-extension | TradingView screenshot → GPT-4o/GPT-5 vision | Hybrid vision→reasoning (4o vision → GPT-5 reasoning, −40% cost); session memory |
| brandononchain/opentrade | https://github.com/brandononchain/opentrade | Explicitly *anti*-screenshot: reads indicator values via Chrome DevTools Protocol into tool-use agent loop | Contrast case: argues screenshot analyzers "get a vague paragraph back" |
| sunwasan/technical-analyst-agent | https://github.com/sunwasan/technical-analyst-agent | matplotlib/plotly chart PNG → Gemini vision | Random-point backtest loop for evaluation |
| NeuroTinkerLab/crypto-analyzer-showcase | https://github.com/NeuroTinkerLab/crypto-analyzer-showcase | Text-only (JSON report → LLM) | Example system prompt for "Algorithmic Multi-Timeframe Financial Analyst" |

### Published evaluations of LLM chart-reading accuracy (caveats noted)

- **FinChart-Bench** (1,200 real financial charts, 7,016 QA): GPT-4o avg 76.6%, GPT-4.1 80.9%, o3 83.9%, Claude Sonnet 4 84.3%, Gemini 2.5 Pro 83.7%; open-source Qwen2.5-VL 72.2%, Mistral 3.1 74.4%. Open-ended reasoning QA stalls ~60% for *all* models; spatial reasoning and instruction-following are the weak spots. (index-level numbers)
- **"Do VLMs Truly 'Read' Candlesticks?"** (arXiv 2604.12659, 193,524 multi-scale candlestick charts): best VLM ~53% (Claude-Sonnet-4-5 thinking 53.48%, Gemini-2.5-Pro 52.44%) vs XGBoost numeric baseline 50.87%, GPT-4o 49.40%. "Most VLMs perform well only under persistent uptrend or downtrend conditions." No clean image-vs-numeric ablation. (index-level, secondhand summary — cite with caveat)
- **Independent audit** (roman-rr gist, April 2026, cited in an index doc): 4 models, 40 verified crypto signals, 215 calls → direction 51.4–57.1% (all CIs include 50%), pattern-name accuracy **1/215**; Gemini 3 Flash had a 90pp long/short bias gap. Conclusion quoted: "no frontier vision LLM we tested is capable of reliable directional chart-pattern analysis." (index-level, secondhand)
- **"AI Trading: Evaluating LLMs for Technical Market Analysis"**: candlestick pattern recognition from *OHLCV text sequences*: FinGPT 81.5%, GPT-4 Turbo 80.5%, Claude 3 Opus 77.2%, Gemini 1.5 Pro 74.5%, Llama 3 70B 66.0%. (index-level; paper labels results simulated/illustrative)
- **qrak/llm_trader**: qualitative — deleting 900 lines of heuristics and switching to chart vision reduced hallucinated trends after a −4.2% phase. (anecdotal, builder's own report)
- **EncQA (apple/ml-encqa)**: VLMs read **position-aligned-to-axes** best, length/shape moderate, area/quantitative-color worst — a candlestick is "position-non-aligned plus length" (mid-tier encoding). Useful prior for chart design: gridlines and aligned reference lines help models read values.

---

## 4. Chart Pattern Datasets

| Dataset | URL | Size / format | Notes |
|---|---|---|---|
| li-dg/stock-pattern-recognition- | https://github.com/li-dg/stock-pattern-recognition- | **7,000 images**, 500/class, 14 classes (8 candlestick + H&S, double top/bottom, cup & handle, asc/desc triangle, falling/rising wedge), folder-per-class | Volume-aware confidence filtering, balanced + augmented; custom CNN ~85% |
| sujalgour/ece-176_finalproject | https://github.com/sujalgour/ece-176_finalproject | **10,500 synthetic** candlestick charts (1,500/class, 7 classes incl. no-pattern) | Custom CNN + fine-tuned ResNet-18, Grad-CAM, backtest on real S&P 500; tests synthetic→real transfer |
| harshilpanchal11/stock-pattern-recognition | https://github.com/harshilpanchal11/stock-pattern-recognition | Hybrid: real yfinance charts (weak-labeled) + synthetic parametric charts | EfficientNet/ConvNeXt/YOLOv8; mplfinance rendering |
| kcenon/screener_system | https://github.com/kcenon/screener_system | Synthetic labeled generator (`build_labeled_dataset.py`) + ChartImageGenerator | Algorithmic detector + ResNet50 |
| charvi99/stockanalyzer | https://github.com/charvi99/stockanalyzer | Labeling UI: detect 40 candle + 12 chart patterns, human confirm/reject → export (~10k patterns from 200 stocks × 5Y) | Human-in-the-loop dataset builder |
| ChartNet (MIT-IBM) | https://huggingface.co/datasets/ibm-granite/ChartNet (repo: https://github.com/ibm-granite/granite-vision-models) | **1.7M synthetic** + 94,643 human-verified + 2,000 test; 24 chart types, 6 libs; image+code+table+summary+QA aligned | Best fine-tuning resource; Granite 4.0 3B Vision beats GPT-4o per IBM/MIT |
| FinChart-Bench | https://github.com/Tizzzzy/FinChart-Bench / HF Tizzzzy/FinChart-Bench | **1,200 real financial charts**, 7,016 QA (TF/MC/reasoning, single-token answers) | First finance-specific VLM chart benchmark |
| FinChart-Multimodal (CVPR 2026) | (promised) | 100,000 financial charts with pixel-aligned OHLCV | Announced, not yet released |

**Gap:** no public dataset pairs *annotated technical-analysis prose* (the kind of writeup a human analyst produces) with charts — every repo either has images+labels (CNN path) or QA pairs (VQA path). Generating analyst-style rationales via code-guided synthesis (ChartNet-style) is the obvious build.

---

## 5. Educational Repos (TA as code)

- **vnegi10/candlestick_pattern_analysis** (https://github.com/vnegi10/candlestick_pattern_analysis): one notebook — CoinGecko OHLC → pure-Python SMA/EMA/BB/RSI/MACD + bullish-engulfing detection → Plotly multi-panel charts. Best minimal reference for the chart-*rendering* side of the pipeline.
- **olimiemma/ema-and-ma-crossover…** (https://github.com/olimiemma/ema-and-ma-crossover-analysis-with-trade-visualization-spy-weekly-candlestick-chart-with-ma-ema-cros): EMA/MA crossover strategy on SPY with Plotly trade visualization — strategy-implementation template.
- **rukminimukherjee1998/heikin-ashi-bollinger-strategy** (https://github.com/rukminimukherjee1998/heikin-ashi-bollinger-strategy): Heikin-Ashi + Bollinger Bands strategy + backtest metrics.
- **kamal-manick/learn-options-trading** (https://github.com/kamal-manick/learn-options-trading): Claude Code skill that auto-generates a full course (SVG candlestick diagrams with green/red/neutral conventions, mermaid flowcharts) — pattern for AI-generated analyst curricula.
- **miladtm94/investment-portfolio-tracker** (https://github.com/miladtm94/investment-portfolio-tracker): `AI_ANALYSIS_PLAN.md` documents a full multi-agent analyst architecture (3 specialist agents → synthesis agent, rule-based pattern detection, outcome tracking DB).
- **rlancaster243/quant_agent**: multi-agent design doc (IndicatorAgent → pandas_ta, PatternAgent → chart images, TrendAgent, Groq DecisionAgent → JSON).

---

## Recommended architecture (synthesized from the repos)

1. **Chart rendering** (matplotlib/Plotly, `mplfinance`): one composite image per decision — candles + SMA overlays + RSI/volume panels; 1080p-ish; aligned gridlines (EncQA prior). Composite single image bounds token cost (`llm-trading-lab`).
2. **Prompt**: system prompt with pattern catalog (geometry + reliability priors, `claude-trading-skills`) + budget context (time/trades remaining, `llm-trading-lab`); user instruction demanding **structured JSON** (schema-validated, `llm_trader`) including entry/trigger, invalidation, target, R:R, confidence.
3. **Cross-check**: deterministic detector (TA-Lib CDL* or pandas-ta-classic `cdl_pattern`, plus pivot-geometry code à la `zeta-zetra/chart_patterns`) run on the same OHLCV; vision/rules reconciliation with lowered confidence on disagreement.
4. **Gates**: falsification gate (model must state invalidation price), trend validator (ADX), EV/Kelly sizing, min R:R; fallback HOLD on parse failure.
5. **Evaluation**: sample-based vision-vs-text A/B (orallexa's "Multimodal Lift" pattern); adversarial self-tests (mislabeled-title charts); random-point historical backtest loop (sunwasan template).
6. **Training data**: code-guided synthesis à la ChartNet (aligned chart image + OHLCV table + analyst rationale + QA) — no public dataset does this for TA prose yet.

---

## Could not verify / open questions

- Star counts for `bukosabino/ta` (5,235) and others marked "verified live" are from a fetch on 2026-10-07; treat as approximate. Some repos marked "index" were never opened live — their descriptions come from search-index crawls (dated crawls shown) and should be re-verified before being cited as primary evidence.
- Benchmark numbers (FinChart-Bench scores, candlestick-VLM accuracies, 1/215 audit) are from search-index/arxiv text, not from re-running any evaluation; the candlestick paper's exact figures came secondhand via a market-scout doc — cite with caveats.
- FinChart-Multimodal (100k aligned charts) is announced but not released; verify before planning on it.
- Several repos (`chart_patterns`, `TradingPatternScanner`, orallexa, llm-trading-lab, TradingPatternScanner) were not inspected at the code level; their described mechanics come from READMEs/commits, not line-by-line review.
- Missing parameter: none blocking — the mission was scope-complete.

## Sources

(All URLs copied verbatim from tool results; read 2026-10-07.)

- https://github.com/mrjbq7/ta-lib — verified live (12,274 stars, CDL pattern functions, binary wheels) — notes/ta-libs.md
- https://github.com/bukosabino/ta — verified live (5,235 stars, 43 indicators) — notes/ta-libs.md
- https://github.com/peerchemist/finta — verified live (2,264 stars, archived, ~80 indicators) — notes/ta-libs.md
- https://github.com/xgboosted/pandas-ta-classic — verified live (449 stars, 284 indicators+patterns, native CDL) — notes/ta-libs.md
- https://github.com/zeta-zetra/chart_patterns/blob/main/chart_patterns/head_and_shoulders.py — verified live (pivot+geometry detection code) — notes/pattern-detection.md
- https://github.com/qrak/llm_trader/blob/HEAD/articles/architecture_and_journey.md — verified live (chart-vision phase, 1080p Plotly → Gemini Flash) — notes/llm-vision-repos.md
- https://github.com/qrak/llm_trader/blob/HEAD/src/analyzer/AGENTS.md — index (JSON prompt strategy, falsification gate, Numba pattern engine) — notes/llm-vision-repos.md
- https://github.com/jazzi57/claude-trading-skills/blob/HEAD/skills/chart-pattern-scanner/SKILL.md — verified live (vision+rules cross-check, reconciliation protocol) — notes/llm-vision-repos.md
- https://github.com/HKUDS/Vibe-Trading/pull/464 — verified live (analyze_image tool, adversarial vision test) — notes/llm-vision-repos.md
- https://github.com/ArgusOnline01/trading-ai-extension — verified live (GPT-4o/5 SMC analysis, hybrid vision→reasoning) — notes/llm-vision-repos.md
- https://github.com/sunwasan/technical-analyst-agent — verified live (Gemini vision + backtest loop) — notes/llm-vision-repos.md
- https://github.com/NeuroTinkerLab/crypto-analyzer-showcase — verified live (JSON-for-LLM text pipeline, system prompt file) — notes/llm-vision-repos.md
- https://github.com/aadisalhotra/llm-trading-lab/commit/cd53b8d113e7d13ec7d3926ec2a3d9448ef5d240 — index (multimodal adapters, composite chart, budget context) — notes/llm-vision-repos.md
- https://github.com/alex-jb/orallexa-ai-trading-agent — index (multimodal sampling + vision-vs-text eval) — notes/llm-vision-repos.md
- https://github.com/brandononchain/opentrade/blob/HEAD/ABOUT.md — index (CDP-based anti-screenshot approach) — notes/llm-vision-repos.md
- https://github.com/white07S/TradingPatternScanner — index (pip pattern scanner) — notes/pattern-detection.md
- https://github.com/nodalytics/till_infinity — index (placebo-controlled pattern backtest, cautionary) — notes/pattern-detection.md
- https://github.com/kcenon/screener_system — index (algorithmic detector + synthetic dataset gen + ResNet50) — notes/pattern-detection.md
- https://github.com/li-dg/stock-pattern-recognition- — index (7,000 images, 14 classes) — notes/datasets-benchmarks.md
- https://github.com/sujalgour/ece-176_finalproject — index (10,500 synthetic charts) — notes/datasets-benchmarks.md
- https://github.com/harshilpanchal11/stock-pattern-recognition — index (hybrid real+synthetic, YOLOv8) — notes/datasets-benchmarks.md
- https://github.com/charvi99/stockanalyzer — index (labeling UI → ML dataset) — notes/datasets-benchmarks.md
- https://github.com/movestarts/chartscanai — index (YOLOv8 Buy/Sell detector) — notes/datasets-benchmarks.md
- https://github.com/ibm-granite/granite-vision-models + https://huggingface.co/datasets/ibm-granite/ChartNet — index (ChartNet 1.7M aligned samples) — notes/datasets-benchmarks.md
- https://github.com/Tizzzzy/FinChart-Bench — index (1,200 real charts, 7,016 QA) — notes/datasets-benchmarks.md
- https://arxiv.org/abs/2507.14823 — index (FinChart-Bench paper) — notes/datasets-benchmarks.md
- https://arxiv.org/pdf/2604.12659v1 — index ("Do VLMs Truly Read Candlesticks?") — notes/datasets-benchmarks.md
- https://arxiv.org/pdf/2603.27064v1 — index (ChartNet paper) — notes/datasets-benchmarks.md
- https://arxiv.org/pdf/2311.16483 — index (ChartLlama) — notes/datasets-benchmarks.md
- https://github.com/vis-nlp/ChartQA — index (general chart QA) — notes/datasets-benchmarks.md
- https://github.com/apple/ml-encqa — index (visual encoding hierarchy) — section 3
- https://github.com/vnegi10/candlestick_pattern_analysis — index (notebook TA toolkit) — notes/educational.md
- https://github.com/kamal-manick/learn-options-trading — index (AI-generated course skill) — notes/educational.md
- https://github.com/miladtm94/investment-portfolio-tracker — index (multi-agent analyst plan) — notes/educational.md
- https://github.com/AI4Finance-Foundation/FinGPT — index (FinGPT fine-tuning framework) — notes/llm-vision-repos.md
- https://github.com/z-quant-research-lab/awesome-quant — index (TA library survey) — notes/ta-libs.md

No page instructions conflicted with the mission; nothing was skipped on those grounds.
