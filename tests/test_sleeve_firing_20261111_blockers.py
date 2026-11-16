"""SLEEVE-FIRING-20261111 blockers.

Root cause (census 2026-11-11, research_notes/sleeve-firing-2026-11-11):
seven sleeves sat UNFED on producer-registry declarations naming
keys no live producer emits, while the code paths they run read
produced keys under the desk's own names:

  momentum_rotation / phase_daily / raschke_pf3 declared "journal";
  the port_b5 bridge serves the journal from the sleeve's own state
  dir (desk3/port_b5/_ctx.py) and nothing reads view["journal"].
  raschke_rre declared "latest_quotes"; its ctx.latest_quotes()
  reads view["quotes"] (desk3/port4_context.SnapshotCtx).
  free_opt_parity declared "options.chain"; its adapter reads
  ctx.options_chain("SPY") -> view["options"].
  iron_condor / leaps_momentum declared "options:chains" (a v2
  warm-cache entry name); ctx.options_chain() reads view["options"].

Cure: declarations corrected in config/sleeves.json AND the module
INPUTS (the bta_onebar contract: both, always), and the dated
shrink-only LEGACY_UNPRODUCED_KEYS ledger in
test_bta_unfed_20261030_blockers.py shrinks by the four keys
(journal, latest_quotes, options.chain, options:chains). iron_condor
stays UNFED on "iv" alone (indicative feed carries no
impliedVolatility; OPRA not entitled) — "iv" stays on the ledger.

Second cure: QullaScanWarmer treated a proposals.json whose
evidence carries an engine error as the session's completed scan,
so a pre-market attempt that failed on zero intraday frames
(intraday_rows 0, "qulla frames incomplete", live artifact
2026-11-11) blocked every retry for the whole session while
QullaFileProducer fail-closed on the same error. The warmer now
treats an evidence-error doc as not completed and falls through
to the existing per-session attempt marker (one relaunch per
retry window), so the scan retries when intraday frames exist.
"""
from __future__ import annotations

import importlib
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
# The runner resolves bare adapter module names (e.g. raschke_rre)
# with the adapter dirs on sys.path; mirror that here.
for _d in ("desk_sleeves", "adapters3", "laz_sleeves"):
    _p = os.path.join(ROOT, _d)
    if _p not in sys.path:
        sys.path.insert(0, _p)

EXPECTED_INPUTS = {
    "momentum_rotation": ["bars", "positions"],
    "phase_daily": ["bars", "positions", "earnings"],
    "raschke_pf3": ["bars", "positions"],
    "raschke_rre": ["bars_5min", "positions", "session_fills",
                    "quotes", "macro_events"],
    "free_opt_parity": ["options", "bars"],
    "leaps_momentum": ["bars:*:1Day", "options", "positions",
                       "journal:momentum"],
    "iron_condor": ["bars:*:1Day", "bars:VIX:1Day", "options",
                    "earnings", "iv"],
}

SHRUNK_KEYS = ("journal", "latest_quotes", "options.chain",
               "options:chains")


def _config_rows():
    cfg = json.load(open(os.path.join(ROOT, "config", "sleeves.json")))
    return {r["id"]: r for r in cfg["sleeves"]}


class TestSleeveFiringDeclarations(unittest.TestCase):
    def test_config_inputs_cured(self):
        rows = _config_rows()
        for sid, want in EXPECTED_INPUTS.items():
            self.assertIn(sid, rows)
            self.assertEqual(want, rows[sid].get("inputs"), sid)

    def test_module_inputs_match_config(self):
        rows = _config_rows()
        for sid, want in EXPECTED_INPUTS.items():
            mod = importlib.import_module(rows[sid]["module"])
            self.assertEqual(want, list(mod.INPUTS), sid)

    def test_no_roster_sleeve_declares_shrunk_keys(self):
        for sid, row in _config_rows().items():
            for key in SHRUNK_KEYS:
                self.assertNotIn(key, row.get("inputs", []),
                                 f"{sid} still declares {key}")

    def test_legacy_ledger_shrunk(self):
        path = os.path.join(ROOT, "tests",
                            "test_bta_unfed_20261030_blockers.py")
        spec = importlib.util.spec_from_file_location("bta_ledger", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        for key in SHRUNK_KEYS:
            self.assertNotIn(key, mod.LEGACY_UNPRODUCED_KEYS, key)
        # "iv" SHRUNK 2026-11-14 (IV-PRODUCER-20261114, Lane C
        # 3ca0c78): desk3.producers.IVProducer now serves
        # iron_condor's iv product over the desk's AlpacaOptions
        # route, so the ledger entry is gone (shrink applied in
        # 3615f2b). The sentence this replaces ("iron_condor's
        # producer genuinely does not exist") is superseded.
        self.assertNotIn("iv", mod.LEGACY_UNPRODUCED_KEYS)


class TestQullaWarmerRetriesErrorDoc(unittest.TestCase):
    def _warmer(self, root, launches):
        from desk3.producers_g4 import QullaScanWarmer
        return QullaScanWarmer(
            root, launcher=lambda r: launches.append(r), retry_s=3600)

    def _setup_root(self, doc):
        tmp = tempfile.mkdtemp()
        qdir = os.path.join(tmp, "cache", "qulla")
        os.makedirs(qdir)
        with open(os.path.join(qdir, "proposals.json"), "w") as fh:
            json.dump(doc, fh)
        return tmp

    def _now(self):
        # QULLA-WARMER-CLOCK-20261116: the warmer is driven through
        # its production time source (the producer context's "now"),
        # pinned to a fixed trading-day afternoon: Monday
        # 2026-11-16, 15:00 ET. Wall-clock now made the relaunch
        # tests pass or fail by the hour they ran, because
        # QULLA-PREOPEN-DEFERRAL-20261113 suppresses launches
        # before 09:47 ET on a trading day. The deferral path stays
        # exercised against this same clock; the simulated
        # pre-09:47 behavior is pinned in
        # test_qulla_warmer_clock_20261116_blockers.py.
        from zoneinfo import ZoneInfo
        return datetime(2026, 11, 16, 15, 0,
                        tzinfo=ZoneInfo("America/New_York"))

    def _expected_session(self):
        from desk3.producers_g4 import _expected_qulla_session, ET
        return _expected_qulla_session(self._now().astimezone(ET).date())

    def test_error_doc_relaunches(self):
        doc = {"session": self._expected_session(), "proposals": [],
               "evidence": {"error": "RuntimeError: qulla frames "
                                     "incomplete",
                            "intraday_rows": 0}}
        root = self._setup_root(doc)
        launches = []
        self._warmer(root, launches)({"now": self._now()})
        self.assertEqual(1, len(launches),
                         "evidence-error doc must not count as the "
                         "session's completed scan")

    def test_clean_doc_does_not_relaunch(self):
        doc = {"session": self._expected_session(), "proposals": [],
               "evidence": {"intraday_rows": 1234}}
        root = self._setup_root(doc)
        launches = []
        self._warmer(root, launches)({"now": self._now()})
        self.assertEqual(0, len(launches))

    def test_error_doc_relaunch_is_bounded_by_marker(self):
        doc = {"session": self._expected_session(), "proposals": [],
               "evidence": {"error": "RuntimeError: qulla frames "
                                     "incomplete"}}
        root = self._setup_root(doc)
        launches = []
        warmer = self._warmer(root, launches)
        warmer({"now": self._now()})
        warmer({"now": self._now()})
        self.assertEqual(1, len(launches),
                         "attempt marker must bound relaunches to "
                         "one per retry window")


class TestQullaSnippetRthGate(unittest.TestCase):
    """The scan snippet gated its 1Min fetch on qulla_warm's
    _has_session, whose 1Min test is the bar's UTC date: the prior
    evening's after-hours bars (19:00-19:59 ET = 00:00-00:59Z) mark
    the session present, the real RTH fetch never runs, and the
    engine's intraday frame (ET RTH window only) stays empty —
    "qulla frames incomplete" on every attempt (live 2026-11-11).
    The snippet now gates 1Min on an ET-RTH presence test that
    mirrors the engine's own frame rule."""

    def _gate(self):
        import re
        from datetime import datetime as _dt, timezone as _tz
        from zoneinfo import ZoneInfo as _ZI
        from desk3.qulla_scan import _SNIPPET
        m = re.search(r"def _has_rth_1min\(.*?\n(?=\S)", _SNIPPET,
                      re.S)
        self.assertIsNotNone(m, "snippet carries no _has_rth_1min "
                                "gate (pre-cure shape)")
        ns = {"datetime": _dt, "timezone": _tz, "ZoneInfo": _ZI,
              "_epoch": lambda iso: _dt.fromisoformat(
                  str(iso).replace("Z", "+00:00")).timestamp(),
              "_ET": _ZI("America/New_York")}
        exec(m.group(0), ns)
        return ns["_has_rth_1min"]

    def _cache(self, stamps):
        class _Bar:
            def __init__(self, t):
                self.t = t

        class _Cache:
            def read_bars(self, sym, tf, n):
                assert tf == "1Min"
                return [_Bar(t) for t in stamps]
        return _Cache()

    def test_after_hours_bars_do_not_satisfy_gate(self):
        gate = self._gate()
        # 2026-11-11T00:30Z is 2026-11-10 19:30 ET (after-hours):
        # _has_session's UTC-date test calls this session present.
        cache = self._cache(["2026-11-11T00:30:00Z"])
        self.assertFalse(gate(cache, "NVDA", "2026-11-11"))

    def test_rth_bar_satisfies_gate(self):
        gate = self._gate()
        cache = self._cache(["2026-11-11T14:35:00Z"])  # 09:35 ET
        self.assertTrue(gate(cache, "NVDA", "2026-11-11"))

    def test_other_session_and_post_close_do_not_satisfy(self):
        gate = self._gate()
        self.assertFalse(gate(self._cache(["2026-11-10T14:35:00Z"]),
                              "NVDA", "2026-11-11"))
        # 21:05Z is 16:05 ET: after the 15:59 ET window close.
        self.assertFalse(gate(self._cache(["2026-11-11T21:05:00Z"]),
                              "NVDA", "2026-11-11"))

    def test_snippet_wiring(self):
        from desk3.qulla_scan import _SNIPPET
        self.assertIn("_has_rth_1min(cache, sym, session)", _SNIPPET)
        # The 1Day leg keeps the original presence test.
        self.assertIn("_has_session(cache, sym, tf, session)",
                      _SNIPPET)


if __name__ == "__main__":
    unittest.main()
