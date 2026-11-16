"""TENSOR-STALE-SESSION-WARMER-20261116 blockers.

Root cause (proven from final artifacts, see BUGLOG_2026-11-16.md):
the bundle READERS (desk3/producers.py TensorBundleFile._read_bundle,
CURE-1 2026-11-11) refuse a bundle whose "session" is strictly older
than the cycle's ET calendar session, naming
stale_bundle_session:<session>; the WARMER (desk3/tensor_warm.py
TensorWarmer) decided rebuilds on AGE ONLY (rebuild iff the bundle
is missing or >= WARM_INTERVAL_S = 3600 s old). The two freshness
rules disagree in exactly one window: a cycle that starts after ET
midnight while the on-disk bundle was built less than an hour
before midnight. The warmer sees a fresh bundle and builds nothing;
the readers see a stale session and refuse it, so every
tensor-dependent sleeve is UNFED for that cycle.

Live instances, counted from the journals and the bundle history:
  * Sat 2026-11-14: cycles at 05:07:36Z, 05:21:55Z and 05:31:46Z
    each carry 28 tensor/tensor_fires UNFED journal rows (last
    Friday-session build 2026-11-14T04:37:48Z, session 2026-11-13;
    its age crossed 3600 s only at 05:37:48Z; first Saturday build
    generated 05:45:07Z).
  * Mon 2026-11-16: cycle-1 at 05:06:41Z carries 31 missing-tensor
    + 8 missing-tensor_fires UNFED rows (last Sunday-session build
    2026-11-16T04:14:57Z, session 2026-11-15, age at cycle start
    3,104 s < 3,600 s); the mid-cycle health roll generated
    2026-11-16T05:18Z names stale_bundle_session:2026-11-15 on
    tensor_bundle, tensor_fires and tensor_g4_events (night
    inspection item 6, 41 tensor-dependent sleeves UNFED in that
    roll). The first Monday-session build landed 05:34:01Z, after
    the age bound crossed, and the family cleared.
  * Sun 2026-11-15 shows no tensor UNFED rows: no cycle happened
    to start inside that day's window. The defect is the window,
    not a day.

Cure pinned here (pipeline around the channel; the Tensor ENGINE
and the readers are untouched): the warmer applies the readers'
own session rule as a rebuild trigger — a bundle carrying a
session older than the cycle's ET session is rebuilt in that same
cycle regardless of age — and the build is stamped with the
CYCLE's session (passed from the producer context's now), never a
wall-clock date read mid-build. Age gating for a current-session
bundle, the sessionless legacy shape, the fail-closed readers and
the failure backoff all stand exactly as before.
"""
import hashlib
import json
import os
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Mon 2026-11-16 00:06:41 ET — the live failing cycle-1's start.
NOW_MON = datetime(2026, 11, 16, 5, 6, 41, tzinfo=timezone.utc)
# The live last Sunday-session build stamp (bundle history).
MON_STALE_GEN = "2026-11-16T04:14:57.698643+00:00"
# Sat 2026-11-14 00:07:36 ET — the first live failing Saturday cycle.
NOW_SAT = datetime(2026, 11, 14, 5, 7, 36, tzinfo=timezone.utc)
SAT_STALE_GEN = "2026-11-14T04:37:48.502156+00:00"

FIRE = {"symbol": "ARM", "decision": "TRADE", "entry": 100.0}


def write_bundle(root, session_marker, generated_at):
    d = os.path.join(root, "cache", "tensor")
    os.makedirs(d, exist_ok=True)
    doc = {"generated_at": generated_at, "sleeves": {}, "fires": [FIRE]}
    if session_marker is not None:
        doc["session"] = session_marker
    with open(os.path.join(d, "bundle.json"), "w") as fh:
        json.dump(doc, fh)
    return doc


def recording_builder(calls, generated_at):
    """build_bundle-shaped stub: records the session it was handed
    and writes a bundle stamped with it, generated at the driven
    cycle's instant."""
    def builder(root, session=None):
        calls.append(session)
        write_bundle(root, session, generated_at)
        return {}
    return builder


class TestSessionStaleWarmer(unittest.TestCase):
    def _root(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        return tmp

    def test_age_fresh_session_stale_bundle_rebuilds_and_serves(self):
        from desk3.tensor_warm import TensorWarmer
        from desk3.producers import TensorBundleFile
        for now, stale_sess, gen in (
                (NOW_MON, "2026-11-15", MON_STALE_GEN),
                (NOW_SAT, "2026-11-13", SAT_STALE_GEN)):
            tmp = self._root()
            write_bundle(tmp, stale_sess, gen)
            # the reader alone refuses this bundle at this instant
            rd = TensorBundleFile(tmp, "tensor_fires")
            self.assertEqual(rd({"now": now}), {})
            self.assertEqual(rd.last_error,
                             f"stale_bundle_session:{stale_sess}")
            calls = []
            w = TensorWarmer(tmp, builder=recording_builder(
                calls, now.isoformat()))
            self.assertEqual(w({"now": now}), {})
            self.assertEqual(
                len(calls), 1,
                f"warmer built nothing for the {stale_sess} bundle at "
                f"{now} although the readers refuse it")
            # the build is stamped with the CYCLE's session
            self.assertEqual(calls[0],
                             now.astimezone(ET).date().isoformat())
            # and the same cycle's reader now serves it
            self.assertEqual(
                TensorBundleFile(tmp, "tensor_fires")({"now": now}),
                {"tensor_fires": [FIRE]})
            self.assertIsNone(w.last_error)

    def test_current_session_fresh_bundle_still_skips(self):
        from desk3.tensor_warm import TensorWarmer
        tmp = self._root()
        write_bundle(tmp, "2026-11-16", MON_STALE_GEN)
        calls = []
        w = TensorWarmer(tmp, builder=recording_builder(
            calls, NOW_MON.isoformat()))
        self.assertEqual(w({"now": NOW_MON}), {})
        self.assertEqual(calls, [])

    def test_current_session_old_bundle_still_rebuilds_on_age(self):
        from desk3.tensor_warm import TensorWarmer
        tmp = self._root()
        write_bundle(tmp, "2026-11-16", "2026-11-16T02:06:41+00:00")
        calls = []
        w = TensorWarmer(tmp, builder=recording_builder(
            calls, NOW_MON.isoformat()))
        self.assertEqual(w({"now": NOW_MON}), {})
        self.assertEqual(len(calls), 1)

    def test_sessionless_fresh_bundle_keeps_age_only_skip(self):
        from desk3.tensor_warm import TensorWarmer
        tmp = self._root()
        write_bundle(tmp, None, MON_STALE_GEN)
        calls = []
        w = TensorWarmer(tmp, builder=recording_builder(
            calls, NOW_MON.isoformat()))
        self.assertEqual(w({"now": NOW_MON}), {})
        self.assertEqual(calls, [])

    def test_failed_session_rebuild_is_named_and_backs_off(self):
        from desk3.tensor_warm import TensorWarmer
        from datetime import timedelta
        tmp = self._root()
        write_bundle(tmp, "2026-11-15", MON_STALE_GEN)
        calls = []

        def boom(root, session=None):
            calls.append(session)
            raise RuntimeError("canonical feed down")
        w = TensorWarmer(tmp, builder=boom)
        self.assertEqual(w({"now": NOW_MON}), {})
        self.assertEqual(len(calls), 1)
        self.assertIn("canonical feed down", w.last_error)
        self.assertEqual(w({"now": NOW_MON + timedelta(seconds=60)}), {})
        self.assertEqual(len(calls), 1)  # backoff: no retry storm

    def test_legacy_builder_without_session_kwarg_still_builds(self):
        from desk3.tensor_warm import TensorWarmer
        tmp = self._root()
        write_bundle(tmp, "2026-11-15", MON_STALE_GEN)
        calls = []

        def legacy(root):
            calls.append(root)
            write_bundle(root, "2026-11-16", NOW_MON.isoformat())
            return {}
        w = TensorWarmer(tmp, builder=legacy)
        self.assertEqual(w({"now": NOW_MON}), {})
        self.assertEqual(len(calls), 1)
        self.assertIsNone(w.last_error)

    def test_real_build_bundle_through_warmer_serves_same_cycle(self):
        from desk3.tensor_warm import TensorWarmer, build_bundle
        from desk3.producers import TensorBundleFile

        class FakeProducer:
            def extra_for(self, sleeve_id, ctx):
                if sleeve_id == "tensor_swing":
                    return {"tensor_signals": [FIRE], "tensor_exit": {}}
                return {"tensor_signals": [], "nyse_holidays": [],
                        "qqq_day_return": 0.0, "day_returns": {}}

        tmp = self._root()
        write_bundle(tmp, "2026-11-15", MON_STALE_GEN)
        w = TensorWarmer(tmp, builder=lambda root, session=None:
                         build_bundle(root, session=session,
                                      producer=FakeProducer()))
        self.assertEqual(w({"now": NOW_MON}), {})
        self.assertIsNone(w.last_error)
        doc = json.load(open(os.path.join(
            tmp, "cache", "tensor", "bundle.json")))
        self.assertEqual(doc["session"], "2026-11-16")
        served = TensorBundleFile(tmp, "tensor")({"now": NOW_MON})
        self.assertEqual(served["tensor"]["session"], "2026-11-16")

    def test_reader_fail_closed_rule_unchanged(self):
        from desk3.producers import TensorBundleFile
        tmp = self._root()
        write_bundle(tmp, "2026-11-15", NOW_MON.isoformat())
        prod = TensorBundleFile(tmp, "tensor")
        self.assertEqual(prod({"now": NOW_MON}), {})
        self.assertEqual(prod.last_error,
                         "stale_bundle_session:2026-11-15")


class TestPinsUntouched(unittest.TestCase):
    def test_saty_sol_and_engine_pins_match(self):
        self.assertEqual(
            hashlib.sha256(open(os.path.join(
                ROOT, "sleeves", "saty_sol.py"), "rb").read()).hexdigest(),
            "36e306c6294c385a5e9e96a89f8f4cd2753067597c95efb1fea416cc08962bdc")
        sys.path.insert(0, os.path.join(ROOT, "vendor"))
        import tensor_exact
        tensor_exact.verify_engine_hashes()  # raises on any drift


if __name__ == "__main__":
    unittest.main()
