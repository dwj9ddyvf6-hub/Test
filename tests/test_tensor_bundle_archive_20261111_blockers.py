"""TENSOR BUNDLE ARCHIVE blockers (D-RUN-1 / CURE-2, 2026-11-11).

Diagnosis (TENSOR-FIRE-PATH.md Section 1(b)): the warmer overwrote the
single cache/tensor/bundle.json in place and the signals memo
self-overwrote per build, so no per-session evidence of the fire path's
own runs survived: "one bundle per session, no missed, no duplicated"
was unprovable for 9 of the last 10 sessions. That unprovability is the
defect. Cure pinned here: every build leaves (a) a write-once archive
copy cache/tensor/archive/bundle-<session>.json, (b) a write-once memo
archive state/tensor_memo_archive/memo-<session>.json when the memo
belongs to the built session, and (c) one appended line in
state/tensor_bundle_history.jsonl {session, generated_at,
symbols_evaluated, fires}.
"""
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

SIGNAL = {"symbol": "OUST", "decision": "TRADE", "entry": 12.5}


class FakeProducer:
    """Writes a session memo the way TensorProducer does, so the
    archive behaviour is exercised end to end."""

    def extra_for(self, sleeve_id, ctx):
        memo = {"session": ctx.session,
                "rows": {"OUST": {"row": SIGNAL}, "MSFT": {"row": None}}}
        path = os.path.join(self._root, "state", "tensor_signals_memo.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            json.dump(memo, fh)
        if sleeve_id == "tensor_swing":
            return {"tensor_signals": [SIGNAL], "tensor_exit": {}}
        return {"tensor_signals": [SIGNAL], "qqq_day_return": 0.01,
                "day_returns": {"OUST": 0.01}, "nyse_holidays": []}


class TestTensorBundleArchive(unittest.TestCase):
    def _root(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        return tmp

    def _build(self, root, session):
        from desk3.tensor_warm import build_bundle
        fp = FakeProducer()
        fp._root = root
        return build_bundle(root, session=session, producer=fp)

    def test_two_builds_one_session_one_archive_two_history_lines(self):
        tmp = self._root()
        self._build(tmp, "2026-11-11")
        self._build(tmp, "2026-11-11")
        arch = os.path.join(tmp, "cache", "tensor", "archive",
                            "bundle-2026-11-11.json")
        self.assertTrue(os.path.exists(arch),
                        "no per-session bundle archive written")
        doc = json.load(open(arch))
        self.assertEqual(doc["session"], "2026-11-11")
        # CURE-3 envelope layer: the archived fires copy carries
        # price derived from the fire's own entry.
        self.assertEqual(doc["fires"], [dict(SIGNAL, price=12.5)])
        hist = open(os.path.join(
            tmp, "state", "tensor_bundle_history.jsonl")).readlines()
        self.assertEqual(len(hist), 2)
        row = json.loads(hist[0])
        self.assertEqual(row["session"], "2026-11-11")
        self.assertEqual(row["fires"], 1)
        self.assertEqual(row["symbols_evaluated"], 2)
        self.assertIn("generated_at", row)

    def test_second_session_adds_second_archive_and_memo_archived_once(self):
        tmp = self._root()
        self._build(tmp, "2026-11-11")
        self._build(tmp, "2026-11-12")
        arch_dir = os.path.join(tmp, "cache", "tensor", "archive")
        self.assertEqual(sorted(os.listdir(arch_dir)),
                         ["bundle-2026-11-11.json",
                          "bundle-2026-11-12.json"])
        memo_arch = os.path.join(tmp, "state", "tensor_memo_archive",
                                 "memo-2026-11-11.json")
        self.assertTrue(os.path.exists(memo_arch),
                        "session memo was not archived")
        self.assertEqual(json.load(open(memo_arch))["session"],
                         "2026-11-11")


if __name__ == "__main__":
    unittest.main()
