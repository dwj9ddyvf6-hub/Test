"""Blocker for PANEL-END-RECENT-SIP-20261102.

fetch_bars must cap a future request end at now minus 20 minutes so
the scheduled post-close advance never queries inside the
subscription's recent SIP window (403). An end already in the past
passes through unchanged.
"""
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, "site")
sys.path.insert(0, "forecast")
import advance_price_panel as app


def test_future_end_is_capped():
    tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).date().isoformat()
    capped = app._capped_end(tomorrow)
    cap_dt = datetime.fromisoformat(capped.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    assert cap_dt <= now - timedelta(minutes=19), capped
    assert cap_dt >= now - timedelta(minutes=25), capped


def test_past_end_passes_through():
    assert app._capped_end("2026-10-30") == "2026-10-30T00:00:00Z"


if __name__ == "__main__":
    test_future_end_is_capped()
    test_past_end_passes_through()
    print("PASS")
