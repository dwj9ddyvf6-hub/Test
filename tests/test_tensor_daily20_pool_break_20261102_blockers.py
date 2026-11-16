"""D20-POOL-BREAK-20261102 regression blockers.

Incident: the 2026-11-02 weekday rebuilds (build_ids parity-20261102
and parity-20261102-v2) each finalized with 9 built / 1,808 excluded,
every exclusion "unavailable_after_retry: BrokenProcessPool", while
each symbol built fine in-process.

Root cause: pool workers raise tensor_engine.TensorEngineError on a
bad tape (2026-11-02: ABCB's live Yahoo tape). The executor parent
must unpickle that exception off the result pipe, which requires the
tensor_engine module to be importable IN THE PARENT. The producer's
_handoff() inserts HANDOFF_BACKEND into sys.path only in whichever
process calls it; the prescribed launch (python3 -m
desk3.daily20_producer) never called it in the parent, so the first
engine error killed the executor's result thread and every pending
future was reported BrokenProcessPool. The retry pool died the same
way on the same symbol, and the producer converted the wreckage to
excluded-by-name, overwriting a healthy 1,809-built manifest.

Cure: build_store primes the parent via _handoff() before any pool
work. These tests run the scenario in a fresh subprocess whose
parent never imports the engine module itself (mirroring the cron
launch), so they fail on the pre-cure producer and pass on the cure.
"""
import json, os, subprocess, sys, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DRIVER = r"""
import json, os, sys, tempfile
sys.path.insert(0, "__ROOT__")
from desk3 import daily20_producer as p

orig_build_one = p._build_one

def stub(symbol, anchor, sdir, tmp_dir):
    if symbol == "ABCB":
        # Raise the engine's own error type exactly as a worker does:
        # the module is imported here, inside the worker, only.
        te, _tdm = p._handoff()
        raise te.TensorEngineError("probe: invalid prices")
    return orig_build_one(symbol, anchor, sdir, tmp_dir)

p._build_one = stub
root = tempfile.mkdtemp(prefix="d20_pool_break_")
m = p.build_store(root=root, symbols=["ABBV", "ABCB"], workers=3,
                  build_id="pool-break-probe")
out = {}
for sym, e in m["symbols"].items():
    out[sym] = {"status": e.get("status"), "reason": e.get("reason")}
print("PROBE_JSON:" + json.dumps(out))
"""


def _run_driver():
    code = DRIVER.replace("__ROOT__", ROOT)
    proc = subprocess.run([sys.executable, "-c", code], cwd=ROOT,
                          capture_output=True, text=True, timeout=600)
    for line in proc.stdout.splitlines():
        if line.startswith("PROBE_JSON:"):
            return json.loads(line[len("PROBE_JSON:"):]), proc
    raise AssertionError(
        "driver produced no probe output\nstdout:\n%s\nstderr:\n%s"
        % (proc.stdout[-2000:], proc.stderr[-2000:]))


class TestEngineErrorDoesNotBreakPool(unittest.TestCase):
    def test_engine_error_is_named_and_pool_survives(self):
        out, _proc = _run_driver()
        self.assertEqual(set(out), {"ABBV", "ABCB"})
        # The healthy symbol must actually build: on the broken
        # producer it was dragged down as BrokenProcessPool.
        self.assertEqual(out["ABBV"]["status"], "built",
                         "ABBV did not build: %r" % (out["ABBV"],))
        # The engine error must reach the manifest under its own
        # name (error on first pass, excluded on retry), never as a
        # pool failure.
        self.assertIn(out["ABCB"]["status"], ("error", "excluded"))
        self.assertIn("TensorEngineError", out["ABCB"]["reason"] or "")
        for sym, e in out.items():
            self.assertNotIn("BrokenProcessPool", e.get("reason") or "",
                             "%s was lost to a broken pool" % sym)

    def test_build_store_primes_parent_engine_import(self):
        # Source tripwire: build_store must prime the parent-side
        # engine import (_handoff) before the pool runs, so worker
        # exceptions stay unpicklable-proof under any launch route.
        src = open(os.path.join(ROOT, "desk3", "daily20_producer.py")).read()
        body = src[src.index("def build_store"):]
        self.assertIn("\n    _handoff()\n", body)
        self.assertLess(body.index("\n    _handoff()\n"),
                        body.index("def _run_pool"))


if __name__ == "__main__":
    unittest.main()
