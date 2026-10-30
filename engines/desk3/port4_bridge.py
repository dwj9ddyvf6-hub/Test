"""Canonical v2<->old-contract bridge (D9 cure, AUDIT-CURE-2).

Single implementation of everything the four historical bridge modules
(adapters/_common.py, _batch5_common.py, _v2bridge.py, _old_bridge.py)
duplicated: ISO->epoch conversion, Bar->bar-dict conversion,
sleeve-state-from-positions, old-context construction, and old Intent
-> v2 intent-dict translation. Those modules are now thin re-export
shims over this file; no adapter imports change.

The batches' contracts genuinely differ (naive-timestamp timezone,
state-record fields, fractional-qty handling, reason-string parsing),
so each differing behavior lives here ONCE as an explicit profile /
parameter — never as a copy. No strategy math lives here.
"""
from __future__ import annotations

import importlib
import os
import re
import sys
from datetime import datetime, timezone
from functools import partial
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from desk3.vendor.core.sleeve import Context as CoreContext  # noqa: E402

ET = ZoneInfo("America/New_York")

PI_SIDE = {"buy_to_open": "buy", "buy_to_close": "buy",
           "sell_to_open": "sell", "sell_to_close": "sell"}

CANDIDATES = [
    "SPY", "QQQ", "AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "GOOG",
    "AVGO", "JPM", "XOM", "UNH", "V", "MA", "HD", "PG", "COST", "NFLX",
    "AMD", "CRM", "BAC", "WMT", "LLY", "ORCL", "TSLA", "INTC", "CSCO",
    "PEP", "KO",
]

# ---------------------------------------------------------------- epoch
def epoch(ts, *, naive="utc", on_error="raise"):
    """ISO timestamp -> epoch seconds. `naive`: tz attached when the
    string carries none ("utc" | "et" | "local" = leave naive, the
    interpreter's local tz applies). `on_error`: "raise" | "zero"
    (ValueError -> 0.0) | "zero_any" (any error -> 0.0)."""
    try:
        d = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        if d.tzinfo is None:
            if naive == "utc":
                d = d.replace(tzinfo=timezone.utc)
            elif naive == "et":
                d = d.replace(tzinfo=ET)
        return d.timestamp()
    except ValueError:
        if on_error in ("zero", "zero_any"):
            return 0.0
        raise
    except Exception:
        if on_error == "zero_any":
            return 0.0
        raise


epoch_common = partial(epoch, naive="utc", on_error="zero_any")
epoch_batch5 = partial(epoch, naive="et")
epoch_v2 = partial(epoch, naive="utc")
epoch_old = partial(epoch, naive="local", on_error="zero")

# ---------------------------------------------------------------- bars
def bar_dict(bar, *, epoch_fn, healthy=False):
    d = {"t": epoch_fn(bar.t), "o": float(bar.o), "h": float(bar.h),
         "l": float(bar.l), "c": float(bar.c), "v": float(bar.v)}
    if healthy:
        d["healthy"] = True
    return d


def ctx_bars(ctx, symbol, tf, n=2000, *, epoch_fn, cast=True, healthy=False,
             sort=False, guard=False):
    """v2 Bar objects -> old bar dicts for one symbol."""
    bars = ctx.bars(symbol, tf, n)
    if guard:
        bars = bars or []
    out = []
    for b in bars:
        if cast:
            out.append(bar_dict(b, epoch_fn=epoch_fn, healthy=healthy))
        else:
            out.append({"t": epoch_fn(b.t), "o": b.o, "h": b.h,
                        "l": b.l, "c": b.c, "v": b.v})
    if sort:
        out.sort(key=lambda x: x["t"])
    return out


bar_dict_common = partial(bar_dict, epoch_fn=epoch_common)
bars_batch5 = partial(ctx_bars, epoch_fn=epoch_batch5, healthy=True, sort=True)
bars_v2 = partial(ctx_bars, epoch_fn=epoch_v2, cast=False)
bars_old = partial(ctx_bars, epoch_fn=epoch_old, sort=True, guard=True)


def fetch_bars(ctx, symbols, tf, n):
    """_common profile: {sym: [bar_dict]} for symbols with bars;
    a failing symbol yields no entry, never an exception."""
    out = {}
    for sym in symbols:
        try:
            bars = ctx.bars(sym, tf, n)
        except Exception:
            bars = []
        if bars:
            out[sym] = [bar_dict_common(b) for b in bars]
    return out


def bars_map(ctx, symbols, tf, n, *, bars_fn):
    return {s: bars_fn(ctx, s, tf, n) for s in symbols}


bars_map_batch5 = partial(bars_map, bars_fn=bars_batch5)


def _first_bars(bars_fn, ctx, symbol, tfs, n=2000):
    for tf in tfs:
        bars = bars_fn(ctx, symbol, tf, n)
        if bars:
            return bars
    return []


first_bars_old = partial(_first_bars, bars_old)

# ---------------------------------------------------------------- state
def state_common(ctx):
    """{SYM: {"position": {...}|None}} — _common profile."""
    state = {}
    for p in (ctx.positions or []):
        qty = float(p.get("qty") or 0)
        opened = p.get("opened_at") or ""
        pos = {"qty": qty, "entry_px": float(p.get("avg_price") or 0),
               "exit_rules": p.get("exit_rules"), "stop_px": p.get("stop_px"),
               **{k: p.get(k) for k in ("condor","entry_credit","spread","entry_debit","expiry","occ","box_lo","box_hi","datr14_prior","entry_spot","kind","debit") if p.get(k) is not None},
               "ref_px": float(p.get("avg_price") or 0),
               "entry_date": str(opened)[:10] if opened else None,
               "entry_bar_t": epoch_common(opened) if opened else None,
               "opened_at": opened, "intent_id": p.get("intent_id")}
        state[p["symbol"]] = {"position": pos if qty != 0 else None}
    return state


def state_batch5(ctx):
    """{SYM: {"position": {...}}} — batch-5 profile (fill_t/entry_t set)."""
    state = {}
    for p in ctx.positions or []:
        opened = p.get("opened_at")
        entry_date, fill_t = None, None
        if opened:
            try:
                fill_t = epoch_batch5(opened)
                entry_date = datetime.fromtimestamp(
                    fill_t, tz=ET).date().isoformat()
            except Exception:
                entry_date = str(opened)[:10]
        state[p["symbol"]] = {"position": {
            "qty": float(p.get("qty") or 0),
            "entry_px": float(p.get("avg_price") or 0),
            "avg_price": float(p.get("avg_price") or 0),
            "entry_date": entry_date, "opened_at": opened,
            "exit_rules": p.get("exit_rules"), "stop_px": p.get("stop_px"),
            **{k: p.get(k) for k in ("condor","entry_credit","spread","entry_debit","expiry","occ","box_lo","box_hi","datr14_prior","entry_spot","kind","debit") if p.get(k) is not None},
            "fill_t": fill_t, "entry_t": fill_t,
            "intent_id": p.get("intent_id")}}
    return state


def state_old(ctx):
    """{SYM: {"position": {...}}} — batch-7 profile: the position record
    carried verbatim, plus entry_px/entry_premium/entry_date aliases
    and OCC-underlying aliasing."""
    state = {}
    for p in ctx.positions or []:
        pos = dict(p)
        if pos.get("avg_price") is not None:
            pos.setdefault("entry_px", pos.get("avg_price"))
            pos.setdefault("entry_premium", pos.get("avg_price"))
        if pos.get("opened_at"):
            pos.setdefault("entry_date", str(pos["opened_at"])[:10])
        state[pos["symbol"]] = {"position": pos}
        m = re.match(r"^([A-Z]{1,6})\d{6}[CP]\d{8}$", pos["symbol"] or "")
        if m:
            pos.setdefault("occ", pos["symbol"])
            state.setdefault(m.group(1), {"position": pos})
    return state


def build_extra(ctx):
    """_v2bridge profile: params["extra"] plus sleeve-state in BOTH the
    flat and nested served shapes, held-qty anchors, and cash."""
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
    # GAP-CURE (free_opt family): session_dates from the SPY 1Day bar
    # calendar and last_exit_date from this sleeve's own journal fills
    # were read by the sleeves but written by nobody.
    if "session_dates" not in extra:
        try:
            _sb = ctx.bars("SPY", "1Day", 600) or []
            if _sb:
                extra["session_dates"] = sorted({str(b.t)[:10] for b in _sb})
        except Exception:
            pass
    if "last_exit_date" not in extra:
        _jp = getattr(ctx, "_journal", None)
        if _jp:
            try:
                from desk3.vendor.runtime.journal import tail_lines
                for _r in reversed(tail_lines(_jp, 4000)):
                    if _r.get("event") == "fill" and _r.get("position_intent") in ("sell_to_close", "buy_to_close"):
                        extra["last_exit_date"] = str(_r.get("ts") or "")[:10]
                        break
            except Exception:
                pass
    return extra


def held_map(ctx):
    return {p["symbol"]: float(p.get("qty") or 0)
            for p in (ctx.positions or [])}


def symbols_for(ctx, extra_candidates=()):
    syms = list(CANDIDATES)
    for s in extra_candidates:
        if s not in syms:
            syms.append(s)
    params = ctx.params or {}
    for s in (params.get("universe") or []):
        if s not in syms:
            syms.append(s)
    extra = params.get("extra") or {}
    for key in ("leader_events", "momentum_book", "chains", "sleeve_state"):
        d = extra.get(key) or {}
        if isinstance(d, dict):
            for s in d:
                if s not in syms:
                    syms.append(s)
    for p in (ctx.positions or []):
        if p["symbol"] not in syms:
            syms.append(p["symbol"])
    return syms

def serve_options(ctx, symbols):
    """Normalize ctx.options_chain(sym) payloads (every cache shape the
    warmers write: {"chains": {SYM: [rows]}, "quotes": {OCC: {...}}} and
    the SPY parity {"quotes": [rows]}) into the sleeves' documented
    extra shapes: chains {SYM: [rows]}, quotes {OCC: {bid, ask}}.
    Params/fixture channels keep precedence at the call site."""
    chains, quotes = {}, {}
    for sym in symbols or []:
        try:
            payload = ctx.options_chain(sym)
        except Exception:
            payload = None
        if not isinstance(payload, dict):
            continue
        ch = payload.get("chains")
        if isinstance(ch, dict):
            for s, rows in ch.items():
                if isinstance(rows, list) and rows:
                    chains.setdefault(s, rows)
        elif isinstance(ch, list) and ch:
            chains.setdefault(sym, ch)
        if isinstance(payload.get("chain"), list) and payload["chain"]:
            chains.setdefault(sym, payload["chain"])
        q = payload.get("quotes")
        if isinstance(q, dict):
            for occ, row in q.items():
                if isinstance(row, dict):
                    quotes.setdefault(occ, row)
        elif isinstance(q, list):
            for row in q:
                if isinstance(row, dict) and row.get("symbol"):
                    quotes.setdefault(row["symbol"], row)
                    chains.setdefault(sym, []).append(row)
    return chains, quotes


def session_fills_of(ctx):
    fn = getattr(ctx, "session_fills", None)
    if not callable(fn):
        return []
    try:
        return fn()
    except Exception:
        return []


def latest_quotes_of(ctx):
    fn = getattr(ctx, "latest_quotes", None)
    if callable(fn):
        try:
            return fn() or {}
        except Exception:
            return {}
    cache = getattr(ctx, "_cache", None)
    fn = getattr(cache, "read_quotes", None)
    if callable(fn):
        try:
            return fn() or {}
        except Exception:
            return {}
    return {}


# ---------------------------------------------------------------- contexts
class OldContext:
    """_common profile context (carries .market)."""
    def __init__(self, now, session, equity, extra, market=None,
                 account_equity=None):
        self.now = now
        self.session = session
        self.equity = equity
        self.account_equity = account_equity
        self.extra = extra
        self.market = market or {}


def make_old_context(ctx, derived_extra=None):
    params = ctx.params or {}
    extra = dict(params.get("extra") or {})
    for k, v in (derived_extra or {}).items():
        extra.setdefault(k, v)
    equity = float((ctx.slice or {}).get("cash_usd")
                   or (ctx.slice or {}).get("capital_usd") or 0.0)
    if params.get("equity"):
        equity = float(params["equity"])
    now = ctx.now
    return OldContext(now=now.timestamp(),
                      session=now.astimezone(ET).date().isoformat(),
                      equity=equity, extra=extra,
                      account_equity=account_equity_of(ctx))


def session_of(ctx):
    now = ctx.now
    if now.tzinfo is None:
        now = now.replace(tzinfo=ET)
    return now.astimezone(ET).date().isoformat()


def equity_of(ctx):
    """capital-first equity (batch-5 and batch-7 profiles)."""
    sl = ctx.slice or {}
    return float(sl.get("capital_usd") or sl.get("cash_usd") or 0.0)


def account_equity_of(ctx):
    """ACCOUNT equity for gate-semantic consumers (spx_premium cure):
    fixture overrides first (params["account_equity"], then
    params["extra"]["account_equity"]), then the v2 context's
    account_equity() (the door read-back cached at warm — a plain
    numeric attribute on a test double is also accepted). None when
    no account read-back exists. This NEVER touches equity_of: the
    slice stays every sizing consumer's basis."""
    params = ctx.params or {}
    for v in (params.get("account_equity"),
              (params.get("extra") or {}).get("account_equity")
              if isinstance(params.get("extra"), dict) else None):
        if v is not None:
            try:
                return float(v)
            except (TypeError, ValueError):
                return None
    acct = getattr(ctx, "account_equity", None)
    if callable(acct):
        try:
            acct = acct()
        except Exception:
            acct = None
    if acct is not None:
        try:
            return float(acct)
        except (TypeError, ValueError):
            return None
    return None


def old_context_batch5(ctx, extra):
    return CoreContext(now=ctx.now.timestamp(), session=session_of(ctx),
                       equity=equity_of(ctx),
                       account_equity=account_equity_of(ctx), market={}, extra=extra)


def old_context_v2(ctx, extra):
    now = ctx.now
    if now.tzinfo is None:
        now = now.replace(tzinfo=ET)
    return CoreContext(now=now.timestamp(),
                       session=now.astimezone(ET).date().isoformat(),
                       equity=float((ctx.slice or {}).get("capital_usd") or 0),
                       account_equity=account_equity_of(ctx),
                       extra=extra)


def old_context_old(ctx, extra):
    return CoreContext(now=ctx.now.timestamp(),
                       session=ctx.now.date().isoformat(),
                       equity=equity_of(ctx),
                       account_equity=account_equity_of(ctx), extra=extra)

# ---------------------------------------------------------------- translate
def translate_common(old_intents, sleeve_id, ctx, held=None):
    """_common profile: fractional qty carried, price_hint/target kept,
    exit side from the held map, reason truncated at 400."""
    held = held or {}
    stamp = ctx.now.strftime("%Y%m%dT%H%M%S")
    out = []
    for i, it in enumerate(old_intents or [], 1):
        kind = "entry" if it.kind == "enter" else "exit"
        qty = it.qty if getattr(it, "qty", None) is not None else it.qty_hint
        if qty is None:
            continue
        side = getattr(it, "side", None)
        pi = getattr(it, "position_intent", None)
        if side is None and pi:
            side = PI_SIDE.get(pi)
        if side is None:
            if kind == "entry":
                side = "buy"
            else:
                side = "buy" if float(held.get(it.symbol, 0)) < 0 else "sell"
        d = {"intent_id": f"{sleeve_id}-{stamp}-{i}", "kind": kind,
             "symbol": it.symbol, "side": side, "qty": qty,
             "order_type": "limit" if getattr(it, "limit_price", None) else "market",
             "limit_price": getattr(it, "limit_price", None),
             "stop_price": getattr(it, "stop", None),
             "reason": (getattr(it, "reason", "") or "")[:400],
             "time_in_force": "day"}
        if pi:
            d["position_intent"] = pi
        if getattr(it, "price_hint", None):
            d["price_hint"] = it.price_hint
        if getattr(it, "target", None):
            d["target"] = it.target
        _er = getattr(it, "exit_rules", None)
        if _er:
            d["exit_rules"] = [{"kind": r.kind, "value": float(r.value)} for r in _er]
        out.append(d)
    return out


def translate_batch5(ctx, sleeve_id, old_intents):
    """Batch-5 profile: fractional qty skipped (logged), whole qty int,
    limit/stop rounded to 2, position_intent inferred from reason
    tokens, reason truncated at 240."""
    stamp = ctx.now.strftime("%Y%m%dT%H%M%S")
    out, seq = [], 0
    for it in old_intents or []:
        qty_raw = getattr(it, "qty", None)
        if qty_raw is None:
            qty_raw = getattr(it, "qty_hint", None)
        if qty_raw is None or float(qty_raw) <= 0:
            continue
        if float(qty_raw) != int(float(qty_raw)):
            ctx.log("intent_skipped_fractional_qty", symbol=it.symbol,
                    qty=float(qty_raw))
            continue
        qty = int(float(qty_raw))
        seq += 1
        kind = "entry" if it.kind == "enter" else "exit"
        pi = getattr(it, "position_intent", None)
        reason = getattr(it, "reason", "") or ""
        if pi is None:
            for tok in PI_SIDE:
                if tok in reason:
                    pi = tok
                    break
        side = getattr(it, "side", None) or (PI_SIDE.get(pi) if pi else None) \
            or ("buy" if kind == "entry" else "sell")
        lp = getattr(it, "limit_price", None)
        d = {"intent_id": f"{sleeve_id}-{stamp}-{seq}", "kind": kind,
             "symbol": it.symbol, "side": side, "qty": qty,
             "order_type": "limit" if lp else "market",
             "limit_price": round(float(lp), 2) if lp else None,
             "stop_price": (round(float(it.stop), 2)
                            if getattr(it, "stop", None) else None),
             "reason": reason[:240] or sleeve_id, "time_in_force": "day"}
        if pi:
            d["position_intent"] = pi
        if getattr(it, "price_hint", None):
            d["price_hint"] = float(it.price_hint)
        _er = getattr(it, "exit_rules", None)
        if _er:
            d["exit_rules"] = [{"kind": r.kind, "value": float(r.value)} for r in _er]
        out.append(d)
    return out


def _derive_side_v2(oi):
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


def _derive_pi_v2(oi):
    if oi.position_intent:
        return oi.position_intent
    reason = oi.reason or ""
    for pi in ("buy_to_open", "sell_to_open", "sell_to_close", "buy_to_close"):
        if pi in reason:
            return pi
    if oi.kind == "exit":
        side = _derive_side_v2(oi)
        return "sell_to_close" if side == "sell" else "buy_to_close"
    return None


def to_v2_intents(ctx, sleeve_id, old_intents):
    """_v2bridge profile: side/position_intent derived from the intent,
    then its reason tokens (incl. SHORT / cover conventions)."""
    stamp = ctx.now.strftime("%Y%m%dT%H%M%S")
    out = []
    for i, oi in enumerate(old_intents, 1):
        qty = oi.qty if oi.qty is not None else oi.qty_hint
        intent = {"intent_id": f"{sleeve_id}-{stamp}-{i}",
                  "kind": "entry" if oi.kind == "enter" else "exit",
                  "symbol": oi.symbol, "side": _derive_side_v2(oi),
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
        _er = getattr(oi, "exit_rules", None)
        if _er:
            intent["exit_rules"] = [{"kind": r.kind, "value": float(r.value)} for r in _er]
        pi = _derive_pi_v2(oi)
        if pi:
            intent["position_intent"] = pi
        # DESIGNED-ORDER-LOGIC §4 (free_opt_parity): multi-leg packages
        # must survive translation — legs/package_id carried verbatim
        # (additive: intents without legs are byte-identical to before).
        if getattr(oi, "legs", None):
            intent["legs"] = [dict(leg) for leg in oi.legs]
        if getattr(oi, "package_id", None):
            intent["package_id"] = oi.package_id
        out.append(intent)
    return out


def serve_journal(ctx, journal_key):
    """Latest persisted journal dict for `journal_key` from the sleeve's
    own journal file (event == journal_key, stamped by a prior pass),
    or None. The v2-native durable-state channel (v02 precedent)."""
    path = getattr(ctx, "_journal", None)
    if not path:
        return None
    try:
        from desk3.vendor.runtime.journal import tail_lines
        for rec in reversed(tail_lines(path, 4000)):
            if rec.get("event") == journal_key and isinstance(rec.get("journal"), dict):
                return rec["journal"]
    except Exception:
        return None
    return None


def run_old_persisted(ctx, module_name, bars, extra, journal_key):
    """run_old_signal variant that runs the sleeve CLASS directly so
    its last_evaluation stamp survives: serves the persisted journal
    under extra[journal_key] (params/fixture channel wins) and logs the
    updated stamp back to the sleeve journal for the next pass. Without
    this, journals stamped on last_evaluation were discarded every pass
    and every stateful exit/dedupe rule reset (GAP-CURE)."""
    mod = importlib.import_module(module_name)
    state = state_old(ctx)
    extra = dict(extra or {})
    extra.setdefault("sleeve_state", state)
    params_extra = (ctx.params or {}).get("extra")
    if isinstance(params_extra, dict):
        for k, v in params_extra.items():
            extra.setdefault(k, v)
    if journal_key and journal_key not in extra:
        served = serve_journal(ctx, journal_key)
        if served is not None:
            extra[journal_key] = served
    old_ctx = old_context_old(ctx, extra)
    cls = None
    for v in vars(mod).values():
        if isinstance(v, type) and v.__module__ == mod.__name__ and hasattr(v, "signal"):
            cls = v
            break
    if cls is None:
        intents = mod.signal(bars, state, old_ctx) or []
        stamp = {}
    else:
        inst = cls()
        intents = inst.signal(bars, state, old_ctx) or []
        stamp = getattr(inst, "last_evaluation", None) or {}
    if isinstance(stamp, dict) and stamp:
        try:
            ctx.log("last_evaluation", stamp=stamp)
        except Exception:
            pass
    if journal_key and isinstance(stamp, dict) and isinstance(stamp.get(journal_key), dict):
        try:
            ctx.log(journal_key, journal=stamp[journal_key])
        except Exception:
            pass
    out, seq = [], 0
    for it in intents:
        seq += 1
        t = translate_old(it, ctx, seq)
        if t is not None:
            out.append(t)
    return out


def translate_old(intent, ctx, seq):
    """Batch-7 profile, ONE intent: qty defaults to 1 (stamped in the
    reason) when the strategy declares none, OCC contract may be
    encoded in the reason, legs carried, reason truncated at 500."""
    kind = "entry" if intent.kind == "enter" else "exit"
    qty = intent.qty if getattr(intent, "qty", None) is not None else intent.qty_hint
    note = ""
    if qty is None:
        qty = 1
        note = " [adapter: qty defaulted to 1 - strategy declared no qty]"
    qty = int(round(float(qty)))
    if qty <= 0:
        return None
    side = getattr(intent, "side", None) or PI_SIDE.get(
        getattr(intent, "position_intent", None) or "")
    if not side:
        side = "sell" if kind == "exit" else "buy"
    symbol = intent.symbol
    position_intent = getattr(intent, "position_intent", None)
    m = re.search(r"occ=([A-Z]{1,6}\d{6}[CP]\d{8})", intent.reason or "")
    if m:
        symbol = m.group(1)
        if position_intent is None:
            position_intent = "buy_to_open" if kind == "entry" else "sell_to_close"
        side = "buy" if position_intent.startswith("buy") else "sell"
    out = {"intent_id": f"{ctx.sleeve_id}-{ctx.now.strftime('%Y%m%dT%H%M%S')}-{seq}",
           "kind": kind, "symbol": symbol, "side": side, "qty": qty,
           "order_type": "limit" if getattr(intent, "limit_price", None) else "market",
           "limit_price": (float(intent.limit_price)
                           if getattr(intent, "limit_price", None) else None),
           "stop_price": (float(intent.stop)
                          if getattr(intent, "stop", None) else None),
           "reason": ((intent.reason or intent.kind) + note)[:500],
           "time_in_force": "day"}
    if position_intent:
        out["position_intent"] = position_intent
    if getattr(intent, "price_hint", None):
        out["price_hint"] = float(intent.price_hint)
    _er = getattr(intent, "exit_rules", None)
    if _er:
        out["exit_rules"] = [{"kind": r.kind, "value": float(r.value)} for r in _er]
    if getattr(intent, "legs", None):
        out["legs"] = [dict(leg) for leg in intent.legs]
    return out

# ---------------------------------------------------------------- runners
def run_old_batch5_persisted(ctx, sleeve_id, module, bars, extra, journal_keys=()):
    """Batch-5 persisted variant (GAP-CURE): run the sleeve CLASS so
    last_evaluation survives; serve each journal key from the sleeve's
    own journal file (params/fixture channel wins) and log the updated
    stamp back. Also files the full stamp as a last_evaluation record
    and, when the stamp carries earnings_flat / a rebalance happened,
    the phase_daily / momentum_rotation durable records."""
    extra = dict(extra or {})
    for key in journal_keys:
        if key not in extra:
            served = serve_journal(ctx, key)
            if served is not None:
                extra[key] = served
    if sleeve_id == "phase_daily":
        flat = serve_journal(ctx, "earnings_flat")
        st = dict(extra.get("sleeve_state") or {})
        if flat is not None and "earnings_flat" not in st:
            st["earnings_flat"] = flat
            extra["sleeve_state"] = st
    if sleeve_id == "momentum_rotation":
        lr = serve_journal(ctx, "last_rebalance")
        if isinstance(lr, dict) and lr.get("date"):
            extra.setdefault("last_rebalance", lr["date"])
            meta = dict(extra.get("meta") or {})
            meta.setdefault("last_rebalance", lr["date"])
            extra["meta"] = meta
    oc = old_context_batch5(ctx, extra)
    cls = None
    for v in vars(module).values():
        if isinstance(v, type) and v.__module__ == module.__name__ and hasattr(v, "signal"):
            cls = v
            break
    if cls is None:
        return translate_batch5(ctx, sleeve_id, module.signal(bars, {}, oc))
    inst = cls()
    intents = inst.signal(bars, {}, oc) or []
    stamp = getattr(inst, "last_evaluation", None) or {}
    if stamp:
        try: ctx.log("last_evaluation", stamp=stamp)
        except Exception: pass
    for key in journal_keys:
        if isinstance(stamp.get(key), dict):
            try: ctx.log(key, journal=stamp[key])
            except Exception: pass
    if sleeve_id == "phase_daily" and "earnings_flat" in stamp:
        try: ctx.log("earnings_flat", journal=stamp["earnings_flat"])
        except Exception: pass
    if sleeve_id == "momentum_rotation" and intents:
        try: ctx.log("last_rebalance", journal={"date": oc.session})
        except Exception: pass
    return translate_batch5(ctx, sleeve_id, intents)


def run_old_batch5(ctx, sleeve_id, module, bars, extra):
    """Call the ported module-level signal() and translate (batch-5)."""
    oc = old_context_batch5(ctx, extra)
    return translate_batch5(ctx, sleeve_id, module.signal(bars, {}, oc))


def run_old_signal(ctx, module_name, bars, extra):
    """Call the ported strategy's module-level signal() (batch-7)."""
    mod = importlib.import_module(module_name)
    state = state_old(ctx)
    extra = dict(extra or {})
    extra.setdefault("sleeve_state", state)
    params_extra = (ctx.params or {}).get("extra")
    if isinstance(params_extra, dict):
        for k, v in params_extra.items():
            extra.setdefault(k, v)
    old_ctx = old_context_old(ctx, extra)
    intents = mod.signal(bars, state, old_ctx) or []
    out, seq = [], 0
    for it in intents:
        seq += 1
        t = translate_old(it, ctx, seq)
        if t is not None:
            out.append(t)
    try:
        ctx.log("adapter_eval", module=module_name, intents=len(out),
                bars={k: len(v) for k, v in (bars or {}).items()})
    except Exception:
        pass
    return out
