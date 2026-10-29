"""free_opt_parity: the source desk's FREE_OPT_PARITY_V1 decision path vs the port (tools/parity/free_options_common.py)."""
from .free_options_common import run_for


def run():
    return run_for("free_opt_parity", "FREE_OPT_PARITY_V1")
