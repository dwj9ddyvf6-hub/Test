"""The survivors and avoid vetoes of EVIDENCE.md / PREDICTION_MAP.md that the P1 adapters do not already carry,
clean-room from their published definitions (the formulas below; thresholds are the sources' published numbers, never
learned here). Per name on the guarded bars; SPY on its own calendar, mapped by session.

  surv.rev1        -r1: yesterday's losers beat its winners (T2/U2; drawdown and fear are context cells)
  mom.r5           r5 = c / c[-5] - 1 (the momentum-dip input, a short reversal on its own)
  mom.r126         c / c[-126] - 1 (S10 cross-sectional momentum)
  mom.r126_21      c[-21] / c[-126] - 1 (momentum 6-1, the FB2 mom6 form)
  mom.resid126     residual momentum (S11): e = r - beta60 * SPY r; sum(e, 126) / (sd(e, 126) sqrt 126)
  mom.volscaled    vol-scaled momentum (S11): r126 / (sd(r, 126) sqrt 126)
  nvi.ema255       NVI / EMA255(NVI) - 1 (S13): NVI moves by the day's return only on a day whose volume is under the
                   previous day's; NVI starts at 1
  veto.panic       panic flush (D8): r1 <= -15% on volume >= 3x the median of the 60 bars before
  veto.spikemem    spike memory (D17): the largest r1 of the last 60 bars >= +40%
  veto.crashed     crashed and volatile (A1, without its $1M floor: tier is a context): r120 <= -50% and the 60-bar
                   annualised volatility >= 100%
  veto.pump100     fresh pump (A2b): r20 >= +100%
  veto.lod         buying far above the day's low (A9/D11): c / l - 1
  veto.cgtph       short-term strength (A4/D4): close above the previous bar's high
  veto.gapup10     an episodic-pivot gap (A12/D14, no earnings filter: the desk has no PIT earnings calendar on DEEP):
                   o / c[-1] - 1 >= +10%
Flags are 1.0 or 0.0 (0.0 while their window is short); the veto forecasters carry sign -1."""
import numpy as np

from .. import Forecaster, Laws, Ledger
from ._common import lag, market, ret, roll, wrap

INF = float("inf")
SPEC = {   # id: (sign, bounds, warmup, targets, evidence, ledger kwargs)
    "surv.rev1": (1, (-INF, 1.0), 1, ("up_excess_5", "up_excess_20"), ("EVIDENCE T2", "PREDICTION_MAP U2"),
                  {"payer": "forced sellers (liquidity provision)", "speed_decay": "1-10 sessions"}),
    "mom.r5": (-1, (-1.0, INF), 5, ("up_excess_5", "up_excess_20"), ("xcheck/composite C4 input",), {}),
    "mom.r126": (1, (-1.0, INF), 126, ("up_excess_20", "up_excess_60"), ("EVIDENCE S10",),
                 {"payer": "underreaction / risk premium", "speed_decay": "3-12 months",
                  "co_losses": "momentum crashes; crowded QQQ/semis"}),
    "mom.r126_21": (1, (-1.0, INF), 126, ("up_excess_20", "up_excess_60"), ("EVIDENCE S10", "FB2 mom6"), {}),
    "mom.resid126": (1, (-INF, INF), 186, ("up_excess_20", "up_excess_60"), ("EVIDENCE S11",), {}),
    "mom.volscaled": (1, (-INF, INF), 127, ("up_excess_20", "up_excess_60"), ("EVIDENCE S11",), {}),
    "nvi.ema255": (1, (-1.0, INF), 255, ("up_excess_20", "up_excess_60"), ("EVIDENCE S13",),
                   {"payer": "quiet-day accumulation (hypothesis)"}),
    "veto.panic": (-1, (0.0, 1.0), 0, ("up_excess_20", "up_excess_60"), ("PREDICTION_MAP D8", "xcheck/predmap"), {}),
    "veto.spikemem": (-1, (0.0, 1.0), 0, ("up_excess_20", "up_excess_60"), ("PREDICTION_MAP D17",), {}),
    "veto.crashed": (-1, (0.0, 1.0), 0, ("up_excess_20", "up_excess_60"), ("EVIDENCE A1",),
                     {"payer": "lottery demand, dilution"}),
    "veto.pump100": (-1, (0.0, 1.0), 0, ("up_excess_20", "up_excess_60"), ("PREDICTION_MAP D2 (A2b)",), {}),
    "veto.lod": (-1, (0.0, INF), 0, ("up_excess_5", "up_excess_20"), ("EVIDENCE A9",), {}),
    "veto.cgtph": (-1, (0.0, 1.0), 0, ("up_excess_5", "up_excess_20"), ("EVIDENCE A4",), {}),
    "veto.gapup10": (-1, (0.0, 1.0), 0, ("up_excess_5", "up_excess_20"), ("EVIDENCE A12",), {}),
}
VETO_LEDGER = {"holdable": "veto only (never a short book, EVIDENCE A16)", "execution_net": "a veto trades nothing",
               "payer": "retail overreaction / distress (EVIDENCE AVOID)"}


def _fc(fid, spec):
    sign, bounds, warm, targets, ev, led = spec
    lk = dict(VETO_LEDGER, **led) if fid.startswith("veto.") else led
    return Forecaster(id=fid, version="p2-1", kind="rule" if bounds == (0.0, 1.0) else "score",
                      owner_module="desk.forecast.adapters.survivors", family=fid.split(".")[0], targets=targets,
                      laws=Laws(bounded=bounds, warmup=warm, abstains=False, costed="own_name_cs_impact"),
                      inputs=("daily bars", "SPY"), grade="B", evidence=ev, sign=sign, ledger=Ledger(**lk))


FORECASTERS = tuple(_fc(k, v) for k, v in SPEC.items())


def _flag(x, n_ok=None):
    return np.where(x, 1.0, 0.0)


def fn(b, m):
    import pandas as pd
    d, o, h, l, c, v = (b["d"], b["o"], b["h"], b["l"], b["c"], b["v"])
    r = ret(c)
    sp = pd.Series(np.asarray(d)).map(m["spyr"]).to_numpy(float)
    out = {"surv.rev1": -r, "mom.r5": ret(c, 5), "mom.r126": ret(c, 126)}
    out["mom.r126_21"] = lag(c, 21) / lag(c, 126) - 1
    with np.errstate(invalid="ignore", divide="ignore"):
        cov = roll(r * sp, 60, "mean") - roll(r, 60, "mean") * roll(sp, 60, "mean")
        beta = cov / roll(sp, 60, "var")
        e = r - beta * sp
        out["mom.resid126"] = roll(e, 126, "sum") / (roll(e, 126, "std") * np.sqrt(126))
        out["mom.volscaled"] = out["mom.r126"] / (roll(r, 126, "std") * np.sqrt(126))
    quiet = np.r_[False, v[1:] < v[:-1]]
    g = np.where(quiet & np.isfinite(r), 1 + r, 1.0)
    nvi = np.cumprod(g)
    from ._common import ema
    out["nvi.ema255"] = nvi / ema(nvi, 255) - 1
    vm1 = lag(roll(v, 60, "median"))
    with np.errstate(invalid="ignore"):
        out["veto.panic"] = _flag((r <= -0.15) & (v >= 3 * vm1))
        out["veto.spikemem"] = _flag(roll(r, 60, "max", minp=1) >= 0.40)
        out["veto.crashed"] = _flag((ret(c, 120) <= -0.5) & (roll(r, 60, "std") * np.sqrt(252) >= 1.0))
        out["veto.pump100"] = _flag(ret(c, 20) >= 1.0)
        out["veto.lod"] = c / l - 1
        out["veto.cgtph"] = _flag(c > lag(h))
        out["veto.gapup10"] = _flag(o / lag(c) - 1 >= 0.10)
    return out


compute = wrap(fn, [f.id for f in FORECASTERS])
