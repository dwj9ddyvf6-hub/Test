"""free_opt_pair: the source desk's FREE_OPT_PAIR_V1 decision path vs the port (tools/parity/free_options_common.py)."""
from .free_options_common import run_for


def run():
    return run_for("free_opt_pair", "FREE_OPT_PAIR_V1")
