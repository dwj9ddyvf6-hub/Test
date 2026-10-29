"""Bounded, logged self-calibration of EXECUTION — never of a sleeve's rules.

  buffer_bps   the marketable-limit buffer per asset class. Signal: how often a filled marketable child
               filled on its FIRST parent (the rest needed a reprice). Evidence >= 20 filled children:
               first-try < 85%  -> widen x1.25 (<= 300 bps); first-try > 97% with median slippage under a
               quarter of the buffer -> tighten x0.9 (>= 25 bps). At most one step per calibration.
  replica      the broker replica's allocation across sleeves (the virtual books are untouched: every
               sleeve keeps its full forward test). "equal", or "evidence": a sleeve with >= 20 closed trades
               and >= 30 days earns weight clip(1 + 0.5 x Sharpe, 0.25, 3); every other sleeve weight 1."""
import os
from datetime import datetime, timezone

from ..util import read_json, write_json_atomic

BUFFER_DEFAULT = 100.0
BUFFER_MIN, BUFFER_MAX = 25.0, 300.0
MIN_EVIDENCE_FILLS = 20


def load(root):
    return read_json(os.path.join(root, "state", "calibration.json"), {}) or {}


def calibrate(root, tca, stats, mode="evidence", now=None):
    prev = load(root)
    out = {"buffer_bps": dict(prev.get("buffer_bps") or {}), "replica_weights": {}, "changes": [],
           "replica_mode": mode,
           "at": datetime.fromtimestamp(now or datetime.now(timezone.utc).timestamp(), tz=timezone.utc)
           .isoformat(timespec="seconds")}
    for asset, ft in (tca.get("first_try") or {}).items():
        if (ft.get("filled") or 0) < MIN_EVIDENCE_FILLS or ft.get("ratio") is None:
            continue
        cur = float(out["buffer_bps"].get(asset, BUFFER_DEFAULT))
        slip = ((tca.get("by_asset") or {}).get(asset) or {}).get("median_slip_bps")
        new = cur
        if ft["ratio"] < 0.85 and cur < BUFFER_MAX:
            new = min(BUFFER_MAX, cur * 1.25)
        elif ft["ratio"] > 0.97 and slip is not None and slip < cur / 4 and cur > BUFFER_MIN:
            new = max(BUFFER_MIN, cur * 0.9)
        if abs(new - cur) > 1e-9:
            out["buffer_bps"][asset] = round(new, 2)
            out["changes"].append({"what": "buffer_bps", "asset": asset, "from": cur, "to": round(new, 2),
                                   "first_try": ft["ratio"], "median_slip_bps": slip})
    if mode == "evidence":
        for sid, s in (stats or {}).items():
            if (s.get("trades") or 0) >= 20 and (s.get("days") or 0) >= 30 and s.get("sharpe") is not None:
                out["replica_weights"][sid] = round(max(0.25, min(3.0, 1.0 + 0.5 * float(s["sharpe"]))), 4)
    write_json_atomic(os.path.join(root, "state", "calibration.json"), out)
    return out
