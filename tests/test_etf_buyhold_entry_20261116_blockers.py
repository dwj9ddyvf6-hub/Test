"""ETF-BUYHOLD-ENTRY-20261116 blockers (total audit, Mon 2026-11-16).

Diagnosis (proven from primary code by the escalations lane): the six
aster BUY_HOLD ETF sleeves — aster_etf_qld_buy_hold,
aster_etf_qqq_buy_hold, aster_etf_qqq_qld_buy_hold,
aster_etf_smh_hold_c098, aster_etf_smh_hold_m150,
aster_etf_spy_buy_hold — were not flagged own_book_view in
config/sleeves.json, so they evaluated on the aggregate broker book,
whose sole position is BTC/USD 0.132675707. desk3/aster_etf.evaluate
returns [] for BUY_HOLD whenever positions is non-empty, and
_flat_top is False so the CR-1 catch-up never engages: the six read a
foreign BTC position as their completed allocation and never entered
live (zero dispatcher rows across all five generations, zero fills,
no weight_lag_pending.json in their state dirs).

Cure (the estate's own CR-S3 shape, CLEAR-THE-BOARD-20261114):
own_book_view: true on exactly these six config rows, so
desk3/cycle.own_book_positions serves each sleeve its
journal-derived book — empty for all six, which is the truth.
No exit is added: BUY_HOLD is no-exit-by-design (source-unanimous).

Fixture: the recorded warm snapshot (state/warm_bars.json fetched
2026-11-16T16:38:20Z; last 1Day closes, 2026-11-13): SPY 754.37,
QQQ 679.89, QLD 79.30, SMH 486.75. At $10K slices the initial
entries are SPY buy 13; QQQ buy 14; QLD buy 126; QQQ 7 + QLD 63;
SMH 20 (gross 0.98); SMH 30 (gross 1.5) — the quantities the
escalations lane proved on the live snapshot with true empty books.
"""
import json
import os
import shutil
import sys
import tempfile
import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# aster_etf_spy_buy_hold's spec registers into desk3.aster_etf.SPECS
# when desk3.aster_batch11 is imported — exactly what loading its
# adapters3 module does on the live runner path.
import desk3.aster_batch11  # noqa: F401,E402

ET = ZoneInfo("America/New_York")
ROOT = os.path.join(os.path.dirname(__file__), "..")

SIX = ["aster_etf_qld_buy_hold", "aster_etf_qqq_buy_hold",
       "aster_etf_qqq_qld_buy_hold", "aster_etf_smh_hold_c098",
       "aster_etf_smh_hold_m150", "aster_etf_spy_buy_hold"]

EXPECTED = {
    "aster_etf_spy_buy_hold": [("SPY", 13)],
    "aster_etf_qqq_buy_hold": [("QQQ", 14)],
    "aster_etf_qld_buy_hold": [("QLD", 126)],
    "aster_etf_qqq_qld_buy_hold": [("QQQ", 7), ("QLD", 63)],
    "aster_etf_smh_hold_c098": [("SMH", 20)],
    "aster_etf_smh_hold_m150": [("SMH", 30)],
}

CLOSES = {"SPY": 754.37, "QQQ": 679.89, "QLD": 79.30, "SMH": 486.75}

AGGREGATE = [{"symbol": "BTC/USD", "qty": 0.132675707,
              "avg_price": 0.0}]

# Every own_book_view flag that existed before this cure
# (CR-S3 leader + five overnight baskets + the ENJ 22).
PRE_EXISTING_FLAGGED = {
    "aster_etf_leader1_c098",
    "overnight_focus29", "overnight_energy8", "overnight_basket8",
    "overnight_semis12", "overnight_focus29_ex_rklb",
    "aster_abs_enj_4h", "aster_enj_nfs_fixed96_vol",
    "aster_enj_nfs_lost_full", "aster_enj_nfs_lost_vol",
    "aster_enj_nfs_norm_full", "aster_enj_nfs_norm_vol",
    "aster_enj_nfs_normfail_full", "aster_enj_nfs_normfail_vol",
    "aster_pub_enj_iu_body",
    "aster_r19_enjusdt_absorption_base_fixed16_fullcash",
    "aster_r19_enjusdt_absorption_base_fixed16_volume1pct",
    "aster_r19_enjusdt_absorption_negative_funding_fixed16_fullcash",
    "aster_r19_enjusdt_absorption_negative_funding_fixed16_volume1pct",
    "aster_r19_enjusdt_absorption_nonnegative_funding_fixed16_fullcash",
    "aster_r19_enjusdt_absorption_nonnegative_funding_fixed16_volume1pct",
    "aster_r19_enjusdt_breakout_base_fixed16_fullcash",
    "aster_r19_enjusdt_breakout_base_fixed16_volume1pct",
    "aster_r19_enjusdt_negative_funding_squeeze_fixed16_fullcash",
    "aster_r19_enjusdt_negative_funding_squeeze_fixed16_volume1pct",
    "aster_r19_enjusdt_negative_funding_squeeze_fixed96_fullcash",
    "free_kraken_enj_spot", "fwd_alpaca_enj_iu_body",
}


def _rows():
    cfg = json.load(open(os.path.join(ROOT, "config", "sleeves.json")))
    return cfg["sleeves"]


def _served_positions(rows, journal_path):
    """The cycle seam, exactly as the runner serves it: flagged
    sleeves get their journal-derived book (empty journal => []),
    unflagged sleeves get the aggregate broker book."""
    from desk3.cycle import own_book_positions
    sleeves = {r["id"]: {"own_book_view": bool(r.get("own_book_view"))}
               for r in rows}
    own = own_book_positions(sleeves, journal_path)
    return {r["id"]: own.get(r["id"], AGGREGATE) for r in rows}


def _view(now, positions):
    return {"now": now,
            "bars": {f"{s}|1Day": [{"c": px}]
                     for s, px in CLOSES.items()},
            "positions": positions}


def _ctx(state_dir):
    return {"state_dir": state_dir,
            "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0},
            "extra": {"account_value": 10000.0}}


class TestBuyHoldEntryCure(unittest.TestCase):
    def _root(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        return tmp

    def _drive(self, sid, served):
        import desk3.aster_etf as ae
        ae._PENDING_TARGETS.pop(sid, None)
        sd = os.path.join(self._root(), sid)
        t1 = datetime(2026, 11, 16, 9, 35, tzinfo=ET)
        t2 = datetime(2026, 11, 16, 9, 36, tzinfo=ET)
        out1 = ae.evaluate(sid, _view(t1, served), _ctx(sd))
        out2 = ae.evaluate(sid, _view(t2, served), _ctx(sd))
        return out1, out2, sd

    def test_aggregate_book_blocks_all_six(self):
        # The disease, pinned: served the aggregate book (the
        # pre-cure serving for an unflagged sleeve), every one of
        # the six emits nothing on either evaluation.
        for sid in SIX:
            out1, out2, _ = self._drive(sid, AGGREGATE)
            self.assertEqual(out1, [], sid)
            self.assertEqual(out2, [], sid)

    def test_own_book_serving_emits_initial_entries(self):
        rows = _rows()
        jpath = os.path.join(self._root(), "dispatcher.jsonl")
        open(jpath, "w").close()  # no fills: derived books are empty
        served = _served_positions(rows, jpath)
        for sid in SIX:
            self.assertEqual(served[sid], [],
                             f"{sid} was not served its empty own book")
            out1, out2, sd = self._drive(sid, served[sid])
            self.assertEqual(out1, [], sid)  # weight lag: 1st stores
            got = sorted((o["symbol"], o["qty"]) for o in out2)
            self.assertEqual(got, sorted(EXPECTED[sid]), sid)
            for o in out2:
                self.assertEqual(o["kind"], "entry", sid)
                self.assertEqual(o["side"], "buy", sid)
            self.assertTrue(os.path.exists(
                os.path.join(sd, "weight_lag_pending.json")), sid)

    def test_no_exit_after_allocation(self):
        # BUY_HOLD is no-exit-by-design: once the own book holds the
        # allocation, evaluation emits nothing (no exit, no trim).
        import desk3.aster_etf as ae
        for sid in SIX:
            ae._PENDING_TARGETS.pop(sid, None)
            held = [{"symbol": s, "qty": float(q),
                     "avg_price": CLOSES[s]} for s, q in EXPECTED[sid]]
            sd = os.path.join(self._root(), sid)
            t = datetime(2026, 11, 16, 9, 35, tzinfo=ET)
            self.assertEqual(
                ae.evaluate(sid, _view(t, held), _ctx(sd)), [], sid)


class TestConfigPin(unittest.TestCase):
    def test_exactly_the_six_newly_flagged(self):
        rows = _rows()
        # T474U-CRYPTO-PORT-20261116 (amendment, dated estate form):
        # the roster grew 387 -> 396 when the 9 t474u crypto sleeves
        # were rostered later the same day; the pin's claim is about
        # THIS cure's six rows, so the count follows the roster.
        # TOTAL-AUDIT-PIN-REBASE-20261116 (5): the roster then grew
        # 396 -> 398 (SEGMENT-CONSTRUCTION), 398 -> 399
        # (CONV57-G4-VARIATION) and 399 -> 400 (CONV123-REVIVAL);
        # the count follows the roster to 400.
        self.assertEqual(len(rows), 400)
        by_id = {r["id"]: r for r in rows}
        for sid in SIX:
            self.assertIs(by_id[sid].get("own_book_view"), True, sid)
        flagged = {r["id"] for r in rows if r.get("own_book_view")}
        # EXIT-STORM-CURE-20261116 (amendment, dated estate form):
        # beatendown and confluence were flagged later the same day
        # by the phantom-exit storm cure; the pin's claim is that
        # THIS cure added exactly the six and no other row changed
        # at its landing, so the storm pair is admitted by name.
        storm2 = {"beatendown", "confluence"}
        # T474U-CRYPTO-PORT-20261116 (same dated form): the three
        # t474u ENJ twins carry own_book_view as members of the
        # kraken_paper class; admitted by name.
        t474u_enj3 = {"crypto_bratr_enj", "crypto_mfi_enj",
                      "crypto_stdev_enj"}
        # SEGMENT-CONSTRUCTION-20261116 and CONV123-REVIVAL-
        # 20261116 (same dated form, carried by
        # TOTAL-AUDIT-PIN-REBASE-20261116 (5)): the two segment
        # sleeves and revival_basket carry own_book_view from
        # their own landings; admitted by name.
        segment2 = {"ls9_midday_short", "b3_midday_fade_var"}
        revival1 = {"revival_basket"}
        # OBV-CLASS-20261116 (amendment, dated estate form): the
        # full sleeve audit's Lane F class sweep flagged the 217
        # VULNERABLE sleeves the same day; admitted by name as a
        # set. This pin's claim (this cure added exactly the six)
        # is unchanged.
        obv217 = {"1d",
            "1d_vardh",
            "1d_vardt",
            "1d_varhx4",
            "1d_varjx2",
            "1dc",
            "1h",
            "1w",
            "1w_vargd",
            "1wa",
            "1wa_vargd",
            "aster_core_rsi2_long",
            "aster_core_rsi2_vertical",
            "aster_etf_core25_c098",
            "aster_etf_core25_m150",
            "aster_etf_drift1_c098",
            "aster_etf_drift1_m150",
            "aster_etf_exsmh1_c098",
            "aster_etf_exsmh1_m150",
            "aster_etf_interval1_c098",
            "aster_etf_interval1_m150",
            "aster_etf_interval_core25_c098",
            "aster_etf_interval_core25_m150",
            "aster_etf_interval_drift1_c098",
            "aster_etf_interval_drift1_m150",
            "aster_etf_leader1_m150",
            "aster_etf_qld_monthly",
            "aster_etf_qqq_monthly_c098",
            "aster_etf_qqq_monthly_m150",
            "aster_etf_qqq_qld_monthly",
            "aster_etf_spy_monthly_c098",
            "aster_etf_spy_monthly_m150",
            "aster_link_nfs_norm_vol",
            "aster_native_btc_eth_sma200",
            "aster_native_eth_sma200",
            "aster_pub_rsi2_ada",
            "aster_r19_adausdt_negative_funding_squeeze_normalization_failure_fullcash",
            "aster_r19_adausdt_negative_funding_squeeze_normalization_failure_volume1pct",
            "aster_r19_adausdt_negative_funding_squeeze_normalization_fullcash",
            "aster_r19_adausdt_negative_funding_squeeze_normalization_volume1pct",
            "aster_rsi2_1d",
            "aster_saty_research",
            "aster_squeeze_1d",
            "aster_tensor_c1_reserve_all_25",
            "aster_tensor_c1_reserve_cool_25",
            "aster_tensor_c1_reserve_hot_25",
            "aster_tensor_g4_reserve_all_10",
            "aster_tensor_g4_reserve_all_25",
            "aster_tensor_g4_reserve_cool_25",
            "aster_trader_donchian55",
            "aster_trader_turtle2010",
            "aurelia_gold",
            "aurelia_ndx",
            "bta_onebar_rth",
            "capitulation",
            "capitulation_options",
            "daily_cyan_gbm",
            "donchian",
            "donchian_crypto",
            "earnings_buyback",
            "em_1587",
            "ema_vwap",
            "ema_vwap_options",
            "fear_premium",
            "free_kraken_ada_basis",
            "free_kraken_ada_basis_varspot",
            "free_kraken_link_basis",
            "free_kraken_link_basis_varspot",
            "free_opt_own_iv",
            "free_opt_pair",
            "free_opt_parity",
            "free_opt_release",
            "free_opt_tail",
            "free_opt_wheel",
            "fwd_alpaca_ada_rsi2",
            "fwd_alpaca_link_ai_volume",
            "fwd_coinbase_sma200",
            "investandbefree_dmac",
            "investandbefree_dmac_dailyonly",
            "investandbefree_dmac_deep",
            "investandbefree_dmac_intraday",
            "investandbefree_dmac_premacd",
            "mk_zerodte_spx",
            "momentum",
            "momentum_rotation",
            "morning_dip",
            "phase_daily",
            "phoenix",
            "po10_qqq",
            "przm_fade_edges",
            "przm_zero",
            "qullamaggie",
            "raschke_pf3",
            "raschke_rre",
            "red_day_reversal",
            "rsi_meanrev",
            "rsi_meanrev_options",
            "rule_1d_cyan_smallcap",
            "rule_1d_green_tom",
            "rule_1h_cyan_raw",
            "rule_1w_cyan_mom_adx",
            "rule_1w_swing_beta_wt",
            "s_1dg",
            "s_1dg_vardh",
            "s_1dgp5",
            "s_1wc_micro",
            "s_1wc_ml",
            "s_1wc_ml_vards",
            "s_1wg_small",
            "s_1wlab",
            "s_1wsw",
            "s_1wsw_stress",
            "s_cl_qm_small",
            "s_cl_vmr_qqq",
            "s_mn_d_green_band",
            "s_mn_faber",
            "s_mn_hedge",
            "s_mn_hourly",
            "s_mn_hourly_1w",
            "s_mn_hourly_1w_varn1",
            "s_mn_kronos",
            "s_mn_macd",
            "s_mn_moonshot",
            "s_mn_nostop",
            "s_mn_opt_pairs",
            "s_mn_opt_reversal",
            "s_mn_opt_turtle",
            "s_mn_pairs",
            "s_mn_reversal",
            "s_mn_vwap",
            "s_mn_w_cyan_breadth",
            "s_mn_w_cyan_vix",
            "s_mn_w_green_smh",
            "s_moonshot",
            "s_q07w_c52_ml_mom6_tierA_wlow",
            "s_q07w_c52_ml_mom6_tierA_wlow_vargd",
            "s_q07w_c52_ml_mom6_wspike2",
            "s_q07w_c52_ml_mom6_wspike2_vargd",
            "s_q07w_c52_ml_tierA_wcov",
            "s_q07w_c52_ml_tierA_wcov_vargd",
            "s_q07w_c52_ml_tierA_wlow",
            "s_q07w_c52_ml_tierA_wlow_vargd",
            "s_q07w_c52_sm_cheap5_ins2_mom6",
            "s_q07w_c52_sm_cheap5_wcov",
            "s_q07w_c52_sm_deep70_wcov",
            "s_q07w_c52_sm_tierA_wcov",
            "s_q07w_c78_ml_deep70_tierA_wlow",
            "s_q07w_c78_ml_deep70_tierA_wlow_vargd",
            "s_q07w_c78_ml_mom6_tierA_wlow",
            "s_q07w_c78_ml_mom6_tierA_wlow_vargd",
            "s_q07w_c78_ml_tierA_wcov",
            "s_q07w_c78_ml_tierA_wcov_vargd",
            "s_q07w_c78_ml_tierA_wlow",
            "s_q07w_c78_ml_tierA_wlow_vargd",
            "s_q07w_c78_sm_deep70_ins2_vix20",
            "s_q07w_c78_sm_deep70_wcov",
            "s_q07w_c78_sm_ins2_mom6_vix20",
            "s_q07w_c78_sm_tierA_wcov",
            "s_q07w_g52_ml_ats_z1_mom6_wlow",
            "s_q07w_g52_ml_ats_z1_mom6_wlow_vargd",
            "s_q07w_g52_ml_ins2_wlow",
            "s_q07w_g52_ml_ins2_wlow_vargd",
            "s_q07w_g52_ml_tierA_wcov",
            "s_q07w_g52_ml_tierA_wcov_vargd",
            "s_q07w_g52_sm_deep70_ins2_vix20",
            "s_q07w_g52_sm_deep70_wcov",
            "s_q07w_g52_sm_ins2_wcov",
            "s_q07w_g52_sm_tierA_wcov",
            "s_q07w_g78_mi_cheap5_deep70_ins2",
            "s_q07w_g78_ml_tierA_wcov",
            "s_q07w_g78_ml_tierA_wcov_vargd",
            "s_q07w_g78_sm_cheap5_ins2",
            "s_q07w_g78_sm_deep70_ins2",
            "s_q07w_g78_sm_deep70_wcov",
            "s_q07w_g78_sm_tierA_wcov",
            "s_q07w_s52_ml_deep70_ins2_vix20",
            "s_q07w_s52_ml_deep70_ins2_vix20_vargd",
            "s_q07w_s52_ml_deep70_vix20_wlow",
            "s_q07w_s52_ml_deep70_wlow",
            "s_q07w_s52_ml_ins2_mom6_vix20",
            "s_q07w_s52_ml_ins2_mom6_wlow",
            "s_q07w_s52_sm_cheap5_deep70_ins2",
            "s_q07w_s52_sm_cheap5_ins2_vix20",
            "s_q07w_s52_sm_cheap5_wcov",
            "s_q07w_s52_sm_deep70_wcov",
            "s_q07w_s78_mi_ats_z1_cheap5",
            "s_q07w_s78_mi_ats_z1_mom6",
            "s_q07w_s78_mi_cheap5_ins2_mom6",
            "s_q07w_s78_ml_deep70_glow_ins2",
            "s_q07w_s78_ml_deep70_ins2_vix20",
            "s_q07w_s78_ml_deep70_ins2_vix20_vargd",
            "s_q07w_s78_ml_deep70_mom6_wlow",
            "s_q07w_s78_ml_deep70_wcov",
            "s_q07w_s78_sm_cheap5_ins2_vix20",
            "s_q07w_s78_sm_cheap5_wcov",
            "s_q07w_s78_sm_deep70_ins2",
            "s_q07w_s78_sm_deep70_wcov",
            "s_rules_1d",
            "s_rules_1d_vardh",
            "s_rules_1d_varhx4",
            "s_rules_1w",
            "s_rules_1w_varhx2",
            "saty_day",
            "saty_gpt_v02",
            "saty_gpt_v03",
            "saty_magnum",
            "saty_sol",
            "saty_sol_0dte",
            "shen_fade",
            "snapback",
            "soxl_pm_breakout",
            "spx_premium",
            "teddy_orb_spy",
            "tensor_red_dip",
            "tensor_swing",
            "ts_momentum_decile",
            "vix_hedge"}
        # OBV-CLASS-20261116 landing recheck (same dated form):
        # aster_r19_tensor_g4_hot_reserve_25 admitted by name
        # (batch15 G4 reserve funding sale, no own-book anchor).
        recheck1 = {"aster_r19_tensor_g4_hot_reserve_25"}
        # OBV-DRIVE-20261116 (2026-11-16): the 12 drive-proven
        # adopters admitted by name, same dated form.
        drive12 = {"grok_sr_spy", "trullas_divergence",
                   "trullas_v01", "trullas_v02", "trullas_v03",
                   "trullas_v04", "trullas_v05", "trullas_v06",
                   "trullas_v07", "trullas_v08", "trullas_v09",
                   "trullas_v10"}
        self.assertEqual(flagged,
                         PRE_EXISTING_FLAGGED | set(SIX) | storm2
                         | t474u_enj3 | segment2 | revival1 | obv217
                         | recheck1 | drive12)


if __name__ == "__main__":
    unittest.main()
