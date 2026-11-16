"""CLEAR-THE-BOARD-20261114 blockers (owner order, Sat 2026-11-14:
"Fix the defect, blocked, and unfed").

Workstream 2 (BLOCKED-EXTERNAL 28): the 22 ENJ sleeves and 6 Kraken
perp sleeves sat parked on the October verdict that Alpaca serves no
ENJ pair. That is a route fact, not a resting state. Kraken's public
REST serves real ENJ/USD spot bars, and the desk's KrakenProducer
already fetched them every cycle — under the ENJUSD|240Min key form
only one sleeve reads. These blockers pin the cure at the source:

* the producer serves the same real Kraken spot rows under the desk
  spot key form ENJ/USD|4Hour (so every engine routing through
  desk3/crypto_bars.resolve_bars step 2 resolves them) and serves
  ENJ/USD 1-minute spot rows under the granular registry key
  bars:ENJ/USD:1Min that fwd_alpaca_enj_iu_body declares;
* the ENJ rows served are the SPOT payload's rows, never the futures
  (perp) chart rows — the F4 provenance doctrine stands;
* desk3/aster_batch8._bars4 (the seven aster_enj_nfs_* sleeves, the
  one engine family the F4 cure missed because its sleeves were
  parked) resolves through crypto_bars.resolve_bars like every other
  Aster crypto engine, archive keys keeping precedence;
* all 28 config rows are unparked with the CLEAR-THE-BOARD stamp.

Workstream 1 (CR-S3, aster_etf_leader1_c098): the sleeve computed
sells against the AGGREGATE broker book (positions it does not own)
and returned before its buy branch on every in-window evaluation.
The cure serves the sleeve its own journal-derived positions at its
own seam (cycle task construction + worker view application), the
same derived book the dispatcher already seeds its slice from. The
strategy file is untouched; no other sleeve's view changes.
"""
import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOW = datetime(2026, 11, 14, 21, 30, tzinfo=timezone.utc)

ENJ28 = [
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
    "fwd_alpaca_enj_iu_body", "free_kraken_enj_spot",
    "free_kraken_ada_basis", "free_kraken_ada_breakdown",
    "free_kraken_ada_crowded", "free_kraken_link_basis",
    "free_kraken_link_breakdown", "free_kraken_link_crowded",
]


def _kraken_transport(url):
    """Fake Kraken public REST. Spot closes are 2.0, futures chart
    closes are 3.0, so a test can prove which payload was served."""
    import urllib.parse as up
    if "tickers" in url:
        return {"tickers": [
            {"symbol": "PF_ADAUSD", "bid": 1.0, "ask": 1.02,
             "fundingRate": 0.0002},
            {"symbol": "PF_LINKUSD", "bid": 1.49, "ask": 1.51,
             "fundingRate": 0.01}]}
    if "Depth" in url:
        return {"error": [], "result": {"ENJUSD": {
            "bids": [["0.10", "5", 1]], "asks": [["0.11", "5", 1]]}}}
    pair = up.parse_qs(up.urlparse(url).query).get("pair", [""])[0]
    if "charts" in url:
        candles = [{"time": (NOW - timedelta(hours=4 * (23 - i)))
                    .timestamp() * 1000, "open": 3.0, "high": 3.1,
                    "low": 2.9, "close": 3.0, "volume": 10}
                   for i in range(24)]
        return {"candles": candles}
    rows = [[(NOW - timedelta(hours=4 * (23 - i))).timestamp(), "2.0",
             "2.1", "1.9", "2.0", "2.0", "10", 0] for i in range(24)]
    return {"error": [], "result": {pair: rows, "last": 0}}


def _mkroot():
    return tempfile.mkdtemp(prefix="ctb-test-")


class TestKrakenEnjSpotServing(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import desk3.producers3 as p3
        cls.p3 = p3
        cls.out = p3.KrakenProducer(_mkroot(),
                                    transport=_kraken_transport)(
                                        {"now": NOW})

    def test_enj_spot_served_in_desk_spot_key_form(self):
        bars = self.out.get("bars") or {}
        self.assertIn("ENJUSD|240Min", bars)  # incumbent key kept
        self.assertIn("ENJ/USD|4Hour", bars)
        self.assertEqual(bars["ENJ/USD|4Hour"], bars["ENJUSD|240Min"])
        self.assertGreaterEqual(len(bars["ENJ/USD|4Hour"]), 20)

    def test_enj_rows_are_the_spot_payload_not_the_perp(self):
        rows = self.out["bars"]["ENJ/USD|4Hour"]
        self.assertTrue(all(abs(r["c"] - 2.0) < 1e-9 for r in rows),
                        "ENJ spot rows must be the spot payload (c=2.0), "
                        "never the futures chart rows (c=3.0)")

    def test_enj_1min_granular_key_served_and_declared(self):
        self.assertIn("bars:ENJ/USD:1Min", self.p3.KrakenProducer.OUTPUTS)
        rows = self.out.get("bars:ENJ/USD:1Min")
        self.assertIsInstance(rows, list)
        self.assertGreaterEqual(len(rows), 20)
        self.assertTrue(all(abs(r["c"] - 2.0) < 1e-9 for r in rows))


class TestBatch8Bars4Resolution(unittest.TestCase):
    ROWS = [{"t": "2026-11-13T%02d:00:00Z" % (4 * i), "o": 1.0, "h": 1.1,
             "l": 0.9, "c": 1.0, "v": 5.0} for i in range(6)]

    def test_resolves_served_spot_form(self):
        from desk3 import aster_batch8
        view = {"bars": {"ENJ/USD|4Hour": list(self.ROWS)}}
        self.assertEqual(aster_batch8._bars4(view), self.ROWS)

    def test_archive_key_keeps_precedence(self):
        from desk3 import aster_batch8
        arch = [dict(r, c=9.9) for r in self.ROWS[:2]]
        view = {"bars": {"ENJUSDT|4Hour": arch,
                         "ENJ/USD|4Hour": list(self.ROWS)}}
        self.assertEqual(aster_batch8._bars4(view), arch)

    def test_no_series_still_empty(self):
        from desk3 import aster_batch8
        self.assertEqual(aster_batch8._bars4({"bars": {}}), [])


class TestOwnBookView(unittest.TestCase):
    def test_worker_applies_override_on_a_copy(self):
        from desk3.worker import _view_for_task
        data = {"positions": [{"symbol": "ARM", "qty": 3.0}],
                "bars": {"X|1Day": []}}
        task = {"positions_override": []}
        view = _view_for_task(data, task)
        self.assertEqual(view["positions"], [])
        self.assertEqual(data["positions"],
                         [{"symbol": "ARM", "qty": 3.0}])  # unmutated
        self.assertIsNot(view, data)

    def test_worker_without_override_serves_snapshot_itself(self):
        from desk3.worker import _view_for_task
        data = {"positions": [{"symbol": "ARM", "qty": 3.0}]}
        self.assertIs(_view_for_task(data, {}), data)

    def test_cycle_helper_derives_only_flagged_sleeves(self):
        from desk3.cycle import own_book_positions
        root = _mkroot()
        jpath = os.path.join(root, "dispatcher.jsonl")
        with open(jpath, "w") as fh:
            fh.write(json.dumps(
                {"event": "fill", "sleeve": "aster_etf_leader1_c098",
                 "symbol": "QQQ", "qty": 4, "side": "buy",
                 "price": 600.0, "ts": "2026-11-10T15:00:00Z"}) + "\n")
            fh.write(json.dumps(
                {"event": "fill", "sleeve": "other_sleeve",
                 "symbol": "ARM", "qty": 3, "side": "buy",
                 "price": 100.0, "ts": "2026-11-10T15:00:00Z"}) + "\n")
        sleeves = {"aster_etf_leader1_c098": {"own_book_view": True},
                   "other_sleeve": {}}
        out = own_book_positions(sleeves, jpath)
        self.assertEqual(set(out), {"aster_etf_leader1_c098"})
        rows = out["aster_etf_leader1_c098"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["symbol"], "QQQ")
        self.assertEqual(float(rows[0]["qty"]), 4.0)

    def test_cycle_helper_empty_book_is_empty_list(self):
        from desk3.cycle import own_book_positions
        root = _mkroot()
        jpath = os.path.join(root, "dispatcher.jsonl")
        open(jpath, "w").close()
        sleeves = {"aster_etf_leader1_c098": {"own_book_view": True}}
        self.assertEqual(own_book_positions(sleeves, jpath),
                         {"aster_etf_leader1_c098": []})

    def test_config_flags_exactly_c098(self):
        rows = json.load(open(os.path.join(ROOT, "config",
                                           "sleeves.json")))
        if isinstance(rows, dict):
            rows = rows.get("sleeves") or rows.get("rows") or []
        flagged = [r["id"] for r in rows if r.get("own_book_view")]
        # GOING-LIVE-BASKETS-20261115: the five overnight basket
        # sleeves also carry own_book_view, by the same CR-S3
        # logic: each basket must exit exactly its own book,
        # never another basket's position in the same name (the
        # baskets overlap heavily by construction).
        # ENJ-PAPER-20261116 (amendment, dated estate form): the 22
        # ENJ-class sleeves also carry own_book_view, by the same
        # CR-S3 logic in its strongest form: their paper book
        # exists ONLY in the dispatcher journal (the broker book
        # can never hold ENJ), so the aggregate book is not merely
        # wrong for them, it is permanently empty. The expected
        # list below is config order: the six pre-ENJ flags in
        # their original relative order, then the ENJ 22 in
        # config order, interleaved exactly as the roster carries
        # them (asserted as a set plus the six's relative order).
        # EXIT-STORM-CURE-20261116 (amendment, dated estate form):
        # beatendown and confluence also carry own_book_view, by
        # the same CR-S3 logic: served the aggregate book they
        # converted a BTC/USD lot neither ever bought into a
        # perpetual phantom 13-week time exit (58 per sleeve on
        # 2026-11-16) and filled phantom exits against other
        # sleeves' positions. The two join the expected set below
        # at full strength; the six's relative order is unchanged.
        enj22 = ["aster_abs_enj_4h", "aster_enj_nfs_fixed96_vol",
                 "aster_enj_nfs_lost_full", "aster_enj_nfs_lost_vol",
                 "aster_enj_nfs_norm_full", "aster_enj_nfs_norm_vol",
                 "aster_enj_nfs_normfail_full",
                 "aster_enj_nfs_normfail_vol",
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
                 # T474U-CRYPTO-PORT-20261116: the three t474u ENJ
                 # twins carry own_book_view in the same kraken_paper
                 # form (desk3/t474u_crypto.py config_rows).
                 "crypto_bratr_enj", "crypto_mfi_enj",
                 "crypto_stdev_enj"]
        # CONV123-REVIVAL-20261116 (amendment, dated estate
        # form): revival_basket also carries own_book_view, by
        # the same CR-S3 logic as the overnight baskets: the
        # revival basket's family names (SPY, the eight Gatev
        # pair names, the PEAD Focus filers) overlap other
        # sleeves heavily, so it must exit exactly its own book.
        # It is rostered last, so the relative-order assertion
        # below still reads config order.
        six = ["aster_etf_leader1_c098",
               "overnight_focus29",
               "overnight_energy8",
               "overnight_basket8",
               "overnight_semis12",
               "overnight_focus29_ex_rklb"]
        # ETF-BUYHOLD-ENTRY-20261116 (amendment, dated estate form):
        # the six aster BUY_HOLD ETF sleeves also carry own_book_view,
        # by the same CR-S3 logic: served the aggregate broker book
        # (sole position BTC/USD) they read a foreign position as
        # their completed allocation and never entered live. Their
        # journal-derived books are empty, which is the truth.
        buyhold6 = ["aster_etf_qld_buy_hold", "aster_etf_qqq_buy_hold",
                    "aster_etf_qqq_qld_buy_hold",
                    "aster_etf_smh_hold_c098", "aster_etf_smh_hold_m150",
                    "aster_etf_spy_buy_hold"]
        # EXIT-STORM-CURE-20261116 (amendment, dated estate form):
        # beatendown and confluence carry own_book_view after the
        # phantom-exit storm disposition (EXIT-STORM-ROOT-20261116).
        storm2 = ["beatendown", "confluence"]
        # CONV123-REVIVAL-20261116: revival_basket joins the set.
        revival1 = ["revival_basket"]
        # SEGMENT-CONSTRUCTION-20261116 (carried by
        # TOTAL-AUDIT-PIN-REBASE-20261116): the two segment
        # sleeves also carry own_book_view (each exits exactly
        # its own midday book); the segment merge left this
        # census unamended and the rebase carries it.
        segment2 = ["ls9_midday_short", "b3_midday_fade_var"]
        # OBV-CLASS-20261116 (amendment, dated estate form): the
        # full sleeve audit's Lane F class sweep (Lane F Job 2)
        # classified 217 further sleeves VULNERABLE to
        # aggregate-book adoption: their exit/manage paths fire
        # on served position fields an aggregate broker row
        # actually carries (symbol/qty/avg_price, OCC form), the
        # shen_fade disease class. All 217 also carry
        # own_book_view, by the same CR-S3 logic. The sweep's 115
        # SAFE-BY-CONSTRUCTION names (anchor/legs-gated exits)
        # and its 26 AMBIGUOUS names do NOT join the set in this
        # landing; the ambiguous 26 are named in the audit
        # report, not cleared.
        obv217 = ["1d",
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
                 "vix_hedge"]
        # OBV-CLASS-20261116 landing recheck (same dated form):
        # aster_r19_tensor_g4_hot_reserve_25 joins the set — the
        # batch15 G4 reserve funding sale reads the served QQQ
        # row with no own-book anchor (Lane F's stated condition
        # for its SAFE call, not met on the coordinator's read).
        recheck1 = ["aster_r19_tensor_g4_hot_reserve_25"]
        # OBV-DRIVE-20261116 (2026-11-16): the 12 sleeves the
        # completion drive proved adopt foreign positions
        # (grok_sr_spy + the trullas family) joined the flagged
        # set; admitted here by name in the same dated form.
        drive12 = ["grok_sr_spy", "trullas_divergence",
                   "trullas_v01", "trullas_v02", "trullas_v03",
                   "trullas_v04", "trullas_v05", "trullas_v06",
                   "trullas_v07", "trullas_v08", "trullas_v09",
                   "trullas_v10"]
        self.assertEqual(sorted(flagged),
                         sorted(six + enj22 + buyhold6 + storm2
                                + revival1 + segment2 + obv217
                                + recheck1 + drive12))
        self.assertEqual([f for f in flagged if f in six], six)


class TestQldWarmUniverse(unittest.TestCase):
    def test_qld_in_desk_symbols(self):
        # CR-1's four QLD sleeves refuse their whole rebalance on a
        # missing target price (aster_etf target loop): QLD is a
        # real Alpaca-listed ETF and the sleeves' own instrument,
        # but desk_symbols never served it (the SMH-warm shape,
        # 2026-11-12). The warm universe is the source; fix there.
        from desk3.warm import desk_symbols
        self.assertIn("QLD", desk_symbols(ROOT))


class TestUnparked28(unittest.TestCase):
    def test_all_28_unparked_with_stamp(self):
        rows = json.load(open(os.path.join(ROOT, "config",
                                           "sleeves.json")))
        if isinstance(rows, dict):
            rows = rows.get("sleeves") or rows.get("rows") or []
        by_id = {r["id"]: r for r in rows}
        for sid in ENJ28:
            self.assertIn(sid, by_id, sid)
            row = by_id[sid]
            self.assertFalse(row.get("parked"), sid)
            stamp = (row.get("params") or {}).get("parked_reason") or ""
            self.assertIn("CLEAR-THE-BOARD", stamp, sid)


if __name__ == "__main__":
    unittest.main()


# ---------------------------------------------------------------- WS3 przm
class TestPrzmTapeBridge(unittest.TestCase):
    """PRZM-TAPE-20261114: the bridge builds spec-shaped prints from
    raw v1beta1-shaped rows. The rows here are UNIT INPUTS (schema-
    real, hand-built); the live route's real-print evidence is the
    morgue tape card's 2026-11-13 run over the identical endpoint
    (510,250 SPY prints), and the dated real-print proof is the
    first in-window live session, Mon 2026-11-16."""

    def _build(self, rows, quotes, spot=750.0):
        from desk3 import przm_tape
        from desk3.producers import _bs_call_price
        from sleeves.przm_zero import bs_delta

        def bs_price(S, K, T, sigma, is_call):
            c = _bs_call_price(S, K, T, 0.0, sigma)
            return c if is_call else c - S + K

        return przm_tape.build_prints(rows, quotes, spot, bs_price,
                                      bs_delta)

    def test_ask_side_call_is_bullish_with_computed_delta(self):
        rows = [{"symbol": "SPY261113C00750000",
                 "t": "2026-11-13T14:05:00Z", "p": 2.50, "s": 100,
                 "c": ["S"]}]
        quotes = {"SPY261113C00750000": (2.40, 2.50)}
        out = self._build(rows, quotes)
        self.assertEqual(len(out), 1)
        p = out[0]
        self.assertEqual(p["bull"], 1)          # ask-side call
        self.assertTrue(p["bought_at_ask"])
        self.assertTrue(p["sweep"])             # condition S
        self.assertGreater(p["delta"], 0.3)     # near-ATM call delta
        self.assertEqual(p["delta_source"], "spec_bs_delta_v1")
        self.assertEqual(p["iv_source"], "quote_mid_inverted")
        self.assertNotIn("opening", p)          # never fabricated
        self.assertNotIn("closing", p)

    def test_mid_print_is_neutral_and_unquoted_print_unjudged(self):
        rows = [{"symbol": "SPY261113P00750000",
                 "t": "2026-11-13T14:05:00Z", "p": 2.45, "s": 10,
                 "c": []},
                {"symbol": "SPY261113C00760000",
                 "t": "2026-11-13T14:06:00Z", "p": 1.00, "s": 5,
                 "c": []}]
        quotes = {"SPY261113P00750000": (2.40, 2.50)}  # mid = 2.45
        out = self._build(rows, quotes)
        self.assertIsNone(out[0]["bull"])       # mid -> neutral
        self.assertTrue(out[0]["mid"])
        self.assertIsNone(out[1]["bull"])       # no quote -> unjudged
        self.assertEqual(out[1]["iv_source"], "spec_default")
        # and the frozen spec sets neutral prints aside itself
        from sleeves.przm_zero import print_weight
        self.assertEqual(print_weight(out[0]), 0.0)
        self.assertEqual(print_weight(out[1]), 0.0)

    def test_adapter_consumes_tape_and_leaves_waiting_state(self):
        import tempfile
        rows = []
        quotes = {}
        # a one-sided bullish tape of ask-side call prints
        for i in range(40):
            occ = "SPY261113C00750000"
            rows.append({"symbol": occ,
                         "t": f"2026-11-13T14:{10 + i // 6:02d}:"
                              f"{(i % 6) * 10:02d}Z",
                         "p": 2.50, "s": 500, "c": ["S"]})
            quotes[occ] = (2.40, 2.50)
        prints = self._build(rows, quotes, spot=752.0)
        self.assertTrue(all(p["bull"] == 1 for p in prints))
        bars = [{"t": f"2026-11-13T{13 + (m // 60):02d}:{m % 60:02d}:00Z",
                 "o": 750.0, "h": 753.0, "l": 749.0,
                 "c": 750.0 + m * 0.01, "v": 1000}
                for m in range(0, 130)]
        view = {"now": "2026-11-13T15:00:00Z",
                "bars": {"SPY|1Min": bars},
                "positions": [], "przm_prints": prints,
                "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0},
                "params": {}}
        sd = tempfile.mkdtemp()
        ctx = {"sleeve_id": "przm_zero", "state_dir": sd,
               "cycle_id": "ctb-przm"}
        import importlib
        mod = importlib.import_module("adapters3.przm_zero")
        mod.evaluate(view, ctx)
        journal = open(os.path.join(sd, "journal.jsonl")).read()
        self.assertIn("adapter_eval", journal)
        self.assertNotIn("WAITING_NO_PRINT_TAPE", journal)
        self.assertIn("drivers", journal)

    def test_recorded_real_prints_drive(self):
        """The recorded REAL Friday tape (tests/fixtures/
        przm_tape_20261113.json: 3,035 Alpaca v1beta1 SPY 0DTE
        prints, 14:00-14:20Z) builds spec prints and the sleeve
        consumes them: state leaves WAITING_NO_PRINT_TAPE with
        drivers computed. Quotes for the expired contracts are no
        longer served, so sides stay unjudged in this fixture
        (bull None, spec weight 0) — the judged path is proven by
        the unit drives above and goes live in-session Monday."""
        import tempfile
        fx = json.load(open(os.path.join(
            ROOT, "tests", "fixtures", "przm_tape_20261113.json")))
        self.assertGreater(len(fx["trades"]), 1000)
        quotes = {k: tuple(v) for k, v in fx["quotes"].items()}
        prints = self._build(fx["trades"], quotes, spot=fx["spot"])
        self.assertGreater(len(prints), 1000)
        self.assertTrue(all(p["delta_source"] == "spec_bs_delta_v1"
                            for p in prints))
        # every recorded print in this slice carries condition
        # 'v' (not a sweep code): the builder's sweep flag is
        # honestly False for all of them; the S/b/d mapping is
        # proven on the unit rows above.
        self.assertTrue(all(p["sweep"] is False for p in prints))
        bars = [{"t": f"2026-11-13T{13 + (m // 60):02d}:{m % 60:02d}:00Z",
                 "o": 750.0, "h": 756.0, "l": 749.0,
                 "c": 750.0 + m * 0.02, "v": 1000}
                for m in range(0, 130)]
        view = {"now": "2026-11-13T15:00:00Z",
                "bars": {"SPY|1Min": bars},
                "positions": [], "przm_prints": prints,
                "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0},
                "params": {}}
        sd = tempfile.mkdtemp()
        ctx = {"sleeve_id": "przm_zero", "state_dir": sd,
               "cycle_id": "ctb-przm-real"}
        import importlib
        mod = importlib.import_module("adapters3.przm_zero")
        mod.evaluate(view, ctx)
        journal = open(os.path.join(sd, "journal.jsonl")).read()
        self.assertIn("adapter_eval", journal)
        self.assertNotIn("WAITING_NO_PRINT_TAPE", journal)
        self.assertIn("drivers", journal)


# ------------------------------------------------------- WS3 milkman chain
class TestMilkmanChain(unittest.TestCase):
    """MILKMAN-CHAIN-20261114: parity spot recovery, computed delta
    within tolerance, non-inverting rows keep delta None, and the
    adapters3 injection serves the chain without mutating the
    shared options product."""

    def _synthetic(self):
        import math
        from datetime import datetime
        from zoneinfo import ZoneInfo
        from desk3.producers import _bs_call_price
        ET = ZoneInfo("America/New_York")
        spot, expiry = 6000.0, "2026-11-16"
        now = datetime(2026, 11, 16, 14, 30, tzinfo=ET)
        from datetime import time as _t
        close = datetime.combine(now.date(), _t(16, 0),
                                 tzinfo=ZoneInfo("America/New_York"))
        T = (close - now).total_seconds() / (365.25 * 86400.0)
        iv = 0.12
        contracts, snaps = [], {}
        for K in range(5950, 6051, 10):
            for right in ("call", "put"):
                c = _bs_call_price(spot, K, T, 0.04, iv)
                px = c if right == "call" else c - spot + K * math.exp(-0.04 * T)
                px = max(px, 0.05)
                sym = f"SPXW261116{'C' if right == 'call' else 'P'}{K * 1000:08d}"
                contracts.append({"symbol": sym, "type": right,
                                  "strike_price": float(K)})
                snaps[sym] = {"latestQuote": {
                    "bp": round(px - 0.05, 2), "ap": round(px + 0.05, 2),
                    "t": "2026-11-16T14:30:00Z"}}
        return contracts, snaps, now

    def test_parity_spot_and_delta(self):
        from desk3 import milkman_chain
        contracts, snaps, now = self._synthetic()
        payload = milkman_chain.build_chain(contracts, snaps, "SPXW",
                                            "2026-11-16", now)
        self.assertIsNotNone(payload)
        self.assertAlmostEqual(payload["spot"], 6000.0, delta=2.0)
        self.assertEqual(payload["spot_source"], "put_call_parity_mid")
        rows = payload["chains"]["SPXW"]
        atm = [r for r in rows if r["strike"] == 6000.0
               and r["type"] == "call"][0]
        self.assertAlmostEqual(atm["delta"], 0.5, delta=0.06)
        self.assertEqual(atm["delta_source"], "bs_parity_indicative_v1")
        self.assertTrue(all(r["delta"] is not None for r in rows))

    def test_adapter_injection_serves_chain_view_unmutated(self):
        import importlib
        import tempfile
        contracts, snaps, now = self._synthetic()
        from desk3 import milkman_chain
        payload = milkman_chain.build_chain(contracts, snaps, "SPXW",
                                            "2026-11-16", now)
        view = {"now": "2026-11-16T14:30:00Z", "bars": {},
                "positions": [], "options": {"SPY": {"chains": {}}},
                "milkman_0dte_chain": payload,
                "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0},
                "params": {}}
        mod = importlib.import_module("adapters3.milkman_0dte")
        sd = tempfile.mkdtemp()
        ctx = {"sleeve_id": "mk_zerodte_spx", "state_dir": sd,
               "cycle_id": "ctb-mk"}
        mod.evaluate(view, ctx)
        # the shared product was not mutated by the injection
        self.assertNotIn("SPX", view["options"])
        journal = open(os.path.join(sd, "journal.jsonl")).read()
        self.assertIn("adapter_eval", journal)
