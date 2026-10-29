"""Elliott wave, read the way the research says it earns its place (Frost & Prechter's rules; EWAVES practice;
docs/research/2026-10-18-terminal/SETUPS_V2.md and the scratch notes elliott_targets.md): not as a target oracle
(Fibonacci ratios have no statistical support: Batchelor & Ramyar 2006, Bulkowski 2020) but as a disciplined map of
where price sits in its trend and of the price that proves a reading wrong.

Counts run on the intermediate swings (4 ATR) with the minor swings (1.5 ATR) as subdivision evidence. Two families:
the impulse (five legs with the trend) and the zigzag (three legs against it), each in every position that ends in
the leg in progress. The hard rules kill a count, the current price included: wave 2 never passes wave 1's start, wave
3 is never the shortest, wave 4 never enters wave 1's range, a zigzag's B never passes A's start. Guidelines rank the
survivors: the canonical ratios (in log space, within 7%), alternation of waves 2 and 4, proportion, wave 3 carrying
the most volume and the momentum peak, and the subdivision. A count is clear when its fit is 0.6 or more and it
leads the best reading that forecasts the other way by 0.30 in relative support; tentative at 0.15; otherwise there
is no clear count, and the read names the two readings and the price that decides between them.

This is context: it moves no number in the plan or the evidence (SYNTHESIS_SPEC section 8, until a validation
protocol and the owner's ruling promote it)."""
import math

from . import pivots
from .core import MAJOR_K, Fact
from .words import p as pct_words

K_INTER, K_MINOR = 4.0, 1.5
TOL = 0.07                     # log-ratio proximity for the canonical ratios
TEMP = 0.10                    # softmax temperature for relative support
RATIOS = {"w2": (0.5, 0.618), "w3": (1.618, 2.618, 1.0), "w4": (0.236, 0.382, 0.5), "w5": (1.0, 0.618),
          "b": (0.5, 0.618), "c": (1.0, 1.618, 0.618)}


def _prox(r, targets):
    if r <= 0:
        return 0.0
    return max(math.exp(-(math.log(r / t) ** 2) / (2 * TOL * TOL)) for t in targets)


def _len(a, b):
    return abs(math.log(b.price / a.price))


def _sub(minor, a, b):
    """minor legs inside the leg a->b"""
    return sum(1 for p in minor if a.i < p.i < b.i) + 1


def _rsi_max(x, a, b):
    w = [v for v in x.rsi[a.i:b.i + 1] if v is not None]
    return max(w) if w else None


def _vol(x, a, b):
    w = x.vol[a.i + 1:b.i + 1]
    return sum(w) / len(w) if w else 0.0


def _impulse(x, seq, minor, bull):
    """a parse of seq (origin first, the last pivot the leg in progress) as an impulse, or None when a rule breaks"""
    s = 1 if bull else -1
    pr = [pv.price for pv in seq]
    n = len(seq) - 1                                      # legs: 2 -> W2 in progress ... 6 -> W5 complete, A forming
    if n < 2 or n > 6:
        return None
    def up(a, b):
        return (b - a) * s > 0                            # b lies beyond a in the trend's direction
    if n >= 2 and not up(pr[0], pr[2]) and pr[2] != pr[0]:
        return None                                       # R1: wave 2 passed wave 1's start
    if n >= 4 and not up(pr[1], pr[4]):
        return None                                       # R3: wave 4 entered wave 1's range (so wave 3 passed wave 1)
    w = [_len(seq[i], seq[i + 1]) for i in range(n)]
    if n >= 5:
        w1, w3, w5 = w[0], w[2], w[4]
        if w3 < w1 and w3 < w5 and seq[5].confirmed:
            return None                                   # R2: wave 3 the shortest
        if w3 < w1 and w5 > w3 * 1.03:
            return None                                   # R2 cap: wave 5 cannot pass p4 + wave 3 when wave 3 < wave 1
    f, wt = [], []
    if n >= 2:
        f.append(_prox(w[1] / w[0], RATIOS["w2"])), wt.append(1.0)
    if n >= 3 and seq[3].confirmed:
        f.append(_prox(w[2] / w[0], RATIOS["w3"])), wt.append(1.0)
    if n >= 4 and seq[4].confirmed:
        f.append(_prox(w[3] / w[2], RATIOS["w4"])), wt.append(1.0)
        d2, d4 = w[1] / w[0], w[3] / w[2]
        f.append(1.0 if (d2 >= 0.5) != (d4 >= 0.5) else 0.0), wt.append(0.5)        # alternation
        f.append(1.0 if _vol(x, seq[2], seq[3]) > max(_vol(x, seq[1], seq[2]), _vol(x, seq[3], seq[4])) else 0.0)
        wt.append(0.5)
    if n >= 5 and seq[5].confirmed:
        f.append(_prox(w[4] / w[0], RATIOS["w5"])), wt.append(1.0)
        r3, r5 = _rsi_max(x, seq[2], seq[3]), _rsi_max(x, seq[4], seq[5])
        if r3 is not None and r5 is not None:
            f.append(1.0 if (r3 > r5) == bull else 0.0), wt.append(0.5)             # momentum peaks in wave 3
    legs = w[:n] if seq[-1].confirmed else w[:n - 1]
    if len(legs) >= 3:
        med = sorted(legs)[len(legs) // 2]
        f.append(1.0 if all(0.15 * med <= v <= 4.0 * med for v in legs) else 0.0), wt.append(0.5)
    subs = [_sub(minor, seq[i], seq[i + 1]) for i in range(n) if seq[i + 1].confirmed]
    if subs:
        good = sum(1 for i, k in enumerate(subs) if (k in (5, 9) if i % 2 == 0 else k in (3, 7)) or k == 1)
        f.append(good / len(subs)), wt.append(0.5)
    fit = sum(a * b for a, b in zip(f, wt)) / sum(wt) if wt else 0.0
    pos = {2: "wave 2", 3: "wave 3", 4: "wave 4", 5: "wave 5", 6: "a correction after wave 5"}[n]
    if n == 6:
        forecast = -s
    elif n in (2, 4):
        forecast = s                                       # the counter-wave is in progress; the trend resumes after it
    else:
        forecast = s
    p0, p1 = pr[0], pr[1]
    w1 = p1 - p0
    if n == 2:
        hard, typical = p0, pr[2] + 1.618 * w1
    elif n == 3:
        hard, typical = p0, pr[2] + 1.618 * w1
    elif n == 4:
        hard, typical = p1, pr[4] + w1
    elif n == 5:
        cap = pr[4] + (pr[3] - pr[2]) if w[2] < w[0] else None
        hard, typical = p1, pr[4] + 0.618 * (pr[3] - p0)
        if cap is not None and (typical - cap) * s > 0:
            typical = cap
    else:
        hard, typical = pr[5], pr[4]                       # the correction aims at wave 4's territory
    thesis = pr[2] if n == 3 else pr[4] if n == 5 else None   # the wave-2 low under wave 3, the wave-4 low under 5
    return {"family": "impulse", "bull": bull, "position": pos, "legs": n, "fit": fit, "forecast": forecast,
            "hard": hard, "thesis": thesis, "target": typical, "seq": seq}


def _zigzag(x, seq, minor, bull_trend):
    """a parse of seq as a zigzag against the trend (A, B, C), or None"""
    s = -1 if bull_trend else 1                            # the correction's direction
    pr = [pv.price for pv in seq]
    n = len(seq) - 1
    if n < 2 or n > 4:
        return None
    if n >= 2 and not ((pr[2] - pr[0]) * s > 0 or pr[2] == pr[0]):
        return None                                        # B passed A's start
    a = _len(seq[0], seq[1])
    f, wt = [], []
    if n >= 2:
        f.append(_prox(_len(seq[1], seq[2]) / a, RATIOS["b"])), wt.append(1.0)
    if n >= 3 and seq[3].confirmed:
        f.append(_prox(_len(seq[2], seq[3]) / a, RATIOS["c"])), wt.append(1.0)
        f.append(1.0 if (pr[3] - pr[1]) * s > 0 else 0.0), wt.append(0.5)         # C beyond A's end
    subs = [_sub(minor, seq[i], seq[i + 1]) for i in range(min(n, 3)) if seq[i + 1].confirmed]
    if subs:
        good = sum(1 for i, k in enumerate(subs) if (k in (5, 9) if i % 2 == 0 else k in (3, 7)) or k == 1)
        f.append(good / len(subs)), wt.append(0.5)
    fit = sum(u * v for u, v in zip(f, wt)) / sum(wt) if wt else 0.0
    if n == 2:
        pos, forecast, hard, target = "wave B of a correction", s, pr[0], pr[2] + (pr[1] - pr[0])
    elif n == 3:
        pos, forecast, hard, target = "wave C of a correction", s, pr[0], pr[2] + (pr[1] - pr[0])
    else:
        pos, forecast, hard, target = "the end of a correction", -s, pr[3], pr[0]
    return {"family": "zigzag", "bull": bull_trend, "position": pos, "legs": n, "fit": fit, "forecast": forecast,
            "hard": hard, "thesis": pr[2] if n == 3 else None, "target": target, "seq": seq}


def count(x):
    """{state, primary, alternate} or None without enough swings"""
    inter = x.major if abs(MAJOR_K - K_INTER) < 1e-9 else pivots.zigzag(x.bars, x.atrs, K_INTER)
    minor = pivots.zigzag(x.bars, x.atrs, K_MINOR)
    if len(inter) < 4:
        return None
    parses = []
    conf_idx = [j for j, pv in enumerate(inter) if pv.confirmed]
    for o in conf_idx[-10:]:
        seq = inter[o:]
        if len(seq) < 3:
            continue
        o_pv = seq[0]
        lows = [pv.price for pv in seq if pv.kind == "L"]
        highs = [pv.price for pv in seq if pv.kind == "H"]
        if o_pv.kind == "L" and o_pv.price <= min(lows) + 1e-12:
            for parse in (_impulse(x, seq, minor, True), _zigzag(x, seq, minor, False)):
                if parse:
                    parses.append(parse)
        if o_pv.kind == "H" and o_pv.price >= max(highs) - 1e-12:
            for parse in (_impulse(x, seq, minor, False), _zigzag(x, seq, minor, True)):
                if parse:
                    parses.append(parse)
    if not parses:
        return None
    for q in parses:                                       # the leg in progress must not have already killed it
        s = 1 if q["forecast"] > 0 else -1
        if (x.close - q["hard"]) * s < 0:
            q["fit"] = -1.0
    parses = [q for q in parses if q["fit"] >= 0]
    if not parses:
        return None
    ws = [math.exp(q["fit"] / TEMP) for q in parses]
    tot = sum(ws)
    for q, w_ in zip(parses, ws):
        q["support"] = w_ / tot
    parses.sort(key=lambda q: -q["fit"])
    prim = parses[0]
    alt = next((q for q in parses[1:] if q["forecast"] != prim["forecast"]), None)
    margin = prim["support"] - (alt["support"] if alt else 0.0)
    known = sum(1 for pv in prim["seq"][1:] if pv.confirmed)          # legs whose end is confirmed
    state = "clear" if prim["fit"] >= 0.6 and margin >= 0.30 and known >= 3 else \
        "tentative" if margin >= 0.15 and known >= 2 else "none"
    return {"state": state, "primary": prim, "alternate": alt, "margin": margin}


def _words(q, x):
    up = q["forecast"] > 0
    trend = "up" if q["bull"] else "down"
    if q["family"] == "impulse":
        if q["legs"] == 6:
            what = f"a five-wave {trend}move looks complete; a correction is under way"
        elif q["legs"] in (2, 4):
            what = f"{q['position']} of a five-wave {trend}move, a pause before the next leg {trend}"
        else:
            what = f"{q['position']} of a five-wave {trend}move"
    else:
        what = f"{q['position']} against the {'up' if q['bull'] else 'down'}trend"
    return what.replace("upmove", "advance").replace("downmove", "decline")


def facts(x):
    c = count(x) if x.n >= 120 else None
    if not c or c["state"] == "none":
        alt = (c or {}).get("alternate")
        prim = (c or {}).get("primary")
        text = "The swings do not settle into one clear wave count."
        if prim and alt:
            text = (f"Two wave counts compete: {_words(prim, x)}, or {_words(alt, x)}.")
        return [Fact("elliott.count", "Elliott wave", "context", 0, 0.0, "No clear wave count", text,
                     "Elliott wave: no clear count", "elliott", 0.0, {"state": "none"})]
    q = c["primary"]
    hard_pct = x.pct_of(q["hard"])
    tgt_pct = x.pct_of(q["target"])
    side = 1 if q["forecast"] > 0 else -1
    word = "clear" if c["state"] == "clear" else "tentative"
    th = q.get("thesis")
    doubt = ""
    if th is not None and (x.close - th) * side > 0 and abs(x.pct_of(th)) < abs(hard_pct):
        doubt = (f"; it is in doubt on a close {'below' if side > 0 else 'above'} {pct_words(x.pct_of(th))} "
                 f"({'the wave-2 low' if q['legs'] == 3 and q['family'] == 'impulse' else 'the wave-4 low' if q['family'] == 'impulse' else 'the wave-B extreme'})")
    text = (f"The {word} count: {_words(q, x)}{doubt}. The count is wrong on a close "
            f"{'below' if side > 0 else 'above'} {pct_words(hard_pct)}"
            + (f"; its next leg typically reaches {pct_words(tgt_pct)}." if abs(tgt_pct) <= 30 and
               (tgt_pct > 0) == (side > 0) else "."))
    if c["alternate"] and c["state"] != "clear":
        text += f" The other reading: {_words(c['alternate'], x)}."
    return [Fact("elliott.count", "Elliott wave", "context", side, 0.0,
                 ("Waves point up" if side > 0 else "Waves point down") + f" ({word} count)", text,
                 f"Elliott wave: {_words(q, x)} ({word})", "elliott", 0.3 if word == "clear" else 0.1,
                 {"state": c["state"], "position": q["position"], "family": q["family"], "hard": q["hard"],
                  "target": q["target"], "fit": round(q["fit"], 2), "margin": round(c["margin"], 2)})]
