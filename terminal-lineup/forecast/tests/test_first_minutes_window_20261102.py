"""Blocker for FIRST-MINUTES-DST-20261102.

The first-minutes fetch window must be the first 30 minutes after
the 09:30 ET open of the session's own date: 13:30-14:00Z under
EDT and 14:30-15:00Z under EST. The pre-cure code hardcoded the
EDT window and read the pre-market hour on the first EST session.
"""
import sys

sys.path.insert(0, "site")
import first_minutes


def test_edt_window():
    assert first_minutes.session_window("2026-10-30") == (
        "2026-10-30T13:30:00Z", "2026-10-30T14:00:00Z")


def test_est_window():
    assert first_minutes.session_window("2026-11-02") == (
        "2026-11-02T14:30:00Z", "2026-11-02T15:00:00Z")


if __name__ == "__main__":
    test_edt_window()
    test_est_window()
    print("PASS")
