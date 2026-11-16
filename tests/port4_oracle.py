"""Oracle driver (NOT a test): run a v2 adapter on a fixture scenario and
print its intents as JSON. Executed as a subprocess with the v2 repo as
cwd/PYTHONPATH by tests/test_port_batch4_blockers.py. v2 is read-only;
this only imports and evaluates in-memory.

Scenario JSON on stdin:
  {sleeve_id, now, bars: {"SYM|TF": [bar,...]}, positions: [...],
   extra: {...}, cash: float}
Prints: [intent, ...]
"""
import importlib.util
import json
import os
import sys
from datetime import datetime
from types import SimpleNamespace

def _find_v2():
    """Same resolution as tests/test_port_batch4_blockers._find_v2:
    the v2 tree is a property of this box, not of this file's
    location (a relocated checkout otherwise looks for a sibling
    that does not exist; clean-export failure, 2026-11-08). The
    test passes its resolved tree via MUSE_DESK_V2_DIR."""
    cands = [os.environ.get("MUSE_DESK_V2_DIR"),
             os.path.abspath(os.path.join(os.path.dirname(__file__),
                                          "..", "..", "muse-desk-v2")),
             os.path.expanduser("~/workspace/muse-desk-v2")]
    for cand in cands:
        if cand and os.path.isdir(cand):
            return cand
    return cands[1]


ROOT = _find_v2()
sys.path.insert(0, ROOT)
ADAPTERS = os.path.join(ROOT, "adapters")


class FakeCtx:
    """Same shape as v2 tests' FakeCtx (test_batch4_fixture.py)."""

    def __init__(self, now_iso, bars=None, positions=None, extra=None,
                 cash=10000.0):
        self.now = datetime.fromisoformat(now_iso)
        self.sleeve_id = "fake"
        self._bars = bars or {}
        self.positions = positions or []
        self.slice = {"capital_usd": cash, "cash_usd": cash}
        self.params = {"extra": extra or {}}

    def bars(self, sym, tf, n):
        rows = self._bars.get((sym, tf)) or []
        return [SimpleNamespace(t=r["t"], o=r["o"], h=r["h"], l=r["l"],
                                c=r["c"], v=r["v"]) for r in rows[-n:]]

    def options_chain(self, u):
        return None

    def log(self, event, **f):
        pass


def main():
    sc = json.load(sys.stdin)
    bars = {}
    for key, rows in (sc.get("bars") or {}).items():
        sym, tf = key.rsplit("|", 1)
        bars[(sym, tf)] = rows
    ctx = FakeCtx(sc["now"], bars=bars, positions=sc.get("positions") or [],
                  extra=sc.get("extra") or {}, cash=sc.get("cash", 10000.0))
    spec = importlib.util.spec_from_file_location(
        f"adapter_{sc['sleeve_id']}",
        os.path.join(ADAPTERS, f"{sc['sleeve_id']}.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    out = mod.evaluate(ctx) or []
    json.dump(out, sys.stdout, sort_keys=True)


if __name__ == "__main__":
    main()
