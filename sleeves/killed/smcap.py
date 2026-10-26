"""52-week small-cap / high-beta beaten-down study (weekly-phenotypes/PRE_REG_SMCAP_BETA_52W.md,
run_smcap_beta_52w.py; killed: the triple-filtered set was empty, n = 0)."""
from datetime import date, timedelta

from ... import calendar as cal
from ...contract import Intent
from . import common as K


def exit_session(friday):
    """the Friday 52 weeks after the signal Friday (its close; the session before it when it is a holiday)."""
    d = date.fromisoformat(friday) + timedelta(days=364)
    while not cal.is_trading_day(d):
        d -= timedelta(days=1)
    return d.isoformat()


class SmcapBeta52w(K.KilledSleeve):
    """each week's M2 qualifiers (the desk's M2 job: the old qualify_week.mjs over the merged weekly bars) scored by
    the study's own block: BEAT = close <= 0.80 x the 52-week high OR 13-week return <= -20%; SMALL = bottom tercile
    of the trailing-52-week mean weekly dollar volume among the week's qualifiers (the pre-registered fallback);
    HIBETA = 52-week weekly beta vs SPY (OLS on weekly log returns, >= 40 weeks) > 1.2. The primary set BEAT and
    SMALL and HIBETA goes LONG and is held 52 weeks (Friday close to Friday close).

    Source behaviour kept as computed: the study calls ols_beta(ry_all, rx_all) with ry = SPY's and rx = the stock's
    weekly log returns, and ols_beta divides the covariance by the variance of rx - the slope of SPY on the stock,
    not the prereg's 'beta vs SPY' (cov / var(SPY)). A volatile name therefore scores low; the kill's empty HIBETA
    set (2 of 2,587 above 1.2) rests on this computation, and the forward test re-checks exactly that."""
    SLEEVE_ID = "killed_smcap_beta_52w"
    SOURCE = K.source("weekly-phenotypes/code/run_smcap_beta_52w.py", "018e54e2d8506fbcff3fd350920ff95493696918",
                      prereg={"path": K.RESEARCH + "weekly-phenotypes/PRE_REG_SMCAP_BETA_52W.md",
                              "blob": "195c93f3d450a59636a64a2d9a0dd33af609db45"},
                      results={"path": K.RESEARCH + "weekly-phenotypes/RESULTS_SMCAP_BETA_52W.md",
                               "blob": "491382636c1580f77b5da98c202ffd70b939524e"},
                      vendored="desk/vendor/midna_research/run_smcap_beta_52w.py")
    CADENCE = 600
    NEEDS = {"feeds": ["killed_smcap"], "quotes": {"source": "equity"}}
    PARAMS = {"beat": "close <= 0.80 x 52w high or 13w return <= -20%", "small": "bottom tercile of 52w mean $vol",
              "hibeta": "52w weekly beta > 1.2 (>= 40 weeks)", "hold_weeks": 52, "notional": K.CAPITAL / 10,
              "removed_gates": []}
    DIVERGENCES = [
        "the qualifiers are computed after the signal Friday's close, so the entry is the next session's open "
        "(the study's endpoint starts at that Friday's close); the exit is the market-on-close of the Friday 52 "
        "weeks later",
        "the qualifier set is the desk's live M2 job (the research file's m23_inadm flag has no live counterpart)",
    ]

    def plan(self, view, st, tb):
        f = (view.extra or {}).get("killed_smcap")
        if not f or K.signal_day(view.now) is None or st.get("seen") == f.get("rank_date"):
            return []
        if K.add_sessions(f["rank_date"], 1) != tb.today:
            return []
        st["seen"] = f["rank_date"]
        prim = [x for x in f.get("features") or [] if x.get("primary")]
        for x in prim:
            tb.add(x["symbol"], +1, K.CAPITAL / 10, "bsh", tb.today, "open", exit_session(x["friday"]), "close",
                   why=f"BEAT/SMALL/HIBETA week {x['friday']} beta {x['beta']:.2f}", event=x["friday"])
        n = len(f.get("features") or [])
        return [Intent("signal", "SPY", signal_key=f"bsh:{f['rank_date']}",
                       reason=f"week {f.get('friday')}: {n} M2 qualifiers, {sum(1 for x in f['features'] if x['beat'])}"
                              f" beat, {sum(1 for x in f['features'] if x['hibeta'])} high-beta, {len(prim)} primary")]
