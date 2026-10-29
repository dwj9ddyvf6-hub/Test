"""V-vibe-3 - factor bench buckets from a per-date IC series.

alive      mean IC > 0.02, share of positive dates >= 0.55, t > 2
reversed   the mirror: mean IC < -0.02, share of positive dates <= 0.45, t < -2 (the sign is the signal, flipped)
dead       tested, neither
untested   under MIN_ICS dates (30): no bucket, never a verdict"""
import numpy as np

from .stats import t_plain

MIN_ICS = 30
MEAN_MIN = 0.02
POS_ALIVE = 0.55
POS_REVERSED = 0.45
T_MIN = 2.0


def bench_bucket(ic_by_date):
    s = np.asarray(ic_by_date, float)
    s = s[np.isfinite(s)]
    if len(s) < MIN_ICS:
        return {"status": "no_data", "bucket": "untested", "n": int(len(s)),
                "reason": f"{len(s)} per-date ICs; need {MIN_ICS}"}
    st = t_plain(s)
    pos = float((s > 0).mean())
    m, t = st["mean"], st["t"]
    if t is not None and m > MEAN_MIN and pos >= POS_ALIVE and t > T_MIN:
        b = "alive"
    elif t is not None and m < -MEAN_MIN and pos <= POS_REVERSED and t < -T_MIN:
        b = "reversed"
    else:
        b = "dead"
    return {"status": "ok", "bucket": b, "n": int(len(s)), "mean": round(m, 4), "pos_ratio": round(pos, 3),
            "t": None if t is None else round(t, 3)}
