"""R2-RRE-20261025 blockers: raschke_rre's section-7 event gates
are data-driven from the desk macro-release calendar.

Semantics (proven from the code, recorded in the ruling):
core/raschke_rre/admission.py Gates carries
(event_coverage_known, events_clear) and _common rejects
EVENT_COVERAGE_UNKNOWN / EVENT_BLACKOUT;
core/raschke_rre/awareness.py ContextGates carries the same
pair and turns either False into DATA_BLOCK. The sleeve trades
SPY only, and BUGLOG_2026-10-24 (HARDEN-B4) established the
gates are macro typed, not earnings typed. Producer:
desk3/macro_calendar.py + committed desk3/macro_calendar.json
(FOMC / CPI / Employment Situation release dates, official
Federal Reserve + BLS schedules, coverage 2026-01-01 ..
2027-12-31).

Fail direction: on the pre-ruling tree desk3/macro_calendar.py
does not exist and sleeves/raschke_rre.py pins
_EVENT_GATES=(False, False), so every test here fails/errors.
"""
import importlib
import os
import sys
import unittest
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
ET = ZoneInfo("America/New_York")

mc = importlib.import_module("desk3.macro_calendar")
rre = importlib.import_module("sleeves.raschke_rre")


def _payload(session_iso):
    prod = mc.MacroCalendarProducer(ROOT)
    now = datetime.fromisoformat(session_iso + "T11:00:00").replace(
        tzinfo=ET)
    out = prod({"now": now, "root": ROOT})
    return out.get("macro_events")


def _rth5(day, base=600.0, drift=0.05):
    out, t, i = [], datetime(2026, 10, day, 9, 30, tzinfo=ET), 0
    while t < datetime(2026, 10, day, 16, 0, tzinfo=ET):
        c = base + drift * i
        out.append({"t": t.timestamp(), "o": c, "h": c + 0.3,
                    "l": c - 0.3, "c": c, "v": 10000})
        t += timedelta(minutes=5)
        i += 1
    return out


def _drive(prior_day, session_day, session_iso, extra):
    from core.sleeve import Context
    bars = {"SPY": _rth5(prior_day) + _rth5(session_day)}
    now = datetime.fromisoformat(session_iso + "T15:00:00").replace(
        tzinfo=ET).timestamp()
    ctx = Context(now=now, session=session_iso, equity=10000.0,
                  extra=extra)
    inst = rre.RaschkeRre()
    inst.signal(bars, {}, ctx)
    return inst.last_evaluation


class TestCalendarData(unittest.TestCase):
    def test_doc_loads_and_covers(self):
        doc = mc.load_calendar()
        self.assertIsNotNone(doc)
        self.assertEqual(doc["coverage_start"], "2026-01-01")
        self.assertEqual(doc["coverage_end"], "2027-12-31")
        self.assertEqual(len(doc["events"]), 64)
        kinds = {e["kind"] for e in doc["events"]}
        self.assertEqual(kinds, {"FOMC", "CPI", "NFP"})
        dates = [e["date"] for e in doc["events"]]
        self.assertEqual(len(dates), len(set(dates)))

    def test_known_release_dates(self):
        doc = mc.load_calendar()
        for iso, kind in (("2026-10-28", "FOMC"),
                          ("2026-11-10", "CPI"),
                          ("2026-11-06", "NFP"),
                          ("2027-06-09", "FOMC"),
                          ("2027-12-10", "CPI"),
                          ("2027-12-03", "NFP")):
            known, clear, ev = mc.event_gates_for(iso, doc)
            self.assertTrue(known, iso)
            self.assertFalse(clear, iso)
            self.assertEqual(ev["kind"], kind, iso)


class TestGateFunction(unittest.TestCase):
    def setUp(self):
        self.doc = mc.load_calendar()

    def test_event_day_blocks(self):
        self.assertEqual(mc.event_gates_for("2026-10-28", self.doc)[:2],
                         (True, False))

    def test_clear_day_passes(self):
        self.assertEqual(mc.event_gates_for("2026-10-26", self.doc)[:2],
                         (True, True))

    def test_outside_coverage_fails_closed(self):
        self.assertEqual(mc.event_gates_for("2028-01-10", self.doc)[:2],
                         (False, False))
        self.assertEqual(mc.event_gates_for("2025-12-31", self.doc)[:2],
                         (False, False))

    def test_malformed_doc_fails_closed(self):
        self.assertEqual(mc.event_gates_for("2026-10-26", None)[:2],
                         (False, False))
        bad = {"version": "desk-macro-calendar-v1", "events": "x",
               "coverage_start": "2026-01-01",
               "coverage_end": "2027-12-31"}
        self.assertEqual(mc.event_gates_for("2026-10-26", bad)[:2],
                         (False, False))


class TestProducer(unittest.TestCase):
    def test_serves_event_day(self):
        p = _payload("2026-10-28")
        self.assertIsNotNone(p)
        self.assertTrue(p["coverage_known"])
        self.assertFalse(p["events_clear"])
        self.assertEqual(p["event"]["kind"], "FOMC")
        self.assertEqual(len(p["events"]), 64)

    def test_serves_clear_day(self):
        p = _payload("2026-10-26")
        self.assertTrue(p["coverage_known"])
        self.assertTrue(p["events_clear"])
        self.assertIsNone(p["event"])

    def test_missing_file_fails_closed(self):
        prod = mc.MacroCalendarProducer(
            ROOT, path=os.path.join(ROOT, "desk3", "no_such.json"))
        now = datetime(2026, 10, 26, 15, 0, tzinfo=timezone.utc)
        self.assertEqual(prod({"now": now, "root": ROOT}), {})

    def test_registered_in_batch3(self):
        from desk3.producers3 import BATCH3_PRODUCERS
        row = [r for r in BATCH3_PRODUCERS if r[0] == "macro_calendar"]
        self.assertEqual(len(row), 1)
        self.assertEqual(row[0][2], ("macro_events",))


class TestSleeveResolver(unittest.TestCase):
    def test_both_directions_from_payload(self):
        extra = {"macro_events": _payload("2026-10-26")}
        self.assertEqual(
            rre._event_gates(extra, "2026-10-28")[:2], (True, False))
        self.assertEqual(
            rre._event_gates(extra, "2026-10-26")[:2], (True, True))
        self.assertEqual(
            rre._event_gates(extra, "2028-03-01")[:2], (False, False))

    def test_absent_payload_is_pre_ruling_posture(self):
        self.assertEqual(rre._event_gates({}, "2026-10-26")[:2],
                         (False, False))
        self.assertEqual(
            rre._event_gates({"macro_events": {"source": "bogus"}},
                             "2026-10-26")[:2], (False, False))

    def test_no_pinned_constant_remains(self):
        self.assertFalse(hasattr(rre, "_EVENT_GATES"))


class TestSleeveSignalGates(unittest.TestCase):
    def test_clear_day_not_data_blocked_by_events(self):
        stamp = _drive(23, 26, "2026-10-26",
                       {"macro_events": _payload("2026-10-26")})
        self.assertEqual(stamp["event_state"], "macro_clear")
        self.assertTrue(stamp["event_coverage_known"])
        self.assertNotEqual(stamp["context_state"], "DATA_BLOCK")

    def test_event_day_data_blocks(self):
        stamp = _drive(27, 28, "2026-10-28",
                       {"macro_events": _payload("2026-10-28")})
        self.assertEqual(stamp["event_state"], "macro_event_blackout")
        self.assertEqual(stamp["event"]["kind"], "FOMC")
        self.assertEqual(stamp["context_state"], "DATA_BLOCK")

    def test_absent_payload_still_blocks(self):
        stamp = _drive(23, 26, "2026-10-26", {})
        self.assertEqual(stamp["event_state"],
                         "event_absent_strict_block")
        self.assertFalse(stamp["event_coverage_known"])
        self.assertEqual(stamp["context_state"], "DATA_BLOCK")


class TestAdmissionGates(unittest.TestCase):
    def _intent_and_ctx(self, session_iso, extra):
        from core.raschke_rre.raschke_engine import Intent as RIntent
        from core.sleeve import Context
        d = datetime.fromisoformat(session_iso)
        open_dt = datetime(d.year, d.month, d.day, 9, 30, tzinfo=ET)
        now = open_dt + timedelta(minutes=30)
        intent = RIntent(
            source_id="fix-rre2-1", variant="RRE2", setup="FIRST_CROSS",
            symbol="SPY", direction=1,
            signal_at=open_dt + timedelta(minutes=29),
            available_at=open_dt + timedelta(minutes=29, seconds=30),
            expires_at=open_dt + timedelta(minutes=34),
            entry_reference=600.05, trigger=600.05, stop=599.0,
            target=602.0, atr14=1.0, session_id=session_iso,
            generation=1, episode_id="fix-ep-1",
            session_close=open_dt + timedelta(hours=6, minutes=30),
            series_id=rre.SERIES_ID,
            calendar_version=rre.CALENDAR_VERSION,
            reference_id="fix-ref-1", max_hold_seconds=1800)
        q = {"t": now.isoformat(), "bp": 600.00, "ap": 600.05,
             "bs": 100, "as": 100, "feed": "iex"}
        ex = {"latest_quote": {"SPY": q}}
        ex.update(extra)
        ctx = Context(now=now.timestamp(), session=session_iso,
                      equity=10000.0, extra=ex)
        return intent, ctx, now

    def _admit(self, session_iso, extra):
        from core.raschke_rre.router import RankedIntent
        intent, ctx, _now = self._intent_and_ctx(session_iso, extra)
        item = RankedIntent(intent, (1.0,), "fix-ctx", "TRANSITION", ())
        inst = rre.RaschkeRre()
        return inst._admit({}, intent, item, ctx, {})

    def test_clear_day_admission_not_event_rejected(self):
        out = self._admit("2026-10-26",
                          {"macro_events": _payload("2026-10-26")})
        self.assertIsNotNone(out)
        rec, desk_intent = out
        self.assertNotIn(rec.reason, ("EVENT_BLACKOUT",
                                      "EVENT_COVERAGE_UNKNOWN"))
        self.assertTrue(rec.allowed, rec.reason)
        self.assertIsNotNone(desk_intent)

    def test_event_day_admission_blackout(self):
        out = self._admit("2026-10-28",
                          {"macro_events": _payload("2026-10-28")})
        rec, desk_intent = out
        self.assertFalse(rec.allowed)
        self.assertEqual(rec.reason, "EVENT_BLACKOUT")
        self.assertIsNone(desk_intent)

    def test_absent_payload_admission_unknown(self):
        out = self._admit("2026-10-26", {})
        rec, desk_intent = out
        self.assertFalse(rec.allowed)
        self.assertEqual(rec.reason, "EVENT_COVERAGE_UNKNOWN")
        self.assertIsNone(desk_intent)


class TestWiring(unittest.TestCase):
    def test_inputs_declared_everywhere(self):
        import json
        cfg = {s["id"]: s for s in json.load(
            open(os.path.join(ROOT, "config", "sleeves.json")))["sleeves"]}
        self.assertIn("macro_events", cfg["raschke_rre"]["inputs"])
        from desk3 import port_batch6
        rows = dict(port_batch6.config_rows() and
                    [(r["id"], r) for r in port_batch6.config_rows()])
        self.assertIn("macro_events", rows["raschke_rre"]["inputs"])
        ad = importlib.import_module("desk_sleeves.raschke_rre")
        self.assertIn("macro_events", ad.INPUTS)


if __name__ == "__main__":
    unittest.main()
