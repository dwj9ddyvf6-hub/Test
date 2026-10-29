"""The lab's option arms (exp1 item 5; AUDIT_OPT.md OPT-08 and OPT-09, AUDIT_MAC.md MAC-15). Paired shadow variants on
the desk's own option orders. Nothing here trades, routes, sizes or changes a sleeve.

  OPT-08   the option quote tape (desk/lab/quotes.py: watch / record / option_rows): each decided contract's quote as
           the pass read it, at every pass of its window. Its own rule: abandon the tape if quotes are unavailable at
           pass cadence for more than half of the decided contracts.
  OPT-09   patient pricing: rest a limit at the mid at the sleeve's first pass of its window, re-price it to the mid +
           half the half-spread at the second, cross at the third (no later than close - 15), against the incumbent,
           which crossed at the first. opt09() prices one order on the tape.
  MAC-15   a 10% spread cap on midna's three option books: a package with any leg wider than 10% of its mid is
           skipped (their rule today is 50%). mac15_report() judges the skipped packages.

Each option fill of a session is a row of its outcome file (arm "option": the fill, its quote at submit and the
OPT-09 counterfactual), built by option_rows() from the ledger and the tape."""
import math

from .. import calendar as cal
from ..util import et_date
from . import stats as S

CLOSE_GUARD_S = 900          # OPT-09 crosses no later than close - 15 minutes
READ_WITHIN_S = 300          # a pass's read: the first tape row within 5 minutes of the step's time
DEFAULT_CADENCE_S = 600      # apex's option sleeves (desk/sleeves/families/apex.py OPTION_CADENCE)
CAP = 0.10                   # MAC-15's relative spread cap per leg
MIDNA_BOOKS = ("midna_opt_turtle_atm_call", "midna_opt_reversal_call_spread", "midna_opt_distance_pair")

ARMS = {
    "opt09_patient": {
        "source": "AUDIT_OPT.md OPT-09 (EXPERIMENT, execution); prerequisite OPT-08, the option quote tape",
        "changes": "on the same once-a-session decision, a limit rests at the mid at the sleeve's first pass of its "
                   "window, moves to the mid + half the half-spread at its second pass, and crosses at its third "
                   "(no later than close - 15); a resting limit fills when a later read's ask (a sale: bid) reaches "
                   "it, at the limit",
        "kept": "the decision, the contracts, quantities, window and capital; the incumbent is the desk's own fill, "
                "which crossed at the first pass",
        "expected": "at least 25% of the half-spread saved (traders who time their trades pay under 40% of the "
                    "conventional effective spread: Muravyev et al.); the sim fills only at the touch, so a sim "
                    "saving comes from quote changes alone and is a lower bound",
        "rival": "indicative-quote noise (a contract read 0.01% wide on 10-22 and 5.0% wide on 10-23), and the "
                 "underlying's move during the wait (drift)",
        "placebo": "none applies: the arm prices the desk's own orders; the drift during the wait is the market "
                   "control",
        "rejection": "rejected if, over at least 40 paired option orders, the mean saving is under 10% of the "
                     "incumbent's half-spread, or a one-sided sign test gives p > 0.10, or the mean drift during the "
                     "wait exceeds the mean saving",
        "min_n": 40, "min_saving_half": 0.10, "sign_p": 0.10,
        "tape_rule": "OPT-08: abandon the tape if quotes are unavailable at pass cadence for more than 50% of the "
                     "decided contracts (judged from 40 decided)",
        "deviations": "single-contract orders in v1: a package's net quote needs its legs' fills, which the ledger "
                      "books per leg without a quote at submit; its legs are on the tape from 2026-10-26. The "
                      "steps are the sleeve's own cadence after the decision (apex: 600 s), each read the first tape "
                      "row within 5 minutes",
    },
    "mac15_spread_cap": {
        "source": "AUDIT_MAC.md MAC-15 (EXPERIMENT, execution / selection)",
        "changes": "midna's three option books (turtle, reversal, distance pair) skip a package with any leg whose "
                   "relative spread (ask - bid) / mid exceeds 10% at the decision; their rule today admits 50%",
        "kept": "the signals, the books, the other packages, their sizes and exits; the incumbent is the desk's own "
                "record of every package",
        "expected": "the skipped packages' P&L before spread is below the spread they paid: opt_distance_pair paid "
                    "660 bps of half-spread ($5,083 on 9 fills), more than its pre-cost loss",
        "rival": "wide markets are where the edge is (thin names, short-dated contracts): skipped packages may have "
                 "made more than their spread",
        "placebo": "none applies: the arm removes the desk's own packages",
        "rejection": "after at least 30 proposed packages, rejected if the skipped packages' P&L before spread "
                     "exceeds the spread they would have paid",
        "min_n": 30, "cap": CAP,
        "deviations": "single-contract legs in v1 (turtle calls and the pairs' two orders), from the fills' quotes at "
                      "submit; the reversal book's spreads go as one package order, whose legs the tape records "
                      "from 2026-10-26. P&L before spread: each leg's mid at its close minus its mid at its open, x "
                      "100 x contracts; the spread paid: each fill's distance from its mid, both ways",
    },
}


def _ok(b, a):
    try:
        return float(b) > 0 and float(a) >= float(b)
    except (TypeError, ValueError):
        return False


def opt09(order, rows, cadence=DEFAULT_CADENCE_S):
    """one single-contract order on the tape. order: {"side": buy | sell, "px": the incumbent's fill, "bid", "ask": its
    quote at submit, "t": when it was sent, "decided_at": the pass's clock}; rows: the contract's tape rows -> the
    arm's fill (step 1 / 2 / 3), the saving (positive: the arm paid less or received more) in price, in bps of the
    incumbent's price and as a share of its half-spread, and the drift (the mid's move against the order from the
    decision to the arm's fill, the same units); or {"state": "unavailable", "why"}"""
    if not _ok(order.get("bid"), order.get("ask")):
        return {"state": "unavailable", "why": "no two-sided quote at submit"}
    buy = order["side"] == "buy"
    sgn = 1.0 if buy else -1.0
    bid1, ask1, inc = float(order["bid"]), float(order["ask"]), float(order["px"])
    mid1, half1 = (bid1 + ask1) / 2.0, (ask1 - bid1) / 2.0
    if half1 <= 0:
        return {"state": "unavailable", "why": "a locked market at submit"}
    t0, sent = float(order["decided_at"]), float(order.get("t") or order["decided_at"])
    last = cal.session_close(et_date(t0)) - CLOSE_GUARD_S
    t2, t3 = min(t0 + cadence, last), min(t0 + 2 * cadence, last)
    tape = sorted((r for r in rows if float(r["t"]) > sent and _ok(r.get("bid"), r.get("ask"))),
                  key=lambda r: float(r["t"]))

    def touched(r, lim):
        return float(r["ask"]) <= lim if buy else float(r["bid"]) >= lim

    def done(px, step, r):
        mid = (float(r["bid"]) + float(r["ask"])) / 2.0
        save = sgn * (inc - px)
        return {"state": "done", "step": step, "arm_px": round(px, 6), "inc_px": inc, "half": round(half1, 6),
                "saving": round(save, 6), "saving_bps": round(save / inc * 1e4, 2),
                "saving_half": round(save / half1, 4), "drift_half": round(sgn * (mid - mid1) / half1, 4),
                "at": round(float(r["t"]), 3)}

    lim = mid1
    for r in tape:
        if float(r["t"]) >= t2:
            break
        if touched(r, lim):
            return done(lim, 1, r)
    r2 = next((r for r in tape if t2 <= float(r["t"]) <= t2 + READ_WITHIN_S), None)
    if r2 is None:
        return {"state": "unavailable", "why": "no read at the second pass"}
    b2, a2 = float(r2["bid"]), float(r2["ask"])
    lim = (b2 + a2) / 2.0 + sgn * (a2 - b2) / 4.0
    for r in tape:
        if float(r["t"]) <= float(r2["t"]):
            continue
        if float(r["t"]) >= t3:
            break
        if touched(r, lim):
            return done(lim, 2, r)
    r3 = next((r for r in tape if t3 <= float(r["t"]) <= t3 + READ_WITHIN_S and float(r["t"]) > float(r2["t"])),
              None)
    if r3 is None:
        return {"state": "unavailable", "why": "no read at the third pass"}
    return done(float(r3["ask"]) if buy else float(r3["bid"]), 3, r3)


def _sign_p(xs):
    """the one-sided sign test's p of a positive median: P(X >= wins | n non-zero, 1/2)"""
    nz = [x for x in xs if x]
    n, k = len(nz), sum(1 for x in nz if x > 0)
    if not n:
        return None
    return round(sum(math.comb(n, i) for i in range(k, n + 1)) / 2.0 ** n, 6)


def opt09_report(rows):
    """OPT-09 over the option rows the tape could price; OPT-08's coverage beside"""
    c = ARMS["opt09_patient"]
    got = [r.get("opt09") for r in rows if r.get("arm") == "option" and r.get("opt09")]
    done = [o for o in got if o.get("state") == "done"]
    sav = [o["saving_half"] for o in done]
    st = S.paired([(r["session"], r["opt09"]["saving_half"]) for r in rows
                   if r.get("arm") == "option" and (r.get("opt09") or {}).get("state") == "done"])
    out = {"contract": dict(c), "n": len(done), "saving_half": st, "sign_p": _sign_p(sav),
           "drift_half": round(sum(o["drift_half"] for o in done) / len(done), 4) if done else None,
           "saving_bps": round(sum(o["saving_bps"] for o in done) / len(done), 2) if done else None,
           "by_step": {k: sum(1 for o in done if o["step"] == k) for k in (1, 2, 3)},
           "unavailable": {}}
    for o in got:
        if o.get("state") != "done":
            out["unavailable"][o.get("why") or "?"] = out["unavailable"].get(o.get("why") or "?", 0) + 1
    cov = round(len(done) / len(got), 4) if got else None
    out["tape"] = {"decided": len(got), "priced": len(done), "coverage": cov,
                   "status": "collecting" if len(got) < c["min_n"] else ("abandon" if cov < 0.5 else "keep")}
    if len(done) < c["min_n"]:
        out["status"] = "descriptive"
        out["note"] = "descriptive until %d paired option orders (%d so far); no rule is applied before" % (
            c["min_n"], len(done))
    else:
        m = st["mean"] or 0.0
        bad = m < c["min_saving_half"] or (out["sign_p"] is None or out["sign_p"] > c["sign_p"]) or \
            (out["drift_half"] or 0.0) > m
        out["status"] = "rejected" if bad else "not_rejected"
    return out


def rel_spread_max(legs):
    """the widest leg's (ask - bid) / mid; inf for a leg without a two-sided market"""
    worst = 0.0
    for l in legs:
        if not _ok(l.get("bid"), l.get("ask")):
            return float("inf")
        b, a = float(l["bid"]), float(l["ask"])
        worst = max(worst, (a - b) / ((a + b) / 2.0))
    return worst


def mac15_skips(legs, cap=CAP):
    return rel_spread_max(legs) > cap


def mac15_report(pkgs):
    """MAC-15 over midna's proposed packages: {"pkg", "sleeve", "legs": [quote at the decision], "closed",
    "pnl_before_spread", "spread_paid"}"""
    c = ARMS["mac15_spread_cap"]
    skip = [p for p in pkgs if mac15_skips(p["legs"])]
    res = [p for p in skip if p.get("closed") and p.get("pnl_before_spread") is not None]
    pnl = round(sum(p["pnl_before_spread"] for p in res), 2)
    paid = round(sum(p["spread_paid"] for p in res), 2)
    out = {"contract": dict(c), "proposed": len(pkgs), "skipped": len(skip), "skipped_resolved": len(res),
           "skipped_pnl_before_spread": pnl, "skipped_spread_paid": paid,
           "open": sum(1 for p in pkgs if not p.get("closed")),
           "by_sleeve": {s: sum(1 for p in skip if p["sleeve"] == s) for s in sorted({p["sleeve"] for p in pkgs})}}
    if len(pkgs) < c["min_n"]:
        out["status"] = "descriptive"
        out["note"] = "descriptive until %d proposed packages (%d so far); no rule is applied before" % (
            c["min_n"], len(pkgs))
    else:
        out["status"] = "rejected" if pnl > paid else "not_rejected"
    return out


# -- the rows: each session's option fills, from the ledger and the tape ---------------------------------------------

def pkg_of(key):
    """a midna package's key: its signal key before ':open' / ':close' (desk/sleeves/midna/options.py)"""
    k = str(key or "")
    for tag in (":open", ":close"):
        if tag in k:
            return k.split(tag, 1)[0]
    return k


def option_rows(rec, root, sessions, cadences=None, version=1):
    """{session: [row]} of the sessions' single-contract option fills: the fill, its child (sleeve, action, key), its
    quote at submit, and for a fill made in its decision's own pass (the incumbent crossed at the first pass) the
    OPT-09 counterfactual on that session's tape"""
    from . import quotes
    from .tape import session_for
    want, out, tapes = set(sessions), {}, {}
    for f in rec.opt_fills:
        d = session_for(f["at"])
        if d not in want:
            continue
        kids = [rec.opt_children[c] for c in f.get("children") or () if c in rec.opt_children]
        if not kids:
            continue
        c = kids[0]
        occ = str(f["inst"])[4:]
        q = f.get("quote_at_submit") or [None, None]
        row = {"v": version, "session": d, "arm": "option", "sleeve": c.get("sleeve"), "occ": occ,
               "side": f.get("side"), "action": c.get("action"), "key": c.get("key"), "pkg": pkg_of(c.get("key")),
               "qty": f.get("qty"), "vqty": c.get("vqty"), "fill_px": f.get("price"), "bid": q[0], "ask": q[1],
               "decided_at": c["at"], "fill_at": f["at"], "first_pass": abs(float(f["at"]) - float(c["at"])) < 1e-6,
               "id": "%s:%s:%s:%s" % (d, c.get("sleeve"), occ, f.get("seq")), "final": True}
        if row["first_pass"]:
            if d not in tapes:
                tapes[d] = {}
                for r in quotes.option_rows(root, d):
                    tapes[d].setdefault(r.get("occ"), []).append(r)
            row["opt09"] = opt09({"side": row["side"], "px": row["fill_px"], "bid": q[0], "ask": q[1],
                                  "t": f.get("sent_at") or f.get("submitted_at") or c["at"], "decided_at": c["at"]},
                                 tapes[d].get(occ, []), (cadences or {}).get(c.get("sleeve")) or DEFAULT_CADENCE_S)
        out.setdefault(d, []).append(row)
    return out


def packages(rows):
    """midna's proposed single-contract packages from the option rows: each package's opening legs (their quotes at
    submit), closed once every opened leg has a closing fill; P&L before spread = sum over legs of (the closing mid -
    the opening mid) x 100 x contracts; the spread paid = each fill's distance from its mid, both ways"""
    by = {}
    for r in rows:
        if r.get("arm") == "option" and r.get("sleeve") in MIDNA_BOOKS:
            by.setdefault((r["sleeve"], r["pkg"]), []).append(r)
    out = []
    for (sid, pkg), rs in sorted(by.items()):
        opens = [r for r in rs if r.get("action") == "enter"]
        if not opens:
            continue
        closes = {r["occ"]: r for r in rs if r.get("action") == "exit"}
        legs = [{"occ": r["occ"], "bid": r["bid"], "ask": r["ask"]} for r in opens]
        closed = all(r["occ"] in closes for r in opens)
        pnl = paid = None
        if closed and all(_ok(r["bid"], r["ask"]) for r in opens + [closes[o["occ"]] for o in opens]):
            pnl = paid = 0.0
            for o in opens:
                x = closes[o["occ"]]
                n = 100.0 * float(o.get("vqty") or o.get("qty") or 0)
                m0, m1 = (float(o["bid"]) + float(o["ask"])) / 2, (float(x["bid"]) + float(x["ask"])) / 2
                pnl += (m1 - m0) * n
                paid += (abs(float(o["fill_px"]) - m0) + abs(float(x["fill_px"]) - m1)) * n
            pnl, paid = round(pnl, 2), round(paid, 2)
        out.append({"pkg": pkg, "sleeve": sid, "legs": legs, "closed": closed and pnl is not None,
                    "pnl_before_spread": pnl, "spread_paid": paid})
    return out


def report(rows):
    """summary.json "arms": the two option arms"""
    return {"opt09_patient": opt09_report(rows), "mac15_spread_cap": mac15_report(packages(rows))}
