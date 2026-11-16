#!/usr/bin/env python3
"""Send-time caps + purpose gate. Round-4 discipline 13. FAILS CLOSED.
Validates an outbound draft before any send on a governed surface.
Where the platform send path cannot be hooked, callers must invoke this
explicitly; see EXECUTION-MAP.md for the named boundary.
"""
import sys

CAPS_WORDS = {"im": 100, "patient_text": 60, "feed": 150, "side_chat": 500, "chat": 500}
CAPS_CHARS = {"patient_text": 320}
PURPOSES = {"result", "attention", "answer", "notification"}
# Round-5 item 6: coded rate caps (YETI m/k), enforced at validation, fail closed.
RATE_CAPS = {"im": (5, 20), "patient_text": (60, 40), "feed": (300, 10), "side_chat": (10, 100), "chat": (10, 100)}  # (min_interval_s, max_per_hour)
_rate_state = {}
def check_rate(surface, now):
    if surface not in RATE_CAPS: raise SendBlocked(f"no rate cap configured for {surface!r}: fail closed")
    mi, mx = RATE_CAPS[surface]; hist = [t for t in _rate_state.get(surface, []) if now - t < 3600]
    if hist and now - max(hist) < mi: raise SendBlocked(f"rate cap: min_interval {mi}s on {surface}")
    if len(hist) >= mx: raise SendBlocked(f"rate cap: max {mx}/hour on {surface}")
    hist.append(now); _rate_state[surface] = hist; return True

class SendBlocked(Exception):
    pass

def sendcheck(surface: str, text: str, purpose: str, origin_event: str = "", recipient: str = "") -> dict:
    if surface not in CAPS_WORDS:
        raise SendBlocked(f"unknown surface {surface!r}: fail closed")
    if not purpose or purpose not in PURPOSES:
        raise SendBlocked(f"purpose missing or not allowed: {purpose!r} (allowed: {sorted(PURPOSES)})")
    if not origin_event:
        raise SendBlocked("origin_event required: one acknowledgement per origin event")
    if not recipient:
        raise SendBlocked("recipient required")
    if not text or not text.strip():
        raise SendBlocked("empty text")
    words = len(text.split())
    if words > CAPS_WORDS[surface]:
        raise SendBlocked(f"word cap exceeded on {surface}: {words} > {CAPS_WORDS[surface]}")
    if surface in CAPS_CHARS and len(text) > CAPS_CHARS[surface]:
        raise SendBlocked(f"char cap exceeded on {surface}: {len(text)} > {CAPS_CHARS[surface]}")
    return {"ok": True, "surface": surface, "words": words, "purpose": purpose}

def selftest() -> int:
    ok = sendcheck("im", "Short status update for you.", "result", origin_event="evt-1", recipient="principal")
    assert ok["ok"] and ok["words"] == 5
    for label, fn in [
        ("over-cap", lambda: sendcheck("im", " ".join(["w"] * 101), "result", origin_event="e", recipient="r")),
        ("missing-purpose", lambda: sendcheck("im", "hi", "", origin_event="e", recipient="r")),
        ("bad-purpose", lambda: sendcheck("im", "hi", "chit-chat", origin_event="e", recipient="r")),
        ("missing-origin", lambda: sendcheck("im", "hi", "result", origin_event="", recipient="r")),
        ("unknown-surface", lambda: sendcheck("smoke-signal", "hi", "result", origin_event="e", recipient="r")),
    ]:
        try:
            fn(); raise AssertionError(f"{label} should have blocked")
        except SendBlocked:
            pass
    check_rate("im", 1000.0)
    try:
        check_rate("im", 1001.0); raise AssertionError("rate cap should block")
    except SendBlocked: pass
    print("SELFTEST PASS sendcheck rate caps: second fire inside min_interval blocked (round-5 item 6)")
    print("SELFTEST PASS sendcheck: valid draft accepted (5 words, purpose=result); over-cap, missing purpose, bad purpose, missing origin, unknown surface all blocked (fail closed)")
    return 0

if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "selftest":
        raise SystemExit(selftest())
    print(__doc__); print("usage: sendcheck.py selftest  (library: sendcheck(surface, text, purpose, origin_event, recipient))")
