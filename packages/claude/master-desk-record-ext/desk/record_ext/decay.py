"""V-vibe-2 - the decay state machine for a registered forecaster (Vibe-Trading strategy_store/decay.py thresholds).

A scan scores the last WINDOW (60) per-date ICs against the discovery IC:
  ic_ratio  mean(window IC) / discovery IC          healthy 0.7   warning 0.5   decayed 0.3
  ir        mean / sd of the window IC, annualised  healthy 1.0   warning 0.5   decayed 0.1
  ic_pos    share of window dates with IC > 0       healthy 0.55  warning 0.45  decayed 0.35
  sharpe    (optional, supplied by the caller)      healthy 1.0   warning 0.5   decayed 0.0
A metric below its healthy bar is "ok" while it holds the warning bar, a "warning" under the warning bar and
"critical" under the decayed bar. The ir annualisation (sqrt 252) is this port's reading: the teardown names the
thresholds, not the scale. A scan is a warning scan when any metric is at warning or critical, a critical scan when at
least half of the metrics are critical, and otherwise a healthy scan.

Transitions (scan counts):  active -> monitoring after 3 consecutive warning scans;  monitoring -> decayed after 2
consecutive warning scans;  monitoring -> active after 2 consecutive healthy scans;  decayed -> disabled after 3
consecutive critical scans. Decayed and disabled are sticky: the teardown names no way back, so a return is an operator
row, never a scan. A state is a row in an append-only log; no forecaster is ever deleted or rewritten by this module."""
import json
import math
import os

import numpy as np

from .stats import no_data

WINDOW = 60
STEP = 20
IR_SCALE = math.sqrt(252)
BARS = {"ic_ratio": (0.7, 0.5, 0.3), "ir": (1.0, 0.5, 0.1), "ic_pos": (0.55, 0.45, 0.35), "sharpe": (1.0, 0.5, 0.0)}
WARNINGS_FOR_MONITORING = 3
WARNINGS_FOR_DECAYED = 2
CRITICAL_FOR_DISABLED = 3
HEALTHY_TO_RECOVER = 2
STATES = ("active", "monitoring", "decayed", "disabled")


def level(metric, value):
    healthy, warn, dead = BARS[metric]
    if value >= healthy:
        return "healthy"
    if value >= warn:
        return "ok"
    if value >= dead:
        return "warning"
    return "critical"


def scan_metrics(window_ic, discovery_ic, sharpe=None):
    """-> {metrics, levels, warning, critical}; the discovery IC must be positive (a forecaster with none has no ratio)"""
    w = np.asarray(window_ic, float)
    w = w[np.isfinite(w)]
    mean = float(w.mean())
    sd = float(w.std(ddof=1)) if len(w) > 1 else 0.0
    m = {"ic_ratio": mean / discovery_ic,
         "ir": (mean / sd * IR_SCALE) if sd > 0 else (math.inf if mean > 0 else -math.inf if mean < 0 else 0.0),
         "ic_pos": float((w > 0).mean())}
    if sharpe is not None:
        m["sharpe"] = float(sharpe)
    lv = {k: level(k, v) for k, v in m.items()}
    n = len(lv)
    crit = sum(1 for v in lv.values() if v == "critical")
    return {"metrics": {k: (round(v, 4) if math.isfinite(v) else None) for k, v in m.items()}, "levels": lv,
            "warning": any(v in ("warning", "critical") for v in lv.values()), "critical": crit * 2 >= n}


def step(state, warning, critical, counters=None):
    """one scan through the machine -> (state, counters)"""
    c = dict(counters or {"warn": 0, "healthy": 0, "crit": 0})
    if state == "active":
        c["warn"] = c["warn"] + 1 if warning else 0
        if c["warn"] >= WARNINGS_FOR_MONITORING:
            return "monitoring", {"warn": 0, "healthy": 0, "crit": 0}
    elif state == "monitoring":
        if warning:
            c["warn"], c["healthy"] = c["warn"] + 1, 0
            if c["warn"] >= WARNINGS_FOR_DECAYED:
                return "decayed", {"warn": 0, "healthy": 0, "crit": 0}
        else:
            c["healthy"], c["warn"] = c["healthy"] + 1, 0
            if c["healthy"] >= HEALTHY_TO_RECOVER:
                return "active", {"warn": 0, "healthy": 0, "crit": 0}
    elif state == "decayed":
        c["crit"] = c["crit"] + 1 if critical else 0
        if c["crit"] >= CRITICAL_FOR_DISABLED:
            return "disabled", {"warn": 0, "healthy": 0, "crit": 0}
    return state, c


def decay_state(ic_series, discovery_ic, window=WINDOW, stride=STEP, state="active", sharpe=None):
    """scan the series every `stride` dates once `window` dates exist -> {status, state, scans, history}"""
    s = np.asarray(ic_series, float)
    if not (discovery_ic and discovery_ic > 0):
        return no_data("the discovery IC is not positive; there is no baseline to decay from", state=state)
    if len(s) < window:
        return no_data(f"{len(s)} per-date ICs; need {window} for the first scan", state=state)
    hist, counters = [], None
    for end in range(window, len(s) + 1, stride):
        sc = scan_metrics(s[end - window:end], discovery_ic, sharpe)
        state, counters = step(state, sc["warning"], sc["critical"], counters)
        hist.append({"scan": len(hist) + 1, "end": end, "metrics": sc["metrics"], "warning": sc["warning"],
                     "critical": sc["critical"], "state": state})
    return {"status": "ok", "state": state, "scans": len(hist), "history": hist}


def state_rows(forecaster, result, as_of):
    """the rows to append to the registry log: one per scan, stamped with the forecaster and the date"""
    return [{"forecaster": forecaster, "as_of": str(as_of), "scan": h["scan"], "state": h["state"],
             "metrics": h["metrics"]} for h in result.get("history", [])]


def append_state_rows(path, rows):
    """append-only: rows are added, never rewritten; returns the count written"""
    if not rows:
        return 0
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    return len(rows)
