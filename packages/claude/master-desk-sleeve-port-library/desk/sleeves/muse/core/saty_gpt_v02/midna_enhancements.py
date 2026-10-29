"""Midna enhancement layer for saty_gpt_v02 (2026-10-23).

User's character direction (fast / smooth / executable /
efficient / agile / intelligent / dynamic) implemented as
individually switched deltas in the wrapper layer ONLY. His
ported strategy code is never edited and no number of his is
changed: every function here is bookkeeping, stamping or
bounding around the faithful evaluation. Each delta defaults
ON; switching it OFF via ctx.extra["gpt_v02_enh"] restores the
faithful behavior exactly (proven per delta by
tests/test_saty_gpt_v02_midna_enh_20261023.py).

Deltas: ENH-1 silence audit, ENH-2 bounded journal retention,
ENH-3 causal context stamps, ENH-4 warmup transparency,
ENH-5 executable-price audit + named admission refusals.
Design + evidence + rejected candidates: ENHANCE-DESIGN.md in
the saty-gpt-v02 workflow work dir.
"""
from datetime import timedelta

ENH_DEFAULTS = {
    "silence_audit": True,      # MIDNA-ENH-1
    "bound_journal": True,      # MIDNA-ENH-2
    "context_stamps": True,     # MIDNA-ENH-3
    "warmup_transparency": True,  # MIDNA-ENH-4
    "exec_audit": True,         # MIDNA-ENH-5
}

EPISODES_CAP = 64
REJECTIONS_CAP = 32
STOP_HISTORY_CAP = 16
CLOSED_LOTS_CAP = 32
BARS_PER_SESSION = {"10m": 39, "1H": 6}


def enh_enabled(extra, key):
    """Per-delta switch: ctx.extra['gpt_v02_enh'][key], default
    ON. A non-dict override is ignored (faithful defaults hold
    is wrong way round — defaults are the ENHANCED build)."""
    overrides = (extra or {}).get("gpt_v02_enh")
    if isinstance(overrides, dict) and key in overrides:
        return bool(overrides[key])
    return ENH_DEFAULTS[key]


def bound_journal(journal):
    """MIDNA-ENH-2: cap the journal's unbounded lists in place.
    Open/intent records are never dropped; only closed history
    is trimmed, newest kept. Returns the journal."""
    episodes = journal.get("episodes") or []
    if len(episodes) > EPISODES_CAP:
        keep_from = len(episodes) - EPISODES_CAP
        pinned = [e for e in episodes[:keep_from]
                  if e.get("state") in ("intent", "filled")]
        journal["episodes"] = pinned + episodes[keep_from:]
    for key in ("sizing_rejections", "admission_rejections"):
        rows = journal.get(key) or []
        if len(rows) > REJECTIONS_CAP:
            journal[key] = rows[-REJECTIONS_CAP:]
    lots = journal.get("lots") or []
    closed = [x for x in lots if x.get("state") != "open"]
    if len(closed) > CLOSED_LOTS_CAP:
        drop = {id(x) for x in closed[:-CLOSED_LOTS_CAP]}
        journal["lots"] = [x for x in lots if id(x) not in drop]
        lots = journal["lots"]
    for lot in lots:
        hist = lot.get("stop_history") or []
        if len(hist) > STOP_HISTORY_CAP:
            lot["stop_history"] = hist[-STOP_HISTORY_CAP:]
    return journal


def silence_audit(decisions, arm_setup, reason):
    """MIDNA-ENH-1: enumerate a no-entry pass from the engine's
    own decision records of THIS pass. Counts by event and, for
    ARM/CANCEL/REJECT, by setup — every family's outcome is
    reason-visible, nothing dies silently."""
    events, setups = {}, {}
    for d in decisions or []:
        ev = d.get("event") or "?"
        events[ev] = events.get(ev, 0) + 1
        if ev in ("ARM", "CANCEL", "REJECT") and d.get("setup"):
            row = setups.setdefault(
                d["setup"], {"arm": 0, "cancel": 0, "reject": 0})
            row[ev.lower()] += 1
    return {"events": events, "setups": setups,
            "arm": arm_setup, "reason": reason}


def warmup_report(counts, warmup_bars):
    """MIDNA-ENH-4: name the cure distance for a warmup block —
    per-clock shortfall, the binding clock, approx sessions."""
    shortfall, sessions = {}, {}
    for clock in ("10m", "1H"):
        missing = max(0, warmup_bars - int(counts.get(clock) or 0))
        shortfall[clock] = missing
        per = BARS_PER_SESSION[clock]
        sessions[clock] = -(-missing // per) if missing else 0
    binding = max(shortfall, key=lambda c: sessions[c])
    return {"shortfall_bars": shortfall, "binding_clock": binding,
            "sessions_remaining": sessions}


def context_stamp(now_dt, session, anchor, atr, close):
    """MIDNA-ENH-3: causal, stance-0 context. Session phase from
    HIS session law (open / flat_at on the Session object) and
    the final close's distance to the day-reference anchor in
    ATR units. Information only — never a veto."""
    if now_dt < session.open + timedelta(minutes=90):
        phase = "opening_90"
    elif now_dt >= session.flat_at:
        phase = "post_flat"
    elif now_dt >= session.close - timedelta(minutes=60):
        phase = "closing_60"
    else:
        phase = "midday"
    dist = None
    if atr and atr > 0 and anchor is not None and close is not None:
        dist = round((close - anchor) / atr, 4)
    return {"phase": phase, "anchor_distance_atr": dist}


def exec_audit(direction, exec_px, reference_entry, atr, quote):
    """MIDNA-ENH-5a: the executable terms of an entry, stamped —
    side price actually used, spread, and the executable price's
    distance from his reference entry in ATR units."""
    spread = None
    if quote is not None:
        spread = round(quote[1] - quote[0], 4)
    chase = None
    if atr and atr > 0:
        chase = round(direction * (exec_px - reference_entry) / atr, 4)
    return {"exec_px": round(exec_px, 4), "spread": spread,
            "exec_vs_reference_atr": chase}
