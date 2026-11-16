"""Regression blockers: CONVERSION-ARMING-20261115 (2026-11-15).

Defect class: the Conversion Program (owner order 2026-11-15 19:37
ET) specified 17 BLOCKED-ON-WIRING rows completely but executed
none of them, so 15 tradeable potential-edge objects had no forward
instrument and two (ENJ, SSO) had premises that did not survive
contact with the desk's own records.

Cure (this landing):
- config/conversion_shadow_20261115.json + desk3/conversion_shadow.py:
  13 registered shadow arms (CONV-25, 26, 28, 29, 30, 31, 32, 33,
  35, 36, 37, 38, 45) grading forward fills and fires from
  2026-11-16 on the pass-2 exit-sim semantics, parents untouched.
- aster_trader_turtle2010 (CONV-47) rostered beside
  aster_trader_donchian55 as a separate evaluator; the parent's
  evaluator sources and roster row are pinned below.
- CONV-27 (ENJ: no price series exists on this desk) and CONV-46
  (SSO: no installed parent exists on any live surface) stay
  BLOCKED-ON-WIRING in the Conversion Register with the exact
  missing piece recorded; the last test here asserts neither was
  silently armed in a loosened form.
- ENJ-FEED-CONV27-20261115 (later the same night): CONV-27's
  unblocker landed (the Kraken ENJ/USD tape persisted by the warm
  layer; the batch7 resolver cure; the intent-sourced shadow arm),
  so the arm census below is fourteen and the last test now
  asserts CONV-27 armed deliberately in its registered form while
  CONV-46 (SSO) remains unarmed. See
  tests/test_conv27_enj_feed_20261115_blockers.py.
- CONVERSION-PASS2-ARMING-20261115 (Sun 2026-11-15 night, landed
  by the desk lane): Conversion Pass 2 added 14 arms as pure
  config additions in the established arm forms (nine FWD_GRADE
  promotion and own-stream grades: CONV-92, 95, 97, 100, 105,
  107, 116, 144, 147; the ENJ squeeze family in intents form:
  CONV-117; three EXIT_PAIR horizon arms: CONV-96, 98, 151; one
  ACTUAL_PAIR night-1 arm: CONV-81), so the arm census below is
  twenty-eight. The 14 pre-existing arms are byte-identical to
  their registered forms; only the registry note gained a dated
  Pass 2 append. See CONVERSION-PASS-2-2026-11-15.md section 4.

Fail direction: on the pre-change tree at commit 173d818 the
registry, the grader module and the turtle sleeve do not exist, so
the registry, grader and turtle tests fail or error there; the
parent pins pass on both trees by design (they pin what must not
move).
"""
import hashlib
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# OBV-CLASS-20261116 re-pin (2026-11-16): twelve pins below were
# re-based because OBV-CLASS-20261116 added own_book_view: true to
# those parents' roster rows (aster_trader_donchian55, 1d, 1dc, 1w,
# 1wa, s_1dg, s_rules_1d, s_rules_1w, s_1wc_ml, s_1wlab,
# s_mn_hourly_1w, tensor_swing). Verified: each amended row differs
# from its pre-OBV row by exactly that one key; the flag set itself
# is pinned exactly by tests/test_obv_class_20261116_blockers.py.
# Module pins are untouched (no strategy file changed).
PARENT_ROW_SHA256 = {
    "aster_trader_donchian55":
        "c02ee7a4b057c94ffa806357c5685196dd7e5802c41189019c501081c872a8cb",
    "aster_breakout_ada_fullcash":
        "ceffee8db90710c4d52fd243cabbc391225aae962e5603d8eb8805ea3f305ee8",
    "aster_breakout_ada_vol1pct":
        "87e75c3c8df03c51a2b89c82888bb5db432c76c5e0839c41d997092bb77e050e",
    "aster_r19_linkusdt_breakout_base_fixed16_fullcash":
        "eef35e5754bded57bdad491cd0e83cd7f2871a952d2e10f8cbb49caf204ca14c",
    "aster_r19_linkusdt_breakout_base_fixed16_volume1pct":
        "87e3ac0674e572b462872cd7d3208f21eae0403c761fa73bbe2396ebed34cc00",
    "aster_pub_link_ai_volume":
        "edc414a2e6a2a3f2ec6c83eae039509fd7a4e49e592e614249c37173c3abcb69",
    "aster_abs_link_4h":
        "b0c20e23076c1140e51a11c88a6c8525ba044983a2188593ed6c5f68f1da954b",
    "aster_r19_linkusdt_absorption_base_fixed16_fullcash":
        "465472f2169ec926a2d35983e918d404ed2723ee875125a4cffc7a6e599338ab",
    "aster_r19_linkusdt_absorption_base_fixed16_volume1pct":
        "a4942fce23e0cfcde97e0dc74aa95972e797e6635605c02bb8b7ab7d0d178c51",
    "1d": "46dd695592d01958faf6af70f9162e1dc6eaf66abd1a1dd8dff45a7fa06b2f1c",
    "1dc": "f3589fdea44d5c704a18cb5bf165b6403e296273aeff8c7ca934c5fc98292db1",
    "1w": "5a4e4c160ca9b9f6869cc27d639e8a281de52f8c589eb5aa92bfe4173a86e037",
    "1wa": "913464465c74e5d52ab6f4fc9add022d4204cd9f92cb265152e9ee4596f52c39",
    "s_1dg": "b71147b4650bb61b480e8e6de828cd90080d1590236b00b630f52f46c68a87fe",
    "s_rules_1d":
        "5a88676d5feb0216ce09cbef558b626e8d08b7cba47607faf16197721f6af641",
    "s_rules_1w":
        "e6ac857b35d25fb2fd35b03d34c11551359ea46d8e580319644e29d003ab1440",
    "s_1wc_ml":
        "4cd2717b7235f339225f1385d12cb28ad58467f7763ff5b3d8814918aef52d3c",
    "s_1wlab": "91c0aaaa382ba42e6a4d6a3814212d6a701cb1750d29b8a95d1fb9434b90f54b",
    "s_mn_hourly_1w":
        "42fbdfa10e1dbdc09ebb2c686a37c6f344d0a5f2efa64df1d9910f04cb32e0f4",
    "aster_tensor_d20_tensor":
        "302d33fe9c705ad853710714fa6d1b7a87c8f661a5260cf6c78dc022207895a0",
    "aster_tensor_d20_pv":
        "bcda95f1ac7e2df4c87671d78d818e69bd30f052c6735efb057b8250a48bd9ea",
    "tensor_swing":
        "d4720a27083755be1ebb321258e26f1f1898499f5bb400db5bc1324086b039e8",
}
# GOING-LIVE-VARIATIONS-20261115: pin refreshed 3db7df4a -> d50cc60e
# on the Lane B landing: desk3/lazarus.py changed additively only
# (new variation SPECS entries plus the force_spec_horizon and
# horizon_sessions None branches keyed only by keys no pre-existing
# entry carries); every pre-existing SPECS entry is pinned
# byte-identically by tests/test_going_live_variations_20261115_blockers.py
# SPEC_PINS, so the parent-untouched guarantee this pin carried is
# preserved at SPECS granularity.
# SILENT-SKIP-SIZING-20261116 refresh (2026-11-16): desk3/lazarus.py
# changed at its sizing site only (the whole-share floor that
# reached 0 now falls back to the same per-slot budget expressed
# fractionally, WS4 shape; quantity >= 1 behavior unchanged). Every
# pre-existing SPECS entry remains pinned byte-identically by the
# going-live-variations SPEC_PINS, so the parent-untouched guarantee
# is preserved at SPECS granularity exactly as in the refresh above.
LAZARUS_PY_SHA256 = \
    "677771cdfbf0766e7ee95f2e3acae4fbbce3909ec8239910ff1ca3239e81f137"
DONCHIAN_FN_SHA256 = {
    "_eval_donchian":
        "2fc3291db122448df719dfb6c594a28bed56b719d12f18396206b1e9c52610bc",
    "_don_features":
        "a52150045da154f2b7f41809859901b1aa533d46f16c2b2f3358cdaa1f0e2ec4",
}
EXPECTED_ARMS = {
    "CONV-25": "FWD_GRADE", "CONV-26": "FWD_GRADE",
    # ENJ-FEED-CONV27-20261115: CONV-27 armed deliberately once
    # its unblocker landed (see the module docstring note).
    "CONV-27": "FWD_GRADE",
    "CONV-28": "FWD_GRADE", "CONV-29": "EXIT_PAIR",
    "CONV-30": "EXIT_PAIR", "CONV-31": "EXIT_PAIR",
    "CONV-32": "EXIT_PAIR", "CONV-33": "EXIT_PAIR",
    "CONV-35": "GATE_PAIR", "CONV-36": "EXIT_PAIR",
    "CONV-37": "ACTUAL_PAIR", "CONV-38": "ACTUAL_PAIR",
    "CONV-45": "RACE",
    # CONVERSION-PASS2-ARMING-20261115: the 14 Pass 2 arms, added
    # as pure config additions in the established arm forms.
    "CONV-81": "ACTUAL_PAIR",
    "CONV-92": "FWD_GRADE", "CONV-95": "FWD_GRADE",
    "CONV-96": "EXIT_PAIR", "CONV-97": "FWD_GRADE",
    "CONV-98": "EXIT_PAIR", "CONV-100": "FWD_GRADE",
    "CONV-105": "FWD_GRADE", "CONV-107": "FWD_GRADE",
    "CONV-116": "FWD_GRADE", "CONV-117": "FWD_GRADE",
    "CONV-144": "FWD_GRADE", "CONV-147": "FWD_GRADE",
    "CONV-151": "EXIT_PAIR",
    # GOING-LIVE-GRADER-ARMS-20261115: the 25 Lane C grader arms
    # under 18 rows joined the census deliberately (CONV-34 x4 and
    # CONV-161 x4 EXIT_PAIR, CONV-152 x2 FWD_GRADE, the rest one
    # arm each in the new kinds); the dict below maps conv to kind
    # as before, and the arm count assertion carries the multi-arm
    # rows. Their own blocker file is
    # tests/test_conversion_grader_arms_20261115_blockers.py.
    "CONV-34": "EXIT_PAIR", "CONV-61": "SPLIT_GRADE",
    "CONV-62": "PHASE_GRADE", "CONV-74": "SPLIT_GRADE",
    "CONV-75": "PHASE_GRADE", "CONV-76": "MEMBER_GRADE",
    "CONV-77": "ACTUAL_PAIR", "CONV-93": "MEMBER_GRADE",
    "CONV-94": "FWD_GRADE", "CONV-99": "FWD_GRADE",
    "CONV-101": "SPLIT_GRADE", "CONV-113": "SPLIT_GRADE",
    "CONV-131": "SPLIT_GRADE", "CONV-143": "FWD_GRADE",
    "CONV-150": "EXIT_PAIR", "CONV-152": "FWD_GRADE",
    "CONV-156": "TWO_POOL", "CONV-161": "EXIT_PAIR",
    # NIGHTLY-JOIN-ARTIFACTS-20261116: CONV-86 and CONV-87 joined
    # the census deliberately as FORECAST_JOIN arms on the one
    # nightly join; their own blocker file is
    # tests/test_nightly_join_artifacts_20261116_blockers.py.
    "CONV-86": "FORECAST_JOIN", "CONV-87": "FORECAST_JOIN",
    # SEGMENT-CONSTRUCTION-20261116: CONV-80 joined the census
    # deliberately as the SEGMENT_GRADE arm; its own blocker file
    # is tests/test_segment_construction_20261116_blockers.py.
    "CONV-80": "SEGMENT_GRADE",
    # CONV21-INVERT-20261116: CONV-21 joined the census as the
    # both-sides FWD_GRADE arm for the QLD monthly inversion;
    # its own blocker file is
    # tests/test_conv21_inverted_20261116_blockers.py.
    "CONV-21": "FWD_GRADE",
}
PASS2_ARMS = {
    "CONV-81", "CONV-92", "CONV-95", "CONV-96", "CONV-97",
    "CONV-98", "CONV-100", "CONV-105", "CONV-107", "CONV-116",
    "CONV-117", "CONV-144", "CONV-147", "CONV-151",
}


def _rows():
    return json.loads((ROOT / "config/sleeves.json")
                      .read_text())["sleeves"]


def _row_sha(row):
    return hashlib.sha256(
        json.dumps(row, sort_keys=True).encode()).hexdigest()


class TestShadowRegistry(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg = json.loads(
            (ROOT / "config/conversion_shadow_20261115.json")
            .read_text())
        cls.arms = {a["conv"]: a for a in cls.reg["arms"]}

    def test_all_fiftythree_arms_registered(self):
        # Renamed from thirteen on the ENJ-FEED-CONV27-20261115
        # landing (CONV-27 joined the census deliberately), then
        # from fourteen on the CONVERSION-PASS2-ARMING-20261115
        # landing: the 14 Pass 2 arms joined the census
        # deliberately, as pure config additions. Renamed from
        # twentyeight on the GOING-LIVE-GRADER-ARMS-20261115
        # landing: the 25 Lane C grader arms under 18 rows joined
        # the census deliberately (multi-arm rows CONV-34 x4,
        # CONV-161 x4, CONV-152 x2 collapse to one dict entry each
        # in the kind map, as the map has always been keyed by
        # conv; the count assertion carries the full 53).
        self.assertEqual({c: a["kind"] for c, a in self.arms.items()},
                         EXPECTED_ARMS)
        # 53 through GOING-LIVE-GRADER-ARMS-20261115; 55 after
        # NIGHTLY-JOIN-ARTIFACTS-20261116 added CONV-86/87; 56
        # after SEGMENT-CONSTRUCTION-20261116 added CONV-80; 57
        # after CONV21-INVERT-20261116 added CONV-21.
        self.assertEqual(len(self.reg["arms"]), 57)
        self.assertEqual(self.reg["start_date_et"], "2026-11-16")
        self.assertEqual(self.reg["exit_cost"], 0.0006)

    def test_pass2_arms_present_in_registered_forms(self):
        # CONVERSION-PASS2-ARMING-20261115: every Pass 2 arm id is
        # present, in the kind its Conversion Register row
        # specifies, and CONV-117 grades the ENJ squeeze family
        # from dispatcher intents (its entries can never fill).
        self.assertTrue(PASS2_ARMS <= set(self.arms))
        for conv in PASS2_ARMS:
            self.assertEqual(self.arms[conv]["kind"],
                             EXPECTED_ARMS[conv], conv)
        self.assertEqual(self.arms["CONV-117"].get("entry_source"),
                         "intents")

    def test_every_arm_carries_its_registered_falsifier(self):
        for conv, arm in self.arms.items():
            self.assertTrue(arm["falsifier"].strip(), conv)
            self.assertTrue(arm["kill_rule"].strip(), conv)
            self.assertGreaterEqual(arm["grade_n"], 10, conv)
        # Exact texts, byte-identical to CONVERSION-REGISTER rows.
        self.assertEqual(
            self.arms["CONV-30"]["kill_rule"],
            "An arm whose paired delta is not positive at its grade "
            "retires.")
        self.assertEqual(
            self.arms["CONV-35"]["kill_rule"],
            "Paired delta not positive retires the gateless form "
            "for that sleeve.")
        self.assertEqual(
            self.arms["CONV-38"]["kill_rule"],
            "Paired delta not positive retires the overlay.")
        self.assertTrue(self.arms["CONV-45"]["falsifier"].startswith(
            "The race itself at 20 forward fires"))

    def test_lazarus_sourced_bases_match_the_live_specs(self):
        from desk3 import conversion_shadow as cs
        for conv, arm in self.arms.items():
            src = arm.get("base_source") or ""
            if src.startswith("lazarus:"):
                self.assertEqual(cs.base_profile(arm), arm["base"],
                                 conv)
                self.assertFalse(cs.spec_drift(arm), conv)

    def test_blocked_rows_were_not_silently_armed(self):
        blob = json.dumps(self.reg)
        # CONV-46 (SSO) stays unarmed here: its unblocker is the
        # fidelity port, registered in the variations registry,
        # never in this shadow registry.
        self.assertNotIn("SSO", blob)
        self.assertNotIn("CONV-46", blob)
        # ENJ-FEED-CONV27-20261115: CONV-27 is armed deliberately,
        # in exactly its registered form (falsifier and kill rule
        # byte-identical to its Conversion Register row), after its
        # named unblocker landed. The protection this test carries
        # forward: no arm exists beyond the EXPECTED_ARMS census
        # above, and CONV-27's texts are the register's own.
        conv27 = [a for a in self.reg["arms"] if a["conv"] == "CONV-27"]
        self.assertEqual(len(conv27), 1)
        self.assertEqual(conv27[0]["falsifier"],
                         "First 10 resolved shadow entries graded at "
                         "fwd10.")
        self.assertEqual(conv27[0]["kill_rule"],
                         "Non-positive fwd10 excess over those "
                         "entries retires the lead.")


class TestGraderMath(unittest.TestCase):
    def _series(self):
        dates = ["2026-11-%02d" % d for d in range(16, 31)] + \
                ["2026-12-01"]
        closes = {d: 100.0 for d in dates}
        closes["2026-11-21"] = 110.0
        closes["2026-11-26"] = 121.0
        bench = (list(dates), {d: 200.0 for d in dates})
        bench[1]["2026-11-21"] = 210.0
        return (dates, closes), bench

    def test_fwd_excess_long_and_short(self):
        from desk3 import conversion_shadow as cs
        series, bench = self._series()
        i = cs.idx_of(series, "2026-11-16")
        raw, exc = cs.fwd_ret(series, bench, i, 100.0, 1, 5)
        self.assertAlmostEqual(raw, 0.10)
        self.assertAlmostEqual(exc, 0.05)
        raw, exc = cs.fwd_ret(series, bench, i, 100.0, -1, 5)
        self.assertAlmostEqual(raw, -0.10)
        self.assertAlmostEqual(exc, -0.15)

    def test_path_stop_target_horizon(self):
        from desk3 import conversion_shadow as cs
        series, bench = self._series()
        i = cs.idx_of(series, "2026-11-16")
        r = cs.path_ret(series, bench, i, 100.0, 1, None, 0.10, 10)
        self.assertAlmostEqual(r["ret"], 0.10 - 0.0006)
        self.assertEqual(r["kind"], "target")
        r = cs.path_ret(series, bench, i, 100.0, 1, None, None, 5)
        self.assertAlmostEqual(r["ret"], 0.10 - 0.0006)
        self.assertTrue(r["resolved"])
        dates, closes = series
        dip = (dates, dict(closes))
        dip[1]["2026-11-18"] = 94.0
        r = cs.path_ret(dip, bench, i, 100.0, 1, 0.05, None, 10)
        self.assertAlmostEqual(r["ret"], -0.05 - 0.0006)
        self.assertEqual(r["kind"], "stop")

    def test_path_drop_horizon_waits_for_min_age(self):
        from desk3 import conversion_shadow as cs
        series, bench = self._series()
        i = cs.idx_of(series, "2026-11-16")
        r = cs.path_ret(series, bench, i, 100.0, 1, None, None, None,
                        min_age=40)
        self.assertFalse(r["resolved"])  # only 15 sessions exist
        r = cs.path_ret(series, bench, i, 100.0, 1, None, None, None,
                        min_age=5)
        self.assertTrue(r["resolved"])
        self.assertAlmostEqual(r["ret"], 0.0 - 0.0006)  # last close 100

    def test_gate_sets_apply_engine_filters(self):
        from desk3 import conversion_shadow as cs
        from desk3.lazarus import SPECS

        def fire(sym, red, fam):
            return {"sleeve_id": None, "symbol": sym,
                    "date": "2026-11-16", "price": 10.0, "side": "buy",
                    "family": fam, "tf": None, "signal_tier": None,
                    "cap_tier": None, "ml_pick": None, "qqq_red": red}
        fires = [fire("AAA", True, "cyan"), fire("BBB", False, "cyan"),
                 fire("CCC", True, "green")]
        bench = (["2026-11-13", "2026-11-16"],
                 {"2026-11-13": 200.0, "2026-11-16": 190.0})
        gated, gateless = cs.gate_sets(fires, "1wa", SPECS["1wa"],
                                       bench)
        self.assertEqual([e["symbol"] for e in gateless],
                         ["AAA", "BBB"])
        self.assertEqual([e["symbol"] for e in gated], ["AAA"])
        gated, gateless = cs.gate_sets(fires, "1w", SPECS["1w"], bench)
        self.assertEqual([e["symbol"] for e in gateless],
                         ["AAA", "BBB", "CCC"])
        self.assertEqual([e["symbol"] for e in gated], ["AAA", "CCC"])


def _bars(closes, pad=0.1, vol=1_000_000.0):
    return [{"t": "2026-01-01", "o": c, "h": c + pad, "l": c - pad,
             "c": c, "v": vol} for c in closes]


def _view(bars_by_sym):
    return {"now": "2026-11-14T15:00:00+00:00",
            "bars": {f"{s}|1Day": b for s, b in bars_by_sym.items()},
            "positions": [],
            "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0}}


class TestTurtleVariation(unittest.TestCase):
    def test_roster_387_and_turtle_row_is_a_pure_clone(self):
        # Count refreshed 359 -> 361 on the SSO-PORT-CONV46-20261115
        # landing (sso_opus + sso_opus_notime25 rostered); the
        # turtle clone assertion below is unchanged.
        # GOING-LIVE-BASKETS-20261115: roster count 361 -> 366
        # GOING-LIVE-VARIATIONS-20261115: roster count 366 -> 381 (the 15 conversion variation sleeves rostered live).
        # PF-SPOT-VARIATIONS-20261116: roster count 381 -> 387 (the six free_kraken PF spot variations rostered live).
        # (the five overnight basket sleeves rostered live).
        rows = _rows()
        # T474U-CRYPTO-PORT-20261116: roster count 387 -> 396 (the nine t474u crypto twins rostered live).
        # SEGMENT-CONSTRUCTION-20261116: roster count 396 -> 398 (ls9_midday_short and b3_midday_fade_var rostered live).
        # CONV57-G4-VARIATION-20261116: roster count 398 -> 399 (aster_tensor_g4_varmk rostered live).
        # CONV123-REVIVAL-20261116: roster count 399 -> 400 (revival_basket rostered live).
        self.assertEqual(len(rows), 400)
        by_id = {r["id"]: r for r in rows}
        tur, don = by_id["aster_trader_turtle2010"], \
            by_id["aster_trader_donchian55"]
        diff = {k for k in set(tur) | set(don)
                if tur.get(k) != don.get(k)}
        self.assertEqual(diff, {"id", "module"})
        self.assertEqual(tur["module"],
                         "adapters3.aster_trader_turtle2010")

    def test_variation_registry_carries_the_falsifier(self):
        reg = json.loads(
            (ROOT / "config/conversion_variations_20261115.json")
            .read_text())
        # SSO-PORT-CONV46-20261115: the registry now carries two
        # variations; select this test's own (CONV-47) by id.
        (v,) = [x for x in reg["variations"] if x["conv"] == "CONV-47"]
        self.assertEqual(v["id"], "aster_trader_turtle2010")
        self.assertEqual(v["parent"], "aster_trader_donchian55")
        self.assertIn("First 20 forward fires", v["falsifier"])
        self.assertIn("donchian55 is untouched", v["kill_rule"])

    def test_turtle_enters_below_sma200_where_parent_cannot(self):
        from adapters3 import aster_trader_turtle2010 as tur
        from adapters3 import aster_trader_donchian55 as don
        closes = [300.0 - i * (200.0 / 259.0) for i in range(260)]
        closes[-1] = max(closes[-21:-1]) + 2.0
        view = _view({"SPY": _bars(closes)})
        t_out = tur.evaluate(view)
        entries = [i for i in t_out if i["kind"] == "entry"]
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["symbol"], "SPY")
        self.assertIn("stop_price", entries[0])
        d_out = don.evaluate(view)
        self.assertEqual(
            [i for i in d_out if i["kind"] == "entry"], [])

    def test_parent_behavior_unchanged_on_its_own_fixture(self):
        from adapters3 import aster_trader_donchian55 as don
        closes = [100.0] * 259 + [101.0]
        view = _view({"SPY": _bars(closes)})
        out = don.evaluate(view)
        entries = [i for i in out if i["kind"] == "entry"]
        self.assertEqual(len(entries), 1)
        self.assertTrue(entries[0]["reason"].startswith(
            "aster_trader_donchian55 entry: "
            "close > max(previous_55_high) and close > sma200"))


class TestParentsUntouched(unittest.TestCase):
    def test_parent_roster_rows_byte_identical(self):
        by_id = {r["id"]: r for r in _rows()}
        for pid, want in PARENT_ROW_SHA256.items():
            self.assertEqual(_row_sha(by_id[pid]), want, pid)

    def test_lazarus_engine_untouched(self):
        got = hashlib.sha256(
            (ROOT / "desk3/lazarus.py").read_bytes()).hexdigest()
        self.assertEqual(got, LAZARUS_PY_SHA256)

    def test_donchian_evaluator_sources_untouched(self):
        src = (ROOT / "desk3/aster_batch16.py").read_text()
        for fn, want in DONCHIAN_FN_SHA256.items():
            m = re.search(r"\ndef %s\(.*?(?=\ndef |\n# ---)" % fn,
                          src, re.S)
            self.assertIsNotNone(m, fn)
            got = hashlib.sha256(m.group(0).encode()).hexdigest()
            self.assertEqual(got, want, fn)


if __name__ == "__main__":
    unittest.main()
