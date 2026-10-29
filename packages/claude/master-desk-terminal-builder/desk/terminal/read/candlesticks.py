"""Candlestick patterns, counted only where they land on a key level (the owner's line: "50 candlestick detectors and
gap ups and downs, counted only when they land on a key level").

The detectors are the study's (2026-10-19, scratchpad lab/src/candles/candles_lib.py): TA-Lib's 61 candlestick functions
re-implemented in numpy from the C source's rules and its default candle settings (ta_global.c), and Nison's tweezers
in TA-Lib's terms; cross-checked bar for bar against TA-Lib-style scalar loops on 2,117,892 bar values (40 names, 21
detectors, all equal), self-tested on 110 hand-built cases and proven point in time on 442 name-sessions x 144 columns.
They are copied here unchanged; every number inside them is TA-Lib's published default (the tweezer's five-session
decline is the study's, see d_tweezer).

Every read checks all 62 named patterns on its last session. Six of them the read's own candle facts already read
(candles.py: the hammer and hanging man, the shooting star and inverted hammer, the engulfing day, the doji): those stay
theirs. Any other is counted only
  - on a key level: its low (a bullish pattern; its high, a bearish one; either, an indecision candle) within the
    read's level distance of a floor (a ceiling) of two or more kinds, known before the pattern's first session;
  - after the move it reverses (a reversal; a continuation: the move it continues) by the read's own rule;
  - once per session: the most specific such pattern (the most candles, then the rarest in the study's data), and
    none when the read's own candle facts or a gap they type already read those sessions with a side.
It joins the session's one kind of evidence (call.FAMILY: "Candles" is the session), never a kind of its own."""
import dataclasses
from collections import namedtuple

import numpy as np

from . import words as W
from .core import Fact, atr_words
from .levels import Area

# --------------------------------------------------------------------------------------- TA-Lib's candle settings
# TA-Lib's defaults (ta_global.c, TA_CandleDefaultSettings): (range measured, trailing period, factor). The average for
# candle k is over the `period` candles before k; a period of 0 compares with candle k's own real body; a Shadows
# average is halved. Published values, none chosen here.
SETTINGS = {
    "BL": ("rb", 10, 1.0),     # BodyLong: body > average body of the 10 prior candles
    "BVL": ("rb", 10, 3.0),    # BodyVeryLong (unused by the defaults of the 61 functions; kept as TA-Lib has it)
    "BS": ("rb", 10, 1.0),     # BodyShort: body < average body of the 10 prior candles
    "BD": ("hl", 10, 0.1),     # BodyDoji: body <= 10% of the average high-low range of the 10 prior candles
    "SL": ("rb", 0, 1.0),      # ShadowLong: shadow > the candle's own body
    "SVL": ("rb", 0, 2.0),     # ShadowVeryLong: shadow > twice the candle's own body
    "SS": ("sh", 10, 1.0),     # ShadowShort: shadow < half the average shadow sum of the 10 prior candles
    "SVS": ("hl", 10, 0.1),    # ShadowVeryShort: shadow < 10% of the average high-low range of the 10 prior candles
    "NE": ("hl", 5, 0.2),      # Near: <= 20% of the average range of the 5 prior candles
    "FA": ("hl", 5, 0.6),      # Far: >= 60% of it
    "EQ": ("hl", 5, 0.05),     # Equal: <= 5% of it
}
HIKKAKE_REACH = 3              # TA-Lib's hikkake: a confirmation within 3 bars of the pattern bar (ta_CDLHIKKAKE.c)


def _shift(x, k):
    """x[i-k] at i (NaN before)"""
    if k == 0:
        return x
    out = np.full(len(x), np.nan)
    if k < len(x):
        out[k:] = x[:-k]
    return out


def _rollsum(x, n):
    """sum of x[i-n+1..i], added in order (a bar's value never depends on how long the array is); NaN until n"""
    out = np.full(len(x), np.nan)
    m = len(x) - n + 1
    if m > 0:
        s = x[0:m].copy()
        for k in range(1, n):
            s += x[k:k + m]
        out[n - 1:] = s
    return out


class _K:
    """candle parts and TA-Lib averages, with shifted views: K.o(k) is the open of candle i-k at every i"""

    def __init__(self, o, h, l, c):
        self.base = {"o": o, "h": h, "l": l, "c": c}
        mx, mn = np.maximum(o, c), np.minimum(o, c)
        self.base.update(rb=np.abs(c - o), hl=h - l, us=h - mx, ls=mn - l, mx=mx, mn=mn,
                         col=np.where(c >= o, 1.0, -1.0))
        rng = {"rb": self.base["rb"], "hl": self.base["hl"], "sh": self.base["us"] + self.base["ls"]}
        for s, (rt, n, f) in SETTINGS.items():
            if n == 0:
                a = f * rng[rt]
            else:
                a = f * (_shift(_rollsum(rng[rt], n), 1) / n)
                if rt == "sh":
                    a = a / 2.0
            self.base["a" + s] = a
        self._c = {}

    def _g(self, key, k):
        kk = (key, k)
        if kk not in self._c:
            self._c[kk] = _shift(self.base[key], k)
        return self._c[kk]

    def o(self, k=0): return self._g("o", k)
    def h(self, k=0): return self._g("h", k)
    def l(self, k=0): return self._g("l", k)
    def c(self, k=0): return self._g("c", k)
    def rb(self, k=0): return self._g("rb", k)
    def hl(self, k=0): return self._g("hl", k)
    def us(self, k=0): return self._g("us", k)
    def ls(self, k=0): return self._g("ls", k)
    def mx(self, k=0): return self._g("mx", k)
    def mn(self, k=0): return self._g("mn", k)
    def col(self, k=0): return self._g("col", k)
    def a(self, s, k=0): return self._g("a" + s, k)
    # TA_REALBODYGAPUP(i-x, i-y) etc.: candle i-x against candle i-y
    def rgu(self, x, y): return self.mn(x) > self.mx(y)
    def rgd(self, x, y): return self.mx(x) < self.mn(y)
    def gu(self, x, y): return self.l(x) > self.h(y)
    def gd(self, x, y): return self.h(x) < self.l(y)


Wh = np.where


# ------------------------------------------------------------------------------- the detectors (the study's, as is)
def d_2crows(K):
    return Wh((K.col(2) == 1) & (K.rb(2) > K.a("BL", 2)) & (K.col(1) == -1) & K.rgu(1, 2) & (K.col(0) == -1)
              & (K.o(0) < K.o(1)) & (K.o(0) > K.c(1)) & (K.c(0) > K.o(2)) & (K.c(0) < K.c(2)), -1.0, 0.0)


def d_3blackcrows(K):
    return Wh((K.col(3) == 1) & (K.col(2) == -1) & (K.ls(2) < K.a("SVS", 2)) & (K.col(1) == -1)
              & (K.ls(1) < K.a("SVS", 1)) & (K.col(0) == -1) & (K.ls(0) < K.a("SVS", 0))
              & (K.o(1) < K.o(2)) & (K.o(1) > K.c(2)) & (K.o(0) < K.o(1)) & (K.o(0) > K.c(1))
              & (K.h(3) > K.c(2)) & (K.c(2) > K.c(1)) & (K.c(1) > K.c(0)), -1.0, 0.0)


def d_3inside(K):
    cond = ((K.rb(2) > K.a("BL", 2)) & (K.rb(1) <= K.a("BS", 1)) & (K.mx(1) < K.mx(2)) & (K.mn(1) > K.mn(2))
            & (((K.col(2) == 1) & (K.col(0) == -1) & (K.c(0) < K.o(2)))
               | ((K.col(2) == -1) & (K.col(0) == 1) & (K.c(0) > K.o(2)))))
    return Wh(cond, -K.col(2), 0.0)


def d_3linestrike(K):
    cond = ((K.col(3) == K.col(2)) & (K.col(2) == K.col(1)) & (K.col(0) == -K.col(1))
            & (K.o(2) >= K.mn(3) - K.a("NE", 3)) & (K.o(2) <= K.mx(3) + K.a("NE", 3))
            & (K.o(1) >= K.mn(2) - K.a("NE", 2)) & (K.o(1) <= K.mx(2) + K.a("NE", 2))
            & (((K.col(1) == 1) & (K.c(1) > K.c(2)) & (K.c(2) > K.c(3)) & (K.o(0) > K.c(1)) & (K.c(0) < K.o(3)))
               | ((K.col(1) == -1) & (K.c(1) < K.c(2)) & (K.c(2) < K.c(3)) & (K.o(0) < K.c(1))
                  & (K.c(0) > K.o(3)))))
    return Wh(cond, K.col(1), 0.0)


def d_3outside(K):
    cond = (((K.col(1) == 1) & (K.col(2) == -1) & (K.c(1) > K.o(2)) & (K.o(1) < K.c(2)) & (K.c(0) > K.c(1)))
            | ((K.col(1) == -1) & (K.col(2) == 1) & (K.o(1) > K.c(2)) & (K.c(1) < K.o(2)) & (K.c(0) < K.c(1))))
    return Wh(cond, K.col(1), 0.0)


def d_3starsinsouth(K):
    cond = ((K.col(2) == -1) & (K.col(1) == -1) & (K.col(0) == -1)
            & (K.rb(2) > K.a("BL", 2)) & (K.ls(2) > K.a("SL", 2))
            & (K.rb(1) < K.rb(2)) & (K.o(1) > K.c(2)) & (K.o(1) <= K.h(2)) & (K.l(1) < K.c(2))
            & (K.l(1) >= K.l(2)) & (K.ls(1) > K.a("SVS", 1))
            & (K.rb(0) < K.a("BS", 0)) & (K.ls(0) < K.a("SVS", 0)) & (K.us(0) < K.a("SVS", 0))
            & (K.l(0) > K.l(1)) & (K.h(0) < K.h(1)))
    return Wh(cond, 1.0, 0.0)


def d_3whitesoldiers(K):
    cond = ((K.col(2) == 1) & (K.us(2) < K.a("SVS", 2)) & (K.col(1) == 1) & (K.us(1) < K.a("SVS", 1))
            & (K.col(0) == 1) & (K.us(0) < K.a("SVS", 0))
            & (K.c(0) > K.c(1)) & (K.c(1) > K.c(2))
            & (K.o(1) > K.o(2)) & (K.o(1) <= K.c(2) + K.a("NE", 2))
            & (K.o(0) > K.o(1)) & (K.o(0) <= K.c(1) + K.a("NE", 1))
            & (K.rb(1) > K.rb(2) - K.a("FA", 2)) & (K.rb(0) > K.rb(1) - K.a("FA", 1))
            & (K.rb(0) > K.a("BS", 0)))
    return Wh(cond, 1.0, 0.0)


def d_abandonedbaby(K, pen=0.3):
    cond = ((K.rb(2) > K.a("BL", 2)) & (K.rb(1) <= K.a("BD", 1)) & (K.rb(0) > K.a("BS", 0))
            & (((K.col(2) == 1) & (K.col(0) == -1) & (K.c(0) < K.c(2) - K.rb(2) * pen) & K.gu(1, 2) & K.gd(0, 1))
               | ((K.col(2) == -1) & (K.col(0) == 1) & (K.c(0) > K.c(2) + K.rb(2) * pen) & K.gd(1, 2)
                  & K.gu(0, 1))))
    return Wh(cond, K.col(0), 0.0)


def d_advanceblock(K):
    cond = ((K.col(2) == 1) & (K.col(1) == 1) & (K.col(0) == 1)
            & (K.c(0) > K.c(1)) & (K.c(1) > K.c(2))
            & (K.o(1) > K.o(2)) & (K.o(1) <= K.c(2) + K.a("NE", 2))
            & (K.o(0) > K.o(1)) & (K.o(0) <= K.c(1) + K.a("NE", 1))
            & (K.rb(2) > K.a("BL", 2)) & (K.us(2) < K.a("SS", 2))
            & (((K.rb(1) < K.rb(2) - K.a("FA", 2)) & (K.rb(0) < K.rb(1) + K.a("NE", 1)))
               | (K.rb(0) < K.rb(1) - K.a("FA", 1))
               | ((K.rb(0) < K.rb(1)) & (K.rb(1) < K.rb(2))
                  & ((K.us(0) > K.a("SS", 0)) | (K.us(1) > K.a("SS", 1))))
               | ((K.rb(0) < K.rb(1)) & (K.us(0) > K.a("SL", 0)))))
    return Wh(cond, -1.0, 0.0)


def d_belthold(K):
    cond = (K.rb(0) > K.a("BL", 0)) & (((K.col(0) == 1) & (K.ls(0) < K.a("SVS", 0)))
                                       | ((K.col(0) == -1) & (K.us(0) < K.a("SVS", 0))))
    return Wh(cond, K.col(0), 0.0)


def d_breakaway(K):
    cond = ((K.rb(4) > K.a("BL", 4)) & (K.col(4) == K.col(3)) & (K.col(3) == K.col(1)) & (K.col(1) == -K.col(0))
            & (((K.col(4) == -1) & K.rgd(3, 4) & (K.h(2) < K.h(3)) & (K.l(2) < K.l(3)) & (K.h(1) < K.h(2))
                & (K.l(1) < K.l(2)) & (K.c(0) > K.o(3)) & (K.c(0) < K.c(4)))
               | ((K.col(4) == 1) & K.rgu(3, 4) & (K.h(2) > K.h(3)) & (K.l(2) > K.l(3)) & (K.h(1) > K.h(2))
                  & (K.l(1) > K.l(2)) & (K.c(0) < K.o(3)) & (K.c(0) > K.c(4)))))
    return Wh(cond, K.col(0), 0.0)


def d_closingmarubozu(K):
    cond = (K.rb(0) > K.a("BL", 0)) & (((K.col(0) == 1) & (K.us(0) < K.a("SVS", 0)))
                                       | ((K.col(0) == -1) & (K.ls(0) < K.a("SVS", 0))))
    return Wh(cond, K.col(0), 0.0)


def d_concealbabyswall(K):
    cond = ((K.col(3) == -1) & (K.col(2) == -1) & (K.col(1) == -1) & (K.col(0) == -1)
            & (K.ls(3) < K.a("SVS", 3)) & (K.us(3) < K.a("SVS", 3))
            & (K.ls(2) < K.a("SVS", 2)) & (K.us(2) < K.a("SVS", 2))
            & K.rgd(1, 2) & (K.us(1) > K.a("SVS", 1)) & (K.h(1) > K.c(2))
            & (K.h(0) > K.h(1)) & (K.l(0) < K.l(1)))
    return Wh(cond, 1.0, 0.0)


def d_counterattack(K):
    cond = ((K.col(1) == -K.col(0)) & (K.rb(1) > K.a("BL", 1)) & (K.rb(0) > K.a("BL", 0))
            & (K.c(0) <= K.c(1) + K.a("EQ", 1)) & (K.c(0) >= K.c(1) - K.a("EQ", 1)))
    return Wh(cond, K.col(0), 0.0)


def d_darkcloudcover(K, pen=0.5):
    cond = ((K.col(1) == 1) & (K.rb(1) > K.a("BL", 1)) & (K.col(0) == -1) & (K.o(0) > K.h(1))
            & (K.c(0) > K.o(1)) & (K.c(0) < K.c(1) - K.rb(1) * pen))
    return Wh(cond, -1.0, 0.0)


def d_doji(K):
    return Wh(K.rb(0) <= K.a("BD", 0), 1.0, 0.0)


def d_dojistar(K):
    cond = ((K.rb(1) > K.a("BL", 1)) & (K.rb(0) <= K.a("BD", 0))
            & (((K.col(1) == 1) & K.rgu(0, 1)) | ((K.col(1) == -1) & K.rgd(0, 1))))
    return Wh(cond, -K.col(1), 0.0)


def d_dragonflydoji(K):
    return Wh((K.rb(0) <= K.a("BD", 0)) & (K.us(0) < K.a("SVS", 0)) & (K.ls(0) > K.a("SVS", 0)), 1.0, 0.0)


def d_engulfing(K):
    cond = (((K.col(0) == 1) & (K.col(1) == -1)
             & (((K.c(0) >= K.o(1)) & (K.o(0) < K.c(1))) | ((K.c(0) > K.o(1)) & (K.o(0) <= K.c(1)))))
            | ((K.col(0) == -1) & (K.col(1) == 1)
               & (((K.o(0) >= K.c(1)) & (K.c(0) < K.o(1))) | ((K.o(0) > K.c(1)) & (K.c(0) <= K.o(1))))))
    return Wh(cond, K.col(0), 0.0)


def d_eveningdojistar(K, pen=0.3):
    cond = ((K.rb(2) > K.a("BL", 2)) & (K.col(2) == 1) & (K.rb(1) <= K.a("BD", 1)) & K.rgu(1, 2)
            & (K.rb(0) > K.a("BS", 0)) & (K.col(0) == -1) & (K.c(0) < K.c(2) - K.rb(2) * pen))
    return Wh(cond, -1.0, 0.0)


def d_eveningstar(K, pen=0.3):
    cond = ((K.rb(2) > K.a("BL", 2)) & (K.col(2) == 1) & (K.rb(1) <= K.a("BS", 1)) & K.rgu(1, 2)
            & (K.rb(0) > K.a("BS", 0)) & (K.col(0) == -1) & (K.c(0) < K.c(2) - K.rb(2) * pen))
    return Wh(cond, -1.0, 0.0)


def d_gapsidesidewhite(K):
    cond = (((K.rgu(1, 2) & K.rgu(0, 2)) | (K.rgd(1, 2) & K.rgd(0, 2)))
            & (K.col(1) == 1) & (K.col(0) == 1)
            & (K.rb(0) >= K.rb(1) - K.a("NE", 1)) & (K.rb(0) <= K.rb(1) + K.a("NE", 1))
            & (K.o(0) >= K.o(1) - K.a("EQ", 1)) & (K.o(0) <= K.o(1) + K.a("EQ", 1)))
    return Wh(cond, Wh(K.rgu(1, 2), 1.0, -1.0), 0.0)


def d_gravestonedoji(K):
    return Wh((K.rb(0) <= K.a("BD", 0)) & (K.ls(0) < K.a("SVS", 0)) & (K.us(0) > K.a("SVS", 0)), 1.0, 0.0)


def d_hammer(K):
    cond = ((K.rb(0) < K.a("BS", 0)) & (K.ls(0) > K.a("SL", 0)) & (K.us(0) < K.a("SVS", 0))
            & (K.mn(0) <= K.l(1) + K.a("NE", 1)))
    return Wh(cond, 1.0, 0.0)


def d_hangingman(K):
    cond = ((K.rb(0) < K.a("BS", 0)) & (K.ls(0) > K.a("SL", 0)) & (K.us(0) < K.a("SVS", 0))
            & (K.mn(0) >= K.h(1) - K.a("NE", 1)))
    return Wh(cond, -1.0, 0.0)


def d_harami(K):
    cond = (K.rb(1) > K.a("BL", 1)) & (K.rb(0) <= K.a("BS", 0)) & (K.mx(0) <= K.mx(1)) & (K.mn(0) >= K.mn(1))
    return Wh(cond, -K.col(1), 0.0)


def d_haramicross(K):
    cond = (K.rb(1) > K.a("BL", 1)) & (K.rb(0) <= K.a("BD", 0)) & (K.mx(0) <= K.mx(1)) & (K.mn(0) >= K.mn(1))
    return Wh(cond, -K.col(1), 0.0)


def d_highwave(K):
    return Wh((K.rb(0) < K.a("BS", 0)) & (K.us(0) > K.a("SVL", 0)) & (K.ls(0) > K.a("SVL", 0)), K.col(0), 0.0)


def _confirm(pat, c, ref_h, ref_l):
    """TA-Lib's hikkake confirmation: within HIKKAKE_REACH bars after a pattern bar p (and before the next pattern
    bar), the first close above ref_h[p] (bullish p) or below ref_l[p] (bearish p); one confirmation per pattern"""
    n = len(pat)
    conf = np.zeros(n)
    P = np.flatnonzero(pat)
    for q, p in enumerate(P):
        stop = min(p + HIKKAKE_REACH, n - 1, (P[q + 1] - 1) if q + 1 < len(P) else n - 1)
        for k in range(p + 1, stop + 1):
            if (pat[p] > 0 and c[k] > ref_h[p]) or (pat[p] < 0 and c[k] < ref_l[p]):
                conf[k] = pat[p]
                break
    return conf


def d_hikkake_both(K):
    inside = (K.h(1) < K.h(2)) & (K.l(1) > K.l(2))
    bull = inside & (K.h(0) < K.h(1)) & (K.l(0) < K.l(1))
    bear = inside & (K.h(0) > K.h(1)) & (K.l(0) > K.l(1))
    pat = Wh(bull, 1.0, Wh(bear, -1.0, 0.0))
    return pat, _confirm(pat, K.c(0), K.h(1), K.l(1))          # against the inside bar (patternIdx - 1)


def d_hikkakemod_both(K):
    nest = (K.h(2) < K.h(3)) & (K.l(2) > K.l(3)) & (K.h(1) < K.h(2)) & (K.l(1) > K.l(2))
    bull = nest & (K.h(0) < K.h(1)) & (K.l(0) < K.l(1)) & (K.c(2) <= K.l(2) + K.a("NE", 2))
    bear = nest & (K.h(0) > K.h(1)) & (K.l(0) > K.l(1)) & (K.c(2) >= K.h(2) - K.a("NE", 2))
    pat = Wh(bull, 1.0, Wh(bear, -1.0, 0.0))
    return pat, _confirm(pat, K.c(0), K.h(1), K.l(1))          # against the 3rd candle


def d_homingpigeon(K):
    cond = ((K.col(1) == -1) & (K.col(0) == -1) & (K.rb(1) > K.a("BL", 1)) & (K.rb(0) <= K.a("BS", 0))
            & (K.o(0) < K.o(1)) & (K.c(0) > K.c(1)))
    return Wh(cond, 1.0, 0.0)


def d_identical3crows(K):
    cond = ((K.col(2) == -1) & (K.ls(2) < K.a("SVS", 2)) & (K.col(1) == -1) & (K.ls(1) < K.a("SVS", 1))
            & (K.col(0) == -1) & (K.ls(0) < K.a("SVS", 0)) & (K.c(2) > K.c(1)) & (K.c(1) > K.c(0))
            & (K.o(1) <= K.c(2) + K.a("EQ", 2)) & (K.o(1) >= K.c(2) - K.a("EQ", 2))
            & (K.o(0) <= K.c(1) + K.a("EQ", 1)) & (K.o(0) >= K.c(1) - K.a("EQ", 1)))
    return Wh(cond, -1.0, 0.0)


def d_inneck(K):
    cond = ((K.col(1) == -1) & (K.rb(1) > K.a("BL", 1)) & (K.col(0) == 1) & (K.o(0) < K.l(1))
            & (K.c(0) <= K.c(1) + K.a("EQ", 1)) & (K.c(0) >= K.c(1)))
    return Wh(cond, -1.0, 0.0)


def d_invertedhammer(K):
    cond = (K.rb(0) < K.a("BS", 0)) & (K.us(0) > K.a("SL", 0)) & (K.ls(0) < K.a("SVS", 0)) & K.rgd(0, 1)
    return Wh(cond, 1.0, 0.0)


def _kick(K):
    return ((K.col(1) == -K.col(0))
            & (K.rb(1) > K.a("BL", 1)) & (K.us(1) < K.a("SVS", 1)) & (K.ls(1) < K.a("SVS", 1))
            & (K.rb(0) > K.a("BL", 0)) & (K.us(0) < K.a("SVS", 0)) & (K.ls(0) < K.a("SVS", 0))
            & (((K.col(1) == -1) & K.gu(0, 1)) | ((K.col(1) == 1) & K.gd(0, 1))))


def d_kicking(K):
    return Wh(_kick(K), K.col(0), 0.0)


def d_kickingbylength(K):
    return Wh(_kick(K), Wh(K.rb(0) > K.rb(1), K.col(0), K.col(1)), 0.0)


def d_ladderbottom(K):
    cond = ((K.col(4) == -1) & (K.col(3) == -1) & (K.col(2) == -1)
            & (K.o(4) > K.o(3)) & (K.o(3) > K.o(2)) & (K.c(4) > K.c(3)) & (K.c(3) > K.c(2))
            & (K.col(1) == -1) & (K.us(1) > K.a("SVS", 1))
            & (K.col(0) == 1) & (K.o(0) > K.o(1)) & (K.c(0) > K.h(1)))
    return Wh(cond, 1.0, 0.0)


def d_longleggeddoji(K):
    return Wh((K.rb(0) <= K.a("BD", 0)) & ((K.ls(0) > K.a("SL", 0)) | (K.us(0) > K.a("SL", 0))), 1.0, 0.0)


def d_longline(K):
    return Wh((K.rb(0) > K.a("BL", 0)) & (K.us(0) < K.a("SS", 0)) & (K.ls(0) < K.a("SS", 0)), K.col(0), 0.0)


def d_marubozu(K):
    return Wh((K.rb(0) > K.a("BL", 0)) & (K.us(0) < K.a("SVS", 0)) & (K.ls(0) < K.a("SVS", 0)), K.col(0), 0.0)


def d_matchinglow(K):
    cond = ((K.col(1) == -1) & (K.col(0) == -1) & (K.c(0) <= K.c(1) + K.a("EQ", 1))
            & (K.c(0) >= K.c(1) - K.a("EQ", 1)))
    return Wh(cond, 1.0, 0.0)


def d_mathold(K, pen=0.5):
    cond = ((K.rb(4) > K.a("BL", 4)) & (K.rb(3) < K.a("BS", 3)) & (K.rb(2) < K.a("BS", 2))
            & (K.rb(1) < K.a("BS", 1))
            & (K.col(4) == 1) & (K.col(3) == -1) & (K.col(0) == 1)
            & K.rgu(3, 4)
            & (K.mn(2) < K.c(4)) & (K.mn(1) < K.c(4))
            & (K.mn(2) > K.c(4) - K.rb(4) * pen) & (K.mn(1) > K.c(4) - K.rb(4) * pen)
            & (K.mx(2) < K.o(3)) & (K.mx(1) < K.mx(2))
            & (K.o(0) > K.c(1)) & (K.c(0) > np.maximum(np.maximum(K.h(3), K.h(2)), K.h(1))))
    return Wh(cond, 1.0, 0.0)


def d_morningdojistar(K, pen=0.3):
    cond = ((K.rb(2) > K.a("BL", 2)) & (K.col(2) == -1) & (K.rb(1) <= K.a("BD", 1)) & K.rgd(1, 2)
            & (K.rb(0) > K.a("BS", 0)) & (K.col(0) == 1) & (K.c(0) > K.c(2) + K.rb(2) * pen))
    return Wh(cond, 1.0, 0.0)


def d_morningstar(K, pen=0.3):
    cond = ((K.rb(2) > K.a("BL", 2)) & (K.col(2) == -1) & (K.rb(1) <= K.a("BS", 1)) & K.rgd(1, 2)
            & (K.rb(0) > K.a("BS", 0)) & (K.col(0) == 1) & (K.c(0) > K.c(2) + K.rb(2) * pen))
    return Wh(cond, 1.0, 0.0)


def d_onneck(K):
    cond = ((K.col(1) == -1) & (K.rb(1) > K.a("BL", 1)) & (K.col(0) == 1) & (K.o(0) < K.l(1))
            & (K.c(0) <= K.l(1) + K.a("EQ", 1)) & (K.c(0) >= K.l(1) - K.a("EQ", 1)))
    return Wh(cond, -1.0, 0.0)


def d_piercing(K):
    cond = ((K.col(1) == -1) & (K.rb(1) > K.a("BL", 1)) & (K.col(0) == 1) & (K.rb(0) > K.a("BL", 0))
            & (K.o(0) < K.l(1)) & (K.c(0) < K.o(1)) & (K.c(0) > K.c(1) + K.rb(1) * 0.5))
    return Wh(cond, 1.0, 0.0)


def d_rickshawman(K):
    mid = K.l(0) + K.hl(0) / 2
    cond = ((K.rb(0) <= K.a("BD", 0)) & (K.ls(0) > K.a("SL", 0)) & (K.us(0) > K.a("SL", 0))
            & (K.mn(0) <= mid + K.a("NE", 0)) & (K.mx(0) >= mid - K.a("NE", 0)))
    return Wh(cond, 1.0, 0.0)


def d_risefall3methods(K):
    s = K.col(4)
    cond = ((K.rb(4) > K.a("BL", 4)) & (K.rb(3) < K.a("BS", 3)) & (K.rb(2) < K.a("BS", 2))
            & (K.rb(1) < K.a("BS", 1)) & (K.rb(0) > K.a("BL", 0))
            & (K.col(4) == -K.col(3)) & (K.col(3) == K.col(2)) & (K.col(2) == K.col(1)) & (K.col(1) == -K.col(0))
            & (K.mn(3) < K.h(4)) & (K.mx(3) > K.l(4)) & (K.mn(2) < K.h(4)) & (K.mx(2) > K.l(4))
            & (K.mn(1) < K.h(4)) & (K.mx(1) > K.l(4))
            & (K.c(2) * s < K.c(3) * s) & (K.c(1) * s < K.c(2) * s)
            & (K.o(0) * s > K.c(1) * s) & (K.c(0) * s > K.c(4) * s))
    return Wh(cond, s, 0.0)


def d_separatinglines(K):
    cond = ((K.col(1) == -K.col(0)) & (K.o(0) <= K.o(1) + K.a("EQ", 1)) & (K.o(0) >= K.o(1) - K.a("EQ", 1))
            & (K.rb(0) > K.a("BL", 0))
            & (((K.col(0) == 1) & (K.ls(0) < K.a("SVS", 0))) | ((K.col(0) == -1) & (K.us(0) < K.a("SVS", 0)))))
    return Wh(cond, K.col(0), 0.0)


def d_shootingstar(K):
    cond = (K.rb(0) < K.a("BS", 0)) & (K.us(0) > K.a("SL", 0)) & (K.ls(0) < K.a("SVS", 0)) & K.rgu(0, 1)
    return Wh(cond, -1.0, 0.0)


def d_shortline(K):
    return Wh((K.rb(0) < K.a("BS", 0)) & (K.us(0) < K.a("SS", 0)) & (K.ls(0) < K.a("SS", 0)), K.col(0), 0.0)


def d_spinningtop(K):
    return Wh((K.rb(0) < K.a("BS", 0)) & (K.us(0) > K.rb(0)) & (K.ls(0) > K.rb(0)), K.col(0), 0.0)


def d_stalledpattern(K):
    cond = ((K.col(2) == 1) & (K.col(1) == 1) & (K.col(0) == 1) & (K.c(0) > K.c(1)) & (K.c(1) > K.c(2))
            & (K.rb(2) > K.a("BL", 2)) & (K.rb(1) > K.a("BL", 1)) & (K.us(1) < K.a("SVS", 1))
            & (K.o(1) > K.o(2)) & (K.o(1) <= K.c(2) + K.a("NE", 2))
            & (K.rb(0) < K.a("BS", 0)) & (K.o(0) >= K.c(1) - K.rb(0) - K.a("NE", 1)))
    return Wh(cond, -1.0, 0.0)


def d_sticksandwich(K):
    cond = ((K.col(2) == -1) & (K.col(1) == 1) & (K.col(0) == -1) & (K.l(1) > K.c(2))
            & (K.c(0) <= K.c(2) + K.a("EQ", 2)) & (K.c(0) >= K.c(2) - K.a("EQ", 2)))
    return Wh(cond, 1.0, 0.0)


def d_takuri(K):
    return Wh((K.rb(0) <= K.a("BD", 0)) & (K.us(0) < K.a("SVS", 0)) & (K.ls(0) > K.a("SVL", 0)), 1.0, 0.0)


def d_tasukigap(K):
    near = np.abs(K.rb(1) - K.rb(0)) < K.a("NE", 1)
    cond = ((K.rgu(1, 2) & (K.col(1) == 1) & (K.col(0) == -1) & (K.o(0) < K.c(1)) & (K.o(0) > K.o(1))
             & (K.c(0) < K.o(1)) & (K.c(0) > K.mx(2)) & near)
            | (K.rgd(1, 2) & (K.col(1) == -1) & (K.col(0) == 1) & (K.o(0) < K.o(1)) & (K.o(0) > K.c(1))
               & (K.c(0) > K.o(1)) & (K.c(0) < K.mn(2)) & near))
    return Wh(cond, K.col(1), 0.0)


def d_thrusting(K):
    cond = ((K.col(1) == -1) & (K.rb(1) > K.a("BL", 1)) & (K.col(0) == 1) & (K.o(0) < K.l(1))
            & (K.c(0) > K.c(1) + K.a("EQ", 1)) & (K.c(0) <= K.c(1) + K.rb(1) * 0.5))
    return Wh(cond, -1.0, 0.0)


def d_tristar(K):
    av = K.a("BD", 2)                                   # TA-Lib measures all three against the first's average
    dj = (K.rb(2) <= av) & (K.rb(1) <= av) & (K.rb(0) <= av)
    bear = dj & K.rgu(1, 2) & (K.mx(0) < K.mx(1))
    bull = dj & K.rgd(1, 2) & (K.mn(0) > K.mn(1))
    return Wh(bull, 1.0, Wh(bear, -1.0, 0.0))


def d_unique3river(K):
    cond = ((K.rb(2) > K.a("BL", 2)) & (K.col(2) == -1) & (K.col(1) == -1) & (K.c(1) > K.c(2))
            & (K.o(1) <= K.o(2)) & (K.l(1) < K.l(2)) & (K.rb(0) < K.a("BS", 0)) & (K.col(0) == 1)
            & (K.o(0) > K.l(1)))
    return Wh(cond, 1.0, 0.0)


def d_upsidegap2crows(K):
    cond = ((K.col(2) == 1) & (K.rb(2) > K.a("BL", 2)) & (K.col(1) == -1) & (K.rb(1) <= K.a("BS", 1))
            & K.rgu(1, 2) & (K.col(0) == -1) & (K.o(0) > K.o(1)) & (K.c(0) < K.c(1)) & (K.c(0) > K.c(2)))
    return Wh(cond, -1.0, 0.0)


def d_xsidegap3methods(K):
    cond = ((K.col(2) == K.col(1)) & (K.col(1) == -K.col(0))
            & (K.o(0) < K.mx(1)) & (K.o(0) > K.mn(1)) & (K.c(0) < K.mx(2)) & (K.c(0) > K.mn(2))
            & (((K.col(2) == 1) & K.rgu(1, 2)) | ((K.col(2) == -1) & K.rgd(1, 2))))
    return Wh(cond, K.col(2), 0.0)


def d_tweezer(K):
    """not a TA-Lib function: Nison's tweezers in TA-Lib's vocabulary. The lows (highs) are equal by TA-Lib's Equal
    setting; "after a decline" is the study's close before against the close five sessions earlier, a number neither
    Nison nor TA-Lib gives (kept as the study tested it; the read's own move rule applies on top)"""
    bot = (K.col(1) == -1) & (K.col(0) == 1) & (np.abs(K.l(0) - K.l(1)) <= K.a("EQ", 1)) & (K.c(1) < K.c(6))
    top = (K.col(1) == 1) & (K.col(0) == -1) & (np.abs(K.h(0) - K.h(1)) <= K.a("EQ", 1)) & (K.c(1) > K.c(6))
    return Wh(bot, 1.0, Wh(top, -1.0, 0.0))


# ------------------------------------------------------------------------------------------------ the registry
# kind: how the read counts it.
#   rev      a reversal (Nison; TA-Lib's sign): on its level after the move it reverses
#   cont     a continuation (Nison, Bulkowski): on its level after the move it continues
#   trap     TA-Lib's confirmed hikkake: a false break that reverses on its own sessions, so only the level
#   doji     an indecision candle (TA-Lib's sign is presence or colour, not a direction): stated on a level, no vote
#   covered  read by the read's own candle fact (read_by), never twice
#   bar      TA-Lib's hikkake pattern bar before its confirmation: checked, counted once confirmed
#   alias    the same candles as another detector (TA-Lib's kicking by length): checked, read as that one
# span: candles in the pattern (its low or high is taken over them). rate: the study's share of name-sessions where it
# fired on a key level of its own definition (lab/candles.md, describe.log; 803,171 name-sessions), in percent.
Pattern = namedtuple("Pattern", "name fn span lookback kind names whats title teach rate read_by")


def _p(name, fn, span, lookback, kind, names, whats, title="", teach="", rate=0.0, read_by=""):
    return Pattern(name, fn, span, lookback, kind, names, whats, title, teach, rate, read_by)


_UP, _DN = "an up session", "a down session"
REG = [
    _p("2crows", d_2crows, 3, 12, "rev", (None, "two crows"),
       (None, "a long up session, a down session whose body gaps above it, then a down session opening inside the "
              "second body and closing inside the first"),
       "Two crows", "A long up session, a down session gapping above it, then a down session closing back into the "
       "first body: the advance stalls (Nison).", 0.062),
    _p("3blackcrows", d_3blackcrows, 3, 13, "rev", (None, "three black crows"),
       (None, "after an up session, three down sessions each opening inside the one before and closing lower, near "
              "its low"),
       "Three black crows", "Three down sessions in a row, each opening inside the one before and closing near its "
       "low, after an up session: sellers in control (Nison).", 0.011),
    _p("3inside", d_3inside, 3, 12, "rev", ("three inside up", "three inside down"),
       ("a long down session, a small session inside its body, then an up session closing above the first one's open",
        "a long up session, a small session inside its body, then a down session closing below the first one's open"),
       "Three inside up or down", "A harami (a small session inside a long one) whose next session closes beyond the "
       "long one's open, confirming the turn (Nison).", 1.265),
    _p("3linestrike", d_3linestrike, 4, 8, "cont", ("a bullish three-line strike", "a bearish three-line strike"),
       ("three up sessions closing higher each time, then a down session opening above the third close and closing "
        "under the first open",
        "three down sessions closing lower each time, then an up session opening under the third close and closing "
        "over the first open"),
       "Three-line strike", "Three sessions in one direction, then one that opens beyond them and wipes them out in "
       "one session; TA-Lib reads it in the direction of the first three, a pause in that trend (Nison).", 0.067),
    _p("3outside", d_3outside, 3, 3, "rev", ("three outside up", "three outside down"),
       ("an up session engulfing the down session before it, then a higher close",
        "a down session engulfing the up session before it, then a lower close"),
       "Three outside up or down", "An engulfing pair whose next session closes further the same way, confirming "
       "the turn (Nison).", 3.064),
    _p("3starsinsouth", d_3starsinsouth, 3, 12, "rev", ("three stars in the south", None),
       ("three down sessions, each smaller and holding above the one before's low, the first with a long lower "
        "shadow", None),
       "Three stars in the south", "Three shrinking down sessions whose lows stop falling, the first with a long "
       "lower shadow: selling running out (Nison).", 0.000),
    _p("3whitesoldiers", d_3whitesoldiers, 3, 12, "rev", ("three white soldiers", None),
       ("three up sessions closing higher each time near their highs, each opening inside the one before", None),
       "Three white soldiers", "Three up sessions in a row, each opening inside the one before and closing near its "
       "high: buyers in control (Nison).", 0.042),
    _p("abandonedbaby", d_abandonedbaby, 3, 12, "rev", ("a bullish abandoned baby", "a bearish abandoned baby"),
       ("a long down session, a doji gapping below it, then an up session gapping back above the doji and closing "
        "back over 30% of the first body",
        "a long up session, a doji gapping above it, then a down session gapping back under the doji and closing "
        "back over 30% of the first body"),
       "Abandoned baby", "A doji left alone by gaps on both sides between two opposite sessions: a rare, sharp "
       "turn (Nison).", 0.006),
    _p("advanceblock", d_advanceblock, 3, 12, "rev", (None, "an advance block"),
       (None, "three up sessions closing higher each time whose bodies shrink or whose upper shadows lengthen"),
       "Advance block", "Three rising up sessions that weaken as they go, bodies shrinking or upper shadows "
       "lengthening: the advance tiring (Nison).", 0.396),
    _p("belthold", d_belthold, 1, 10, "rev", ("a bullish belt hold", "a bearish belt hold"),
       ("a long up session that opened at its low", "a long down session that opened at its high"),
       "Belt hold", "A long session that opens at one extreme and runs the other way all day; after a move the "
       "other way, a turn (Nison).", 13.462),
    _p("breakaway", d_breakaway, 5, 14, "rev", ("a bullish breakaway", "a bearish breakaway"),
       ("a long down session, a down session gapping below it, two more lower sessions, then an up session closing "
        "inside that gap",
        "a long up session, an up session gapping above it, two more higher sessions, then a down session closing "
        "inside that gap"),
       "Breakaway", "Five sessions: a gap that extends a move, three more sessions that way, then one closing back "
       "inside the gap (Nison).", 0.014),
    _p("closingmarubozu", d_closingmarubozu, 1, 10, "rev", ("a bullish closing marubozu", "a bearish closing marubozu"),
       ("a long up session that closed at its high", "a long down session that closed at its low"),
       "Closing marubozu", "A long session that closes at its extreme, no shadow at the close: one side held it to "
       "the end (Nison).", 11.727),
    _p("concealbabyswall", d_concealbabyswall, 4, 13, "rev", ("a concealing baby swallow", None),
       ("two down sessions with almost no shadows, a third gapping lower whose upper shadow reaches into the second, "
        "then a down session engulfing the third", None),
       "Concealing baby swallow", "Four down sessions in which the last engulfs a gap lower: the selling swallows "
       "itself (Nison).", 0.000),
    _p("counterattack", d_counterattack, 2, 11, "rev", ("a bullish counterattack", "a bearish counterattack"),
       ("a long down session, then a long up session closing at the same price",
        "a long up session, then a long down session closing at the same price"),
       "Counterattack", "Two long opposite sessions closing at the same price: the second side fights back to "
       "even (Nison).", 0.107),
    _p("darkcloudcover", d_darkcloudcover, 2, 11, "rev", (None, "a dark cloud cover"),
       (None, "a long up session, then a down session opening above its high and closing under the middle of its "
              "body"),
       "Dark cloud cover", "A down session that opens above the up session before it and closes under its middle: "
       "a turn lower (Nison).", 0.339),
    _p("doji", d_doji, 1, 10, "covered", ("a doji", None), ("", None), rate=13.222, read_by="candle.doji"),
    _p("dojistar", d_dojistar, 2, 11, "rev", ("a bullish doji star", "a bearish doji star"),
       ("a long down session, then a doji whose body gaps below it",
        "a long up session, then a doji whose body gaps above it"),
       "Doji star", "A doji gapping away from a long session: the move halts, a warning of a turn (Nison).", 1.921),
    _p("dragonflydoji", d_dragonflydoji, 1, 10, "doji", ("a dragonfly doji", None),
       ("a doji that opened and closed at its high, with a lower shadow", None),
       "Dragonfly doji", "A doji that opens and closes at its high after trading lower: indecision that rejected "
       "the lows (Nison).", 1.339),
    _p("engulfing", d_engulfing, 2, 2, "covered", ("a bullish engulfing", "a bearish engulfing"), ("", ""),
       rate=7.067, read_by="candle.engulf"),
    _p("eveningdojistar", d_eveningdojistar, 3, 12, "rev", (None, "an evening doji star"),
       (None, "a long up session, a doji whose body gaps above it, then a down session closing back over 30% of the "
              "first body"),
       "Evening doji star", "An evening star whose middle session is a doji (Nison).", 0.171),
    _p("eveningstar", d_eveningstar, 3, 12, "rev", (None, "an evening star"),
       (None, "a long up session, a small session whose body gaps above it, then a down session closing back over "
              "30% of the first body"),
       "Evening star", "A long up session, a small one gapping higher, then a down session closing well into the "
       "first: buyers give way at a high (Nison).", 0.479),
    _p("gapsidesidewhite", d_gapsidesidewhite, 3, 7, "cont",
       ("side-by-side white lines after a gap up", "side-by-side white lines after a gap down"),
       ("an up session gapping above the one before, then another up session of about the same size opening at the "
        "same price",
        "an up session gapping below the one before, then another up session of about the same size opening at the "
        "same price"),
       "Side-by-side white lines", "Two similar up sessions side by side after a gap: the gap holds, and the move "
       "it made goes on (Nison).", 0.237),
    _p("gravestonedoji", d_gravestonedoji, 1, 10, "doji", ("a gravestone doji", None),
       ("a doji that opened and closed at its low, with an upper shadow", None),
       "Gravestone doji", "A doji that opens and closes at its low after trading higher: indecision that rejected "
       "the highs (Nison).", 1.226),
    _p("hammer", d_hammer, 1, 11, "covered", ("a hammer", None), ("", None), rate=1.862, read_by="candle.hammer"),
    _p("hangingman", d_hangingman, 1, 11, "covered", (None, "a hanging man"), (None, ""), rate=1.474,
       read_by="candle.hammer"),
    _p("harami", d_harami, 2, 11, "rev", ("a bullish harami", "a bearish harami"),
       ("a long down session, then a small session inside its body",
        "a long up session, then a small session inside its body"),
       "Harami", "A small session inside the body of a long one before it: the move loses its force (Nison).",
       6.117),
    _p("haramicross", d_haramicross, 2, 11, "rev", ("a bullish harami cross", "a bearish harami cross"),
       ("a long down session, then a doji inside its body", "a long up session, then a doji inside its body"),
       "Harami cross", "A doji inside the body of a long session before it: a harami whose second session is "
       "indecision itself (Nison).", 1.947),
    _p("highwave", d_highwave, 1, 10, "doji", ("a high-wave candle", None),
       ("a small body with very long shadows on both sides", None),
       "High-wave candle", "A small body with very long shadows on both sides: wide swings both ways, no winner "
       "(Nison).", 12.361),
    _p("hikkake", None, 3, 5, "bar", ("a bullish hikkake", "a bearish hikkake"), ("", ""), rate=7.580),
    _p("hikkake_c", None, 1, 5, "trap", ("a confirmed bullish hikkake", "a confirmed bearish hikkake"),
       ("a session inside the one before, a false break under it, then a close above the inside session's high",
        "a session inside the one before, a false break over it, then a close under the inside session's low"),
       "Hikkake", "An inside session, a break out of it that fails, then a close back through its far side within "
       "three sessions: the breakers trapped (Daniel Chesler).", 1.954),
    _p("hikkakemod", None, 4, 10, "bar", ("a bullish modified hikkake", "a bearish modified hikkake"), ("", ""),
       rate=0.093),
    _p("hikkakemod_c", None, 1, 10, "trap",
       ("a confirmed bullish modified hikkake", "a confirmed bearish modified hikkake"),
       ("a session inside the one before that closed near its low, a second inside that, a false break under it, "
        "then a close above the second inside session's high",
        "a session inside the one before that closed near its high, a second inside that, a false break over it, "
        "then a close under the second inside session's low"),
       "Modified hikkake", "A hikkake whose first inside session closed at the end it later fakes: two nested "
       "inside sessions, a failed break, then a close back through them within three sessions.", 0.024),
    _p("homingpigeon", d_homingpigeon, 2, 11, "rev", ("a homing pigeon", None),
       ("a long down session, then a short down session inside its body", None),
       "Homing pigeon", "A small down session inside the body of a long down session: the selling shrinks "
       "(Nison).", 1.043),
    _p("identical3crows", d_identical3crows, 3, 12, "rev", (None, "identical three crows"),
       (None, "three down sessions closing lower each time near their lows, each opening at the one before's close"),
       "Identical three crows", "Three crows each opening at the last close: relentless selling (Nison).", 0.008),
    _p("inneck", d_inneck, 2, 11, "cont", (None, "an in-neck line"),
       (None, "a long down session, then an up session opening under its low and closing at or just above its "
              "close"),
       "In-neck line", "After a long down session, an up session that opens lower and only gets back to its close: "
       "a weak bounce in a decline (Nison).", 0.123),
    _p("invertedhammer", d_invertedhammer, 1, 11, "covered", ("an inverted hammer", None), ("", None), rate=1.114,
       read_by="candle.star"),
    _p("kicking", d_kicking, 2, 11, "rev", ("a bullish kicker", "a bearish kicker"),
       ("a down session with almost no shadows, then an up session with almost no shadows gapping above it",
        "an up session with almost no shadows, then a down session with almost no shadows gapping below it"),
       "Kicker", "Two shadowless sessions of opposite colour with a gap between them: one side kicked the other "
       "out (Nison).", 0.002),
    _p("kickingbylength", d_kickingbylength, 2, 11, "alias", ("a bullish kicker", "a bearish kicker"), ("", ""),
       rate=0.002, read_by="candle.kicking"),
    _p("ladderbottom", d_ladderbottom, 5, 14, "rev", ("a ladder bottom", None),
       ("three down sessions with lower opens and closes, a fourth down session with an upper shadow, then an up "
        "session opening above the fourth's open and closing above its high", None),
       "Ladder bottom", "Four falling down sessions, the last trying higher, then an up session closing over it "
       "(Nison).", 0.102),
    _p("longleggeddoji", d_longleggeddoji, 1, 10, "doji", ("a long-legged doji", None),
       ("open and close nearly equal, with a shadow longer than the body", None),
       "Long-legged doji", "Open and close nearly equal after wide trading: indecision (Nison).", 13.109),
    _p("longline", d_longline, 1, 10, "rev", ("a long white line", "a long black line"),
       ("a long up session with short shadows", "a long down session with short shadows"),
       "Long line", "A long body with short shadows: one side moved price all session; after a move the other "
       "way, a turn (Nison).", 16.485),
    _p("marubozu", d_marubozu, 1, 10, "rev", ("a white marubozu", "a black marubozu"),
       ("a long up session with almost no shadows", "a long down session with almost no shadows"),
       "Marubozu", "A long body with almost no shadows: open at one extreme, close at the other (Nison).", 3.971),
    _p("matchinglow", d_matchinglow, 2, 6, "rev", ("a matching low", None),
       ("two down sessions closing at the same price", None),
       "Matching low", "Two down sessions closing at the same price: a floor under the selling (Nison).", 1.306),
    _p("mathold", d_mathold, 5, 14, "cont", ("a mat hold", None),
       ("a long up session, a small down session gapping above it, two more small sessions holding in its upper "
        "half, then an up session closing above them all", None),
       "Mat hold", "A long up session, three small ones resting in its upper half, then an up session to new "
       "highs: the advance resumes (Nison).", 0.002),
    _p("morningdojistar", d_morningdojistar, 3, 12, "rev", ("a morning doji star", None),
       ("a long down session, a doji whose body gaps below it, then an up session closing back over 30% of the first "
        "body", None),
       "Morning doji star", "A morning star whose middle session is a doji (Nison).", 0.123),
    _p("morningstar", d_morningstar, 3, 12, "rev", ("a morning star", None),
       ("a long down session, a small session whose body gaps below it, then an up session closing back over 30% of "
        "the first body", None),
       "Morning star", "A long down session, a small one gapping lower, then an up session closing well into the "
       "first: sellers give way at a low (Nison).", 0.341),
    _p("onneck", d_onneck, 2, 11, "cont", (None, "an on-neck line"),
       (None, "a long down session, then an up session opening under its low and closing back at that low"),
       "On-neck line", "After a long down session, an up session that opens lower and only gets back to its low: a "
       "weak bounce in a decline (Nison).", 0.253),
    _p("piercing", d_piercing, 2, 11, "rev", ("a piercing line", None),
       ("a long down session, then a long up session opening under its low and closing above the middle of its body",
        None),
       "Piercing line", "An up session that opens under the down session before it and closes above its middle: a "
       "turn higher (Nison).", 0.300),
    _p("rickshawman", d_rickshawman, 1, 10, "doji", ("a rickshaw man", None),
       ("open and close nearly equal in the middle of the session, with long shadows on both sides", None),
       "Rickshaw man", "A long-legged doji whose body sits in the middle of its range: indecision (Nison).", 9.630),
    _p("risefall3methods", d_risefall3methods, 5, 14, "cont", ("rising three methods", "falling three methods"),
       ("a long up session, three small down sessions inside its range, then a long up session closing above the "
        "first one's close",
        "a long down session, three small up sessions inside its range, then a long down session closing below the "
        "first one's close"),
       "Rising or falling three methods", "A long session, three small ones resting against it inside its range, "
       "then a long one to a new close: the move resumes (Nison).", 0.021),
    _p("separatinglines", d_separatinglines, 2, 11, "cont", ("a bullish separating line", "a bearish separating line"),
       ("a down session, then a long up session opening at the same price and at its low",
        "an up session, then a long down session opening at the same price and at its high"),
       "Separating lines", "Two opposite sessions opening at the same price, the second running away from it: the "
       "trend resumes (Nison).", 0.363),
    _p("shootingstar", d_shootingstar, 1, 11, "covered", (None, "a shooting star"), (None, ""), rate=1.134,
       read_by="candle.star"),
    _p("shortline", d_shortline, 1, 10, "doji", ("a short line", None),
       ("a short session with short shadows", None),
       "Short line", "A short body with short shadows: a quiet session (Nison).", 11.198),
    _p("spinningtop", d_spinningtop, 1, 10, "doji", ("a spinning top", None),
       ("a small body with shadows longer than it on both sides", None),
       "Spinning top", "A small body with shadows longer than it on both sides: neither side won the session "
       "(Nison).", 20.804),
    _p("stalledpattern", d_stalledpattern, 3, 12, "rev", (None, "a stalled pattern"),
       (None, "two long up sessions, then a small up session opening near the second one's close"),
       "Stalled pattern", "Two long up sessions, then a small one riding on the second: the advance deliberates "
       "(Nison).", 0.191),
    _p("sticksandwich", d_sticksandwich, 3, 7, "rev", ("a stick sandwich", None),
       ("a down session, an up session trading above its close, then a down session closing at the first one's "
        "close", None),
       "Stick sandwich", "Two down sessions closing at the same price around an up session: a floor at that close "
       "(Nison).", 0.118),
    _p("takuri", d_takuri, 1, 10, "doji", ("a takuri", None),
       ("a doji that opened and closed at its high, with a lower shadow over twice its body", None),
       "Takuri", "A dragonfly doji with a very long lower shadow: indecision that rejected the lows (Nison).", 1.324),
    _p("tasukigap", d_tasukigap, 3, 7, "cont", ("an upside tasuki gap", "a downside tasuki gap"),
       ("an up session whose body gaps above the one before, then a down session of about the same size opening "
        "inside it and closing inside the gap",
        "a down session whose body gaps below the one before, then an up session of about the same size opening "
        "inside it and closing inside the gap"),
       "Tasuki gap", "A gap, a session with it, then a session against it that stops inside the gap: the gap "
       "holds (Nison).", 0.463),
    _p("thrusting", d_thrusting, 2, 11, "cont", (None, "a thrusting line"),
       (None, "a long down session, then an up session opening under its low and closing inside its body, under its "
              "middle"),
       "Thrusting line", "After a long down session, an up session that opens lower and closes into its body but "
       "not past the middle: a weak bounce in a decline (Nison).", 0.698),
    _p("tristar", d_tristar, 3, 12, "rev", ("a bullish tri-star", "a bearish tri-star"),
       ("three dojis, the middle one gapping below the other two", "three dojis, the middle one gapping above the "
        "other two"),
       "Tri-star", "Three dojis, the middle one gapping away: a rare sign the move has stalled (Nison).", 0.103),
    _p("unique3river", d_unique3river, 3, 12, "rev", ("a unique three river", None),
       ("a long down session, a down session inside it with a lower low, then a small up session opening above that "
        "low", None),
       "Unique three river", "A long down session, a lower low that closes back inside it, then a small up session: "
       "the selling stops (Nison).", 0.116),
    _p("upsidegap2crows", d_upsidegap2crows, 3, 12, "rev", (None, "an upside gap two crows"),
       (None, "a long up session, a small down session gapping above it, then a down session engulfing the second "
              "and closing above the first one's close"),
       "Upside gap two crows", "Two down sessions gapping above a long up session, the second engulfing the first: "
       "the advance stalls (Nison).", 0.039),
    _p("xsidegap3methods", d_xsidegap3methods, 3, 2, "cont", ("upside gap three methods", "downside gap three methods"),
       ("two up sessions with a gap between their bodies, then a down session opening inside the second and closing "
        "inside the first, filling the gap",
        "two down sessions with a gap between their bodies, then an up session opening inside the second and closing "
        "inside the first, filling the gap"),
       "Upside or downside gap three methods", "Two sessions with a gap between them, then one that fills the gap "
       "against them: the move goes on (Nison).", 0.577),
    _p("tweezer", d_tweezer, 2, 6, "rev", ("a tweezer bottom", "a tweezer top"),
       ("a down session then an up session with the same low, after lower closes",
        "an up session then a down session with the same high, after higher closes"),
       "Tweezers", "Two sessions with the same low (a bottom) or the same high (a top) at the end of a move: the "
       "price held twice (Nison).", 2.635),
]
PATTERNS = {p.name: p for p in REG}
NAMED = tuple(p.name for p in REG if not p.name.endswith("_c"))     # TA-Lib's 61 functions and the tweezer
READ_KEYS = {"candle.hammer", "candle.star", "candle.engulf", "candle.outside", "candle.wide", "candle.doji",
             "candle.close"}                                           # the read's own candle facts (candles.py)
# the scan reads only the sessions its patterns reach: the deepest TA-Lib lookback (five candles and ten behind their
# averages), the hikkake's confirmation reach behind its pattern bar, and the session itself; a test proves the scan
# equals the full series at every session
WINDOW = max(p.lookback for p in REG) + HIKKAKE_REACH + 1

# how strongly each counts: neither the study (no edge alone, PATTERNS.md 2l) nor the method fixes a weight, so each
# takes the read's own strength for the same kind of candle reading (candles.py): a reversal on a level the hammer's,
# the shooting star's and the engulfing day's there, 0.45; a one-session strong body (belt hold, marubozu, long line)
# the wide-range day's, 0.35; a continuation the runaway gap's (the read's continuation in this kind), 0.35; the
# confirmed hikkake, a reversal of its own false break, 0.45; indecision the doji's, no vote
STRENGTH = {"rev": 0.45, "rev1": 0.35, "cont": 0.35, "trap": 0.45, "doji": 0.0}


def _rarity_scale():
    """the bits of surprise per unit of the read's fixed rarity: fitted through the origin on the read's own candle
    rarities (hammer and engulfing on a level 0.45, doji 0.25) against the study's shares of those patterns on a
    level (1.862%, 7.067%, 13.222%)"""
    import math
    pairs = [(0.45, -math.log2(0.01862)), (0.45, -math.log2(0.07067)), (0.25, -math.log2(0.13222))]
    return sum(r * s for r, s in pairs) / sum(s * s for _, s in pairs)


_RARITY_K = _rarity_scale()
_N_STUDY = 803171                                                      # name-sessions in the study's candles table


def rarity(p):
    """a reading's fixed rarity (call._salience before the roster's shares are known): the study's share in bits,
    on the read's scale; a pattern the study never saw counts as half a session of its 803,171"""
    import math
    share = max(p.rate / 100.0, 0.5 / _N_STUDY)
    return min(1.0, _RARITY_K * -math.log2(share))


def bare(name):
    """the name without its article: "a morning star" -> "morning star\""""
    for a in ("a ", "an "):
        if name.startswith(a):
            return name[len(a):]
    return name


# ------------------------------------------------------------------------------------------------ the scans
def arrays(o, h, l, c):
    """{pattern: full-length array of its value per session (-1, 0, +1), NaN inside TA-Lib's lookback}"""
    o, h, l, c = (np.asarray(v, float) for v in (o, h, l, c))
    K = _K(o, h, l, c)
    hk, hm = d_hikkake_both(K), d_hikkakemod_both(K)
    special = {"hikkake": hk[0], "hikkake_c": hk[1], "hikkakemod": hm[0], "hikkakemod_c": hm[1]}
    out = {}
    for p in REG:
        v = special[p.name] if p.fn is None else p.fn(K)
        v = np.asarray(v, float).copy()
        v[:p.lookback] = np.nan
        out[p.name] = v
    return out


def scan(bars, end=None):
    """{pattern: (its value at session `end`, the index of its first session or None)}: the detectors on the WINDOW
    sessions to `end` (the last by default), which equal the full series' there (test_read_candles)"""
    end = len(bars) - 1 if end is None else end
    lo = max(0, end - WINDOW + 1)
    w = bars[lo:end + 1]
    o, h, l, c = (np.array([float(b[k]) for b in w]) for k in ("o", "h", "l", "c"))
    a = arrays(o, h, l, c)
    out = {}
    for p in REG:
        v = a[p.name][-1]
        v = 0.0 if np.isnan(v) else float(v)
        first = None
        if v:
            if p.name in ("hikkake_c", "hikkakemod_c"):
                pat = a[p.name[:-2]]
                back = next(k for k in range(1, HIKKAKE_REACH + 1) if len(pat) > k and pat[-1 - k] == v)
                first = end - back - (2 if p.name == "hikkake_c" else 3)          # from its mother session
            else:
                first = end - p.span + 1
        out[p.name] = (v, first)
    return out


def span_of(name, cands, background=12):
    """the sessions a pattern found at the end of `cands` covers (a hikkake's from its mother session to its
    confirmation), on `background` sessions of the study's flat background before it"""
    bg = (100.0, 101.5, 99.5, 101.0)
    rows = [bg] * background + list(cands)
    bars = [{"o": r[0], "h": r[1], "l": r[2], "c": r[3]} for r in rows]
    v, first = scan(bars)[name]
    return len(rows) - first if v else PATTERNS[name].span


# ----------------------------------------------------------------------------------------------------- the read
def _level(x, price, first, below, near):
    """the floor (below) or ceiling nearest `price`, of two or more kinds (or a tested swing or 52-week extreme,
    weight 1.5), within `near` ATR, from levels known before the pattern: members dated at its first session or
    later do not count (the read's B-H8 rule over the pattern's own sessions)"""
    best = None
    for a in x.areas:
        if any(m.i is not None and m.i >= first for m in a.members):
            rest = [m for m in a.members if m.i is None or m.i < first]
            if not rest:
                continue
            a = Area(rest, x.bars, x.atr)
        if a.confluence < 2 and a.weight < 1.5:
            continue
        if (a.price > x.close) if below else (a.price < x.close):
            continue
        d = abs(a.price - price)
        if d <= near * x.atr and (best is None or d < best[0]):
            best = (d, a)
    return best[1] if best else None


def moved(x, first):
    """the move into a pattern in ATR: the ten sessions before its first session, the read's own reversal rule
    (candles.py: the ten sessions before the candle) taken before a pattern of several sessions, so its own candles
    are never the move it reverses"""
    if first < 11:
        return 0.0
    return (x.c[first - 1] - x.c[first - 11]) / x.atr


# Votes wait for evidence (the owner's rule, 2026-10-19: nothing arbitrary). The level rule separates the read's
# turning lows from other sessions no better than the same sessions shuffled (allfactors/candles_work/sweep_levels.py),
# and the study found no candle that holds alone. Until a study shows one predicts, the study's candles are read and
# shown as context and vote nothing; setting the flag restores every vote exactly as built (tests prove both).
CANDLESTICKS_VOTE = False


def facts(x, prior=()):
    out = _facts(x, prior)
    if CANDLESTICKS_VOTE:
        return out
    return [dataclasses.replace(f, cls="context", strength=0.0, rarity=0.0, clause="", wrong=None)
            if f.cls != "context" else f for f in out]


def _facts(x, prior=()):
    """the session's candle reading by the patterns the read's own candle facts do not already read (at most one;
    `prior`: the facts candles.py made for this read).

    The numbers are the read's own candle rule (candles.py), one rule for every candle the read counts, checked on
    the study's bars (scratchpad allfactors/candles_work/sweep_levels.py: 300 roster names, 48,624 sessions point in
    time through the read's levels.collect and areas, and the same names with their sessions shuffled):
      NEAR_ATR 0.6, "on a level": from the study's data. The share of the read's turning lows (minor swing lows)
        within a distance of a floor of two or more kinds, minus the share of other sessions, is largest at 0.60 ATR
        (a bootstrap over names: 0.55 to 0.65). Two or more kinds separates more than one kind (0.050 against 0.046)
        and three never does. The shuffled sessions separate as much (0.061 at 0.6 to 0.7): a level marks where lows
        land by the swings' own geometry, not a turn the order of the sessions adds, as the study found (no edge
        alone). Ceilings show no such separation at any distance (turning highs sit under a ceiling less often than
        other sessions); the floors' distance serves both, as it does in the read.
      PRIOR_ATR 1.0 over ten sessions, "after the move it reverses": neither decides. The real-minus-shuffled
        separation at the read's ten-session window peaks at 0.7 ATR with a 90% interval of 0.3 to 1.8 ATR (lows)
        and -0.1 to 1.5 (highs), which holds the read's 1.0; shorter windows separate more (three sessions: 0.080
        against 0.044). The read's rule is kept so one rule reads every candle; changing it changes the read's own
        candle facts, which is the owner's call."""
    from .candles import NEAR_ATR, PRIOR_ATR                    # the read's own candle rule (candles.py)
    if x.n < 30 or not x.atr:
        return []
    if any(f.family == "Candles" and f.side for f in prior):
        return []                                               # the read's own candle reads this session
    quiet = any(f.family == "Candles" for f in prior)           # a reading of this session with no side stands
    gap_days = {x.n - 1 - f.data["ago"] for f in prior if f.family == "Gaps" and f.side and "ago" in f.data}
    hits = scan(x.bars)
    cands = []
    for p in REG:
        v, first = hits[p.name]
        if not v or p.kind not in ("rev", "cont", "trap", "doji"):
            continue
        if any(first <= g for g in gap_days):
            continue                                            # the read's gap facts read these sessions
        side = 0 if p.kind == "doji" else int(v)
        before = moved(x, first)
        if p.kind == "rev" and not (before <= -PRIOR_ATR if side > 0 else before >= PRIOR_ATR):
            continue
        if p.kind == "cont" and not (before >= PRIOR_ATR if side > 0 else before <= -PRIOR_ATR):
            continue
        lo = min(float(b["l"]) for b in x.bars[first:])
        hi = max(float(b["h"]) for b in x.bars[first:])
        if side > 0:
            area = _level(x, lo, first, True, NEAR_ATR)
        elif side < 0:
            area = _level(x, hi, first, False, NEAR_ATR)
        else:
            area = _level(x, lo, first, True, NEAR_ATR) or _level(x, hi, first, False, NEAR_ATR)
        if area is None:
            continue
        cands.append((p, side, first, area, hi, before))
    sided = [c for c in cands if c[1]]
    if sided:
        if len({c[1] for c in sided}) > 1:
            return [_both(x, sided)]
        pool = sided
    elif quiet:
        return []
    else:
        pool = cands
    if not pool:
        return []
    pool.sort(key=lambda c: (c[2], c[0].rate))                 # the most candles, then the rarest in the study
    p, side, first, area, hi, before = pool[0]
    return [_fact(x, p, side, first, area, hi, before, [c[0] for c in pool[1:]])]


def _fact(x, p, side, first, area, hi, before, also):
    name = p.names[1] if side < 0 else p.names[0]
    what = p.whats[1] if side < 0 else p.whats[0]
    n = x.n - 1
    span = n - first + 1
    labels = area.labels(2)
    if p.kind in ("rev", "cont"):
        after = f", after {'falling' if before < 0 else 'rising'} {atr_words(before)} in the ten sessions before it"
    else:
        after = ""
    dates = f" ({x.when(first)} to {x.when(n)})" if span > 1 else ""
    verb = "completed" if span > 1 else "printed"
    kind = "rev1" if p.kind == "rev" and p.span == 1 else p.kind
    strength = STRENGTH[kind]
    head = f"{name[:1].upper()}{name[1:]} at {labels[0]}"         # the head names the level; the text and the
    more = f", also at {labels[1]}" if len(labels) > 1 else ""            # reading do not say it again (read/diet.py)
    text = f"{x.on(n, cap=True)} it {verb} {name}{dates}{more}{after}: {what}."
    reading = (f"Candle{'s' if span > 1 else ''} {x.when(first)}{('–' + x.when(n)) if span > 1 else ''}: "
               f"{bare(name)} ({labels[0]})")
    wrong = (hi, f"the high of the {bare(name)}") if side < 0 and hi > x.close else None
    return Fact("candle." + p.name, "Candles", "structure", side, strength if side else 0.0, head, text, reading,
                "cdl_" + p.name, rarity(p),
                {"pattern": p.name, "span": span, "first": first, "kind": p.kind, "before": before,
                 "level": labels, "also": [q.name for q in also]},
                f"it {verb} {name} at {labels[0]}", wrong)


def _both(x, sided):
    """patterns pointing both ways on the session's levels: stated, no vote"""
    order = sorted(sided, key=lambda c: (c[2], c[0].rate))
    up = next(c for c in order if c[1] > 0)
    dn = next(c for c in order if c[1] < 0)
    a, b = up[0].names[0], dn[0].names[1]
    return Fact("candle.both", "Candles", "structure", 0, 0.0, "Candles pointing both ways at a level",
                f"{x.on(x.n - 1, cap=True)} it completed {a} at {up[3].labels(1)[0]} and {b} at "
                f"{dn[3].labels(1)[0]}: the session's candles point both ways.",
                f"Candles {x.when(x.n - 1)}: {bare(a)} and {bare(b)}", "candles", 0.0,
                {"patterns": [up[0].name, dn[0].name]})


W.GLOSSARY.update({"cdl_" + p.name: (p.title, p.teach) for p in REG if p.kind in ("rev", "cont", "trap", "doji")})
