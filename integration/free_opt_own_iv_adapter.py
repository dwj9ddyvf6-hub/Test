"""v3 adapter for free_opt_own_iv: snapshot view -> v2 old-contract signal ->
v3 intent dicts. Faithful port of the muse-desk-v2 adapter; strategy
math lives unedited in desk3/strategies/free_opt_own_iv.py (single import-line
diff vs v2). Producer inputs arrive in the snapshot (view["extra"],
view["kraken_inputs"], view["options_chain"], view["bars"])."""
from desk3.bridge import ViewCtx, build_extra, old_bars, old_context, to_v2_intents

from desk3.strategies.free_opt_own_iv import signal as _signal
SLEEVE_ID = "free_opt_own_iv"
INPUTS = ("options",)

def evaluate(view, ctx):
    c = ViewCtx(view, ctx)
    extra = build_extra(c)
    return to_v2_intents(c, SLEEVE_ID, _signal({}, {}, old_context(c, extra)))
