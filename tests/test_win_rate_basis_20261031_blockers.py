"""Blockers: WIN-RATE-BASIS-20261031. The quants-mechanisms audit
(item 5) found the desk's published surfaces largely compliant by
the "or are not shown" clause (no win rate / profit factor on the
terminal feed, terminal page, or ensemble report), with two gaps:
sleeves/po10_qqq.py republished a source figure (392 trades, 59%
win rate, PF 1.86) with no accounting basis stated, and no
gate-wired blocker enforced basis-stated-or-not-shown.

Cure (DISPLAY only): the basis statement lands on
desk3/port_b5/po10_qqq.py, the module config/sleeves.json
actually loads for this sleeve, because sleeves/po10_qqq.py is
byte-pinned to the v2 port by test_port_b5_blockers (the first
cut edited that header and the port-fidelity blocker failed on
exactly it, so the edit was reverted completely and moved here,
the weight-lag pass's landing correction). The wrapper states
that the figure's accounting basis is NOT stated by the source
(not FIFO-lot-verified, not equity-based-verified) and carries
it as a structured REPUBLISHED_SOURCE_FIGURE constant; this
blocker also scans the published surfaces so any future
win-rate / profit-factor appearance without a stated basis
fails the gate.

Fail direction: on the pre-cure tree the wrapper carries no
basis statement, so test_po10_basis_stated_on_loaded_entrypoint
fails."""
import json, os, re, sys, unittest
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

WRPF = re.compile(r"win[_ ]?rate|profit[_ ]?factor", re.I)
BASIS = re.compile(
    r"fifo|equity[_ -]based|accounting[_ ]basis", re.I)


def _read(rel):
    with open(os.path.join(ROOT, rel)) as fh:
        return fh.read()


def _flatten(obj, path=""):
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.append((f"{path}.{k}", str(k)))
            out.extend(_flatten(v, f"{path}.{k}"))
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            out.extend(_flatten(v, f"{path}[{i}]"))
    elif isinstance(obj, str):
        out.append((path, obj))
    return out


def _unlabelled_wrpf(obj):
    """Paths in a published structure carrying WR/PF with no basis
    stated anywhere in the same structure."""
    flat = _flatten(obj)
    hits = [p for p, s in flat if WRPF.search(s)]
    if not hits:
        return []
    if any(BASIS.search(s) for _p, s in flat):
        return []
    return hits


class TestPo10RepublishedFigure(unittest.TestCase):
    def test_po10_basis_stated_on_loaded_entrypoint(self):
        # The republished figure is still present in the pinned
        # strategy header (labelled, not silently dropped) ...
        src = _read("sleeves/po10_qqq.py")
        header = src.split('"""', 2)[1]
        self.assertIn("59% win rate", header)
        self.assertIn("PF 1.86", header)
        # ... and its accounting basis status is stated on the
        # module the roster loads (desk3.port_b5.po10_qqq, per
        # config/sleeves.json): not stated by the source, and
        # explicitly neither FIFO-lot-verified nor
        # equity-based-verified, in prose and as a constant.
        wrap = _read("desk3/port_b5/po10_qqq.py")
        low = wrap.lower()
        self.assertIn("accounting basis", low)
        self.assertIn("not stated", low)
        self.assertIn("fifo", low)
        self.assertIn("equity", low)
        from desk3.port_b5.po10_qqq import REPUBLISHED_SOURCE_FIGURE
        self.assertEqual(REPUBLISHED_SOURCE_FIGURE["trades"], 392)
        self.assertEqual(REPUBLISHED_SOURCE_FIGURE["win_rate"], 0.59)
        self.assertEqual(
            REPUBLISHED_SOURCE_FIGURE["profit_factor"], 1.86)
        self.assertEqual(REPUBLISHED_SOURCE_FIGURE["accounting_basis"],
                         "not_stated_by_source")
        self.assertFalse(REPUBLISHED_SOURCE_FIGURE["fifo_lot_verified"])
        self.assertFalse(
            REPUBLISHED_SOURCE_FIGURE["equity_based_verified"])

    def test_po10_pinned_sleeve_unchanged(self):
        # Preservation: the byte-pinned strategy file keeps its
        # figure and its code; the cure added nothing to it.
        src = _read("sleeves/po10_qqq.py")
        self.assertIn('sleeve_id="po10_qqq"', src)
        self.assertIn("def signal(bars, slice_state, context):", src)
        self.assertNotIn("WIN-RATE-BASIS-20261031", src)


class TestPublishedSurfacesBasisOrAbsent(unittest.TestCase):
    def test_terminal_feed_has_no_unlabelled_wrpf(self):
        from desk3.terminal import build_feed
        roll = {"generated_at": "2026-10-31T12:00:00+00:00",
                "cycle_id": "cycle-3-1", "status": "ok",
                "snapshot_hash": "abc123", "producer_errors": {},
                "sleeves": {"fed1": {"state": "FED", "status": "ok",
                                     "orders_placed": 2}}}
        feed = build_feed(roll, {"fed1": {"slice_usd": 100.0}},
                          positions=[],
                          account={"cash": 1.0, "equity": 2.0})
        self.assertEqual(_unlabelled_wrpf(feed), [])

    def test_published_surface_sources_basis_or_absent(self):
        for rel in ("desk3/terminal.py",
                    "desk3/forecast/sleeve_ensemble.py"):
            src = _read(rel)
            if WRPF.search(src):
                self.assertTrue(
                    BASIS.search(src),
                    f"{rel} shows WR/PF without a stated basis")

    def test_internal_fifo_helpers_stay_internal_and_named(self):
        # The FIFO accounting that exists is named in code and
        # feeds no WR/PF surface (preservation).
        for rel in ("sleeves/saty_gpt_v02.py",
                    "sleeves/saty_gpt_v03.py"):
            src = _read(rel)
            self.assertIn("FIFO reconstruction from session fills",
                          src)
            self.assertIsNone(WRPF.search(src), rel)


if __name__ == "__main__":
    unittest.main()
