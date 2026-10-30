"""v3 port of v2 sleeve legends_ema (batch 4).

Strategy: desk3/vendor/sleeves/legends_ema.py — byte-identical copy of the v2
sleeve (sha256-pinned by tests/test_port_batch4_blockers.py).
Adapter: the v2 adapter body below, copied with import lines rewritten
to the vendored bridge (desk3/port4_bridge.py) only; logic untouched,
including every Edge enhancement switch/default and gap-audit cure.
Inputs are re-expressed as the INPUTS producer-registry declaration;
evaluate(view, ctx) serves them from the v3 snapshot via
desk3/port4_context.py.
"""
from desk3.port4_context import evaluate_via

INPUTS = ('bars:QQQ:15Min', 'bars:QQQ:1Day', 'positions', 'journal:self')

from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from desk3.port4_bridge import CANDIDATES, ET, OldContext
from desk3.port4_bridge import bar_dict_common as bar_dict
from desk3.port4_bridge import epoch_common as _epoch
from desk3.port4_bridge import fetch_bars, held_map, make_old_context
from desk3.port4_bridge import state_common as sleeve_state_from_positions
from desk3.port4_bridge import symbols_for
from desk3.port4_bridge import translate_common as translate_intents

from datetime import timezone
from desk3.port4_context import load_strategy
strat = load_strategy("legends_ema")
SLEEVE_ID = "legends_ema"
WARMUP_BARS = {"15Min": 200, "1Day": 14}
def _evaluate_v2(ctx):
    daily = fetch_bars(ctx, ["QQQ"], "1Day", 30)
    m15 = fetch_bars(ctx, ["QQQ"], "15Min", 600)
    derived = {"sleeve_state": sleeve_state_from_positions(ctx)}
    rows = (m15.get("QQQ") or [])
    if rows:
        sessions = {}
        for b in rows:
            d = datetime.fromtimestamp(float(b["t"]), tz=timezone.utc).astimezone(ET).date().isoformat()
            sessions.setdefault(d, []).append(b)
        derived["bars_15m_by_session"] = [sessions[d] for d in sorted(sessions)]
    dr = daily.get("QQQ") or []
    if dr:
        derived["daily_ranges"] = [float(b["h"]) - float(b["l"]) for b in dr]
    # GAP-CURE: run the class directly so the ENH stamp survives;
    # serve the persisted legends_ema_exp_journal and file the new one
    # (module-level signal() discarded both every pass).
    from adapters._bridge import serve_journal
    served = serve_journal(ctx, "legends_ema_exp_journal")
    if served is not None:
        derived["legends_ema_exp_journal"] = served
    old = make_old_context(ctx, derived)
    bars = {"QQQ": dr} if dr else {}
    inst = strat.LegendsEma()
    intents = inst.signal(bars, {}, old) or []
    stamp = getattr(inst, "last_evaluation", None) or {}
    if isinstance(stamp.get("legends_ema_exp_journal"), dict):
        try: ctx.log("legends_ema_exp_journal", journal=stamp["legends_ema_exp_journal"])
        except Exception: pass
    return translate_intents(intents, SLEEVE_ID, ctx, held_map(ctx))


def evaluate(view, ctx):
    return evaluate_via(view, ctx, _evaluate_v2)
