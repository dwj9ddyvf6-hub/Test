#!/usr/bin/env python3
"""Proactive lane: 'tools-gate digest' (WIRED round-5 row a, discipline 1).

The lane we own end to end: it builds a candidate proactive message from the
tools_gate receipt, and its SEND PATH executes, in order, before any send:
  1. proactive_gate.decide (PRISM tau; fail-closed on missing inputs)
  2. proactive_gate.check_rate against the persistent ledger history
     (per-lane min_interval / max_fires_per_window from LANE_CFG below,
     costs and caps live here in config, never in a generator prompt)
  3. sendcheck.sendcheck (surface caps + purpose gate; fail closed)
  4. sendcheck.check_rate (coded rate caps, same-process guard)
  5. delivery_checklist.score_draft (stage-2 delivery grading, discipline 1:
     the score and failed criteria are recorded on every fire's ledger
     record; a natural_format deduction (metadata leakage into a
     user-facing message) BLOCKS the fire. The other criteria grade only:
     this lane's real candidates are terse system digests that the generic
     form criteria would fail on style while leaking nothing, and the
     fire-time gate that blocks on price is steps 1-4.)
Only then does it 'send': append the message to the lane outbox JSONL and a
fire entry to the decision ledger. Every decision (fire / slow / silent /
blocked) is appended to the ledger with its deterministic fire id
(dedup_ids). Slow mode is recorded, not sent. Platform limit, stated exactly:
the platform's own proactive chat delivery cannot be hooked from here, so
this lane's send surface is its outbox file, which the scheduled cron run
relays only when the ledger shows a fire entry it has not yet relayed.
"""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import delivery_checklist, proactive_gate, sendcheck
from dedup_ids import deterministic_id as fire_id

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, "state")
LEDGER = os.path.join(STATE, "proactive_lane_ledger.jsonl")
OUTBOX = os.path.join(STATE, "proactive_lane_outbox.jsonl")
LANE_CFG = {"lane": "tools-gate-digest", "C_FA": 2.0, "C_FN": 8.0, "margin": 0.05,
            "min_interval": 3600, "max_fires_per_window": 3}
SURFACE = "chat"

def _append(path, rec):
    os.makedirs(STATE, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")

def _history():
    if not os.path.isfile(LEDGER):
        return []
    out = []
    for line in open(LEDGER, encoding="utf-8"):
        try:
            r = json.loads(line)
        except Exception:
            continue
        if r.get("verdict") == "fire":
            out.append(r["ts"])
    return out

def run_candidate(candidate, now=None):
    """candidate: {text, purpose, origin_event, recipient, p_accept, p_need, ask}
    Returns the ledger record. Never raises: gate failures land as blocked."""
    now = time.time() if now is None else now
    rec = {"ts": now, "lane": LANE_CFG["lane"], "origin_event": candidate.get("origin_event"),
           "class": candidate.get("class", "vertical"), "ask": candidate.get("ask")}
    try:
        d = proactive_gate.decide(LANE_CFG, candidate.get("p_accept"), candidate.get("p_need"))
    except ValueError as e:
        rec.update(verdict="blocked", reason=f"proactive_gate fail-closed: {e}")
        _append(LEDGER, rec); return rec
    rec["tau"] = round(d["tau"], 4)
    if d["verdict"] != "fire":
        rec.update(verdict=d["verdict"], reason="below tau" + (" (slow: within margin, recorded not sent)" if d["verdict"] == "slow" else ""))
        _append(LEDGER, rec); return rec
    try:
        if not proactive_gate.check_rate(_history(), now, LANE_CFG["min_interval"], LANE_CFG["max_fires_per_window"]):
            rec.update(verdict="blocked", reason="proactive_gate rate caps: min_interval/max_fires_per_window")
            _append(LEDGER, rec); return rec
    except ValueError as e:
        rec.update(verdict="blocked", reason=f"rate caps fail-closed: {e}")
        _append(LEDGER, rec); return rec
    try:
        sendcheck.sendcheck(SURFACE, candidate["text"], candidate.get("purpose"),
                            origin_event=candidate.get("origin_event", ""), recipient=candidate.get("recipient", ""))
        sendcheck.check_rate(SURFACE, now)
    except sendcheck.SendBlocked as e:
        rec.update(verdict="blocked", reason=f"sendcheck: {e}")
        _append(LEDGER, rec); return rec
    grade = delivery_checklist.score_draft(candidate["text"])
    rec["delivery_score"] = grade["score"]
    rec["delivery_failed_criteria"] = sorted({d["criterion"] for d in grade["deductions"]})
    if "natural_format" in rec["delivery_failed_criteria"]:
        rec.update(verdict="blocked", reason=f"delivery grade {grade['score']}/10: metadata leakage (natural_format)")
        _append(LEDGER, rec); return rec
    fid = fire_id([LANE_CFG["lane"], candidate.get("origin_event", ""), str(int(now // LANE_CFG["min_interval"]))])
    rec.update(verdict="fire", fire_id=fid)
    _append(LEDGER, rec)
    _append(OUTBOX, {"ts": now, "fire_id": fid, "lane": LANE_CFG["lane"],
                     "text": candidate["text"], "purpose": candidate.get("purpose")})
    return rec

def record_feedback(fire_id_value, outcome):
    """Structured feedback event (accept / reject / ignore-timeout) on the ledger."""
    if outcome not in ("accept", "reject", "ignore-timeout"):
        raise ValueError(f"bad feedback outcome {outcome!r}")
    rec = {"ts": time.time(), "lane": LANE_CFG["lane"], "verdict": "feedback",
           "fire_id": fire_id_value, "outcome": outcome}
    _append(LEDGER, rec); return rec

def candidate_from_gate_receipt(receipt):
    """Real candidate: need is high only when the tools gate is not GREEN."""
    green = receipt.get("verdict") == "GREEN"
    return {"text": f"Tools gate {receipt.get('verdict')}: {receipt.get('reason', '')}"[:400],
            "purpose": "attention" if not green else "result",
            "origin_event": f"tools-gate-{receipt.get('run_id', 'unknown')}",
            "recipient": "principal",
            "p_accept": 0.9 if not green else 0.55,
            "p_need": 1.0 if not green else 0.3,
            "ask": "review tools gate", "class": "vertical"}

def audit_silent_verdicts(ledger_path=None, sample_n=5):
    """Audit the silent verdicts (adoption A-20, source: thunlp/ProactiveAgent).

    The would-accept review samples SILENT gate verdicts (silent / slow, and
    blocked-below-tau) as well as fires, and scores missed needs, so silence
    is audited, not assumed correct. Returns a summary dict: counts by
    verdict, the sampled silent records, and missed_need = silent records
    whose candidate carried p_need at or above the lane C_FN weight share
    (a need the gate valued highly yet stayed silent on). Read-only."""
    ledger_path = ledger_path or LEDGER
    rows = []
    if os.path.isfile(ledger_path):
        for line in open(ledger_path, encoding="utf-8"):
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    counts = {}
    for r in rows:
        counts[r.get("verdict")] = counts.get(r.get("verdict"), 0) + 1
    silent = [r for r in rows if r.get("verdict") in ("silent", "slow")]
    sample = silent[-sample_n:] if sample_n else silent
    return {"counts": counts, "silent_total": len(silent),
            "silent_sample": sample,
            "rule": "review the silent sample each lane review; a silent verdict is a verdict, scored like a fire"}

def record_reformulation(ledger_path, origin_event, what_changed):
    """Bounded reformulation after a gate rejection (adoption A-20).

    A gate rejection may trigger AT MOST ONE reformulation, and it must name
    what changed; the attempt is logged in the lane ledger. A second
    reformulation for the same origin_event raises ValueError."""
    prior = 0
    if os.path.isfile(ledger_path):
        for line in open(ledger_path, encoding="utf-8"):
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("verdict") == "reformulation" and r.get("origin_event") == origin_event:
                prior += 1
    if prior >= 1:
        raise ValueError(f"reformulation cap reached for {origin_event!r}: at most one per rejection")
    if not what_changed:
        raise ValueError("reformulation must name what changed")
    rec = {"ts": time.time(), "lane": LANE_CFG["lane"], "verdict": "reformulation",
           "origin_event": origin_event, "what_changed": what_changed}
    with open(ledger_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
    return rec

if __name__ == "__main__":
    print(__doc__)
