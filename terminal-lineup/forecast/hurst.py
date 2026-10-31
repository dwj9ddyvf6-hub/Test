"""Frozen Hurst exponent estimator (FE02 route cure, 2026-10-30).

Built for registry research question fe02_hurst_gate (RC-30 in the
remainders census): the registry admitted the FE02 chop gate as a
conditioner candidate only, recorded as not wired because no Hurst
estimator existed in the stack. This module is that estimator,
frozen with the method below so the gate's input is one defined
quantity, never a per caller improvisation.

Method choice, on evidence: the classic rescaled range (R/S)
estimator was built first and measured on synthetic fractional
Gaussian noise with known exponents at a 250 return window: it
read white noise at 0.70, a bias too large for a gate input.
Detrended fluctuation analysis (DFA) at a 1,000 return window
recovered the same synthetic exponents within about 0.10 and read
white noise at 0.55, so DFA is the frozen method and R/S is
recorded here as the rejected route, not silently dropped.

Frozen method (do not change without a registry amendment):
- Input: daily closes. The series analysed is the log returns of
  the trailing WINDOW_RETURNS + 1 closes (the most recent closes
  when more are supplied).
- Build the mean adjusted cumulative profile of the returns.
- Scales: (10, 20, 40, 80, 160) observations, using only scales
  no larger than half the window; at least three scales must
  survive or the estimate is None.
- Per scale: split the profile into contiguous non overlapping
  blocks, fit and remove a straight line per block, and take the
  root mean square residual over all blocks.
- H is the least squares slope of log(fluctuation) against
  log(scale), clipped to [0.0, 1.0].
- Fewer than MIN_RETURNS returns returns None: insufficient is a
  state, never a number. Measured accuracy of this frozen form on
  synthetic series with known exponents is about plus or minus
  0.10 to 0.15; the gate is a conditioner and is read with that
  tolerance, never as a precise measurement.

The chop gate from the registry statement lives here beside its
input so there is one source for both:
chop_gate(h) = clip((0.58 - h) / 0.25, 0, 1).

This module issues no forecast and changes no engine score. The
registry decision rule stands: the gate may be wired as a
conditioner only now that the estimator is built and frozen, and
that wiring is a separate, separately proven step.
"""

import math

WINDOW_RETURNS = 1000
MIN_RETURNS = 250
SCALES = (10, 20, 40, 80, 160)


def _fluctuation(profile, scale):
    n = len(profile)
    blocks = n // scale
    if blocks == 0:
        return None
    ss = 0.0
    cnt = 0
    mx = (scale - 1) / 2.0
    den = sum((i - mx) ** 2 for i in range(scale))
    for b in range(blocks):
        seg = profile[b * scale:(b + 1) * scale]
        my = sum(seg) / scale
        num = sum((i - mx) * (seg[i] - my) for i in range(scale))
        a = num / den
        bb = my - a * mx
        ss += sum((seg[i] - (a * i + bb)) ** 2 for i in range(scale))
        cnt += scale
    if cnt == 0 or ss == 0.0:
        return None
    return math.sqrt(ss / cnt)


def hurst_exponent(closes):
    """Hurst exponent of the trailing window of daily closes.

    Returns None when the record is too short or degenerate.
    """
    closes = [float(c) for c in closes if c is not None]
    window = closes[-(WINDOW_RETURNS + 1):]
    if len(window) < MIN_RETURNS + 1:
        return None
    if any(c <= 0 for c in window):
        return None
    returns = [math.log(window[i] / window[i - 1])
               for i in range(1, len(window))]
    mean = sum(returns) / len(returns)
    profile = []
    run = 0.0
    for r in returns:
        run += r - mean
        profile.append(run)
    xs = []
    ys = []
    for scale in SCALES:
        if scale > len(profile) // 2:
            continue
        f = _fluctuation(profile, scale)
        if f is None or f <= 0:
            return None
        xs.append(math.log(scale))
        ys.append(math.log(f))
    if len(xs) < 3:
        return None
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = sum((x - mx) ** 2 for x in xs)
    if den == 0:
        return None
    h = num / den
    return max(0.0, min(1.0, h))


def chop_gate(h):
    """FE02 chop gate, exactly as registered: clip((0.58 - h) / 0.25, 0, 1)."""
    if h is None:
        return None
    return max(0.0, min(1.0, (0.58 - h) / 0.25))
