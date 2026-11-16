"""TENSOR STALE-SESSION blockers (D-RUN-2 / CURE-1, 2026-11-11).

Diagnosis (TENSOR-FIRE-PATH.md Section 1(b)): TensorBundleFile._read_bundle
gated serving only on generated_at age against a 26 h bound and never
checked that bundle.session equals the cycle's session. A bundle built
late in session N stayed servable well into session N+1, indistinguishable
from fresh: a failed or skipped morning rebuild was silent by construction.

Cure semantics pinned here: a bundle whose session is present and strictly
older than the cycle's ET session is refused ({} served) with last_error
"stale_bundle_session:<session>". A bundle of the current session serves;
a bundle with no session field keeps the legacy age-only behaviour (the
pre-warmer file shape cannot prove staleness either way).
"""
import json
import os
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

NOW = datetime(2026, 11, 11, 20, 0, tzinfo=timezone.utc)  # 15:00 ET
TODAY = "2026-11-11"
YESTERDAY = "2026-11-10"
FIRE = {"symbol": "ARM", "decision": "TRADE", "entry": 100.0}


def write_bundle(root, doc):
    d = os.path.join(root, "cache", "tensor")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "bundle.json"), "w") as fh:
        json.dump(doc, fh)


def bundle_doc(session_marker, generated_at):
    doc = {"generated_at": generated_at, "sleeves": {}, "fires": [FIRE]}
    if session_marker is not None:
        doc["session"] = session_marker
    return doc


class TestTensorStaleSession(unittest.TestCase):
    def _root(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        return tmp

    def test_yesterdays_bundle_with_fresh_stamp_is_refused_and_named(self):
        from desk3.producers import TensorBundleFile
        tmp = self._root()
        write_bundle(tmp, bundle_doc(YESTERDAY, NOW.isoformat()))
        for key in ("tensor", "tensor_fires"):
            prod = TensorBundleFile(tmp, key)
            self.assertEqual(prod({"now": NOW}), {},
                             f"{key} served a stale-session bundle")
            self.assertEqual(prod.last_error,
                             f"stale_bundle_session:{YESTERDAY}")

    def test_current_session_bundle_serves(self):
        from desk3.producers import TensorBundleFile
        tmp = self._root()
        write_bundle(tmp, bundle_doc(TODAY, NOW.isoformat()))
        self.assertEqual(TensorBundleFile(tmp, "tensor_fires")({"now": NOW}),
                         {"tensor_fires": [FIRE]})
        served = TensorBundleFile(tmp, "tensor")({"now": NOW})
        self.assertEqual(served["tensor"]["session"], TODAY)

    def test_sessionless_bundle_keeps_age_only_behaviour(self):
        from desk3.producers import TensorBundleFile
        tmp = self._root()
        write_bundle(tmp, bundle_doc(None, NOW.isoformat()))
        self.assertEqual(TensorBundleFile(tmp, "tensor_fires")({"now": NOW}),
                         {"tensor_fires": [FIRE]})


if __name__ == "__main__":
    unittest.main()
