"""How the team changes size. Aurelia still names the book. These caps bind only in stress.

Scheduled events are watched and remembered. They do not move the book by themselves.
A shock does: extreme volatility, a single-day Nasdaq drop, or a notice the desk was given.
Gold is the hedge and is not cut. This is a risk limit, not a claim of extra return.
"""

from __future__ import annotations

STAND_DOWN_VIX = 40.0
CAUTIOUS_VIX = 25.0
STAND_DOWN_DAY = -0.08
CAUTIOUS_DAY = -0.05


def posture(snapshot: dict, events: list[dict], notes: list[dict]) -> dict:
    reasons = []
    level = "normal"
    for note in notes:
        kind = str(note.get("kind") or "")
        if kind in {"black_swan", "stand_down"}:
            level = "stand_down"
            reasons.append(note.get("text") or "stand-down notice")
    vix = snapshot.get("vix")
    day = snapshot.get("ndx_day")
    if isinstance(vix, (int, float)) and vix >= STAND_DOWN_VIX:
        level = "stand_down"
        reasons.append(f"VIX {vix:.1f} is at a shock level")
    if isinstance(day, (int, float)) and day <= STAND_DOWN_DAY:
        level = "stand_down"
        reasons.append(f"Nasdaq day {day:.1%}")
    if level == "normal":
        if isinstance(vix, (int, float)) and vix >= CAUTIOUS_VIX:
            level = "cautious"
            reasons.append(f"VIX {vix:.1f} is elevated")
        elif isinstance(day, (int, float)) and day <= CAUTIOUS_DAY:
            level = "cautious"
            reasons.append(f"Nasdaq day {day:.1%}")
    if not reasons:
        reasons.append("no shock in the tape and no stand-down notice")
    watched = [e["detail"] for e in events if e["kind"] == "rate_shock"]
    return {"level": level, "reasons": reasons, "watched": watched}


def apply_posture(ndx: float, gold: float, level: str) -> tuple[float, float]:
    """Cap Nasdaq leverage. Gold stays."""
    if level == "stand_down":
        return min(ndx, 0.5), gold
    if level == "cautious":
        return min(ndx, 1.0), gold
    return ndx, gold
