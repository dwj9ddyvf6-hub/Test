# Chart pattern datasets & benchmarks — notes (read 2026-10-07)

1. li-dg/stock-pattern-recognition- — https://github.com/li-dg/stock-pattern-recognition- — 7,000 chart images (500/class, 14 classes: 8 candlestick + 6 chart patterns incl. H&S, double top/bottom, cup & handle, ascending/descending triangle, falling/rising wedge). CNN ~85% on confidence-filtered, volume-aware, balanced dataset. Folder-per-class images. Index-level.

2. sujalgour/ece-176_finalproject — https://github.com/sujalgour/ece-176_finalproject — 10,500 synthetic candlestick charts (1,500/class, 7 classes incl. no-pattern random walk), custom 3-layer CNN + ResNet-18, Grad-CAM, backtest of detections on real S&P500. Synthetic→real transfer question. Index-level.

3. charvi99/stockanalyzer — https://github.com/charvi99/stockanalyzer — labeling UI workflow: detect 40 candlestick + 12 chart patterns on 90-day windows, confirm/reject to build ML training set (~10,000 patterns from 200 stocks x 5 years), export. Relevant as labeling-tool pattern. Index-level.

4. harshilpanchal11/stock-pattern-recognition — https://github.com/harshilpanchal11/stock-pattern-recognition — hybrid: real yfinance charts (weak-labeled) + synthetic parametric charts; EfficientNet-B0/V2-S/ConvNeXt-Tiny + YOLOv8. Index-level.

5. FinChart-Bench — https://github.com/Tizzzzy/FinChart-Bench / HF dataset Tizzzzy/FinChart-Bench — first financial-chart LVLM benchmark: 1,200 real charts (Bloomberg News, corporate slides, 2015-2024), 7,016 QA (2,383 TF + 2,349 MC + 2,284 reasoning QA single-token answers). 25 LVLMs evaluated. Key numbers (index-level, from arxiv/overfitted): GPT-4o avg 76.62, GPT-4.1 80.88, o3 83.89, o4-mini 83.53, Claude Sonnet 4 84.32, Gemini 2.5 Pro 83.73, Qwen2.5-VL 72.16, Mistral 3.1 74.37. Open-ended QA hard for all (~60% top). Findings: narrowing open/closed gap; spatial reasoning weak; LVLMs unreliable as auto-evaluators. Index-level.

6. ChartNet (MIT-IBM) — https://github.com/ibm-granite/granite-vision-models, dataset https://huggingface.co/datasets/ibm-granite/ChartNet — 1.7M synthetic charts (code-guided synthesis: each sample = plotting code + image + data table + summary + QA+reasoning), 94,643 human-verified charts, 2,000 human-verified test, 24 chart types, 6 plotting libraries. Fine-tuned Granite 4.0 3B Vision beats GPT-4o on chart tasks. Technique to steal: code-guided synthesis — aligned image/data-table/summary/QA pairs generated together. Index-level.

7. "Do VLMs Truly 'Read' Candlesticks?" — arXiv 2604.12659 — multi-scale candlestick benchmark: 193,524 charts (96,770 daily + 96,754 weekly), 300 HS300 + 500 S&P500, 2015-2025. Results (via index aggregator, not verified on paper): Claude-Sonnet-4-5 thinking 53.48%, Gemini-2.5-Pro 52.44%, XGBoost numeric baseline 50.87%, GPT-4o 49.40%. "Most VLMs perform well only under persistent uptrend/downtrend." Independent audit (roman-rr gist, April 2026): 40 crypto signals, 215 calls, direction 51.4-57.1%, pattern-name accuracy 1/215, "no frontier vision LLM we tested is capable of reliable directional chart-pattern analysis." CAUTION: these numbers are secondhand (from a market-scout doc), cite with caveat. No clean image-vs-numeric ablation. Index-level.

8. "AI Trading: Evaluating Large Language Models for Technical Market Analysis" — arXiv (index-level) — candlestick pattern recognition from OHLCV text sequences: GPT-4 Turbo 80.5%, Claude 3 Opus 77.2%, Gemini 1.5 Pro 74.5%, FinGPT 81.5%, Llama 3 70B 66.0% (labeled "simulated/illustrative data" in paper). Domain fine-tuning helps on structured data. Index-level.

9. ChartQA (vis-nlp/ChartQA) — https://github.com/vis-nlp/ChartQA — general chart QA benchmark (21.9K charts), not finance. UniChart/ChartInstruct/ChartGemma. Index-level.

10. FinChart-Multimodal (CVPR 2026) — 100,000 financial charts with pixel-level aligned OHLCV time series; systematic visual-numerical alignment; generation pipeline to be released on GitHub, data on HF. "Promised" release — flag as not yet available.
