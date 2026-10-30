"""v3 port of v2 sleeve leaps_momentum (batch 4).

Strategy: desk3/vendor/sleeves/leaps_momentum.py — byte-identical copy of the v2
sleeve (sha256-pinned by tests/test_port_batch4_blockers.py).
Adapter: the v2 adapter body below, copied with import lines rewritten
to the vendored bridge (desk3/port4_bridge.py) only; logic untouched,
including every Edge enhancement switch/default and gap-audit cure.
Inputs are re-expressed as the INPUTS producer-registry declaration;
evaluate(view, ctx) serves them from the v3 snapshot via
desk3/port4_context.py.
"""
from desk3.port4_context import evaluate_via

INPUTS = ('bars:*:1Day', 'options:chains', 'positions', 'journal:momentum')

from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from desk3.port4_bridge import CANDIDATES, ET, OldContext
from desk3.port4_bridge import bar_dict_common as bar_dict
from desk3.port4_bridge import epoch_common as _epoch
from desk3.port4_bridge import fetch_bars, held_map, make_old_context
from desk3.port4_bridge import state_common as sleeve_state_from_positions
from desk3.port4_bridge import symbols_for
from desk3.port4_bridge import translate_common as translate_intents

from desk3.port4_context import load_strategy
strat = load_strategy("leaps_momentum")
SLEEVE_ID = "leaps_momentum"
WARMUP_BARS = {"1Day": 31}
def _mom_book(ctx):
    """The desk momentum sleeve's open book {SYM: {"qty"}} + age in days
    of its newest fill, from its own journal (the documented producer:
    the momentum book this sleeve piggybacks). None when unreadable."""
    import os as _os
    from datetime import datetime as _dt, timezone as _tz
    jp = getattr(ctx, "_journal", None)
    if not jp: return None, None
    path = _os.path.join(_os.path.dirname(_os.path.dirname(jp)), "momentum", "journal.jsonl")
    try:
        from desk3.vendor.runtime.journal import positions_from_journal, tail_lines
        pos = positions_from_journal(path)
        book = {p["symbol"]: {"qty": float(p["qty"])} for p in pos if float(p.get("qty") or 0) != 0}
        last = None
        for rec in reversed(tail_lines(path, 4000)):
            if rec.get("event") == "fill" and rec.get("ts"):
                last = rec["ts"]; break
        age = None
        if last:
            try: age = max(0.0, (ctx.now - _dt.fromisoformat(str(last).replace("Z", "+00:00"))).total_seconds() / 86400.0)
            except Exception: age = None
        return book, age
    except Exception:
        return None, None

def _evaluate_v2(ctx):
    syms = symbols_for(ctx)
    bars = fetch_bars(ctx, syms, "1Day", 60)
    derived = {"sleeve_state": sleeve_state_from_positions(ctx)}
    _book, _age = _mom_book(ctx)
    if _book is not None:
        derived.setdefault("momentum_book", _book)
        derived.setdefault("momentum_book_age_days", _age)
    for sym in syms:
        try:
            chain = ctx.options_chain(sym)
        except Exception:
            chain = None
        if isinstance(chain, dict) and ("chains" in chain or "quotes" in chain):
            for k in ("chains", "quotes"):
                if isinstance(chain.get(k), dict):
                    derived.setdefault(k, {}).update(chain[k])
    old = make_old_context(ctx, derived)
    out = translate_intents(strat.signal(bars, {}, old), SLEEVE_ID, ctx, held_map(ctx))
    for d in out:  # PMCC short sales / roll buy-backs are named in the reason
        if "pmcc_short" in d["reason"] and d["kind"] == "entry": d["side"] = "sell"
        if "pmcc_roll" in d["reason"] and d["kind"] == "exit": d["side"] = "buy"
    return out


def evaluate(view, ctx):
    return evaluate_via(view, ctx, _evaluate_v2)
