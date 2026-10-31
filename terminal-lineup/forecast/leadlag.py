"""FE07 cross-asset lead-lag edge estimation (RC-30 cure, 2026-10-30).

The registry carried FE07's route "pair selection, beta, stability
and R2 estimation with clock alignment" as absent: the source
package contains none of it. This module builds and freezes that
estimation, exactly in the registered form: a single estimated
edge per ordered pair,

    edge = lag_beta * stability * soft_threshold(r2)

where lag_beta is the slope of the follower's daily log return on
the leader's prior session log return, stability is the agreement
of the two split-half betas (1 minus their relative disagreement,
floored at 0), and the soft threshold zeroes edges whose R2 is at
or below R2_FLOOR and reaches 1 at R2_FULL:

    soft_threshold(r2) = clip((r2 - 0.005) / (0.03 - 0.005), 0, 1)

Frozen constants (frozen 2026-10-30, before any consumption):
- universe: the cross-asset proxy set named in PROXIES (index,
  sector and asset proxies that the DEEP panel actually carries;
  a proxy the panel does not carry is named in the run record,
  never silently dropped);
- window: the trailing 500 aligned sessions ending on the
  panel's freshest session; a pair needs at least 250 aligned
  sessions or it is not estimated;
- clock alignment: sessions are aligned on the leader and
  follower sharing the same session date; the lag is exactly
  one shared session;
- pair selection: an ordered pair is selected when its edge is
  nonzero under the frozen form; selected pairs are frozen in
  the run record (site record beside this module's consumer)
  before any engine consumes them.

Estimation only: no engine score changes because of this module.
Wiring an edge into a forecast is a separate step.
"""

import math

PROXIES = ("SPY", "QQQ", "IWM", "DIA", "XLF", "XLK", "XLE",
           "XLV", "XLI", "XLP", "XLY", "XLB", "XLRE", "XLC",
           "XLU", "GLD", "SLV", "USO", "TLT", "HYG", "EEM",
           "EFA", "FXI", "VNQ", "IBIT")
WINDOW = 500
MIN_ALIGNED = 250
R2_FLOOR = 0.005
R2_FULL = 0.03
FROZEN_ON = "2026-10-30"


def soft_threshold(r2):
    if r2 is None:
        return 0.0
    return max(0.0, min(1.0, (r2 - R2_FLOOR) / (R2_FULL - R2_FLOOR)))


def _beta_r2(xs, ys):
    n = len(xs)
    if n < 3:
        return None, None
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx <= 0:
        return None, None
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    syy = sum((y - my) ** 2 for y in ys)
    beta = sxy / sxx
    r2 = (sxy * sxy) / (sxx * syy) if syy > 0 else 0.0
    return beta, r2


def estimate_edge(leader_returns_by_date, follower_returns_by_date):
    """One ordered pair's frozen edge estimate, or None when the
    aligned record is too short. Inputs are {date: log return}
    for sessions after each series' first."""
    shared = sorted(set(leader_returns_by_date)
                    & set(follower_returns_by_date))
    # lag one shared session: leader return on shared[i] pairs
    # with the follower return on shared[i + 1]
    pairs = [(leader_returns_by_date[shared[i]],
              follower_returns_by_date[shared[i + 1]])
             for i in range(len(shared) - 1)]
    pairs = pairs[-WINDOW:]
    if len(pairs) < MIN_ALIGNED:
        return None
    xs = [p[0] for p in pairs]
    ys = [p[1] for p in pairs]
    beta, r2 = _beta_r2(xs, ys)
    if beta is None:
        return None
    half = len(pairs) // 2
    b1, _ = _beta_r2(xs[:half], ys[:half])
    b2, _ = _beta_r2(xs[half:], ys[half:])
    if b1 is None or b2 is None:
        stability = 0.0
    else:
        scale = max(abs(b1), abs(b2), 1e-9)
        stability = max(0.0, 1.0 - abs(b1 - b2) / scale) \
            if (b1 > 0) == (b2 > 0) else 0.0
    edge = beta * stability * soft_threshold(r2)
    return {
        "lag_beta": round(beta, 6),
        "r2": round(r2, 6),
        "stability": round(stability, 4),
        "soft_threshold": round(soft_threshold(r2), 4),
        "edge": round(edge, 6),
        "aligned_sessions": len(pairs),
        "selected": edge != 0.0,
    }


def log_returns(dates, closes):
    out = {}
    for i in range(1, len(dates)):
        if closes[i] > 0 and closes[i - 1] > 0:
            out[dates[i]] = math.log(closes[i] / closes[i - 1])
    return out
