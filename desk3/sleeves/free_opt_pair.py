"""v3 adapter for free_opt_pair: snapshot view -> v2 old-contract signal ->
v3 intent dicts. Faithful port of the muse-desk-v2 adapter; strategy
math lives unedited in desk3/strategies/free_opt_pair.py (single import-line
diff vs v2). Producer inputs arrive in the snapshot (view["extra"],
view["kraken_inputs"], view["options_chain"], view["bars"])."""
from desk3.bridge import ViewCtx, build_extra, old_bars, old_context, to_v2_intents

from desk3.strategies.free_opt_pair import signal as _signal
from desk3.enh2_edge16 import filter_package_expiry_coherence
SLEEVE_ID = "free_opt_pair"
INPUTS = ("options",)

def evaluate(view, ctx):
    c = ViewCtx(view, ctx)
    extra = build_extra(c)
    out = to_v2_intents(c, SLEEVE_ID, _signal({}, {}, old_context(c, extra)))
    # ENH2 (Edge16): refuse packages whose legs expire on different dates.
    return filter_package_expiry_coherence(out, view.get("extra") or {}, SLEEVE_ID)
