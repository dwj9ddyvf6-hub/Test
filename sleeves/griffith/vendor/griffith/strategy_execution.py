"""Execution overlays and portfolio allocator for the three-strategy desk."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone, time as wall_time
from typing import Any
from zoneinfo import ZoneInfo

from strategy_system import StrategyDecision, content_hash


@dataclass(frozen=True)
class ExecutionPlan:
    planId: str
    decisionId: str
    strategyId: str
    overlayVersion: str
    symbol: str
    state: str
    orderType: str
    triggerPrice: float | None
    limitPrice: float
    stopPrice: float
    targetPrice: float | None
    riskPerShare: float
    expiresAt: str
    extendedHours: bool
    strategyRiskFraction: float
    reasonCodes: tuple[str, ...] = ()


@dataclass(frozen=True)
class Allocation:
    allocationId: str
    planId: str
    authorizedQuantity: int
    reservedRisk: float
    reservedNotional: float
    ownerStrategy: str
    collisionState: str
    correlationMultiplier: float = 1.0
    reasonCodes: tuple[str, ...] = ()


class ExecutionOverlays:
    ET = ZoneInfo("America/New_York")

    @classmethod
    def _location_first_expiry(cls, now: datetime) -> datetime:
        """Keep a premarket LF handoff alive until the next regular open."""
        local = now.astimezone(cls.ET)
        regular_open = local.replace(hour=9, minute=30, second=0, microsecond=0)
        if local.time() < wall_time(9, 30):
            return regular_open.astimezone(timezone.utc)
        return now + timedelta(minutes=30)

    def build(
        self,
        decision: StrategyDecision,
        ask: float,
        equity: float,
        *,
        clock: datetime | None = None,
        allow_conditional_wait: bool = False,
        conditional_min_score: float = 70.0,
        conditional_engines: set[str] | None = None,
        conditional_versions: set[str] | None = None,
        conditional_risk_fraction: float = 0.005,
    ) -> ExecutionPlan | None:
        if ask <= 0 or equity <= 0:
            return None
        metrics = decision.metrics
        now = (clock or datetime.now(timezone.utc)).astimezone(timezone.utc)
        if decision.strategyId == "LEADERS_REST" and decision.status == "SETUP":
            atr_entry = max(float(metrics.get("atr14") or 0), 0.015 * float(decision.entryReference or ask))
            if atr_entry <= 0:
                return None
            limit_price = min(ask, float(decision.entryReference) + 0.10 * atr_entry)
            stop = limit_price - 1.6 * atr_entry
            target = limit_price + 2.8 * atr_entry
            return self._plan(decision, "LRX_1_0_0", "limit", None, limit_price, stop, target, 1.6 * atr_entry, now + timedelta(days=5), False, 0.005, ["NEXT_REGULAR_SESSION"])
        if decision.strategyId == "foliotend-location-first-swing" and decision.status == "BUY":
            support = float(metrics.get("support") or 0)
            stop = float(metrics.get("stop") or 0)
            target = float(metrics.get("target") or 0) or None
            limit_price = min(ask, 1.03 * support)
            risk = limit_price - stop
            if support <= 0 or risk <= 0:
                return None
            risk_fraction = 0.005 if decision.setupClass == "S" else 0.0025
            return self._plan(decision, "LFX_1_0_0", "limit", None, limit_price, stop, target, risk, self._location_first_expiry(now), True, risk_fraction, ["FRESH_15M_TRIGGER"])
        if decision.strategyId == "PARALLAX":
            # The conditional lane is an execution experiment only.  It does
            # not rewrite the immutable strategy decision; it arms a
            # trigger-defined paper order for a strong WAIT and records that
            # promotion explicitly in the plan reason codes.  Version and
            # engine allowlists keep this from becoming an accidental blanket
            # override of the research gates.
            conditional = (
                decision.status == "WAIT"
                and allow_conditional_wait
                and float(decision.score or 0) >= float(conditional_min_score)
                and str(decision.engine or "") in (conditional_engines or {"COMPRESSION", "DRIFT", "RECLAIM", "DISLOCATION"})
                and (conditional_versions is None or decision.scannerVersion in conditional_versions)
            )
            if decision.status != "BUY" and not conditional:
                return None
            price, atr = float(decision.entryReference or ask), float(metrics.get("atrPct") or 0) * float(decision.entryReference or ask) / 100
            engine = decision.engine
            if atr <= 0:
                return None
            if conditional:
                # Conditional orders are deliberately non-marketable: price
                # must prove the move after the completed-bar decision before
                # the paper broker can fill the bracket.
                min_gap = max(0.001 * price, 0.10 * atr)
                if engine == "COMPRESSION":
                    prior_high = float(metrics.get("high20") or price)
                    trigger, limit_price = prior_high + max(0.05 * atr, min_gap), prior_high + 0.20 * atr
                    stop = float(metrics.get("compressionLow") or (price - 1.5 * atr)) - 0.25 * atr
                    expiry = now + timedelta(days=5)
                elif engine == "RECLAIM":
                    trigger, limit_price = price + max(0.25 * atr, min_gap), price + 0.35 * atr
                    stop, expiry = price - 1.25 * atr, now + timedelta(days=3)
                elif engine == "DISLOCATION":
                    trigger, limit_price = price + max(0.35 * atr, min_gap), price + 0.45 * atr
                    stop, expiry = price - 1.50 * atr, now + timedelta(days=3)
                else:  # DRIFT
                    trigger, limit_price = price + max(0.20 * atr, min_gap), price + 0.30 * atr
                    stop, expiry = price - 1.50 * atr, now + timedelta(days=3)
                # Do not submit a conditional order that is already crossed
                # by the freshest quote; wait for a new completed-bar
                # decision/trigger instead of converting it into a market
                # chase.  Keep the limit above the trigger after this clamp.
                trigger = max(trigger, ask + min_gap)
                limit_price = max(limit_price, trigger + 0.10 * atr)
                risk = limit_price - stop
                if not (stop > 0 and risk > 0 and trigger > ask and limit_price >= trigger):
                    return None
                target = limit_price + 2.5 * risk
                return self._plan(
                    decision, "PXE_1_1_0_AGGRESSIVE_PAPER", "stop_limit", trigger,
                    limit_price, stop, target, risk, expiry, False,
                    max(0.0001, float(conditional_risk_fraction)),
                    [
                        f"{engine}_CONDITIONAL_PAPER",
                        "AUTHORIZED_PAPER_CONDITIONAL_WAIT",
                        "COMPLETED_BAR_EVIDENCE_ONLY",
                    ],
                )
            if engine == "COMPRESSION":
                prior_high = float(metrics.get("high20") or price)
                trigger, limit_price = prior_high + 0.05 * atr, prior_high + 0.20 * atr
                stop = float(metrics.get("compressionLow") or (price - 1.5 * atr)) - 0.25 * atr
                target, expiry = limit_price + 2.5 * (limit_price - stop), now + timedelta(days=7)
                order_type = "stop_limit"
            elif engine == "DRIFT":
                trigger, limit_price, stop, target, expiry, order_type = None, min(ask, price + 0.10 * atr), price - 1.5 * atr, price + 2.5 * atr, now + timedelta(days=2), "limit"
            elif engine == "RECLAIM":
                trigger, limit_price, stop, target, expiry, order_type = None, min(ask, price + 0.10 * atr), price - 1.25 * atr, price + 2.25 * atr, now + timedelta(days=2), "limit"
            else:
                trigger, limit_price, stop, target, expiry, order_type = None, min(ask, price + 0.10 * atr), price - 1.5 * atr, price + 2.25 * atr, now + timedelta(days=2), "limit"
            return self._plan(decision, "PXE_1_0_0", order_type, trigger, limit_price, stop, target, limit_price - stop, expiry, False, 0.0035, [f"{engine}_OVERLAY"])
        if decision.strategyId == "TENSOR_PHENOTYPE_EXPERIMENTAL" and decision.status == "BUY":
            if not ((metrics.get("qualified") is True and metrics.get("qualificationState") == "QUALIFIED") or metrics.get("paperExperimentAuthorized") is True):
                return None
            trigger = float(metrics.get("triggerPrice") or 0)
            ceiling = float(metrics.get("limitPrice") or decision.entryReference or 0)
            stop = float(metrics.get("initialStop") or decision.invalidationReference or 0)
            target = float(metrics.get("target") or 0)
            if not (trigger > 0 and stop > 0 and stop < trigger <= ceiling < target):
                return None
            # If price has already crossed the trigger but remains inside the frozen
            # slippage ceiling, use a marketable limit; otherwise arm a stop-limit.
            crossed = ask >= trigger
            if crossed and ask > ceiling:
                return None
            order_type = "limit" if crossed else "stop_limit"
            limit_price = ask if crossed else ceiling
            expiry_days = max(1, min(28, int(metrics.get("entryWindowDays") or 28)))
            return self._plan(
                decision, "TENSORX_1_0_0", order_type, None if crossed else trigger,
                limit_price, stop, target, limit_price - stop, now + timedelta(days=expiry_days),
                False, 0.010, ["AUTHORIZED_PAPER_EXPERIMENT" if metrics.get("paperExperimentAuthorized") else "T4_QUALIFIED_EXPERIMENTAL", "HIGH_BREAK_4", str(metrics.get("policyId") or "FROZEN_TENSOR_POLICY")],
            )
        return None

    def _plan(self, decision: StrategyDecision, overlay: str, order_type: str, trigger: float | None, limit_price: float, stop: float, target: float | None, risk: float, expiry: datetime, extended: bool, risk_fraction: float, reasons: list[str]) -> ExecutionPlan:
        raw = {"decision": decision.decisionId, "overlay": overlay, "limit": limit_price, "stop": stop, "target": target}
        return ExecutionPlan(
            planId=f"{overlay}:{decision.symbol}:{content_hash(raw)[:16]}", decisionId=decision.decisionId,
            strategyId=decision.strategyId, overlayVersion=overlay, symbol=decision.symbol,
            state="ARMED", orderType=order_type, triggerPrice=trigger,
            limitPrice=round(limit_price, 2), stopPrice=round(stop, 2),
            targetPrice=round(target, 2) if target else None, riskPerShare=risk,
            expiresAt=expiry.isoformat(), extendedHours=extended,
            strategyRiskFraction=risk_fraction, reasonCodes=tuple(reasons),
        )


class PortfolioAllocator:
    STRATEGY_CAPS = {"PARALLAX": 0.008, "LEADERS_REST": 0.010, "foliotend-location-first-swing": 0.006, "TENSOR_PHENOTYPE_EXPERIMENTAL": 0.020}

    def __init__(self, profile: dict[str, Any] | None = None) -> None:
        profile = profile or {}
        self.total_risk_fraction = float(profile.get("total_risk_fraction", 0.02))
        self.symbol_risk_fraction = float(profile.get("symbol_risk_fraction", 0.006))
        self.sector_risk_fraction = float(profile.get("sector_risk_fraction", 0.0075))
        self.gross_notional_fraction = float(profile.get("gross_notional_fraction", 0.85))
        self.per_order_notional_fraction = float(profile.get("per_order_notional_fraction", 0.15))
        self.strategy_caps = {**self.STRATEGY_CAPS, **{str(k): float(v) for k, v in (profile.get("strategy_caps") or {}).items()}}

    def allocate(self, plan: ExecutionPlan, equity: float, buying_power: float, *, open_risk: float, strategy_risk: float, symbol_risk: float, sector_risk: float, gross_notional: float, existing_owner: str | None = None, max_order_notional: float | None = None, admission_allowed: bool = True, correlation_multiplier: float = 1.0) -> Allocation:
        reasons: list[str] = []
        collision = "NONE"
        if existing_owner and existing_owner != plan.strategyId:
            collision = "SHADOW_REJECTED"
            reasons.append("SAME_SYMBOL_OWNED_BY_OTHER_STRATEGY")
        if not admission_allowed:
            collision = "RISK_TRUTH_BLOCKED"
            reasons.append("PORTFOLIO_RISK_EVIDENCE_INCOMPLETE")
        correlation_multiplier = max(1.0, float(correlation_multiplier))
        if correlation_multiplier > 1.000001:
            reasons.append("POSITIVE_CORRELATION_RISK_ADJUSTMENT")
        risk_budget = min(
            plan.strategyRiskFraction * equity,
            max(0, self.total_risk_fraction * equity - open_risk),
            max(0, self.strategy_caps.get(plan.strategyId, self.STRATEGY_CAPS.get(plan.strategyId, 0.0)) * equity - strategy_risk),
            max(0, self.symbol_risk_fraction * equity - symbol_risk),
            max(0, self.sector_risk_fraction * equity - sector_risk),
        )
        notional_budget = min(
            max(0, self.gross_notional_fraction * equity - gross_notional), self.per_order_notional_fraction * equity,
            0.98 * buying_power,
        )
        if max_order_notional is not None:
            notional_budget = min(notional_budget, max(0, float(max_order_notional)))
        adjusted_risk_per_share = plan.riskPerShare * correlation_multiplier
        quantity = 0 if collision in {"SHADOW_REJECTED", "RISK_TRUTH_BLOCKED"} or adjusted_risk_per_share <= 0 else max(0, min(math.floor(risk_budget / adjusted_risk_per_share), math.floor(notional_budget / plan.limitPrice)))
        if quantity == 0 and not reasons:
            reasons.append("NO_AVAILABLE_RISK_OR_NOTIONAL")
        if quantity > 0:
            collision = "OWNER" if not existing_owner else "ADD_AUTHORIZED"
        raw = {"plan": plan.planId, "quantity": quantity, "owner": plan.strategyId, "correlationMultiplier": round(correlation_multiplier, 8)}
        return Allocation(
            allocationId=f"allocation:{content_hash(raw)[:20]}", planId=plan.planId,
            authorizedQuantity=quantity, reservedRisk=quantity * plan.riskPerShare,
            reservedNotional=quantity * plan.limitPrice, ownerStrategy=plan.strategyId,
            collisionState=collision, correlationMultiplier=round(correlation_multiplier, 8), reasonCodes=tuple(reasons),
        )
