"""Earnings-event killed studies: PEAD on the price surprise (pead/code/04_backtest.py) and its V1 overnight spillover
scalp (pead/v1_spillover_dev_2026-10-02.py), on the Nasdaq calendar the studies read, rebuilt forward by
desk/feedlib/killed_data (pead_job, spillover_job)."""
from ... import calendar as cal
from ...contract import Intent
from . import common as K

PEAD_HOLDS = (1, 5, 10, 20)
SPILL_COST, SPILL_FILT = 0.0015, 0.0001


class PeadPriceSurprise(K.KilledSleeve):
    """pead/results_dev.md (04_backtest.py): S = (P[t+1]/P[t-1]-1) - (SPY[t+1]/SPY[t-1]-1) on adjusted daily closes,
    t = the Nasdaq calendar's event date; the top surprise quintile of the calendar quarter goes LONG at open_{t+2};
    every pre-registered hold is traded as its own tranche: exit at the close of entry+0 / +4 / +9 / +19 sessions
    (1 / 5 / 10 / 20 trading days, win_ret's close[entry + n - 1])."""
    SLEEVE_ID = "killed_pead_price_surprise"
    SOURCE = K.source("pead/code/04_backtest.py", "71819ef28c26d078217585a2da603db9d65d207e",
                      results={"path": K.RESEARCH + "pead/results_dev.md",
                               "blob": "bb43e2520265a954f2782afece7c0e31f0c72784"},
                      prereg={"path": K.RESEARCH + "pead/PRE_REGISTRATION.md",
                              "blob": "c94203dd172049213665b4fdb719feb8bf96e37d"})
    NEEDS = {"feeds": ["killed_pead"], "quotes": {"source": "equity"}}
    PARAMS = {"holds": list(PEAD_HOLDS), "entry": "open of t+2", "cohort": "S above the quarter's 80th percentile",
              "notional_per_tranche": K.CAPITAL / 1500, "removed_gates": []}
    DIVERGENCES = [
        "the cohort cut: the study cut each calendar quarter's quintiles after the quarter; forward, the cut is the "
        "80th percentile (pd.qcut's top-bin edge) of the previous complete calendar quarter's surprises",
        "universe: Nasdaq calendar symbols listed in the NASDAQ Trader directories instead of Alpaca /v2/assets",
        "adjusted closes are the hub's (Alpaca adjustment=all when keyed, else Yahoo's dividend-adjusted close)",
    ]

    def plan(self, view, st, tb):
        f = (view.extra or {}).get("killed_pead")
        d = tb.today
        if not f or not f.get("ready") or st.get("seen") == f["t"] or K.signal_day(view.now) is None:
            return []
        st["seen"] = f["t"]
        for sym in sorted(f["cohort"]):
            for h in PEAD_HOLDS:
                tb.add(sym, +1, K.CAPITAL / 1500, f"pead:{h}", d, "open", K.add_sessions(d, h - 1), "close",
                       why=f"event {f['t']} S {f['cohort'][sym]:+.4f} > cut {f['cut']:+.4f}", event=f["t"])
        return [Intent("signal", "SPY", signal_key=f"pead:{f['t']}",
                       reason=f"PEAD cohort for {f['t']}: {len(f['cohort'])} of {f['n_events']} events above "
                              f"{f['cut']:+.5f} ({f['from_quarter']} cut)")]


class PeadSpilloverScalp(K.KilledSleeve):
    """pead/v1_spillover_prereg_2026-10-02.md (KILL): on earnings day t, r_prev_net = c_t / c_{t-1} - 1 - 0.0015 >
    +0.0001 -> buy at the day-t close, sell at the next session's open."""
    SLEEVE_ID = "killed_pead_spillover_scalp"
    SOURCE = K.source("pead/v1_spillover_dev_2026-10-02.py", "42331b228ec47d4d3f6bbf58e16da35e12bf25fe",
                      prereg={"path": K.RESEARCH + "pead/v1_spillover_prereg_2026-10-02.md",
                              "blob": "9926c2587a58a87274cf2a37c46f1f0d306dcca9"})
    SCHEDULE = "open+0:open+30,close-35:close-11"
    CADENCE = 120
    NEEDS = {"feeds": ["killed_spillover"], "quotes": {"source": "equity"}}
    PARAMS = {"filter": "c_t/c_{t-1} - 1 - 0.0015 > 0.0001", "entry": "close of t (market-on-close)",
              "exit": "open of t+1", "notional": K.CAPITAL / 250, "removed_gates": []}
    DIVERGENCES = [
        "c_t is the live price the spillover job reads 15:28-15:40 ET (the order is the market-on-close, the "
        "study's c_t); c_{t-1} is the previous session's daily close",
        "universe: Nasdaq calendar symbols listed in the NASDAQ Trader directories instead of Alpaca /v2/assets",
    ]

    def plan(self, view, st, tb):
        d = tb.today
        if not K.in_moc_window(view.now) or st.get("day") == d:
            return []
        f = (view.extra or {}).get("killed_spillover")
        if not f or f.get("t") != d:
            return []
        priced = {s: v for s, v in (f.get("events") or {}).items() if v.get("last") and v.get("prev_close")}
        if f.get("events") and not priced:
            return []                                     # the job has not priced today's events yet
        st["day"] = d
        nxt = K.add_sessions(d, 1)
        n = 0
        for sym in sorted(priced):
            v = priced[sym]
            px = K.fresh_last(view, sym) or float(v["last"])
            r = px / float(v["prev_close"]) - 1.0 - SPILL_COST
            if r > SPILL_FILT:
                tb.add(sym, +1, K.CAPITAL / 250, "spill", d, "close", nxt, "open",
                       why=f"r_prev_net {r:+.5f}", event=d)
                n += 1
        return [Intent("signal", "SPY", signal_key=f"spill:{d}",
                       reason=f"{d}: {n} of {len(priced)} earnings events pass r_prev_net > +0.01%")]
