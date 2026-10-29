"""qr_alphaqcmiqcmfactorpolicyreconstructi -- AlphaQCM (IQCM factor-policy, ZhuZhouFan/AlphaQCM@dffc695f) as the
six-strategy reconstruction trades it (quant-research-critical research/2026-10-08-six-strategy-reconstruction
alphaqcm/train_native.py + export_portfolios.py): the validation-selected frozen pool (corrected-seed2, ten factor
expressions with their pool weights, vendored byte-exact as desk/vendor/quant_research/alphaqcm/frozen-pool.json)
scored on the frozen 100-name US roster (configuration.json).

The score is train_native's frozen causal daily score: each expression evaluated on the split-adjusted daily
open / close / high / low / volume / vwap (float32), masked to the causally eligible names (build_panel's rule: 252
complete prior sessions, prior-20 mean dollar volume >= $10M, close >= $5) and to finite values, normalised by day
(population mean / std, NaN -> 0), weighted and summed in pool order. export_portfolios trades it every 20th
exchange session from 2023-01-03: the top 20% (k = floor(0.2 n), at least 1) of the scored names, equal weight,
decided after the close and executed at the next open, shares left to drift until the next decision.

Named divergences:
  1. arithmetic: numpy float32 kernels (desk/sleeves/quant_research/alphagen_np.py) in place of torch: sums can
     differ in the last float32 bit (max 1.9e-7 over the reconstruction's 215,186 native scores; top-20% selections
     identical on all 48 native target dates -- docs/receipts/parity/qr_alphaqcm.json);
  2. data: the desk's Alpaca split-adjusted daily bars (the reconstruction's provider and adjustment) through the
     hub; validity checks the split-adjusted bar only (the panel also required the all-adjusted bar); a name the
     provider no longer serves (delisted roster names) is ineligible; vwap is NaN without Alpaca (Yahoo fallback);
  3. execution: the rebalance trades at the market from the first pass after the decision session, sized on the live
     ask and the sleeve's NAV, sells first then buys (the reconstruction filled at the official open);
  4. downtime: a decision whose open was missed trades at the next pass;
  5. calendar: the 20-session cadence counts the reconstruction panel's sessions (desk.calendar less the 2018-12-05
     and 2025-01-09 closures it lacks)."""
import json
import os

import numpy as np

from ... import calendar as cal
from ...contract import Sleeve, SleeveConfig
from . import alphagen_np as A
from . import common as C

SID = "qr_alphaqcmiqcmfactorpolicyreconstructi"
VENDOR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "vendor",
                      "quant_research", "alphaqcm")
POOL = json.load(open(os.path.join(VENDOR, "frozen-pool.json")))
CONF = json.load(open(os.path.join(VENDOR, "configuration.json")))
ROSTER = tuple(CONF["symbols"])
ANCHOR = "2023-01-03"                  # export_portfolios: dates >= 2023-01-03, every 20th
EVERY, QUANTILE = 20, 0.2
N_ROWS = 300                           # >= 252 + 21 eligibility rows; the pool's longest window is 50
SOURCE = {"repo": C.SOURCE_REPO, "ref": "main", "commit": C.SOURCE_COMMIT,
          "path": C.SIXAI + "alphaqcm/train_native.py", "export": C.SIXAI + "alphaqcm/export_portfolios.py",
          "pool": "alphaqcm/runs/corrected-seed2/frozen-pool.json sha256 cc1574af (seed-selection.json)",
          "upstream": "ZhuZhouFan/AlphaQCM@dffc695f9ea54e6a54e4dac86ee357be314fead4"}
NODES = [A.parse(e) for e in POOL["expressions"]]


def is_decision(day):
    """every 20th panel session from 2023-01-03 (the decision closes the session)."""
    if day < ANCHOR or not C.is_session(day):
        return False
    return (len(C.sessions_between(ANCHOR, day)) - 1) % EVERY == 0


def last_decision_before(session):
    d = C.prev_session(session)
    while not is_decision(d):
        d = C.prev_session(d)
        if d < ANCHOR:
            return None
    return d


def scores(P):
    """the frozen causal score of the panel's last row: {sym: score} over the eligible names."""
    data = np.stack([P[k] for k in A.FEATURES], axis=1)
    data[~np.isfinite(data)] = np.nan
    data = data.astype(np.float32)
    elig = C.eligibility(P["close"], P["volume"], P["valid"])
    n = data.shape[0]
    s = A.ensemble(NODES, POOL["weights"], data, elig, n - 1, n)[0]
    return {ROSTER[j]: float(s[j]) for j in range(len(ROSTER)) if np.isfinite(s[j])}


def top_weights(sc):
    """export_portfolios: k = max(floor(0.2 n), 1) largest scores (pandas nlargest on the sorted roster), 1/k each."""
    if len(sc) < 10:
        return None
    k = max(int(np.floor(len(sc) * QUANTILE)), 1)
    order = sorted(sc, key=lambda s: (-sc[s], s))
    return {s: 1.0 / k for s in order[:k]}


class AlphaQCM(Sleeve):
    def __init__(self):
        self.engine = None
        self._decided = None
        self.CONFIG = SleeveConfig(
            sleeve_id=SID, family="quant_research", cadence_s=300, universe=ROSTER, capital=1_000_000.0,
            schedule="rth",
            needs={"bars": [{"source": "equity_split", "interval": "1d", "n": N_ROWS + 40, "symbols_for": True}],
                   "quotes": {"source": "equity", "symbols": list(ROSTER)}},
            params={"pool": "corrected-seed2 validation-best (10 factors)", "rebalance_sessions": EVERY,
                    "anchor": ANCHOR, "quantile": QUANTILE, "weighting": "equal", "min_names": 10},
            source=SOURCE, state_schema={"decided": "str", "target": "dict", "weights": "dict", "log": "list"})

    def bind(self, engine):
        self.engine = engine

    def bar_symbols(self, spec, now, book):
        d = last_decision_before(cal._as_date(now).isoformat())
        return [] if d is None or self._decided == d else list(ROSTER)

    def signal(self, view):
        st = dict(view.state or {})
        st.setdefault("log", [])
        self._st = st
        if not cal.is_rth(view.now):
            return []
        d = last_decision_before(view.session)
        if d is None:
            return []
        if st.get("decided") != d:
            frames = {s: f for s, bl in ((view.bars or {}).get("1d") or {}).items()
                      if (f := C.frame(bl)) is not None}
            if not frames or max(f.index.max() for f in frames.values()).date().isoformat() < d:
                st["log"] = (st["log"] + [{"at": view.session, "why": f"bars through {d} not in"}])[-50:]
                return []
            P = C.panel(frames, ROSTER, d, N_ROWS)
            sc = scores(P)
            w = top_weights(sc)
            if w is None:
                st.update(decided=d, target={}, weights={})
                st["log"] = (st["log"] + [{"at": view.session, "decision": d, "why": "fewer than 10 scored"}])[-50:]
                return []
            target = C.target_shares(view, w)
            if target is None:
                st["log"] = (st["log"] + [{"at": view.session, "why": "missing quotes"}])[-50:]
                return []
            st.update(decided=d, target=target, weights=w)
            st["log"] = (st["log"] + [{"at": view.session, "decision": d, "names": sorted(w)}])[-50:]
            self._decided = d
        out, _ = C.rebalance(view, st.get("target") or {}, f"alphaqcm:{d}", f"{SID} top 20% of the frozen pool "
                             f"score at {d}")
        return out

    def update_state(self, view, intents):
        return getattr(self, "_st", None) or dict(view.state or {})


def sleeves():
    return [AlphaQCM()]
