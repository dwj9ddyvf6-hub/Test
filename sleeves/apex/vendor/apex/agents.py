"""The source desk's live runtime rules: the execution mapping (desk/agents/portfolio.py alpaca_weights:
exposure L onto QQQ + TQQQ, above 1x QQQ + 3 x TQQQ = L on 100% of NAV, or QQQ + the idle symbol at or
below 1x) and the plan for the next close (desk/agents/risk.py planned_position: the rebalance band).

Source: cursor2 main @ca8ac1f650670e1d1a8344d21cff8dd9f0ba4448. Each block after a `# >>> excerpt` marker is the exact text of that
source line range (the marker carries its sha256; tests/test_apex.py re-hashes every block)."""
from __future__ import annotations

import math


# >>> excerpt desk/agents/portfolio.py lines 14-21 blob 717834bab7f8f87ade1c7abe73a56c3a0a8e2e40 sha256 43bae46e1bff6de2b8c035ee15785c2bdfc9b7ca2ccb8c164198a6ab368e3244
def alpaca_weights(L: float, idle_symbol: str = "BIL") -> dict[str, float]:
    L = max(0.0, min(L, 3.0))
    if L <= 1.0:
        w = {"QQQ": L, idle_symbol: 1.0 - L}
    else:
        tq = (L - 1.0) / 2.0
        w = {"QQQ": 1.0 - tq, "TQQQ": tq}
    return {k: round(v, 6) for k, v in w.items() if v > 1e-9}


# >>> excerpt desk/agents/risk.py lines 21-25 blob ae2332cc456a1a0244da212dd531808e0db28015 sha256 978ea448bffc295eae171e71d40e94829cb0aac831ec0ec94f241629fbfefbfe
def planned_position(target: float, current: float, band: float) -> float:
    target = max(float(target), 0.0) if math.isfinite(target) else 0.0
    if (target == 0.0 and current != 0.0) or abs(target - current) >= band - 1e-12:
        return target
    return current
