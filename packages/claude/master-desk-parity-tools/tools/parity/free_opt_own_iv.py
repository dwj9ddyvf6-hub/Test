"""free_opt_own_iv: the source desk's FREE_OPT_OWN_IV_V1 decision path vs the port (tools/parity/free_options_common.py)."""
from .free_options_common import run_for


def run():
    return run_for("free_opt_own_iv", "FREE_OPT_OWN_IV_V1")
