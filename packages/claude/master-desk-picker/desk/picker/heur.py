"""The Heuristics panel: every heuristic on the owner's list, live, point in time and graded (docs/research/
HEURISTICS_ACCEPTANCE.md; the edition's `heur` block and heur-names.json, schema docs/research/heur_SCHEMA.md).

SCOPE (InfinityBlade, 2026-10-27):
  Surface   this module, the edition's `heur` block (desk/terminal/__init__.py merges ALLOWED under it), the lazily
            fetched heur-names.json and the weekly `heur_inputs` job (S&P 500 list, split history).
  Constraints  pure functions of closed daily bars up to `as_of` (cutting later bars never changes an answer); the
            feature and veto formulas are desk/picker/fearday.py's, imported read-only; every threshold is the
            research's, frozen (engine/EVIDENCE.md, xcheck/avoid/RESULTS.md); no price or volume floor: capacity is a
            label, the lane never sorts by liquidity; a measure the desk cannot take reads "unavailable", never a
            default; no sleeve, take, plan, size or board place moves.
  Outcome   a market banner (which timing heuristics are ON today, each with its grade and what it changes), the
            AVOID flags per name with their named reasons, an "Avoided today" lane, per-name buy-side chips (today's
            value against the day's median), the standing exit line and the refuted list.
  Proof     tests/test_heur.py (hand-built bars, known answers).
  Edges     reverse-split history and the S&P 500 list come from the weekly job; until a name is checked its flag
            reads unmeasured. With SPY under its 200-day the flags are listed and marked "veto off" (the edge reverses).
"""
import datetime as dt
import json
import os
from html.parser import HTMLParser

import numpy as np
import pandas as pd

from ..util import ET
from . import fearday as FD

# ---- the research, copied ------------------------------------------------------------------------------------------
# key: (label, grade, number, effect). number = the graded holdout numbers (xcheck/avoid/RESULTS.md M0, 2023+, vs the
# same-day same-tier mean); effect = |20-day holdout excess| in points, used only to order the lane
REASONS = {
    "spike_day": ("+25% day with no earnings", "A", "20 d -3.14% (t -5.5); fresh pumps -10.6% (t -5.6)", 3.14),
    "far_above_50d": ("Stretched: 1.6x the 50-day or more", "A", "20 d -5.63% (t -4.3); 60 d -8.09%", 5.63),
    "dead_cat": ("Dead-cat bounce", "B", "20 d -4.63% (t -5.5); 60 d -8.29% (t -4.0)", 4.63),
    "reverse_splits": ("Repeat reverse splits", "B", "20 d -3.6% (t -3.7); 60 d -6.5%", 3.6),
    "new_listing": ("New listing (under 252 sessions)", "B", "20 d -0.79% (t -2.5); 60 d -3.63% (t -5.3)", 0.79),
    "pump_nano": ("Fresh pump in a nano name", "A", "20 d -9.05% (t -9.8); 60 d -16.62% (t -16.8)", 9.05),
    "mfi_nano": ("Money flow 75 or more in a nano name", "B", "20 d -1.89% (t -5.5); 60 d -4.44% (t -9.7)", 1.89),
}
REASON_NOTES = {"spike_day": "Earnings reports from the Nasdaq archive explain a move; a name with none on file is "
                             "judged without them.",
                "reverse_splits": "Needs the weekly split history; a name not yet checked is unavailable.",
                "pump_nano": "Nano = the thinnest fifth of the day's names by 20-day dollar volume.",
                "mfi_nano": "Nano = the thinnest fifth of the day's names by 20-day dollar volume."}
VETO_VALUE = ("Names that pass the avoid veto beat those that fail it by +6.9% (discovery) and +10.7% (holdout) over 60 "
              "days, net of costs (t 7.1 / 8.5); micro names +3.6% / +6.7%.")
STACKED = "Four or more warnings together: -3.36% (t -3.3) discovery, -7.45% (t -8.2) holdout over 20 days."
REMOVED = ("The small-cap 20-day-loser veto was removed: its sign flipped (+0.69% in discovery, -0.43% in holdout, "
           "not significant).")
REVERSED = "+2.64% over 20 days (t 2.2) in the holdout"
CHIPS = (
    ("F3", "Pullback deeper than its own usual", "B", "UP", "higher",
     "Uptrend names on fear days: a deeper pullback than the stock's own norm ranks higher. IC +0.026 / +0.031 "
     "(t 4.3 / 4.3), same sign in both eras.",
     "Fear days only; otherwise information. A plain pullback is refuted."),
    ("N1", "Pullback that is the market's, not the company's", "B", "UP", "higher",
     "Uptrend names on fear days: indiscriminate selling hurts names that did nothing wrong. IC +0.026 / +0.028; all "
     "days +0.001.", "Fear days only. Raw log, no written study."),
    ("N7", "Gap-downs bought back (10 sessions)", "B", "UP", "higher",
     "Uptrend names on fear days: absorbed supply. IC +0.018 / +0.017; all days +0.008 / +0.006.",
     "Fear days only."),
    ("F7", "10-day return vs SPY", "B", "RESET", "lower",
     "Deep resets: laggards win. IC -0.041 in both eras (t -5.5 / -4.9).",
     "Deep resets only (35% under the high, near the low). Lower is better."),
    ("F6", "Selling volume vs the month before", "B", "RESET", "higher",
     "Deep resets: capitulation volume is better. IC +0.040 / +0.020; spreads +0.95 / +1.28 points.",
     "Deep resets only."),
    ("MOM", "Six-month gain (126 days)", "B", "ALL", "higher",
     "Liquid names: the top tenth beat the market by +15.4% / +20.8% over a 63-day hold.",
     "A ranking tilt, never a buy signal: in small caps a tie-break only, and not shown to beat SPY as a portfolio."),
    ("DIP", "Momentum dip", "B", "ALL", "true",
     "Top 30% on six-month gain and bottom 30% on the 5-day return: +5.9% per trade over matched random picks on "
     "fear days (t 2.35).",
     "Beats random but not SPY: as a ladder its portfolio t is 1.2 and its Sharpe 0.85 is under SPY's 1.41. It does "
     "not beat SPY."),
    ("NVI", "Negative volume index vs its 1-year average", "B", "ALL", "true",
     "Quiet-day accumulation: above the 255-day average is +0.8 (t 6.2) in every tier, both eras.",
     "Needs 300 sessions."),
    ("SP", "S&P 500 member", "B", "ALL", "true",
     "S&P 500 members beat by +0.37% / +0.39% (t 2.8 / 3.3); S&P 600 members lag -0.74% / -0.78%.",
     "Survivors-only study. The list is fetched weekly from a public source."),
    ("YD", "Last session's return", "A", "ALL", "lower",
     "In drawdowns yesterday's losers beat yesterday's winners: IC -0.058 / -0.028 in the deepest SPY-drawdown third.",
     "Counts only while SPY is in that drawdown third (the banner says)."),
)
REFUTED = (
    ("Textbook pullbacks to the 20/50-day", "+0.05R vs random +0.08R; a first tag of the 20-day lags (t -2.18)",
     "EV S18"),
    ("Stacking reversal confirmations", "4+ signs -0.15R vs random +0.07R", "EV S19"),
    ("Named setups on their own (VCP, flags, breakouts, pocket pivots)",
     "naive breakout excess +0.03 [-0.90, 1.01] over 47,037 cases", "EV S20"),
    ("The 9,861 mined rules", "0 of 9,861 pass the false-discovery test", "EV S21"),
    ("Elliott waves and Fibonacci", "wave setups 1.07x the shuffle; Fibonacci mass 0.99-1.04x", "EV S22"),
    ("AI chart reading", "partial IC +0.003 [-0.046, +0.052]; contaminated by training memory", "EV S22, D8"),
    ("Echo's calls", "median -4.8% vs SPY", "EV S22"),
    ("Raw Tensor markers and the old board ranking", "1D cyan -0.3% (t -2.4); board +0.012R vs random -0.021R",
     "EV S23"),
    ("Calendar effects", "ruled out", "EV T10"),
    ("Breadth or internals to call direction", "no internal calls SPY or IWM; they size volatility only", "EV T11"),
    ("Red-day and red-open entries", "tier A -0.88 out of sample", "EV T12"),
    ("Trailing stops, profit caps, early exits", "159 of 159 significant results were harmful", "EV E1"),
    ("Shorting the avoid list", "gross +2%/yr, net -27% to -36%/yr after borrow and squeezes", "AV M5, EV A16"),
    ("Small-cap 20-day-loser veto", "sign flipped (+0.69% then -0.43%): removed", "AV M0"),
    ("Kelly sizing and per-name HMM", "ruled out", "EV V7"),
    ("Gap and limit filters, breakout-stop entries", "rejected", "EV X5"),
)
LANE_TOP = 40
MOMDIP = (0.7, 0.3)              # C4: six-month gain in the top 30%, 5-day return in the bottom 30% (RESULTS2)
VRP_RICH, VRP_CHEAP, VRP_WINDOW, VRP_MIN = 0.9, 0.1, 252, 126
DD_WINDOW, DD_HIST, DD_MIN = 252, 756, 252
NVI_SPAN, NVI_MIN = 255, 300
EXIT = ("Hold about 60 sessions from the next open and leave on time. Trailing stops, profit caps and early exits hurt: "
        "159 of 159 significant trailing-stop results were harmful.")

ALLOWED = {
    "": {"kind", "as_of", "provisional", "market", "avoid", "avoided", "n", "chips", "buy", "exit", "refuted", "gaps"},
    "market": {"tape", "items"},
    "market.items[]": {"key", "title", "on", "state", "ev_grade", "reading", "evidence", "changes"},
    "avoid": {"on", "state", "text", "veto_value", "stacked", "removed", "reasons"},
    "avoid.reasons[]": {"key", "label", "ev_grade", "number", "measured", "note"},
    "avoided[]": {"symbol", "tier", "tier_word", "close", "n", "capacity_usd", "flags", "off"},
    "n": {"universe", "flagged", "avoided", "no_data", "unmeasured"},
    "chips[]": {"key", "label", "ev_grade", "applies", "good", "evidence", "caution", "median"},
    "buy": {"fear", "text", "caveat"},
    "exit": {"text", "hold"},
    "refuted[]": {"label", "why", "source"},
}


# ---- indicators ---------------------------------------------------------------------------------------------------
def nvi(close, vol):
    """the negative volume index from 1000: it follows the close on a day whose volume fell from the day before and
    stands still on any other day"""
    c, v = close.astype(float).reset_index(drop=True), vol.astype(float).reset_index(drop=True)
    out, cur = [], 1000.0
    for i in range(len(c)):
        if i and v[i] < v[i - 1] and c[i - 1]:
            cur *= c[i] / c[i - 1]
        out.append(cur)
    return pd.Series(out)


def _r(x, nd=3):
    return None if x is None or (isinstance(x, float) and not np.isfinite(x)) else round(float(x), nd)


# ---- the banner ---------------------------------------------------------------------------------------------------
def _row(key, title, on, state, grade, reading, evidence, changes):
    return {"key": key, "title": title, "on": on, "state": state, "ev_grade": grade, "reading": reading,
            "evidence": evidence, "changes": changes}


def _pct(x, nd=1):
    return f"{x * 100:.{nd}f}%"


def market(spy_bars, vix=None, both_red=None, as_of=None, params=None):
    """-> {"tape", "items"}: the timing heuristics and whether each is ON at as_of's close"""
    p = params or FD.CONFIG
    spy = FD._cut(spy_bars, as_of) if as_of else list(spy_bars or ())
    s = FD._spy(spy)
    ms = FD.market_state(spy, vix=vix, params=p)
    items = []
    # T2 losers beat winners in drawdowns
    dd = (s / s.rolling(DD_WINDOW).max() - 1).dropna()
    hist = dd.iloc[-DD_HIST - 1:-1]
    ev = ("Last-day return IC -0.058 / -0.028 in the deepest SPY-drawdown third (discovery / holdout); 393 confirmed "
          "pairs against a null of 17 (EV T2).")
    ch = "Marks every name's last-session move: while ON, yesterday's losers are the ones to favour over yesterday's winners."
    if len(hist) < DD_MIN or not len(dd):
        items.append(_row("drawdown_reversal", "Losers beat winners", None, "Not measured", "A",
                          "Unavailable: needs about two years of SPY history.", ev, ch))
    else:
        cut, now = float(hist.quantile(1 / 3)), float(dd.iloc[-1])
        on = now < cut
        items.append(_row("drawdown_reversal", "Losers beat winners", on, "ON" if on else "OFF", "A",
                          f"SPY is {_pct(-now)} under its 1-year high; the deepest third of the last three years "
                          f"starts at {_pct(-cut)}." + ("" if on else " Not deep enough today."), ev, ch))
    # T1 fear day
    why = ms.get("why") or []
    ret = float(s.pct_change().iloc[-1]) if len(s) > 1 else 0.0
    words = {"spy_drop": f"SPY fell {abs(ret) * 100:.1f}% today", "below_50d": "SPY closed under its 50-day",
             "vol_spike": "SPY's 20-day volatility is above 1.5x its 1-year median",
             "vix_spike": "the VIX is above 1.5x its 1-year median"}
    ev = ("Fear, risk-off and VIX-spike days lift every long entry: +0.13R vs +0.035R, uptrend names +0.29 to +0.36R. "
          "Random entries get the same lift, so this is market timing, not chart shape (EV T1).")
    items.append(_row("fear_day", "Fear day", bool(ms["fear"]), "ON" if ms["fear"] else "OFF", "B",
                      (lambda x: x[0].upper() + x[1:] + ".")("; ".join(words[w] for w in why if w in words)) if ms["fear"] else
                      "No fear signal: SPY is not down 1%, it is over its 50-day and volatility is normal.", ev,
                      "ON: the buy-side chips below are the ones the research ranks and the Fear-Day Buy List opens. "
                      "OFF: they are information only."))
    items.append(_row("two_red", "SPY and QQQ both red", both_red, "ON" if both_red else "OFF" if both_red is False
                      else "Not measured", "P",
                      "SPY and QQQ both closed red." if both_red else "Not both red." if both_red is False else
                      "Unavailable: QQQ's close is not in the desk's cache.",
                      "The owner's rule (2026-10-18): a long is bought only on a day its fund and the name both close "
                      "red. The Execution Lab is measuring it forward; no result yet.",
                      "Timing only: it is not the Buy List's fear-day rule (SPY down 1% or more, under its 50-day, or a volatility spike)."))
    # T4 SPY above a rising 200-day
    m200 = s.rolling(p["bull"]["ma"]).mean()
    bull = ms.get("bull")
    ev = ("Leader setups pay +0.1 to +0.2% per 20 days with SPY above a rising 200-day, against -1.2 to -1.3% "
          "otherwise: a 1.3 to 1.5 point gap in both eras (EV T4).")
    ch = ("ON: leader and momentum names are worth ranking. OFF: they are not, and avoid flags are not used (below the "
          "200-day the avoid edge reverses).")
    if bull is None:
        items.append(_row("trend_200", "SPY above a rising 200-day", None, "Not measured", "B",
                          "Unavailable: needs 220 sessions of SPY.", ev, ch))
    else:
        gap = float(s.iloc[-1] / m200.iloc[-1] - 1)
        rising = bool(m200.iloc[-1] > m200.shift(p["bull"]["rising_lookback"]).iloc[-1])
        reading = (f"SPY is {_pct(abs(gap))} {'above' if gap >= 0 else 'below'} its 200-day, which is "
                   f"{'rising' if rising else 'falling'}.")
        items.append(_row("trend_200", "SPY above a rising 200-day", bull, "ON" if bull else "OFF", "B", reading, ev, ch))
    # T3 the option premium (VIX minus realized volatility)
    ev = ("Index months after a top-tenth premium were better: DIA +489 bp per 60 days (t 5.2), both eras; "
          "index only (EV T3).")
    ch = "Nothing on single names. Rich means index entries have been better; cheap means no edge is claimed."
    vrp = None
    if vix and vix.get("dates") and len(s) > 25:
        vx = pd.Series(vix["close"], index=vix["dates"], dtype=float)
        rv = s.pct_change().rolling(21).std() * np.sqrt(252) * 100
        vrp = (vx.reindex(s.index) - rv).dropna()
        if not len(vrp) or vrp.index[-1] != s.index[-1] or len(vrp.iloc[-VRP_WINDOW:]) < VRP_MIN:
            vrp = None
    if vrp is None:
        items.append(_row("vrp", "Option premium vs realized volatility", None, "Not measured", "B",
                          "Unavailable: no VIX close for today, or under a year of history.", ev, ch))
    else:
        w = vrp.iloc[-VRP_WINDOW:]
        rank = float((w <= w.iloc[-1]).mean())
        state = "Rich" if rank >= VRP_RICH else "Cheap" if rank <= VRP_CHEAP else "Normal"
        items.append(_row("vrp", "Option premium vs realized volatility", state == "Rich", state, "B",
                          f"The VIX is {w.iloc[-1]:.1f} points over SPY's 21-day realized volatility, a higher gap "
                          f"than {rank * 100:.0f}% of the last year.", ev, ch))
    # the avoid edge by regime
    ma = s.rolling(p["vetoes"]["off_below_spy_ma"]).mean()
    ok = None if pd.isna(ma.iloc[-1]) else bool(s.iloc[-1] >= ma.iloc[-1])
    items.append(_row("avoid_regime", "Avoid flags work", ok, "ON" if ok else "OFF" if ok is False else "Not measured",
                      "B", "SPY is over its 200-day." if ok else "SPY is under its 200-day." if ok is False else
                      "Unavailable: needs 200 sessions of SPY.",
                      f"The avoid edge is a calm-bull effect; with SPY under its 200-day it reverses ({REVERSED}) "
                      "(AV M6).", "ON: the flags below are the veto. OFF: they stay listed but the veto is off; "
                      "the edge reverses."))
    return {"tape": _tape(items), "items": items}


def _tape(items):
    d = {x["key"]: x for x in items}
    parts = []
    f = d["fear_day"]
    parts.append("Fear day" if f["on"] else "Calm day")
    t = d["trend_200"]["on"]
    parts.append("SPY over a rising 200-day" if t else "SPY not over a rising 200-day" if t is False else
                 "200-day unavailable")
    v = d["vrp"]["state"]
    if v in ("Rich", "Cheap"):
        parts.append(f"option premium {v.lower()}")
    if d["drawdown_reversal"]["on"]:
        parts.append("in a deep drawdown: losers beat winners")
    a = d["avoid_regime"]["on"]
    tail = ("avoid flags are live" if a else "avoid flags are off (the edge reverses)" if a is False else "")
    return ", ".join(parts) + ("; " + tail if tail else "") + "."


# ---- per-name flags -----------------------------------------------------------------------------------------------
def _spike(fr, i, earn, p):
    """a +25% day in the window that no earnings report explains (the report on that day or up to 3 days before)"""
    vp = p["vetoes"]["spike_day"]
    x = fr["r"].iloc[max(0, i - vp["window"] + 1):i + 1]
    days = [fr["d"].iloc[k] for k in x.index if x[k] >= vp["day"]]
    if earn is not None:
        ed = [dt.date.fromisoformat(e) for e in earn]
        days = [d for d in days if not any(0 <= (dt.date.fromisoformat(d) - e).days <= 3 for e in ed)]
    return bool(days)


def flags_of(fr, i, tier, splits, earn, p):
    """{reason: True | False | None} for the owner's seven avoid reasons (None = unavailable)"""
    res = FD.warnings(fr, i, tier, splits, p)
    out = {k: res[k][0] for k in REASONS if k != "spike_day"}
    out["spike_day"] = _spike(fr, i, earn, p)
    return {k: out[k] for k in REASONS}


# ---- the build ----------------------------------------------------------------------------------------------------
def _median(xs):
    xs = [x for x in xs if x is not None]
    return _r(float(np.median(xs))) if xs else None


def build(universe, spy_bars, vix=None, as_of=None, splits=None, members=None, earnings=None, both_red=None,
          params=None):
    """-> (the edition's `heur` block, {symbol: {s, t, a, ao?, c}} for heur-names.json). universe {sym: daily bars};
    splits {sym: [{"ex","num","den"}]} (a name absent from it is unchecked) or None; members a set of S&P 500 symbols or
    None; earnings {sym: [report dates]} or None"""
    p = params or FD.CONFIG
    spy = FD._cut(spy_bars, as_of) if as_of else list(spy_bars or ())
    mk = market(spy, vix=vix, both_red=both_red, params=p)
    ms = FD.market_state(spy, vix=vix, params=p)
    as_of = ms["as_of"]
    gaps = []
    block = {"kind": "heuristics", "as_of": as_of, "provisional": bool(p.get("provisional")), "market": mk}
    rows, no_data = [], 0
    for sym in sorted(universe):
        bars = FD._cut(universe[sym], as_of) if as_of else []
        if not bars or FD._day(bars[-1]) != as_of:
            no_data += 1
            continue
        fr = FD.frame(bars, spy, p)
        i = len(fr) - 1
        if FD.bad_print(fr, i, p):
            no_data += 1
            continue
        rows.append((sym, fr, i))
    dv = pd.Series({s: fr["dv20"].iloc[i] for s, fr, i in rows}, dtype=float).dropna()
    q = p["tiers"]["quintiles"]
    tiers = {s: int(min(q, np.ceil(x * q))) for s, x in dv.rank(pct=True).items()}
    s_ = FD._spy(spy)
    ma = s_.rolling(p["vetoes"]["off_below_spy_ma"]).mean()
    spy_ok = not (len(ma) and pd.notna(ma.iloc[-1]) and s_.iloc[-1] < ma.iloc[-1])
    dd_on = next(x for x in mk["items"] if x["key"] == "drawdown_reversal")["on"]
    # cross-sectional pieces: momentum-dip percentiles and the last-session ranks
    mom = pd.Series({s: fr["MOM126"].iloc[i] for s, fr, i in rows}, dtype=float)
    r5 = pd.Series({s: fr["r5"].iloc[i] for s, fr, i in rows}, dtype=float)
    yd = pd.Series({s: fr["r"].iloc[i] for s, fr, i in rows}, dtype=float)
    pm, p5, py = mom.rank(pct=True), r5.rank(pct=True), yd.rank(pct=True)
    names, flagged, unmeasured, vals = {}, [], 0, {k[0]: {} for k in CHIPS}
    for sym, fr, i in rows:
        tier = tiers.get(sym)
        sp_ = splits.get(sym) if splits is not None else None
        fl = flags_of(fr, i, tier, sp_, (earnings or {}).get(sym) if earnings is not None else None, p)
        unmeasured += fl["reverse_splits"] is None
        hit = [k for k, v in fl.items() if v]
        st = fr["state"].iloc[i]
        ent = {"s": st, "t": tier, "a": hit, "c": []}
        if hit and not spy_ok:
            ent["ao"] = True
        c = {}
        if st == "UP":
            for k in ("F3", "N1", "N7"):
                c[k] = _r(fr[k].iloc[i])
        if st == "RESET":
            c["F7"] = _r(fr["F7"].iloc[i] * 100, 2)
            c["F6"] = _r(fr["F6"].iloc[i], 2)
        c["MOM"] = _r(mom[sym] * 100, 1) if pd.notna(mom[sym]) else None
        c["DIP"] = (bool(pm[sym] >= MOMDIP[0] and p5[sym] <= MOMDIP[1]) if pd.notna(pm.get(sym)) and
                    pd.notna(p5.get(sym)) else None)
        if len(fr) >= NVI_MIN:
            n_ = nvi(fr["c"], fr["v"])
            c["NVI"] = _r((n_.iloc[-1] / n_.ewm(span=NVI_SPAN, adjust=False).mean().iloc[-1] - 1) * 100, 2)
        else:
            c["NVI"] = None
        c["SP"] = (sym.upper() in members) if members is not None else None
        c["YD"] = _r(yd[sym] * 100, 2) if pd.notna(yd[sym]) else None
        for k, v in c.items():
            vals[k][sym] = v
        names[sym] = ent
        if hit:
            eff = sum(REASONS[k][3] for k in hit)
            flagged.append((-len(hit), -eff, sym, fl, tier, fr, i, hit))
    med = {k: _median([v for v in d.values() if v is not None and not isinstance(v, bool)]) for k, d in vals.items()}
    leg = {k[0]: k for k in CHIPS}
    for sym, ent in names.items():
        out = []
        for k in ("F3", "N1", "N7", "F7", "F6", "MOM", "DIP", "NVI", "SP", "YD"):
            if sym not in vals[k]:
                continue
            v = vals[k][sym]
            out.append([k, v, _good(k, v, med.get(k), leg[k][4], yd, py, sym, dd_on)])
        ent["c"] = out
    flagged.sort(key=lambda t: t[:3])
    avoided = [{"symbol": sym, "tier": tier, "tier_word": p["tiers"]["words"].get(str(tier)) if tier else None,
                "close": _r(float(fr["c"].iloc[i]), 2), "n": len(hit),
                "capacity_usd": int(round(p["plan"]["adv_cap"] * float(fr["dv20"].iloc[i] or 0))),
                "flags": hit, "off": not spy_ok}
               for _, _, sym, _, tier, fr, i, hit in flagged[:LANE_TOP]]
    no_splits = splits is None or bool(rows and unmeasured == len(rows))
    reasons = [{"key": k, "label": v[0], "ev_grade": v[1], "number": v[2],
                "measured": not (k == "reverse_splits" and no_splits),
                "note": REASON_NOTES.get(k, "")} for k, v in REASONS.items()]
    block["avoid"] = {"on": spy_ok if len(ma) and pd.notna(ma.iloc[-1]) else None,
                      "state": "Live" if spy_ok else "Veto off",
                      "text": ("SPY is over its 200-day, where the avoid veto has worked: do not buy a flagged name."
                               if spy_ok else
                               f"SPY is under its 200-day: the avoid edge reverses here ({REVERSED}), so flags are "
                               "listed but the veto is off."),
                      "veto_value": VETO_VALUE, "stacked": STACKED, "removed": REMOVED, "reasons": reasons}
    block["avoided"] = avoided
    block["n"] = {"universe": len(rows), "flagged": len(flagged), "avoided": len(flagged) if spy_ok else 0,
                  "no_data": no_data, "unmeasured": unmeasured}
    block["chips"] = [{"key": k, "label": lab, "ev_grade": g, "applies": ap, "good": good, "evidence": ev,
                       "caution": ca, "median": med.get(k)} for k, lab, g, ap, good, ev, ca in CHIPS]
    fear = bool(ms["fear"])
    block["buy"] = {"fear": fear,
                    "text": ("Fear day: the research ranks pullback depth, bystander and gap-absorbed in uptrend "
                             "names, and laggards and capitulation volume in deep resets. The chips show today's value "
                             "against the day's median." if fear else
                             "Calm day: the buy-side features are graded on fear days (on all days their IC is near "
                             "zero). The chips are information."),
                    "caveat": "Momentum and the momentum dip beat random picks; neither has been shown to beat SPY as a "
                              "portfolio."}
    block["exit"] = {"text": EXIT, "hold": 60}
    block["refuted"] = [{"label": a, "why": b, "source": c_} for a, b, c_ in REFUTED]
    if splits is None:
        gaps.append("Repeat reverse splits: the desk has not collected split history yet, so no name can carry this flag.")
    elif unmeasured:
        gaps.append(f"Repeat reverse splits: {unmeasured} of {len(rows)} names have not been checked yet.")
    if members is None:
        gaps.append("S&P 500 membership: the list has not been fetched, so the chip reads unavailable.")
    if earnings is None:
        gaps.append("Earnings dates: the Nasdaq archive could not be read, so +25% days are not tested for news.")
    block["gaps"] = gaps
    return block, names


def _good(key, v, med, direction, yd, py, sym, dd_on):
    """True when the value is on the side the evidence favours, False when on the other, None when it does not apply"""
    if v is None:
        return None
    if key == "DIP":
        return True if v else None
    if key in ("SP", "NVI"):
        return bool(v) if key == "SP" else v > 0
    if key == "YD":
        if not dd_on or pd.isna(py.get(sym)):
            return None
        return True if py[sym] <= 1 / 3 else False if py[sym] >= 2 / 3 else None
    if med is None:
        return None
    return v > med if direction == "higher" else v < med


# ---- the names file -----------------------------------------------------------------------------------------------
def save_names(dash_dir, as_of, names):
    os.makedirs(dash_dir, exist_ok=True)
    p = os.path.join(dash_dir, "heur-names.json")
    with open(p + ".tmp", "w", encoding="utf-8") as f:
        json.dump({"as_of": as_of, "names": names}, f, separators=(",", ":"))
    os.replace(p + ".tmp", p)
    return p


# ---- inputs the weekly job keeps ---------------------------------------------------------------------------------
MEMBERS_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
MIN_MEMBERS = 400


class _Table(HTMLParser):
    def __init__(self):
        super().__init__()
        self.depth, self.tr, self.td, self.buf, self.out = 0, False, 0, "", []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "table":
            self.depth = self.depth + 1 if self.depth else (1 if a.get("id") == "constituents" else 0)
        elif self.depth and tag == "tr":
            self.tr, self.td, self.buf = True, 0, ""
        elif self.depth and self.tr and tag == "td":
            self.td += 1
            self.buf = ""

    def handle_endtag(self, tag):
        if tag == "table" and self.depth:
            self.depth -= 1
        elif self.depth and tag == "td" and self.td == 1:
            s = self.buf.strip()
            if s:
                self.out.append(s)

    def handle_data(self, data):
        if self.depth and self.td == 1:
            self.buf += data


def parse_sp500(html):
    """the symbols in the constituents table of the public list page, sorted"""
    t = _Table()
    t.feed(html or "")
    return sorted(set(t.out))


def _variants(syms):
    out = set()
    for s in syms:
        s = s.upper()
        out |= {s, s.replace(".", "-"), s.replace("-", ".")}
    return out


def members_path(root):
    return os.path.join(root, "cache", "sp500_members.json")


def save_members(root, symbols, now):
    os.makedirs(os.path.dirname(members_path(root)), exist_ok=True)
    with open(members_path(root) + ".tmp", "w") as f:
        json.dump({"at": now, "symbols": sorted(symbols)}, f)
    os.replace(members_path(root) + ".tmp", members_path(root))


def load_members(root):
    """the S&P 500 symbols (with their dot and dash spellings), or None when the list was never fetched"""
    try:
        with open(members_path(root)) as f:
            return _variants((json.load(f) or {}).get("symbols") or []) or None
    except (OSError, ValueError):
        return None


def refresh_members(root, now, fetch=None):
    if fetch is None:
        from ..data import http
        fetch = lambda: http.get(MEMBERS_URL, as_text=True, headers={"User-Agent": "Master Desk research (Jack Tailor)"})
    syms = parse_sp500(fetch())
    if len(syms) < MIN_MEMBERS:                     # a page change must not wipe a good list
        return {"error": f"only {len(syms)} symbols parsed", "kept": True}
    save_members(root, syms, now)
    return {"members": len(syms)}


def splits_path(root):
    return os.path.join(root, "cache", "heur_splits.json")


def _splits_state(root):
    try:
        with open(splits_path(root)) as f:
            return json.load(f) or {}
    except (OSError, ValueError):
        return {}


def refresh_splits(root, yahoo, symbols, now, batch=150, years=3):
    """check the `batch` least recently checked names for splits over `years` (Yahoo chart events), merge into the
    cache; the roster is covered in rotation -> {"checked", "known"}"""
    st = _splits_state(root)
    order = sorted(set(symbols), key=lambda s: ((st.get(s) or {}).get("at", -1), s))[:batch]
    n = 0
    for s in order:
        try:
            ev = yahoo.events(s, now - years * 365.25 * 86400, now)
        except Exception:                           # noqa: BLE001  (one name never stops the rotation)
            continue
        st[s] = {"at": now, "splits": [{"ex": dt.datetime.fromtimestamp(e["t"], tz=ET).date().isoformat(),
                                        "num": e["num"], "den": e["den"]} for e in ev.get("splits") or []]}
        n += 1
    os.makedirs(os.path.dirname(splits_path(root)), exist_ok=True)
    with open(splits_path(root) + ".tmp", "w") as f:
        json.dump(st, f)
    os.replace(splits_path(root) + ".tmp", splits_path(root))
    return {"checked": n, "known": len(st)}


def load_splits(root):
    """{sym: [{"ex","num","den"}]} for the names checked (plus the last 14 days of held names' events), or None"""
    st = _splits_state(root)
    out = {s: list(v.get("splits") or []) for s, v in st.items()}
    try:
        from ..feedlib import corp_actions
        for s, ev in corp_actions.load(root).items():
            have = {x["ex"] for x in out.get(s, [])}
            out.setdefault(s, []).extend(x for x in ev.get("splits") or [] if x["ex"] not in have and
                                         "num" in x and "den" in x)
    except Exception:                               # noqa: BLE001
        pass
    return out or None
