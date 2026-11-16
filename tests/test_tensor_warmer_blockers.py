"""R4 TENSOR WARMER blockers (MIDNA RULING 2026-10-25; audit OPEN #6).

Pre-cure state: muse-desk-v3 had NO vendor/ tree (core.data's Tensor
door pointed at a nonexistent vendor/canonical_bars.py), NO
core/tensor_feeds.py, and NO warmer — cache/tensor/bundle.json was
never written, so every tensor dependent sat UNFED with
producer_errors naming tensor_bundle / tensor_fires /
tensor_daily20_bundle "no_bundle_file". Every test below fails on
that tree (ImportError / missing files).

Cure proven here:
  * the vendored engine + canonical feed + producer are byte-identical
    ports of muse-desk-v2 @3593668 (sha256 pins below) and the
    wrapper's own verify_engine_hashes() passes (engine hard rail);
  * desk3.tensor_warm.build_bundle writes a well-formed bundle from
    fixture inputs (session/generated_at/sleeves/fires schema);
  * the bundle-file consumers read it: TensorBundleFile serves
    "tensor" and "tensor_fires", the base tensor_swing adapter
    extracts its sleeves slice, aster_batch14._fires reads the fires;
  * TensorWarmer gating: fresh bundle -> no rebuild; missing bundle
    -> build; failed build -> last_error named + backoff;
    (amended 2026-11-16, TENSOR-STALE-SESSION-WARMER-20261116: the
    gating fixture below now builds the cycle's own session
    (2026-10-26, NOW's ET date) instead of 2026-10-23 — under the
    session-roll rebuild trigger a 2026-10-23 bundle at a
    2026-10-26 cycle is session-stale, not fresh, so the old
    fixture no longer expressed "fresh -> skipped"; the assertion
    stands at full strength for a bundle that is fresh AND
    current-session. Session-stale gating itself is pinned by
    tests/test_tensor_stale_session_warmer_20261116_blockers.py.)
  * register_all registers "tensor_warmer" before the readers;
  * a fixture build leaves every engine file hash-identical
    (before == after — the rail held);
  * "tensor_daily20" is ABSENT from the bundle by design: its rows
    are the Aster daily feature pipeline's product, not a v698
    producer output — pinned here so the key is never fabricated.
"""
import hashlib, importlib, json, os, shutil, sys, tempfile, unittest
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

NOW = datetime(2026, 10, 26, 13, 37, tzinfo=timezone.utc)  # Mon 09:37 ET

# sha256 of the muse-desk-v2 @3593668 originals (the port source).
V2_PINS = {
    "vendor/tensor_exact.py":
        "c8a66f5e43d35af6fcb836187ae624f07c56adc9ac6b846b99e745046bf04abd",
    "vendor/canonical_bars.py":
        "0f774e8a79781b73408fc4d735f2f1d7740f149e7d117937c08bc9c77ad6b228",
    "core/tensor_feeds.py":
        "e4241113957517698fbcd88326bef953800680bbcdd616ec355d7716e50a72f5",
}

SIGNAL = {"symbol": "OUST", "decision": "TRADE", "confidence": 7,
          "phenotype": "RECLAIM", "regime": "bearish",
          "bar_date": "2026-10-23", "t": 1792785600, "bull_votes": 7,
          "bear_votes": 0, "entry": 29.69, "stop": 29.69,
          "target": 30.28, "extended": False}


def _sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def _engine_hashes():
    out = {}
    vdir = os.path.join(ROOT, "vendor")
    for base, _dirs, files in os.walk(vdir):
        for f in files:
            p = os.path.join(base, f)
            out[os.path.relpath(p, ROOT)] = _sha(p)
    out["core/tensor_feeds.py"] = _sha(
        os.path.join(ROOT, "core", "tensor_feeds.py"))
    return out


class FakeProducer:
    """TensorProducer-shaped fixture: extra_for per sleeve."""

    def __init__(self):
        self.calls = []

    def extra_for(self, sleeve_id, ctx):
        self.calls.append((sleeve_id, ctx.session))
        if sleeve_id == "tensor_swing":
            return {"tensor_signals": [SIGNAL],
                    "tensor_exit": {"OUST": {"bearish_exit": False}}}
        return {"tensor_signals": [SIGNAL],
                "nyse_holidays": ["2026-01-01"],
                "qqq_day_return": -0.0001,
                "day_returns": {"OUST": 0.01}}


class TestEnginePortIntegrity(unittest.TestCase):
    def test_vendored_files_match_v2_pins(self):
        for rel, pin in V2_PINS.items():
            self.assertEqual(_sha(os.path.join(ROOT, rel)), pin, rel)

    def test_engine_self_verification_and_pin(self):
        sys.path.insert(0, os.path.join(ROOT, "vendor"))
        import tensor_exact
        tensor_exact.verify_engine_hashes()  # raises on any drift
        self.assertEqual(tensor_exact.ENGINE_VERSION_PINNED, "v698")

    def test_tensor_door_resolves_vendored_feed(self):
        import core.data as data
        import pathlib
        v = pathlib.Path(ROOT) / "vendor" / "canonical_bars.py"
        self.assertTrue(v.exists())
        self.assertTrue(callable(data.tensor_bars))


class TestWarmerBuild(unittest.TestCase):
    def _root(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        return tmp

    def test_build_bundle_writes_wellformed_bundle(self):
        from desk3.tensor_warm import build_bundle
        tmp = self._root()
        fp = FakeProducer()
        payload = build_bundle(tmp, session="2026-10-23", producer=fp)
        path = os.path.join(tmp, "cache", "tensor", "bundle.json")
        self.assertTrue(os.path.exists(path))
        doc = json.load(open(path))
        self.assertEqual(doc, payload)
        self.assertEqual(doc["session"], "2026-10-23")
        self.assertIn("generated_at", doc)
        self.assertEqual(
            doc["sleeves"]["tensor_swing"]["tensor_signals"], [SIGNAL])
        self.assertEqual(
            doc["sleeves"]["tensor_red_dip"]["day_returns"],
            {"OUST": 0.01})
        # CURE-3 envelope layer (2026-11-11): the fires copies carry
        # the fire's own values under the consumers' key names
        # (price/date/signal_end/ts/fired_at); the sleeves channel
        # above keeps the engine row verbatim.
        self.assertEqual(doc["fires"], [dict(
            SIGNAL, price=SIGNAL["entry"], date=SIGNAL["bar_date"],
            signal_end=SIGNAL["bar_date"], ts=SIGNAL["t"],
            fired_at=datetime.fromtimestamp(
                SIGNAL["t"], timezone.utc).isoformat())])
        # daily20 absent by design (Aster daily pipeline product,
        # not a v698 producer output — never fabricated)
        self.assertNotIn("tensor_daily20", doc)
        self.assertEqual({c[0] for c in fp.calls},
                         {"tensor_swing", "tensor_red_dip"})

    def test_consumers_read_the_built_bundle(self):
        from desk3.tensor_warm import build_bundle
        from desk3.producers import TensorBundleFile
        from zoneinfo import ZoneInfo
        tmp = self._root()
        # D-RUN-2 / CURE-1 (2026-11-11): the readers now refuse a bundle
        # whose session is older than the cycle's ET session, so the
        # fixture bundle is built for the CURRENT session; every
        # assertion below stands at full strength.
        build_bundle(tmp,
                     session=datetime.now(
                         ZoneInfo("America/New_York")).date().isoformat(),
                     producer=FakeProducer())
        # generated_at is "now" at build time; serve it at real now
        now = datetime.now(timezone.utc)
        served = TensorBundleFile(tmp, "tensor")({"now": now})
        self.assertIn("tensor", served)
        self.assertEqual(
            served["tensor"]["sleeves"]["tensor_swing"]
            ["tensor_signals"], [SIGNAL])
        self.assertEqual(
            TensorBundleFile(tmp, "tensor_fires")({"now": now}),
            {"tensor_fires": [dict(
                SIGNAL, price=SIGNAL["entry"], date=SIGNAL["bar_date"],
                signal_end=SIGNAL["bar_date"], ts=SIGNAL["t"],
                fired_at=datetime.fromtimestamp(
                    SIGNAL["t"], timezone.utc).isoformat())]})
        # daily20 reader stays fail-closed on the honest absence,
        # and NAMES it truthfully (bundle exists, key absent — never
        # the stale "no_bundle_file" from before the warmer existed)
        d20 = TensorBundleFile(tmp, "tensor_daily20")
        self.assertEqual(d20({"now": now}), {})
        self.assertEqual(d20.last_error,
                         "bundle_missing_key:tensor_daily20")
        # a served key clears any prior error state
        rd = TensorBundleFile(tmp, "tensor_fires")
        rd.last_error = "no_bundle_file"
        self.assertEqual(rd({"now": now}), {"tensor_fires": [dict(
            SIGNAL, price=SIGNAL["entry"], date=SIGNAL["bar_date"],
            signal_end=SIGNAL["bar_date"], ts=SIGNAL["t"],
            fired_at=datetime.fromtimestamp(
                SIGNAL["t"], timezone.utc).isoformat())]})
        self.assertIsNone(rd.last_error)
        # base sleeve adapter extracts its slice from the bundle
        import adapters.tensor_swing as ad

        class Ctx:
            params = {}
            def tensor_bundle(self):
                return served["tensor"]
        extra = ad._bundle_extra(Ctx())
        self.assertEqual(extra["tensor_signals"], [SIGNAL])
        self.assertIn("tensor_exit", extra)
        # Aster G4 (batch14) fires channel reads the same bundle
        from desk3 import aster_batch14
        self.assertEqual(aster_batch14._fires(served), [dict(
            SIGNAL, price=SIGNAL["entry"], date=SIGNAL["bar_date"],
            signal_end=SIGNAL["bar_date"], ts=SIGNAL["t"],
            fired_at=datetime.fromtimestamp(
                SIGNAL["t"], timezone.utc).isoformat())])
        # stale bundle: readers fail closed (Sunday-stale honesty is
        # the file's generated_at, never a relabel)
        stale = now + timedelta(days=3)
        self.assertEqual(TensorBundleFile(tmp, "tensor")({"now": stale}),
                         {})

    def test_engine_files_hash_identical_after_build(self):
        from desk3.tensor_warm import build_bundle
        before = _engine_hashes()
        tmp = self._root()
        build_bundle(tmp, session="2026-10-23", producer=FakeProducer())
        self.assertEqual(_engine_hashes(), before)


class TestWarmerGating(unittest.TestCase):
    def _root(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        return tmp

    def test_missing_builds_fresh_skips_failed_names_and_backs_off(self):
        from desk3.tensor_warm import TensorWarmer, build_bundle
        tmp = self._root()
        calls = []

        def builder(root):
            calls.append(root)
            # 2026-11-16 amendment (see header): the fixture bundle
            # carries the cycle's own session, so "fresh" below is
            # fresh under both the age and the session rule.
            return build_bundle(root, session="2026-10-26",
                                producer=FakeProducer())
        w = TensorWarmer(tmp, builder=builder)
        self.assertEqual(w({"now": NOW}), {})
        self.assertEqual(len(calls), 1)          # missing -> built
        self.assertIsNone(w.last_error)
        self.assertEqual(w({"now": NOW}), {})
        self.assertEqual(len(calls), 1)          # fresh -> skipped

        def boom(root):
            calls.append(root)
            raise RuntimeError("canonical feed down")
        w2 = TensorWarmer(self._root(), builder=boom)
        self.assertEqual(w2({"now": NOW}), {})
        self.assertIn("canonical feed down", w2.last_error)
        n = len(calls)
        self.assertEqual(w2({"now": NOW + timedelta(seconds=60)}), {})
        self.assertEqual(len(calls), n)          # backoff: no retry


class TestRegistryWiring(unittest.TestCase):
    def test_register_all_names_tensor_warmer_before_readers(self):
        from desk3.cycle import Desk
        from desk3.broker import FakeBroker
        from desk3.producers import register_all
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        desk = Desk(tmp, broker=FakeBroker(), sleeve_path=tmp)
        register_all(desk, tmp, env={})
        self.assertIn("tensor_warmer", desk.registry.producers)
        names = list(desk.producers)
        self.assertLess(names.index("tensor_warmer"),
                        names.index("tensor_bundle"))
        self.assertLess(names.index("tensor_warmer"),
                        names.index("tensor_fires"))
        desk.close()


if __name__ == "__main__":
    unittest.main()
