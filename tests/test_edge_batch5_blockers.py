"""Edge batch 5 blockers (ENH-B5-*, 2026-10-24): second-look Edge pass
over aster_etf_spy_monthly_c098/m150, aster_link_nfs_norm_vol,
aster_native_btc_eth_sma200, aster_native_eth_sma200,
aster_open_gamma_a/b (VERIFY-ONLY), aster_pead_long_a/b,
aster_pead_vertical_a/b, aster_pub_enj_iu_body.

Each ENHANCED sleeve: treatment (switch ON, default) vs control
(switch OFF = pre-change rule exactly) on identical fixtures must
produce the named decision diff. Fail-first: every treatment
assertion fails on the pre-change engines (catch-up windows, the
opened_at deadline/stop derivations, per-leg warmup, and the
deadband do not exist there).
"""
import importlib, json, os, sys, tempfile, unittest
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
ET = ZoneInfo("America/New_York")
import desk3.aster_batch11  # registers SPY specs into aster_etf.SPECS


def ev(sid, view, ctx=None):
    return importlib.import_module(f"adapters3.{sid}").evaluate(
        view, ctx if ctx is not None else {"sleeve_id": sid,
        "state_dir": tempfile.mkdtemp(), "cycle_id": "fx"})


# ------------------------------------------------------------------ ETF
class TestEtfMonthlyCatchup(unittest.TestCase):
    def view(self, now, extra=None, positions=None):
        v = {"bars": {"SPY": [{"c": 100.0}] * 260}, "positions": positions or [],
             "quotes": {}, "now": now}
        if extra: v["extra"] = extra
        return v

    CTX = {"slice": {"capital_usd": 10000.0}}

    def test_catchup_fires_after_missed_window(self):
        for sid, qty in [("aster_etf_spy_monthly_c098", 98),
                         ("aster_etf_spy_monthly_m150", 150)]:
            o = ev(sid, self.view("2026-10-01T10:30:00"), self.CTX)
            self.assertEqual(len(o), 1, sid)
            self.assertEqual(o[0]["qty"], qty, sid)
            self.assertIn("ENH-B5-ETF-CATCHUP", o[0]["reason"], sid)
            self.assertEqual(o[0]["enhance_exp"]["control_intents"], 0, sid)

    def test_switch_off_restores_window_only(self):
        off = {"aster_etf_enh": {"catchup": False}}
        for sid in ("aster_etf_spy_monthly_c098", "aster_etf_spy_monthly_m150"):
            self.assertEqual(ev(sid, self.view("2026-10-01T10:30:00", off), self.CTX), [], sid)
            # and the designed window still fires with the switch OFF
            self.assertTrue(ev(sid, self.view("2026-10-01T09:36:00", off), self.CTX), sid)

    def test_catchup_buy_hold_flat_only_after_pending_and_never_same_month(self):
        # CR-1 (2026-11-11) supersedes the buy-hold half of the old
        # "never for buy hold" pin: the catch-up treatment now
        # covers flat BUY_HOLD initial allocations once their lagged
        # targets exist (that exclusion was the S1 defect: flat
        # buy-hold sleeves could never allocate the same session).
        # An unprimed first evaluation still emits nothing.
        import desk3.aster_etf as _ae
        _ae._PENDING_TARGETS.pop("aster_etf_spy_buy_hold", None)
        self.assertEqual(ev("aster_etf_spy_buy_hold",
                             self.view("2026-10-01T10:30:00"), self.CTX), [])
        _ae._PENDING_TARGETS["aster_etf_spy_buy_hold"] = {"SPY": 100}
        o = ev("aster_etf_spy_buy_hold",
               self.view("2026-10-01T10:30:00"), self.CTX)
        self.assertEqual(len(o), 1)
        self.assertIn("ENH-B5-ETF-CATCHUP", o[0]["reason"])
        p = [{"symbol": "SPY", "qty": 98, "avg_price": 100.0,
              "entry_date": "2026-10-01"}]
        self.assertEqual(ev("aster_etf_spy_monthly_c098",
                            self.view("2026-10-01T10:30:00", positions=p), self.CTX), [])

    def test_catchup_stops_at_1555(self):
        self.assertEqual(ev("aster_etf_spy_monthly_c098",
                            self.view("2026-10-01T16:05:00"), self.CTX), [])


# ------------------------------------------------------------------ LINK
NOW = datetime(2026, 10, 23, 16, 0, tzinfo=timezone.utc)


def link_bars(n=25):
    out = []
    for i in range(n):
        t = NOW - timedelta(hours=4 * (n - i))
        out.append({"t": t.isoformat(), "o": 10.0, "h": 10.5, "l": 9.5,
                    "c": 10.0, "v": 100000.0})
    return out


class TestLinkDeadlineDerived(unittest.TestCase):
    def view(self, hours_ago, extra=None):
        pos = [{"symbol": "LINKUSDT", "qty": 10.0, "avg_price": 20.0,
                "opened_at": (NOW - timedelta(hours=hours_ago)).isoformat()}]
        v = {"now": NOW.isoformat(), "bars": {"LINKUSDT|4Hour": link_bars()},
             "funding": {}, "positions": pos}
        if extra: v["extra"] = extra
        return v

    def test_deadline_fires_from_opened_at_without_funding(self):
        o = ev("aster_link_nfs_norm_vol", self.view(100))
        self.assertEqual([x["kind"] for x in o], ["exit"])
        self.assertIn("deadline_96h", o[0]["reason"])
        self.assertIn("ENH-B5-LINK-DEADLINE", o[0]["reason"])
        self.assertEqual(o[0]["enhance_exp"]["control_decision"],
                         "no_exit_hours_unknown")

    def test_switch_off_restores_field_only_rule(self):
        off = {"enh_aster_link_nfs_norm_vol": {"deadline_from_opened_at": False}}
        self.assertEqual(ev("aster_link_nfs_norm_vol", self.view(100, off)), [])

    def test_young_position_not_exited(self):
        self.assertEqual(ev("aster_link_nfs_norm_vol", self.view(10)), [])


# ------------------------------------------------------------------ PEAD
EPOCH = date(1970, 1, 1); START = date(2025, 1, 1)


def pbars(closes, start=START, vol=10000):
    return [{"t": float(((start + timedelta(days=i)) - EPOCH).days * 86400),
             "o": c, "h": c * 1.001, "l": c * .999, "c": c, "v": vol}
            for i, c in enumerate(closes)]


def pchain(sym="ACME", spot=50.0, dte=28):
    exp = (date(2025, 10, 6) + timedelta(days=dte)).isoformat()
    return [{"symbol": f"{sym}P", "underlying": sym, "right": "put",
             "expiry": exp, "strike": spot, "delta": -0.55, "bid": 0.35,
             "ask": 0.4, "bid_size": 50, "ask_size": 50},
            {"symbol": f"{sym}PW", "underlying": sym, "right": "put",
             "expiry": exp, "strike": spot - 5, "delta": -0.3, "bid": 0.2,
             "ask": 0.25, "bid_size": 50, "ask_size": 50}]


class TestPeadCatchup(unittest.TestCase):
    def view(self, extra=None):
        evv = {"symbol": "ACME", "event_id": "E1", "surprise": -0.05,
               "threshold": -0.02, "spot_at_signal": 50.0,
               "mean20_dollar_volume": 5000000,
               "entry_session": "2025-10-06", "event_date": "2025-10-01"}
        v = {"bars": {"ACME": pbars([50.0] * 30)}, "options": pchain(),
             "positions": [], "earnings_events": [evv]}
        if extra: v["extra"] = extra
        return v

    def ctx(self, sid, now):
        return {"sleeve_id": sid, "session": "2025-10-06", "now": now,
                "equity": 10000.0}

    def test_catchup_entry_same_session_all_four_books(self):
        for sid in ("aster_pead_long_a", "aster_pead_long_b",
                    "aster_pead_vertical_a", "aster_pead_vertical_b"):
            o = ev(sid, self.view(), self.ctx(sid, "2025-10-06T10:30:00"))
            self.assertEqual(len(o), 1, sid)
            self.assertEqual(o[0]["kind"], "entry", sid)
            self.assertIn("ENH-B5-PEAD-CATCHUP", o[0]["reason"], sid)

    def test_switch_off_restores_window_only(self):
        off = {"aster_b2_enh": {"pead_catchup": False}}
        for sid in ("aster_pead_long_a", "aster_pead_vertical_b"):
            self.assertEqual(ev(sid, self.view(off),
                                self.ctx(sid, "2025-10-06T10:30:00")), [], sid)
            self.assertEqual(len(ev(sid, self.view(off),
                                    self.ctx(sid, "2025-10-06T09:37:00"))), 1, sid)

    def test_catchup_does_not_extend_to_next_session(self):
        v = self.view(); v["earnings_events"][0]["entry_session"] = "2025-10-05"
        c = {"sleeve_id": "aster_pead_long_a", "session": "2025-10-06",
             "now": "2025-10-06T10:30:00", "equity": 10000.0}
        self.assertEqual(ev("aster_pead_long_a", v, c), [])


# ------------------------------------------------------------------ NATIVE
def daily(closes, sym):
    base = datetime(2025, 1, 1, tzinfo=timezone.utc)
    return {f"{sym}|1Day": [{"t": (base + timedelta(days=i)).isoformat(),
                             "o": c, "h": c * 1.001, "l": c * 0.999,
                             "c": c, "v": 100000} for i, c in enumerate(closes)]}


UP = [100 + 0.5 * i for i in range(210)]  # last close 204.5, above SMA200


class TestNativePairPerLeg(unittest.TestCase):
    def view(self, extra=None):
        bars = {}
        bars.update(daily(UP, "BTC-USD"))
        bars.update(daily(UP[:100], "ETH-USD"))  # ETH leg unqualified
        v = {"now": "2026-10-23T14:00:00+00:00", "bars": bars,
             "positions": [], "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0}}
        if extra: v["extra"] = extra
        return v

    def test_qualified_leg_trades_alone(self):
        o = ev("aster_native_btc_eth_sma200", self.view())
        # BROKER-422-ASTER-CRYPTO-20261027: broker dialect on emit.
        self.assertEqual([x["symbol"] for x in o], ["BTC/USD"])
        self.assertIn("ENH-B5-NATIVE-PERLEG", o[0]["reason"])

    def test_switch_off_restores_all_or_nothing(self):
        off = {"enh_aster_native_btc_eth_sma200": {"per_leg_warmup": False}}
        self.assertEqual(ev("aster_native_btc_eth_sma200", self.view(off)), [])


class TestNativeEthDeadband(unittest.TestCase):
    def view(self, extra=None):
        px = UP[-1]
        qty = 9960.0 / px
        v = {"now": "2026-10-23T14:00:00+00:00", "bars": daily(UP, "ETH-USD"),
             "positions": [{"symbol": "ETH-USD", "qty": qty, "avg_price": 200.0}],
             "slice": {"capital_usd": 10000.0, "cash_usd": 40.0}}
        if extra: v["extra"] = extra
        return v

    def test_dust_rebalance_refused(self):
        self.assertEqual(ev("aster_native_eth_sma200", self.view()), [])

    def test_switch_off_restores_dust_rebalance(self):
        off = {"enh_aster_native_eth_sma200": {"deadband": False}}
        o = ev("aster_native_eth_sma200", self.view(off))
        self.assertEqual(len(o), 1)
        self.assertLess(o[0]["qty"] * UP[-1], 50.0)  # the dust trade itself


# ------------------------------------------------------------------ ENJ
class TestEnjHeldBarsDerived(unittest.TestCase):
    def bars(self):
        bars = []
        for i in range(40):
            c = 20.0 if i < 30 else 24.0
            bars.append({"t": float(i * 14400), "o": c, "h": c + 0.5,
                         "l": c - 0.5, "c": c, "v": 1000.0})
        bars[-1] = {"t": float(39 * 14400), "o": 23.0, "h": 23.5,
                    "l": 20.8, "c": 23.0, "v": 1000.0}
        return bars

    def view(self, extra=None):
        pos = [{"symbol": "ENJUSDT", "qty": 400, "avg_price": 20.0,
                "opened_at": float(29 * 14400)}]  # no bars_held field
        v = {"bars": {"ENJUSDT|4Hour": self.bars()}, "positions": pos}
        if extra: v["extra"] = extra
        return v

    def test_atr_stop_fires_from_opened_at(self):
        o = ev("aster_pub_enj_iu_body", self.view(), {})
        self.assertEqual([x["kind"] for x in o], ["exit"])
        self.assertIn("atr_trailing_stop", o[0]["reason"])
        self.assertIn("ENH-B5-ENJ-HELDBARS", o[0]["reason"])

    def test_switch_off_restores_field_only_rule(self):
        off = {"enhance_held_bars": False}
        self.assertEqual(ev("aster_pub_enj_iu_body", self.view(off), {}), [])


# ------------------------------------------------------------------ GAMMA (verify-only)
SESS, PREV = "2026-10-23", "2026-10-22"
OPENED = datetime(2026, 10, 23, 9, 30, tzinfo=ET)
GNOW = datetime(2026, 10, 23, 9, 37, tzinfo=ET)


def iso(d):
    return d.astimezone(timezone.utc).isoformat()


def gamma_event(**kw):
    e = {"event_id": "E1", "symbol": "SPY", "session": SESS,
         "prior_afternoon_session": PREV,
         "first_5min_start_at": iso(OPENED),
         "first_5min_end_at": iso(OPENED + timedelta(minutes=5)),
         "first_5min_received_at": iso(OPENED + timedelta(minutes=5, seconds=1)),
         "break_market_at": iso(GNOW - timedelta(seconds=2)),
         "break_received_at": iso(GNOW - timedelta(seconds=1)),
         "R5_signal_at": iso(datetime(2026, 10, 22, 15, 0, tzinfo=ET)),
         "R5_received_at": iso(datetime(2026, 10, 22, 15, 1, tzinfo=ET)),
         "first_5min_low": 99.5, "observed_break_price": 99.0,
         "first_5min_return": -0.008, "causal_R5_prior_afternoon": True,
         "first_5min_complete": True, "source_sha256": "a" * 64}
    e.update(kw)
    return e


class TestGammaVerifyOnly(unittest.TestCase):
    def view(self, event, now=GNOW):
        chain = [{"symbol": "SPY261024P00099000", "underlying": "SPY",
                  "right": "put", "expiry": "2026-10-24", "strike": 99.0,
                  "delta": -0.55, "bid": 0.8, "ask": 0.9, "bid_size": 50,
                  "ask_size": 50}]
        return {"now": iso(now),
                "calendar": {"session": SESS, "previous_session": PREV,
                             "open": iso(OPENED), "verified": True},
                "opening_events": [event], "options": chain,
                "quotes": {"SPY": {"bid": 98.9, "ask": 99.1}},
                "positions": [], "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0},
                "market_open": True}

    def test_fresh_break_still_enters(self):
        self.assertEqual(len(ev("aster_open_gamma_a", self.view(gamma_event()))), 1)

    def test_stale_break_still_refused_causality_pinned(self):
        stale = gamma_event(break_market_at=iso(GNOW - timedelta(seconds=30)),
                            break_received_at=iso(GNOW - timedelta(seconds=29)))
        self.assertEqual(ev("aster_open_gamma_a", self.view(stale)), [])
        self.assertEqual(ev("aster_open_gamma_b", self.view(stale)), [])

    def test_verify_only_artifacts_recorded(self):
        for sid in ("aster_open_gamma_a", "aster_open_gamma_b"):
            p = os.path.join(ROOT, "proof", "enhance", f"{sid}.json")
            d = json.load(open(p))
            self.assertEqual(d["sleeve"], sid)
            self.assertEqual(d["disposition"], "VERIFY-ONLY")


if __name__ == "__main__":
    unittest.main()
