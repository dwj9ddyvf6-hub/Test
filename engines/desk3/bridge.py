"""v3 bridge: snapshot view -> v2 old-contract ctx -> v3 intent dicts.

Faithful port of the v2 _v2bridge profile (muse-desk-v2
adapters/_bridge.py): build_extra, old_context_v2, bars_v2, to_v2_intents
with _derive_side_v2/_derive_pi_v2. No strategy math lives here.
The view is the cycle snapshot data dict:
  {"now": iso, "bars": {"SYM|TF": [{t,o,h,l,c,v}]}, "extra": {...},
   "positions": [...], "slice": {...}, "kraken_inputs": {...},
   "options_chain": {UNDERLYING: payload}}
"""
from __future__ import annotations
from collections import namedtuple
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from desk3.contract import Context as OldContext

ET = ZoneInfo("America/New_York")
PI_SIDE = {"buy_to_open": "buy", "buy_to_close": "buy",
           "sell_to_open": "sell", "sell_to_close": "sell"}
Bar = namedtuple("Bar", "t o h l c v")


def _epoch(ts):
    d = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.timestamp()


class ViewCtx:
    """Shim exposing the v2 ctx surface over a snapshot view."""

    def __init__(self, view, ctx):
        view = view or {}
        self._view = view
        now = view.get("now") or (ctx or {}).get("now")
        self.now = (datetime.fromisoformat(str(now).replace("Z", "+00:00"))
                    if now else datetime.now(timezone.utc))
        if self.now.tzinfo is None:
            self.now = self.now.replace(tzinfo=timezone.utc)
        self.sleeve_id = (ctx or {}).get("sleeve_id")
        self.positions = view.get("positions") or []
        self.slice = view.get("slice") or {"capital_usd": 10000.0,
                                           "cash_usd": 10000.0}
        self.params = {"extra": view.get("extra") or {}}
        if view.get("params"):
            self.params.update(view["params"])
        self.logs = []

    def bars(self, symbol, tf, n):
        rows = (self._view.get("bars") or {}).get(f"{symbol}|{tf}") or []
        return [Bar(r["t"], r["o"], r["h"], r["l"], r["c"], r["v"])
                for r in rows[-n:]]

    def options_chain(self, underlying):
        return (self._view.get("options_chain") or {}).get(underlying)

    def kraken_inputs(self):
        return self._view.get("kraken_inputs") or {}

    def log(self, event, **fields):
        self.logs.append((event, fields))


def build_extra(ctx):
    """_v2bridge profile, verbatim semantics from v2 _bridge.build_extra
    (journal last_exit_date channel omitted: v3 journals are per-sleeve
    files read by the cycle, not the adapter)."""
    params = ctx.params or {}
    extra = dict(params.get("extra") or {})
    if ctx.positions:
        flat, nested = {}, {}
        for p in ctx.positions:
            flat[p["symbol"]] = {"qty": p["qty"],
                                 "entry_due_at": p.get("opened_at")}
            _oa = p.get("opened_at")
            nested[p["symbol"]] = {"position": {
                "qty": p["qty"], "entry_px": p.get("avg_price"),
                "entry_date": str(_oa or "")[:10],
                "entry_time": _oa, "entry_due_at": _oa}}
        extra.setdefault("sleeve_state", nested)
        extra.setdefault("sleeve_state_flat", flat)
        for p in ctx.positions:
            extra.setdefault("held_qty", p["qty"])
            extra.setdefault("entry_close_at", p.get("opened_at"))
    if "cash" not in extra and ctx.slice:
        extra["cash"] = ctx.slice.get("cash_usd")
    if "session_dates" not in extra:
        try:
            _sb = ctx.bars("SPY", "1Day", 600) or []
            if _sb:
                extra["session_dates"] = sorted({str(b.t)[:10] for b in _sb})
        except Exception:
            pass
    return extra


def old_bars(ctx, symbol, tf, n=2000):
    """bars_v2 profile: cast=False (raw values), epoch naive=utc."""
    return [{"t": _epoch(b.t), "o": b.o, "h": b.h, "l": b.l, "c": b.c,
             "v": b.v} for b in (ctx.bars(symbol, tf, n) or [])]


def old_context(ctx, extra):
    now = ctx.now
    if now.tzinfo is None:
        now = now.replace(tzinfo=ET)
    return OldContext(now=now.timestamp(),
                      session=now.astimezone(ET).date().isoformat(),
                      equity=float((ctx.slice or {}).get("capital_usd") or 0),
                      account_equity=None, extra=extra)


def _derive_side(oi):
    if oi.side:
        return oi.side
    if oi.position_intent:
        return PI_SIDE[oi.position_intent]
    reason = oi.reason or ""
    for pi in ("sell_to_open", "buy_to_close", "sell_to_close", "buy_to_open"):
        if pi in reason:
            return PI_SIDE[pi]
    if oi.kind == "exit" and "cover" in reason:
        return "buy"
    if "SHORT" in reason:
        return "sell"
    return "buy" if oi.kind == "enter" else "sell"


def _derive_pi(oi):
    if oi.position_intent:
        return oi.position_intent
    reason = oi.reason or ""
    for pi in ("buy_to_open", "sell_to_open", "sell_to_close", "buy_to_close"):
        if pi in reason:
            return pi
    if oi.kind == "exit":
        return "sell_to_close" if _derive_side(oi) == "sell" else "buy_to_close"
    return None


def to_v2_intents(ctx, sleeve_id, old_intents):
    stamp = ctx.now.strftime("%Y%m%dT%H%M%S")
    out = []
    for i, oi in enumerate(old_intents, 1):
        qty = oi.qty if oi.qty is not None else oi.qty_hint
        intent = {"intent_id": f"{sleeve_id}-{stamp}-{i}",
                  "kind": "entry" if oi.kind == "enter" else "exit",
                  "symbol": oi.symbol, "side": _derive_side(oi),
                  "qty": qty, "reason": oi.reason or sleeve_id,
                  "time_in_force": "day"}
        if oi.limit_price is not None:
            intent["order_type"] = "limit"
            intent["limit_price"] = float(oi.limit_price)
        else:
            intent["order_type"] = "market"
        if oi.stop is not None:
            intent["stop_price"] = float(oi.stop)
        if getattr(oi, "price_hint", None):
            intent["price_hint"] = float(oi.price_hint)
        if getattr(oi, "exit_rules", None):
            intent["exit_rules"] = [{"kind": r.kind, "value": float(r.value)}
                                    for r in oi.exit_rules]
        pi = _derive_pi(oi)
        if pi:
            intent["position_intent"] = pi
        if getattr(oi, "legs", None):
            intent["legs"] = [dict(leg) for leg in oi.legs]
        if getattr(oi, "package_id", None):
            intent["package_id"] = oi.package_id
        out.append(intent)
    return out
