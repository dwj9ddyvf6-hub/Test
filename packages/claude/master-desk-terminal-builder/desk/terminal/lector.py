"""ChartsLector's Opportunity Score, rebuilt on the desk's own bars (edition `lector`).

His method, from his posted rankings (2026-09-17 to 10-06, nine sessions, 450 rows; Author-research/CHARTSLECTOR
out/ranker_fit.md and scratch/cos/chartslector/SPECS.md section 1):
  - the list: his curated liquid tech and AI names that have 2X leveraged ETFs, about 45-55 at a time, changing slowly.
    He never published it; LIST is every ticker seen in his posted tables (66). A name ranks when its bars are there.
  - Opp = mean(S10, S20, S42, S63), S_h = b_h*Breakout + e_h*Expansion + r_h*Risk with his exact weights (WEIGHTS):
    Opp = 0.40 Breakout + 0.35 Expansion + 0.25 Risk. Bands: top 10%, 25%, 50% by floor(p*N).
  - Breakout, Expansion and Risk are not disclosed. COEFS is the desk's fit to his numbers (all nine sessions):
    in-sample Opp MAE 1.9; held out on three later sessions MAE 3.2, rank rho 0.88, top-10 overlap 67%.
  - u_ terms are percentiles against the broad universe (the desk's 1,838-name roster: his RS and ATR Rank columns
    match a broad US universe at r >= 0.997); l_ terms rank within the day's list.
Daily closes only (his is a daily table): the session of the cached bars, computed once per session and kept.

  lector  {as_of, credit, n, rows: [{rank, symbol, score, band, parts: [Breakout, Expansion, Risk]}]}   None until a session has been scored"""
import bisect
import math
import os
from datetime import datetime, timezone

from ..util import read_json, write_json_atomic

LIST = ("AAOI ADI AEHR ALAB AMD ANET ARM ASML AXTI BE BMNR BTDR CBRS CHYM COHR COHU CRDO CRM CRWD CRWV DASH DELL EOSE "
        "FORM GLW GTLB HOOD HPE INFQ INTC IREN KEYS LITE LRCX MPWR MRVL MSTR MTSI MU NBIS NET NOK NOW NTAP OKTA OUST "
        "PANW PATH POET PURR QCOM RBRK RDW RMBS SKHY SMCI SMTC SNDK SNOW SPCX STX TER TSM UMC ZETA").split()
WEIGHTS = {"S10": (0.50, 0.20, 0.30), "S20": (0.45, 0.30, 0.25), "S42": (0.35, 0.40, 0.25), "S63": (0.30, 0.50, 0.20)}
COEFS = {   # out/ranker_fit.md "Production refit on all sessions"
    "Breakout": (5.1, {"l_pos21": 0.215, "u_slope20": 0.095, "u_atr5_20": -0.156, "u_upfrac20": 0.202,
                       "u_sharpe63": 0.150, "u_er20": 0.399, "l_er20": -0.216}),
    "Expansion": (27.8, {"ext_abs2.5": -6.304, "u_ret21": 0.217, "u_atrp": 0.325, "u_dhi252": 0.180,
                         "u_xs150": -0.128, "u_dhi50": -0.075}),
    "Risk": (97.3, {"ext_abs2": 1.069, "u_atrp": -0.405, "u_bbw": -0.274, "ext_under0.5": -24.892,
                    "ext_over2.5": -11.746, "u_xs200": 0.125})}
RAW = ("pos21", "slope20", "atr5_20", "upfrac20", "sharpe63", "er20", "ret21", "atrp", "dhi252", "xs150", "dhi50",
       "bbw", "xs200")
NEED = 260                      # bars: the 252-day high plus the moving averages' warm-up
MIN_UNIVERSE = 20
CREDIT = ("ChartsLector's Opportunity Score: his formula and his names, rebuilt on the desk's bars "
          "(its Breakout, Expansion and Risk parts are fitted to his posted tables)")


def _sma(x, n):
    return sum(x[-n:]) / n if len(x) >= n else None


def _std(x, n):
    if len(x) < n:
        return None
    m = sum(x[-n:]) / n
    return math.sqrt(sum((v - m) ** 2 for v in x[-n:]) / n)


def _rma_last(x, n):
    """Pine ta.rma (Wilder): seeded with the mean of the first n values, then alpha 1/n"""
    if len(x) < n:
        return None
    v = sum(x[:n]) / n
    for t in x[n:]:
        v += (t - v) / n
    return v


def features(bars):
    """the last bar's raw terms {name: value} and e50ATR from daily bars [{h,l,c}], oldest first; None when short"""
    if not bars or len(bars) < NEED:
        return None
    b = bars[-NEED:]
    try:
        H, L, C = [float(x["h"]) for x in b], [float(x["l"]) for x in b], [float(x["c"]) for x in b]
    except (KeyError, TypeError, ValueError):
        return None
    if min(C) <= 0:
        return None
    tr = [H[0] - L[0]] + [max(H[i] - L[i], abs(H[i] - C[i - 1]), abs(L[i] - C[i - 1])) for i in range(1, len(C))]
    a14 = _rma_last(tr, 14)
    if not a14:
        return None
    c = C[-1]

    def hi(n): return max(H[-n:])
    def lo(n): return min(L[-n:])
    dl = [math.log(C[i] / C[i - 1]) for i in range(1, len(C))]
    ad = [abs(C[i] - C[i - 1]) for i in range(1, len(C))]
    m20, s20 = _sma(C, 20), _std(C, 20) * math.sqrt(20 / 19)
    sd63 = _std(dl, 63) * math.sqrt(63 / 62)
    m20_lag5, tr20, ad20 = sum(C[-25:-5]) / 20, _sma(tr, 20), sum(ad[-20:])
    return {
        "pos21": (c - lo(21)) / (hi(21) - lo(21)) if hi(21) > lo(21) else None,
        "slope20": m20 / m20_lag5 - 1,
        "atr5_20": _sma(tr, 5) / tr20 if tr20 else None,
        "upfrac20": sum(1 for i in range(-20, 0) if C[i] > C[i - 1]) / 20,
        "sharpe63": (sum(dl[-63:]) / 63) / sd63 if sd63 else None,
        "er20": abs(c - C[-21]) / ad20 if ad20 else None,
        "ret21": c / C[-22] - 1,
        "atrp": a14 / c,
        "dhi252": c / hi(252) - 1,
        "xs150": (c - _sma(C, 150)) / a14,
        "dhi50": c / hi(50) - 1,
        "bbw": 4 * s20 / m20,
        "xs200": (c - _sma(C, 200)) / a14,
        "e50ATR": (c - _sma(C, 50)) / a14,
    }


def _lpct(values):
    """percentile rank inside the list (average ties), x100: {symbol: pct}"""
    items = sorted((v, s) for s, v in values.items() if v is not None)
    n, out, i = len(items), {}, 0
    while i < n:
        j = i
        while j + 1 < n and items[j + 1][0] == items[i][0]:
            j += 1
        for k in range(i, j + 1):
            out[items[k][1]] = ((i + j) / 2 + 1) / n * 100
        i = j + 1
    return out


def _term(name, f, u, l, sym):
    e = f["e50ATR"]
    if name.startswith("ext_abs"):
        return abs(e - float(name[7:]))
    if name.startswith("ext_under"):
        return max(float(name[9:]) - e, 0.0)
    if name.startswith("ext_over"):
        return max(e - float(name[8:]), 0.0)
    return (u if name.startswith("u_") else l)[name[2:]].get(sym)


def rank(list_feats, universe_feats):
    """[{rank, symbol, score, band}] for the list names with every term, by Opp; universe_feats includes the list"""
    univ = {k: sorted(f[k] for f in universe_feats.values() if f and f.get(k) is not None) for k in RAW}
    if min(len(v) for v in univ.values()) < MIN_UNIVERSE:
        return []
    feats = {s: f for s, f in list_feats.items() if f}
    u = {k: {s: bisect.bisect_left(univ[k], f[k]) / len(univ[k]) * 100 for s, f in feats.items()
             if f.get(k) is not None} for k in RAW}
    l = {k: _lpct({s: f.get(k) for s, f in feats.items()}) for k in RAW}
    rows = []
    for s, f in feats.items():
        comp = {}
        for name, (const, terms) in COEFS.items():
            vals = [_term(t, f, u, l, s) for t in terms]
            if any(v is None for v in vals):
                break
            comp[name] = min(100.0, max(0.0, const + sum(w * v for w, v in zip(terms.values(), vals))))
        else:
            b, e, r = comp["Breakout"], comp["Expansion"], comp["Risk"]
            opp = sum(wb * b + we * e + wr * r for wb, we, wr in WEIGHTS.values()) / len(WEIGHTS)
            rows.append({"symbol": s, "score": round(opp, 1), "parts": [round(b, 1), round(e, 1), round(r, 1)]})
    rows.sort(key=lambda r: (-r["score"], r["symbol"]))
    n = len(rows)
    for i, r in enumerate(rows, 1):
        r["rank"] = i
        r["band"] = ("Top 10%" if i <= math.floor(0.10 * n) else "Top 25%" if i <= math.floor(0.25 * n)
                     else "Top 50%" if i <= math.floor(0.50 * n) else "Lower 50%")
    return rows


def _day(b):
    return datetime.fromtimestamp(float(b[-1]["t"]), tz=timezone.utc).date().isoformat() if b else None


def table(root, hub, universe_names, diag=None):
    """the edition's `lector` block: scored once per session of the cached daily bars (the list's own bars fetched
    when the roster lacks them) and kept in cache/terminal/lector.json"""
    path = os.path.join(root, "cache", "terminal", "lector.json")
    st = read_json(path, None) or {}
    if hub is not None:
        try:
            probe = hub.bars("equity_split", "1d", ["SPY"], NEED + 5, cache_only=True) or {}
            as_of = _day(probe.get("SPY"))
            if as_of and st.get("as_of") != as_of:
                univ = {}
                for i in range(0, len(universe_names), 200):
                    got = hub.bars("equity_split", "1d", universe_names[i:i + 200], NEED + 5, cache_only=True) or {}
                    univ.update({s: features(b) for s, b in got.items() if _day(b) == as_of})
                miss = [s for s in LIST if univ.get(s) is None]
                if miss:
                    got = hub.bars("equity_split", "1d", miss, NEED + 5) or {}
                    univ.update({s: features(b) for s, b in got.items() if _day(b) == as_of})
                rows = rank({s: univ.get(s) for s in LIST}, univ)
                if diag is not None:
                    diag["lector"] = f"{len(rows)} of {len(LIST)} names ranked on {as_of}, universe {len(univ)}"
                if rows:
                    st = {"as_of": as_of, "n": len(rows), "rows": rows}
                    write_json_atomic(path, st)
        except Exception as e:                       # a failed read keeps the last table
            if diag is not None:
                diag["lector"] = f"{type(e).__name__}: {str(e)[:120]}"
    if not st.get("rows"):
        return None
    return {"as_of": st["as_of"], "credit": CREDIT, "n": st["n"], "rows": st["rows"][:15]}
