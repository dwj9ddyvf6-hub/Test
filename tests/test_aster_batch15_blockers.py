"""Aster batch 15 blockers (ASTER-B15): G4 Tensor green value/recovery
(hot delay / hot QQQ-reserve / red-timeout) + timing (EMA cloud x2,
confirmed hourly swing x4, overnight 25bp).

Oracle = staged archive r19_tensor.py / r19_timing.py + RULES.json
books (see FIDELITY-LEDGER ASTER-B15). Fail-first: adapters absent
pre-build => import errors.
AMENDED 2026-11-12 (GATE-CURE-20261112, STRICTNESS-CENSUS proposals
1-2): the G4 buy-green marker requirement is removed by the owner's
too-strict ruling; the cyan-marker pin below now asserts the cured
behavior (a cyan-marked fire with passing numerics enters). The
pre-cure pin is preserved in ~/workspace/.gatecure-20261112/pre/tests/.
"""
import importlib
import json
import os
import sys
import tempfile
import unittest
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
ET = ZoneInfo("America/New_York")
P = "aster_r19_"
G4_DELAY = P + "tensor_g4_hot_delay_25"
G4_RES = P + "tensor_g4_hot_reserve_25"
G4_RED = P + "tensor_g4_red_timeout_25"
CLOUD_A = P + "timing_cloud_aggressive"
CLOUD_B = P + "timing_cloud_base"
H00 = P + "timing_hour_floor0_delay0"
H01 = P + "timing_hour_floor0_delay1"
H10 = P + "timing_hour_floor1_delay0"
H11 = P + "timing_hour_floor1_delay1"
ON25 = P + "timing_overnight_25bp"
IDS = [G4_DELAY, G4_RES, G4_RED, CLOUD_A, CLOUD_B,
       H00, H01, H10, H11, ON25]


def weekdays(start, n):
    out, d = [], start
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


SESSIONS = weekdays(date(2025, 1, 6), 640)  # Mon 2025-01-06, ~128 wks
SESSION_STRS = [d.isoformat() for d in SESSIONS]


def at(d, hh=9, mm=30):
    return datetime.combine(d, time(hh, mm), ET).astimezone(timezone.utc)


def drive(sid, view, state_dir=None):
    mod = importlib.import_module(f"adapters3.{sid}")
    view.setdefault("extra", {})["session_dates"] = SESSION_STRS
    return mod.evaluate(view, {"sleeve_id": sid, "cycle_id": "fx",
                               "state_dir": state_dir or tempfile.mkdtemp()})


def fire(sym="AAA", end=None, **kw):
    f = {"symbol": sym, "issuer_id": "iss-" + sym, "signal_end": end,
         "markers": ["buy-green"], "native_close": 5.0, "depth60": 80.0,
         "ret60": 5.0, "vol20": 0.12, "dv20": 5e6, "atr_ratio": 1.5}
    f.update(kw)
    return f


def g4_view(now, fires, positions=None, cash=10000.0, bars=None):
    return {"now": now.isoformat(), "tensor_fires": fires,
            "positions": positions or [],
            "bars": bars or {"AAA|1Day": [{"t": "2025-01-03", "o": 5.0,
                                           "h": 5.1, "l": 4.9, "c": 5.0,
                                           "v": 1e6}]},
            "slice": {"capital_usd": 10000.0, "cash_usd": cash},
            "quotes": {}, "extra": {}}


# signal week: signal_end = Friday 2025-02-14 (a session); following
# sessions Mon 02-17, Tue 02-18 ...
SIG_END = "2025-02-14"
FOLLOW = [d for d in SESSION_STRS if d > SIG_END]


class TestG4Entries(unittest.TestCase):
    def test_delay_entry_on_second_session(self):
        sd = tempfile.mkdtemp()
        v = g4_view(at(SESSIONS[25]), [fire(end=SIG_END)])
        self.assertEqual(drive(G4_DELAY, v, sd), [])  # pending only
        entry_day = date.fromisoformat(FOLLOW[1])
        out = drive(G4_DELAY, g4_view(at(entry_day),
                                      [fire(end=SIG_END)]), sd)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["kind"], "entry")
        self.assertEqual(out[0]["qty"], 79)  # floor(400/(5*1.003))

    def test_delay_no_entry_on_first_session(self):
        sd = tempfile.mkdtemp()
        drive(G4_DELAY, g4_view(at(SESSIONS[25]), [fire(end=SIG_END)]), sd)
        out = drive(G4_DELAY, g4_view(at(date.fromisoformat(FOLLOW[0])),
                                      [fire(end=SIG_END)]), sd)
        self.assertEqual(out, [])

    def test_red_timeout_enters_after_red_day(self):
        sd = tempfile.mkdtemp()
        w = FOLLOW[:5]  # Mon..Fri wait sessions
        qbars, abars = [], []
        qclose = {SIG_END: 101.0, w[0]: 102.0, w[1]: 99.0, w[2]: 99.5,
                  w[3]: 100.0, w[4]: 100.5}
        for d in sorted(qclose):
            qbars.append({"t": d, "o": qclose[d], "h": qclose[d],
                          "l": qclose[d], "c": qclose[d], "v": 1e6})
            abars.append({"t": d, "o": 5.0, "h": 5.0, "l": 5.0, "c": 5.0,
                          "v": 1e6})
        bars = {"QQQ|1Day": qbars, "AAA|1Day": abars}
        drive(G4_RED, g4_view(at(SESSIONS[25]), [fire(end=SIG_END)],
                              bars=bars), sd)
        # red on w[1] (QQQ down, AAA at signal close) -> entry w[2]
        out = drive(G4_RED, g4_view(at(date.fromisoformat(w[2])),
                                    [fire(end=SIG_END)], bars=bars), sd)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["kind"], "entry")

    def test_red_timeout_five_session_timeout(self):
        sd = tempfile.mkdtemp()
        w = FOLLOW[:5]
        qbars, abars = [], []
        qbars.append({"t": SIG_END, "o": 99.0, "h": 99.0, "l": 99.0,
                      "c": 99.0, "v": 1e6})
        abars.append({"t": SIG_END, "o": 5.0, "h": 5.0, "l": 5.0,
                      "c": 5.0, "v": 1e6})
        for i, d in enumerate(w):
            qbars.append({"t": d, "o": 100 + i, "h": 100 + i,
                          "l": 100 + i, "c": 100 + i, "v": 1e6})
            abars.append({"t": d, "o": 5.0, "h": 5.0, "l": 5.0,
                          "c": 5.0, "v": 1e6})
        bars = {"QQQ|1Day": qbars, "AAA|1Day": abars}
        drive(G4_RED, g4_view(at(SESSIONS[25]), [fire(end=SIG_END)],
                              bars=bars), sd)
        entry_day = [d for d in SESSION_STRS if d > w[4]][0]
        out = drive(G4_RED, g4_view(at(date.fromisoformat(entry_day)),
                                    [fire(end=SIG_END)], bars=bars), sd)
        self.assertEqual(len(out), 1)  # timeout entry after 5th session


class TestG4Refusals(unittest.TestCase):
    def _no_pending_entry(self, **kw):
        sd = tempfile.mkdtemp()
        drive(G4_DELAY, g4_view(at(SESSIONS[25]),
                                [fire(end=SIG_END, **kw)]), sd)
        out = drive(G4_DELAY,
                    g4_view(at(date.fromisoformat(FOLLOW[1])),
                            [fire(end=SIG_END, **kw)]), sd)
        self.assertEqual(out, [])

    def test_cool_vol_refuses_hot_book(self):
        self._no_pending_entry(atr_ratio=0.5)

    def test_cyan_marker_refuses(self):
        # GATE-CURE-20261112: renamed in behavior, not in name
        # history: the marker no longer gates, so a buy-cyan fire
        # with passing numerics produces the pending entry on the
        # follow session (the pre-cure refusal pin is preserved in
        # ~/workspace/.gatecure-20261112/pre/tests/).
        sd = tempfile.mkdtemp()
        drive(G4_DELAY, g4_view(at(SESSIONS[25]),
                                [fire(end=SIG_END, markers=["buy-cyan"])]), sd)
        out = drive(G4_DELAY,
                    g4_view(at(date.fromisoformat(FOLLOW[1])),
                            [fire(end=SIG_END, markers=["buy-cyan"])]), sd)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["kind"], "entry")

    def test_price_above_10_refuses(self):
        self._no_pending_entry(native_close=10.5)

    def test_shallow_depth_refuses(self):
        self._no_pending_entry(depth60=60.0)

    def test_low_dollar_volume_refuses(self):
        self._no_pending_entry(dv20=1e6)

    def test_missing_fires_refuses(self):
        out = drive(G4_DELAY, g4_view(at(SESSIONS[25]), []))
        self.assertEqual(out, [])


class TestG4ExitAndReserve(unittest.TestCase):
    def test_52_week_scheduled_exit(self):
        entry = date(2025, 2, 18)
        monday = entry - timedelta(days=entry.weekday())
        week = monday + timedelta(weeks=51)
        rows = [d for d in SESSIONS if week <= d < week + timedelta(days=7)]
        xday = rows[-1]
        pos = [{"symbol": "AAA", "qty": 79, "avg_price": 5.0,
                "opened_at": at(entry).isoformat(), "issuer_id": "iss-AAA"}]
        out = drive(G4_DELAY, g4_view(at(xday), [], positions=pos))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["kind"], "exit")
        self.assertIn("52_week", out[0]["reason"])
        # one week earlier: no exit
        out2 = drive(G4_DELAY, g4_view(at(xday - timedelta(days=7)), [],
                                       positions=pos))
        self.assertEqual(out2, [])

    def test_reserve_weekly_qqq_buy(self):
        monday = date(2025, 3, 3)
        assert monday.weekday() == 0 and monday.isoformat() in SESSION_STRS
        bars = {"QQQ|1Day": [{"t": "2025-02-28", "o": 100.0, "h": 100.0,
                              "l": 100.0, "c": 100.0, "v": 1e6}]}
        out = drive(G4_RES, g4_view(at(monday), [], bars=bars))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["symbol"], "QQQ")
        self.assertEqual(out[0]["qty"], 99)  # floor(10000/(100*1.001))

    def test_reserve_funding_sale(self):
        sd = tempfile.mkdtemp()
        pos = [{"symbol": "QQQ", "qty": 200, "avg_price": 100.0,
                "opened_at": at(date(2025, 2, 10)).isoformat(),
                "issuer_id": "QQQ"}]
        v = g4_view(at(date.fromisoformat(FOLLOW[0])),
                    [fire(end=SIG_END)], positions=pos, cash=0.0)
        v["quotes"] = {"QQQ": {"bid": 100.0, "ask": 100.0}}
        out = drive(G4_RES, v, sd)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["kind"], "exit")
        self.assertEqual(out[0]["symbol"], "QQQ")
        self.assertEqual(out[0]["qty"], 5)  # ceil(400/(100*0.999))
        self.assertIn("reserve_ticket_funding", out[0]["reason"])


# ---------------------------------------------------------------- timing
NOW_H = datetime(2026, 10, 23, 15, 0, tzinfo=timezone.utc)  # 11:00 ET


def hour_bars(n=61, end=NOW_H, close=100.0):
    out = []
    for i in range(n):
        t = end - timedelta(hours=n - i)
        out.append({"t": t.isoformat(),
                    "end": (t + timedelta(hours=1)).isoformat(),
                    "o": close, "h": close + 1, "l": close - 1,
                    "c": close, "v": 1000})
    return out


def swing(**kw):
    s = {"confirmed": True, "score": 9, "invalidation": 99.0,
         "target": 110.0, "phenotype": "BULL", "usesFutureData": False,
         "bearishConflict": False}
    s.update(kw)
    return {"swing": s}


def hour_view(sid_bars=61, sw=None, quotes=None, positions=None):
    return {"now": NOW_H.isoformat(),
            "bars": {"MU|1Hour": hour_bars(sid_bars)},
            "timing_signals": {"MU": sw if sw is not None else swing()},
            "quotes": quotes or {"MU": {"bid": 99.9, "ask": 100.0}},
            "positions": positions or [],
            "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0},
            "extra": {}}


class TestHourly(unittest.TestCase):
    def test_entry_floor0(self):
        out = drive(H00, hour_view())
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["stop"], 99.0)
        self.assertEqual(out[0]["qty"], 9)  # notional cap $1000

    def test_entry_floor1_widens_stop(self):
        out = drive(H10, hour_view())
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["stop"], 98.0)  # entry - 1*ATR(2)

    def test_delay1_entry(self):
        out = drive(H01, hour_view(sid_bars=62, sw=swing(invalidation=98.0)))
        self.assertEqual(len(out), 1)

    def test_delay1_geometry_death_refuses(self):
        v = hour_view(sid_bars=62)
        v["bars"]["MU|1Hour"][-1]["l"] = 98.5  # waited bar pierced stop
        self.assertEqual(drive(H01, v), [])

    def test_low_score_refuses(self):
        self.assertEqual(drive(H00, hour_view(sw=swing(score=7))), [])

    def test_unconfirmed_refuses(self):
        self.assertEqual(drive(H00, hour_view(sw=swing(confirmed=False))),
                         [])

    def test_missing_swing_input_refuses(self):
        v = hour_view()
        v["timing_signals"] = {}
        self.assertEqual(drive(H00, v), [])

    def test_stop_exit(self):
        pos = [{"symbol": "MU", "qty": 9, "avg_price": 100.0,
                "opened_at": NOW_H.isoformat(),
                "meta": {"stop": 99.0, "target": 110.0}}]
        v = hour_view(positions=pos,
                      quotes={"MU": {"bid": 98.0, "ask": 98.1}})
        out = drive(H00, v)
        self.assertEqual([o["kind"] for o in out], ["exit"])
        self.assertIn("stop", out[0]["reason"])

    def test_target_exit(self):
        pos = [{"symbol": "MU", "qty": 9, "avg_price": 100.0,
                "opened_at": NOW_H.isoformat(),
                "meta": {"stop": 99.0, "target": 110.0}}]
        v = hour_view(positions=pos,
                      quotes={"MU": {"bid": 111.0, "ask": 111.1}})
        out = drive(H00, v)
        self.assertEqual([o["kind"] for o in out], ["exit"])
        self.assertIn("target", out[0]["reason"])

    def test_deadline_exit(self):
        pos = [{"symbol": "MU", "qty": 9, "avg_price": 100.0,
                "opened_at": NOW_H.isoformat(),
                "meta": {"stop": 50.0, "target": 500.0,
                         "signal_end": (NOW_H - timedelta(hours=21))
                         .isoformat(), "deadline_bars": 20}}]
        out = drive(H00, hour_view(positions=pos))
        self.assertEqual([o["kind"] for o in out], ["exit"])
        self.assertIn("deadline", out[0]["reason"])


def cloud_fixture(prior_high=130.0, hour_falling=False):
    end = datetime(2026, 10, 23, 14, 50, tzinfo=timezone.utc)  # 10:50 ET
    ten = []
    for i in range(30):
        c = 100 + 0.02 * i * i
        t = end - timedelta(minutes=10 * (30 - i))
        o, h, l = c, c + 0.2, c - 0.2
        if i == 29:
            l = 113.0  # wick touches the frozen EMA cloud (upper ~113.6)
        ten.append({"t": t.isoformat(),
                    "end": (t + timedelta(minutes=10)).isoformat(),
                    "o": o, "h": h, "l": l, "c": c, "v": 1000})
    hour = []
    for i in range(60):
        c = (130 - 0.5 * i) if hour_falling else (90 + 0.2 * i)
        t = end - timedelta(hours=60 - i)
        hour.append({"t": t.isoformat(),
                     "end": (t + timedelta(hours=1)).isoformat(),
                     "o": c, "h": c + 0.3, "l": c - 0.3, "c": c, "v": 1000})
    daily = [{"t": "2026-10-22", "o": 100.0, "h": prior_high, "l": 99.0,
              "c": 105.0, "v": 1000}]
    return {"now": end.isoformat(),
            "bars": {"MU|10Min": ten, "MU|1Hour": hour, "MU|1Day": daily},
            "quotes": {"MU": {"bid": ten[-1]["c"] - 0.05,
                              "ask": ten[-1]["c"]}},
            "positions": [],
            "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0},
            "extra": {}}


class TestCloud(unittest.TestCase):
    def test_base_entry(self):
        out = drive(CLOUD_B, cloud_fixture())
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["kind"], "entry")
        self.assertEqual(out[0]["target"], 130.0)
        self.assertIn("exit_at", out[0])  # forced intraday deadline

    def test_aggressive_sizes_double(self):
        b = drive(CLOUD_B, cloud_fixture())
        a = drive(CLOUD_A, cloud_fixture())
        self.assertEqual(len(a), 1)
        self.assertGreater(a[0]["qty"], b[0]["qty"])

    def test_no_cloud_uptrend_refuses(self):
        self.assertEqual(drive(CLOUD_B, cloud_fixture(hour_falling=True)),
                         [])

    def test_two_r_failure_refuses(self):
        v = cloud_fixture()
        px = v["bars"]["MU|10Min"][-1]["c"]
        v["bars"]["MU|1Day"][0]["h"] = px + 0.5  # target < 2R away
        self.assertEqual(drive(CLOUD_B, v), [])

    def test_cloud_stop_exit(self):
        v = cloud_fixture()
        v["positions"] = [{"symbol": "MU", "qty": 5, "avg_price": 110.0,
                           "opened_at": v["now"],
                           "meta": {"stop": 200.0, "target": 300.0}}]
        out = drive(CLOUD_B, v)
        self.assertEqual([o["kind"] for o in out], ["exit"])

    def test_cloud_time_exit(self):
        v = cloud_fixture()
        v["positions"] = [{"symbol": "MU", "qty": 5, "avg_price": 110.0,
                           "opened_at": v["now"],
                           "meta": {"stop": 1.0, "target": 999.0,
                                    "exit_at": "2026-10-23T14:00:00+00:00"}}]
        out = drive(CLOUD_B, v)
        self.assertEqual([o["kind"] for o in out], ["exit"])
        self.assertIn("time", out[0]["reason"])


def overnight_fixture(current_ret=0.01, sessions_n=130):
    days = weekdays(date(2026, 4, 27), sessions_n)
    today = days[-1]
    bars = []
    for i, d in enumerate(days):
        r = current_ret if d == today else 0.0
        a = {"t": datetime.combine(d, time(12, 30), ET).isoformat(),
             "o": 100.0, "h": 100.0, "l": 100.0, "c": 100.0, "v": 1000}
        b = {"t": datetime.combine(d, time(14, 30), ET).isoformat(),
             "o": 100.0, "h": 100.0, "l": 100.0, "c": 100 * (1 + r),
             "v": 1000}
        bars += [a, b]
    now = datetime.combine(today, time(15, 32), ET)
    return {"now": now.astimezone(timezone.utc).isoformat(),
            "bars": {"MU|30Min": bars},
            "quotes": {"MU": {"bid": 100.9, "ask": 101.0}},
            "positions": [],
            "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0},
            "extra": {"session_dates": [d.isoformat() for d in days]}}


class TestOvernight(unittest.TestCase):
    def test_entry(self):
        out = drive(ON25, overnight_fixture())
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["kind"], "entry")
        self.assertIn("exit_at", out[0])  # next session open

    def test_weak_afternoon_refuses(self):
        self.assertEqual(drive(ON25, overnight_fixture(current_ret=-0.01)),
                         [])

    def test_next_open_exit(self):
        v = overnight_fixture()
        v["now"] = datetime(2026, 10, 26, 14, 0,
                            tzinfo=timezone.utc).isoformat()
        v["positions"] = [{"symbol": "MU", "qty": 9, "avg_price": 101.0,
                           "opened_at": "2026-10-23T19:32:00+00:00",
                           "meta": {"exit_at":
                                    "2026-10-26T13:30:00+00:00"}}]
        out = drive(ON25, v)
        self.assertEqual([o["kind"] for o in out], ["exit"])
        self.assertIn("time", out[0]["reason"])


class TestRegistryAndE2E(unittest.TestCase):
    def test_config_rows_and_inputs(self):
        from desk3.aster_batch15 import config_rows
        rows = {r["id"]: r for r in config_rows()}
        self.assertEqual(sorted(rows), sorted(IDS))
        cfg = json.load(open(os.path.join(ROOT, "config", "sleeves.json")))
        have = {r["id"]: r for r in cfg["sleeves"]}
        for sid in IDS:
            self.assertIn(sid, have)
            self.assertEqual(have[sid]["inputs"], rows[sid]["inputs"])
            self.assertEqual(have[sid]["slice"]["capital_usd"], 10000.0)
            mod = importlib.import_module(f"adapters3.{sid}")
            self.assertEqual(list(mod.INPUTS), rows[sid]["inputs"])

    def test_hourly_unfed_by_producer_absence(self):
        # timing_signals is declared but no v3 producer emits it yet:
        # the sleeve must land visibly UNFED, never fake-fed.
        from desk3.aster_batch15 import PRODUCERS
        produced = {o for p in PRODUCERS for o in p["outputs"]}
        self.assertNotIn("timing_signals", produced)

    def test_e2e_hourly_roundtrip_fake_broker(self):
        from desk3.broker import FakeBroker
        from desk3.dispatcher import Dispatcher
        out = drive(H00, hour_view())
        self.assertEqual(len(out), 1)
        tmp = tempfile.mkdtemp()
        broker = FakeBroker(prices={"MU": 100.0})
        disp = Dispatcher(tmp, broker,
                          slices={H00: {"capital_usd": 10000.0,
                                        "cash_usd": 10000.0}})
        r = disp.process_intent(out[0], H00)
        self.assertEqual(r["status"], "filled")
        held = disp.slice_for(H00)["positions"]
        self.assertIn("MU", held)
        pos = [{"symbol": "MU", "qty": held["MU"]["qty"],
                "avg_price": 100.0, "opened_at": NOW_H.isoformat(),
                "meta": {"stop": 99.0, "target": 110.0}}]
        v = hour_view(positions=pos,
                      quotes={"MU": {"bid": 111.0, "ask": 111.1}})
        ex = drive(H00, v)
        r2 = disp.process_intent(ex[0], H00)
        self.assertEqual(r2["status"], "filled")
        self.assertEqual(disp.slice_for(H00)["positions"], {})

    def test_e2e_g4_roundtrip_fake_broker(self):
        from desk3.broker import FakeBroker
        from desk3.dispatcher import Dispatcher
        sd = tempfile.mkdtemp()
        drive(G4_DELAY, g4_view(at(SESSIONS[25]), [fire(end=SIG_END)]), sd)
        entry_day = date.fromisoformat(FOLLOW[1])
        out = drive(G4_DELAY, g4_view(at(entry_day), [fire(end=SIG_END)]),
                    sd)
        tmp = tempfile.mkdtemp()
        broker = FakeBroker(prices={"AAA": 5.0})
        disp = Dispatcher(tmp, broker,
                          slices={G4_DELAY: {"capital_usd": 10000.0,
                                             "cash_usd": 10000.0}})
        r = disp.process_intent(out[0], G4_DELAY)
        self.assertEqual(r["status"], "filled")
        held = disp.slice_for(G4_DELAY)["positions"]
        self.assertIn("AAA", held)
        monday = entry_day - timedelta(days=entry_day.weekday())
        week = monday + timedelta(weeks=51)
        rows = [d for d in SESSIONS
                if week <= d < week + timedelta(days=7)]
        pos = [{"symbol": "AAA", "qty": held["AAA"]["qty"],
                "avg_price": 5.0,
                "opened_at": at(entry_day).isoformat(),
                "issuer_id": "iss-AAA"}]
        ex = drive(G4_DELAY, g4_view(at(rows[-1]), [], positions=pos), sd)
        r2 = disp.process_intent(ex[0], G4_DELAY)
        self.assertEqual(r2["status"], "filled")
        self.assertEqual(disp.slice_for(G4_DELAY)["positions"], {})


if __name__ == "__main__":
    unittest.main()
