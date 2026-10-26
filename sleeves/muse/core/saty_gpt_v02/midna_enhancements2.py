"""Midna BEHAVIORAL enhancement layer for saty_gpt_v02
(MIDNA-ENH2, 2026-10-23) — the layer that changes trade
decisions, commissioned after the owner rejected MIDNA-ENH-1..5 as
bookkeeping ("didn't actually enhance the strategy AT ALL").

Seven deltas, each individually switched via
ctx.extra["gpt_v02_enh2"] (default ON); ALL OFF restores the
pre-ENH2 behavior exactly. Every parameter below is one of HIS
constants or derived from his constants with the derivation
written in ENHANCE2-DESIGN.md (saty-gpt-v02 workflow work dir).
His ported core files are never edited; his refusal floors
stay absolute vetoes — these functions arbitrate among his
SURVIVORS and add named refusals; they never admit what he
refuses. Pure functions: no I/O, no state of their own (the
wrapper owns the journal).

Deltas: ENH2-1 best-chart arbitration, ENH2-2 freshness /
chase-lifetime, ENH2-3 opposite-signal sanity, ENH2-4
executable pricing + spread honesty, ENH2-5 context as
decision, ENH2-6 session-risk posture, ENH2-7 late-session
reachability.
"""

# --- his constants (strategies.py StrategyConfig / risk_lots
# RiskConfig / data.py Calendar — transcribed, never tuned) ---
COST = 0.02               # estimated_round_trip_cost
MIN_NET_R = 1.5           # minimum_net_reward_risk
CHASE_ATR = 0.40          # max_chase_atr
TOLERANCE_ATR = 0.10      # tolerance_atr (his noise band)
PHASE_SIGNIFICANCE = 5.0  # minimum_phase_divergence
FIRST_SCALE_FRACTION = 0.5  # RiskConfig partial_fraction: his
# first scale-out milestone — the room-consumed bound (ENH2-2)
MAX_SESSION_LOSS_R = 2.0  # RiskConfig max_session_loss_r
POSTURE_TRIGGER_R = -MAX_SESSION_LOSS_R / 2.0  # -1.0R: half
# his session budget gone — the selective posture (ENH2-6)
BAR_SECONDS = 600         # his 10m execution clock

# His router precedence (strategies.py update() evaluation
# order, PORT-SPEC 2.5): compression (config order: retest
# before breakout), vomy transitions, pro21, divergence, phase,
# then aligned continuation golden_gate -> pivot -> atr.
PRECEDENCE = (
    "compression_retest", "compression_breakout",
    "vomy_early13", "vomy_confirmed48", "vomy_pro21",
    "divergence_mean_reversion", "phase_mean_reversion",
    "golden_gate", "pivot_pullback", "atr_retest",
)
# His two countertrend families (countertrend=True in _signal,
# risk_multiplier 0.5).
MEAN_REVERSION = ("divergence_mean_reversion",
                  "phase_mean_reversion")
# Lane groups for independent family evaluation: one lane per
# family, except the compression pair shares a lane in his
# config order (a solo breakout lane would manufacture
# candidates his config refuses by construction).
LANE_GROUPS = (
    ("vomy_early13",), ("vomy_confirmed48",), ("vomy_pro21",),
    ("golden_gate",), ("compression_retest", "compression_breakout"),
    ("pivot_pullback",), ("atr_retest",),
    ("divergence_mean_reversion",), ("phase_mean_reversion",),
)

ENH2_DEFAULTS = {
    "arbitration": True,        # MIDNA-ENH2-1
    "freshness": True,          # MIDNA-ENH2-2
    "opposite_sanity": True,    # MIDNA-ENH2-3
    "exec_pricing": True,       # MIDNA-ENH2-4
    "context_decision": True,   # MIDNA-ENH2-5
    "session_posture": True,    # MIDNA-ENH2-6
    "late_session": True,       # MIDNA-ENH2-7
}


def enh2_enabled(extra, key):
    """Per-delta switch: ctx.extra['gpt_v02_enh2'][key],
    default ON. A non-dict override is ignored."""
    overrides = (extra or {}).get("gpt_v02_enh2")
    if isinstance(overrides, dict) and key in overrides:
        return bool(overrides[key])
    return ENH2_DEFAULTS[key]


def any_enh2_on(extra):
    return any(enh2_enabled(extra, k) for k in ENH2_DEFAULTS)


def lanes_on(extra):
    """Lane engines exist only for the two set-level deltas."""
    return enh2_enabled(extra, "arbitration") or \
        enh2_enabled(extra, "opposite_sanity")


# --- his geometry, recomputed from a candidate's own fields ---
def net_reward(c):
    """d*(first obstacle - entry) - cost: his _signal net
    reward numerator, price units."""
    d = 1 if c["direction"] > 0 else -1
    return d * (c["targets"][0] - c["reference_entry"]) - COST


def net_risk(c):
    d = 1 if c["direction"] > 0 else -1
    return d * (c["reference_entry"] - c["stop"]) + COST


def net_r(c):
    risk = net_risk(c)
    return net_reward(c) / risk if risk > 0 else 0.0


def precedence_index(setup):
    return PRECEDENCE.index(setup) if setup in PRECEDENCE \
        else len(PRECEDENCE)


def candidate_from_signal(sig, faithful=False):
    return {
        "setup": sig.setup, "direction": int(sig.direction),
        "reference_entry": float(sig.reference_entry),
        "stop": float(sig.stop),
        "targets": tuple(float(t) for t in sig.targets),
        "atr": float(sig.atr), "signal_id": sig.signal_id,
        "bar_end": sig.bar_end.isoformat()
        if hasattr(sig.bar_end, "isoformat") else str(sig.bar_end),
        "risk_multiplier": float(sig.risk_multiplier),
        "faithful": bool(faithful),
    }


# --- ENH2-5: strong context from his causal outputs only ---
def strong_context(context):
    """(direction, alignment inputs). Strong requires ALL THREE
    of his witnesses to agree: the 1H ribbon stack (his _stack),
    the 1H Phase Oscillator (sign agrees, |phase| >= his 5.0
    significance), and the close on the stack's side of the day
    anchor by >= his 0.10 ATR tolerance. Returns 0 when any
    witness disagrees or is absent — one witness never vetoes.
    context = {"stack": int, "phase": float|None,
               "anchor_distance_atr": float|None}."""
    if not context:
        return 0
    stack = int(context.get("stack") or 0)
    phase = context.get("phase")
    dist = context.get("anchor_distance_atr")
    if stack == 0 or phase is None or dist is None:
        return 0
    if (1 if phase > 0 else -1) != stack:
        return 0
    if abs(phase) < PHASE_SIGNIFICANCE:
        return 0
    if (1 if dist > 0 else -1) != stack or abs(dist) < TOLERANCE_ATR:
        return 0
    return stack


def alignment_score(c, context, strong_dir):
    """ENH2-1 near-tie breaker: 2 = with the strong context,
    1 = agrees with the close-vs-anchor sign, 0 = neither."""
    d = 1 if c["direction"] > 0 else -1
    if strong_dir and d == strong_dir:
        return 2
    dist = (context or {}).get("anchor_distance_atr")
    if dist is not None and d * dist > 0:
        return 1
    return 0


def decide(candidates, extra, *, quote=None, context=None,
           session_pnl_r=None, best_net_r=None,
           decision_bar_end=None, decision_time=None,
           flat_at=None):
    """The ENH2 decision pipeline over his surviving candidates.

    candidates: candidate dicts (candidate_from_signal); the
    faithful engine's candidate carries faithful=True.
    quote: (bid, ask) or None. context: see strong_context.
    Returns {"selected": candidate|None, "refusals": [...],
    "survivors_net_r": [...], "strong_context": int}.
    With every switch OFF the selection is the faithful
    candidate (else his precedence) and refusals are empty —
    the pre-ENH2 behavior exactly."""
    refusals = []
    pool = list(candidates or [])
    sdir = strong_context(context)

    # ENH2-5 — counter-context mean reversion refused by name.
    if enh2_enabled(extra, "context_decision") and sdir:
        keep = []
        for c in pool:
            d = 1 if c["direction"] > 0 else -1
            if c["setup"] in MEAN_REVERSION and d == -sdir:
                refusals.append({
                    "setup": c["setup"], "signal_id": c["signal_id"],
                    "reason": "enh2_counter_context_strong"})
            else:
                keep.append(c)
        pool = keep

    # ENH2-3 — opposite survivors: the weaker-geometry side is
    # refused by name; sides within his cost noise keep the
    # faithful candidate's side.
    if enh2_enabled(extra, "opposite_sanity"):
        dirs = {1 if c["direction"] > 0 else -1 for c in pool}
        if len(dirs) > 1:
            best = {d: max(net_reward(c) for c in pool
                           if (1 if c["direction"] > 0 else -1) == d)
                    for d in dirs}
            if abs(best[1] - best[-1]) < COST:
                f = next((c for c in pool if c.get("faithful")), None)
                keep_dir = (1 if f["direction"] > 0 else -1) \
                    if f else (1 if best[1] >= best[-1] else -1)
            else:
                keep_dir = 1 if best[1] > best[-1] else -1
            keep = []
            for c in pool:
                if (1 if c["direction"] > 0 else -1) == keep_dir:
                    keep.append(c)
                else:
                    refusals.append({
                        "setup": c["setup"],
                        "signal_id": c["signal_id"],
                        "reason": "enh2_opposite_weaker_geometry"})
            pool = keep

    # Selection — ENH2-1 arbitration, else his precedence with
    # the faithful candidate first (the pre-ENH2 choice).
    selected = None
    if pool:
        if enh2_enabled(extra, "arbitration"):
            top = max(net_reward(c) for c in pool)
            tied = [c for c in pool if top - net_reward(c) < COST]
            if len(tied) == 1:
                selected = tied[0]
            else:
                selected = max(tied, key=lambda c: (
                    alignment_score(c, context, sdir),
                    -precedence_index(c["setup"]),
                    1 if c.get("faithful") else 0))
        else:
            f = next((c for c in pool if c.get("faithful")), None)
            selected = f or min(
                pool, key=lambda c: precedence_index(c["setup"]))

    # Per-selected refusals, in commission order.
    if selected is not None:
        d = 1 if selected["direction"] > 0 else -1
        exec_px = selected["reference_entry"]
        if quote is not None:
            exec_px = quote[1] if d > 0 else quote[0]
        reason = None
        # ENH2-2 freshness: stale bar, then room consumed.
        if enh2_enabled(extra, "freshness"):
            if decision_bar_end is not None and \
                    selected.get("bar_end") != decision_bar_end:
                reason = "enh2_stale_candidate"
            elif quote is not None:
                consumed = d * (exec_px - selected["reference_entry"])
                room = d * (selected["targets"][0]
                            - selected["reference_entry"])
                if consumed > 0 and room > 0 and \
                        consumed >= FIRST_SCALE_FRACTION * room:
                    reason = "enh2_room_consumed"
        # ENH2-4 spread honesty: his geometry assumes the 0.02
        # round-trip cost; a wider live spread falsifies it.
        if reason is None and enh2_enabled(extra, "exec_pricing") \
                and quote is not None:
            if quote[1] - quote[0] > COST:
                reason = "enh2_spread_exceeds_cost_model"
        # ENH2-6 posture: down half his budget, demand the best
        # trade seen today, not just another trade.
        if reason is None and enh2_enabled(extra, "session_posture"):
            if session_pnl_r is not None and \
                    session_pnl_r <= POSTURE_TRIGGER_R and \
                    best_net_r is not None and \
                    net_r(selected) < best_net_r:
                reason = "enh2_posture_selective"
        # ENH2-7 reachability: bars left to his flat_at times
        # his per-bar ATR is the generous range bound.
        if reason is None and enh2_enabled(extra, "late_session"):
            if flat_at is not None and decision_time is not None:
                bars_left = int((flat_at - decision_time)
                                .total_seconds() // BAR_SECONDS)
                dist = d * (selected["targets"][0] - exec_px)
                if bars_left <= 0 or \
                        dist > bars_left * selected["atr"]:
                    reason = "enh2_target_unreachable"
        if reason is not None:
            refusals.append({"setup": selected["setup"],
                             "signal_id": selected["signal_id"],
                             "reason": reason})
            selected = None

    return {"selected": selected, "refusals": refusals,
            "survivors_net_r": [net_r(c) for c in (candidates or [])],
            "strong_context": sdir}
