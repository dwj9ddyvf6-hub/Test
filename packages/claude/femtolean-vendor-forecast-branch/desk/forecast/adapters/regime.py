"""Index and volatility-regime forecasters (FACTORY.md §1 adapters/regime.py, phase P2): one value per session, the
same for every name, scored in the search's market lane on SPY's own bars (realized-volatility and return targets),
never as a cross-sectional rank. Inputs are the Cboe files (VIX, VIX3M, SKEW) and SqueezeMetrics' DIX.csv (DIX, GEX).

  vol.gex_pct      the GEX's percentile within its trailing 252 sessions (126 at least), d included. Low GEX ->
                   higher realized vol (PREDICTION_MAP B13; SpotGamma / SqueezeMetrics teardowns): sign -1 on rv.
                   DIX.csv history is REVISED by the vendor: graded non-PIT, a validation fixture only (never
                   committed; access_pit says so on the ledger)
  idx.dix_pct      DIX's trailing-252 percentile -> SPY's 20/60-session return (SqueezeMetrics: high DIX, up)
  vol.vix_ts       VIX / VIX3M (> 1 is backwardation) -> realized vol (EVIDENCE V3; volsignals term structure)
  vol.vix_level    ln VIX -> realized vol (the benchmark every vol forecaster must beat)
  idx.vrp          VIX / 100 - SPY's 20-session realized vol (annualised) -> SPY's 60-session return (EVIDENCE T3)
  idx.skew_pct     SKEW's trailing-252 percentile -> SPY's 20-session return, sign -1 (volsignals Mixon-skew proxy)
A session the input lacks is NaN (the forecaster abstains)."""
import numpy as np
import pandas as pd

from .. import Forecaster, Laws, Ledger
from ._common import market, on

PCT_N, PCT_MIN = 252, 126
INF = float("inf")
RV = ("spy_rv_5", "spy_rv_20", "spy_rvx_20")
RET = ("spy_ret_20", "spy_ret_60")
SPEC = {
    "vol.gex_pct": (-1, (0.0, 1.0), RV, ("PREDICTION_MAP B13", "vendors/squeezemetrics.md", "vendors/spotgamma.md"),
                    {"access_pit": "revised history (non-PIT): SqueezeMetrics DIX.csv, a validation fixture only",
                     "payer": "dealer gamma hedging", "holdable": "options paper only (straddle/condor routing)"}),
    "idx.dix_pct": (1, (0.0, 1.0), RET, ("vendors/squeezemetrics.md",),
                    {"access_pit": "revised history (non-PIT): DIX.csv validation fixture"}),
    "vol.vix_ts": (1, (0.0, INF), RV, ("EVIDENCE V3", "vendors/volsignals.md"), {"access_pit": "Cboe daily close"}),
    "vol.vix_level": (1, (-INF, INF), RV, ("EVIDENCE V2",), {"access_pit": "Cboe daily close"}),
    "idx.vrp": (1, (-INF, INF), RET, ("EVIDENCE T3",), {"access_pit": "Cboe daily close + SPY bars",
                                                        "payer": "the variance risk premium"}),
    "idx.skew_pct": (-1, (0.0, 1.0), ("spy_ret_20",), ("vendors/volsignals.md",), {"access_pit": "Cboe daily close"}),
}
NEEDS = {"vol.gex_pct": "gex", "idx.dix_pct": "dix", "vol.vix_ts": "vix3m", "idx.skew_pct": "skew"}

FORECASTERS = tuple(
    Forecaster(id=k, version="p2-1", kind="score", owner_module="desk.forecast.adapters.regime", family="index",
               targets=t, laws=Laws(bounded=bd, warmup=0, abstains=True, costed="index: SPY 1 bp + 2 bp auction"),
               contexts_declared=("market",), inputs=("Cboe", "SqueezeMetrics DIX.csv") if k in NEEDS else ("Cboe",),
               grade="C" if k in ("vol.gex_pct", "idx.dix_pct") else "B", evidence=ev, sign=sg, ledger=Ledger(**lk))
    for k, (sg, bd, t, ev, lk) in SPEC.items())


def _pct(s):
    """each value's percentile within its trailing PCT_N values (d included); NaN under PCT_MIN"""
    x = s.to_numpy(float)
    out = np.full(len(x), np.nan)
    for i in range(PCT_MIN - 1, len(x)):
        w = x[max(0, i - PCT_N + 1):i + 1]
        out[i] = ((w < x[i]).sum() + 0.5 * ((w == x[i]).sum() - 1) + 0.5) / len(w)
    return pd.Series(out, index=s.index)


def series(m):
    """the session series of every forecaster (index = session); computed once per run"""
    out = {}
    if "gex" in m:
        out["vol.gex_pct"] = _pct(m["gex"])
    if "dix" in m:
        out["idx.dix_pct"] = _pct(m["dix"])
    if "skew" in m:
        out["idx.skew_pct"] = _pct(m["skew"])
    if "vix" in m:
        vx = m["vix"]
        out["vol.vix_level"] = np.log(vx[vx > 0])
        if "vix3m" in m:
            j = pd.concat([vx, m["vix3m"]], axis=1, join="inner")
            j = j[(j.iloc[:, 0] > 0) & (j.iloc[:, 1] > 0)]
            out["vol.vix_ts"] = j.iloc[:, 0] / j.iloc[:, 1]
        hv = m["spyr"].rolling(20).std() * np.sqrt(252)
        j = pd.concat([vx / 100.0, hv], axis=1, join="inner").dropna()
        out["idx.vrp"] = j.iloc[:, 0] - j.iloc[:, 1]
    return out


def compute(a, mkt, m=None, ser=None):
    ser = ser if ser is not None else series(m if m is not None else market(mkt))
    n = len(a["c"])
    out = {}
    for f in FORECASTERS:
        s = ser.get(f.id)
        x = on(a["d"], s) if s is not None else np.full(n, np.nan)
        out[f.id] = np.where(np.isfinite(x), x, np.nan)
    return out
