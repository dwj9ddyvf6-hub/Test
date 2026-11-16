# Pattern detection repos — notes (read 2026-10-07)

1. zeta-zetra/chart_patterns — https://github.com/zeta-zetra/chart_patterns — algorithmic chart-pattern detection in Python. Algorithm: find pivot points (left_count/right_count window extrema, two resolutions), collect pivot maxima/minima over lookback (60), pick head = argmax of maxima, enforce head/shoulder ratio constraints (head_ratio_before/after ~1.0002), neckline slope constraint via scipy.stats.linregress on minima (abs(slope) <= upper_slmin), and ordering constraint (left trough after left shoulder pivot, right trough before right shoulder pivot). Also contains triangle/channel detectors presumably. Technique: pivot extraction + geometric ratio constraints + linear regression slope checks. Verified live (head_and_shoulders.py source).

2. white07S/TradingPatternScanner — https://github.com/white07S/TradingPatternScanner — pip package `tradingpattern`. Detects HS, inverse HS, multiple tops/bottoms, horizontal S/R, ascending/descending triangles, wedges, channels, double tops/bottoms, trendline S/R, HH/LL. Heatmap output with abbreviations. Index-level (not verified live).

3. TA-Lib CDL* functions: ~60 single/double/triple candle patterns as Cython functions returning -100/0/100. Industry standard for candlestick pattern labeling.

4. nodalytics/till_infinity — https://github.com/nodalytics/till_infinity — research notebook + Python harness (patterns.py): algorithmic pattern detection paired with placebo-controlled backtest. Key cautionary finding: head-and-shoulders/double-top edges (~53% win on gold) collapsed vs placebo; only inverse H&S barely significant; patterns beat random entry of same geometry by 1-2pp but can't clear breakevens. Honest warning about pattern overfitting. Index-level.

5. kcenon/screener_system — https://github.com/kcenon/screener_system — algorithmic PatternDetector (H&S, double top, triangle via polyfit trendline slopes on swing highs/lows: converging highs-descending/lows-ascending = triangle), ChartImageGenerator for synthetic chart rendering, ResNet50 transfer-learning CNN, build_labeled_dataset.py for synthetic labeled datasets. Index-level.

6. CNN-based pattern recognizers (see datasets notes): li-dg/stock-pattern-recognition- (7,000 images, 14 classes, ~85% acc), sujalgour/ece-176 (10,500 synthetic charts, CNN+ResNet18, Grad-CAM), harshilpanchal11/stock-pattern-recognition (EfficientNet/ConvNeXt/YOLOv8 on live charts), movestarts/chartscanai (YOLOv8, Buy/Sell 2-class object detection on candlestick images).
