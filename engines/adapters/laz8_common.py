"""Shared adapter glue for Lazarus batch 8 (s_mn_*).

evaluate(view, ctx) convention (same as adapters/vix_hedge.py):
  view["bars"]      {SYM: [daily bars {t,o,h,l,c,v}]}
  view["options"]   {"chains": {...}, "quotes": {...}}  (opt sleeves)
  view["fires"]     [ingested research-lane fires]      (fire sleeves)
  view["positions"] [broker position dicts]
  ctx               {sleeve_id, session, now, equity, extra}
Positions become slice_state {SYM: {"position": {qty, avg_price,
entry_px, entry_date}}} (v2 state_old semantics); fires/chains/
quotes are merged into context.extra. Output: v3 intent dicts.
"""
from __future__ import annotations

import importlib
import re
from datetime import datetime, timezone

_OCC_RE = re.compile(r"^([A-Z]{1,6})\d{6}[CP]\d{8}$")


class _Context:
    def __init__(self, now, session, equity, extra):
        self.now = now
        self.session = session
        self.equity = equity
        self.account_equity = None
        self.extra = extra


def _state_old(positions):
    state = {}
    for p in positions or []:
        pos = dict(p)
        if pos.get("avg_price") is not None:
            pos.setdefault("entry_px", pos.get("avg_price"))
            pos.setdefault("entry_premium", pos.get("avg_price"))
        if pos.get("opened_at"):
            pos.setdefault("entry_date", str(pos["opened_at"])[:10])
        state[pos["symbol"]] = {"position": pos}
    return state


def _normalize_bars(bars):
    """BAR-T-SHAPE-20261026: the live WarmBars producer serves bar
    "t" as an ISO-8601 string (raw Alpaca shape, e.g.
    '2025-06-13T04:00:00Z'); the laz8 contract (every fixture, and
    sleeves/laz8_common.bar_dates) is epoch-seconds float. Convert
    string timestamps to epoch at this adapter boundary — the one
    place every laz8 sleeve's bars pass through — leaving numeric
    timestamps untouched. Only FULL ISO timestamps (carrying a 'T')
    are converted: date-only strings ('2026-10-01') are a dialect
    some laz8 consumers parse natively as dates (s_mn_faber's ENH19
    stale gate reads str(t)[:10]), and no live producer serves them
    as bar timestamps.

    BROKER-422-SMN-SYMBOL-20261027: the warm producer ALSO serves
    each symbol under timeframe-suffixed duplicate keys
    ("AG|1Hour", "TE|1Week" — desk3/warm.py). The laz8 sleeves are
    documented 1D strategies whose contract (and every fixture) is a
    map keyed by PLAIN symbol; iterating the raw live map made each
    suffixed duplicate a phantom symbol, so sleeves ranked/traded
    the duplicates (s_mn_reversal ranked 21-WEEK returns off
    "|1Week" keys) and emitted intents whose symbol was the raw key
    — Alpaca 422s them ("asset \\"AG|1Hour\\" not found", body
    captured live 2026-10-27). Cure at this boundary: drop suffixed
    duplicates; a symbol served ONLY under a suffixed key is
    surfaced under its plain name so coverage is never lost."""
    out = {}
    for sym, rows in (bars or {}).items():
        if "|" in sym:
            plain = sym.split("|", 1)[0]
            if plain in (bars or {}) or plain in out:
                continue  # timeframe duplicate of a plain-keyed symbol
            sym = plain  # only served suffixed: keep, under plain name
        fixed = []
        for b in rows or []:
            t = b.get("t") if isinstance(b, dict) else None
            if isinstance(t, str) and "T" in t:
                try:
                    b = dict(b)
                    b["t"] = datetime.fromisoformat(
                        t.replace("Z", "+00:00")).timestamp()
                except ValueError:
                    pass
            fixed.append(b)
        out[sym] = fixed
    return out


def make_evaluate(sleeve_id, default_equity):
    mod = importlib.import_module(f"sleeves.{sleeve_id}")

    def evaluate(view, ctx):
        view = view or {}
        ctx = ctx or {}
        positions = view.get("positions")
        if positions is None:
            positions = ctx.get("positions") or []
        bars = _normalize_bars(view.get("bars") or {})
        extra = {}
        options = view.get("options") or {}
        if options.get("chains"):
            extra["chains"] = options["chains"]
        if options.get("quotes"):
            extra["quotes"] = options["quotes"]
        fires = view.get("fires")
        if fires is None:
            fires = (view.get("extra") or {}).get("fires")
        if fires is not None:
            extra["fires"] = fires
        for src in (view.get("extra"), ctx.get("extra")):
            if isinstance(src, dict):
                for k, v in src.items():
                    extra.setdefault(k, v)
        session = ctx.get("session") or view.get("session")
        now_iso = ctx.get("now") or view.get("now")
        if not session and now_iso:
            session = str(now_iso)[:10]
        if not session:
            session = "1970-01-01"
        if now_iso:
            try:
                now_dt = datetime.fromisoformat(str(now_iso).replace("Z", "+00:00"))
                if now_dt.tzinfo is None:
                    now_dt = now_dt.replace(tzinfo=timezone.utc)
                now_ts, stamp = now_dt.timestamp(), now_dt.strftime("%Y%m%dT%H%M%S")
            except ValueError:
                now_ts, stamp = 0.0, session.replace("-", "") + "T000000"
        else:
            now_ts, stamp = 0.0, session.replace("-", "") + "T000000"
        equity = ctx.get("equity") or view.get("equity") or default_equity
        old_ctx = _Context(now=now_ts, session=session,
                           equity=float(equity), extra=extra)
        intents = mod.signal(bars, _state_old(positions), old_ctx) or []
        out, seq = [], 0
        for it in intents:
            seq += 1
            qty = it.qty if it.qty is not None else it.qty_hint
            if qty is None or int(round(float(qty))) <= 0:
                continue
            kind = "entry" if it.kind == "enter" else "exit"
            side = it.side or ("sell" if kind == "exit" else "buy")
            row = {"intent_id": f"{sleeve_id}-{stamp}-{seq}",
                   "kind": kind, "symbol": it.symbol, "side": side,
                   "qty": int(round(float(qty))), "order_type": "market",
                   "limit_price": None,
                   "stop_price": float(it.stop) if it.stop else None,
                   "reason": (it.reason or it.kind)[:500],
                   "time_in_force": "day"}
            if it.position_intent:
                row["position_intent"] = it.position_intent
            if it.price_hint:
                row["price_hint"] = float(it.price_hint)
            out.append(row)
        return out

    return evaluate
