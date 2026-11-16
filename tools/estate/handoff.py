#!/usr/bin/env python3
"""One-shot handoff capability store. Round-5 item 38 (discipline 9), WIRED.
Structurally outside the tool registry: a file store under
~/workspace/tools/handoff_store/. A handoff is created with a summary, a
separate handoff id, and a random token; only the token's sha256 is stored.
Rules: TTL-bound; exactly one waiter may claim; delivery consumes the
capability (second delivery rejected); empty summary rejected; expired
rejected; wrong token rejected. The token delivers a summary string only:
this module exposes no tool invocation surface of any kind.
"""
import hashlib, json, os, secrets, sys, time

STORE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "handoff_store")

class HandoffError(Exception):
    pass

def _path(handoff_id):
    if not handoff_id or "/" in handoff_id or ".." in handoff_id:
        raise HandoffError("bad handoff id")
    return os.path.join(STORE, handoff_id + ".json")

def _load(handoff_id):
    p = _path(handoff_id)
    if not os.path.isfile(p):
        raise HandoffError(f"unknown handoff {handoff_id!r}")
    return json.load(open(p, encoding="utf-8"))

def _save(rec):
    os.makedirs(STORE, exist_ok=True)
    tmp = _path(rec["id"]) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(rec, f)
    os.replace(tmp, _path(rec["id"]))

ADMISSION_STRENGTHS = ("explicit", "inferred", "not_admitted")

def create(summary, ttl_s=900, now=None, admission_strength="explicit"):
    """Producer side. Returns (handoff_id, token). Token shown once, never stored.

    A-17: every handoff records its admission strength on the dsh lattice
    (explicit = instructed work; inferred = derived work, visibly weaker;
    not_admitted = context only, never a work instruction)."""
    if not summary or not summary.strip():
        raise HandoffError("empty summary rejected")
    if admission_strength not in ADMISSION_STRENGTHS:
        raise HandoffError(f"bad admission_strength {admission_strength!r}: must be one of {ADMISSION_STRENGTHS}")
    now = time.time() if now is None else now
    token = secrets.token_urlsafe(32)
    rec = {"id": "ho-" + secrets.token_hex(8),
           "token_sha256": hashlib.sha256(token.encode()).hexdigest(),
           "summary": summary, "created": now, "expires": now + ttl_s,
           "admission_strength": admission_strength,
           "waiter": None, "state": "open"}
    _save(rec)
    return rec["id"], token

def claim_waiter(handoff_id, waiter, now=None):
    """Exactly one waiter: the first claim wins, a second distinct waiter is rejected."""
    now = time.time() if now is None else now
    rec = _load(handoff_id)
    if rec["state"] != "open":
        raise HandoffError(f"handoff not open (state={rec['state']})")
    if now > rec["expires"]:
        rec["state"] = "expired"; _save(rec)
        raise HandoffError("handoff expired (TTL)")
    if rec["waiter"] is not None and rec["waiter"] != waiter:
        raise HandoffError("second waiter rejected: exactly one waiter")
    rec["waiter"] = waiter; _save(rec)
    return True

def deliver(handoff_id, token, waiter, now=None):
    """Consumer side. Verifies token + waiter, returns summary, consumes capability."""
    now = time.time() if now is None else now
    rec = _load(handoff_id)
    if rec["state"] != "open":
        raise HandoffError(f"handoff already consumed (state={rec['state']}): second delivery rejected")
    if now > rec["expires"]:
        rec["state"] = "expired"; _save(rec)
        raise HandoffError("handoff expired (TTL): delivery rejected")
    if hashlib.sha256(token.encode()).hexdigest() != rec["token_sha256"]:
        raise HandoffError("bad token: delivery rejected")
    if rec["waiter"] is not None and rec["waiter"] != waiter:
        raise HandoffError("not the claimed waiter: delivery rejected")
    rec["state"] = "consumed"; rec["delivered_at"] = now; rec["delivered_to"] = waiter
    _save(rec)
    return rec["summary"]

def deliver_full(handoff_id, token, waiter, now=None):
    """Like deliver(), but returns the full record view including the
    recorded admission_strength (A-17). Consumes the capability the same
    way; deliver() keeps its original summary-string contract."""
    summary = deliver(handoff_id, token, waiter, now=now)
    rec = _load(handoff_id)
    return {"summary": summary,
            "admission_strength": rec.get("admission_strength", "explicit"),
            "delivered_to": rec.get("delivered_to"), "state": rec.get("state")}

def abort(handoff_id, token):
    rec = _load(handoff_id)
    if hashlib.sha256(token.encode()).hexdigest() != rec["token_sha256"]:
        raise HandoffError("bad token: abort rejected")
    rec["state"] = "aborted"; _save(rec)
    return True

def selftest():
    hid, tok = create("gate summary: 3 obligations covered", ttl_s=60)
    assert claim_waiter(hid, "tools_gate") is True
    try:
        claim_waiter(hid, "someone_else"); raise SystemExit("second waiter not rejected")
    except HandoffError: pass
    try:
        deliver(hid, "wrong-token", "tools_gate"); raise SystemExit("bad token not rejected")
    except HandoffError: pass
    out = deliver(hid, tok, "tools_gate")
    assert out.startswith("gate summary"), out
    try:
        deliver(hid, tok, "tools_gate"); raise SystemExit("second delivery not rejected")
    except HandoffError: pass
    try:
        create("   "); raise SystemExit("empty summary not rejected")
    except HandoffError: pass
    hid2, tok2 = create("stale summary", ttl_s=10, now=1000.0)
    try:
        deliver(hid2, tok2, "w", now=2000.0); raise SystemExit("expired not rejected")
    except HandoffError: pass
    hid3, tok3 = create("inferred follow-up summary", admission_strength="inferred")
    full = deliver_full(hid3, tok3, "w2")
    assert full["admission_strength"] == "inferred" and full["summary"].startswith("inferred"), full
    try:
        create("x", admission_strength="bogus"); raise SystemExit("bad admission_strength not rejected")
    except HandoffError: pass
    print("SELFTEST PASS handoff A-17: admission strength recorded on the record and returned by deliver_full; invalid strength rejected")
    print("SELFTEST PASS handoff: round trip consumed once, second waiter/delivery rejected, bad token rejected, empty summary rejected, TTL expiry rejected")
    return 0

if __name__ == "__main__":
    raise SystemExit(selftest() if len(sys.argv) > 1 and sys.argv[1] == "selftest" else print(__doc__))
