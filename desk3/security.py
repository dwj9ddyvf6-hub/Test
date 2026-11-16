"""Security posture: paper-door only. The desk refuses to start pointed at
a live environment; sleeves run in workers with a stripped environment
(see pool.py), so no credential ever reaches sleeve code."""
from __future__ import annotations
import os

PAPER_BASE_URL = "https://paper-api.alpaca.markets"


class LiveTradingRefused(RuntimeError):
    pass


def assert_paper_only(env=None):
    env = os.environ if env is None else env
    if str(env.get("ALPACA_ENV", "")).lower() == "live":
        raise LiveTradingRefused("ALPACA_ENV=live refused: muse-desk-v3 is paper-only")


def assert_paper_url(base_url: str):
    if base_url.rstrip("/") != PAPER_BASE_URL:
        raise LiveTradingRefused(f"non-paper base URL refused: {base_url}")
