"""D20-POOL-FALLBACK-20261104 blockers.

Live failure, 2026-11-02: one hard worker death broke the
rebuild's single ProcessPoolExecutor and the run mass-errored:
1,808 of 1,817 symbols excluded as
"unavailable_after_retry: BrokenProcessPool" while each symbol
built fine in-process. The store has been degraded since
(manifest parity-20261102-v2, 9 built symbols) and both daily20
sleeves trade on it.

Cure: the pool submits in waves of 64 with a fresh executor per
wave; a wave whose pool breaks falls back to serial in-process
_build_one calls for its uncollected symbols, with the same
per-symbol ledger appends, and a built symbol's scratch dir is
removed after collection.

Fail direction: pre-cure the broken pool's futures all surface
as per-symbol errors, the retry pool breaks identically, and
every symbol ends excluded; nothing is built.
"""
import os, sys, tempfile, unittest
from concurrent.futures import Future
from concurrent.futures.process import BrokenProcessPool

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import concurrent.futures as cf  # noqa: E402
import desk3.daily20_producer as d20  # noqa: E402


class _BrokenPool:
    def __init__(self, max_workers=None):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def submit(self, fn, *args):
        fut = Future()
        fut.set_exception(BrokenProcessPool("worker died"))
        return fut


class D20PoolFallbackTests(unittest.TestCase):
    def test_broken_pool_falls_back_to_in_process_builds(self):
        root = tempfile.mkdtemp(prefix="d20-test-")
        syms = ["AAA", "BBB", "CCC"]
        real_pool = cf.ProcessPoolExecutor
        real_build_one = d20._build_one
        real_anchors = d20._anchors
        real_handoff = d20._handoff
        self.addCleanup(setattr, cf, "ProcessPoolExecutor", real_pool)
        self.addCleanup(setattr, d20, "_build_one", real_build_one)
        self.addCleanup(setattr, d20, "_anchors", real_anchors)
        self.addCleanup(setattr, d20, "_handoff", real_handoff)
        cf.ProcessPoolExecutor = _BrokenPool
        d20._anchors = lambda: {s: {"symbol": s} for s in syms}
        d20._handoff = lambda: None
        built_in_process = []

        def fake_build_one(symbol, anchor, sdir, tmp_dir):
            built_in_process.append(symbol)
            rows_dir = os.path.join(sdir, "rows")
            os.makedirs(rows_dir, exist_ok=True)
            with open(os.path.join(rows_dir, symbol + ".json.gz"),
                      "wb") as fh:
                fh.write(b"rows")
            return {"symbol": symbol, "status": "built"}

        d20._build_one = fake_build_one
        manifest = d20.build_store(root=root, symbols=syms, workers=3,
                                   build_id="test-broken-pool")
        self.assertTrue(manifest["complete"], manifest)
        self.assertEqual(
            {s: e["status"] for s, e in manifest["symbols"].items()},
            {s: "built" for s in syms})
        self.assertEqual(sorted(built_in_process), syms)


if __name__ == "__main__":
    unittest.main()
