"""Blockers: worker-pool isolation (CORE-1), no-network evaluation (CORE-2),
snapshot immutability + integrity (CORE-3). Fail on pre-core tree (no desk3)."""
import json, os, subprocess, sys, tempfile, textwrap, time, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

FIXTURES = {
    "good_sleeve": '''
        def evaluate(view, ctx):
            bars = view["bars"]["SPY"]
            return [{"intent_id": ctx["cycle_id"] + "-e1", "kind": "entry",
                     "symbol": "SPY", "side": "buy", "qty": 1,
                     "limit_price": bars[-1]["c"], "order_type": "limit"}]
    ''',
    "loop_sleeve": '''
        def evaluate(view, ctx):
            while True:
                pass
    ''',
    "crash_sleeve": '''
        import os
        def evaluate(view, ctx):
            os._exit(3)
    ''',
    "net_sleeve": '''
        import socket
        def evaluate(view, ctx):
            try:
                socket.create_connection(("1.1.1.1", 443), timeout=2).close()
                net = "REACHED"
            except Exception as e:
                net = "BLOCKED:" + type(e).__name__
            return [{"intent_id": ctx["cycle_id"] + "-n1", "kind": "entry",
                     "symbol": "SPY", "side": "buy", "qty": 1,
                     "limit_price": 1.0, "order_type": "limit",
                     "note": net}]
    ''',
    "env_sleeve": '''
        import os
        def evaluate(view, ctx):
            return [{"intent_id": ctx["cycle_id"] + "-v1", "kind": "entry",
                     "symbol": "SPY", "side": "buy", "qty": 1,
                     "limit_price": 1.0, "order_type": "limit",
                     "note": "SECRET=" + str(os.environ.get("DESK3_TEST_SECRET"))}]
    ''',
}


def write_fixtures(d):
    for name, src in FIXTURES.items():
        with open(os.path.join(d, name + ".py"), "w") as fh:
            fh.write(textwrap.dedent(src))


class PoolBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.fixdir = os.path.join(self.tmp, "fixtures")
        os.makedirs(self.fixdir)
        write_fixtures(self.fixdir)
        self.state = os.path.join(self.tmp, "state")
        from desk3.snapshot import build_snapshot, save_snapshot
        snap = build_snapshot({"bars": {"SPY": [{"t": "2026-10-23T19:00:00Z",
                                                 "o": 1, "h": 1, "l": 1, "c": 100.0, "v": 1}]}},
                              asof="2026-10-23T19:00:00Z")
        self.snap_path = save_snapshot(snap, os.path.join(self.state, "snapshots"))
        self.snap_hash = snap.hash

    def task(self, sid, module):
        return {"sleeve_id": sid, "module": module, "snapshot_path": self.snap_path,
                "snapshot_hash": self.snap_hash,
                "ctx": {"cycle_id": "c1", "sleeve_id": sid,
                        "state_dir": os.path.join(self.state, sid)}}


class TestPoolIsolation(PoolBase):
    def test_infinite_loop_cannot_stall_cycle(self):
        from desk3.pool import WorkerPool
        pool = WorkerPool(size=2, sleeve_path=self.fixdir, state_root=self.state,
                          timeout_s=2.0)
        try:
            t0 = time.monotonic()
            res = pool.run([self.task("loopy", "loop_sleeve"),
                            self.task("good", "good_sleeve")])
            wall = time.monotonic() - t0
        finally:
            pool.close()
        self.assertLess(wall, 20)
        self.assertEqual(res["loopy"]["status"], "wedged")
        self.assertEqual(res["good"]["status"], "ok")
        self.assertEqual(len(res["good"]["intents"]), 1)

    def test_crash_kills_and_respawns_worker(self):
        from desk3.pool import WorkerPool
        pool = WorkerPool(size=1, sleeve_path=self.fixdir, state_root=self.state,
                          timeout_s=5.0)
        try:
            r1 = pool.run([self.task("crasher", "crash_sleeve")])
            r2 = pool.run([self.task("good", "good_sleeve")])
        finally:
            pool.close()
        self.assertIn(r1["crasher"]["status"], ("wedged", "error"))
        self.assertEqual(r2["good"]["status"], "ok")

    def test_worker_env_has_no_secrets(self):
        from desk3.pool import WorkerPool
        os.environ["DESK3_TEST_SECRET"] = "hunter2"
        pool = WorkerPool(size=1, sleeve_path=self.fixdir, state_root=self.state,
                          timeout_s=5.0)
        try:
            res = pool.run([self.task("envy", "env_sleeve")])
        finally:
            pool.close()
            del os.environ["DESK3_TEST_SECRET"]
        self.assertEqual(res["envy"]["intents"][0]["note"], "SECRET=None")


class TestNoNetworkEval(PoolBase):
    def test_evaluation_under_unshare_no_network(self):
        """Whole pool runs inside `unshare -rn` (no network namespace):
        evaluation must still complete from the snapshot alone."""
        code = textwrap.dedent(f'''
            import json, sys
            sys.path.insert(0, {ROOT!r})
            from desk3.pool import WorkerPool
            pool = WorkerPool(size=1, sleeve_path={self.fixdir!r},
                              state_root={self.state!r}, timeout_s=10.0)
            task = {json.dumps(self.task("netty", "net_sleeve"))}
            res = pool.run([task])
            pool.close()
            print("RESULT=" + json.dumps(res))
        ''')
        out = subprocess.run(["unshare", "-rn", sys.executable, "-c", code],
                             capture_output=True, text=True, timeout=60)
        self.assertEqual(out.returncode, 0, out.stderr[-2000:])
        line = [l for l in out.stdout.splitlines() if l.startswith("RESULT=")][0]
        res = json.loads(line[len("RESULT="):])
        self.assertEqual(res["netty"]["status"], "ok")
        self.assertTrue(res["netty"]["intents"][0]["note"].startswith("BLOCKED"))


class TestSnapshot(unittest.TestCase):
    def test_immutable_and_hash_verified(self):
        from desk3.snapshot import build_snapshot
        snap = build_snapshot({"bars": {"SPY": [{"c": 1.0}]}}, asof="t0")
        with self.assertRaises(TypeError):
            snap.data["bars"] = {}
        with self.assertRaises(TypeError):
            snap.data["bars"]["SPY"][0]["c"] = 2.0
        self.assertTrue(snap.verify())

    def test_corrupt_snapshot_detected(self):
        from desk3.snapshot import build_snapshot, save_snapshot, load_snapshot, SnapshotCorrupt
        tmp = tempfile.mkdtemp()
        snap = build_snapshot({"a": 1}, asof="t0")
        path = save_snapshot(snap, tmp)
        with open(path) as fh:
            doc = json.load(fh)
        doc["data"]["a"] = 999
        with open(path, "w") as fh:
            json.dump(doc, fh)
        with self.assertRaises(SnapshotCorrupt):
            load_snapshot(path)


if __name__ == "__main__":
    unittest.main()
