"""The Execution Lab's avoid-filter arms (engine/EVIDENCE.md, the AVOID layer: vetoes, the most robust layer). Each
equity long entry signal (and each placebo draw, beside) carries the avoid flags the desk could compute at its
decision from the daily bars it already holds, point in time (only bars whose session closed by then); two paired
shadow variants then ask whether the flags would have helped. Nothing here trades, routes, sizes or changes a sleeve:
the flags are facts on the lab's rows (arms.avoid), scored in summary.json "arms".

  flags   pump25       A2: a +25% close-to-close day in the last 20 completed sessions
          stretched    A3: the last close more than 2.5 ATR14 above its 50-session average, or at least 1.6x it
          dead_cat     A7: a dead-cat bounce (constants below: a >= 30% fall from the 60-session high close to a low
                       inside the last 15 sessions, a >= 15% bounce off that low, still >= 15% under the high)
          idio_decline A15: a 20-session fall of at least 10% of which at least 75% is company-specific (the fall
                       minus beta63 x SPY's fall over the same sessions)
          new_listing  fewer than 252 completed daily bars cached (the tape reads LISTING_DAYS of them)
          small_loser  A1's small-cap 20-day-loser bottom decile: the desk holds no market-cap cross-section, so it is
                       always None, reason no_data
  A flag is True / False, or None when its bars are too few (its reason in `missing`); `warnings` counts the True ones.

  avoid_skip  a flagged entry is not taken: the pair is the entry (the lab's reference policy, nso_t5, and the 20-session
              hold, nso_t20, beside) against flat (0 R); a positive difference is a loss avoided, a negative one a gain
              missed
  avoid_exit  a held entry (nso_t20's position) that becomes flagged after a session's close (a flag True that was not
              True at the decision) exits at the next session's open (COST_BPS, as the hold's own exit); the pair is
              that exit against the hold, in R (the decision's ATR)"""
from . import stats as S
from .policies import COST_BPS

LISTING_DAYS = 253                    # daily bars the tape reads (252 completed + the decision's own session)
PUMP_PCT, PUMP_N = 0.25, 20
SMA_N, STRETCH_ATR, STRETCH_X = 50, 2.5, 1.6
DC_N, DC_LOW_N, DC_FALL, DC_BOUNCE, DC_BELOW = 60, 15, 0.30, 0.15, 0.85
IDIO_N, IDIO_FALL, IDIO_SHARE, BETA_N, BETA_MIN = 20, 0.10, 0.75, 63, 20
FLAGS = ("pump25", "stretched", "dead_cat", "idio_decline", "new_listing", "small_loser")
SKIP_POLICY, HOLD_POLICY = "nso_t5", "nso_t20"

CONTRACTS = {
    "avoid_skip": {
        "source": "engine/EVIDENCE.md AVOID layer (A2, A3, A7, A15, A1; new listings), as a veto, never a short book "
                  "(A16)",
        "changes": "a long entry carrying any avoid flag at its decision is not taken (flat, 0 R)",
        "kept": "every signal, its side, timing and exit; the incumbent is the entry as the lab scores it (the "
                "reference policy, nso_t5; the 20-session hold, nso_t20, beside); unflagged entries are the same in "
                "both and are reported beside as the control",
        "expected": "flagged entries lose on average: flat beats taking them (a positive mean of flat minus taken)",
        "rival": "flagged names are volatile names; a negative mean R there can be the period's selloff of volatile "
                 "names (the placebo's flagged draws, beside, say which)",
        "placebo": "the same flags on the seeded placebo's draws, beside and never judged",
        "rejection": "rejected if, over at least 100 flagged paired entries and 20 sessions, the mean of flat minus "
                     "taken (nso_t5 R) is at or below 0",
        "min_n": 100, "min_sessions": 20,
        "deviations": "the small-cap loser decile needs a market-cap cross-section the desk does not hold: no_data. "
                      "Earnings are not excluded from the +25% day (the desk holds no point-in-time earnings dates "
                      "here). The dead-cat and idiosyncratic thresholds are fixed in advance here (EVIDENCE.md names "
                      "the patterns, not the cut-offs)",
    },
    "avoid_exit": {
        "source": "engine/EVIDENCE.md AVOID layer, applied to positions already held",
        "changes": "a held long position (nso_t20) that becomes flagged after a session's close exits at the next "
                   "session's open",
        "kept": "the entry, its capital and the hold's exit when no new flag appears; the incumbent is the hold",
        "expected": "a position that turns flagged then loses: the exit beats the hold (a positive mean R difference)",
        "rival": "a new flag on a held winner is often A3 stretch: the exit then cuts the right tail (E1); the "
                 "by-flag split says which",
        "placebo": "the same exit on the seeded placebo's draws, beside and never judged",
        "rejection": "rejected if, over at least 100 paired exits and 20 sessions, the mean R difference (exit minus "
                     "hold) is at or below 0",
        "min_n": 100, "min_sessions": 20,
    },
}


def flags(tape, t, spy=None, at_k=None):
    """the avoid flags from the daily bars completed at t (or the first at_k bars) -> {"flags", "missing",
    "warnings", "flagged", "values", "n_days"}; spy: {session: close}"""
    k = tape.n_done(t) if at_k is None else at_k
    days = tape.days[:k]
    c = [d[6] for d in days]
    f, why, val = {}, {}, {}
    if len(c) >= PUMP_N + 1:
        best = max(b / a - 1.0 for a, b in zip(c[-PUMP_N - 1:-1], c[-PUMP_N:]) if a > 0)
        val["max_day_pct"] = round(100 * best, 3)
        f["pump25"] = best >= PUMP_PCT
    else:
        f["pump25"], why["pump25"] = None, "fewer than %d closes" % (PUMP_N + 1)
    atr = _atr(days)
    if len(c) >= SMA_N and atr:
        sma = sum(c[-SMA_N:]) / SMA_N
        val.update(sma50=round(sma, 6), ext_atr=round((c[-1] - sma) / atr, 4), ext_x=round(c[-1] / sma, 4))
        f["stretched"] = c[-1] - sma > STRETCH_ATR * atr or c[-1] >= STRETCH_X * sma
    else:
        f["stretched"], why["stretched"] = None, "fewer than %d closes or no ATR" % SMA_N
    if len(c) >= DC_N:
        w = c[-DC_N:]
        hi_i = max(range(len(w)), key=lambda i: w[i])
        lo_i = min(range(len(w) - DC_LOW_N, len(w)), key=lambda i: w[i])
        hi, lo = w[hi_i], w[lo_i]
        val.update(dc_fall=round(lo / hi - 1.0, 4), dc_bounce=round(c[-1] / lo - 1.0, 4))
        f["dead_cat"] = hi_i < lo_i and lo / hi - 1.0 <= -DC_FALL and c[-1] / lo - 1.0 >= DC_BOUNCE and \
            c[-1] <= DC_BELOW * hi
    else:
        f["dead_cat"], why["dead_cat"] = None, "fewer than %d closes" % DC_N
    f["idio_decline"], why_i = _idio(days, spy, val)
    if why_i:
        why["idio_decline"] = why_i
    f["new_listing"] = k < LISTING_DAYS - 1
    f["small_loser"], why["small_loser"] = None, "no_data: the desk holds no market-cap cross-section"
    n = sum(1 for x in f.values() if x)
    return {"flags": f, "missing": why, "warnings": n, "flagged": n > 0, "values": val, "n_days": k}


def _atr(days, n=14):
    if len(days) < n + 1:
        return None
    b = days[-n - 1:]
    trs = [max(y[4] - y[5], abs(y[4] - x[6]), abs(y[5] - x[6])) for x, y in zip(b, b[1:])]
    v = sum(trs) / len(trs)
    return v if v > 0 else None


def _idio(days, spy, val):
    if len(days) < IDIO_N + 1:
        return None, "fewer than %d closes" % (IDIO_N + 1)
    a, b = days[-IDIO_N - 1], days[-1]
    r = b[6] / a[6] - 1.0
    val["r20"] = round(r, 4)
    if r > -IDIO_FALL:
        return False, None
    if not spy or a[0] not in spy or b[0] not in spy:
        return None, "no SPY closes for the sessions"
    pairs = [(y[6] / x[6] - 1.0, spy[y[0]] / spy[x[0]] - 1.0)
             for x, y in zip(days[-BETA_N - 1:-1], days[-BETA_N:]) if x[0] in spy and y[0] in spy]
    if len(pairs) < BETA_MIN:
        return None, "fewer than %d aligned returns for beta" % BETA_MIN
    mx, my = sum(p[0] for p in pairs) / len(pairs), sum(p[1] for p in pairs) / len(pairs)
    var = sum((p[1] - my) ** 2 for p in pairs)
    beta = sum((p[0] - mx) * (p[1] - my) for p in pairs) / var if var > 0 else 0.0
    share = (r - beta * (spy[b[0]] / spy[a[0]] - 1.0)) / r
    val.update(beta63=round(beta, 4), idio_share=round(share, 4))
    return share >= IDIO_SHARE, None


def exit_facts(tape, row, at0, spy=None):
    """avoid_exit for one long row: the hold (nso_t20) once final, the first session after the entry whose close
    raises a flag not raised at the decision, and the exit at the next session's open against the hold's exit"""
    o = (row.get("outcomes") or {}).get(HOLD_POLICY) or {}
    if row.get("side") != "long" or not row.get("atr"):
        return {"eligible": False, "why": "short or no ATR"}
    if o.get("state") != "done" or not o.get("filled"):
        return {"eligible": False, "why": "hold not final" if o.get("state") == "open" else "hold not filled"}
    e = tape.next_day(float(o["entry_at"]) - 1.0)
    x = tape.next_day(float(o["exit_at"]) - 1.0)
    if e is None:
        return {"eligible": False, "why": "no entry bar"}
    x = len(tape.days) - 1 if x is None else x
    base = {n for n, v in at0["flags"].items() if v}
    for j in range(e, x):
        if j + 1 >= x:                           # the hold's own exit comes first
            break
        got = flags(tape, None, spy, at_k=j + 1)
        new = sorted(n for n, v in got["flags"].items() if v and n not in base)
        if new:
            px = tape.days[j + 1][3]
            entry, atr = float(o["entry_px"]), float(row["atr"])
            ret = (px - entry) / entry - (COST_BPS / 1e4)
            r = ret * entry / atr
            return {"eligible": True, "triggered": True, "flag_session": tape.days[j][0], "new_flags": new,
                    "exit_session": tape.days[j + 1][0], "exit_px": round(px, 6), "exit_r": round(r, 4),
                    "hold_r": o["r"], "diff_r": round(r - float(o["r"]), 4)}
    return {"eligible": True, "triggered": False, "hold_r": o["r"], "diff_r": 0.0}


def facts(tape, row, ctx=None):
    """the avoid facts of one row: the flags at the decision and, for a long row, the exit arm's pair"""
    spy = (ctx or {}).get("spy")
    at0 = flags(tape, float(row["decided_at"]), spy)
    out = dict(at0, exit=exit_facts(tape, row, at0, spy))
    return out


# -- the report -------------------------------------------------------------------------------------------------------

def _r(row, policy):
    o = (row.get("outcomes") or {}).get(policy) or {}
    if o.get("state") != "done":
        return None
    return float(o["r"]) if o.get("filled") else 0.0


def _skip(rows):
    """flat minus taken on the flagged long rows (positive: a loss avoided), the unflagged beside, the avoided losses
    and missed gains in R, and the split by flag and by warning count"""
    long_ = [r for r in rows if r.get("side") == "long" and ((r.get("arms") or {}).get("avoid") or {}).get("flags")]
    out = {}
    for pol in (SKIP_POLICY, HOLD_POLICY):
        fl = [(r, _r(r, pol)) for r in long_ if r["arms"]["avoid"]["flagged"]]
        fl = [(r, x) for r, x in fl if x is not None]
        un = [(r["session"], x) for r, x in ((r, _r(r, pol)) for r in long_ if not r["arms"]["avoid"]["flagged"])
              if x is not None]
        out[pol] = {"flat_minus_taken": S.paired([(r["session"], -x) for r, x in fl]),
                    "loss_avoided_r": round(sum(-x for _, x in fl if x < 0), 4),
                    "gain_missed_r": round(sum(x for _, x in fl if x > 0), 4),
                    "unflagged_r": S.paired(un),
                    "by_flag": {n: S.paired([(r["session"], -x) for r, x in fl if r["arms"]["avoid"]["flags"].get(n)])
                                for n in FLAGS},
                    "by_warnings": {str(w): S.paired([(r["session"], -x) for r, x in fl
                                                      if min(r["arms"]["avoid"]["warnings"], 3) == w])
                                    for w in (1, 2, 3)}}
    out["flagged"] = sum(1 for r in long_ if r["arms"]["avoid"]["flagged"])
    out["long_rows"] = len(long_)
    out["no_data"] = {n: sum(1 for r in long_ if r["arms"]["avoid"]["flags"].get(n) is None) for n in FLAGS}
    return out


def _exit(rows):
    ex = [(r, ((r.get("arms") or {}).get("avoid") or {}).get("exit") or {}) for r in rows if r.get("side") == "long"]
    trig = [(r, f) for r, f in ex if f.get("triggered")]
    by = {}
    for r, f in trig:
        for n in f["new_flags"]:
            by.setdefault(n, []).append((r["session"], f["diff_r"]))
    return {"eligible": sum(1 for _, f in ex if f.get("eligible")), "triggered": len(trig),
            "exit_minus_hold_r": S.paired([(r["session"], f["diff_r"]) for r, f in trig]),
            "by_new_flag": {n: S.paired(v) for n, v in sorted(by.items())}}


def _status(st, c):
    if st["n"] < c["min_n"] or st["sessions"] < c["min_sessions"]:
        return "descriptive", "descriptive until %d paired entries and %d sessions (%d and %d so far); no rule is " \
                              "applied before" % (c["min_n"], c["min_sessions"], st["n"], st["sessions"])
    return ("rejected" if (st["mean"] or 0) <= 0 else "not_rejected"), None


def report(live, plc):
    """summary.json "arms": avoid_skip and avoid_exit with their contracts, the placebo beside"""
    sk, ex = _skip(live), _exit(live)
    sk.update(contract=dict(CONTRACTS["avoid_skip"]), placebo=_skip(plc))
    ex.update(contract=dict(CONTRACTS["avoid_exit"]), placebo=_exit(plc))
    for d, st, name in ((sk, sk[SKIP_POLICY]["flat_minus_taken"], "avoid_skip"),
                        (ex, ex["exit_minus_hold_r"], "avoid_exit")):
        d["status"], note = _status(st, CONTRACTS[name])
        if note:
            d["note"] = note
    return {"avoid_skip": sk, "avoid_exit": ex}
