"""Gate G1, replay fidelity (docs/research/2026-10-18-lab/METHODS.md M6; PROPOSALS.md section 2).

Before any timing or order type is replayed on the decision tape (desk/lab/quotes.py), replaying what the desk did
must reproduce what the sim filled. A US-equity fill the sim made at submission (in the pass that sent it, as a
marketable order fills) priced on the hub's quote of that pass, and the tape kept that quote: the name's row read in
the pass, at or before the submission. The fill's own order (side, quantity, limit) goes back through
quotes.replay_order on that row: the same equity_touch, the same SimVenue fill rule.

- replay_fills(root, rec, sessions) -> {fill seq: replay}. Each session's tape is streamed once; only rows that can be
  a candidate fill's quote are parsed and kept, so memory follows the fills, not the tape.
- for_signal(seqs, replays, atr) -> a signal row's "replay": its candidate fills, those on the tape, those the replay
  refused, and the error (replay - fill, signed so that + is the replay paying more or receiving less), in bps and in
  R (the signal's daily ATR, the lab's R).
- gate(rows) -> G1 over the signal rows (summary.json "fidelity"):
    pass        median |error| <= 0.01 R, the 95% CI of the mean error within +-0.02 R (sessions as clusters, t with
                sessions - 1 degrees of freedom), and at most 1% of the replayed fills refused
    fail        any of the three, with the worst cases
    collecting  under MIN_N replayed signals, or a single session
  It gates nothing yet: every lab policy so far replays bars. A policy replayed on the tape is promoted only while G1
  passes."""
import re

from . import quotes
from . import stats as S
from .tape import session_for

PASS_S = 300.0          # a fill submitted up to this long after its pass's start is that pass's (passes take seconds)
AFTER_S = 0.5           # a quote the fill itself read is stamped as the read starts, microseconds after the submission
MIN_N = 30
MAX_MEDIAN_R, MAX_BIAS_R, MAX_REFUSED = 0.01, 0.02, 0.01
_SYM = re.compile(r'"sym":\s*"([^"]+)"')


def _candidates(rec, sessions):
    """{session: {symbol: [fill]}}: the US-equity fills made in the pass that sent them"""
    want, out = set(sessions), {}
    for f in rec.fills:
        sub, at = f.get("submitted_at"), f.get("at")
        if sub is None or at is None or not (0.0 <= float(sub) - float(at) <= PASS_S):
            continue
        d = session_for(at)
        if d in want:
            out.setdefault(d, {}).setdefault(str(f["inst"])[3:], []).append(f)
    return out


def _sent(f):
    """when the fill's order went out: sent_at, the clock as the OMS sent it; a fill recorded before sent_at existed has
    only submitted_at, the pass's clock, which the order's own quote read can follow by the whole pass (2026-10-19:
    SOXX submitted_at 09:30:15, priced on the quote read at 09:34:48, so no fill of the day was found on the tape)"""
    return float(f["sent_at"] if f.get("sent_at") is not None else f["submitted_at"])


def _quotes_of(root, session, by_sym):
    """{fill seq: the tape row the fill priced on}: the latest row of its name read in its pass, at or before its
    submission (AFTER_S allows the read the fill itself made; the tape rounds to milliseconds)"""
    best = {}
    for line in quotes.lines(root, session):
        m = _SYM.search(line)
        if not m or m.group(1) not in by_sym:
            continue
        row = quotes.parse(line)
        try:
            t = float(row["t"])
        except (TypeError, KeyError, ValueError):            # a torn or foreign line: not a quote
            continue
        for f in by_sym[m.group(1)]:
            if float(f["at"]) - 1e-3 <= t <= _sent(f) + AFTER_S:
                k = f.get("seq")
                if k not in best or t > float(best[k]["t"]):
                    best[k] = row
    return best


def replay_fills(root, rec, sessions):
    out = {}
    for d, by_sym in _candidates(rec, sessions).items():
        if not quotes.has_tape(root, d):
            continue
        rows = _quotes_of(root, d, by_sym)
        for sym, fills in by_sym.items():
            for f in fills:
                base = {"fill_px": f["price"], "side": f["side"], "qty": f.get("qty"), "session": d}
                row = rows.get(f.get("seq"))
                if row is None:
                    out[f.get("seq")] = dict(base, on_tape=False)
                    continue
                px, why = quotes.replay_order(row, {"symbol": sym, "side": f["side"], "qty": f.get("qty"),
                                                    "limit_price": f.get("limit")}, _sent(f))
                out[f.get("seq")] = dict(base, on_tape=True, px=px, why=why, row_t=row["t"])
    return out


def for_signal(seqs, replays, atr):
    got = [replays[s] for s in seqs or () if s in replays]
    if not got:
        return None
    on = [g for g in got if g["on_tape"]]
    done = [g for g in on if g.get("px") is not None]
    out = {"fills": len(got), "on_tape": len(on), "refused": len(on) - len(done)}
    if out["refused"]:
        out["why"] = "; ".join(sorted({g.get("why") or "" for g in on if g.get("px") is None}))[:200]
    if done:
        w = [float(g.get("qty") or 0) or 1.0 for g in done]
        err = sum(wi * (1.0 if g["side"] == "buy" else -1.0) * (float(g["px"]) - float(g["fill_px"]))
                  for wi, g in zip(w, done)) / sum(w)
        ref = sum(wi * float(g["fill_px"]) for wi, g in zip(w, done)) / sum(w)
        out["err_bps"] = round(err / ref * 1e4, 4)
        out["err_r"] = round(err / atr, 6) if atr else None
    return out


def _t975(df):
    """the two-sided 95% critical value of Student's t (stats.t_sf inverted by bisection)"""
    lo, hi = 0.0, 1000.0
    for _ in range(80):
        mid = (lo + hi) / 2.0
        lo, hi = (mid, hi) if S.t_sf(mid, df) > 0.025 else (lo, mid)
    return hi


def gate(rows):
    sig = [r for r in rows if r.get("arm") == "signal" and r.get("replay")]
    obs = [(r["session"], r["replay"]["err_r"]) for r in sig if r["replay"].get("err_r") is not None]
    on = sum(r["replay"]["on_tape"] for r in sig)
    refused = sum(r["replay"]["refused"] for r in sig)
    st = S.paired(obs)
    med = S.median([abs(x) for _, x in obs])
    ci = None
    if st["se"] is not None:
        h = _t975(st["sessions"] - 1.0) * st["se"]
        ci = [round(st["mean"] - h, 4), round(st["mean"] + h, 4)]
    out = {"signals": len(obs), "sessions": st["sessions"], "with_fills": len(sig),
           "coverage": round(sum(1 for r in sig if r["replay"]["on_tape"]) / len(sig), 3) if sig else None,
           "fills_on_tape": on, "refused": refused, "refused_share": round(refused / on, 4) if on else None,
           "median_abs_r": None if med is None else round(med, 6), "mean_r": st["mean"], "ci95_r": ci,
           "thresholds": {"median_abs_r": MAX_MEDIAN_R, "ci95_r": MAX_BIAS_R, "refused_share": MAX_REFUSED,
                          "signals": MIN_N, "sessions": 2}}
    if len(obs) < MIN_N or ci is None:
        out["verdict"] = "collecting"
    elif med > MAX_MEDIAN_R or ci[0] < -MAX_BIAS_R or ci[1] > MAX_BIAS_R or (out["refused_share"] or 0) > MAX_REFUSED:
        out["verdict"] = "fail"
    else:
        out["verdict"] = "pass"
    bad = sorted((r for r in sig if r["replay"].get("refused") or r["replay"].get("err_r")),
                 key=lambda r: (-(r["replay"].get("refused") or 0), -abs(r["replay"].get("err_r") or 0)))
    out["worst"] = [dict({"id": r.get("id")}, **{k: r["replay"].get(k) for k in ("err_r", "err_bps", "refused", "why")
                                                if k in r["replay"]}) for r in bad[:5]]
    return out
