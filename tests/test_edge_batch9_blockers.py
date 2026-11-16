"""EDGE BATCH 9 blockers: latched structural-trigger scan (LINK NFS
normalization / normalization_failure x3) + execution-window grace
(Tensor G4 x3, timing cloud x2, timing hourly x4).

Fail-first: pre-enhancement engines evaluated structural triggers only
on the latest bar once it was itself executable, and allowed entries
only in 09:30-09:35 ET (G4) / 5 min of actionable_at (timing), so the
enhanced-behavior tests below fail on the old code and pass after.
Switch OFF must restore the pre-change rule exactly.
"""
import importlib, os, sys, tempfile, unittest
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
ET = ZoneInfo("America/New_York")
NOW = datetime(2026, 10, 23, 16, 0, tzinfo=timezone.utc)
SYM = "LINKUSDT"
NF_F = "aster_r19_linkusdt_negative_funding_squeeze_normalization_failure_fullcash"
NF_V = "aster_r19_linkusdt_negative_funding_squeeze_normalization_failure_volume1pct"
NM_F = "aster_r19_linkusdt_negative_funding_squeeze_normalization_fullcash"

def lbars(n=25, shift_h=8, fail_idx=None):
    out = []
    for i in range(n):
        t = NOW - timedelta(hours=shift_h) - timedelta(hours=4 * (n - i))
        out.append({"t": t.isoformat(), "o": 20.0, "h": 20.5, "l": 19.5, "c": 20.0, "v": 100000.0})
    if fail_idx is not None:
        out[fail_idx].update({"c": 18.0, "l": 17.5})
    return out

def ldrive(sid, brs, funding, off=False):
    mod = importlib.import_module(f"adapters3.{sid}")
    view = {"now": NOW.isoformat(), "bars": {f"{SYM}|4Hour": brs},
            "funding": {SYM: funding},
            "positions": [{"symbol": SYM, "qty": 400.0, "avg_price": 20.0,
                           "opened_at": (NOW - timedelta(hours=20)).isoformat(),
                           "breakout_level": 20.5}],
            "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0},
            "params": {sid: {"enhance_trigger_latch": False}} if off else {},
            "extra": {}}
    return mod.evaluate(view, {"sleeve_id": sid, "state_dir": tempfile.mkdtemp()})

class TestLatchedTrigger(unittest.TestCase):
    def test_failure_trigger_latched_after_recovery_fullcash(self):
        b = lbars(fail_idx=-3)  # failure bar, then recovery bars
        self.assertEqual(len(ldrive(NF_F, b, 0.002)), 1)
    def test_failure_trigger_latched_after_recovery_volume(self):
        b = lbars(fail_idx=-3)
        self.assertEqual(len(ldrive(NF_V, b, 0.002)), 1)
    def test_failure_latch_off_restores_evaporation(self):
        b = lbars(fail_idx=-3)
        self.assertEqual(ldrive(NF_F, b, 0.002, off=True), [])
    def test_failure_latch_still_needs_funding(self):
        b = lbars(fail_idx=-3)
        self.assertEqual(ldrive(NF_F, b, -0.002), [])
    def test_normalization_verify_only_behavior(self):
        # VERIFY-ONLY evidence: funding-state trigger (not a bar event)
        # fires at the archive delay and refuses on negative funding.
        self.assertEqual(len(ldrive(NM_F, lbars(shift_h=8), 0.0)), 1)
        self.assertEqual(ldrive(NM_F, lbars(shift_h=8), -0.01), [])
        self.assertEqual(ldrive(NM_F, lbars(shift_h=0), 0.0), [])
    def test_no_trigger_no_exit(self):
        self.assertEqual(ldrive(NF_F, lbars(), 0.002), [])
        self.assertEqual(ldrive(NM_F, lbars(), -0.01), [])

# ---- batch15 fixtures (mirrors test_aster_batch15_blockers) ----
def weekdays(start, n):
    out, d = [], start
    while len(out) < n:
        if d.weekday() < 5: out.append(d)
        d += timedelta(days=1)
    return out
SESSIONS = weekdays(date(2025, 1, 6), 640); SESSION_STRS = [d.isoformat() for d in SESSIONS]
SIG_END = "2025-02-14"; FOLLOW = [d for d in SESSION_STRS if d > SIG_END]
def at(d, hh=9, mm=30):
    return datetime.combine(d, time(hh, mm), ET).astimezone(timezone.utc)
def fire(sym="AAA", end=None, **kw):
    f = {"symbol": sym, "issuer_id": "iss-" + sym, "signal_end": end,
         "markers": ["buy-green"], "native_close": 5.0, "depth60": 80.0,
         "ret60": 5.0, "vol20": 0.12, "dv20": 5e6, "atr_ratio": 1.5}
    f.update(kw); return f
def g4_view(now, fires, positions=None, bars=None):
    return {"now": now.isoformat(), "tensor_fires": fires, "positions": positions or [],
            "bars": bars or {"AAA|1Day": [{"t": "2025-01-03", "o": 5.0, "h": 5.1, "l": 4.9, "c": 5.0, "v": 1e6}]},
            "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0}, "quotes": {}, "extra": {}}
def drive15(sid, view, sd, off_key=None):
    mod = importlib.import_module(f"adapters3.{sid}")
    view.setdefault("extra", {})["session_dates"] = SESSION_STRS
    if off_key: view["params"] = {sid: {off_key: False}}
    return mod.evaluate(view, {"sleeve_id": sid, "cycle_id": "fx", "state_dir": sd})

G4D = "aster_r19_tensor_g4_hot_delay_25"; G4R = "aster_r19_tensor_g4_hot_reserve_25"; G4T = "aster_r19_tensor_g4_red_timeout_25"
class TestG4Grace(unittest.TestCase):
    def test_delay_entry_at_1000_et(self):
        sd = tempfile.mkdtemp()
        self.assertEqual(drive15(G4D, g4_view(at(SESSIONS[25]), [fire(end=SIG_END)]), sd), [])
        out = drive15(G4D, g4_view(at(date.fromisoformat(FOLLOW[1]), 10, 0), []), sd)
        self.assertEqual(len([o for o in out if o["kind"] == "entry"]), 1)
    def test_delay_grace_off_refuses_at_1000(self):
        sd = tempfile.mkdtemp()
        self.assertEqual(drive15(G4D, g4_view(at(SESSIONS[25]), [fire(end=SIG_END)]), sd), [])
        out = drive15(G4D, g4_view(at(date.fromisoformat(FOLLOW[1]), 10, 0), []), sd, off_key="enhance_window_grace")
        self.assertEqual(out, [])
    def test_reserve_entry_at_1000_et(self):
        sd = tempfile.mkdtemp()
        self.assertEqual(drive15(G4R, g4_view(at(SESSIONS[25]), [fire(end=SIG_END)]), sd), [])
        out = drive15(G4R, g4_view(at(date.fromisoformat(FOLLOW[1]), 10, 0), []), sd)
        self.assertEqual(len([o for o in out if o["kind"] == "entry"]), 1)
    def test_red_timeout_entry_at_1000_et(self):
        sd = tempfile.mkdtemp()
        w = FOLLOW[:5]
        qclose = {SIG_END: 101.0, w[0]: 102.0, w[1]: 99.0, w[2]: 99.5, w[3]: 100.0, w[4]: 100.5}
        qbars, abars = [], []
        for d in sorted(qclose):
            qbars.append({"t": d, "o": qclose[d], "h": qclose[d], "l": qclose[d], "c": qclose[d], "v": 1e6})
            abars.append({"t": d, "o": 5.0, "h": 5.0, "l": 5.0, "c": 5.0, "v": 1e6})
        bars = {"QQQ|1Day": qbars, "AAA|1Day": abars}
        drive15(G4T, g4_view(at(SESSIONS[25]), [fire(end=SIG_END)], bars=bars), sd)
        out = drive15(G4T, g4_view(at(date.fromisoformat(w[2]), 10, 0), [fire(end=SIG_END)], bars=bars), sd)
        self.assertEqual(len([o for o in out if o["kind"] == "entry"]), 1)
    def test_no_entry_after_1030(self):
        sd = tempfile.mkdtemp()
        self.assertEqual(drive15(G4D, g4_view(at(SESSIONS[25]), [fire(end=SIG_END)]), sd), [])
        out = drive15(G4D, g4_view(at(date.fromisoformat(FOLLOW[1]), 11, 0), []), sd)
        self.assertEqual(out, [])

NOW_H = datetime(2026, 10, 23, 15, 0, tzinfo=timezone.utc)
def hour_bars(n=61, end=NOW_H, close=100.0):
    out = []
    for i in range(n):
        t = end - timedelta(hours=n - i)
        out.append({"t": t.isoformat(), "end": (t + timedelta(hours=1)).isoformat(),
                    "o": close, "h": close + 1, "l": close - 1, "c": close, "v": 1000})
    return out
def hour_view(now, n=61, inv=99.0):
    return {"now": now.isoformat(), "bars": {"MU|1Hour": hour_bars(n)},
            "timing_signals": {"MU": {"swing": {"confirmed": True, "score": 9, "invalidation": inv,
                "target": 110.0, "phenotype": "BULL", "usesFutureData": False, "bearishConflict": False}}},
            "quotes": {"MU": {"bid": 99.9, "ask": 100.0}}, "positions": [],
            "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0}, "extra": {}}
HIDS = ["aster_r19_timing_hour_floor0_delay0", "aster_r19_timing_hour_floor1_delay0"]
class TestHourlyGrace(unittest.TestCase):
    def test_entry_10min_after_actionable(self):
        for sid in HIDS:
            out = drive15(sid, hour_view(NOW_H + timedelta(minutes=10)), tempfile.mkdtemp())
            self.assertEqual(len(out), 1, sid)
    def test_entry_10min_delay1(self):
        out = drive15("aster_r19_timing_hour_floor0_delay1",
                      hour_view(NOW_H + timedelta(minutes=10), n=62, inv=98.0), tempfile.mkdtemp())
        self.assertEqual(len(out), 1)
        out = drive15("aster_r19_timing_hour_floor1_delay1",
                      hour_view(NOW_H + timedelta(minutes=10), n=62, inv=98.0), tempfile.mkdtemp())
        self.assertEqual(len(out), 1)
    def test_grace_off_refuses_10min(self):
        v = hour_view(NOW_H + timedelta(minutes=10))
        out = drive15(HIDS[0], v, tempfile.mkdtemp(), off_key="enhance_actionable_grace")
        self.assertEqual(out, [])
    def test_no_entry_20min_after(self):
        out = drive15(HIDS[0], hour_view(NOW_H + timedelta(minutes=20)), tempfile.mkdtemp())
        self.assertEqual(out, [])

def cloud_fixture(now):
    end = datetime(2026, 10, 23, 14, 50, tzinfo=timezone.utc)
    ten = []
    for i in range(30):
        c = 100 + 0.02 * i * i; t = end - timedelta(minutes=10 * (30 - i))
        o, h, l = c, c + 0.2, c - 0.2
        if i == 29: l = 113.0
        ten.append({"t": t.isoformat(), "end": (t + timedelta(minutes=10)).isoformat(), "o": o, "h": h, "l": l, "c": c, "v": 1000})
    hour = []
    for i in range(60):
        c = 90 + 0.2 * i; t = end - timedelta(hours=60 - i)
        hour.append({"t": t.isoformat(), "end": (t + timedelta(hours=1)).isoformat(), "o": c, "h": c + 0.3, "l": c - 0.3, "c": c, "v": 1000})
    daily = [{"t": "2026-10-22", "o": 100.0, "h": 130.0, "l": 99.0, "c": 105.0, "v": 1000}]
    return {"now": now.isoformat(), "bars": {"MU|10Min": ten, "MU|1Hour": hour, "MU|1Day": daily},
            "quotes": {"MU": {"bid": ten[-1]["c"] - 0.05, "ask": ten[-1]["c"]}}, "positions": [],
            "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0}, "extra": {}}
class TestCloudGrace(unittest.TestCase):
    def test_entry_10min_after_signal_end(self):
        now = datetime(2026, 10, 23, 14, 50, tzinfo=timezone.utc) + timedelta(minutes=10)
        for sid in ("aster_r19_timing_cloud_base", "aster_r19_timing_cloud_aggressive"):
            out = drive15(sid, cloud_fixture(now), tempfile.mkdtemp())
            self.assertEqual(len(out), 1, sid)
    def test_cloud_grace_off_refuses(self):
        now = datetime(2026, 10, 23, 14, 50, tzinfo=timezone.utc) + timedelta(minutes=10)
        out = drive15("aster_r19_timing_cloud_base", cloud_fixture(now), tempfile.mkdtemp(), off_key="enhance_actionable_grace")
        self.assertEqual(out, [])

if __name__ == "__main__":
    unittest.main()
