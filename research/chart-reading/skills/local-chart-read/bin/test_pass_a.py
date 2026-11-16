#!/usr/bin/env python3
"""Parity + regression tests for pass_a.py — thesis audit style.

Each indicator is checked against an INDEPENDENTLY WRITTEN reference
computation (different formulation, same contract), on deterministic
synthetic bars. The point is the thesis's 1,323-check discipline: our
EMA/ATR/pivot/oscillator numbers must reproduce from first principles,
not merely agree with themselves.

Run: python3 test_pass_a.py
"""
import math, random, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import pass_a as P

def synth_bars(n, seed=42):
    r = random.Random(seed)
    bars, px = [], 100.0
    for i in range(n):
        o = px
        drift = r.uniform(-1.5, 1.6)
        c = o + drift
        h = max(o, c) + r.uniform(0, 0.8)
        l = min(o, c) - r.uniform(0, 0.8)
        v = r.randint(1000, 9000)
        bars.append({"t": f"2026-01-{(i%28)+1:02d}T14:30:00Z",
                     "o": o, "h": h, "l": l, "c": c, "v": v})
        px = c
    return bars

BARS = synth_bars(300)
C = [b["c"] for b in BARS]
fails = []

def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + (f" [{detail}]" if detail and not cond else ""))
    if not cond: fails.append(name)

def close(a, b, tol=1e-9):
    if a is None and b is None: return True
    if a is None or b is None: return False
    return abs(a-b) <= tol*max(1, abs(a), abs(b))

# ---- EMA: closed-form weighted sum with matching seed convention ----
# P.ema uses the standard recursive EMA seeded with x[0]. The independent
# closed form is e_i = (1-a)^i * x_0 + sum_{j=1..i} a*(1-a)^(i-j) * x_j,
# provable by induction from the recurrence. (An earlier draft of this
# test used a self-normalized closed form — a different, also-legitimate
# convention — and "failed" on convention mismatch, not a code bug.)
def ref_ema(vals, n):
    a = 2/(n+1); out = [None]*len(vals)
    for i in range(n-1, len(vals)):
        s = (1-a)**i * vals[0]
        for j in range(1, i+1):
            s += a*(1-a)**(i-j)*vals[j]
        out[i] = s
    return out

for n in (12, 20, 50):
    mine, ref = P.ema(C, n), ref_ema(C, n)
    ok = all(close(m, r, 1e-9) for m, r in zip(mine, ref))
    check(f"ema{n} parity vs closed-form", ok)

# ---- ATR: naive TR + manual Wilder smoothing ----
def ref_atr(bars, n=14):
    trs = []
    for i, b in enumerate(bars):
        pc = bars[i-1]["c"] if i else b["c"]
        trs.append(max(b["h"]-b["l"], abs(b["h"]-pc), abs(b["l"]-pc)))
    out = [None]*len(bars)
    a = sum(trs[:n])  # seed = sum of first n
    for i in range(n, len(bars)):
        if i == n: a = (a + trs[n])/n
        else: a = (a*(n-1) + trs[i])/n
        out[i] = a
    return out

mine, ref = P.wilder_atr(BARS), ref_atr(BARS)
check("wilder_atr parity vs naive", all(close(m, r, 1e-9) for m, r in zip(mine, ref)))

# ---- pivots: brute-force window extremes ----
def ref_pivots(bars, L=5, R=5):
    res = []
    for i in range(L, len(bars)-R):
        w = bars[i-L:i+R+1]
        hi, lo = max(b["h"] for b in w), min(b["l"] for b in w)
        if bars[i]["h"] == hi: res.append(("H", bars[i]["h"]))
        if bars[i]["l"] == lo: res.append(("L", bars[i]["l"]))
    return res

mine = [(p["kind"], p["px"]) for p in P.pivots(BARS)]
check("pivots parity vs brute force", mine == ref_pivots(BARS),
      f"{len(mine)} vs {len(ref_pivots(BARS))}")

# ---- RSI: hand-rolled Wilder on a small fixture ----
# Wilder: first avg = SMA of first n changes; each subsequent value folds in
# the next change. (An earlier draft skipped the update at i==n — off-by-one
# in the REFERENCE, not in P.rsi_wilder.)
def ref_rsi(closes, n=14):
    chg = [closes[i]-closes[i-1] for i in range(1, len(closes))]
    g = [max(x, 0) for x in chg]; l = [max(-x, 0) for x in chg]
    ag = sum(g[:n])/n; al = sum(l[:n])/n
    out = [None]*len(closes)
    # first value at closes index n uses the first n changes (thesis: seed
    # uses n price changes, requiring n+1 prices)
    out[n] = 100.0 if al == 0 and ag > 0 else (50.0 if al == 0 else 100-100/(1+ag/al))
    for i in range(n, len(chg)):
        ag = (ag*(n-1) + g[i])/n; al = (al*(n-1) + l[i])/n
        out[i+1] = 100.0 if al == 0 and ag > 0 else (50.0 if al == 0 else 100-100/(1+ag/al))
    return out

mine, ref = P.rsi_wilder(C), ref_rsi(C)
ok = all(close(m, r, 1e-9) for m, r in zip(mine, ref) if not (m is None and r is None))
check("rsi_wilder parity vs hand-rolled", ok)

# ---- MACD: naive line/signal via the closed-form EMA ----
def ref_macd(closes):
    ef, es = ref_ema(closes, 12), ref_ema(closes, 26)
    line = [None if ef[i] is None or es[i] is None else ef[i]-es[i] for i in range(len(closes))]
    first = next(i for i, x in enumerate(line) if x is not None)
    sig = ref_ema(line[first:], 9)  # seeded with line[first], like P.macd
    signal = [None]*first + sig
    return line, signal

ml, ms, mh = P.macd(C); rl, rs = ref_macd(C)
check("macd line parity", all(close(m, r, 1e-9) for m, r in zip(ml, rl)))
check("macd signal parity",
      all(close(m, r, 1e-6) for m, r in zip(ms, rs) if not (m is None and r is None)))

# ---- CCI: naive recompute ----
def ref_cci(bars, n=20):
    tp = [(b["h"]+b["l"]+b["c"])/3 for b in bars]
    out = [None]*len(bars)
    for i in range(n-1, len(bars)):
        w = tp[i-n+1:i+1]; m = sum(w)/n
        md = sum(abs(x-m) for x in w)/n
        out[i] = (tp[i]-m)/(0.015*md) if md else 0.0
    return out

mine, ref = P.cci(BARS), ref_cci(BARS)
check("cci parity vs naive", all(close(m, r, 1e-9) for m, r in zip(mine, ref)))

# ---- ADX/DMI: naive recompute ----
def ref_adx(bars, n=14):
    up, dn, tr = [], [], []
    for i, b in enumerate(bars):
        if i == 0: up.append(0); dn.append(0); tr.append(b["h"]-b["l"])
        else:
            p = bars[i-1]; um = b["h"]-p["h"]; dm = p["l"]-b["l"]
            up.append(um if um > dm and um > 0 else 0)
            dn.append(dm if dm > um and dm > 0 else 0)
            tr.append(max(b["h"]-b["l"], abs(b["h"]-p["c"]), abs(b["l"]-p["c"])))
    def wrma(v):
        o = [None]*len(v); s = sum(v[:n])/n; o[n-1] = s
        for i in range(n, len(v)): o[i] = (o[i-1]*(n-1)+v[i])/n
        return o
    ru, rd, rt = wrma(up), wrma(dn), wrma(tr)
    pdi, mdi, dx = [None]*len(bars), [None]*len(bars), [None]*len(bars)
    for i in range(len(bars)):
        if rt[i]:
            pdi[i] = 100*ru[i]/rt[i]; mdi[i] = 100*rd[i]/rt[i]
            s = pdi[i]+mdi[i]; dx[i] = 100*abs(pdi[i]-mdi[i])/s if s else 0.0
    ax = wrma([0.0 if x is None else x for x in dx])
    return pdi, mdi, [None if dx[i] is None else ax[i] for i in range(len(bars))]

mp, mm, ma = P.adx_dmi(BARS); rp, rm, ra = ref_adx(BARS)
check("adx parity vs naive",
      all(close(m, r, 1e-9) for m, r in zip(ma, ra) if not (m is None and r is None)))
check("plus_di parity",
      all(close(m, r, 1e-9) for m, r in zip(mp, rp) if not (m is None and r is None)))

# ---- level_tests regression (the PLTR bug) ----
ATR = 5.90
# 1. PLTR case: prior HIGH 194.67, last bar below, close -0.10 ATR -> approach-below
bar = {"o": 192.0, "h": 193.9, "l": 191.5, "c": 194.08}
r = P.level_tests(194.67, "H", bar, ATR)
check("PLTR regression: prior high + bar below is NOT rejected-low-test",
      r["relationship"] == "approach-below", r["relationship"])

# 2. Genuine rejection of a high
bar = {"o": 194.0, "h": 196.5, "l": 193.5, "c": 194.4}  # pushed 0.31 ATR over, closed below
r = P.level_tests(194.67, "H", bar, ATR)
check("rejected-high-test fires correctly", r["relationship"] == "rejected-high-test", r["relationship"])

# 3. Genuine rejection of a low
bar = {"o": 191.0, "h": 191.5, "l": 189.2, "c": 191.2}  # pushed 0.30 ATR under, closed above
r = P.level_tests(191.0, "L", bar, ATR)
check("rejected-low-test fires correctly", r["relationship"] == "rejected-low-test", r["relationship"])

# 4. Break and hold above a high
bar = {"o": 194.0, "h": 196.5, "l": 194.2, "c": 196.0}
r = P.level_tests(194.67, "H", bar, ATR)
check("broke-above-held fires correctly", r["relationship"] == "broke-above-held", r["relationship"])

# 5. Bar far below a prior high -> no interaction
bar = {"o": 180.0, "h": 181.0, "l": 179.0, "c": 180.5}
r = P.level_tests(194.67, "H", bar, ATR)
check("far-below prior high -> None", r["relationship"] is None, r["relationship"])

# 6. Bar far above a prior low -> no interaction
bar = {"o": 200.0, "h": 201.0, "l": 199.0, "c": 200.5}
r = P.level_tests(191.0, "L", bar, ATR)
check("far-above prior low -> None", r["relationship"] is None, r["relationship"])

# 7. Nick of a high (wick touch, no penetration)
bar = {"o": 193.0, "h": 194.67, "l": 192.5, "c": 193.5}
r = P.level_tests(194.67, "H", bar, ATR)
check("wick touch -> nicked-high", r["relationship"] == "nicked-high", r["relationship"])

# ---- rsi_divergence: hand-built fixtures ----
pivs = [
    {"i": 10, "t": "2026-01-10T14:30:00Z", "kind": "L", "px": 100.0},
    {"i": 20, "t": "2026-01-20T14:30:00Z", "kind": "L", "px": 95.0},   # lower low
    {"i": 30, "t": "2026-01-30T14:30:00Z", "kind": "H", "px": 110.0},
    {"i": 40, "t": "2026-02-09T14:30:00Z", "kind": "H", "px": 115.0},  # higher high
]
rsi_fix = [None]*50
rsi_fix[10] = 30.0; rsi_fix[20] = 38.0   # higher RSI low -> bullish
rsi_fix[30] = 70.0; rsi_fix[40] = 62.0   # lower RSI high -> bearish
divs = P.rsi_divergence(pivs, rsi_fix)
check("rsi_divergence finds bullish", any(d["type"] == "bullish" for d in divs),
      str(divs))
check("rsi_divergence finds bearish", any(d["type"] == "bearish" for d in divs),
      str(divs))

rsi_fix2 = [None]*50
rsi_fix2[10] = 30.0; rsi_fix2[20] = 25.0  # lower RSI low -> no bullish
rsi_fix2[30] = 70.0; rsi_fix2[40] = 75.0  # higher RSI high -> no bearish
check("rsi_divergence quiet when absent", P.rsi_divergence(pivs, rsi_fix2) == [])

# too-close pivots (<5 bars apart) must not pair
pivs_close = [
    {"i": 10, "t": "2026-01-10T14:30:00Z", "kind": "L", "px": 100.0},
    {"i": 13, "t": "2026-01-13T14:30:00Z", "kind": "L", "px": 95.0},
]
rsi_fix3 = [None]*50; rsi_fix3[10] = 30.0; rsi_fix3[13] = 38.0
check("rsi_divergence respects min separation",
      P.rsi_divergence(pivs_close, rsi_fix3) == [])

# ---- fib_zones: exact arithmetic ----
fz = P.fib_zones([
    {"i": 10, "t": "2026-01-10T14:30:00Z", "kind": "L", "px": 100.0},
    {"i": 30, "t": "2026-01-30T14:30:00Z", "kind": "H", "px": 200.0},
])
check("fib_zones up-swing arithmetic",
      fz["levels"] == {"38.2%": 161.8, "50.0%": 150.0, "61.8%": 138.2}, str(fz))
check("fib_zones labeled policy", fz["note"] == "policy levels, not calibrated forecasts")
fz2 = P.fib_zones([
    {"i": 10, "t": "2026-01-10T14:30:00Z", "kind": "H", "px": 200.0},
    {"i": 30, "t": "2026-01-30T14:30:00Z", "kind": "L", "px": 100.0},
])
check("fib_zones down-swing arithmetic",
      fz2["levels"] == {"38.2%": 138.2, "50.0%": 150.0, "61.8%": 161.8}, str(fz2))

# ---- ema_stack ----
check("ema_stack bullish order", P.ema_stack(194.0, 185.0, 173.0, 159.0) == "C>20>50>200")
check("ema_stack mixed order", P.ema_stack(170.0, 185.0, 173.0, 159.0) == "20>50>C>200")
check("ema_stack missing 200", P.ema_stack(170.0, 185.0, 173.0, None) == "20>50>C")

# ---- candle_anatomy: exact arithmetic ----
ca = P.candle_anatomy({"o": 10.0, "h": 10.30, "l": 9.70, "c": 10.20}, 0.45)
check("candle_anatomy arithmetic",
      ca["range"] == 0.6 and ca["body"] == 0.2 and ca["upper_wick"] == 0.1
      and ca["lower_wick"] == 0.3 and ca["range_atr"] == 1.33
      and ca["direction"] == "up" and not ca["degenerate"], str(ca))
ca0 = P.candle_anatomy({"o": 10.0, "h": 10.0, "l": 10.0, "c": 10.0}, 0.45)
check("candle_anatomy zero-range policy", ca0["degenerate"] and ca0["range"] == 0)

# ---- failed_breakouts: hand-built tape ----
ATR_FB = 1.0
bars_fb = [
    {"t": "2026-01-01T14:30:00Z", "o": 98, "h": 100, "l": 97, "c": 99},    # 0
    {"t": "2026-01-02T14:30:00Z", "o": 99, "h": 100, "l": 98, "c": 99},    # 1 pivot H 100
    {"t": "2026-01-03T14:30:00Z", "o": 99, "h": 100.4, "l": 98, "c": 99},  # 2 poke 0.4, close back -> FAIL
    {"t": "2026-01-04T14:30:00Z", "o": 99, "h": 99.5, "l": 95, "c": 96},   # 3
    {"t": "2026-01-05T14:30:00Z", "o": 96, "h": 97, "l": 95, "c": 96},     # 4 pivot L 95
    {"t": "2026-01-06T14:30:00Z", "o": 96, "h": 97, "l": 94.6, "c": 96},   # 5 poke 0.4 under, close back -> FAIL
    {"t": "2026-01-07T14:30:00Z", "o": 96, "h": 102, "l": 96, "c": 101},   # 6 pivot H 102
    {"t": "2026-01-08T14:30:00Z", "o": 101, "h": 103, "l": 100, "c": 102.5},  # 7 close 0.5 over -> HELD
]
pivs_fb = [{"i": 1, "t": bars_fb[1]["t"], "kind": "H", "px": 100.0},
           {"i": 4, "t": bars_fb[4]["t"], "kind": "L", "px": 95.0},
           {"i": 6, "t": bars_fb[6]["t"], "kind": "H", "px": 102.0}]
fbs = P.failed_breakouts(bars_fb, pivs_fb, ATR_FB)
check("failed_breakouts finds failed high",
      any(f["level"] == 100.0 and f["kind"] == "H" for f in fbs), str(fbs))
check("failed_breakouts finds failed low",
      any(f["level"] == 95.0 and f["kind"] == "L" for f in fbs), str(fbs))
check("failed_breakouts silent on held breakout",
      not any(f["level"] == 102.0 for f in fbs), str(fbs))

# ---- contraction ----
bars_c = [{"t": f"2026-01-{i+1:02d}T14:30:00Z", "o": 100, "h": 102, "l": 98, "c": 100}
          for i in range(20)]
for j in range(10):  # strictly shrinking ranges
    i = 20 + j
    if j == 5:
        bars_c.append({"t": f"2026-01-{i+1:02d}T14:30:00Z", "o": 100, "h": 103,
                       "l": 99, "c": 100})  # pokes out: NOT inside
    else:
        bars_c.append({"t": f"2026-01-{i+1:02d}T14:30:00Z", "o": 100,
                       "h": round(101-0.05*j, 2), "l": round(99+0.05*j, 2), "c": 100})
atr_c = [2.0]*10 + [1.0]*20  # contracted by half 20 bars ago
co = P.contraction(bars_c, atr_c)
check("contraction ratio", co["atr_ratio_20b"] == 0.5, str(co))
check("contraction inside count", co["inside_bars_10"] == 9, str(co))

# ---- displacement ----
bars_dsp = [{"t": f"2026-01-{i+1:02d}T14:30:00Z", "o": 100, "h": 100.5, "l": 99.5, "c": 100}
            for i in range(20)]
bars_dsp[13] = {"t": "2026-01-14T14:30:00Z", "o": 100, "h": 104, "l": 99, "c": 103.5}
dsp = P.displacement(bars_dsp, 1.0)
check("displacement finds max bar",
      dsp["t"] == "2026-01-14" and dsp["range_atr"] == 5.0 and dsp["direction"] == "up",
      str(dsp))

# ---- cmf: exact arithmetic ----
bars_cmf = [
    {"t": "2026-01-01T14:30:00Z", "o": 10, "h": 12, "l": 8, "c": 11, "v": 100},   # signed +0.5
    {"t": "2026-01-02T14:30:00Z", "o": 11, "h": 12, "l": 8, "c": 9, "v": 300},    # signed -0.5
]
cmf2 = P.cmf(bars_cmf, 2)
check("cmf arithmetic", abs(cmf2[-1] - ((0.5*100 + -0.5*300)/400)) < 1e-12, str(cmf2))
check("cmf zero-volume -> 0",
      P.cmf([{"t": "x", "o": 10, "h": 12, "l": 8, "c": 11, "v": 0}], 1) == [0.0])

# ---- mfi: exact arithmetic ----
bars_mfi = []
tpv = 100.0
for i in range(15):
    tpv += 1.0  # always rising -> all positive
    bars_mfi.append({"t": f"2026-01-{i+1:02d}T14:30:00Z", "o": tpv-0.5, "h": tpv+0.5,
                     "l": tpv-0.5, "c": tpv, "v": 1000})
mfi1 = P.mfi(bars_mfi, 14)
check("mfi all-rising -> 100", mfi1[-1] == 100.0, str(mfi1[-1]))
bars_mfi2 = []
tpv = 100.0
for i in range(15):
    tpv -= 1.0  # always falling -> all negative
    bars_mfi2.append({"t": f"2026-01-{i+1:02d}T14:30:00Z", "o": tpv+0.5, "h": tpv+0.5,
                      "l": tpv-0.5, "c": tpv, "v": 1000})
check("mfi all-falling -> 0", P.mfi(bars_mfi2, 14)[-1] == 0.0)

# ---- level_clusters ----
pivs_lc = [
    {"i": 10, "t": "2026-01-10T14:30:00Z", "avail_t": "2026-01-15T14:30:00Z", "kind": "H", "px": 100.0},
    {"i": 20, "t": "2026-01-20T14:30:00Z", "avail_t": "2026-01-25T14:30:00Z", "kind": "H", "px": 100.4},
    {"i": 40, "t": "2026-02-09T14:30:00Z", "avail_t": "2026-02-14T14:30:00Z", "kind": "L", "px": 90.0},
]
bars_lc = [{"t": f"2026-01-{(i%28)+1:02d}T14:30:00Z", "o": 95, "h": 96, "l": 94, "c": 95}
           for i in range(50)]
bars_lc[12] = {"t": "2026-01-12T14:30:00Z", "o": 99, "h": 100.2, "l": 99, "c": 100}  # touches zone
bars_lc[30] = {"t": "2026-01-30T14:30:00Z", "o": 99, "h": 100.1, "l": 99, "c": 99.5}  # 2nd episode
zc = P.level_clusters(pivs_lc, bars_lc, 2.0)
top = zc[0]
check("level_clusters merges near pivots",
      top["pivot_touches"] == 2 and top["zone"] == [100.0, 100.4], str(top))
check("level_clusters counts episodes", top["episodes"] == 2, str(top))
check("level_clusters lone pivot separate", len(zc) == 2, str(len(zc)))

# ---- round_numbers ----
rn = P.round_numbers(194.08, 5.9)
check("round_numbers grid", [r["level"] for r in rn] == [185, 190, 195, 200, 205], str(rn))
check("round_numbers dist_atr",
      abs(rn[3]["dist_atr"] - round((200-194.08)/5.9, 2)) < 1e-9, str(rn[3]))

# ---- pivot availability timestamps ----
pb = P.pivots([{"t": f"2026-01-{i+1:02d}T14:30:00Z", "o": 100, "h": 100+i%3, "l": 99, "c": 100}
               for i in range(20)], 2, 2)
check("pivots carry avail_t", all("avail_t" in p for p in pb) and
      all(p["avail_t"] > p["t"] for p in pb), str(pb[:1]))

# ---- double_bottom ----
pivs_db = [
    {"i": 10, "t": "2026-01-10T14:30:00Z", "avail_t": "2026-01-15T14:30:00Z", "kind": "L", "px": 100.0},
    {"i": 16, "t": "2026-01-16T14:30:00Z", "avail_t": "2026-01-21T14:30:00Z", "kind": "H", "px": 108.0},
    {"i": 30, "t": "2026-01-30T14:30:00Z", "avail_t": "2026-02-04T14:30:00Z", "kind": "L", "px": 100.3},
]
db = P.double_bottom(pivs_db, 2.0)
check("double_bottom detects", len(db) == 1 and db[0]["neckline"] == 108.0, str(db))
check("double_bottom mismatch",
      abs(db[0]["low_mismatch_atr"] - 0.15) < 1e-9, str(db))
pivs_db2 = [
    {"i": 10, "t": "2026-01-10T14:30:00Z", "avail_t": "2026-01-15T14:30:00Z", "kind": "L", "px": 100.0},
    {"i": 30, "t": "2026-01-30T14:30:00Z", "avail_t": "2026-02-04T14:30:00Z", "kind": "L", "px": 105.0},
]
check("double_bottom rejects wide mismatch", P.double_bottom(pivs_db2, 2.0) == [])
pivs_db3 = [
    {"i": 10, "t": "2026-01-10T14:30:00Z", "avail_t": "2026-01-15T14:30:00Z", "kind": "L", "px": 100.0},
    {"i": 30, "t": "2026-01-30T14:30:00Z", "avail_t": "2026-02-04T14:30:00Z", "kind": "L", "px": 100.2},
]
check("double_bottom needs rebound", P.double_bottom(pivs_db3, 2.0) == [])

# ---- reset_candidate ----
bars_rc = []
px = 120.0
for i in range(40):
    px -= 0.8  # steady decline
    bars_rc.append({"t": f"2026-01-{(i%28)+1:02d}T14:30:00Z", "o": px+0.4, "h": px+0.5,
                    "l": px-0.5, "c": px, "v": 1000})
for i in range(40, 50):  # compression + improving closes at the lows
    px += 0.3
    bars_rc.append({"t": f"2026-02-{(i-39):02d}T14:30:00Z", "o": px-0.1, "h": px+0.2,
                    "l": px-0.2, "c": px, "v": 1000})
atr_rc = [2.0]*30 + [1.0]*20
clusters_rc = [{"zone": [90.5, 91.5]}]  # last close ~91 lands inside
rc = P.reset_candidate(bars_rc, clusters_rc, atr_rc, 1.0, 3)
check("reset_candidate components",
      rc["decline_atr"] > 2.0 and rc["compressed"] and rc["improving_closes"],
      str(rc))
rc2 = P.reset_candidate(bars_rc, [{"zone": [50.0, 51.0]}], atr_rc, 1.0, 3)
check("reset_candidate far from support -> not candidate",
      not rc2["candidate"] and rc2["dist_to_support_atr"] > 0.5, str(rc2))

# ---- last_bar_provisional ----
check("provisional returns bool-or-None",
      P.last_bar_provisional("2020-01-01T14:30:00Z") is False)

# ---- data_status ----
# 2026-10-14 hardening: the PARTIAL/VERIFIED legs previously hard-coded
# 2026-10-07 as "fresh"; data_status() compares last_t against the real
# wall-clock today (STALE when >3 days old), so the fixed date became
# STALE itself and all three legs failed on the calendar, not on logic.
# Verified against production pass_a.data_status: stale rule is
# (today - last_t) > 3 days. Fresh legs now use today's date dynamically.
from datetime import datetime as _dt
try:
    from zoneinfo import ZoneInfo as _ZI
    _today = _dt.now(_ZI("America/New_York")).strftime("%Y-%m-%d")
except Exception:
    _today = _dt.now().strftime("%Y-%m-%d")
_FRESH = _today + "T14:30:00Z"
check("data_status NO_VIEW", P.data_status(5, True, False, True, _FRESH) == "NO_VIEW")
check("data_status STALE",
      P.data_status(100, True, False, True, "2020-01-01T14:30:00Z") == "STALE")
check("data_status PARTIAL no-volume",
      P.data_status(100, False, False, True, _FRESH) == "PARTIAL")
check("data_status PARTIAL provisional",
      P.data_status(100, True, True, True, _FRESH) == "PARTIAL")
check("data_status PARTIAL no-ema200",
      P.data_status(100, True, False, False, _FRESH) == "PARTIAL")
check("data_status VERIFIED",
      P.data_status(260, True, False, True, _FRESH) == "VERIFIED")

# ---- frame_stance ----
check("stance higher", P.frame_stance(110, 100, 90) == "higher")
check("stance lower", P.frame_stance(80, 100, 90) == "lower")
check("stance sideways", P.frame_stance(95, 100, 90) == "sideways")
check("stance unresolved", P.frame_stance(95, None, None) == "unresolved")
check("stance one ma", P.frame_stance(95, 100) == "lower")

# ---- bar_payload_hash: deterministic + sensitive ----
bars_h = [{"t": "x", "o": 1, "h": 2, "l": 0.5, "c": 1.5, "v": 100}]
h1, h2 = P.bar_payload_hash(bars_h), P.bar_payload_hash(bars_h)
bars_h2 = [{"t": "x", "o": 1, "h": 2, "l": 0.5, "c": 1.6, "v": 100}]
check("hash deterministic", h1 == h2 and len(h1) == 16)
check("hash sensitive", P.bar_payload_hash(bars_h2) != h1)

# ---- split-adjustment regression (SOXX cure, 2026-11-10 lane4) ----
# Defect: fetch() called the bars CLI with NO --adjustment, so the CLI's
# raw default mixed pre-split history (old scale) with post-split bars.
# SOXX 3-for-1, effective 2026-11-05: raw closes Nov 4 450.41 -> Nov 5
# 131.90 (phantom -70.7%), printing ATR14 36.02 (24.57% of price) and
# RSI14 15.05 against the split-adjusted truth (ATR 8.19, RSI 39.11).
# Cure: fetch() passes --adjustment split explicitly for every frame.
# (a) Source assertion: the explicit split request is in fetch()'s call.
_src = (Path(__file__).parent / "pass_a.py").read_text()
check("fetch requests --adjustment split explicitly",
      '"--adjustment", "split"' in _src)
# (b) Captured-argv: fetch() must hand the CLI the split adjustment.
import subprocess as _sp_mod
class _FakeProc:
    returncode = 0; stdout = "[]"; stderr = ""
_captured = {}
_real_run = _sp_mod.run
def _fake_run(args, **kw):
    _captured["args"] = args
    return _FakeProc()
try:
    P.subprocess.run = _fake_run
    P.fetch("SOXX", "1D", 10)
finally:
    P.subprocess.run = _real_run
_a = _captured.get("args", [])
check("fetch argv carries split adjustment",
      "--adjustment" in _a and _a[_a.index("--adjustment") + 1] == "split"
      if "--adjustment" in _a else False, str(_a))
# (c) Live geometry: Pass A geometry on the fetched SOXX daily series
# must equal an independently computed split-adjusted reference (this
# file's own ref_ema / ref_atr / ref_rsi formulations) within 0.01, and
# no close-to-close jump over 25% may exist across the split window.
try:
    import json as _json
    _cli = Path.home() / "workspace/skills/alpaca-paper/bin/alpaca_get_bars_1h.py"
    _rp = _real_run([sys.executable, str(_cli), "--symbol", "SOXX",
                     "--timeframe", "1D", "--limit", "260",
                     "--adjustment", "split"],
                    capture_output=True, text=True, timeout=180)
    _ref_bars = _json.loads(_rp.stdout)
    _got_bars = P.fetch("SOXX", "1D", 260)
    _rc = [b["c"] for b in _ref_bars]; _gc = [b["c"] for b in _got_bars]
    check("SOXX fetched closes == split-adjusted reference closes",
          _gc == _rc, f"{len(_gc)} vs {len(_ref_bars)} bars")
    check("SOXX EMA20 split-adjusted parity",
          abs(P.ema(_gc, 20)[-1] - ref_ema(_rc, 20)[-1]) <= 0.01,
          f"{P.ema(_gc, 20)[-1]} vs {ref_ema(_rc, 20)[-1]}")
    check("SOXX EMA50 split-adjusted parity",
          abs(P.ema(_gc, 50)[-1] - ref_ema(_rc, 50)[-1]) <= 0.01,
          f"{P.ema(_gc, 50)[-1]} vs {ref_ema(_rc, 50)[-1]}")
    check("SOXX ATR14 split-adjusted parity",
          abs(P.wilder_atr(_got_bars)[-1] - ref_atr(_ref_bars)[-1]) <= 0.01,
          f"{P.wilder_atr(_got_bars)[-1]} vs {ref_atr(_ref_bars)[-1]}")
    check("SOXX RSI14 split-adjusted parity",
          abs(P.rsi_wilder(_gc)[-1] - ref_rsi(_rc)[-1]) <= 0.01,
          f"{P.rsi_wilder(_gc)[-1]} vs {ref_rsi(_rc)[-1]}")
    _win = [(b["t"][:10], b["c"]) for b in _got_bars
            if "2026-11-03" <= b["t"][:10] <= "2026-11-07"]
    _jumps = [abs(_win[i][1] / _win[i - 1][1] - 1)
              for i in range(1, len(_win))]
    check("SOXX no >25% close jump across split window",
          bool(_jumps) and max(_jumps) <= 0.25, str(_win))
except Exception as _e:  # live route unavailable: say so, do not pass it
    print(f"SKIP live SOXX split checks (fetch route failed: {_e})")

print()
if fails:
    print(f"{len(fails)} FAILURES: {fails}"); sys.exit(1)
print("ALL PARITY + REGRESSION TESTS GREEN")
