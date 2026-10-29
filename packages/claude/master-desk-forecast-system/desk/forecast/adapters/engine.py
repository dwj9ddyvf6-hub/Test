"""The analysis engine FB2 as forecasters (desk/analysis: the frozen spec deep2-engine-secv-1.0.0-final, loaded through
its sha256 pin; bars.features and the reference scorer's functions, imported, never refit or copied).

At each bar i the name's window is its last job.N_BARS (140) bars through i, exactly the window the nightly job reads;
bars.features gives the scorer's features, bars.ineligible the eligibility rule, ref.tier_of the tier. Then
  engine.har    sigma_mean (the per-day volatility forecast of the next 20 sessions); its log variance forecast for
                QLIKE is 0.5 log var_mean (the validation's convention). Target realized_vol_20.
  engine.veto   SEC-V's P(lose5) with OW by the spec's frozen cutoff (ref.ow_frozen: the screen's per-name fallback;
                the same-session OW needs the whole cross-section, which a per-name forecaster does not see).
                A DOWN forecaster: target up_excess_20 with sign -1.
  engine.mom6   momentum 6-1, ln(c[d-21] / c[d-126]) (the screen's mom6_pct is its rank within session x tier; a rank
                IC within a tier cell is the same). Target up_excess_60.
A name outside the spec's universe on d (raw close under $1, dv20 under $100,000, under 60 bars, no volume) abstains:
the frozen spec's own rule, not a floor of the factory. The cache's split-adjusted bars serve as both the adjusted and
the raw series (the replay's input has no separate raw file); that is recorded on every run."""
import math

import numpy as np

from ...analysis import bars as AB
from ...analysis import engine_score_ref as ref
from ...analysis import frozen as FZ
from ...analysis.job import N_BARS
from .. import Forecaster, Laws
from .. import data as D

_SPEC = {}


def spec():
    if not _SPEC:
        s, sha = FZ.load_spec()
        _SPEC.update(spec=s, sha=sha)
    return _SPEC["spec"], _SPEC["sha"]


def _f(fid, targets, bounds, sign=1, note=""):
    return Forecaster(id=fid, version=FZ.SPEC_VERSION, kind="model", owner_module="desk.analysis",
                      family="engine.fb2", targets=targets, laws=Laws(bounded=bounds, warmup=N_BARS, abstains=True,
                                                                     costed="own_name_half_spread"),
                      inputs=("daily bars",), frozen_sha=FZ.SPEC_SHA256, grade="B", sign=sign, note=note,
                      evidence=("docs/research/2026-10-25-engine/DESIGN.md",))


FORECASTERS = (_f("engine.har", ("realized_vol_20",), (0.0, float("inf"))),
               _f("engine.veto", ("up_excess_20",), (0.0, 1.0), sign=-1, note="DOWN: P(lose5)"),
               _f("engine.mom6", ("up_excess_60",), (float("-inf"), float("inf"))))
EXTRA = ("engine.har_logvar", "engine.rv22")       # QLIKE inputs: the HAR log variance forecast and lrv22 persistence


def row(window_bars, session):
    """(har, veto P, mom6, 0.5 log var_mean, lrv22) for one session, or None when the name is not scored"""
    sp, _ = spec()
    f, why = AB.features(window_bars, window_bars, session)
    if why or AB.ineligible(f) is not None:
        return None
    t = ref.tier_of(f["close"], f["dv20"])
    if t is None or f["log_atr_pct"] is None:
        return None
    har = ref.har_forecast(f["lrv1"], f["lrv5"], f["lrv22"], f["log_atr_pct"], t, sp)
    p = ref.veto_probability(ref.ow_frozen(f["lrv22"], t, sp), f["lrv1"], f["lrv5"], f["lrv22"], t, sp)
    m6 = f["mom6"] if f["mom6"] is not None and math.isfinite(f["mom6"]) else np.nan
    return har["sigma_mean"], p, m6, 0.5 * math.log(har["var_mean"]), f["lrv22"]


def compute(a, mkt=None, at=None):
    """{engine.*: per-bar values}; `at` limits the bars computed (the rest stay NaN), for sampled runs"""
    n = len(a["c"])
    out = {k: np.full(n, np.nan) for k in [f.id for f in FORECASTERS] + list(EXTRA)}
    ok = D.guard(a)
    bars = D.to_bars(a)
    pos = np.where(ok)[0]
    for i in (range(n) if at is None else at):
        if not ok[i]:
            continue
        k = int(np.searchsorted(pos, i))
        win = [bars[j] for j in pos[max(0, k - N_BARS + 1):k + 1]]
        r = row(win, str(a["d"][i]))
        if r is None:
            continue
        for key, v in zip(("engine.har", "engine.veto", "engine.mom6", "engine.har_logvar", "engine.rv22"), r):
            out[key][i] = v
    return out
