#!/usr/bin/env python3
"""Build the FE07 lead-lag run record from the DEEP panel.

Runs forecast/leadlag.py's frozen estimation over every ordered
pair of its proxy universe on the panel's freshest alignment and
writes site/leadlag-record.json: the frozen pair table the
registry's FE07 decision rule requires (pair selection, beta,
stability, R2 and clock alignment, frozen per pair in advance).

Usage: python3 build_leadlag_record.py
"""

import json
import os
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(os.path.dirname(HERE))
PANEL_PATH = os.path.join(WS, "morgue", "data_cache", "deep_bars.json")
OUT_PATH = os.path.join(HERE, "leadlag-record.json")

sys.path.insert(0, os.path.join(WS, "terminal-lineup", "forecast"))
sys.path.insert(0, HERE)
import leadlag  # noqa: E402
from deep_panel_reader import DeepPanelReader  # noqa: E402


def main():
    reader = DeepPanelReader(PANEL_PATH)
    lengths = reader.lengths()
    present, missing = [], []
    series = {}
    for sym in leadlag.PROXIES:
        if sym in lengths and lengths[sym] >= leadlag.MIN_ALIGNED + 2:
            rows = reader[sym]
            dates = [r[0] for r in rows]
            closes = [float(r[4]) for r in rows]
            series[sym] = leadlag.log_returns(dates, closes)
            present.append(sym)
        else:
            missing.append(sym)
    pairs = []
    for leader in present:
        for follower in present:
            if leader == follower:
                continue
            est = leadlag.estimate_edge(series[leader], series[follower])
            if est is None:
                continue
            est = {"leader": leader, "follower": follower, **est}
            pairs.append(est)
    selected = [p for p in pairs if p["selected"]]
    selected.sort(key=lambda p: -abs(p["edge"]))
    record = {
        "record": "FE07 cross-asset lead-lag edge estimation, frozen run",
        "built_at_utc": datetime.now(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"),
        "panel_fingerprint": reader.fingerprint,
        "module": "forecast/leadlag.py",
        "frozen_on": leadlag.FROZEN_ON,
        "window_sessions": leadlag.WINDOW,
        "min_aligned_sessions": leadlag.MIN_ALIGNED,
        "r2_floor": leadlag.R2_FLOOR,
        "r2_full": leadlag.R2_FULL,
        "proxies_present": present,
        "proxies_missing_from_panel": missing,
        "pairs_estimated": len(pairs),
        "pairs_selected": len(selected),
        "selected_pairs": selected,
        "note": ("Estimation frozen per pair in advance, in the "
                 "registered form (lag beta times stability times "
                 "the R2 soft threshold). No engine consumes these "
                 "edges yet; wiring is a separate step."),
    }
    tmp = OUT_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=1, sort_keys=True)
        fh.write("\n")
    os.replace(tmp, OUT_PATH)
    print(f"leadlag record: {len(pairs)} pairs estimated, "
          f"{len(selected)} selected, missing proxies {missing}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
