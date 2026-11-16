"""Canonical v3 port bridge for batch 6 (mirrors v2 adapters/_bridge.py
profiles 'old' and 'batch5' verbatim in behavior).

Snapshot view contract (the producer-registry declaration surface):
  view = {
    "now": ISO-8601 str (evaluation clock; falls back to ctx cycle time
           fields / last bar),
    "bars": {"SYM|TF": [{"t": ISO str or epoch, "o","h","l","c","v"}]},
    "positions": [ {symbol, qty, avg_price, opened_at, intent_id, ...} ],
    "extra": { ... old context.extra keys ... }  (flat, or {sleeve_id: {...}}),
    "options": {"SYM": payload-dict},   # ctx.options_chain(sym) channel
    "earnings_calendar": {"earnings": {...}, "fresh": bool},
    "session_fills": [...], "latest_quotes": {...},
    "slice": {"capital_usd": ..., "cash_usd": ...},
  }
Intent translation, state shaping, epoch conversion and context
construction follow the v2 bridge profiles EXACTLY (old profile for the
batch-6 sleeves, batch5 profile for raschke_rre) — no strategy math here.
"""
from __future__ import annotations

import importlib
import json
import os
import re
from datetime import datetime, timezone
from functools import partial
from zoneinfo import ZoneInfo

from core.sleeve import Context as CoreContext

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


epoch_batch5 = partial(epoch, naive="et")
epoch_old = partial(epoch, naive="local", on_error="zero")


def _epoch_any(ts, epoch_fn):
    if isinstance(ts, (int, float)):
        return float(ts)
    return epoch_fn(ts)


# ---------------------------------------------------------------- view ctx
class _Bar:
    __slots__ = ("t", "o", "h", "l", "c", "v")

    def __init__(self, d):
        t = d.get("t")
        if isinstance(t, (int, float)):
            t = datetime.fromtimestamp(float(t), tz=timezone.utc).isoformat().replace("+00:00", "Z")
        self.t = t
        self.o = d.get("o"); self.h = d.get("h"); self.l = d.get("l")
        self.c = d.get("c"); self.v = d.get("v")


class ViewCtx:
    """A v2-runtime-context-shaped facade over the v3 snapshot view."""

    def __init__(self, view, ctx, sleeve_id):
        self.view = view or {}
        self.ctx = ctx or {}
        self.sleeve_id = sleeve_id
        now_raw = self.view.get("now") or self.ctx.get("now")
        if now_raw:
            self.now = datetime.fromisoformat(str(now_raw).replace("Z", "+00:00"))
            if self.now.tzinfo is None:
                self.now = self.now.replace(tzinfo=ET)
        else:
            self.now = datetime.now(ET)
        pos = self.view.get("positions")
        if isinstance(pos, dict):
            pos = pos.get(sleeve_id) or []
        self.positions = list(pos or [])
        extra = self.view.get("extra") or {}
        if isinstance(extra, dict) and isinstance(extra.get(sleeve_id), dict) \
                and set(extra.keys()) == {sleeve_id}:
            extra = extra[sleeve_id]
        self.params = {"extra": dict(extra or {})}
        sl = self.view.get("slice") or self.view.get("slices") or {}
        if isinstance(sl, dict) and isinstance(sl.get(sleeve_id), dict):
            sl = sl[sleeve_id]
        self.slice = dict(sl) if isinstance(sl, dict) and sl else \
            {"capital_usd": 10000.0, "cash_usd": 10000.0}
        self._journal = os.path.join(self.ctx.get("state_dir") or ".", "journal.jsonl")
        self.logs = []

    # v2 ctx surface used by the copied adapters/bridge ---------------
    def bars(self, symbol, tf, n=2000):
        rows = (self.view.get("bars") or {}).get(f"{symbol}|{tf}") or []
        rows = rows[-n:] if n else rows
        return [_Bar(r) for r in rows]

    def options_chain(self, sym):
        opts = self.view.get("options") or {}
        if isinstance(opts, dict):
            if isinstance(opts.get(sym), dict):
                return opts[sym]
            # flat payload shape {chains:..., quotes:...}
            if "chains" in opts or "quotes" in opts:
                return opts
        return None

    def earnings_calendar(self):
        cal = self.view.get("earnings_calendar")
        return cal if isinstance(cal, dict) else {}

    def session_fills(self):
        return self.view.get("session_fills") or \
            (self.params.get("extra") or {}).get("session_fills") or []

    def latest_quotes(self):
        return self.view.get("latest_quotes") or \
            (self.params.get("extra") or {}).get("latest_quote") or {}

    def log(self, event, **kw):
        rec = {"event": event}
        rec.update(kw)
        self.logs.append(rec)
        try:
            os.makedirs(os.path.dirname(self._journal) or ".", exist_ok=True)
            with open(self._journal, "a") as fh:
                fh.write(json.dumps(rec, default=str) + "\n")
        except Exception:
            pass


# ---------------------------------------------------------------- bars
def bar_dict(bar, *, epoch_fn, healthy=False):
    d = {"t": _epoch_any(bar.t, epoch_fn), "o": float(bar.o), "h": float(bar.h),
         "l": float(bar.l), "c": float(bar.c), "v": float(bar.v)}
    if healthy:
        d["healthy"] = True
    return d


def ctx_bars(ctx, symbol, tf, n=2000, *, epoch_fn, cast=True, healthy=False,
             sort=False, guard=False):
    bars = ctx.bars(symbol, tf, n)
    if guard:
        bars = bars or []
    out = []
    for b in bars:
        if cast:
            out.append(bar_dict(b, epoch_fn=epoch_fn, healthy=healthy))
        else:
            out.append({"t": _epoch_any(b.t, epoch_fn), "o": b.o, "h": b.h,
                        "l": b.l, "c": b.c, "v": b.v})
    if sort:
        out.sort(key=lambda x: x["t"])
    return out


bars_batch5 = partial(ctx_bars, epoch_fn=epoch_batch5, healthy=True, sort=True)
bars_old = partial(ctx_bars, epoch_fn=epoch_old, sort=True, guard=True)
bar_dicts = bars_batch5
old_bars = bars_old


def _first_bars(bars_fn, ctx, symbol, tfs, n=2000):
    for tf in tfs:
        bars = bars_fn(ctx, symbol, tf, n)
        if bars:
            return bars
    return []


first_bars_old = partial(_first_bars, bars_old)
first_bars = first_bars_old


def bars_map(ctx, symbols, tf, n, *, bars_fn=bars_batch5):
    return {s: bars_fn(ctx, s, tf, n) for s in symbols}


# ---------------------------------------------------------------- state
def state_batch5(ctx):
    state = {}
    for p in ctx.positions or []:
        opened = p.get("opened_at")
        entry_date, fill_t = None, None
        if opened:
            try:
                fill_t = epoch_batch5(opened)
                entry_date = datetime.fromtimestamp(fill_t, tz=ET).date().isoformat()
            except Exception:
                entry_date = str(opened)[:10]
        state[p["symbol"]] = {"position": {
            "qty": float(p.get("qty") or 0),
            "entry_px": float(p.get("avg_price") or 0),
            "avg_price": float(p.get("avg_price") or 0),
            "entry_date": entry_date, "opened_at": opened,
            "exit_rules": p.get("exit_rules"), "stop_px": p.get("stop_px"),
            **{k: p.get(k) for k in ("condor", "entry_credit", "spread", "entry_debit", "expiry", "occ", "box_lo", "box_hi", "datr14_prior", "entry_spot", "kind", "debit") if p.get(k) is not None},
            "fill_t": fill_t, "entry_t": fill_t,
            "intent_id": p.get("intent_id")}}
    return state


state_from_positions = state_batch5


def state_old(ctx):
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


# ---------------------------------------------------------------- options
def serve_options(ctx, symbols):
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


# ---------------------------------------------------------------- contexts
def session_of(ctx):
    now = ctx.now
    if now.tzinfo is None:
        now = now.replace(tzinfo=ET)
    return now.astimezone(ET).date().isoformat()


def equity_of(ctx):
    sl = ctx.slice or {}
    return float(sl.get("capital_usd") or sl.get("cash_usd") or 0.0)


def account_equity_of(ctx):
    params = ctx.params or {}
    for v in (params.get("account_equity"),
              (params.get("extra") or {}).get("account_equity")
              if isinstance(params.get("extra"), dict) else None):
        if v is not None:
            try:
                return float(v)
            except (TypeError, ValueError):
                return None
    return None


def old_context_batch5(ctx, extra):
    return CoreContext(now=ctx.now.timestamp(), session=session_of(ctx),
                       equity=equity_of(ctx),
                       account_equity=account_equity_of(ctx), market={}, extra=extra)


def old_context_old(ctx, extra):
    return CoreContext(now=ctx.now.timestamp(),
                       session=ctx.now.date().isoformat(),
                       equity=equity_of(ctx),
                       account_equity=account_equity_of(ctx), extra=extra)


# ---------------------------------------------------------------- translate
def translate_batch5(ctx, sleeve_id, old_intents):
    stamp = ctx.now.strftime("%Y%m%dT%H%M%S")
    out, seq = [], 0
    for it in old_intents or []:
        qty_raw = getattr(it, "qty", None)
        if qty_raw is None:
            qty_raw = getattr(it, "qty_hint", None)
        if qty_raw is None or float(qty_raw) <= 0:
            continue
        if float(qty_raw) != int(float(qty_raw)):
            ctx.log("intent_skipped_fractional_qty", symbol=it.symbol, qty=float(qty_raw))
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
             "stop_price": (round(float(it.stop), 2) if getattr(it, "stop", None) else None),
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


def translate_old(intent, ctx, seq):
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
           "limit_price": (float(intent.limit_price) if getattr(intent, "limit_price", None) else None),
           "stop_price": (float(intent.stop) if getattr(intent, "stop", None) else None),
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


# ---------------------------------------------------------------- journals
def serve_journal(ctx, journal_key):
    path = getattr(ctx, "_journal", None)
    if not path or not os.path.exists(path):
        return None
    try:
        with open(path) as fh:
            lines = fh.readlines()[-4000:]
        for line in reversed(lines):
            try:
                rec = json.loads(line)
            except Exception:
                continue
            if rec.get("event") == journal_key and isinstance(rec.get("journal"), dict):
                return rec["journal"]
    except Exception:
        return None
    return None


# ---------------------------------------------------------------- runners
def run_old_signal(ctx, module_name, bars, extra):
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


def run_old_persisted(ctx, module, bars, extra, journal_keys=()):
    """Batch5 persisted runner (raschke_rre): serve journal keys from the
    sleeve's own journal file in state_dir, run the sleeve CLASS so its
    last_evaluation stamp survives, log the stamp back."""
    extra = dict(extra or {})
    for key in journal_keys:
        if key not in extra:
            served = serve_journal(ctx, key)
            if served is not None:
                extra[key] = served
    oc = old_context_batch5(ctx, extra)
    cls = None
    for v in vars(module).values():
        if isinstance(v, type) and v.__module__ == module.__name__ and hasattr(v, "signal"):
            cls = v
            break
    if cls is None:
        return translate_batch5(ctx, ctx.sleeve_id, module.signal(bars, {}, oc))
    inst = cls()
    intents = inst.signal(bars, {}, oc) or []
    stamp = getattr(inst, "last_evaluation", None) or {}
    if stamp:
        try:
            ctx.log("last_evaluation", stamp=stamp)
        except Exception:
            pass
    for key in journal_keys:
        if isinstance(stamp.get(key), dict):
            try:
                ctx.log(key, journal=stamp[key])
            except Exception:
                pass
    return translate_batch5(ctx, ctx.sleeve_id, intents)


run_old = run_old_signal
run_old_batch5_persisted = run_old_persisted
