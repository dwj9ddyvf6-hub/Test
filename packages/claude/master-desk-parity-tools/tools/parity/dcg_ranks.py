"""dcg ranks: the old mode_rank of daily_cyan_gbm_sleeve, rule_1d_cyan_smallcap, rule_1d_green_tom,
rule_1w_cyan_mom_adx and rule_1w_swing_beta_wt vs the restored sleeves' signals + dcg_core.rank.

Per case a synthetic genome (tools/parity/dcg_frame._case) scored by the vendored Node scorers; some signal-bar
fires get their score / features nudged across the sleeves' thresholds so every filter is exercised (the rank
law consumes the scorer's output; the scorer itself is byte-identical — dcg_frame). The OLD mode_rank runs with
its scorer, market frame and EDGAR lookup stubbed to the same values (book, surviving pending and the mcap
values random per case); the port reads the nightly scoring file built from the same fires. Compared: the
staged pending (buys, sells, exit dates)."""
import json
import os
import random
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from desk.feedlib import dcg
from desk.sleeves.femto import compat as fc

from . import femto_module, old_run, write_receipt
from .dcg_frame import _case

ET = ZoneInfo("America/New_York")
N_CASES = 8
SLEEVES = {"daily_cyan_gbm": ("daily_cyan_gbm_sleeve", None), "rule_1d_cyan_smallcap": ("rule_1d_cyan_smallcap", "1D:cyan"),
           "rule_1d_green_tom": ("rule_1d_green_tom", "1D:green"), "rule_1w_cyan_mom_adx": ("rule_1w_cyan_mom_adx", "1W:cyan"),
           "rule_1w_swing_beta_wt": ("rule_1w_swing_beta_wt", "1W:swing")}

OLD = r'''
import sys, types, importlib
from datetime import datetime
from zoneinfo import ZoneInfo
sys.argv = ["x"]
ET = ZoneInfo("America/New_York")
import sleeve_core as core
import rule_sleeve_base as B
out = []
for c in PAYLOAD["cases"]:
    M = importlib.import_module(c["module"])
    bars = {s: [list(r) for r in rows] for s, rows in c["bars"].items()}
    today = c["today"]
    now = datetime.fromisoformat(today).replace(hour=16, minute=40, tzinfo=ET)
    core.et_now = lambda now=now: now
    b2 = {s: [b for b in bl if b[0] <= today] for s, bl in bars.items()}
    b2 = {s: bl for s, bl in b2.items() if len(bl) >= 60}
    days = sorted({b[0] for bl in b2.values() for b in bl})
    STATE = {"book": c["book"], "pending": c["pending"], "stats": {}}
    M.SL.load_state = lambda dry_run=False, STATE=STATE: STATE
    M.SL.save_state = lambda s: None
    M.SL.log = lambda e: None
    fires = c["fires"]
    if c["module"] == "daily_cyan_gbm_sleeve":
        core.load_cache = lambda path, bars=bars: {"bars": bars}
        M.build_market = lambda days, bars: {}
        M.load_xsect = lambda: {"days": [], "xsect": {}}
        M.score_symbols = lambda *a, fires=fires, **k: fires
    else:
        M.base.prepare_bars = lambda today, b2=b2, days=days, **k: (b2, days)
        M.base.build_market = lambda days, bars: {}
        M.base.prepare_xsect = lambda days: {"xsect": {}}
        M.base.fomc_indices = lambda days: []
        M.base.score_rule_symbols = lambda *a, fires=fires, **k: fires
        if hasattr(M, "mcap_edgar"):
            LM = c["mcap"]
            M.mcap_edgar.log_mcap = lambda s, d, log=None, LM=LM: (LM.get(s), "stub")
    M.mode_rank(today, dry_run=False, no_fetch=True)
    out.append({k: STATE["pending"].get(k) for k in ("buys", "sells", "exit_dates")})
print(json.dumps(out))
'''


def _nudge(rnd, fires_by_sym, bars, gbm):
    """push some signal-bar fires across the sleeves' thresholds (the rank law's inputs); names without a
    signal-bar fire get one injected (random walks rarely fire on their last bar)."""
    for s in rnd.sample(sorted(bars), min(len(bars), 30)):
        bl = bars[s]
        if s in dcg.NOT_SCORED or any(f.get("date") == bl[-1][0] for f in fires_by_sym.get(s) or []):
            continue
        fires_by_sym.setdefault(s, []).append({"date": bl[-1][0], "score": 0.0, "features": {}} if gbm else
                                              {"date": bl[-1][0], "features": {}})
    for s, fires in fires_by_sym.items():
        bl = bars.get(s) or []
        for f in fires:
            if not bl or f.get("date") != bl[-1][0] or rnd.random() > 0.6:
                continue
            if gbm:
                f["score"] = round(rnd.choice((0.0021, 0.003, 0.01, 0.0019, 0.02)), 6)
            else:
                ft = f.setdefault("features", {})
                ft.update(pxn=2, di=rnd.uniform(-12, 14), mom121=rnd.uniform(0.5, 0.9), disp=rnd.uniform(0.02, 0.03),
                          tom=rnd.choice((0, 1)), dv=rnd.uniform(6.5, 7.6), mom=rnd.uniform(0.3, 0.7),
                          adx=rnd.uniform(20, 40), beta=rnd.uniform(1.0, 2.0), wt1=rnd.uniform(10, 50),
                          ribbons=rnd.uniform(0.0, 0.02))


def run():
    rnd = random.Random(77)
    old_fomc = [e["date"] for e in json.load(open(os.path.join(dcg.VENDOR, "macro_events.json")))["events"]
                if "FOMC" in e.get("name", "").upper()]
    cases, news = [], []
    for k in range(N_CASES):
        c = _case(rnd, k)
        if k % 2 == 0:                                # a turn-of-month day: the green rule's tom == 1
            days = sorted({r[0] for rows in c["bars"].values() for r in rows})
            tom = [d for i, d in enumerate(days[300:], 300) if d[:7] != days[i - 1][:7]
                   or (i + 1 < len(days) and d[:7] != days[i + 1][:7])]
            c["today"] = rnd.choice(tom)
            c["vix"] = {d: v for d, v in c["vix"].items() if d <= c["today"]}
            c["vix"][c["today"]] = 20.0
        # a richer price spread so the $5 / $5-$10 bands bite
        for s in list(c["bars"])[10:60]:
            f = rnd.uniform(0.02, 0.3)
            c["bars"][s] = [[r[0], r[1] * f, r[2] * f, r[3] * f, r[4] * f, r[5]] for r in c["bars"][s]]
        base, syms, bars = dcg.frame(c["bars"], c["vix"], c["today"], ahead_n=0, fomc=old_fomc)
        gfires, _ = dcg.score(dcg.SCORER, base, syms)
        rfires = {}
        for lane, sig in dcg.RULE_LANES:
            rfires[f"{lane}:{sig}"], _ = dcg.score(dcg.RULE_SCORER, dict(base, lane=lane, signal=sig), syms)
        _nudge(rnd, gfires, bars, True)
        for v in rfires.values():
            _nudge(rnd, v, bars, False)
        scored = list(bars)
        dates = sorted({b[0] for bl in bars.values() for b in bl})
        for name, (module, key) in SLEEVES.items():
            book = {}
            for s in rnd.sample(scored, rnd.randint(0, 9)):
                ed = dates[-rnd.randint(2, 140)]
                book[s] = {"qty": 10.0, "entry_px": 20.0, "entry_date": ed, "exit_due_date": "2099-01-01"}
            pend = {"buys": rnd.sample(scored, rnd.randint(0, 3)), "sells": rnd.sample(scored, rnd.randint(0, 1)),
                    "exit_dates": {}}
            mcap = {s: rnd.choice((None, 9.1, 9.5, 8.7)) for s in scored}
            fires = gfires if key is None else rfires[key]
            cases.append({"module": module, "bars": c["bars"], "today": c["today"], "book": book, "pending": pend,
                          "fires": fires, "mcap": mcap})
            news.append((name, key, bars, gfires, rfires, base))
    old = old_run(OLD, {"cases": cases}, timeout=3000)
    n = same = 0
    diffs = []
    counts = {"staged_buys": 0, "staged_sells": 0}

    def cmp(kind, ref, a, b):
        nonlocal n, same
        n += 1
        same += a == b
        if a != b:
            diffs.append({"kind": kind, "ref": ref, "old": a, "new": b})

    for ci, (c, (name, key, bars, gfires, rfires, base), o) in enumerate(zip(cases, news, old)):
        F = femto_module(name)
        scores = {"date": c["today"], "gbm": {s: {"date": f["date"], "score": f["score"]}
                                              for s, f in dcg.last_bar_fires(gfires, bars).items()},
                  "rules": {k: {s: {"date": f["date"], "features": f.get("features") or {}}
                                for s, f in dcg.last_bar_fires(v, bars).items()} for k, v in rfires.items()},
                  "facts": {s: {"date": bl[-1][0], "px": bl[-1][4], "dv20": dcg.dv20(bl, len(bl) - 1)}
                            for s, bl in bars.items()},
                  "recent_days": base["days"][-30:]}
        for s, fa in scores["facts"].items():
            fa["log_mcap"] = c["mcap"].get(s)
        ebars = {s: [{"t": datetime.fromisoformat(r[0]).replace(hour=4, tzinfo=timezone.utc).timestamp(), "o": r[1],
                      "h": r[2], "l": r[3], "c": r[4], "v": r[5]} for r in bars[s]] for s in c["book"] if s in bars}
        state = {s: {"position": dict(p)} for s, p in c["book"].items()}
        now = datetime.fromisoformat(c["today"]).replace(hour=16, minute=45, tzinfo=ET).timestamp()
        ctx = fc.Context(now=now, session=c["today"], equity=100_000.0,
                         extra={"sleeve_state": state, "meta": {"pending": c["pending"]}, "dcg": scores})
        meta = F.next_meta(ebars, {}, ctx, [])
        p = meta.get("pending") or {}
        cmp("pending", [ci, name], o, {k: p.get(k) for k in ("buys", "sells", "exit_dates")})
        counts["staged_buys"] += len(o.get("buys") or [])
        counts["staged_sells"] += len(o.get("sells") or [])
        counts[name] = counts.get(name, 0) + len(set(o.get("buys") or []) - set(c["pending"]["buys"]))
    res = {"sleeve": "dcg_ranks", "cases": n, "identical": same, "n_diffs": len(diffs), "diffs": diffs[:20],
           "exercised": counts}
    write_receipt("dcg_ranks", res)
    return res
