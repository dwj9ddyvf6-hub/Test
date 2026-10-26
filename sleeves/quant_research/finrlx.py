"""qr_finrlxreleasedadaptiverotationrecons -- FinRL-X's released adaptive multi-asset rotation (AI4Finance
FinRL-Trading @4409abe9, AdaptiveRotationConf_v1.2.1.yaml), as the six-strategy reconstruction runs it
(quant-research-critical research/2026-10-08-six-strategy-reconstruction finrlx/finrlx_reconstruction.py,
principal stream `native_cash`).

The upstream engine (17 files, vendored byte-exact under desk/vendor/quant_research/finrlx/, each matching the
reconstruction's upstream-used-source-lock.json blob) decides once a week from completed Friday data: the slow regime
(26-week trend, 13-week drawdown, 3-year VIX z-score; SPY stands in for ^GSPC as in the reconstruction), the 12-week
risk-adjusted strength of the Growth / Real Assets / Defensive groups, robust z-score ranking inside the groups,
the M/K and strong-signal exceptions and the portfolio builder (at most two groups, two names each, residual cash,
fallback SPY / QQQ / IAU / XLU / XLV). Its native weights -- residual cash kept, no normalisation, no overlays --
are the reconstruction's principal allocation, executed at the next session's open and left to drift until the
next Friday decision.

Named divergences:
  1. data: the desk's daily bars with split adjustment (Alpaca adjustment=split through the hub, the reconstruction's
     own provider and adjustment; Yahoo when no Alpaca), and Yahoo's ^VIX closes for CBOE's VIX CSV (the same index);
  2. execution: the rebalance trades at the market from the first pass of the session after the decision Friday,
     sized on the live quote and the sleeve's NAV (cash + holdings at the bid); sells go first and buys follow on the
     next pass once no sell is outstanding (the reconstruction filled the whole rebalance at the official open);
  3. downtime: a decision whose open was missed trades at the next pass (the reconstruction never misses an open);
  4. calendar: pandas_market_calendars is not installed; desk.calendar stands in for its NYSE calendar
     (common.install_calendar_shim). The weekly decision path never calls it (verified in tests)."""
import math

import pandas as pd

from ... import calendar as cal
from ...contract import Intent, Sleeve, SleeveConfig
from . import common as C

SID = "qr_finrlxreleasedadaptiverotationrecons"
GROUPS = {"group_a_growth_tech": ("AAPL", "MSFT", "NVDA", "META", "AMZN", "GOOGL", "TSLA"),
          "group_b_real_assets": ("XOM", "CVX", "COP", "FCX", "BHP", "GLD", "SLV"),
          "group_c_defensive": ("TLT", "IEF", "XLU", "XLV", "IAU", "SHY", "UUP")}
FALLBACK = ("SPY", "QQQ", "IAU", "XLU", "XLV")
TRADABLES = tuple(sorted(set(s for g in GROUPS.values() for s in g) | set(FALLBACK) | {"QQQ"}))
HISTORY_START = "2016-01-01"           # the reconstruction's genuine 2016-onward history
N_BARS = 2900
SOURCE = {"repo": C.SOURCE_REPO, "ref": "main", "commit": C.SOURCE_COMMIT,
          "path": C.SIXAI + "finrlx/finrlx_reconstruction.py",
          "upstream": "AI4Finance-Foundation/FinRL-Trading@4409abe925c904e570be78ebfb5e77ac3491dff8"}

_ENGINE = {}


def engine_mod():
    """the vendored upstream engine, its config loader and the v1.2.1 config (loaded once)."""
    if not _ENGINE:
        C.install_calendar_shim()
        from ...vendor.quant_research.finrlx.src.strategies.adaptive_rotation import config_loader as cl
        from ...vendor.quant_research.finrlx.src.strategies.adaptive_rotation import adaptive_rotation_engine as ae
        import os
        from ...vendor.quant_research import finrlx as pkg
        path = os.path.join(os.path.dirname(pkg.__file__), "src", "strategies", "AdaptiveRotationConf_v1.2.1.yaml")
        _ENGINE.update(load_config=cl.load_config, Engine=ae.AdaptiveRotationEngine, config=cl.load_config(path))
    return _ENGINE


class _DailyAdapter:
    """the released engine's point-in-time daily-data interface (finrlx_reconstruction.DailyAdapter)."""

    def __init__(self, daily):
        self.daily = daily

    def get_daily_data_as_of(self, as_of_date, symbols=None):
        return {s: v.loc[:as_of_date] for s, v in self.daily.items() if symbols is None or s in symbols}


def native_weights(closes, friday):
    """the native weekly allocation at Friday `friday` from daily closes {sym: Series} (tradables + ^VIX), each
    holding data through that Friday: generate_signals' weekly branch (native_cash stream)."""
    E = engine_mod()
    config = E["config"]
    friday = pd.Timestamp(friday)
    daily = {s: v.loc[:friday].dropna() for s, v in closes.items() if s != "^VIX"}
    daily["^GSPC"] = daily["SPY"].copy()               # the reconstruction's explicit SPY proxy for SPX
    daily["^VIX"] = closes["^VIX"].loc[:friday]
    weekly = {s: v.resample("W-FRI").last().dropna() for s, v in daily.items()}
    import contextlib
    import io
    eng = E["Engine"](config=config, data_preprocessor=_DailyAdapter(daily))
    with contextlib.redirect_stdout(io.StringIO()):
        result, audit = eng.run(weekly, friday, current_positions={}, mode="backtest")
    tradables = sorted((set(config.get_required_symbols()) | set(config.portfolio.fallback.symbols))
                       - {"^VIX", "^GSPC"})
    w = {s: float(result.weights.get(s, 0.0)) for s in tradables}
    return w, audit


class FinRLX(Sleeve):
    def __init__(self):
        self.engine = None
        self._decided = None
        self.CONFIG = SleeveConfig(
            sleeve_id=SID, family="quant_research", cadence_s=300, universe=TRADABLES, capital=1_000_000.0,
            schedule="rth",
            needs={"bars": [{"source": "equity_split", "interval": "1d", "n": N_BARS, "symbols_for": True},
                            {"source": "yahoo", "interval": "1d", "n": N_BARS, "symbols_for": True, "key": "vix"}],
                   "quotes": {"source": "equity", "symbols": list(TRADABLES)}},
            params={"config": "AdaptiveRotationConf_v1.2.1.yaml (unchanged)", "stream": "native_cash",
                    "decision": "completed Friday close", "execution": "next session open, drift until next decision",
                    "regime_index": "SPY proxy for ^GSPC; ^VIX"},
            source=SOURCE, state_schema={"decided": "str", "target": "dict", "weights": "dict", "log": "list"})

    def bind(self, engine):
        self.engine = engine

    def bar_symbols(self, spec, now, book):
        d = C.last_friday_before(cal._as_date(now).isoformat())
        if d is None or self._decided == d.isoformat():
            return []
        return ["^VIX"] if spec.get("key") == "vix" else list(TRADABLES)

    def signal(self, view):
        st = dict(view.state or {})
        st.setdefault("log", [])
        self._st = st
        if not cal.is_rth(view.now):
            return []
        fri = C.last_friday_before(view.session)
        if fri is None:
            return []
        fri_s = fri.isoformat()
        if st.get("decided") != fri_s:
            closes = {}
            for s, bl in ((view.bars or {}).get("1d") or {}).items():
                f = C.frame(bl)
                if f is not None:
                    closes[s] = f.c
            vix = C.frame(((view.extra or {}).get("bars_vix") or {}).get("^VIX"))
            missing = [s for s in TRADABLES if s not in closes or closes[s].index.max() < pd.Timestamp(fri)]
            if missing or vix is None or vix.index.max() < pd.Timestamp(fri):
                st["log"] = (st["log"] + [{"at": view.session, "why": f"waiting for bars {missing[:4]}"}])[-50:]
                return []
            closes = {s: v.loc[HISTORY_START:] for s, v in closes.items()}
            closes["^VIX"] = vix.c.loc[HISTORY_START:]
            w, audit = native_weights(closes, fri_s)
            total = C.nav(view)
            target = {}
            for s, x in w.items():
                q = (view.quotes or {}).get(s) or {}
                px = q.get("ask") or q.get("last")
                if x > 0 and not px:
                    st["log"] = (st["log"] + [{"at": view.session, "why": f"no quote for {s}"}])[-50:]
                    return []
                target[s] = x * total / float(px) if x > 0 else 0.0
            st.update(decided=fri_s, target=target, weights=w)
            st["log"] = (st["log"] + [{"at": view.session, "friday": fri_s, "weights": {k: v for k, v in w.items()
                                                                                       if v}}])[-50:]
            self._decided = fri_s
        out, _ = C.rebalance(view, st.get("target") or {}, f"finrlx:{fri_s}",
                             f"{SID} native weekly allocation of {fri_s}")
        return out

    def update_state(self, view, intents):
        return getattr(self, "_st", None) or dict(view.state or {})


def sleeves():
    return [FinRLX()]
