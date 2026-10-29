"""How we know the desk AI is good, not just fluent (study I, 3.8). A skeleton the odds and record builds fill in:

replay(edition, calls)      the tools on a frozen edition, offline, so an answer can be re-derived exactly
corruption_test(...)        change only what is dated after the snapshot; a tool answer that moves is reading the future
gate_cut_rate(results)      the share of figures the grounding gate had to cut (target: zero)
brier(probs, outcomes)      calibration of stated probabilities once setup_odds lands; no_data until then
"""
import copy
import json

from . import run
from .source import Source


def replay(edition, calls):
    """[(tool, args)] on a frozen edition -> their envelopes (data_age is measured from the edition's own time)"""
    from datetime import datetime
    src = Source(edition=edition, offline=True)
    try:
        t = datetime.fromisoformat(edition.get("generated_at")).timestamp()
    except (TypeError, ValueError):
        t = None
    return [run(name, args, source=src, now=t) for name, args in calls]


def _strip(env):
    return json.dumps({k: env[k] for k in ("status", "reason", "result")}, sort_keys=True, default=str)


def corruption_test(edition, calls):
    """calls opened after the snapshot's market session are future facts: corrupt them and every answer must hold"""
    as_of = ((edition.get("market") or {}).get("as_of")) or ""
    bad = copy.deepcopy(edition)
    for c in bad.get("calls") or []:
        if str(c.get("opened") or "")[:10] > as_of:
            c["outcome_r"], c["status"] = 99.0, "closed"
    a, b = replay(edition, calls), replay(bad, calls)
    moved = [x["tool"] for x, y in zip(a, b) if _strip(x) != _strip(y)]
    return {"ok": not moved, "moved": moved, "future_rows": sum(1 for c in bad.get("calls") or []
                                                                 if str(c.get("opened") or "")[:10] > as_of)}


def gate_cut_rate(results):
    figs = sum(r.get("figures", 0) for r in results)
    cut = sum(len(c["numbers"]) for r in results for c in r.get("cut", []))
    return {"figures": figs, "cut": cut, "rate": round(cut / figs, 4) if figs else None}


def brier(probs, outcomes):
    if not probs or len(probs) != len(outcomes):
        return {"status": "no_data", "reason": "no matured stated probabilities yet (setup_odds not live)"}
    return {"status": "ok", "n": len(probs),
            "brier": round(sum((p - o) ** 2 for p, o in zip(probs, outcomes)) / len(probs), 4)}
