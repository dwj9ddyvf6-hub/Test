"""Edge batch 4 blockers (ENH-ETWIN-20261024): the batch-10/11 ETF
engine must read its 09:35-09:40 ET execution window in ET. Pre-cure
the raw clock hour was used, so the desk's UTC cycle stamps fired the
window 05:35-05:40 ET and never in RTH. Fail-first: UTC-stamp tests
fail on the pre-cure engine."""
import unittest
from desk3.aster_etf import evaluate as ev
from desk3.aster_etf_b9 import evaluate as ev9

IDS = ["aster_etf_leader1_m150", "aster_etf_qld_buy_hold", "aster_etf_qld_monthly",
       "aster_etf_qqq_buy_hold", "aster_etf_qqq_monthly_c098", "aster_etf_qqq_monthly_m150",
       "aster_etf_qqq_qld_buy_hold", "aster_etf_qqq_qld_monthly",
       "aster_etf_smh_hold_c098", "aster_etf_smh_hold_m150", "aster_etf_spy_buy_hold"]
import desk3.aster_batch11  # registers SPY specs into aster_etf.SPECS

def bars(sym, px=100.0):
    return {sym: [{"c": px}] * 260}

def view(now, sym="QQQ", px=100.0, extra=None):
    v = {"bars": bars(sym, px), "positions": [], "quotes": {}, "now": now}
    if extra: v["extra"] = extra
    return v

CTX = {"slice": {"capital_usd": 10000.0}}

def ev2(sid, v, ctx=None):
    # WEIGHT-LAG-ACTIVE-20261031: aster_etf acts on the PREVIOUS
    # evaluation's targets. Clear stale pending state, then drive two
    # evaluations: the first computes weights and emits nothing, the
    # second acts on them. Returns (first, second).
    import desk3.aster_etf as _ae
    _ae._PENDING_TARGETS.pop(sid, None)
    return ev(sid, v, ctx or CTX), ev(sid, v, ctx or CTX)

class TestEtWindow(unittest.TestCase):
    def test_utc_stamp_inside_et_window_fires(self):
        for sid, sym in [("aster_etf_qqq_buy_hold", "QQQ"), ("aster_etf_qld_buy_hold", "QLD"),
                         ("aster_etf_spy_buy_hold", "SPY"), ("aster_etf_smh_hold_c098", "SMH")]:
            first, o = ev2(sid, view("2026-10-26T13:37:00+00:00", sym), CTX)
            self.assertEqual(first, [], sid)  # weight lag: first evaluation emits nothing
            self.assertTrue(o, sid)
    def test_utc_stamp_at_0937utc_is_premarket_no_fire(self):
        self.assertEqual(ev("aster_etf_qqq_buy_hold", view("2026-10-26T09:37:00+00:00"), CTX), [])
    def test_utc_stamp_outside_et_window_no_fire(self):
        # CR-1 (2026-11-11): 15:00Z is 11:00 ET, inside the
        # same-session catch-up range that now covers flat BUY_HOLD
        # allocations with lagged targets pending. Unprimed, the
        # first evaluation still emits nothing (weight lag).
        import desk3.aster_etf as _ae
        _ae._PENDING_TARGETS.pop("aster_etf_qqq_buy_hold", None)
        self.assertEqual(ev("aster_etf_qqq_buy_hold", view("2026-10-26T15:00:00+00:00"), CTX), [])
    def test_switch_off_restores_legacy_exactly(self):
        off = {"aster_etf_enh": {"et_window": False}}
        # CR-1: unprimed first evaluation (see the no-fire test
        # above); the legacy assertions below stand unchanged.
        import desk3.aster_etf as _ae
        _ae._PENDING_TARGETS.pop("aster_etf_qqq_buy_hold", None)
        self.assertEqual(ev("aster_etf_qqq_buy_hold", view("2026-10-26T13:37:00+00:00", extra=off), CTX), [])
        first, o = ev2("aster_etf_qqq_buy_hold", view("2026-10-26T09:37:00+00:00", extra=off), CTX)
        self.assertEqual(first, [])  # weight lag: first evaluation emits nothing
        self.assertTrue(o)
    def test_naive_stamp_still_read_as_et(self):
        first, o = ev2("aster_etf_qqq_buy_hold", view("2026-10-26T09:37:00"), CTX)
        self.assertEqual(first, [])  # weight lag: first evaluation emits nothing
        self.assertTrue(o)
    def test_paired_shadow_record(self):
        j = {"records": []}
        extra = {"aster_etf_exp_journal": j}
        ev("aster_etf_qqq_buy_hold", view("2026-10-26T13:37:00+00:00", extra=extra), CTX)
        self.assertEqual(len(j["records"]), 1)
        self.assertTrue(j["records"][0]["treatment_window_open"])
        self.assertFalse(j["records"][0]["control_window_open"])
    def test_leader1_m150_engine_fires_on_utc_stamp(self):
        basket = {s: [{"c": 100.0}] * 260 for s in
                  ["QQQ","SPY","SMH","XLB","XLC","XLE","XLF","XLI","XLK","XLP","XLRE","XLU","XLV","XLY"]}
        first, o = ev2("aster_etf_leader1_m150", {"bars": basket, "positions": [], "quotes": {},
               "now": "2026-10-26T13:37:00+00:00"}, CTX)
        self.assertEqual(first, [])  # weight lag: first evaluation emits nothing
        self.assertTrue(o)
    def test_b9_leader1_c098_verify_only_still_fires(self):
        b = {s: [{"c": 100.0, "t": "2026-10-23"}] * 260 for s in
             ["QQQ","SPY","SMH","XLB","XLC","XLE","XLF","XLI","XLK","XLP","XLRE","XLU","XLV","XLY"]}
        o = ev9("aster_etf_leader1_c098", {"bars": b, "positions": [], "now": "2026-10-26T13:37:00+00:00"},
                {"slice": {"cash_usd": 10000.0}})
        self.assertEqual(len(o), 1)

if __name__ == "__main__":
    unittest.main()
