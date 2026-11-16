"""Edge batch 1 blockers (ENH-LAZ-REPRICE / ENH-ABS-WINDOW /
ENH-ABS4H-CATCHUP, 2026-10-24). Each test fails on the pre-change
engines and passes on the treated ones; the OFF position of every
switch is asserted to restore the pre-change rule exactly."""
import shutil, sys, tempfile, unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
UTC = timezone.utc


def iso(d):
    return d.isoformat().replace("+00:00", "Z")


# ------------------------------------------------------------- Lazarus
def _laz_view(sid, fire_px, cur_px, age, red_last=True):
    now = datetime(2026, 10, 26, 14, 0, tzinfo=UTC)
    base = datetime(2026, 10, 20, tzinfo=UTC)
    bars = []
    for i in range(10):
        c = cur_px if i < 9 else (cur_px - 0.1 if red_last else cur_px)
        bars.append({"t": iso(base + timedelta(days=i)), "o": c,
                     "h": c * 1.01, "l": c * 0.99, "c": c, "v": 1e6})
    fire = {"sleeve_id": sid, "symbol": "ACME",
            "fired_at": iso(now - age), "price": fire_px,
            "qqq_red": True, "stock_red": True}
    return {"now": iso(now), "lazarus_fires": [fire],
            "bars": {"ACME|1Day": bars}, "positions": []}


class LazReprice(unittest.TestCase):
    def setUp(self):
        self.sd = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.sd, ignore_errors=True)

    def _run(self, sid, fp, cp, age, ctx_extra=None):
        from desk3.lazarus import evaluate
        ctx = {"state_dir": self.sd}
        if ctx_extra:
            ctx.update(ctx_extra)
        return evaluate(sid, _laz_view(sid, fp, cp, age), ctx)

    def test_on_sizes_and_stops_off_fresh_price(self):
        out = self._run("1d", 10.0, 12.5, timedelta(hours=47))
        self.assertEqual(len(out), 1)
        e = out[0]
        self.assertEqual(e["qty"], 139)            # 1725 // 12.4
        self.assertEqual(e["stop_price"], 10.54)   # 15% below CURRENT
        self.assertEqual(e["price_hint"], 12.4)    # last bar close
        rec = e["enhance_exp"]["records"][0]
        self.assertEqual(rec["control_qty"], 172)
        self.assertEqual(rec["control_stop"], 8.5)
        self.assertEqual(rec["treatment_qty"], 139)

    def test_off_restores_fire_price_rule_exactly(self):
        out = self._run("1d", 10.0, 12.5, timedelta(hours=47),
                        {"enhance": {"1d": {"fresh_price": False}}})
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["qty"], 172)
        self.assertEqual(out[0]["stop_price"], 8.5)
        self.assertNotIn("enhance_exp", out[0])

    def test_1dc_undershoot_cured(self):
        out = self._run("1dc", 20.0, 10.0, timedelta(hours=47))
        self.assertEqual(out[0]["qty"], 18)  # was 9 at the stale print

    def test_1h_fresh_within_30min_fire(self):
        out = self._run("1h", 10.0, 12.5, timedelta(minutes=20))
        self.assertEqual(out[0]["qty"], 139)  # 1725 // 12.4 (red bar)

    def test_no_bars_falls_back_to_fire_price(self):
        from desk3.lazarus import evaluate
        v = _laz_view("1w", 10.0, 12.5, timedelta(days=7))
        v["bars"] = {}
        out = evaluate("1w", v, {"state_dir": self.sd})
        self.assertEqual(out[0]["qty"], 128)  # baseline fire-price qty


# ------------------------------------------------------ ADA absorption
def _ada_bars(n=310):
    start = datetime(2025, 1, 1, tzinfo=UTC)
    bars = []
    for i in range(n):
        bars.append({"t": iso(start + timedelta(hours=4 * i)),
                     "o": 1.0, "h": 1.01, "l": 0.99, "c": 1.0,
                     "v": 1000.0})
    bars[n - 3].update({"o": 1.0, "h": 1.0, "l": 0.90, "c": 0.92,
                        "v": 100000.0})
    bars[n - 2].update({"o": 0.93, "h": 0.99, "l": 0.92, "c": 0.98,
                        "v": 5000.0})
    return bars


def _ada(family, capacity, lag_s, funding=None, ctx=None):
    from aster_sleeves._common import evaluate_crypto
    bars = _ada_bars()
    entry_close = datetime.fromisoformat(
        bars[-1]["t"].replace("Z", "+00:00")) + timedelta(hours=4)
    view = {"now": iso(entry_close + timedelta(seconds=lag_s)),
            "bars": {"ADAUSDT|4Hour": bars}, "positions": [],
            "slice": {"cash_usd": 10000.0}}
    if funding is not None:
        view["funding"] = {"ADAUSDT": {"rate": funding}}
    sid = "aster_abs_base_ada_fullcash"
    return evaluate_crypto(view, ctx or {}, sid, family, capacity)


class AbsWindow(unittest.TestCase):
    def test_on_enters_within_one_cadence(self):
        for fam, cap, fund in [("absorption_base", "fullcash", None),
                               ("absorption_base", "volume1pct", None),
                               ("absorption_negative_funding", "fullcash",
                                -0.001),
                               ("absorption_nonnegative_funding",
                                "fullcash", 0.001)]:
            out = _ada(fam, cap, 1800, fund)
            self.assertEqual(len(out), 1, fam)
            rec = out[0]["enhance_exp"]["records"][0]
            self.assertEqual(rec["control"],
                             "no_entry_outside_300s_window")
            self.assertEqual(rec["lag_s"], 1800.0)

    def test_off_restores_300s_window_exactly(self):
        ctx = {"enhance": {"entry_window_cadence": False}}
        self.assertEqual(_ada("absorption_base", "fullcash", 1800,
                              ctx=ctx), [])
        self.assertEqual(len(_ada("absorption_base", "fullcash", 120,
                                  ctx=ctx)), 1)

    def test_beyond_one_cadence_still_refused(self):
        self.assertEqual(_ada("absorption_base", "fullcash", 3700), [])

    def test_in_window_entry_has_no_shadow_record(self):
        out = _ada("absorption_base", "fullcash", 120)
        self.assertNotIn("enhance_exp", out[0])


# ------------------------------------------------- ENJ/LINK 4h catch-up
def _abs4h_bars(n=310, confirm_at=-1, hold_close=0.99):
    start = datetime(2025, 1, 1, tzinfo=UTC)
    bars = []
    for i in range(n):
        bars.append({"t": iso(start + timedelta(hours=4 * i)),
                     "o": 1.0, "h": 1.01, "l": 0.99, "c": 1.0,
                     "v": 1000.0})
    si = n + confirm_at - 1
    bars[si].update({"o": 1.0, "h": 1.0, "l": 0.90, "c": 0.92,
                     "v": 100000.0})
    bars[si + 1].update({"o": 0.93, "h": 0.99, "l": 0.92, "c": 0.98,
                         "v": 5000.0})
    if confirm_at == -2:
        bars[n - 1].update({"o": 0.98, "h": 1.0, "l": 0.96,
                            "c": hold_close, "v": 3000.0})
    return bars


def _abs4h(sid, confirm_at, ctx=None, hold_close=0.99):
    from desk3.aster_batch1 import evaluate
    sym = "ENJUSDT" if "enj" in sid else "LINKUSDT"
    bars = _abs4h_bars(confirm_at=confirm_at, hold_close=hold_close)
    last_close = datetime.fromisoformat(
        bars[-1]["t"].replace("Z", "+00:00")) + timedelta(hours=4)
    view = {"now": iso(last_close + timedelta(minutes=30)),
            "bars": {f"{sym}|4Hour": bars}, "positions": [],
            "slice": {"cash_usd": 10000.0}}
    sd = tempfile.mkdtemp()
    try:
        c = {"state_dir": sd}
        if ctx:
            c.update(ctx)
        return evaluate(sid, view, c), sd
    except Exception:
        shutil.rmtree(sd, ignore_errors=True)
        raise


class Abs4hCatchup(unittest.TestCase):
    def test_on_catches_up_one_bar_late(self):
        for sid in ("aster_abs_enj_4h", "aster_abs_link_4h"):
            out, sd = _abs4h(sid, -2)
            try:
                self.assertEqual(len(out), 1, sid)
                self.assertIn("catchup", out[0]["reason"])
                rec = out[0]["enhance_exp"]["records"][0]
                self.assertEqual(rec["treatment"],
                                 "catchup_entry_one_bar_late")
                import json, os
                st = json.load(open(os.path.join(
                    sd, f"aster_b1_{sid}.json")))
                # deadline anchored to ORIGINAL confirmation bar
                bars = _abs4h_bars(confirm_at=-2)
                row = st["ENJUSDT" if "enj" in sid else "LINKUSDT"]
                self.assertTrue(row["confirm_close_at"]
                                .startswith(bars[-2]["t"][:13]))
                due = datetime.fromisoformat(row["exit_due_at"])
                conf = datetime.fromisoformat(row["confirm_close_at"])
                self.assertEqual(due - conf, timedelta(hours=16))
            finally:
                shutil.rmtree(sd, ignore_errors=True)

    def test_off_restores_single_look_rule(self):
        ctx = {"enhance": {"catchup_entry": False}}
        out, sd = _abs4h("aster_abs_enj_4h", -2, ctx=ctx)
        shutil.rmtree(sd, ignore_errors=True)
        self.assertEqual(out, [])

    def test_catchup_refused_when_absorption_invalidated(self):
        out, sd = _abs4h("aster_abs_enj_4h", -2, hold_close=0.94)
        shutil.rmtree(sd, ignore_errors=True)
        self.assertEqual(out, [])  # 0.94 < shock midpoint 0.95

    def test_normal_confirmation_unchanged(self):
        out, sd = _abs4h("aster_abs_link_4h", -1)
        shutil.rmtree(sd, ignore_errors=True)
        self.assertEqual(len(out), 1)
        self.assertNotIn("enhance_exp", out[0])


if __name__ == "__main__":
    unittest.main()
