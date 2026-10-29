"""The lab's analysis: summary.json from the outcome rows (docs/research/2026-10-18-lab/DESIGN.md section 8). Every
statistic is in R (the decision's ATR) and paired by session (desk/lab/stats.py).

  alpha          the reference policy's R minus the same session's placebo mean: overall, per engine, per sleeve
                 (shrunk across sleeves), the killed_* controls apart
  policy_effects each policy minus the reference on the same signals, per engine and pooled; BH across policies x
                 engines; the controls' effect beside each; per-sleeve effects shrunk across sleeves
  fingerprints   per engine: the stop keeping 90 % of the reference winners, the losers it cuts; the MFE horizon
  agreement      the terminal's ranking: 2+ engines on one (symbol, side, session) vs one engine
  evidence       signals, sessions, resolved outcomes, the standard error and the minimum detectable effect
  capture / freshness   the desk's real execution and its decisions' price bases (entries, exits, targets), per sleeve
  engine_fb2     the analysis engine's forward test on the desk's long entries (desk/analysis, desk/lab/research.py):
                 a VETO arm (the veto applied: small, micro and nano) and a PASS arm (every other scored entry), each
                 with n, the reference R, its excess over the placebo and the share of big losers; descriptive until
                 each arm holds FB2_MIN resolved entries (FB2's own test is the research's, PROGRAM2.md 2-19 s5)
A verdict needs q <= GATE_Q, >= GATE_N signals and >= GATE_SESSIONS sessions; anything less is "collecting". A policy
whose effect on the controls has the same sign and at least the live size is "not_specific": it helps the
research-killed formulations as much, so it says something about the period, not about execution."""
import math

from .. import calendar as cal
from . import arms, fidelity, lazarus, options
from . import stats as S
from .policies import (ARM_ONLY, BENCHMARKS, OPEN_CONTEXT, OPEN_ONLY, OPEN_TESTS, POLICIES, REFERENCE, TEXT,
                       WINDOWS)
from .tape import in_session

GATE_N, GATE_SESSIONS, GATE_Q = 30, 5, 0.10
FP_MIN = 10                                  # a fingerprint needs this many reference winners and losers
FB2_MIN = 30                                 # the FB2 section is descriptive until each arm holds this many resolved
BIG_LOSER_Q = 0.05                           # a big loser: R at or below the placebo's own 5% tail (the research's
#                                              lose5 is the bottom 5% of its session's names)


def r_of(row, policy):
    """a row's R under a policy once final (an unfilled or skipped policy is 0), else None"""
    o = (row.get("outcomes") or {}).get(policy) or {}
    if o.get("state") != "done":
        return None
    return float(o["r"]) if o.get("filled") else 0.0


def _arms(rows):
    sig = [r for r in rows if r["arm"] == "signal"]
    return ([r for r in sig if r["class"] != "control"], [r for r in sig if r["class"] == "control"],
            [r for r in rows if r["arm"] == "placebo"])


def _placebo_means(plc):
    acc = {}
    for r in plc:
        x = r_of(r, REFERENCE)
        if x is not None:
            acc.setdefault(r["session"], []).append(x)
    return {d: sum(v) / len(v) for d, v in acc.items()}


def gated(st, q):
    """a statistic's verdict: collecting until n, sessions and q pass the gates"""
    if st.get("n", 0) < GATE_N or st.get("sessions", 0) < GATE_SESSIONS or q is None or q > GATE_Q:
        return "collecting"
    return "positive" if (st.get("mean") or 0) > 0 else "negative"


def _alpha(rows, pm):
    obs, raw, base = [], [], []
    for r in rows:
        x = r_of(r, REFERENCE)
        if x is not None and r["session"] in pm:
            obs.append((r["session"], x - pm[r["session"]]))
            raw.append(x)
            base.append(pm[r["session"]])
    st = S.paired(obs)
    st["ref_r"] = round(sum(raw) / len(raw), 4) if raw else None
    st["placebo_r"] = round(sum(base) / len(base), 4) if base else None
    return st


def _by(rows, key):
    out = {}
    for r in rows:
        out.setdefault(r[key], []).append(r)
    return out


def _table(groups, fn):
    """{name: stat} with BH q-values across the table and each row's verdict"""
    t = {k: fn(v) for k, v in sorted(groups.items())}
    qs = S.qvalues({k: v.get("p") for k, v in t.items()})
    for k, v in t.items():
        v["q"] = qs.get(k)
        v["status"] = gated(v, v["q"])
    return t


def _shrunk(table):
    """per-sleeve means shrunk across sleeves (se^2 from the row's own SE, else the pooled dispersion / n)"""
    est = {k: (v["mean"], v["se"] ** 2) for k, v in table.items() if v.get("mean") is not None and v.get("se")}
    pooled = [v["se"] ** 2 * v["n"] for v in table.values() if v.get("se")]
    s2 = sum(pooled) / len(pooled) if pooled else None
    for k, v in table.items():
        if k not in est and v.get("mean") is not None and s2:
            est[k] = (v["mean"], s2 / max(1, v["n"]))
    shrunk, tau2, m = S.shrink(est)
    for k, v in table.items():
        v["shrunk"] = shrunk.get(k)
    return {"tau2": tau2, "mean": m}


def alpha(live, ctrl, pm):
    out = {"overall": _alpha(live, pm), "control": _alpha(ctrl, pm)}
    for k in ("overall", "control"):
        out[k]["q"] = out[k]["p"]
        out[k]["status"] = gated(out[k], out[k]["q"])
    out["by_engine"] = _table(_by(live, "engine"), lambda v: _alpha(v, pm))
    out["by_sleeve"] = _table(_by(live + ctrl, "sleeve"), lambda v: dict(_alpha(v, pm), **{"class": v[0]["class"]}))
    out["shrinkage"] = _shrunk(out["by_sleeve"])
    return out


def _effect(rows, policy, base=REFERENCE):
    obs = []
    for r in rows:
        a, b = r_of(r, policy), r_of(r, base)
        if a is not None and b is not None:
            obs.append((r["session"], a - b))
    return S.paired(obs)


def effects(live, ctrl):
    """policy effects vs the reference: per engine (and pooled 'all'), BH across policies x engines, the controls'"""
    others = [p for p in POLICIES if p != REFERENCE and p not in OPEN_ONLY and p not in ARM_ONLY]
    groups = dict(_by(live, "engine"), all=live)
    table = {e: {p: _effect(rows, p) for p in others} for e, rows in sorted(groups.items())}
    qs = S.qvalues({(e, p): st.get("p") for e, ps in table.items() for p, st in ps.items() if p not in BENCHMARKS})
    controls = {p: _effect(ctrl, p) for p in others}
    recs = []
    for e, ps in table.items():
        for p, st in ps.items():
            st["q"] = qs.get((e, p))
            c = controls[p]
            st["control_mean"], st["control_n"] = c.get("mean"), c.get("n")
            if st.get("se") is not None and c.get("se") is not None:
                st["vs_control"] = {"diff": round(st["mean"] - c["mean"], 4),
                                    "se": round(math.hypot(st["se"], c["se"]), 4)}
            if p in BENCHMARKS:
                st["status"] = "benchmark"
            elif gated(st, st["q"]) == "collecting":
                st["status"] = "collecting"
            elif c.get("n", 0) >= GATE_N and c.get("mean") is not None and \
                    (c["mean"] > 0) == (st["mean"] > 0) and abs(c["mean"]) >= abs(st["mean"]):
                st["status"] = "not_specific"
            else:
                st["status"] = "recommend"
                st["controls_checked"] = c.get("n", 0) >= GATE_N
                recs.append({"engine": e, "policy": p, "family": "primary", "rule": TEXT[p], "effect_r": st["mean"],
                             "q": st["q"],
                             "n": st["n"], "sessions": st["sessions"],
                             "direction": "adopt" if st["mean"] > 0 else "avoid",
                             "controls_checked": st["controls_checked"]})
    by_sleeve = {}
    for p in others:
        t = {s: _effect(rows, p) for s, rows in _by(live, "sleeve").items()}
        t = {s: v for s, v in t.items() if v["n"]}
        meta = _shrunk(t)
        by_sleeve[p] = {"sleeves": {s: {k: v.get(k) for k in ("n", "sessions", "mean", "shrunk")}
                                    for s, v in sorted(t.items())}, **meta}
    opened, orecs = _open_family(groups, ctrl)
    recs += orecs
    recs.sort(key=lambda x: (-abs(x["effect_r"]), x["engine"], x["policy"]))
    return {"by_engine": table, "control": controls, "by_sleeve_shrunk": by_sleeve, "open": opened}, recs


def _open_family(groups, ctrl):
    """the open family (policies.OPEN_TESTS): each test a paired difference against its own comparator, with its own
    BH across tests x engines and the primary family's gates and control check"""
    def _in(rows, t):                                    # a context test reads only the rows whose flag is true
        k = OPEN_CONTEXT.get(t)
        return rows if k is None else [r for r in rows if (r.get("ctx") or {}).get(k)]
    table = {e: {t: _effect(_in(rows, t), a, b) for t, (a, b, _) in OPEN_TESTS.items()}
             for e, rows in sorted(groups.items())}
    qs = S.qvalues({(e, t): st.get("p") for e, ts in table.items() for t, st in ts.items()})
    controls = {t: _effect(_in(ctrl, t), a, b) for t, (a, b, _) in OPEN_TESTS.items()}
    recs = []
    for e, ts in table.items():
        for t, st in ts.items():
            st["q"] = qs.get((e, t))
            c = controls[t]
            st["control_mean"], st["control_n"] = c.get("mean"), c.get("n")
            if gated(st, st["q"]) == "collecting":
                st["status"] = "collecting"
            elif c.get("n", 0) >= GATE_N and c.get("mean") is not None and \
                    (c["mean"] > 0) == (st["mean"] > 0) and abs(c["mean"]) >= abs(st["mean"]):
                st["status"] = "not_specific"
            else:
                st["status"] = "recommend"
                recs.append({"engine": e, "policy": OPEN_TESTS[t][0], "test": t, "family": "open",
                             "against": OPEN_TESTS[t][1], "rule": OPEN_TESTS[t][2], "effect_r": st["mean"],
                             "q": st["q"], "n": st["n"], "sessions": st["sessions"],
                             "direction": "adopt" if st["mean"] > 0 else "avoid",
                             "controls_checked": c.get("n", 0) >= GATE_N})
    return {"tests": {t: {"policy": a, "against": b, "rule": txt, "context": OPEN_CONTEXT.get(t)}
                      for t, (a, b, txt) in OPEN_TESTS.items()},
            "by_engine": table, "control": controls}, recs


def _mae5(r):
    o = (r.get("outcomes") or {}).get(REFERENCE) or {}
    m = o.get("mae") or [None] * len(WINDOWS)
    return m[WINDOWS.index(5)]


def _mfe(rows, i):
    xs = [((r.get("outcomes") or {}).get(REFERENCE) or {}).get("mfe") for r in rows]
    return [x[i] for x in xs if x and x[i] is not None]


def fingerprint(rows, plc):
    """the reference entry's MAE / MFE fingerprint of one group of signals"""
    done = [(r_of(r, REFERENCE), _mae5(r)) for r in rows
            if r_of(r, REFERENCE) is not None and ((r.get("outcomes") or {}).get(REFERENCE) or {}).get("filled")]
    done = [(x, m) for x, m in done if m is not None]
    win, lose = [m for x, m in done if x > 0], [m for x, m in done if x <= 0]
    out = {"winners": len(win), "losers": len(lose), "status": "collecting"}
    if len(win) >= FP_MIN and len(lose) >= FP_MIN:
        s = S.quantile(win, 0.9)
        out.update(status="measured", stop_atr=round(s, 3),
                   winners_kept=round(sum(1 for m in win if m <= s) / len(win), 3),
                   losers_cut=round(sum(1 for m in lose if m > s) / len(lose), 3),
                   ref_r=round(sum(x for x, _ in done) / len(done), 4),
                   ref_r_with_stop=round(sum((-s if m > s else x) for x, m in done) / len(done), 4))
    med = {n: (S.median(_mfe(rows, i)), S.median(_mfe(plc, i)), len(_mfe(rows, i))) for i, n in enumerate(WINDOWS)}
    out["mfe_median"] = {str(n): {"signals": None if a is None else round(a, 3),
                                  "placebo": None if b is None else round(b, 3), "n": k}
                         for n, (a, b, k) in med.items()}
    if med[WINDOWS[-1]][2] >= 2 * FP_MIN and all(a is not None and b is not None for a, b, _ in med.values()):
        excess = {n: a - b for n, (a, b, _) in med.items()}
        top = max(excess.values())
        out["horizon"] = next(n for n in WINDOWS if excess[n] >= 0.9 * top) if top > 0 else None
    return out


def agreement(live, rows_manifest):
    """2+ engines agreeing on (symbol, side, session) vs one, among the terminal's eligible sleeves"""
    cands = {}
    for r in live:
        row = rows_manifest.get(r["sleeve"]) or {}
        if r["class"] != "trading" or r["sleeve"].startswith("mon_") or row.get("status") == "disabled" \
                or row.get("kind", "trading") != "trading":
            continue
        c = cands.setdefault((r["session"], r["symbol"], r["side"]), {"engines": set(), "first": r})
        c["engines"].add(r["engine"])
        if r["decided_at"] < c["first"]["decided_at"]:
            c["first"] = r
    days = {}
    for (d, _, _), c in cands.items():
        x = r_of(c["first"], REFERENCE)
        if x is not None:
            days.setdefault(d, ([], []))[0 if len(c["engines"]) >= 2 else 1].append(x)
    obs = [(d, sum(m) / len(m) - sum(s) / len(s)) for d, (m, s) in days.items() if m and s]
    st = S.paired(obs)
    n_multi = sum(len(m) for m, _ in days.values())
    n_single = sum(len(s) for _, s in days.values())
    st.update(candidates=len(cands), multi=sum(1 for c in cands.values() if len(c["engines"]) >= 2),
              resolved_multi=n_multi, resolved_single=n_single)
    q = st["p"]
    st["status"] = "collecting" if (n_multi + n_single < GATE_N or st["sessions"] < GATE_SESSIONS or q is None
                                    or q > GATE_Q) else ("multi_better" if st["mean"] > 0 else "multi_worse")
    return st


def _med(xs):
    xs = [x for x in xs if x is not None]
    m = S.median(xs)
    return None if m is None else round(m, 2)


def _share(xs):
    xs = [x for x in xs if x is not None]
    return round(sum(1 for x in xs if x) / len(xs), 3) if xs else None


def nbo_src(row):
    """where a row's next-bar price came from (tape.nbo_source; EQ-06): the row's own field, else (a row frozen before
    it was recorded) what its interval and its nbo entry say"""
    if row.get("nbo_src"):
        return row["nbo_src"]
    live = in_session(row["decided_at"])
    if not live:
        return "next_open"
    if row.get("iv") != "1h":
        return "fallback"
    at_ = ((row.get("outcomes") or {}).get("nbo_t5") or {}).get("entry_at")
    return "1h" if at_ is not None and at_ < cal.session_close(live) else "next_open"


def _own(rs):
    """a sleeve's own bar interval: the one most of its rows carry"""
    n = {}
    for r in rs:
        if r.get("own"):
            n[r["own"]] = n.get(r["own"], 0) + 1
    return max(sorted(n), key=n.get) if n else None


def capture(rows):
    """the desk's real entries per sleeve (Perold: is = delay + trade; vs_nbo against the simplest rule). A 1h sleeve's
    vs_nbo is the median over its 1h-sourced rows only (EQ-06): a row whose decision session's hourly bars were not
    cached was priced at the next session's open, another question; it is counted and reported apart"""
    out = {}
    for sid, rs in sorted(_by([r for r in rows if r["arm"] == "signal"], "sleeve").items()):
        caps = [r.get("capture") or {} for r in rs]
        kids = [c for c in caps if c.get("children")]
        filled = [c for c in kids if c.get("filled")]
        ended = [c for c in kids if c.get("filled") or c.get("ended")]
        if not kids:
            continue
        fr = [(nbo_src(r), r["capture"]) for r in rs if (r.get("capture") or {}).get("filled")]
        srcs = _count(s for s, _ in fr)
        hourly = _own(rs) == "1h"
        used = [c for s, c in fr if s != "fallback"] if hourly else [c for _, c in fr]
        vs = {"vs_nbo_bps": _med(c.get("vs_nbo_bps") for c in used), "nbo_src": srcs,
              "vs_nbo_rows": sum(1 for c in used if c.get("vs_nbo_bps") is not None),
              "vs_nbo_basis": "1h-sourced rows only" if hourly else "all filled rows"}
        if hourly and srcs.get("fallback"):
            vs["vs_nbo_fallback_bps"] = _med(c.get("vs_nbo_bps") for s, c in fr if s == "fallback")
        out[sid] = {"signals": len(rs), "with_children": len(kids), "filled": len(filled),
                    "fill_rate": round(len(filled) / len(ended), 3) if ended else None,
                    **{k: _med(c.get(k) for c in filled) for k in ("is_bps", "delay_bps", "trade_bps", "lag_s")},
                    **vs,
                    "corrected": sum(1 for c in filled if c.get("corrected")),
                    "corr_bps_max": max((abs(c.get("corr_bps") or 0) for c in filled), default=None),
                    "decision_off_arrival_2pct": sum(1 for c in filled if abs(c.get("delay_bps") or 0) > 200),
                    "decision_off_arrival_5pct": sum(1 for c in filled if abs(c.get("delay_bps") or 0) > 500),
                    "exits": sum(1 for c in filled if c.get("exit_at")),
                    "same_session_exits": sum(1 for c in filled if c.get("same_session_exit"))}
    return out


FRESH_FLAGS = ("stale", "cross_session", "off_market", "mismatch")


def freshness(rows):
    """per sleeve, over its entry signals and its exit / target intents: bases, flag shares, median gaps, and the
    flags most of its decisions carry"""
    facts = [(r["sleeve"], r.get("kind", "enter"), r.get("fresh")) for r in rows if r["arm"] in ("signal", "intent")]
    out = {}
    for sid in sorted({s for s, _, _ in facts}):
        fs = [(k, f) for s, k, f in facts if s == sid and f]
        if not fs:
            continue
        basis = {}
        for _, f in fs:
            basis[f.get("basis") or "none"] = basis.get(f.get("basis") or "none", 0) + 1
        kinds = {}
        for k, _ in fs:
            kinds[k] = kinds.get(k, 0) + 1
        row = {"intents": len(fs), "kinds": kinds, "basis": basis, "own": fs[0][1].get("own"),
               **{k: _share(f.get(k) for _, f in fs) for k in FRESH_FLAGS},
               "abs_dev_pct": _med(abs(f["dev_pct"]) if f.get("dev_pct") is not None else None for _, f in fs),
               "abs_exec_gap_pct": _med(abs(f["exec_gap_pct"]) if f.get("exec_gap_pct") is not None else None
                                        for _, f in fs),
               "basis_age_s": _med(f.get("basis_age_s") for _, f in fs),
               "event_age_s": _med(f.get("event_age_s") for _, f in fs)}
        row["flags"] = [k for k in FRESH_FLAGS if (row[k] or 0) > 0.5]
        out[sid] = row
    return out


def _missing(reason):
    r = str(reason or "")
    return "no screen" if r.startswith("no screen") else "not in the screen" if " is not in the " in r else r


def engine_fb2(live, plc):
    """the analysis engine's arms on the live long entries whose screen is from FB2's first session on: VETO (the
    veto applied) and PASS (every other scored entry, liquid included: never vetoed); per arm n, the resolved count,
    the mean reference R, its excess over the same session's placebo mean (paired, day-clustered) and the share of
    big losers (R at or below the 5% quantile of every resolved placebo R)"""
    from ..analysis import FB2_START                   # here, not at import: desk/engine.py loads this package
    plc_r = [x for x in (r_of(r, REFERENCE) for r in plc) if x is not None]
    cut = S.quantile(plc_r, BIG_LOSER_Q)
    pm = _placebo_means(plc)
    arms, out = {"VETO": [], "PASS": []}, {"short": 0, "before_fb2": 0, "unscored": {}, "missing": {},
                                           "liquid_flagged": 0}
    for r in live:
        res = r.get("research") or {}
        e = res.get("engine")
        if r.get("side") != "long":
            out["short"] += 1
        elif str(res.get("engine_session") or "") < FB2_START:     # a row from before the engine counts here too
            out["before_fb2"] += 1
        elif e is None:
            k = _missing(res.get("engine_reason"))
            out["missing"][k] = out["missing"].get(k, 0) + 1
        elif not e.get("scored"):
            out["unscored"][e.get("reason")] = out["unscored"].get(e.get("reason"), 0) + 1
        else:
            arms["VETO" if e.get("veto_applied") else "PASS"].append(r)
            out["liquid_flagged"] += bool(e.get("tier") == "liquid" and e.get("veto"))
    stats = {}
    for k, rs in arms.items():
        xs = [x for x in (r_of(r, REFERENCE) for r in rs) if x is not None]
        exc = _alpha(rs, pm)
        big = sum(1 for x in xs if cut is not None and x <= cut)
        stats[k] = {"n": len(rs), "resolved": len(xs), "mean_r": round(sum(xs) / len(xs), 4) if xs else None,
                    "excess_r": {k2: exc.get(k2) for k2 in ("n", "sessions", "mean", "se", "t", "p")},
                    "big_losers": big, "big_loser_share": round(big / len(xs), 3) if xs else None}
    done = all(a["resolved"] >= FB2_MIN for a in stats.values())
    return dict(out, from_session=FB2_START, arms=stats, big_loser_r=cut, placebo_n=len(plc_r),
                status="measured" if done else "descriptive",
                note="descriptive until each arm holds %d resolved entries; R and its excess over the placebo are "
                     "the lab's reference policy, in ATR units. FB2's own verdict is the research's test "
                     "(PROGRAM2.md 2-19 s5: the volatility-matched 20-session excess return, a session-block "
                     "bootstrap), never this table" % FB2_MIN)


def evidence(live, ctrl, plc, open_sessions):
    sessions = sorted({r["session"] for r in live})
    res = [r for r in live if r_of(r, REFERENCE) is not None]
    st = _alpha(live, _placebo_means(plc))
    se = st.get("se")
    need = None
    if se and st["sessions"]:
        need = math.ceil(st["sessions"] * (S.mde(se) / 0.25) ** 2)
    return {"signals": len(live), "controls": len(ctrl), "placebo": len(plc), "sessions": len(sessions),
            "first_session": sessions[0] if sessions else None, "last_session": sessions[-1] if sessions else None,
            "resolved_reference": len(res), "resolved_sessions": len({r["session"] for r in res}),
            "alpha_se_r": se, "mde_r": S.mde(se), "sessions_for_mde_0.25r": need,
            "provisional_rows": sum(1 for r in live + ctrl + plc if r["session"] in open_sessions),
            "one_hour_signals": sum(1 for r in live + ctrl if r.get("iv") == "1h"),
            "nbo_sources": _count(nbo_src(r) for r in live + ctrl)}


def _count(xs):
    out = {}
    for x in xs:
        out[x] = out.get(x, 0) + 1
    return dict(sorted(out.items()))


def summary(rows, manifest, meta):
    live, ctrl, plc = _arms(rows)
    pm = _placebo_means(plc)
    eff, recs = effects(live, ctrl)
    engines = _by(live, "engine")
    fp = {e: fingerprint(v, plc) for e, v in sorted(engines.items())}
    fp["all"], fp["control"] = fingerprint(live, plc), fingerprint(ctrl, plc)
    return dict(meta, reference=REFERENCE, policies=TEXT, benchmarks=list(BENCHMARKS),
                gates={"q": GATE_Q, "signals": GATE_N, "sessions": GATE_SESSIONS},
                evidence=evidence(live, ctrl, plc, set(meta.get("open_sessions") or ())),
                alpha=alpha(live, ctrl, pm), policy_effects=eff, recommendations=recs, fingerprints=fp,
                agreement=agreement(live, manifest), capture=capture(rows), freshness=freshness(rows),
                fidelity=fidelity.gate(rows), engine_fb2=engine_fb2(live, plc),
                arms=dict(arms.report(live, ctrl, plc), **options.report(rows), **lazarus.report(rows)))
