"""The desk's memory: an append-only journal (state/journal.jsonl, one digest per session) and the durable
facts it has learned (state/memory.json). The digest is what a person — or the desk itself on its next
calibration — needs to know about the day: P&L by sleeve, trades closed, verdict changes, calibration
changes, health findings."""
import json
import os
from datetime import datetime, timezone

from ..util import ET, read_json, write_json_atomic


def last_digest(root):
    path = os.path.join(root, "state", "journal.jsonl")
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        f.seek(0, 2)
        n = f.tell()
        f.seek(max(0, n - 2_000_000))
        lines = f.read().splitlines()
    for ln in reversed(lines):
        try:
            return json.loads(ln)
        except ValueError:
            continue
    return None


def digest(root, report, tca, health, cal, cards, now=None):
    now = float(now or datetime.now(timezone.utc).timestamp())
    prev = last_digest(root) or {}
    prev_eq = {sid: s.get("equity") for sid, s in (prev.get("sleeves") or {}).items()}
    prev_cards = prev.get("verdicts") or {}
    since = float(prev.get("at") or 0)
    books = read_json(os.path.join(root, "state", "books.json"), {}) or {}
    sleeves = {}
    for sid, s in (report.get("sleeves") or {}).items():
        closed = [t for t in (books.get(sid) or {}).get("trades") or () if float(t.get("closed_at") or 0) > since]
        sleeves[sid] = {"equity": s["equity"], "day_pnl": round(s["equity"] - prev_eq[sid], 2) if sid in prev_eq else None,
                        "trades_closed": len(closed), "pnl_closed": round(sum(float(t.get("pnl") or 0) for t in closed), 2),
                        "open": s["open_positions"], "max_dd_pct": s["max_drawdown_pct"]}
    verdicts = {sid: c["verdict"] for sid, c in (cards or {}).items()}
    notes = []
    for sid, v in sorted(verdicts.items()):
        if v != prev_cards.get(sid) and v in ("PROPOSE", "REVIEW"):
            notes.append({"what": "verdict", "sleeve": sid, "from": prev_cards.get(sid), "to": v})
    for ch in (cal or {}).get("changes") or ():
        notes.append(dict(ch, what="calibration:" + ch.get("what", "")))
    for c in (health or {}).get("checks") or ():
        if c["level"] != "OK":
            notes.append({"what": "health", "check": c["check"], "level": c["level"]})
    movers = sorted(((sid, s["day_pnl"]) for sid, s in sleeves.items() if s["day_pnl"] is not None), key=lambda kv: kv[1])
    rec = {"at": now, "session": datetime.fromtimestamp(now, tz=ET).date().isoformat(), "desk": report.get("desk"),
           "sleeves": sleeves, "verdicts": verdicts, "notes": notes, "tca": (tca or {}).get("all"),
           "best": movers[-5:][::-1], "worst": movers[:5], "health": (health or {}).get("level")}
    with open(os.path.join(root, "state", "journal.jsonl"), "a") as f:
        f.write(json.dumps(rec, sort_keys=True, default=str) + "\n")
    mem = read_json(os.path.join(root, "state", "memory.json"), {}) or {}
    mem["sessions"] = int(mem.get("sessions") or 0) + 1
    mem.setdefault("first_session", rec["session"])
    mem["last_session"] = rec["session"]
    facts = mem.setdefault("facts", {})
    for n in notes:
        if n["what"] == "verdict":
            facts.setdefault("verdict_history", []).append([rec["session"], n["sleeve"], n["to"]])
        elif n["what"].startswith("calibration"):
            facts.setdefault("calibration_history", []).append([rec["session"], n.get("asset"), n.get("to")])
        elif n["what"] == "health":
            k = facts.setdefault("health_incidents", {})
            k[n["check"]] = int(k.get(n["check"]) or 0) + 1
    write_json_atomic(os.path.join(root, "state", "memory.json"), mem)
    return rec
