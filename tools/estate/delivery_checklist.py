#!/usr/bin/env python3
"""Pre-send delivery-form checklist (A-21). ProactiveEval Stage 2
deduction arithmetic as a cheap scoring step for any proactive message
draft, run before the proactive gate. Start at 10; deduct per failed
criterion across five criteria:
  1. goal progression: the draft moves a named goal or task forward
  2. personalisation: the draft is specific to this recipient/context
  3. proactive tone: offers a next step, not a bare notification or plea
  4. concise: each message at most 2 sentences or 50 words
  5. natural format: no metadata leakage (no lane ids, tau values,
     origin events, JSON scaffolding, or internal field names)
Deductions are 2 to 4 points by severity. This scores FORM only; it is
not the price/purpose gate (proactive_gate.py, sendcheck.py) and a high
score never authorizes a send by itself.

Usage: delivery_checklist.py selftest
Library: score_draft(text, recipient_name="", goal_terms=()) -> dict
"""
import re, sys

LEAK_MARKERS = ("origin_event", "lane:", "lane_id", "tau=", "p_accept", "p_need",
                "would-accept", "would_accept", "fire_id", "dedup", "{", "}",
                "verdict", "C_FA", "C_FN")
NEXT_STEP_HINTS = ("next", "shall i", "want me to", "ready to", "you can",
                   "tap", "reply", "scheduled", "booked", "confirmed", "due")

def _sentences(text):
    return [s for s in re.split(r"[.!?]+", text) if s.strip()]

def score_draft(text, recipient_name="", goal_terms=()):
    deductions = []
    score = 10
    def deduct(points, criterion, reason):
        nonlocal score
        score -= points
        deductions.append({"criterion": criterion, "points": points, "reason": reason})
    low = text.lower()
    words = text.split()
    # 1. goal progression: references a goal term or a concrete outcome
    if goal_terms:
        if not any(g.lower() in low for g in goal_terms):
            deduct(3, "goal_progression", "draft names none of the goal terms")
    elif not re.search(r"\b(done|ready|due|scheduled|confirmed|booked|finished|arrives|visit|appointment)\b", low):
        deduct(3, "goal_progression", "no concrete outcome or goal reference")
    # 2. personalisation
    if recipient_name:
        if recipient_name.lower() not in low and "you" not in low and "your" not in low:
            deduct(2, "personalisation", "no recipient name or second-person reference")
    elif "you" not in low and "your" not in low:
        deduct(2, "personalisation", "generic broadcast wording, no second-person reference")
    # 3. proactive tone
    if not any(h in low for h in NEXT_STEP_HINTS):
        deduct(2, "proactive_tone", "no next step, offer, or actionable anchor")
    # 4. concise: at most 2 sentences or 50 words
    if len(words) > 50:
        deduct(3, "concise", f"{len(words)} words exceeds 50")
    elif len(_sentences(text)) > 2 and len(words) > 30:
        deduct(2, "concise", "more than 2 sentences and over 30 words")
    # 5. natural format, no metadata leakage
    leaks = [m for m in LEAK_MARKERS if m in low or m in text]
    if leaks:
        deduct(4 if len(leaks) > 1 else 3, "natural_format", f"metadata leakage: {leaks}")
    return {"score": max(0, score), "deductions": deductions,
            "passed": score >= 7 and not any(d["criterion"] == "natural_format" for d in deductions)}

def selftest():
    good = score_draft("Your Tuesday visit is confirmed and your arrival window is ready. Tap to see the details.",
                       recipient_name="", goal_terms=("visit",))
    assert good["score"] == 10 and good["passed"], good
    leaky = score_draft('lane: tools-gate-digest verdict fire tau=0.20 origin_event evt-9 {"a": 1} ' + "word " * 60,
                        goal_terms=("visit",))
    crits = {d["criterion"] for d in leaky["deductions"]}
    assert "natural_format" in crits and "concise" in crits and "goal_progression" in crits, leaky
    assert leaky["score"] < good["score"] and not leaky["passed"], leaky
    bland = score_draft("Something happened somewhere at some point in the system today.")
    assert any(d["criterion"] == "goal_progression" for d in bland["deductions"]), bland
    print("SELFTEST PASS delivery_checklist: clean draft 10/10, leaky+verbose draft deducted on format/concise/goal, bland draft deducted on goal progression")
    return 0

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "selftest":
        raise SystemExit(selftest())
    print(__doc__)
