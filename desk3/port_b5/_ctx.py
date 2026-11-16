"""Snapshot -> v2 SleeveContext bridge for batch-5 ported sleeves.

The v3 worker calls evaluate(view, ctx) where view is the cycle's single
immutable snapshot data (plain JSON dict) and ctx is the worker task ctx.
This module rebuilds, per sleeve, the v2 runtime.context.SleeveContext
surface the copied v2 adapters expect, backed ONLY by the snapshot:

  view = {
    "now": iso8601,                        # cycle time
    "bars": {"SYM|TF": [bar dicts]},       # producer: bars
    "positions": [v2 position dicts],      # producer: broker_readback
    "slice": {"capital_usd", "cash_usd"},  # config row
    "params": {...},                       # config row params
    "options": {"QQQ": {...chain...}},     # producer: options
    "earnings": {...calendar...},          # producer: earnings
    "quotes": {...latest quotes...},       # producer: quotes
    "qulla": {...proposals...},            # producer: qulla
    "session_fills": [fill rows],          # producer: session fills
    "account_equity": float | None,
  }

Positions absent from the view are rebuilt from the sleeve's own
journal fills (runtime.journal.positions_from_journal — the exact v2
run_sleeve route). The journal path is exposed as ctx._journal so the
v2 bridge's persisted-journal serving (serve_journal: momentum_rotation
/ phase_daily / raschke_pf3 stamps) works unchanged. No network, no
cache files: anything absent from the snapshot is absent for the
sleeve, exactly as an empty v2 cache was.
"""
from __future__ import annotations
import os
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class _Bar:
    t: str; o: float; h: float; l: float; c: float; v: float = 0.0


class SnapshotSleeveContext:
    def __init__(self, sleeve_id, view, ctx):
        self.sleeve_id = sleeve_id
        self._view = view or {}
        now = self._view.get("now") or (ctx or {}).get("now")
        if now is None:
            raise ValueError("snapshot_missing_now")
        self.now = (now if isinstance(now, datetime)
                    else datetime.fromisoformat(str(now).replace("Z", "+00:00")))
        if self.now.tzinfo is None:
            self.now = self.now.replace(tzinfo=timezone.utc)
        self._state_dir = (ctx or {}).get("state_dir") or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.abspath(__file__)))), "state", sleeve_id)
        os.makedirs(self._state_dir, exist_ok=True)
        self._journal = os.path.join(self._state_dir, "journal.jsonl")
        if self._view.get("positions") is not None:
            self.positions = list(self._view.get("positions") or [])
        else:
            from runtime.journal import positions_from_journal
            self.positions = positions_from_journal(self._journal)
        self.slice = dict(self._view.get("slice") or {})
        self.params = dict(self._view.get("params") or {})
        extra = dict(self.params.get("extra") or {})
        extra.update(self._view.get("extra") or {})
        if extra:
            self.params["extra"] = extra
        self.logs = []

    # -- v2 SleeveContext surface -------------------------------------
    def bars(self, symbol, tf, n):
        rows = (self._view.get("bars") or {}).get(f"{symbol}|{tf}") or []
        return [_Bar(t=str(r["t"]), o=float(r["o"]), h=float(r["h"]),
                     l=float(r["l"]), c=float(r["c"]),
                     v=float(r.get("v", 0.0))) for r in rows][-int(n):]

    def cache_age_s(self, symbol, tf):
        return 0.0

    def options_chain(self, underlying):
        payload = (self._view.get("options") or {}).get(underlying) or {}
        if isinstance(payload, dict) and isinstance(payload.get("quotes"), dict):
            # OPT-SHAPE-20261026: the live options producer serves
            # "quotes" as an OCC-keyed MAP ({OCC: {bid, ask, ...}}),
            # while the batch-5 consumers (qqq_put_ladder is the only
            # options_chain consumer in this batch) iterate "quotes"
            # as a LIST of quote records carrying
            # symbol/expiration/strike/delta/bid/ask — the shape every
            # fixture serves. Iterating the map yielded its string
            # keys and crashed on quote.get. Serve the canonical list:
            # the full chain rows for this underlying (they carry all
            # of those fields) when present, else the map's values.
            payload = dict(payload)
            chains = payload.get("chains")
            rows = chains.get(underlying) if isinstance(chains, dict) else None
            payload["quotes"] = (list(rows) if rows
                                 else list(payload["quotes"].values()))
        return payload

    def tensor_bundle(self):
        return self._view.get("tensor") or {}

    def qulla_proposals(self):
        return self._view.get("qulla") or {}

    def kraken_inputs(self):
        return self._view.get("kraken") or {}

    def earnings_calendar(self):
        return self._view.get("earnings") or {}

    def iv_history(self, underlying):
        return (self._view.get("iv") or {}).get(underlying) or {}

    def buyback_scan(self):
        return self._view.get("buyback_scan") or {}

    def latest_quotes(self):
        return self._view.get("quotes") or {}

    def account_equity(self):
        for v in (self._view.get("account_equity"),
                  self.params.get("account_equity"),
                  (self.params.get("extra") or {}).get("account_equity")):
            if v is not None:
                try:
                    return float(v)
                except (TypeError, ValueError):
                    return None
        return None

    def session_fills(self):
        if "session_fills" in self._view:
            return self._view.get("session_fills")
        # v2 SleeveContext.session_fills semantics, verbatim shape.
        from runtime.journal import tail_lines
        from zoneinfo import ZoneInfo
        try:
            recs = tail_lines(self._journal, 100000)
        except Exception:
            return None
        today = self.now.astimezone(ZoneInfo("America/New_York")).date().isoformat()
        out = []
        for r in recs:
            if r.get("event") != "fill":
                continue
            ts = str(r.get("ts") or "")
            if ts[:10] != today:
                continue
            out.append({"position_intent": r.get("position_intent"),
                        "qty": r.get("qty"), "price": r.get("price"),
                        "symbol": r.get("symbol"), "side": r.get("side"),
                        "ts": r.get("ts")})
        return out

    def log(self, event, **fields):
        self.logs.append({"event": event, **fields})
        try:
            from runtime.journal import append_line
            append_line(self._journal,
                        {"event": event, "sleeve": self.sleeve_id,
                         "ts": self.now.isoformat(), **fields})
        except Exception:
            pass


def run(sleeve_id, view, ctx):
    """Run the copied v2 adapter for sleeve_id on the snapshot view."""
    import importlib
    mod = importlib.import_module(f"adapters.{sleeve_id}")
    return mod.evaluate(SnapshotSleeveContext(sleeve_id, view, ctx)) or []
