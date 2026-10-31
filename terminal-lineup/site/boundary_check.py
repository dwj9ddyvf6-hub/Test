#!/usr/bin/env python3
"""Boundary map check for multiplicative scorers (DEEP-PASS 3.2.9).

The pre publication check: any new multiplicative scorer ships with
its corner map reviewed, and any scorer mirror proves parity over
these sweeps, never over one synthetic vector. This run maps
engine_adaptations.fe17_centre, the multiplicative centre adopted for
Engine 12: (0.60 * implied + 0.40 * historical) multiplied by a
dispersion factor and by timing quality, including its clip region
(dispersion clipped at plus and minus 2) and its refusal branch
(timing quality 0 is outside (0, 1] and is refused, not floored).

Usage: python3 boundary_check.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "forecast"))
sys.path.insert(0, HERE)
from diagnostics_patterns import boundary_sweep  # noqa: E402
from engine_adaptations import fe17_centre  # noqa: E402


def scorer(point):
    try:
        out = fe17_centre(point["implied"], point["historical"],
                          point["dispersion"], point["timing"])
    except Exception:
        return None
    if not isinstance(out, dict) or out.get("centre_pct") is None:
        return None
    return out["centre_pct"]


def main():
    baseline = {"implied": 8.0, "historical": 7.0,
                "dispersion": 0.0, "timing": 1.0}
    ranges = {"implied": (0.5, 20.0), "historical": (0.5, 20.0),
              "dispersion": (-3.0, 3.0), "timing": (0.0, 1.0)}
    result = boundary_sweep(scorer, baseline, ranges)
    print(f"status: {result['status']}")
    print(f"baseline centre: {result['baseline']}")
    print(f"cases: {len(result['cases'])} "
          f"(one feature, pairwise and joint corners)")
    print(f"score range over corners: {result['score_min']} to "
          f"{result['score_max']}")
    print(f"abstained cases: {result['abstained_cases']}")
    zero = [c for c in result["cases"]
            if c["point"].get("timing") == 0.0]
    print(f"timing zero branch (timing must lie in (0, 1], so the "
          f"scorer refuses): {len(zero)} cases, all refused: "
          f"{all(c['score'] is None for c in zero)}")
    clip = [c for c in result["cases"]
            if abs(c["point"].get("dispersion", 0)) == 3.0]
    print(f"dispersion clip region (|z| = 3, clipped at 2): "
          f"{len(clip)} cases reviewed")
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
