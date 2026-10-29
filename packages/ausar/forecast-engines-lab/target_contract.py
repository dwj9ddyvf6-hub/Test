"""Stable identity for the intended target semantics of a forecast engine."""

from __future__ import annotations

from functools import lru_cache
import hashlib
import json
from typing import Any

from .catalog import EngineSpec, get_engine
from .edge_cards import get_edge_card
from .label_context import LABEL_CONTEXT_FIELDS, LABEL_CONTEXT_SCHEMA


TARGET_CONTRACT_SCHEMA = "forecast-target-contract-v3"


def _label(
    label_kind: str,
    definition: str,
    windows: tuple[str, ...],
    *,
    status: str = "labelable",
    excluded: str = "Secondary outcomes described in the Edge card are not part of this label.",
) -> dict[str, Any]:
    return {
        "label_kind": label_kind,
        "label_definition": definition,
        "allowed_window_ids": list(windows),
        "status": status,
        "excluded_secondary_outcomes": excluded,
    }


# One primary scalar estimand per emitted forecast. Secondary card ideas are
# retained as research context but cannot silently become alternate labels.
TARGET_LABEL_CONTRACTS: dict[str, dict[str, Any]] = {
    "FE01": _label("continuous", "Benchmark-adjusted return from as_of to the selected fixed session close.", ("5-session", "10-session", "20-session"), excluded="First-hit barrier events are separate labels and are excluded."),
    "FE02": _label("continuous", "Residual spread return from as_of to the selected fixed session close.", ("1-session", "3-session", "5-session"), excluded="Spread half-life and convergence-before-break are separate event labels."),
    "FE03": _label("continuous", "Underlying return from the pre-cutoff breakout reference to the selected fixed session close.", ("1-session", "3-session", "5-session"), excluded="Breakout acceptance and failed-reclaim events are not pooled into the return label."),
    "FE04": _label("continuous", "Opening-gap residual return from the declared open reference to the selected intraday/session endpoint.", ("30-minute", "regular-close", "next-session-close"), excluded="Auction-open and regular-open references must use distinct forecast requests."),
    "FE05": _label("continuous", "Index return relative to the predeclared market benchmark from as_of to the selected fixed session close.", ("1-session", "3-session", "5-session")),
    "FE06": _label("continuous", "Sector return relative to the predeclared benchmark from as_of to the selected fixed session close.", ("5-session", "10-session", "20-session"), excluded="Leadership handoff is a separate event label."),
    "FE07": _label("continuous", "Follower residual return at the single selected lag endpoint, using a predeclared leader/follower pair.", ("1-minute", "5-minute", "30-minute", "1-session", "5-session"), excluded="Edge half-life and sign-flip hazard are separate labels."),
    "FE08": _label("variance", "Realized variance accumulated over the selected fixed session window, with a frozen sampling and adjustment rule.", ("1-session", "3-session", "5-session")),
    "FE09": _label("binary", "One if absolute return exceeds the predeclared volatility-scaled barrier by the selected window end; otherwise zero.", ("1-session", "3-session", "5-session"), excluded="Absolute-move and downside-gap events must not be conflated; downside risk requires its own contract."),
    "FE10": _label("binary", "One if the predeclared volatility/correlation regime transition occurs by the selected window end; otherwise zero.", ("5-session", "10-session", "20-session"), excluded="Transition direction and variance/correlation component labels are separate."),
    "FE11": _label("continuous", "Close-to-next-open return for the declared instrument and venue session.", ("next-open",)),
    "FE12": _label("binary", "One if depth remains impaired or spread remains outside the predeclared band by the selected endpoint; otherwise zero.", ("30-minute", "regular-close", "next-session-close")),
    "FE13": _label("continuous", "Midquote return from the first eligible post-signal quote to the selected fixed elapsed-time endpoint.", ("10-second", "1-minute", "5-minute", "30-minute"), excluded="Trade-price markouts and quote-mid markouts are separate label contracts."),
    "FE14": _label("binary", "One if the underlying realizes the predeclared left-tail barrier within the selected window; otherwise zero.", ("1-session", "5-session", "20-session"), excluded="Risk-neutral skew, implied variance, event frequency, and loss magnitude are not this per-forecast binary label."),
    "FE15": _label("scenario_only", "Conditional price/hedge-flow sensitivity under a caller-specified spot path; no unconditional realized outcome label is defined.", (), status="scenario_only", excluded="Do not score as a realized return forecast unless a scenario-path identity and outcome mapping are added."),
    "FE16": _label("continuous", "Underlying residual return from the classified flow event to the selected fixed endpoint.", ("30-minute", "1-session", "5-session"), excluded="Trade classification confidence is conditioning metadata, not a second outcome."),
    "FE17": _label("continuous", "Absolute underlying return from the timestamped earnings release to the selected next-session close.", ("next-session-close",), excluded="Implied-move surprise is a derived comparison, not the realized target."),
    "FE18": _label("continuous", "Sector-residual return from the first executable post-release open to the selected fixed session close.", ("5-session", "10-session", "20-session")),
    "FE19": _label("continuous", "Issuer return less the frozen sector/market benchmark from revision availability to the selected fixed session close.", ("20-session", "40-session", "60-session"), excluded="Revision-dispersion change is a separate fundamental outcome."),
    "FE20": _label("continuous", "Next-period fundamental surprise z-score using the frozen consensus vintage and standardization population.", ("1-month", "2-month", "3-month")),
    "FE21": _label("continuous", "Change in cash-conversion measure between the frozen accession vintage and the next comparable filing.", ("next-comparable-filing",), excluded="Forward quality classifications are separate labels."),
    "FE22": _label("continuous", "Parser-normalized disclosure delta in the same predeclared filing section/type at the next comparable filing.", ("next-comparable-filing",), excluded="Event-level and next-filing labels are not pooled; this contract selects next comparable filing."),
    "FE23": _label("continuous", "Issuer residual return from filing availability to the selected fixed session close.", ("20-session", "40-session", "60-session")),
    "FE24": _label("binary", "One if the predeclared crowded-position unwind event occurs by the selected quarter end; otherwise zero.", ("1-quarter", "2-quarter", "3-quarter"), excluded="Illiquidity is a separate outcome and must not be folded into the unwind label."),
    "FE25": _label("continuous", "Issuer residual return from buyback-report availability to the selected fixed session close, conditional on verified executed pace.", ("5-session", "10-session", "20-session"), excluded="Causal price-support contribution is not observable from a forward-return label."),
    "FE26": _label("continuous", "Constituent return relative to the frozen index benchmark from announcement to the selected effective-date close.", ("effective-close",), excluded="Post-effective reversal is a separate label."),
    "FE27": _label("continuous", "Return of the declared cross-asset instrument from the first executable post-release mark to 30 minutes after release.", ("30-minute-post-release",), excluded="Variance response and longer horizons are separate target contracts."),
    "FE28": _label("binary", "One if the predeclared market-stress transition criterion is met by the selected quarter end; otherwise zero.", ("1-quarter", "2-quarter", "4-quarter"), excluded="Recession dating is a separate outcome."),
    "FE29": _label("continuous", "Commodity excess return from the selected publication-time reference to the fixed week endpoint.", ("1-week", "4-week", "8-week"), excluded="Tail-event labels and COT/inventory event-window reactions are separate."),
    "FE30": _label("binary", "One if a venue-specific liquidation/depth squeeze event occurs by the selected endpoint; otherwise zero.", ("1-minute", "5-minute", "30-minute", "1-session", "5-session"), excluded="Conditional markout is a separate return label."),
}


def target_label_contract(engine_id: str) -> dict[str, Any]:
    """Return a defensive copy of the primary outcome-label contract."""
    contract = TARGET_LABEL_CONTRACTS[engine_id]
    return {**contract, "allowed_window_ids": list(contract["allowed_window_ids"])}


def target_contract_payload(engine_id: str) -> dict[str, Any]:
    """Return the frozen semantic contract, separate from model implementation code."""
    spec: EngineSpec = get_engine(engine_id)
    card = get_edge_card(engine_id)
    return {
        "schema": TARGET_CONTRACT_SCHEMA,
        "engine_id": spec.engine_id,
        "target": spec.target,
        "target_unit": spec.target_unit,
        "horizon": spec.horizon,
        "forecast_unit": spec.forecast_unit,
        "score_kind": spec.score_kind,
        "target_definition": card.target_definition.strip(),
        "label_contract": target_label_contract(engine_id),
        "label_context_schema": LABEL_CONTEXT_SCHEMA,
        "label_context_fields": list(LABEL_CONTEXT_FIELDS),
    }


@lru_cache(maxsize=None)
def target_contract_fingerprint(engine_id: str) -> str:
    """Hash the exact target definition and typed forecast/outcome coordinates."""
    canonical = json.dumps(
        target_contract_payload(engine_id),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()
