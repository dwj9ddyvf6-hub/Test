#!/usr/bin/env python3
"""Regression blocker DESK-PRIVACY-20261103.

The hourly public sync (sync_to_test.py) must never publish private
desk payload fields (account, balances, buying power, equity,
positions, money assigned, starting capital) to the public Test repo.
On 2026-11-03 the 13:13 ET sync re-published the raw producer desk
payload over a sanitized public copy. These tests pin the gate:

- raw desk JSON payloads are refused at candidate_for(),
- terminal_feed.json is refused by name anywhere in the tree,
- archived .published-trees snapshots are excluded from the sync set,
- the desk page is refused while it reads the internal feed,
- clean desk JSON and non-desk files are NOT blocked (scope discipline).

Run: python3 test_sync_desk_privacy_gate_20261103.py
"""
import importlib.util
import json
import sys
from pathlib import Path
import tempfile

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "sync_to_test", HERE / "sync_to_test.py")
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)

FAILURES = []


def check(name, cond, detail=""):
    if cond:
        print(f"PASS {name}")
    else:
        print(f"FAIL {name} {detail}")
        FAILURES.append(name)


RAW_DESK = json.dumps({
    "account": {"buying_power": 1.0, "cash": 2.0, "equity": 3.0},
    "epoch": {"starting_capital": 1000000},
    "positions": [{"symbol": "SPY", "qty": 5}],
}).encode()

# 1. Raw desk data payload is refused.
cand, reason = sync.candidate_for("site/desk/data.json", RAW_DESK)
check("raw desk data.json refused",
      cand is None and reason and "privacy" in reason.lower(),
      f"cand={cand is not None} reason={reason}")

# 2. terminal_feed.json refused by name, even with innocuous content.
cand, reason = sync.candidate_for("site/desk/terminal_feed.json", b"{}")
check("terminal_feed.json refused by name (desk)",
      cand is None and reason and "privacy" in reason.lower(),
      f"reason={reason}")

# 3. terminal_feed.json refused anywhere in the tree.
cand, reason = sync.candidate_for("forecast/terminal_feed.json", b"{}")
check("terminal_feed.json refused by name (anywhere)",
      cand is None and reason and "privacy" in reason.lower(),
      f"reason={reason}")

# 4. Attractions payload (money assigned, position cost) is refused.
cand, reason = sync.candidate_for(
    "site/desk/attractions.json",
    json.dumps({"families": [{"money_assigned": 10}],
                "positions_cost": [{"symbol": "SPY", "cost": 1}]}).encode())
check("attractions payload refused",
      cand is None and reason and "privacy" in reason.lower(),
      f"reason={reason}")

# 5. Archived snapshot desk payload is refused AND snapshots are
#    excluded from the sync set entirely.
cand, reason = sync.candidate_for(
    "site/.published-trees/20261103T002321Z/desk/data.json", RAW_DESK)
check("snapshot desk payload refused",
      cand is None and reason and "privacy" in reason.lower(),
      f"reason={reason}")
# Keep the sync-set check hermetic: build a temporary source tree with one
# active desk file and one archived snapshot, then prove snapshots are excluded.
old_root = sync.ROOT
with tempfile.TemporaryDirectory(prefix="desk-privacy-test-") as tmp:
    sync.ROOT = Path(tmp)
    active = sync.ROOT / "site" / "desk"
    archive = sync.ROOT / "site" / ".published-trees" / "fixture" / "desk"
    active.mkdir(parents=True)
    archive.mkdir(parents=True)
    (active / "data.json").write_text("{}", encoding="utf-8")
    (archive / "data.json").write_text("{}", encoding="utf-8")
    included = sync.included_files()
    check("no .published-trees paths in sync set",
          "site/desk/data.json" in included
          and not any(".published-trees" in p for p in included))
sync.ROOT = old_root

# 6. Unparseable desk JSON fails closed.
cand, reason = sync.candidate_for("site/desk/data.json", b"{not json")
check("unparseable desk JSON refused (fail closed)",
      cand is None and reason and "privacy" in reason.lower(),
      f"reason={reason}")

# 7. Desk page that reads the internal feed is refused.
cand, reason = sync.candidate_for(
    "site/desk/index.html",
    b'<script>fetch("terminal_feed.json")</script>')
check("desk page reading internal feed refused",
      cand is None and reason and "privacy" in reason.lower(),
      f"reason={reason}")

# 8. Clean desk JSON still publishes (gate is not a blanket desk ban).
cand, reason = sync.candidate_for(
    "site/desk/data.json",
    json.dumps({"series": [1, 2, 3],
                "strategies": [{"name": "x", "return_pct": 1.5}]}).encode())
check("clean desk JSON publishes", cand is not None,
      f"reason={reason}")

# 9. Non-desk file with a 'cash' key is NOT caught by the desk gate.
cand, reason = sync.candidate_for(
    "site/some-tool/data.json", b'{"cash": 1, "note": "fine"}')
check("non-desk cash key untouched", cand is not None,
      f"reason={reason}")

# 10. Unsafe payloads are refused at active, temporary and archived desk
#     paths, while the safe public V2 projection remains publishable.
unsafe_paths = (
    "site/desk/data.json",
    "site/desk/data.json.tmp",
    "site/.published-trees/fixture/desk/data.json",
    "site/.published-trees/fixture/desk/data.json.tmp",
)
for rel in unsafe_paths:
    cand, reason = sync.candidate_for(rel, RAW_DESK)
    check(f"unsafe desk JSON refused ({Path(rel).name})",
          cand is None and reason and "privacy" in reason.lower(),
          f"reason={reason}")

SAFE_PUBLIC = json.dumps({
    "schema": "PEER_BREADTH_PUBLIC_DESK_FEED_V2",
    "generated_at": "2030-01-02T03:04:05Z",
    "cycle_id": "synthetic-cycle",
}).encode()
for rel in unsafe_paths:
    cand, reason = sync.candidate_for(rel, SAFE_PUBLIC)
    check(f"safe public feed allowed ({Path(rel).name})",
          cand is not None and reason is None,
          f"reason={reason}")

print("RESULT:", "ALL PASS" if not FAILURES else f"{len(FAILURES)} FAILED")
sys.exit(1 if FAILURES else 0)
