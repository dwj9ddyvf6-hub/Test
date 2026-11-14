#!/usr/bin/env python3
"""Regression blocker for LEDGER-APPEND-RACE-20261113.

Defect (2026-11-12 tools run): refresh_proofgate.py died with
"ledger changed repeatedly during the streaming append pass;
refusing to append". The streaming append state's only read
demanded the shared ledger sit still for a whole pass over the
grown (745 MB) file and retried three times; on an evening when
the engines lane was appending to the same ledger, every pass
moved. The classic append path had the mirror race: its tail
read and its write were not serialized, so two lanes could
link onto the same tail.

Cure (forecast/ledger.py): _stream_pass verifies a bounded
snapshot (exactly the bytes present when the pass opened; an
append-only prefix is a complete valid chain), appends that
land during the pass are absorbed by _extend_stream_state
under an inter-process append lock (each delta row
hash-verified onto the state's tail before anything links),
and both write paths take the same lock for their critical
section. Verification is unchanged in strength: every row a
state is built from is hash-verified before its tail is
trusted, and a shrink or a broken link still refuses.

Fail direction: test 3 is the deterministic discriminator.
One streaming-path writer (the engines lane's own append
route) mutates the file every few milliseconds while the
main process builds its streaming state over a padded seed
file; the main process waits until the ledger has provably
grown before building state, so every pre-cure pass attempt
sees a changed stat and the build refuses with "ledger
changed repeatedly during the streaming append pass", the
exact production error of 2026-11-12. On the cured
ledger the same scenario completes with exact dedupe and a
verifying chain. Test 1 is the functional batch test; its
race is timing-dependent at test scale (800-row file, 2 ms
writer) and in Lane C's 2026-11-13 verification run it
PASSED on the pre-cure ledger, so it does not by itself
prove the fail direction; test 3 carries that proof.
Lands together with the cured ledger.py.
"""
import multiprocessing as mp
import os
import sys
import tempfile
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
import ledger as ledger_mod  # noqa: E402

CLOCKS = {c: "2026-11-12" for c in ledger_mod.CLOCK_FIELDS}
LINEAGE = {"clocks": CLOCKS, "source_artifacts": [
    {"path": "/tmp/x", "sha256": "0" * 64}]}


def _classic_writer(path, n, delay):
    led = ledger_mod.Ledger(path)
    for k in range(n):
        led.append_forecast_declared(
            engine_id="engine_01", issued_ts="2026-11-12",
            subject=f"W{k}", quantity="q",
            value={"pad": "x" * 200, "k": k},
            horizon_open="2026-11-12", horizon_close="2026-12-12",
            lineage=LINEAGE, families=["price"],
            outcome={"kind": "test"})
        time.sleep(delay)


def _continuous_writer(path, stop_path):
    # The production condition, one lane: the engines lane
    # appends through the streaming path, whose per-row cost
    # after its state build is a tail check and one write, so
    # the file mutates every few milliseconds all evening.
    # (A classic-path writer does not discriminate at test
    # scale: its dedupe re-parse leaves the file still for
    # ~80 ms at a time, about one whole pass, so a pass can
    # slip through; Lane C measurement, 2026-11-13: pass over
    # a 4.3 MB file 0.09 s, classic append interval 80 ms.)
    # A lane whose append is refused rebuilds its state and
    # keeps coming, so the writer never dies.
    led = ledger_mod.Ledger(path)
    k = 0
    state = None
    while not os.path.exists(stop_path):
        try:
            if state is None:
                state = led.append_stream_state(
                    engine_id="engine_01", issued_ts="2026-11-12")
            led.append_forecast_streaming(
                state, engine_id="engine_01",
                issued_ts="2026-11-12", subject=f"C{k}",
                quantity="q", value={"pad": "x" * 200, "k": k},
                horizon_open="2026-11-12",
                horizon_close="2026-12-12",
                lineage=LINEAGE, families=["price"],
                outcome={"kind": "test"})
            k += 1
        except ledger_mod.LedgerError:
            state = None


def _forecast(led, state, k):
    return led.append_forecast_streaming(
        state, engine_id="engine_19", issued_ts="2026-11-12",
        subject=f"S{k}", quantity="proof state forward check",
        value={"pad": "z" * 300, "k": k},
        horizon_open="2026-11-12", horizon_close="2026-12-12",
        lineage=LINEAGE, families=["price"],
        outcome={"kind": "test"})


class AppendRaceTests(unittest.TestCase):
    def test_streaming_batch_survives_concurrent_appends(self):
        tmp = tempfile.mkdtemp(prefix="ledger-race-test-")
        path = os.path.join(tmp, "ledger.jsonl")
        led = ledger_mod.Ledger(path)
        led.append_genesis("test")
        for k in range(800):
            led.append_forecast_declared(
                engine_id="engine_02", issued_ts="2026-11-11",
                subject=f"F{k}", quantity="q",
                value={"pad": "y" * 1500, "k": k},
                horizon_open="2026-11-11",
                horizon_close="2026-12-11", lineage=LINEAGE,
                families=["price"], outcome={"kind": "test"})
        writer = mp.Process(target=_classic_writer,
                            args=(path, 300, 0.002))
        writer.start()
        try:
            created = duplicates = 0
            state = led.append_stream_state(
                engine_id="engine_19", issued_ts="2026-11-12")
            for k in range(60):
                _row, made = _forecast(led, state, k)
                created += made
                duplicates += (not made)
            state2 = led.append_stream_state(
                engine_id="engine_19", issued_ts="2026-11-12")
            for k in range(60):
                _row, made = _forecast(led, state2, k)
                created += made
                duplicates += (not made)
        finally:
            writer.join(timeout=120)
        self.assertEqual(writer.exitcode, 0)
        self.assertEqual((created, duplicates), (60, 60))
        self.assertTrue(led.verify_chain_streaming())

    def test_streaming_state_survives_continuous_writer(self):
        tmp = tempfile.mkdtemp(prefix="ledger-race-test-")
        path = os.path.join(tmp, "ledger.jsonl")
        stop_path = os.path.join(tmp, "stop")
        led = ledger_mod.Ledger(path)
        led.append_genesis("test")
        for k in range(400):
            led.append_forecast_declared(
                engine_id="engine_02", issued_ts="2026-11-11",
                subject=f"F{k}", quantity="q",
                value={"pad": "y" * 20000, "k": k},
                horizon_open="2026-11-11",
                horizon_close="2026-12-11", lineage=LINEAGE,
                families=["price"], outcome={"kind": "test"})
        size0 = os.path.getsize(path)
        writer = mp.Process(target=_continuous_writer,
                            args=(path, stop_path))
        writer.start()
        try:
            # Build state only once the writer is provably
            # appending: the file must have grown well past
            # one row.
            deadline = time.time() + 120
            while os.path.getsize(path) <= size0 + 200000:
                self.assertLess(time.time(), deadline,
                                "continuous writer never appended")
                time.sleep(0.05)
            created = duplicates = 0
            state = led.append_stream_state(
                engine_id="engine_19", issued_ts="2026-11-12")
            for k in range(60):
                _row, made = _forecast(led, state, k)
                created += made
                duplicates += (not made)
            state2 = led.append_stream_state(
                engine_id="engine_19", issued_ts="2026-11-12")
            for k in range(60):
                _row, made = _forecast(led, state2, k)
                created += made
                duplicates += (not made)
        finally:
            open(stop_path, "w").close()
            writer.join(timeout=120)
        self.assertEqual(writer.exitcode, 0)
        self.assertEqual((created, duplicates), (60, 60))
        self.assertTrue(led.verify_chain_streaming())

    def test_broken_chain_still_refuses(self):
        tmp = tempfile.mkdtemp(prefix="ledger-race-test-")
        path = os.path.join(tmp, "ledger.jsonl")
        led = ledger_mod.Ledger(path)
        led.append_genesis("test")
        with open(path, "a", encoding="utf-8") as fh:
            fh.write('{"type": "forecast", "row_hash": "bad", '
                     '"prev_hash": "bad"}\n')
        with self.assertRaises(ledger_mod.LedgerError):
            led.append_stream_state(engine_id="engine_19",
                                    issued_ts="2026-11-12")


if __name__ == "__main__":
    unittest.main()
