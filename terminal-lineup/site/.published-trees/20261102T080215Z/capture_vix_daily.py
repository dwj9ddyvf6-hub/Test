#!/usr/bin/env python3
"""Daily VIX and VIX3M close capture (hookup cure, 2026-10-30).

The terminal's fear family and Engine 1 (Corrected Band) read one
VIX store: the raw Yahoo chart response at
~/workspace/opt/rea-teardowns/azrael-1587/source/yahoo-vix-daily.json.
That file was a one-off fetch (23 readings, ending 2026-10-21) and
no lane ever advanced it, and no VIX3M series existed anywhere, so
Engine 1's registered backwardation state (VIX above VIX3M, AD-59)
was permanently no_data and the Fear Day record stayed one local
day. This lane is the single continuing capture for both series:
Yahoo daily closes, price only (Yahoo hourly volume is corrupt and
is never requested or used here). Each response is stored verbatim
in the chart shape the existing readers parse, so no reader changes
its source: the VIX file keeps its existing path, and VIX3M lands
beside it as yahoo-vix3m-daily.json.

Fail closed: a series with no usable closes writes nothing and the
lane exits non-zero, leaving the prior store on disk.

Usage: python3 capture_vix_daily.py
"""

import json
import os
import sys
import urllib.parse
import urllib.request

STORE_DIR = os.path.expanduser(
    "~/workspace/opt/rea-teardowns/azrael-1587/source")
SERIES = {
    "^VIX": os.path.join(STORE_DIR, "yahoo-vix-daily.json"),
    "^VIX3M": os.path.join(STORE_DIR, "yahoo-vix3m-daily.json"),
}
URL = ("https://query1.finance.yahoo.com/v8/finance/chart/{sym}"
       "?range=2y&interval=1d")


def fetch(symbol):
    req = urllib.request.Request(
        URL.format(sym=urllib.parse.quote(symbol)),
        headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as fh:
        return json.load(fh)


def usable_closes(doc):
    result = doc["chart"]["result"][0]
    closes = result["indicators"]["quote"][0]["close"]
    return sum(1 for c in closes if c is not None)


def main():
    written = []
    for symbol, path in SERIES.items():
        doc = fetch(symbol)
        n = usable_closes(doc)
        if n < 30:
            print(f"FAIL: {symbol} returned only {n} usable closes; "
                  f"leaving {path} untouched")
            return 1
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(doc, fh)
            fh.write("\n")
        os.replace(tmp, path)
        written.append(f"{symbol}: {n} closes -> {path}")
    for line in written:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
