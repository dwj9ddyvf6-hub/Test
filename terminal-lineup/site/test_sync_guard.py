#!/usr/bin/env python3
"""Regression blocker: zero-byte publish guard (HUB-BLANK-20261102).

The hub (site/index.html) was truncated to 0 bytes at source on
2026-11-02 17:58Z by a writer killed mid-write inside a
memory-saturation window, and the hourly sync then published the
empty file: the public hub served a blank page. The systemic cure
is in sync_to_test.py: zero_byte_violations() refuses, before any
upload, (a) any zero-byte .html page file outright, and (b) any
zero-byte file whose repo version is non-empty. A refused publish
fails loud (nonzero exit, named file), never silently skips.

Fail-first: on the pre-guard sync_to_test.py this test fails
(zero_byte_violations does not exist, and its source carries no
guard call). Run standalone: python3 test_sync_guard.py
(exit 0 = pass).
"""
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent
sys.path.insert(0, str(SITE))


def main() -> int:
    fails = []
    try:
        import sync_to_test as sync
    except Exception as e:  # import must stay network-free
        print(f"FAIL: sync_to_test does not import: {e}")
        return 1
    guard = getattr(sync, "zero_byte_violations", None)
    if guard is None:
        fails.append("sync_to_test.zero_byte_violations missing: "
                     "a staged zero-byte page would be published")
    else:
        # (a) zero-byte .html refused outright, even with no repo copy.
        v = guard([("site/index.html", b"")], {})
        if not any("site/index.html" in x for x in v):
            fails.append("zero-byte .html not refused: %r" % (v,))
        # (b) zero-byte file refused when the repo version is non-empty.
        v = guard([("site/data.json", b"")],
                  {"terminal-lineup/site/data.json": 1234})
        if not any("site/data.json" in x for x in v):
            fails.append("zero-byte shrink of a non-empty repo file "
                         "not refused: %r" % (v,))
        # (c) honest cases pass: non-empty page, and a brand-new
        # zero-byte non-page file with no repo version to shrink.
        v = guard([("site/index.html", b"<html>ok</html>"),
                   ("site/new-note.txt", b"")], {})
        if v:
            fails.append("guard refused honest candidates: %r" % (v,))
        # (d) the OLD behaviour is exactly what the guard must stop:
        # an empty candidate differs from the repo blob, so the
        # pre-guard census would have queued and published it.
        if sync.blob_sha(b"") == "4e03b3bdc41fbc059244c10597eecc2cee4cad26":
            fails.append("empty blob unexpectedly equals the hub blob")
    src = (SITE / "sync_to_test.py").read_text(encoding="utf-8")
    if "zero_byte_violations(changed" not in src:
        fails.append("main() does not run the guard over the changed set")
    if "GUARD REFUSAL" not in src:
        fails.append("guard refusal is not a loud named failure")
    # refresh_hub must write atomically (temp + rename in same dir):
    # an in-place write is what left the 0-byte hub behind.
    hub_src = (SITE / "refresh_hub.py").read_text(encoding="utf-8")
    if "os.replace" not in hub_src or "_atomic_write" not in hub_src:
        fails.append("refresh_hub.py does not write the hub atomically")
    if "HUB.write_text" in hub_src:
        fails.append("refresh_hub.py still writes the hub in place")
    for f in fails:
        print("FAIL:", f)
    if fails:
        return 1
    print("PASS: zero-byte publish guard + atomic hub write")
    return 0


if __name__ == "__main__":
    sys.exit(main())
