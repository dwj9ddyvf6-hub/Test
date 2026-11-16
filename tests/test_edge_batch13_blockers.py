"""Edge batch 13 blockers — ENH-B13-* (2026-10-24).

Three decision-changing cures, each fail-first against the pre-cure
engine (verified by temporary revert in the batch work log):
- aster_tensor_{h1,w1}_recovery: entries sized/priced off the Tensor
  panel close, which can lag the executable bar by the bundle SLA
  (86400s). Cure: re-check the $5 floor and size off the latest bar
  close when a current bar exists (ENH-B13-TENSORREC-REPRICE).
- aster_tensor_leaps_{a,b}: entry paid the ask on 540-720 DTE LEAPS
  with NO spread check. Cure: refuse when (ask-bid)/mid > 0.30, the
  desk's existing options spread gate (ENH-B13-LEAPS-SPREAD).
- aster_xsp_pcs_{calm,graded}_{a,b}: the 10:00-10:05 ET entry window
  was sliced raw from the timestamp string, so UTC-stamped live
  snapshots never opened it. Cure: convert tz-aware stamps to ET
  (ENH-B13-XSP-ETWIN).
Every cure is behind a per-sleeve switch (default ON); OFF restores
the pre-change rule exactly, proven below. aurelia_gold is
VERIFY-ONLY this batch (see proof/enhance/aurelia_gold.json).
"""
import importlib, os, sys, tempfile, unittest
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "tests"))
import test_aster_batch1_blockers as b1
import test_aster_batch3_blockers as b3
import test_aster_batch4_blockers as b4


def ev(sid, view, ctx=None):
    return importlib.import_module(f"adapters3.{sid}").evaluate(view, ctx or {})


# ------------------------------------------------------- tensor rec
def rec_view(frame, bar_close, extra=None):
    tf = "1Hour" if frame == "1h" else "1Week"
    bars = {f"ACME|{tf}": [{"t": "2026-10-23", "o": bar_close,
                            "h": bar_close, "l": bar_close,
                            "c": bar_close, "v": 1000}]}
    if frame == "1wk":
        # AMENDED 2026-11-12 (GATE-CURE-W1-20261112): w1's 234-bar
        # minimum now reads the underlying daily source series, so
        # the weekly fixture carries one (250 bars). The reprice
        # assertions are unchanged (sizing reads the 1Week bar).
        bars["ACME|1Day"] = [{"t": f"2025-{(i % 12) + 1:02d}-01",
                              "o": 50.0, "h": 50.0, "l": 50.0,
                              "c": 50.0, "v": 1000}
                             for i in range(250)]
    v = {"now": "2026-10-23T14:00:00+00:00",
         "tensor": {"ACME": b1.repair_panel(frame)},
         "bars": bars,
         "positions": [], "slice": b1.slice10k()}
    if extra: v["extra"] = extra
    return v

def rec_ctx():
    return {"sleeve_id": "x", "state_dir": tempfile.mkdtemp(), "cycle_id": "fx"}

class TestTensorRecReprice(unittest.TestCase):
    def test_h1_sizes_off_current_bar_not_panel(self):
        o = ev("aster_tensor_h1_recovery", rec_view("1h", 25.0), rec_ctx())
        self.assertEqual(len(o), 1)
        self.assertEqual(o[0]["qty"], 39)  # 1000 // (25*1.001); panel 50 -> 19
        rec = o[0]["enhance_exp"]["records"][0]
        self.assertEqual((rec["control_qty"], rec["treatment_qty"]), (19, 39))
    def test_w1_sizes_off_current_bar(self):
        o = ev("aster_tensor_w1_recovery", rec_view("1wk", 25.0), rec_ctx())
        self.assertEqual(o[0]["qty"], 39)
    def test_current_bar_below_floor_refuses(self):
        self.assertEqual(ev("aster_tensor_h1_recovery", rec_view("1h", 4.0), rec_ctx()), [])
    def test_switch_off_restores_panel_rule_exactly(self):
        off = {"aster_tensor_rec_enh": {"exec_reprice": False}}
        o = ev("aster_tensor_h1_recovery", rec_view("1h", 25.0, off), rec_ctx())
        self.assertEqual(o[0]["qty"], 19)
        o2 = ev("aster_tensor_h1_recovery", rec_view("1h", 4.0, off), rec_ctx())
        self.assertEqual(len(o2), 1)  # pre-change rule ignores the bar

# ------------------------------------------------------------- leaps
class TestLeapsSpreadGate(unittest.TestCase):
    def _view(self, sid, ask, bid, extra=None):
        v = b3.leaps_view(sid)
        contracts, quotes = b3.leaps_chain(ask=ask, bid=bid)
        und = "ACME"
        v["options_chain"] = {und: contracts}
        v["options_quotes"] = quotes
        if extra: v["extra"].update(extra)
        return v
    def test_wide_spread_refused_a_and_b(self):
        v = self._view("aster_tensor_leaps_a", ask=1.80, bid=0.90)  # 0.667
        self.assertEqual(b3.ev("aster_tensor_leaps_a", v), [])
        v = b3.leaps_view("aster_tensor_leaps_b", micro=True)
        contracts, quotes = b3.leaps_chain(
            occ="PENY280616C00001350", und="PENY", strike=1.35,
            ask=0.45, bid=0.15)  # spread/mid = 1.0; debit 45.65 fits B $50
        v["options_chain"] = {"PENY": contracts}
        v["options_quotes"] = quotes
        self.assertEqual(b3.ev("aster_tensor_leaps_b", v), [])
    def test_tight_spread_still_enters(self):
        out = b3.ev("aster_tensor_leaps_a", self._view("aster_tensor_leaps_a", 1.50, 1.40))
        self.assertEqual(len(out), 1)
    def test_switch_off_restores_ask_only_rule(self):
        off = {"aster_leaps_enh": {"spread_gate": False}}
        out = b3.ev("aster_tensor_leaps_a",
                    self._view("aster_tensor_leaps_a", 1.80, 0.90, off))
        self.assertEqual(len(out), 1)

# ---------------------------------------------------------------- xsp
class TestXspEtWindow(unittest.TestCase):
    def test_utc_stamp_inside_et_window_fires_all_four(self):
        for sid in ("aster_xsp_pcs_calm_a", "aster_xsp_pcs_calm_b",
                    "aster_xsp_pcs_graded_a", "aster_xsp_pcs_graded_b"):
            v = b4.xsp_view()
            if sid.startswith("aster_xsp_pcs_graded"):
                # exact batch-4 graded regime fixture (median .35,
                # p75 .45, adjacent digital .40, legs 585/580)
                from datetime import date, timedelta
                hist = ([{"week_end": (date(2025, 10, 3) - timedelta(days=7 * (i + 1))).isoformat(),
                          "value": 0.25} for i in range(15)]
                        + [{"week_end": (date(2025, 10, 3) - timedelta(days=7 * (i + 16))).isoformat(),
                            "value": 0.45} for i in range(15)])
                v = b4.xsp_view()
                v["xsp_state"]["prior_digitals"] = hist
                v["options"] = b4.xsp_chain(adj_lo_mid=6.0, adj_hi_mid=8.0)
                sb, la = (4.9, 0.6) if sid.endswith("_b") else (4.0, 1.5)
                for c in v["options"]:
                    if c["strike"] == 585.0: c["bid"], c["ask"] = sb, sb + 0.2
                    if c["strike"] == 580.0: c["bid"], c["ask"] = la - 0.2, la
            elif sid.endswith("_b"):
                v = b4.xsp_view(short_bid=4.6, long_ask=0.4)
            ctx = b4.xsp_ctx(sid, now="2025-10-06T14:02:00+00:00")  # 10:02 ET
            self.assertEqual(len(ev(sid, v, ctx)), 1, sid)
    def test_utc_stamp_at_1002utc_is_0602et_no_fire(self):
        ctx = b4.xsp_ctx("aster_xsp_pcs_calm_a", now="2025-10-06T10:02:00+00:00")
        self.assertEqual(ev("aster_xsp_pcs_calm_a", b4.xsp_view(), ctx), [])
    def test_switch_off_restores_raw_slice(self):
        v = b4.xsp_view(); v["extra"] = {"aster_xsp_enh": {"et_window": False}}
        ctx = b4.xsp_ctx("aster_xsp_pcs_calm_a", now="2025-10-06T14:02:00+00:00")
        self.assertEqual(ev("aster_xsp_pcs_calm_a", v, ctx), [])
        v2 = b4.xsp_view(); v2["extra"] = {"aster_xsp_enh": {"et_window": False}}
        self.assertEqual(len(ev("aster_xsp_pcs_calm_a", v2,
                                b4.xsp_ctx("aster_xsp_pcs_calm_a"))), 1)  # naive 10:02
    def test_paired_shadow_record(self):
        j = {"records": []}
        v = b4.xsp_view(); v["extra"] = {"edge_exp_journal": j}
        ctx = b4.xsp_ctx("aster_xsp_pcs_calm_a", now="2025-10-06T14:02:00+00:00")
        ev("aster_xsp_pcs_calm_a", v, ctx)
        self.assertEqual(len(j["records"]), 1)
        self.assertTrue(j["records"][0]["treatment_window_open"])
        self.assertFalse(j["records"][0]["control_window_open"])

if __name__ == "__main__":
    unittest.main()

# ------------------------------------------------- g4 reserve (b14)
import test_aster_batch14_blockers as b14
class TestG4ReserveReprice(unittest.TestCase):
    """Reserve sleeves execute >=1 session after the fire (design), so
    the shared ENH-TENSOR14-REPRICE cure binds hardest here: the fire
    price is guaranteed stale at execution."""
    def _v(self, cur):
        pos = [{"symbol": "QQQ", "qty": 10, "avg_price": 100.0}]
        barsm = {"QQQ": b14.bars(100.0), "ABC": b14.bars(cur)}
        return b14.V([b14.fire()], positions=pos, bars=barsm)
    def test_current_above_cap_refuses_entry_and_reserve_sale(self):
        for sid in ("aster_tensor_g4_reserve_all_10",
                    "aster_tensor_g4_reserve_all_25",
                    "aster_tensor_g4_reserve_cool_25"):
            self.assertEqual(b14.ev(sid, self._v(12.0)), [], sid)
    def test_current_within_cap_sizes_off_current(self):
        o = b14.ev("aster_tensor_g4_reserve_all_25", self._v(9.0))
        self.assertEqual([x["symbol"] for x in o], ["QQQ", "ABC"])
        self.assertEqual(o[1]["qty"], 44)  # 400//9, not 400//8=50
        rec = o[1]["enhance_exp"]["records"][0]
        self.assertEqual((rec["control_qty"], rec["treatment_qty"]), (50, 44))
    def test_switch_off_restores_fire_price_rule(self):
        ctx = {"session": "2026-10-23", "now": "2026-10-23T15:00:00",
               "enhance": {"exec_reprice": False}}
        o = b14.ev("aster_tensor_g4_reserve_all_25", self._v(12.0), ctx)
        self.assertEqual(o[-1]["qty"], 50)  # pre-change: fire price 8
