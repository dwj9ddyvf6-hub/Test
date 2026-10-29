"""The Execution Lab's improvement arms (exp1, 2026-10-26). The owner, 2026-10-25: "Any opportunities to enhance,
execute them", and of ChartsLector's tools "Execute all". The Edge audits' EXPERIMENTs and ChartsLector's tools run
as paired shadow variants on the desk's own signals: the same signals and capital, the incumbent beside each arm, the
seeded placebo, and the desk's real fills. Nothing here trades, routes, sizes or changes a sleeve.

Every arm states in ARMS what changes, what stays the same, the result expected if the idea is right, a rival
explanation, its REJECTION RULE and the minimum sample before any review. Until an arm holds that sample the report
shows it as descriptive and says so (report.arms). Passing a rule is never an adoption: that is the owner's.

  eq01_open_print   AUDIT_EQ.md EQ-01: opening entries filled at the official opening print instead of when the first
                    pass routes them. Facts per signal row: arms.eq01."""
import json
import os

from .. import calendar as cal
from ..util import et_date
from . import avoid, quotes
from . import stats as S
from .tape import in_session, session_for

AUCTION_BPS = 2.0          # EQ-01: the opening auction's cost, charged to the arm (the audit's "net of 2 bps")
FIRST_PASS_S = 300         # a decision inside the session's first pass (by 09:35 ET) is an opening entry (AUDIT_EQ 2.4)
FILL_WITHIN_S = 1200       # ... and the desk's first fill came within 20 minutes of the open (the audit's method)
DEFAULT_WINDOW_S = 6 * 3600   # the engine's child window when an intent sets none (config/desk.json
#                               default_child_window_s; desk/engine.py's own default)


class Windows:
    """the entry windows the decision tape noted (desk/lab/quotes.py windows), read once per ET date; the desk's
    default child window from config/desk.json"""

    def __init__(self, root):
        self.root, self._days = root, {}
        try:
            with open(os.path.join(root, "config", "desk.json")) as f:
                self.default_s = float(json.load(f).get("default_child_window_s") or DEFAULT_WINDOW_S)
        except (OSError, ValueError, TypeError, AttributeError):
            self.default_s = DEFAULT_WINDOW_S

    def get(self, t0, sym, key):
        d = et_date(t0)
        if d not in self._days:
            self._days[d] = quotes.windows(self.root, d)
        return self._days[d].get((round(float(t0), 3), sym, key or ""))


def _next_hour(t0):
    """the canonical hour the tensor plane's 1h lots enter in: the first open-anchored hour starting after t0 (this
    session's, else the next session's first) -> (its session, its start, its end)"""
    from ..feedlib.canonical import session_opens
    d = cal._as_date(float(t0))
    for _ in range(8):
        for s in session_opens(d):
            if s > t0:
                return d.isoformat(), float(s), min(float(s) + 3600.0, cal.session_close(d))
        d = cal.next_trading_day(d)
    return None


def window(row, tape, windows=None):
    """the entry window an intraday arm acts inside, for one long row: the intent's own (the tape's note: not_before,
    then not_after, else the decision + window_s, else + the desk's default), else the interval rule (a 1h row: its
    entry hour, as tensor_research's lots enter; any other: the session the decision acts on), never past that
    session's close; with low0, the session's running low through the decision (completed bars; None before the
    session) -> {"session", "start", "end", "low0", "src"}"""
    t0 = float(row["decided_at"])
    note = windows.get(t0, row["symbol"], row.get("key")) if windows is not None and row["arm"] == "signal" else None
    start = None
    if note is not None:
        d, src = session_for(t0), "intent"
        start = note.get("not_before")
        end = note.get("not_after") or (t0 + float(note["window_s"]) if note.get("window_s") else
                                        t0 + (windows.default_s if windows is not None else DEFAULT_WINDOW_S))
    elif row.get("own") == "1h" and _next_hour(t0):
        d, start, end = _next_hour(t0)
        src = "1h entry bar"
    else:
        d, src = session_for(t0), "session"
        end = cal.session_close(d)
    low = tape.day_low(t0) if in_session(t0) == d else None
    return {"session": d, "start": None if start is None else float(start), "end": min(float(end),
                                                                                       cal.session_close(d)),
            "low0": None if not low else round(low[0], 6), "src": src, "piv": tape.pivot_state(t0)}

ARMS = {
    "eq01_open_print": {
        "source": "AUDIT_EQ.md EQ-01 (EXPERIMENT, execution)",
        "changes": "an entry decided before the open, or inside the session's first pass (by 09:35 ET), fills at the "
                   "session's official opening print (its daily bar's open) and pays a %g bps auction cost, instead "
                   "of the fill the first pass routed" % AUCTION_BPS,
        "kept": "the signal, its side, size and exit; the desk's real fill is the incumbent, paired entry by entry",
        "expected": "a positive saving (the fill minus the official open, QQQ-adjusted, net of the auction cost): "
                    "the record showed +16.6 bps QQQ-adjusted over 1,083 opening entries",
        "rival": "the gap is the market's move in the first minutes (QQQ's move over the same minutes is "
                 "subtracted) or the sim's half-spread, part of which an auction order would also pay",
        "placebo": "none applies: the arm prices the desk's own fills; QQQ's move from its open to each fill is the "
                   "market control",
        "rejection": "rejected if, over at least 200 paired entries, the mean QQQ-adjusted saving net of the auction "
                     "cost is under 5 bps",
        "min_n": 200, "threshold_bps": 5.0,
        "audit_rule": "AUDIT_EQ.md's own bar, reported beside: at least 300 entries over at least 10 sessions, and "
                      "the 95% interval of the mean saving excludes 0",
    },
    "lod_gate": {
        "source": "CLX_REVIEW_2026-10-25.md item 1: ChartsLector's `LoD Intraday Entry` (tv-indicators c55ad51), "
                  "his BLUE state",
        "changes": "on each equity long entry signal the arm waits, inside the sleeve's own entry window, until the "
                   "price is at most the running day's low + 0.65 x ATR14 (daily) and the stop (the day's low - "
                   "0.1 x ATR14) is under 4% of the price; it fills at the first price that qualifies (a market fill, "
                   "5 bps), otherwise it skips (policy lod_u20)",
        "kept": "the signal, its side, its window and its capital (a skip is a zero outcome); the exit, the open of "
                "session 20 (the open family's common exit), so the comparison is the entry alone; the incumbent "
                "is the immediate entry on the same intraday path (now_u20)",
        "expected": "a better entry with most entries still taken: a higher 30-minute mark-out and a higher "
                    "20-session R than the immediate entry (the daily proxy of the stop distance is grade A in small "
                    "caps: holdout t -8.3 in small3)",
        "rival": "waiting for a dip buys the names that keep falling (adverse selection) and misses the runners that "
                 "never come back: a gain in R can be the skipped losers alone, and the missed-runner rate says "
                 "what it cost",
        "placebo": "the same gate on the seeded placebo's entries, reported beside and never judged: a gain the "
                   "placebo shows as well belongs to the period, not to the signals",
        "rejection": "it survives only if both the 20-session R and the 30-minute mark-out improve on the "
                     "immediate entry; it is rejected if either does not: over at least 100 paired entries, rejected "
                     "when the mean 20-session R difference or the mean 30-minute mark-out difference is at or below "
                     "0, or when the gate skips more than 50% of entries",
        "min_n": 100, "max_skip": 0.5, "runner_r": 1.0,
        "deviations": "his ATR is ta.atr (Wilder's average, today's developing bar included); the lab's is the mean "
                      "of the last 14 true ranges completed at the decision, the lab's R unit. His second rule "
                      "(entry to stop under one ATR) always holds inside the 0.65 ATR band (the distance is at most "
                      "0.75 ATR). The day's low is the market's, from bars: completed bars at the decision, then the "
                      "path's bars; a bar that reaches the ceiling fills at it. The window is the intent's own when "
                      "the decision tape noted it, else the 1h entry bar (1h rows) or the session",
    },
    "piv30": {
        "source": "CLX_REVIEW_2026-10-25.md: ChartsLector's `30 min Pivot` (tv-indicators c55ad51, credited to "
                  "@1ChartMaster); its daily-bar proxy did not confirm (ev_clxp_piv1/2): a low prior, built because "
                  "the lab now holds 30-minute bars",
        "changes": "on each equity long entry signal the arm waits, inside the sleeve's own entry window, for a "
                   "30-minute bar that completes either of his two 4-bar patterns, and enters at the next half "
                   "hour's open (the pattern is known at the bar's close), inside the window too; otherwise it skips "
                   "(policy piv30_u20)",
        "kept": "the signal, its side, its window and its capital (a skip is a zero outcome); the exit, the open of "
                "session 20; the incumbent is the immediate entry (now_u20), as for the LoD gate",
        "expected": "a better-timed entry: a higher 30-minute mark-out and a higher 20-session R than the immediate "
                    "entry",
        "rival": "a short reversal pattern on half hours is noise around the signal's own move; the daily proxy "
                 "found no effect, and a rare pattern skips most entries",
        "placebo": "the same arm on the seeded placebo's entries, beside and never judged",
        "rejection": "it survives only if both the 20-session R and the 30-minute mark-out improve on the immediate "
                     "entry; it is rejected if either does not: over at least 100 paired entries, rejected when the "
                     "mean 20-session R difference or the mean 30-minute mark-out difference is at or below 0, or "
                     "when it skips more than 50% of entries (the LoD gate's rule)",
        "min_n": 100, "max_skip": 0.5, "runner_r": 1.0,
        "deviations": "as coded: cond1 = within 5% of EMA20(30m), the bar opening under it and closing green above "
                      "the opens of bars 2 and 3 and the close of bar 1, after bars 3 and 2 red and bar 1 green; "
                      "cond2 = bars 3, 2 and 1 green, bars 2 and 1 inside bar 3, the bar closing above the three "
                      "closes with its high under bar 3's. His cond2 has no EMA condition, so only cond1 is 'near "
                      "EMA20'; both are kept exactly as coded. The EMA is seeded by the first close of the series "
                      "(Pine's ta.ema); the half hours are the regular session's SIP bars, continuous across "
                      "sessions as his chart is. A pattern needs 30-minute bars: the canonical store's half hours",
    },
}
# the sizing arms (item 3): the same entries as an equal-dollar book (the reference policy's 5-session positions,
# NOTIONAL each), re-weighted within each session's cohort to the same gross; each arm judged on the entries that carry
# its input, against equal-dollar on those same entries
_SIZE_KEPT = ("the entries (the lab's reference policy, nso_t5: the next session's open, out at session 5), their "
              "timing and exits, and each session's gross (the cohort's weights sum to its count: equal gross, "
              "the incumbent's); the incumbent is the equal-dollar book on the same entries")
_SIZE_RULE = ("rejected if, over at least 100 entries and 20 sessions, the paired mean daily P&L difference to "
              "equal-dollar is at or below 0, or the book's realized daily volatility is not at least 10% lower")
ARMS.update({
    "size_har": {
        "source": "Addendum 2-19 section 2 (the VOL forecaster's use) and AUDIT_EQ.md EQ-04",
        "changes": "each entry's dollars = clip(target sigma / forecast sigma, 0.25, 2) x equal-dollar, renormalized "
                   "to the cohort's gross; forecast sigma = the analysis engine's screen row's sigma_mean (the "
                   "per-day volatility forecast for the next 20 sessions); target sigma = the cohort's median "
                   "forecast (2-19 leaves the target unset: the median name keeps its size)",
        "kept": _SIZE_KEPT, "rejection": _SIZE_RULE,
        "expected": "a smoother book at equal gross: lower daily volatility and drawdown, no lower P&L (volatility "
                    "is predictable, grade A in liquid names: T05)",
        "rival": "a lower-volatility book can be a lower-beta book (lower P&L in a rising market): the paired daily "
                 "P&L difference says which",
        "placebo": "the same weights on the seeded placebo's entries, beside: a gain the placebo shows as well is the "
                   "forecast's generic effect, which is still the arm's point (sizing is not selection)",
        "min_n": 100, "min_sessions": 20, "vol_cut": 0.10, "input": "sigma",
    },
    "size_vantharp": {
        "source": "CLX_REVIEW_2026-10-25.md item 5: ChartsLector's VanTharp stop-risk cap (`LoD Intraday Entry`)",
        "changes": "each entry's shares = risk dollars / (price - stop), with his LoD stop (the day's low - 0.1 x "
                   "ATR14) at the decision's current price (the last completed bar's close): dollars proportional to "
                   "1 / the stop distance, renormalized to the cohort's gross",
        "kept": _SIZE_KEPT, "rejection": _SIZE_RULE,
        "expected": "equal dollar risk to the stop: a smoother book, no lower P&L",
        "rival": "a near stop is a quiet name or a name sitting on its low: the weight can load on one entry; the "
                 "report shows the largest weight",
        "placebo": "the same weights on the seeded placebo's entries, beside",
        "min_n": 100, "min_sessions": 20, "vol_cut": 0.10, "input": "stop_dist",
        "deviations": "his RPRP blend, ((0.35 x max + 0.65 x min) of the two caps) / 2, carries an extra / 2: the "
                      "weights already sum to 1 and his comment says 'Average min & max', so the / 2 halves the size. "
                      "It is not reproduced: the blend is no arm here (at equal gross a constant factor cancels in "
                      "any case), and each cap is tested on its own",
    },
    "size_beta_atr": {
        "source": "CLX_REVIEW_2026-10-25.md item 5: ChartsLector's Vandenbord risk factor (`LoD Intraday Entry`)",
        "changes": "each entry's position % = base / RVF, RVF = 0.5 x beta63 (daily returns against SPY, completed "
                   "sessions) + 0.5 x ATR14% (ATR in percent, as he codes it), renormalized to the cohort's gross",
        "kept": _SIZE_KEPT, "rejection": _SIZE_RULE,
        "expected": "a smoother book at equal gross",
        "rival": "RVF mixes a unitless beta with ATR in percent, so ATR% dominates for volatile names: it is close to "
                 "an inverse-ATR rule, and any gain may be the ATR's alone",
        "placebo": "the same weights on the seeded placebo's entries, beside",
        "min_n": 100, "min_sessions": 20, "vol_cut": 0.10, "input": "rvf",
        "deviations": "beta needs 20 aligned daily returns (his rprpN >= 20), up to 63",
    },
})
ARMS.update(avoid.CONTRACTS)   # the avoid-filter arms (desk/lab/avoid.py)
NOTIONAL = 10_000.0          # dollars per equal-dollar entry
BETA_N, BETA_MIN = 63, 20
AVOID_ON = True              # the avoid arms' facts (off only in the on/off identity test)
LOD_STOP_ATR = 0.10          # his stop buffer below the day's low


def eq01(tape, row, qqq=None):
    """the opening-print arm's facts for one signal row: eligible (decided by the end of its session's first pass and
    first filled within FILL_WITHIN_S of the open), the official open, the desk's fill, and the saving in bps
    (side-adjusted, positive = the open print would have paid less): raw, QQQ's move over the same minutes, and
    saving = raw - qqq - AUCTION_BPS"""
    t0, cap = row["decided_at"], row.get("capture") or {}
    d = session_for(t0)
    op = cal.session_open(d)
    if t0 >= op + FIRST_PASS_S:
        return {"eligible": False, "why": "decided after the opening pass"}
    out = {"eligible": False, "decided": "pre_open" if t0 < op else "first_pass", "session": d}
    k = tape.day_index(d)
    if k is None:
        return dict(out, why="no daily bar for the session")
    if not cap.get("filled"):
        return dict(out, why="not filled")
    delay = float(cap["fill_at"]) - op
    if delay < 0:
        return dict(out, why="filled before the open", delay_s=round(delay))
    if delay > FILL_WITHIN_S:
        return dict(out, why="first fill more than 20 minutes after the open", delay_s=round(delay))
    sgn = 1.0 if row["side"] == "long" else -1.0
    open_px, fill_px = tape.days[k][3], float(cap["fill_px"])
    raw = sgn * (fill_px / open_px - 1.0) * 1e4
    q, q_iv = None, None
    if qqq is not None and qqq.day_index(d) is not None:
        at_ = qqq.price_at(float(cap["fill_at"]), d)
        if at_:
            q, q_iv = sgn * (at_[0] / qqq.days[qqq.day_index(d)][3] - 1.0) * 1e4, at_[1]
    out.update(eligible=True, why=None, open_px=round(open_px, 6), fill_px=round(fill_px, 6), delay_s=round(delay),
               raw_bps=round(raw, 2), qqq_bps=None if q is None else round(q, 2), qqq_iv=q_iv,
               saving_bps=None if q is None else round(raw - q - AUCTION_BPS, 2),
               saving_raw_bps=round(raw - AUCTION_BPS, 2))
    return out


def closes(tape):
    """{session: close} of a tape's daily bars"""
    return {d[0]: d[6] for d in tape.days}


def size_facts(tape, row, ctx=None):
    """the sizing arms' inputs at the decision, from completed bars: beta63 against SPY and ATR14% (his RVF), the LoD
    stop's distance at the current price, and the reference policy's (nso_t5) position as daily P&L per $1, net of its
    costs: [[session, contribution]], entry at the next session's open, marked at each close, out at session 5's open"""
    t0, sgn = float(row["decided_at"]), 1.0 if row["side"] == "long" else -1.0
    atr = tape.atr(t0)
    k = tape.n_done(t0)
    out = {"beta63": None, "beta_n": 0, "atr_pct": None, "stop_dist": None, "marks": None}
    if atr and k:
        last = tape.days[k - 1][6]
        out["atr_pct"] = round(100.0 * atr / last, 4)
        spy = (ctx or {}).get("spy") or {}
        rets = [(b[0], b[6] / a[6] - 1.0) for a, b in zip(tape.days[max(0, k - BETA_N - 1):k - 1],
                                                          tape.days[max(1, k - BETA_N):k])]
        pairs = [(x, spy[d] / spy[p] - 1.0) for (d, x), p in zip(rets, [tape.days[i - 1][0] for i in
                                                                       range(max(1, k - BETA_N), k)])
                 if d in spy and p in spy]
        if len(pairs) >= BETA_MIN:
            ms, mb = sum(x for x, _ in pairs) / len(pairs), sum(y for _, y in pairs) / len(pairs)
            var = sum((y - mb) ** 2 for _, y in pairs)
            if var > 0:
                out["beta63"] = round(sum((x - ms) * (y - mb) for x, y in pairs) / var, 4)
            out["beta_n"] = len(pairs)
        px, low = tape.last_close(t0), tape.day_low(t0)
        if px and low:
            stop = low[0] - LOD_STOP_ATR * atr
            if px[0] > stop > 0:
                out["stop_dist"] = round(1.0 - stop / px[0], 6)
    j = tape.next_day(t0)
    if j is not None and len(tape.days) >= j + 6:
        d = tape.days[j:j + 6]
        e, c = d[0][3], 0.0005
        prev = e
        marks = []
        for i, b in enumerate(d):
            px = b[6] if i < 5 else b[3]                      # sessions 0-4 marked at their close; out at 5's open
            marks.append([b[0], round(sgn * (px - prev) / e - (c if i in (0, 5) else 0.0), 8)])
            prev = px
        out["marks"] = marks
    return out


def facts(tape, row, ctx=None):
    """the arms' facts for one row: EQ-01 for a signal (it carries its capture), the sizing inputs for every row"""
    out = {"size": size_facts(tape, row, ctx)}
    if row["arm"] == "signal":
        out["eq01"] = eq01(tape, row, (ctx or {}).get("qqq"))
    if row["arm"] in ("signal", "placebo") and AVOID_ON:
        out["avoid"] = avoid.facts(tape, row, ctx)
    return out


# -- the report (summary.json "arms") --------------------------------------------------------------------------------

def _ci95(st):
    """the 95% interval of a paired mean (sessions as clusters, t with sessions - 1 degrees of freedom), or None"""
    from .fidelity import _t975
    if st.get("se") is None:
        return None
    h = _t975(st["sessions"] - 1.0) * st["se"]
    return [round(st["mean"] - h, 4), round(st["mean"] + h, 4)]


def _count(xs):
    out = {}
    for x in xs:
        out[x] = out.get(x, 0) + 1
    return dict(sorted(out.items()))


def _contract(name):
    return {k: v for k, v in ARMS[name].items()}


def eq01_report(live):
    """EQ-01 over the live arm's eligible entries: the QQQ-adjusted saving (the rule's statistic), the raw saving, the
    split by when the entry was decided, and the rule applied once the minimum sample is reached"""
    c = ARMS["eq01_open_print"]
    facts_ = [(r, (r.get("arms") or {}).get("eq01") or {}) for r in live]
    el = [(r, f) for r, f in facts_ if f.get("eligible")]
    adj = [(r["session"], f["saving_bps"]) for r, f in el if f.get("saving_bps") is not None]
    st = S.paired(adj)
    st["ci95"] = _ci95(st)
    out = {"contract": _contract("eq01_open_print"), "saving_bps": st,
           "saving_raw_bps": S.paired([(r["session"], f["saving_raw_bps"]) for r, f in el]),
           "by_decided": {k: S.paired([(r["session"], f["saving_bps"]) for r, f in el
                                       if f.get("decided") == k and f.get("saving_bps") is not None])
                          for k in ("pre_open", "first_pass")},
           "eligible": len(el), "without_qqq": len(el) - len(adj),
           "not_eligible": _count(f.get("why") for _, f in facts_ if f and not f.get("eligible"))}
    if st["n"] < c["min_n"]:
        out["status"] = "descriptive"
        out["note"] = "descriptive until %d paired entries (%d so far); no rule is applied before" % (c["min_n"],
                                                                                                    st["n"])
    else:
        out["status"] = "rejected" if st["mean"] < c["threshold_bps"] else "not_rejected"
    ci = st["ci95"]
    out["audit_rule"] = "collecting" if st["n"] < 300 or st["sessions"] < 10 or ci is None else \
        ("met" if ci[0] > 0 else "not_met")
    return out


def _r(row, policy):
    """an outcome's R once final (a skip is 0), else None"""
    o = (row.get("outcomes") or {}).get(policy) or {}
    if o.get("state") != "done":
        return None
    return float(o["r"]) if o.get("filled") else 0.0


def _entry_stats(rows, arm, base, runner_r):
    """an intraday entry arm against its comparator on the same rows: the pairs (the comparator filled and final, the
    arm final), the fill rate, the paired R and 30-minute mark-out differences, each side's means, and the missed
    runners (skipped entries whose comparator made at least runner_r)"""
    pairs = []
    for r in rows:                                      # a row without the arm (frozen before it existed) is no pair
        a, b = _r(r, arm), _r(r, base)
        if a is None or b is None or not r["outcomes"][base].get("filled"):
            continue
        pairs.append((r, a, b, r["outcomes"][arm], r["outcomes"][base]))
    filled = [p for p in pairs if p[3].get("filled")]
    skipped = [p for p in pairs if not p[3].get("filled")]
    marks = [(r["session"], oa["mark30_bps"] - ob["mark30_bps"]) for r, _, _, oa, ob in filled
             if oa.get("mark30_bps") is not None and ob.get("mark30_bps") is not None]
    missed = sum(1 for _, _, b, _, _ in skipped if b >= runner_r)
    n = len(pairs)
    return {"n": n, "sessions": len({p[0]["session"] for p in pairs}), "filled": len(filled),
            "fill_rate": round(len(filled) / n, 4) if n else None,
            "r20_diff": S.paired([(r["session"], a - b) for r, a, b, _, _ in pairs]),
            "r20_arm": round(sum(a for _, a, _, _, _ in pairs) / n, 4) if n else None,
            "r20_incumbent": round(sum(b for _, _, b, _, _ in pairs) / n, 4) if n else None,
            "mark30_bps": S.paired(marks),
            "mark30_arm_bps": _mean(oa.get("mark30_bps") for _, _, _, oa, _ in filled),
            "mark30_incumbent_bps": _mean(ob.get("mark30_bps") for _, _, _, _, ob in filled),
            "missed_runners": missed, "missed_runner_rate": round(missed / n, 4) if n else None,
            "skips_that_were_runners": round(missed / len(skipped), 4) if skipped else None}


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return round(sum(xs) / len(xs), 2) if xs else None


def lod_report(live, plc, name="lod_gate", policy="lod_u20"):
    """an intraday entry arm (the LoD gate, lod_u20; the pivot, piv30_u20) against the immediate entry (now_u20) on
    the live arm's long entries, split by whether the decision came inside its session (before the open the day's low
    is the open, so the gate fills at once), the placebo beside; the rule applied once the minimum sample is
    reached"""
    c = ARMS[name]
    st = _entry_stats(live, policy, "now_u20", c["runner_r"])
    out = dict(st, contract=_contract(name),
               by_decided={"in_session": _entry_stats([r for r in live if in_session(r["decided_at"])], policy,
                                                      "now_u20", c["runner_r"])["r20_diff"],
                           "before": _entry_stats([r for r in live if not in_session(r["decided_at"])], policy,
                                                  "now_u20", c["runner_r"])["r20_diff"]},
               placebo=_entry_stats(plc, policy, "now_u20", c["runner_r"]))
    if st["n"] < c["min_n"]:
        out["status"] = "descriptive"
        out["note"] = "descriptive until %d paired entries (%d so far); no rule is applied before" % (c["min_n"],
                                                                                                    st["n"])
    else:
        worse = (st["r20_diff"]["mean"] or 0) <= 0 or (st["mark30_bps"]["mean"] or 0) <= 0
        out["status"] = "rejected" if worse or 1 - st["fill_rate"] > c["max_skip"] else "not_rejected"
    return out


def _size_item(r):
    """a row's sizing inputs once its reference position is final, or None"""
    f = ((r.get("arms") or {}).get("size")) or {}
    o = (r.get("outcomes") or {}).get("nso_t5") or {}
    if not f.get("marks") or o.get("state") != "done" or not o.get("filled"):
        return None
    rvf = None
    if f.get("beta63") is not None and f.get("atr_pct") is not None:
        rvf = 0.5 * f["beta63"] + 0.5 * f["atr_pct"]
    return {"session": r["session"], "marks": f["marks"], "sigma": f.get("sigma"),
            "stop_dist": f.get("stop_dist"), "rvf": rvf if rvf is not None and rvf > 0 else None}


def weights(arm, items):
    """one cohort's weights under an arm, summing to its count (equal gross)"""
    if arm == "size_har":
        sig = sorted(x["sigma"] for x in items)
        target = S.median(sig)
        raw = [min(2.0, max(0.25, target / x["sigma"])) for x in items]
    elif arm == "size_vantharp":
        raw = [1.0 / x["stop_dist"] for x in items]
    elif arm == "size_beta_atr":
        raw = [1.0 / x["rvf"] for x in items]
    else:
        raw = [1.0] * len(items)
    tot = sum(raw)
    return [w * len(items) / tot for w in raw]


def _book(items, ws):
    """{date: dollar P&L} of a book holding NOTIONAL x weight in each item's position"""
    pnl = {}
    for x, w in zip(items, ws):
        for d, c in x["marks"]:
            pnl[d] = pnl.get(d, 0.0) + NOTIONAL * w * c
    return pnl


def _stats(pnl, dates):
    xs = [pnl.get(d, 0.0) for d in dates]
    n = len(xs)
    if not n:
        return {"pnl": None, "vol": None, "max_drawdown": None}
    m = sum(xs) / n
    vol = (sum((x - m) ** 2 for x in xs) / (n - 1)) ** 0.5 if n > 1 else None
    peak, cum, dd = 0.0, 0.0, 0.0
    for x in xs:
        cum += x
        peak = max(peak, cum)
        dd = max(dd, peak - cum)
    return {"pnl": round(sum(xs), 2), "vol": None if vol is None else round(vol, 2), "max_drawdown": round(dd, 2)}


def _sizing(rows, arm):
    """one sizing arm against equal-dollar on the rows that carry its input"""
    key = ARMS[arm]["input"]
    items = [x for x in (_size_item(r) for r in rows) if x is not None and x.get(key)]
    cohorts = {}
    for x in items:
        cohorts.setdefault(x["session"], []).append(x)
    arm_w, eq_w, flat_items, top = [], [], [], 0.0
    for d in sorted(cohorts):
        c = cohorts[d]
        w = weights(arm, c)
        arm_w += w
        eq_w += [1.0] * len(c)
        flat_items += c
        top = max([top] + [wi / len(c) for wi in w])
    a, b = _book(flat_items, arm_w), _book(flat_items, eq_w)
    dates = sorted(set(a) | set(b))
    sa, sb = _stats(a, dates), _stats(b, dates)
    diff = S.paired([(d, a.get(d, 0.0) - b.get(d, 0.0)) for d in dates])
    gross_ok = all(abs(sum(weights(arm, c)) - len(c)) < 1e-9 for c in cohorts.values())
    return {"n": len(items), "sessions": len(cohorts), "days": len(dates), "arm": sa, "equal": sb,
            "daily_pnl_diff": diff, "vol_ratio": round(sa["vol"] / sb["vol"], 4) if sa["vol"] and sb["vol"] else None,
            "drawdown_ratio": round(sa["max_drawdown"] / sb["max_drawdown"], 4) if sb["max_drawdown"] else None,
            "largest_weight_share": round(top, 4), "gross_equal": gross_ok, "notional": NOTIONAL}


def sizing_report(live, plc):
    """the three sizing arms on the live arm's entries, the placebo beside; each arm's rule once its minimum sample
    is reached"""
    out = {}
    for arm in ("size_har", "size_vantharp", "size_beta_atr"):
        c = ARMS[arm]
        st = _sizing(live, arm)
        st.update(contract=_contract(arm), placebo=_sizing(plc, arm))
        if st["n"] < c["min_n"] or st["sessions"] < c["min_sessions"]:
            st["status"] = "descriptive"
            st["note"] = "descriptive until %d entries and %d sessions (%d and %d so far); no rule is applied " \
                         "before" % (c["min_n"], c["min_sessions"], st["n"], st["sessions"])
        else:
            worse = (st["daily_pnl_diff"]["mean"] or 0) <= 0
            calm = st["vol_ratio"] is not None and st["vol_ratio"] <= 1.0 - c["vol_cut"]
            st["status"] = "rejected" if worse or not calm else "not_rejected"
        out[arm] = st
    return out


def report(live, ctrl, plc):
    """summary.json "arms": every arm's contract, its statistics and its state"""
    return dict({"eq01_open_print": eq01_report(live), "lod_gate": lod_report(live, plc),
                 "piv30": lod_report(live, plc, "piv30", "piv30_u20")}, **sizing_report(live, plc), **avoid.report(live, plc))
