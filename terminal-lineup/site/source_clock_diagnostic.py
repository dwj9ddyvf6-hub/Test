#!/usr/bin/env python3
"""Source clock diagnostic over our own refresh logs (DEEP-PASS 3.2.8).

Reads refresh runner logs, estimates per source how often a refresh
arrived (exit 0), and writes site/source-clock/data.json. This is a
data arrival diagnostic, never a market forecast: it is not ledgered,
not graded, and carries that label in its output. Sources with fewer
than 30 recorded runs are refused an estimate, and the Wilson interval
is suppressed with the estimate (his flaw, fixed on import).

Usage: python3 source_clock_diagnostic.py [log ...]
Default log: ~/workspace/terminal-lineup/refresh_proof.log
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "forecast"))
from diagnostics_patterns import diagnostic_over_refresh_logs  # noqa: E402
try:
    import terminal_common as _tc
except ImportError:
    _tc = None

OUT = os.path.join(HERE, "source-clock", "data.json")
DEFAULT_LOG = os.path.join(ROOT, "refresh_proof.log")


def main(argv):
    paths = argv or [DEFAULT_LOG]
    texts = []
    for path in paths:
        with open(path, encoding="utf-8") as fh:
            texts.append(fh.read())
    data = diagnostic_over_refresh_logs(texts)
    data["tool"] = "Source Clock Diagnostic"
    # Reading date (NO-DATE-CURE-20261117): the diagnostic's
    # evidence is the refresh logs it just read; its reading
    # date is the latest date those logs carry, stated plainly
    # so the canonical freshness resolver finds a date on this
    # store. Before this the store carried no date field at all.
    import re as _re
    _dates = [d for t in texts
              for d in _re.findall(r"\d{4}-\d{2}-\d{2}", t)]
    if _dates:
        data["as_of"] = max(_dates)
        data["as_of_note"] = (
            "The latest date in the refresh logs this diagnostic "
            "read; its estimates are computed over those logs "
            "through that date.")
    if _tc is not None:
        data = _tc.stamp_provenance(
            data, feed="terminal_refresh_logs",
            price_basis="none_diagnostic_only")
    data["sources_read"] = [os.path.basename(p) for p in paths]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=1, sort_keys=True)
    refused = sum(1 for s in data["sources"]
                  if s["state"] == "insufficient_history")
    print(f"source-clock: {len(data['sources'])} sources, "
          f"{refused} refused for insufficient history "
          f"(interval suppressed with the estimate)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
