"""Batch-4 port plumbing: v2 ctx contract rebuilt from the v3 snapshot.

The v2 adapters (copied near-verbatim into desk3/sleeves/<id>.py, glue
only) call a v2 SleeveContext: bars/options/earnings/iv from the warm
cache, own positions/slice, params["extra"], own journal. In v3 those
inputs arrive through the ONE immutable per-cycle snapshot (the view)
plus the sleeve's own state dir. Snapshot view layout:

    view = {
      "now_iso":   ISO timestamp of the cycle,
      "bars":      {SYM: {TF: [{t,o,h,l,c,v}, ...]}},   # t = ISO string
      "positions": {sleeve_id: [position dict, ...]},   # v2 journal shape
      "slice":     {sleeve_id: {"capital_usd": x, "cash_usd": y}},
      "params":    {sleeve_id: {...}},                  # incl. "extra"
      "options":   {underlying: chain payload},
      "earnings":  earnings-calendar payload,
      "iv":        {underlying: iv-history payload},
      "quotes":    latest-quotes payload,
    }

Producer-registry input keys declared per sleeve (desk3/sleeves/<id>.py
INPUTS) name exactly these view entries, e.g. "bars:ADA/USD:1Hour",
"positions", "options:chains", "earnings", "iv", "journal:momentum".
"""
from __future__ import annotations

import importlib
import os
import sys
from datetime import datetime
from types import SimpleNamespace

_VENDOR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "desk3", "vendor")


def ensure_core():
    """Strategies import `from core.sleeve import ...` (their byte-identical
    source). Register the vendored byte-identical copy under that name."""
    if "core.sleeve" in sys.modules:
        return
    if _VENDOR not in sys.path:
        sys.path.insert(0, _VENDOR)
    import core.sleeve  # noqa: F401  (vendored copy, sha-pinned by blockers)


def load_strategy(sleeve_id):
    ensure_core()
    return importlib.import_module(f"desk3.vendor.sleeves.{sleeve_id}")


class SnapshotCtx:
    """The v2 SleeveContext surface, served from the snapshot view."""

    def __init__(self, view, ctx):
        self.sleeve_id = ctx["sleeve_id"]
        self.now = datetime.fromisoformat(view["now_iso"])
        self._view = view
        # CURE2-1: the v3 snapshot contract is positions = LIST of position
        # dicts (bridge/port_b5/lazarus all consume the list shape); the
        # batch-4 ctx alone assumed {sleeve_id: [...]} and crashed with
        # 'list' object has no attribute 'get' whenever positions was the
        # canonical list. Accept both shapes; filter list rows to this
        # sleeve when they carry a sleeve_id.
        _pos = view.get("positions")
        if isinstance(_pos, dict):
            self.positions = list(_pos.get(self.sleeve_id) or [])
        elif isinstance(_pos, list):
            self.positions = [p for p in _pos
                              if p.get("sleeve_id") in (None, self.sleeve_id)]
        else:
            self.positions = []
        sl = (view.get("slice") or {}).get(self.sleeve_id) or {}
        self.slice = {"capital_usd": float(sl.get("capital_usd", 10000.0)),
                      "cash_usd": float(sl.get("cash_usd", sl.get("capital_usd", 10000.0)))}
        self.params = dict((view.get("params") or {}).get(self.sleeve_id) or {})
        self._journal = os.path.join(ctx["state_dir"], "journal.jsonl")
        self._logs = []

    # -- warm products -------------------------------------------------
    def bars(self, symbol, tf, n):
        # CURE2-1 (cont.): accept the canonical shapes — {SYM: {TF: rows}},
        # {SYM: rows}, and flat {"SYM|TF": rows} — instead of assuming one.
        bars = self._view.get("bars") or {}
        per = bars.get(symbol)
        if isinstance(per, dict):
            rows = per.get(tf) or []
        elif isinstance(per, list):
            rows = per
        else:
            rows = bars.get(f"{symbol}|{tf}") or []
        return [SimpleNamespace(t=r["t"], o=r["o"], h=r["h"], l=r["l"],
                                 c=r["c"], v=r["v"]) for r in rows[-n:]]

    def cache_age_s(self, symbol, tf):
        return None

    def options_chain(self, underlying):
        return (self._view.get("options") or {}).get(underlying)

    def earnings_calendar(self):
        return self._view.get("earnings") or {}

    def iv_history(self, underlying):
        return (self._view.get("iv") or {}).get(underlying) or {}

    def latest_quotes(self):
        return self._view.get("quotes") or {}

    def account_equity(self):
        params = self.params or {}
        for v in (params.get("account_equity"),
                  (params.get("extra") or {}).get("account_equity")
                  if isinstance(params.get("extra"), dict) else None):
            if v is not None:
                try:
                    return float(v)
                except (TypeError, ValueError):
                    return None
        acct = self._view.get("account_equity")
        return float(acct) if acct is not None else None

    def session_fills(self):
        from desk3.vendor.runtime.journal import tail_lines
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

    # -- journal --------------------------------------------------------
    def log(self, event, **fields):
        from desk3.vendor.runtime.journal import append_line
        rec = {"event": event, "sleeve": self.sleeve_id,
               "ts": self.now.isoformat(), **fields}
        self._logs.append(rec)
        append_line(self._journal, rec)


def evaluate_via(view, ctx, adapter_evaluate):
    """Run a copied v2 adapter body against the snapshot ctx."""
    return adapter_evaluate(SnapshotCtx(view, ctx)) or []
