# TA libraries — notes (read 2026-10-07)

1. TA-Lib/ta-lib-python — https://github.com/mrjbq7/ta-lib — 12,274 stars, 2,003 forks, BSD-2. ISC (redirects from mrjbq7/ta-lib). Cython wrapper of TA-Lib C. 150+ indicators incl. CDL candlestick pattern recognition functions (the CDL* pattern functions, e.g. CDLENGULFING, CDLHAMMER, CDLDOJI — ~60). Groups: Overlap Studies, Momentum, Volume, Cycle, Price Transform, Volatility, Pattern Recognition, Statistics. Now ships binary wheels (PyPI TA-Lib 0.4.x–0.8.x). Verified live.

2. bukosabino/ta — https://github.com/bukosabino/ta — 5,235 stars, MIT. Pure pandas/numpy, 43 indicators in 5 classes (Volume, Volatility, Trend, Momentum, Others): RSI, MACD, BB, ADX, Ichimoku, VWAP, STC, KAMA etc. Feature-engineering oriented. Verified live.

3. peerchemist/finta — https://github.com/peerchemist/finta — 2,264 stars, LGPL-3.0, ARCHIVED. ~80 indicators (SMA/EMA/DEMA/TEMA, KAMA, FRAMA, ZLEMA, VW_MACD, SQZMI, ICHIMOKU...). API: TA.SMA(ohlc, 42). Verified live.

4. xgboosted/pandas-ta-classic — https://github.com/xgboosted/pandas-ta-classic — 449 stars, MIT, active (1,460 commits). Community fork of twopirllc/pandas-ta. 224 indicators + 62 native CDL patterns = 284 unique; CDL patterns never use TA-Lib (native Python). Usage: df.ta.rsi(), df.ta.cdl_pattern(name="engulfing"), df.ta.strategy("CommonStrategy"). Optional numba 6-230x speedups. Verified live.

5. Other libraries per awesome-quant (index): talipp (incremental), Tulipy (C bindings), tulipindicators, bta-lib, QuantWave (Polars-native + agent skill), wickra (Rust, 514 indicators, O(1) streaming). Not verified individually — treat as index-level.
