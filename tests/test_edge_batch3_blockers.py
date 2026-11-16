"""Edge batch 3 blockers (ENH-ETWIN8-20261024 + ENH-NAVBASE-20261024).

Batch-8 ETF engine (core25_c098, core25_m150, drift1_c098): the
09:35-09:40 ET window was read off the raw clock hour while the desk
cycle stamps view["now"] in UTC — the window fired 05:35-05:40 ET and
never in RTH. Fail-first: the UTC-stamp tests fail on the pre-cure
engine (raw-hour gate).

Batch-9 ETF engine (exsmh1/interval1/interval_core25, c098+m150):
targets were sized on nav = static config cash ($10,000) + held
value — phantom cash that ratchets targets toward
gross*cash/(1-gross). Cure: NAV = slice capital. Fail-first: the
held-position buy-qty tests fail on the pre-cure engine (legacy
basis). DRIFT sleeves: NAV term proven non-binding (VERIFY-ONLY).
"""
import importlib
import unittest

B8 = ["aster_etf_core25_c098", "aster_etf_core25_m150", "aster_etf_drift1_c098"]
B9_ENH = ["aster_etf_exsmh1_c098", "aster_etf_exsmh1_m150",
          "aster_etf_interval1_c098", "aster_etf_interval1_m150",
          "aster_etf_interval_core25_c098", "aster_etf_interval_core25_m150"]
B9_DRIFT = ["aster_etf_drift1_m150", "aster_etf_interval_drift1_c098",
            "aster_etf_interval_drift1_m150"]
UNIVERSE = ["QQQ", "SPY", "SMH", "XLB", "XLC", "XLE", "XLF", "XLI",
            "XLK", "XLP", "XLRE", "XLU", "XLV", "XLY"]


def ev(sid, v, ctx=None):
    return importlib.import_module(f"adapters3.{sid}").evaluate(v, ctx or {})


# ---- batch-8 fixtures (mirrors test_aster_batch8_blockers) ----
def fb(px, n=130, start=None):
    return [{"t": f"2026-01-{(i % 28) + 1:02d}", "o": px, "h": px, "l": px,
             "c": (start if (start is not None and i == n - 127) else px),
             "v": 1000} for i in range(n)]


def basket8(leader="XLK"):
    m = {s: fb(100.0) for s in UNIVERSE}
    if leader:
        m[leader] = fb(120.0, start=100.0)
    return m


def view8(now, extra=None):
    return {"now": now, "bars": basket8(), "positions": [], "quotes": {},
            "extra": extra or {}}


CTX8 = {"session": "2026-10-26", "slice": {"capital_usd": 10000.0}}


class TestEtwin8(unittest.TestCase):
    def test_utc_stamp_inside_et_window_fires(self):
        for sid in B8:  # 13:37Z = 09:37 ET
            self.assertTrue(ev(sid, view8("2026-10-26T13:37:00+00:00"), CTX8), sid)

    def test_utc_stamp_at_0937utc_is_premarket_no_fire(self):
        for sid in B8:  # 09:37Z = 05:37 ET
            self.assertEqual(ev(sid, view8("2026-10-26T09:37:00+00:00"), CTX8), [], sid)

    def test_switch_off_restores_legacy_exactly(self):
        off = {"aster_batch8_enh": {"et_window": False}}
        for sid in B8:
            self.assertEqual(ev(sid, view8("2026-10-26T13:37:00+00:00", off), CTX8), [], sid)
            self.assertTrue(ev(sid, view8("2026-10-26T09:37:00+00:00", off), CTX8), sid)

    def test_naive_stamp_still_read_as_et(self):
        for sid in B8:
            self.assertTrue(ev(sid, view8("2026-10-26T09:37:00"), CTX8), sid)

    def test_paired_shadow_record(self):
        j = {"records": []}
        extra = {"aster_batch8_exp_journal": j}
        ev("aster_etf_core25_c098", view8("2026-10-26T13:37:00+00:00", extra), CTX8)
        self.assertEqual(len(j["records"]), 1)
        self.assertTrue(j["records"][0]["treatment_window_open"])
        self.assertFalse(j["records"][0]["control_window_open"])


# ---- batch-9 fixtures (mirrors test_aster_batch9_blockers) ----
def series(base, growth):
    return [base * (1 + growth * (i / 259.0)) for i in range(260)]


def make_bars9(winner="XLK"):
    m = {}
    for s in UNIVERSE:
        g = 0.60 if s == winner else 0.05
        rows = [{"t": "2026-09-15", "o": c, "h": c, "l": c, "c": c, "v": 1000}
                for c in series(100.0, g)]
        rows[-1] = dict(rows[-1], t="2026-10-15")
        m[f"{s}|1Day"] = rows
    return m


def view9(sid, positions=None, extra=None, cash=10000.0):
    b = make_bars9("XLK")
    v = {"now": "2026-10-05T13:36:00+00:00", "bars": b,
         "positions": positions or [],
         "slice": {"capital_usd": 10000.0, "cash_usd": cash},
         "extra": extra or {}}
    if "interval" in sid:
        v["bars_secondary"] = b
    return v


HELD_XLK = [{"symbol": "XLK", "qty": 10, "avg_price": 100.0,
             "signal_month": "2026-09"}]
XLK_PX = 160.0  # series(100, 0.60) last close


class TestNavbase(unittest.TestCase):
    def test_held_position_buy_sized_on_capital_not_phantom_cash(self):
        # treatment: floor(0.98*10000/160)-10 = 51; legacy: nav=11600 -> 61
        o = ev("aster_etf_exsmh1_c098", view9("aster_etf_exsmh1_c098", HELD_XLK))
        self.assertEqual(len(o), 1)
        self.assertEqual(o[0]["qty"], int(0.98 * 10000 // XLK_PX) - 10)

    def test_switch_off_restores_legacy_basis_exactly(self):
        off = {"aster_etf_b9_enh": {"nav_basis": False}}
        o = ev("aster_etf_exsmh1_c098", view9("aster_etf_exsmh1_c098", HELD_XLK, off))
        legacy_nav = 10000.0 + 10 * XLK_PX
        self.assertEqual(o[0]["qty"], int(0.98 * legacy_nav // XLK_PX) - 10)

    def test_all_enhanced_sleeves_change_decision_on_held_fixture(self):
        for sid in B9_ENH:
            on = ev(sid, view9(sid, HELD_XLK))
            off = ev(sid, view9(sid, HELD_XLK, {"aster_etf_b9_enh": {"nav_basis": False}}))
            self.assertNotEqual([(i["symbol"], i["qty"]) for i in on],
                                [(i["symbol"], i["qty"]) for i in off], sid)

    def test_flat_entry_unchanged(self):
        for sid in B9_ENH:
            on = ev(sid, view9(sid))
            off = ev(sid, view9(sid, extra={"aster_etf_b9_enh": {"nav_basis": False}}))
            self.assertEqual([(i["symbol"], i["qty"]) for i in on],
                             [(i["symbol"], i["qty"]) for i in off], sid)

    def test_paired_shadow_record(self):
        j = {"records": []}
        ev("aster_etf_exsmh1_c098",
           view9("aster_etf_exsmh1_c098", HELD_XLK, {"aster_etf_b9_exp_journal": j}))
        self.assertEqual(len(j["records"]), 1)
        r = j["records"][0]
        self.assertEqual(r["treatment_nav"], 10000.0)
        self.assertEqual(r["control_nav"], 10000.0 + 10 * XLK_PX)
        self.assertNotEqual(r["treatment_desired"], r["control_desired"])

    def test_leader1_c098_not_in_enhancement_set(self):
        # batch-4's sleeve shares this engine; its basis stays legacy
        o = ev("aster_etf_leader1_c098", view9("aster_etf_leader1_c098", HELD_XLK))
        legacy_nav = 10000.0 + 10 * XLK_PX
        self.assertEqual(o[0]["qty"], int(0.98 * legacy_nav // XLK_PX) - 10)


class TestDriftVerifyOnly(unittest.TestCase):
    def test_nav_term_nonbinding_across_fixtures(self):
        fixtures = [
            [], HELD_XLK,
            [{"symbol": "SPY", "qty": 100, "avg_price": 100.0, "signal_month": "2026-09"},
             {"symbol": "XLK", "qty": 10, "avg_price": 100.0, "signal_month": "2026-09"}],
            [{"symbol": "XLK", "qty": 100, "avg_price": 100.0, "signal_month": "2026-09"}],
        ]
        for sid in B9_DRIFT:
            for pos in fixtures:
                on = ev(sid, view9(sid, pos))
                legacy = ev(sid, view9(sid, pos, {"aster_etf_b9_enh": {"nav_basis": True}}))
                # engine ignores the switch for drift ids (not in set):
                # emitted decisions are the designed drift decisions
                self.assertEqual([(i["symbol"], i["side"], i["qty"]) for i in on],
                                 [(i["symbol"], i["side"], i["qty"]) for i in legacy],
                                 (sid, pos))


if __name__ == "__main__":
    unittest.main()
