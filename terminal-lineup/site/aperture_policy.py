#!/usr/bin/env python3
"""Aperture policy architecture: candidate qualification.

One source of truth for DEEP-PASS 3.2 item 1 (adapted from
Ausar's Aperture discovery policy, Section 2.8 of the deep
pass), rebuilt for our candidate and card surfaces. Best Setups
itself stays disconnected and disabled by the owner's
2026-10-25 ruling; this module adopts the policy pattern for
the live candidate surfaces only.

The policy is ordinal and deterministic. Stages run in a fixed
order and the first stage that decides a name is its decision;
there is no blended score anywhere in the output:

1. Data integrity stop. A name that fails a data check is not
   dropped: it returns as an exclusion record carrying every
   per name reason, so exclusions are ledgered by name, never
   only counted in aggregate. (His classifyOne returned null
   and dropped the name silently; that is the first fix.)
2. Proof gate. A QUARANTINED or REJECTED proof state avoids.
3. Hard vetoes. Anchor HARD AVOID, mature or failed formation,
   headwind topology, distribution participation, incomplete
   levels, chase line breached, target already traded, reward
   to risk below 1.25, failed or expired trigger, and the name
   level vetoes (more than 25 percent above the 60 session low,
   a 10 session run above 18 percent, invalidation breached,
   price below 1 dollar, median dollar volume below 5 million,
   or liquidity evidence missing entirely).
4. Trigger lifecycle. No trigger, an unconfirmed trigger
   (SEED or APPROACH), or a confirmed trigger whose freshness
   cannot be proven stays FORMING.
5. Tier qualification. S: reward to risk at least 2.0 with a
   confirmed trigger at age 0 or 1 bars. A: reward to risk at
   least 2.0 with a confirmed fresh trigger at an older age.
   B: reward to risk at least 1.25 with a confirmed fresh
   trigger.

Trigger freshness (the second fix): freshness is computed from
the trigger's age in bars against the registry TTL for its
family (sweep reclaim 3 bars, structural hold 4 bars, rotation
ignition 6 bars). A window flag on the trigger is ignored by
design: his code passed the observation window flag as the
freshness value and never consulted the TTLs. A trigger whose
age cannot be computed is freshness unknown, and unknown fails
closed: the name stays FORMING, never qualified.

Geometry is frozen to completed structure: support as supplied
from completed levels, entry zone support minus 0.12 ATR to
plus 0.45 ATR, invalidation support minus 0.7 ATR, chase line
support plus 1.2 ATR, risk floored at 0.25 ATR. The target is
structure bounded: the lower of the prior resistance and price
plus 3.2 ATR, never manufactured from a desired multiple.

Operational defaults fail closed: shadow_only is true when the
field is omitted, and a candidate that asks for more than
shadow without an explicit ORDER_AUTHORIZED authority is
forced back to shadow only. Execution eligibility requires
both: shadow_only explicitly false and that authority. This
desk and terminal are paper only regardless.

Out of hours degradation: when the session is not regular
(a missing session counts as not regular, fail closed), the
qualification itself is unchanged but an S tier displays as
A, a BUY NOW verdict degrades to WAIT, and the owner action
is suppressed to NO VIEW.

This module is pure: callers pass the current bar index and
every field in; nothing here reads a clock, a file or a
network, and absent inputs are never invented.
"""

import math

TRIGGER_TTLS = {"sweep_reclaim": 3, "structural_hold": 4,
                "rotation_ignition": 6}
MIN_DAILY_BARS = 80
MIN_INTRADAY_BARS = 3
MIN_MEDIAN_DOLLAR_VOLUME = 5_000_000
MIN_REWARD_TO_RISK = 1.25
TIER_REWARD_TO_RISK = 2.0
AUTHORITY_ORDER = "ORDER_AUTHORIZED"
TIERS = ("S", "A", "B", "FORMING", "AVOID", "NO_VIEW")


def _num(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    value = float(value)
    return value if math.isfinite(value) else None


def _r(value):
    return round(float(value), 6) if value is not None else None


def structure_bounded_target(price, resistance, atr):
    """The lower of prior resistance and price plus 3.2 ATR.

    Resistance may be None, in which case the ATR bound alone
    applies; qualification vetoes incomplete levels separately,
    so this helper never has to invent a resistance.
    """
    bound = float(price) + 3.2 * float(atr)
    if resistance is not None:
        bound = min(bound, float(resistance))
    return _r(bound)


def trigger_freshness(trigger, current_bar=None):
    """Freshness from trigger age against the registry TTL.

    Returns {state, family, age_bars, ttl_bars} with state one
    of fresh, expired, failed or unknown. The trigger's own
    in_window flag is never consulted.
    """
    if not isinstance(trigger, dict):
        return {"state": "unknown", "family": None,
                "age_bars": None, "ttl_bars": None}
    family = trigger.get("family") or trigger.get("type")
    ttl = TRIGGER_TTLS.get(family)
    state = str(trigger.get("state") or "").upper()
    if state in ("FAILED", "EXPIRED"):
        return {"state": "failed", "family": family,
                "age_bars": None, "ttl_bars": ttl}
    age = _num(trigger.get("age_bars"))
    if age is None:
        fired = _num(trigger.get("fired_bar"))
        if fired is None:
            fired = _num(trigger.get("bar_index"))
        if fired is not None and current_bar is not None:
            age = float(current_bar) - fired
    if age is None or age < 0 or ttl is None:
        return {"state": "unknown", "family": family,
                "age_bars": _r(age), "ttl_bars": ttl}
    return {"state": "fresh" if age <= ttl else "expired",
            "family": family, "age_bars": _r(age),
            "ttl_bars": ttl}


def compute_geometry(candidate):
    """Frozen geometry, or None when any level is missing."""
    price = _num(candidate.get("price"))
    support = _num(candidate.get("support"))
    atr = _num(candidate.get("atr"))
    resistance = _num(candidate.get("resistance"))
    if price is None or support is None or atr is None \
            or resistance is None or atr <= 0:
        return None
    invalidation = support - 0.7 * atr
    risk = max(price - invalidation, 0.25 * atr)
    target = structure_bounded_target(price, resistance, atr)
    reward = target - price
    return {
        "support": _r(support),
        "entry_zone": [_r(support - 0.12 * atr),
                       _r(support + 0.45 * atr)],
        "invalidation": _r(invalidation),
        "chase_line": _r(support + 1.2 * atr),
        "target": target,
        "risk_distance": _r(risk),
        "reward_to_risk": _r(reward / risk) if risk > 0 else None,
    }


def proof_display(candidate):
    """The proof state as a scanner surface may print it
    (DEEP-PASS 3.2 item 2): always provisional, because the
    Aperture proof gate manufactures the state from the name's
    own in sample history. A bare SUPPORTED is never a
    displayable string; the BH q-value travels with it when
    the gate supplied one."""
    state = str(candidate.get("proof_state") or "").upper()
    return {"state": state, "provisional": True,
            "display": f"PROVISIONAL {state}",
            "bh_q_value": candidate.get("proof_bh_q_value"),
            "episodes": candidate.get("proof_episodes")}


def exclusion_record(symbol, reasons):
    """One ledgered exclusion: a name is named with its reasons,
    never silently dropped."""
    return {"symbol": symbol, "stage": "exclusion",
            "tier": "NO_VIEW", "display_tier": "NO_VIEW",
            "verdict": "NO_VIEW", "owner_action": "NO_VIEW",
            "reasons": sorted(set(reasons)),
            "shadow_only": True, "execution_eligible": False,
            "degraded": False, "geometry": None}


def _operational(candidate):
    """Fail closed operational posture for one candidate."""
    shadow = candidate.get("shadow_only", True)
    shadow = True if shadow is None else bool(shadow)
    authority = candidate.get("authority")
    if not shadow and authority != AUTHORITY_ORDER:
        shadow = True  # stronger than shadow needs authority
    eligible = (not shadow) and authority == AUTHORITY_ORDER
    return shadow, eligible


def classify_candidate(candidate, current_bar=None):
    """Qualify one candidate. Always returns a decision dict;
    a name is never dropped and no score is ever produced."""
    if not isinstance(candidate, dict):
        return exclusion_record(None, ["candidate_not_a_mapping"])
    symbol = candidate.get("symbol")
    shadow, eligible = _operational(candidate)

    # Stage 1: data integrity stop, ledgered per name.
    reasons = []
    if candidate.get("provider_eligible") is False:
        reasons.append("provider_ineligible")
    for flag in candidate.get("quality_flags") or []:
        reasons.append(f"quality_flag:{flag}")
    daily = candidate.get("daily_bar_count")
    if daily is None:
        reasons.append("missing_daily_bar_count")
    elif not isinstance(daily, (int, float)) or daily < MIN_DAILY_BARS:
        reasons.append("insufficient_daily_bars")
    intraday = candidate.get("intraday_bar_count")
    if intraday is None:
        reasons.append("missing_intraday_bar_count")
    elif not isinstance(intraday, (int, float)) \
            or intraday < MIN_INTRADAY_BARS:
        reasons.append("insufficient_intraday_bars")
    if candidate.get("series_valid") is False:
        reasons.append("series_invalid")
    if candidate.get("last_intraday_bar_matches_expected") is False:
        reasons.append("last_intraday_bar_mismatch")
    if reasons:
        rec = exclusion_record(symbol, reasons)
        if candidate.get("proof_state"):
            rec["proof"] = proof_display(candidate)
        return rec

    def decision(stage, tier, verdict, why, geometry=None, fresh=None):
        degraded = candidate.get("session") != "regular"
        display = tier
        out_verdict = verdict
        owner = "HOLD" if tier in ("S", "A") else "NO_VIEW"
        if degraded:
            if display == "S":
                display = "A"
            if out_verdict == "BUY_NOW":
                out_verdict = "WAIT"
            owner = "NO_VIEW"
        out = {"symbol": symbol, "stage": stage, "tier": tier,
               "display_tier": display, "verdict": out_verdict,
               "owner_action": owner, "reasons": sorted(set(why)),
               "shadow_only": shadow,
               "execution_eligible": eligible,
               "degraded": bool(degraded), "geometry": geometry,
               "trigger_freshness": fresh}
        if candidate.get("proof_state"):
            out["proof"] = proof_display(candidate)
        return out

    # Stage 2: proof gate.
    proof = str(candidate.get("proof_state") or "").upper()
    if proof in ("QUARANTINED", "REJECTED"):
        return decision("proof_gate", "AVOID", "AVOID",
                        [f"proof_{proof.lower()}"])

    # Stage 3: hard vetoes.
    vetoes = []
    if str(candidate.get("anchor") or "").upper() == "HARD_AVOID":
        vetoes.append("anchor_hard_avoid")
    if str(candidate.get("formation") or "").lower() \
            in ("mature", "failed"):
        vetoes.append("formation_mature_or_failed")
    if candidate.get("headwind"):
        vetoes.append("headwind_topology")
    if candidate.get("distribution"):
        vetoes.append("distribution_participation")
    geometry = compute_geometry(candidate)
    price = _num(candidate.get("price"))
    if geometry is None:
        vetoes.append("incomplete_levels")
    else:
        if price > geometry["chase_line"]:
            vetoes.append("chase_line_breached")
        if price >= geometry["target"]:
            vetoes.append("target_already_traded")
        if geometry["reward_to_risk"] is not None \
                and geometry["reward_to_risk"] < MIN_REWARD_TO_RISK:
            vetoes.append("reward_to_risk_below_1_25")
        if price <= geometry["invalidation"]:
            vetoes.append("invalidation_breached")
    if price is not None and price < 1:
        vetoes.append("price_below_one_dollar")
    pct_low = _num(candidate.get("pct_above_60_low"))
    if pct_low is not None and pct_low > 0.25:
        vetoes.append("more_than_25pct_above_60_session_low")
    run10 = _num(candidate.get("run_10_pct"))
    if run10 is not None and run10 > 0.18:
        vetoes.append("ten_session_run_above_18pct")
    mdv = _num(candidate.get("median_dollar_volume"))
    if mdv is None:
        vetoes.append("missing_liquidity_evidence")
    elif mdv < MIN_MEDIAN_DOLLAR_VOLUME:
        vetoes.append("median_dollar_volume_below_5m")
    trigger = candidate.get("trigger")
    fresh = trigger_freshness(trigger, current_bar) \
        if isinstance(trigger, dict) else None
    if fresh is not None and fresh["state"] == "failed":
        vetoes.append("trigger_failed")
    elif fresh is not None and fresh["state"] == "expired":
        vetoes.append("trigger_expired")
    if vetoes:
        return decision("hard_veto", "AVOID", "AVOID", vetoes,
                        geometry, fresh)

    # Stage 4: trigger lifecycle.
    if not isinstance(trigger, dict):
        return decision("lifecycle", "FORMING", "WAIT",
                        ["no_trigger"], geometry, fresh)
    tstate = str(trigger.get("state") or "").upper()
    if tstate != "CONFIRMED":
        return decision("lifecycle", "FORMING", "WAIT",
                        ["trigger_not_confirmed"], geometry, fresh)
    if fresh is None or fresh["state"] != "fresh":
        return decision("lifecycle", "FORMING", "WAIT",
                        ["trigger_freshness_unprovable"],
                        geometry, fresh)

    # Stage 5: tier qualification, ordinal only.
    rr = geometry["reward_to_risk"]
    if rr >= TIER_REWARD_TO_RISK and fresh["age_bars"] <= 1:
        tier = "S"
    elif rr >= TIER_REWARD_TO_RISK:
        tier = "A"
    else:
        tier = "B"
    verdict = "BUY_NOW" if tier in ("S", "A") else "WAIT"
    return decision("tier_qualification", tier, verdict,
                    [f"tier_{tier.lower()}_qualified"], geometry, fresh)


def classify_candidates(candidates, current_bar=None):
    """Qualify a batch. Every input name yields exactly one
    output record; exclusions are listed separately with their
    reasons, and the tier counts always sum to the total."""
    decisions = [classify_candidate(c, current_bar)
                 for c in candidates]
    by_tier = {t: 0 for t in TIERS}
    for d in decisions:
        by_tier[d["tier"]] += 1
    return {"decisions": decisions,
            "exclusions": [d for d in decisions
                           if d["stage"] == "exclusion"],
            "counts": {"total": len(decisions), "by_tier": by_tier,
                       "excluded": sum(1 for d in decisions
                                       if d["stage"] == "exclusion")}}
