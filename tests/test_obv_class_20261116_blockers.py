"""Regression blockers for OBV-CLASS-20261116 — the full sleeve
audit's Lane F own_book_view class sweep (Mon 2026-11-16).

Lane F classified all 358 unflagged roster sleeves by whether
their exit/manage paths can fire on a position record an
aggregate broker row actually carries (symbol / qty / avg_price,
OCC symbol form): VULNERABLE 217, SAFE-BY-CONSTRUCTION 115,
AMBIGUOUS 26. The index case is shen_fade (Lane B Job 1): served
the aggregate book, a plain SPY share position held by other
sleeves is adopted as its own 0DTE option position; the record
carries no occ, so _manage's flat ladder builds
Intent("exit", None) and core/sleeve.py raises
ValueError("intent needs a symbol") — health status error on
2026-11-16 at 14:34Z and 18:18Z, proven on the retained snapshot.

Cure (this landing): the fleet's established CR-S3 shape —
own_book_view: true on exactly the 217 VULNERABLE config rows.
No strategy file is touched (much of the class is byte-pinned
ports); the cycle serves flagged sleeves their own
journal-derived book via own_book_positions and the worker's
positions_override, so the aggregate book is never served to
them again once the runner adopts the config.

Pinned here:
- the 217 carry the flag, plus one name moved from
  SAFE-BY-CONSTRUCTION to VULNERABLE on the coordinator's
  landing recheck (aster_r19_tensor_g4_hot_reserve_25:
  desk3/aster_batch15.py _eval_g4's reserve funding sale reads
  pos_by_sym["QQQ"] from all served positions with no own-book
  anchor — the batch13/14 shape Lane F exempted it from on a
  condition the code read does not meet); the flagged total at
  this landing was 260 (42 prior + 217 + 1). The sweep's 26
  AMBIGUOUS names were then decided by the completion drive
  (OBV-DRIVE-20261116, same day): 12 proven adopters flagged
  (total 272), 14 drive-negative and unflagged, both sets
  pinned below by name;
- the shen_fade disease, driven through the real adapter: the
  aggregate SPY share row served raw raises
  ValueError("intent needs a symbol") at the flat branch
  (control — the pinned strategy is unchanged, so this holds
  before and after; it proves the drive exercises the defect);
- the cured serving path (config row -> own_book_positions ->
  worker _view_for_task -> adapters3.shen_fade.evaluate): the
  same aggregate snapshot reaches the sleeve as its own empty
  book and evaluate returns without error;
- the signal is preserved: with the sleeve's own OCC fill in
  the journal, the cured serving path delivers that OCC position
  and the sleeve emits its 11:15 flat exit intent carrying the
  OCC symbol;
- saty_sol's byte pin is untouched.
"""
import hashlib
import importlib
import json
import os
import pathlib
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
ROOT = pathlib.Path(__file__).resolve().parents[1]
SATY_SOL_PIN = \
    "36e306c6294c385a5e9e96a89f8f4cd2753067597c95efb1fea416cc08962bdc"

OBV217 = ["1d", "1d_vardh", "1d_vardt", "1d_varhx4", "1d_varjx2",
          "1dc", "1h", "1w", "1w_vargd", "1wa", "1wa_vargd",
          "aster_core_rsi2_long", "aster_core_rsi2_vertical",
          "aster_etf_core25_c098", "aster_etf_core25_m150",
          "aster_etf_drift1_c098", "aster_etf_drift1_m150",
          "aster_etf_exsmh1_c098", "aster_etf_exsmh1_m150",
          "aster_etf_interval1_c098", "aster_etf_interval1_m150",
          "aster_etf_interval_core25_c098",
          "aster_etf_interval_core25_m150",
          "aster_etf_interval_drift1_c098",
          "aster_etf_interval_drift1_m150", "aster_etf_leader1_m150",
          "aster_etf_qld_monthly", "aster_etf_qqq_monthly_c098",
          "aster_etf_qqq_monthly_m150", "aster_etf_qqq_qld_monthly",
          "aster_etf_spy_monthly_c098", "aster_etf_spy_monthly_m150",
          "aster_link_nfs_norm_vol", "aster_native_btc_eth_sma200",
          "aster_native_eth_sma200", "aster_pub_rsi2_ada",
          "aster_r19_adausdt_negative_funding_squeeze_normalization_failure_fullcash",
          "aster_r19_adausdt_negative_funding_squeeze_normalization_failure_volume1pct",
          "aster_r19_adausdt_negative_funding_squeeze_normalization_fullcash",
          "aster_r19_adausdt_negative_funding_squeeze_normalization_volume1pct",
          "aster_rsi2_1d", "aster_saty_research", "aster_squeeze_1d",
          "aster_tensor_c1_reserve_all_25",
          "aster_tensor_c1_reserve_cool_25",
          "aster_tensor_c1_reserve_hot_25",
          "aster_tensor_g4_reserve_all_10",
          "aster_tensor_g4_reserve_all_25",
          "aster_tensor_g4_reserve_cool_25",
          "aster_trader_donchian55", "aster_trader_turtle2010",
          "aurelia_gold", "aurelia_ndx", "bta_onebar_rth",
          "capitulation", "capitulation_options", "daily_cyan_gbm",
          "donchian", "donchian_crypto", "earnings_buyback",
          "em_1587", "ema_vwap", "ema_vwap_options", "fear_premium",
          "free_kraken_ada_basis", "free_kraken_ada_basis_varspot",
          "free_kraken_link_basis", "free_kraken_link_basis_varspot",
          "free_opt_own_iv", "free_opt_pair", "free_opt_parity",
          "free_opt_release", "free_opt_tail", "free_opt_wheel",
          "fwd_alpaca_ada_rsi2", "fwd_alpaca_link_ai_volume",
          "fwd_coinbase_sma200", "investandbefree_dmac",
          "investandbefree_dmac_dailyonly",
          "investandbefree_dmac_deep",
          "investandbefree_dmac_intraday",
          "investandbefree_dmac_premacd", "mk_zerodte_spx",
          "momentum", "momentum_rotation", "morning_dip",
          "phase_daily", "phoenix", "po10_qqq", "przm_fade_edges",
          "przm_zero", "qullamaggie", "raschke_pf3", "raschke_rre",
          "red_day_reversal", "rsi_meanrev", "rsi_meanrev_options",
          "rule_1d_cyan_smallcap", "rule_1d_green_tom",
          "rule_1h_cyan_raw", "rule_1w_cyan_mom_adx",
          "rule_1w_swing_beta_wt", "s_1dg", "s_1dg_vardh", "s_1dgp5",
          "s_1wc_micro", "s_1wc_ml", "s_1wc_ml_vards", "s_1wg_small",
          "s_1wlab", "s_1wsw", "s_1wsw_stress", "s_cl_qm_small",
          "s_cl_vmr_qqq", "s_mn_d_green_band", "s_mn_faber",
          "s_mn_hedge", "s_mn_hourly", "s_mn_hourly_1w",
          "s_mn_hourly_1w_varn1", "s_mn_kronos", "s_mn_macd",
          "s_mn_moonshot", "s_mn_nostop", "s_mn_opt_pairs",
          "s_mn_opt_reversal", "s_mn_opt_turtle", "s_mn_pairs",
          "s_mn_reversal", "s_mn_vwap", "s_mn_w_cyan_breadth",
          "s_mn_w_cyan_vix", "s_mn_w_green_smh", "s_moonshot",
          "s_q07w_c52_ml_mom6_tierA_wlow",
          "s_q07w_c52_ml_mom6_tierA_wlow_vargd",
          "s_q07w_c52_ml_mom6_wspike2",
          "s_q07w_c52_ml_mom6_wspike2_vargd",
          "s_q07w_c52_ml_tierA_wcov",
          "s_q07w_c52_ml_tierA_wcov_vargd",
          "s_q07w_c52_ml_tierA_wlow",
          "s_q07w_c52_ml_tierA_wlow_vargd",
          "s_q07w_c52_sm_cheap5_ins2_mom6",
          "s_q07w_c52_sm_cheap5_wcov", "s_q07w_c52_sm_deep70_wcov",
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
          "s_q07w_c78_sm_ins2_mom6_vix20", "s_q07w_c78_sm_tierA_wcov",
          "s_q07w_g52_ml_ats_z1_mom6_wlow",
          "s_q07w_g52_ml_ats_z1_mom6_wlow_vargd",
          "s_q07w_g52_ml_ins2_wlow", "s_q07w_g52_ml_ins2_wlow_vargd",
          "s_q07w_g52_ml_tierA_wcov",
          "s_q07w_g52_ml_tierA_wcov_vargd",
          "s_q07w_g52_sm_deep70_ins2_vix20",
          "s_q07w_g52_sm_deep70_wcov", "s_q07w_g52_sm_ins2_wcov",
          "s_q07w_g52_sm_tierA_wcov",
          "s_q07w_g78_mi_cheap5_deep70_ins2",
          "s_q07w_g78_ml_tierA_wcov",
          "s_q07w_g78_ml_tierA_wcov_vargd",
          "s_q07w_g78_sm_cheap5_ins2", "s_q07w_g78_sm_deep70_ins2",
          "s_q07w_g78_sm_deep70_wcov", "s_q07w_g78_sm_tierA_wcov",
          "s_q07w_s52_ml_deep70_ins2_vix20",
          "s_q07w_s52_ml_deep70_ins2_vix20_vargd",
          "s_q07w_s52_ml_deep70_vix20_wlow",
          "s_q07w_s52_ml_deep70_wlow",
          "s_q07w_s52_ml_ins2_mom6_vix20",
          "s_q07w_s52_ml_ins2_mom6_wlow",
          "s_q07w_s52_sm_cheap5_deep70_ins2",
          "s_q07w_s52_sm_cheap5_ins2_vix20",
          "s_q07w_s52_sm_cheap5_wcov", "s_q07w_s52_sm_deep70_wcov",
          "s_q07w_s78_mi_ats_z1_cheap5", "s_q07w_s78_mi_ats_z1_mom6",
          "s_q07w_s78_mi_cheap5_ins2_mom6",
          "s_q07w_s78_ml_deep70_glow_ins2",
          "s_q07w_s78_ml_deep70_ins2_vix20",
          "s_q07w_s78_ml_deep70_ins2_vix20_vargd",
          "s_q07w_s78_ml_deep70_mom6_wlow",
          "s_q07w_s78_ml_deep70_wcov",
          "s_q07w_s78_sm_cheap5_ins2_vix20",
          "s_q07w_s78_sm_cheap5_wcov", "s_q07w_s78_sm_deep70_ins2",
          "s_q07w_s78_sm_deep70_wcov", "s_rules_1d",
          "s_rules_1d_vardh", "s_rules_1d_varhx4", "s_rules_1w",
          "s_rules_1w_varhx2", "saty_day", "saty_gpt_v02",
          "saty_gpt_v03", "saty_magnum", "saty_sol", "saty_sol_0dte",
          "shen_fade", "snapback", "soxl_pm_breakout", "spx_premium",
          "teddy_orb_spy", "tensor_red_dip", "tensor_swing",
          "ts_momentum_decile", "vix_hedge"]

RECHECK1 = ["aster_r19_tensor_g4_hot_reserve_25"]

# The completion drive (ambig_drive.py over the Lane D snapshot,
# positions replaced by the standing trigger set; results in the
# audit dir's ambig-drive-results.jsonl) decided Lane F's 26:
# DRIVE12 ADOPTED a foreign row (an exit intent against the full
# foreign quantity) and are flagged by OBV-DRIVE-20261116; the
# remaining 14 returned no exit-side intent against any trigger
# row and stay unflagged, drive-negative.
DRIVE12 = ["grok_sr_spy", "trullas_divergence", "trullas_v01",
           "trullas_v02", "trullas_v03", "trullas_v04",
           "trullas_v05", "trullas_v06", "trullas_v07",
           "trullas_v08", "trullas_v09", "trullas_v10"]

AMBIGUOUS26 = ["aster_pub_link_ai_volume", "bb_rsi_divergence",
               "bilbo_options", "free_kraken_ada_breakdown_varspot",
               "free_kraken_ada_crowded_varspot",
               "free_kraken_link_breakdown_varspot",
               "free_kraken_link_crowded_varspot", "gate_1h",
               "iron_condor", "leader_d", "leader_sc",
               "leaps_momentum", "legends_ema", "qullamaggie_paper"]

AGGREGATE_SPY = {"symbol": "SPY", "qty": 13, "avg_price": 741.903077}
PUT_OCC = "SPY261021P00582000"
SESSION_DAY = datetime(2026, 10, 21, tzinfo=ET)
PRIOR_DAY = datetime(2026, 10, 20, tzinfo=ET)


def _config_rows():
    cfg = json.loads((ROOT / "config" / "sleeves.json").read_text())
    rows = cfg["sleeves"] if isinstance(cfg, dict) else cfg
    return {r["id"]: r for r in rows}


def _bar(t, o, h, l, c):
    return {"t": t.astimezone(timezone.utc).isoformat(),
            "o": o, "h": h, "l": l, "c": c, "v": 1000.0}


def _fixture_bars():
    """Prior session RTH (flat 580, PDH/PDL prints) + today's
    premarket and RTH up to 13:17 ET, flat — enough for the plan
    to file; no level is touched, no RSI extreme occurs."""
    bars = []
    t = PRIOR_DAY.replace(hour=9, minute=30)
    for i in range(390):
        h = l = 580.0
        if i == 100:
            h = 582.40
        if i == 200:
            l = 577.60
        bars.append(_bar(t, 580.0, h, l, 580.0))
        t += timedelta(minutes=1)
    t = SESSION_DAY.replace(hour=8, minute=0)
    for _ in range(90):
        bars.append(_bar(t, 580.0, 580.0, 580.0, 580.0))
        t += timedelta(minutes=1)
    t = SESSION_DAY.replace(hour=9, minute=30)
    for _ in range(228):
        bars.append(_bar(t, 580.0, 580.0, 580.0, 580.0))
        t += timedelta(minutes=1)
    return bars


def _snapshot(positions):
    now = SESSION_DAY.replace(hour=13, minute=18)
    return {"now": now.astimezone(timezone.utc).isoformat(),
            "bars": {"SPY|1Min": _fixture_bars()},
            "options": {"SPY": {"chains": [], "quotes": {}}},
            "positions": positions, "session_fills": [],
            "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0},
            "params": {}, "extra": {}}


def _serve_through_seam(sid, data, djournal_path):
    """The cycle+worker serving path, driven from the config row
    (the exit-storm blocker's shape): a flagged sleeve's task
    carries positions_override = its own journal-derived book;
    an unflagged sleeve's task carries none and the worker serves
    the snapshot itself."""
    from desk3.cycle import own_book_positions
    from desk3.worker import _view_for_task
    row = _config_rows()[sid]
    task = {}
    if row.get("own_book_view"):
        own = own_book_positions({sid: {"own_book_view": True}},
                                 djournal_path)
        task["positions_override"] = own.get(sid, [])
    return _view_for_task(data, task)


def _evaluate_shen(view, state_dir):
    mod = importlib.import_module("adapters3.shen_fade")
    return mod.evaluate(view, {"sleeve_id": "shen_fade",
                               "state_dir": state_dir})


def _write_journal(root, rows):
    path = os.path.join(root, "dispatcher.jsonl")
    with open(path, "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    return path


class TestObvConfigSet(unittest.TestCase):
    def test_all_217_vulnerable_rows_flagged(self):
        rows = _config_rows()
        self.assertEqual(len(OBV217), 217)
        for sid in OBV217:
            self.assertIs(rows[sid].get("own_book_view"), True, sid)

    def test_flagged_total_is_260(self):
        # Renamed in substance by OBV-DRIVE-20261116: the total is
        # 272 (260 + the 12 drive-proven adopters).
        rows = _config_rows()
        flagged = [sid for sid, r in rows.items()
                   if r.get("own_book_view")]
        self.assertEqual(len(flagged), 272)

    def test_drive_proven_12_flagged(self):
        rows = _config_rows()
        for sid in DRIVE12:
            self.assertIs(rows[sid].get("own_book_view"), True,
                          sid)

    def test_recheck1_flagged(self):
        rows = _config_rows()
        for sid in RECHECK1:
            self.assertIs(rows[sid].get("own_book_view"), True,
                          sid)

    def test_drive_negative_14_not_flagged(self):
        rows = _config_rows()
        for sid in AMBIGUOUS26:
            self.assertIsNot(rows[sid].get("own_book_view"), True,
                             sid)

    def test_saty_sol_pin_untouched(self):
        digest = hashlib.sha256(
            (ROOT / "sleeves" / "saty_sol.py").read_bytes()
        ).hexdigest()
        self.assertEqual(digest, SATY_SOL_PIN)


class TestShenFadeServing(unittest.TestCase):
    def test_disease_control_aggregate_served_raw_raises(self):
        """Control: the pinned strategy, handed the aggregate SPY
        share row directly, still raises — the defect lives in
        the serving, and this drive exercises it."""
        tmp = tempfile.mkdtemp()
        view = _snapshot([dict(AGGREGATE_SPY)])
        with self.assertRaises(ValueError) as cm:
            _evaluate_shen(view, tmp)
        self.assertIn("intent needs a symbol", str(cm.exception))

    def test_cured_seam_serves_own_empty_book(self):
        tmp = tempfile.mkdtemp()
        jpath = _write_journal(tmp, [])
        data = _snapshot([dict(AGGREGATE_SPY)])
        view = _serve_through_seam("shen_fade", data, jpath)
        self.assertEqual(view["positions"], [])
        out = _evaluate_shen(view, tmp)
        self.assertEqual(out, [])

    def test_cured_seam_preserves_own_occ_position(self):
        tmp = tempfile.mkdtemp()
        fill = {"event": "fill", "sleeve": "shen_fade",
                "symbol": PUT_OCC, "side": "buy",
                "position_intent": "buy_to_open", "qty": 1,
                "price": 2.05, "intent_id": "shen-occ-1",
                "ts": "2026-10-21T13:31:00Z"}
        jpath = _write_journal(tmp, [fill])
        data = _snapshot([dict(AGGREGATE_SPY)])
        view = _serve_through_seam("shen_fade", data, jpath)
        self.assertEqual(len(view["positions"]), 1)
        self.assertEqual(view["positions"][0]["symbol"], PUT_OCC)
        out = _evaluate_shen(view, tmp)
        exits = [i for i in out if i["kind"] == "exit"]
        self.assertEqual(len(exits), 1, out)
        self.assertEqual(exits[0]["symbol"], PUT_OCC)


if __name__ == "__main__":
    unittest.main()
