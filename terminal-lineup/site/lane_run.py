#!/usr/bin/env python3
"""Producer lanes by cadence class (liveness phase, 2026-10-31).

One runner, four lanes, each ending the same way: enrich every page,
rebuild the hub (refresh_hub.py, which also republishes desk/), stamp
a watermark in lane_state.json, and append ONE freshness line to
terminal-lineup/lane_freshness.log naming the lane, the result, and
the freshest data file in its class.

    python3 lane_run.py intraday     tape family, market hours only
    python3 lane_run.py hourly       close only (enrich + hub)
    python3 lane_run.py daily-close  close only; the derivation lanes
                                     (engines 17:46, tape 17:30, tools
                                     19:00, stores 18:46, psychology
                                     18:15) run earlier the same
                                     evening under their own crons
    python3 lane_run.py weekly       the five weekly pages, then close

The intraday market-hours gate lives here, not in the cron schedule:
Mon-Fri 09:30-16:00 America/New_York. Outside it the lane writes its
watermark as skipped and exits 0; a page never claims freshness
faster than its inputs arrive.

Exit 0 only when every producer in the lane and the close succeeded.
"""
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
STATE = HERE / "lane_state.json"
FRESH_LOG = ROOT / "lane_freshness.log"
ET = ZoneInfo("America/New_York")

WEEKLY_SCRIPTS = ["refresh_insider.py", "refresh_insiderdivergence.py",
                  "refresh_13ftracker.py", "refresh_smartmoney.py",
                  "refresh_filings.py"]
CLASS_SLUGS = {
    "intraday": ["flow-tape", "golden-sweep-wire", "activity-profile",
                 "premium-meter", "flow-board", "tape-heatmap",
                 "flow-engine", "alert-tape"],
    "weekly": ["insider-divergence", "insider-wire", "filings-wire",
               "13f-tracker", "smart-money-tracker"],
}


def run(script: str) -> int:
    print(f"--- {script}", flush=True)
    return subprocess.run([sys.executable, script], cwd=str(HERE)).returncode


def market_open(now: datetime) -> bool:
    return (now.weekday() < 5
            and (9, 30) <= (now.hour, now.minute) < (16, 0))


def freshest(slugs) -> str:
    stamps = []
    for slug in slugs:
        p = HERE / slug / "data.json"
        if p.exists():
            stamps.append(p.stat().st_mtime)
    if not stamps:
        return "none"
    return datetime.fromtimestamp(max(stamps), timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


def all_slugs():
    return sorted(p.parent.name for p in HERE.glob("*/data.json"))


def stamp(lane: str, result: str, slugs, note: str = "") -> str:
    now = datetime.now(timezone.utc)
    state = {}
    if STATE.exists():
        try:
            state = json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            state = {}
    state.setdefault("lanes", {})[lane] = {
        "last_run_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "result": result,
        "pages": len(slugs),
        "freshest_data_utc": freshest(slugs),
    }
    STATE.write_text(json.dumps(state, indent=1, sort_keys=True),
                     encoding="utf-8")
    line = (f"{now.strftime('%Y-%m-%dT%H:%M:%SZ')} lane={lane} "
            f"result={result} pages={len(slugs)} "
            f"freshest={freshest(slugs)}" + (f" {note}" if note else ""))
    with FRESH_LOG.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")
    print(line, flush=True)
    return line


def close() -> int:
    code = 0
    for script in ("enrich_all.py", "refresh_hub.py"):
        if run(script) != 0:
            code = 1
    return code


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in (
            "intraday", "hourly", "daily-close", "weekly"):
        print(__doc__)
        return 2
    lane = sys.argv[1]
    slugs = CLASS_SLUGS.get(lane) or all_slugs()
    if lane == "intraday":
        now_et = datetime.now(ET)
        if not market_open(now_et):
            stamp(lane, "skipped-market-closed", slugs,
                  f"et={now_et.strftime('%a %H:%M')}")
            return 0
        code = run("tape_family_run.py")
        if close() != 0:
            code = 1
        stamp(lane, "ok" if code == 0 else "FAILED", slugs)
        return code
    if lane == "weekly":
        code = 0
        for script in WEEKLY_SCRIPTS:
            if run(script) != 0:
                code = 1
        if close() != 0:
            code = 1
        stamp(lane, "ok" if code == 0 else "FAILED", slugs)
        return code
    # hourly and daily-close: the close is the lane. Derivation for
    # daily pages belongs to the post-close lanes named above; this
    # lane re-enriches, republishes the hub and desk, and proves the
    # served tree is the freshest written tree.
    code = close()
    stamp(lane, "ok" if code == 0 else "FAILED", slugs)
    return code


if __name__ == "__main__":
    sys.exit(main())
