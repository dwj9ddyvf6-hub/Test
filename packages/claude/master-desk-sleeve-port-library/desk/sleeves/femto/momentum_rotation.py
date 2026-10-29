"""Momentum Rotation — lean-desk port.

EXTRACTED from the old desk's momentum_rotation_sleeve.py.
momentum_60d / compute_ranks ported verbatim; plumbing is core-owned.
See ports/momentum_rotation.md.

Strategy (old module): rank the universe by 60-day total return;
hold the top 5 at 20% equal weight; at the weekly (7-day) rebalance,
sell held positions ranked worse than 10; -25% GTC disaster stop
below entry (desk norm #18).

Inputs via context.extra:
  "sleeve_state": {SYM: {"position": {"entry_px","entry_date","qty"} | None}}
  "last_rebalance": "YYYY-MM-DD" | None (core-persisted sleeve meta)
  "universe": optional override (default: bars keys)
Bars: daily dicts {"t","o","h","l","c","v"} ascending.
"""
from datetime import date, datetime, timezone

from .compat import BaseSleeve, ExitRule, Intent, SleeveConfig

MOMENTUM_DAYS = 60
TOP_HOLD = 5
SELL_RANK_CUTOFF = 10
REBALANCE_DAYS = 7
TARGET_WEIGHT = 0.20
DISASTER_STOP = 0.25
WARMUP_BARS = MOMENTUM_DAYS + 5

CONFIG = SleeveConfig(
    sleeve_id="momentum_rotation", cadence_s=300, universe=(),
    state_schema={"position": "dict|None", "meta.last_rebalance": "str|None"},
    risk_pct=None)


def _dates(bars):
    return [datetime.fromtimestamp(float(b["t"]) + 4 * 3600,
                                   tz=timezone.utc).date().isoformat()
            for b in bars]


def momentum_60d(bars):
    """60-day total return from closed bars; None when insufficient."""
    if not bars or len(bars) < MOMENTUM_DAYS + 1:
        return None
    try:
        c0 = float(bars[-(MOMENTUM_DAYS + 1)]["c"])
        c1 = float(bars[-1]["c"])
        if c0 <= 0:
            return None
        return c1 / c0 - 1
    except (TypeError, ValueError, KeyError):
        return None


def compute_ranks(bars_map):
    """{sym: (rank, momentum)} sorted by momentum desc; rank 1-based.
    Verbatim port of the old compute_ranks."""
    scored = []
    for sym, bl in bars_map.items():
        m = momentum_60d(bl)
        if m is not None:
            scored.append((sym, m))
    scored.sort(key=lambda t: t[1], reverse=True)
    return {sym: (i + 1, m) for i, (sym, m) in enumerate(scored)}


def rebalance_due(last_rebalance_iso, today_iso):
    """Weekly cadence: >= REBALANCE_DAYS calendar days since the last
    rebalance (the old runner fired on its weekly cron; the date math
    here is the sleeve-visible rule)."""
    if not last_rebalance_iso:
        return True
    try:
        d = (date.fromisoformat(today_iso)
             - date.fromisoformat(str(last_rebalance_iso)[:10])).days
    except ValueError:
        return True
    return d >= REBALANCE_DAYS


class MomentumRotation(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        extra = context.extra or {}
        state = extra.get("sleeve_state") or {}
        equity = float(context.equity or 0.0)
        today = context.session
        if equity <= 0:
            return []
        if not rebalance_due(extra.get("last_rebalance"), today):
            return []
        # master-desk: the old daily_pass keeps only symbols with > WARMUP_BARS bars in bars_map
        bars = {s: bl for s, bl in bars.items() if bl and len(bl) >= WARMUP_BARS + 1}
        ranks = compute_ranks(bars)
        if not ranks:
            return []
        intents = []
        held = {s: (state.get(s) or {}).get("position")
                for s in ranks if (state.get(s) or {}).get("position")}
        # sells: held ranked worse than the cutoff (or unranked)
        for sym, p in held.items():
            r = ranks.get(sym)
            if r is None:
                continue        # master-desk: old rebalance_hold_unranked — no 60d momentum, hold fail-closed
            if r[0] > SELL_RANK_CUTOFF:
                qty = int(float(p.get("qty") or 0))
                if qty > 0:
                    intents.append(Intent(
                        "exit", sym, qty_hint=qty,
                        price_hint=round(float(bars[sym][-1]["c"]), 2),
                        reason="rotation rebalance: rank=%s > %d"
                               % (None if r is None else r[0], SELL_RANK_CUTOFF)))
        # buys: top-5 not held, sized to the 20% target weight
        top = [s for s, (rk, _m) in sorted(ranks.items(), key=lambda kv: kv[1][0])
               if rk <= TOP_HOLD]
        # master-desk: old capacity rule — positions + pending entries (sold-this-pass still count) >= 5 stops buying
        committed = sum(1 for v in state.values() if isinstance(v, dict)
                        and (v.get("position") or v.get("pending_entry")))
        for sym in top:
            if sym in held:
                continue
            if committed >= TOP_HOLD:
                break
            if (state.get(sym) or {}).get("position") or (state.get(sym) or {}).get("pending_entry"):
                continue
            px = float(bars[sym][-1]["c"])
            if px <= 0:
                continue
            qty = int((equity * TARGET_WEIGHT) / px)
            if qty < 1:
                continue
            committed += 1
            stop_px = round(px * (1 - DISASTER_STOP), 2)
            intents.append(Intent(
                "enter", sym, qty_hint=qty, price_hint=round(px, 2),
                stop=stop_px, exit_rules=(ExitRule("stop", stop_px),),
                reason="rotation rebalance: rank=%d mom60=%.4f target_wt=%.2f"
                       % (ranks[sym][0], ranks[sym][1], TARGET_WEIGHT)))
        return intents


def signal(bars, slice_state, context):
    return MomentumRotation().signal(bars, slice_state, context)
