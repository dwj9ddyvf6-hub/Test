"""v3 sleeve module for free_kraken_ada_breakdown_varspot — spot-expression
variation of free_kraken_ada_breakdown (PF-SPOT-VARIATIONS-20261116).

The v3 worker entrypoint: evaluate(view, ctx) rebuilds the v2
SleeveContext from the cycle snapshot and delegates to the
variation's own adapter/strategy (adapters/ + sleeves/, new files;
the parent's files are byte-untouched).
"""
from adapters3._snapshot_ctx import evaluate_ported

SLEEVE_ID = "free_kraken_ada_breakdown_varspot"


def evaluate(view, ctx):
    return evaluate_ported(SLEEVE_ID, view, ctx)
