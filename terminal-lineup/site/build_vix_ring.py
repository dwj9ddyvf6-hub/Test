#!/usr/bin/env python3
"""AMAZING Build (2026-11-02): VIX ring data for the market-mood page.

Reads the VIX daily store the capture lane (capture_vix_daily.py)
maintains and writes site/market-mood/vix-ring.json with the latest
reading and its own date, so the ring card on market-mood can show
the reading with the date it belongs to and never draw it as newer
than it is. Bands are the plain market convention printed on the
card: under 15 calm, 15 to 20 normal, 20 to 30 uneasy, 30 and over
stressed. Nothing is computed beyond reading the store's last
close.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

STORE = Path.home() / "workspace/opt/rea-teardowns/azrael-1587/source/yahoo-vix-daily.json"
OUT = Path(__file__).with_name("market-mood") / "vix-ring.json"


def main():
    raw = json.loads(STORE.read_text())
    result = raw["chart"]["result"][0]
    stamps = result["timestamp"]
    closes = result["indicators"]["quote"][0]["close"]
    pairs = [(t, c) for t, c in zip(stamps, closes) if c]
    t, close = pairs[-1]
    date = datetime.fromtimestamp(t, timezone.utc).date().isoformat()
    band = ("Calm" if close < 15 else "Normal" if close < 20
            else "Uneasy" if close < 30 else "Stressed")
    OUT.write_text(json.dumps({
        "instrument": "VIX (volatility index)",
        "value": round(float(close), 2),
        "date": date,
        "band": band,
        "bands": "Under 15 calm, 15 to 20 normal, 20 to 30 uneasy, 30 and over stressed",
        "source": "VIX daily closes captured from Yahoo chart data by capture_vix_daily.py",
    }, indent=2) + "\n")
    print(f"vix-ring: {close:.2f} on {date} ({band})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
