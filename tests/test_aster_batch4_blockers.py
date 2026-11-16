"""Blockers: Aster batch 4 (recovery VWAP20 vertical x4, XSP PCS x4,
public_recipe spot LINK/ENJ x2) — ASTER-B4-1.
Source: archive r19_options.py (recovery_signal VWAP20, select_xsp_legs,
_xsp, _weekly_atr14, _exit_intents) + options_rules.json books
OPT_VWAP20_VERTICAL_*, OPT_XSP_*; public_source_sleeves.py
source_features ai_volume / iu_body + their Pine sources.
Fail direction: pre-build none of adapters3.aster_rec_vwap20_vert_* /
aster_xsp_pcs_* / aster_pub_* exist (imports error)."""
import importlib, json, os, sys, unittest
from datetime import date, timedelta
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
EPOCH = date(1970, 1, 1); START = date(2025, 1, 1)


def ctx(sid, session="2025-10-06", now=None, **kw):
    c = {"sleeve_id": sid, "session": session,
         "now": now or (session + "T09:37:00"), "equity": 10000.0}
    c.update(kw); return c


def ev(sid, view, c=None):
    return importlib.import_module(f"adapters3.{sid}").evaluate(view, c or ctx(sid))


# ------------------------------------------------------------- recovery
def vwap_bars():
    """210 daily bars: uptrend (close>SMA200) with the last close dipped
    to <= 98% of VWAP20 (19 flat bars at 300, final 300/293/293)."""
    out = []
    closes = [100 + (199 * i / 189) for i in range(190)] + [300.0] * 19
    for i, c in enumerate(closes):
        out.append({"t": float(((START + timedelta(days=i)) - EPOCH).days * 86400),
                    "o": c, "h": c, "l": c, "c": c, "v": 10000.0})
    out.append({"t": float(((START + timedelta(days=209)) - EPOCH).days * 86400),
                "o": 300.0, "h": 300.0, "l": 293.0, "c": 293.0, "v": 10000.0})
    return out


def vwap_chain(long_ask=0.50, long_bid=0.45, wing_bid=0.25, wing_ask=0.30):
    exp = "2025-10-23"
    return [
        {"symbol": "SPY251023C00295000", "underlying": "SPY", "right": "call",
         "expiry": exp, "strike": 295.0, "delta": 0.55, "bid": long_bid,
         "ask": long_ask, "bid_size": 50, "ask_size": 50},
        {"symbol": "SPY251023C00300000", "underlying": "SPY", "right": "call",
         "expiry": exp, "strike": 300.0, "delta": 0.30, "bid": wing_bid,
         "ask": wing_ask, "bid_size": 50, "ask_size": 50}]


def vwap_pos(held=0, entry_spot=293.0):
    legs = [{"symbol": "SPY251023C00295000", "underlying": "SPY", "right": "call",
             "expiry": "2025-10-23", "strike": 295.0, "ratio": 1},
            {"symbol": "SPY251023C00300000", "underlying": "SPY", "right": "call",
             "expiry": "2025-10-23", "strike": 300.0, "ratio": -1}]
    return [{"symbol": "SPY251023C00295000", "qty": 2, "avg_price": 0.25,
             "entry_spot": entry_spot, "sessions_held": held, "legs": legs,
             "opened_at": "2025-10-06"}]


class TestRecoveryVWAP(unittest.TestCase):
    def view(self, chain=None):
        return {"bars": {"SPY": vwap_bars()}, "options": chain or vwap_chain(),
                "positions": []}

    def test_entry_all_four_books(self):
        for sid in ("aster_rec_vwap20_vert_fixed_a", "aster_rec_vwap20_vert_fixed_b",
                    "aster_rec_vwap20_vert_touch_a", "aster_rec_vwap20_vert_touch_b"):
            out = ev(sid, self.view())
            self.assertEqual(len(out), 1, sid)
            self.assertEqual(out[0]["kind"], "entry")
            self.assertEqual(len(out[0]["legs"]), 2)  # vertical
            self.assertEqual(out[0]["legs"][0]["position_intent"], "buy_to_open")
            self.assertEqual(out[0]["legs"][1]["position_intent"], "sell_to_open")

    def test_sizing_a_exceeds_b(self):
        a = ev("aster_rec_vwap20_vert_fixed_a", self.view())
        b = ev("aster_rec_vwap20_vert_fixed_b", self.view())
        self.assertEqual(a[0]["qty"], 7)   # $200 risk / $26.30 per pkg
        self.assertEqual(b[0]["qty"], 1)   # $50 risk / $26.30 per pkg

    def test_refusals(self):
        warm = {"bars": {"SPY": vwap_bars()[:100]}, "options": vwap_chain(), "positions": []}
        self.assertEqual(ev("aster_rec_vwap20_vert_fixed_a", warm), [])  # <200 sessions
        flat = vwap_bars()
        for x in flat:  # no dip: last close = 300 > 98% VWAP
            pass
        nodip = [dict(x) for x in vwap_bars()]
        nodip[-1].update({"h": 300.0, "l": 300.0, "c": 300.0})
        self.assertEqual(ev("aster_rec_vwap20_vert_fixed_a",
                            {"bars": {"SPY": nodip}, "options": vwap_chain(), "positions": []}), [])
        self.assertEqual(ev("aster_rec_vwap20_vert_fixed_a",
                            {"bars": {"SPY": vwap_bars()}, "options": [], "positions": []}), [])
        wide = vwap_chain(long_ask=4.0, long_bid=3.8, wing_bid=0.5, wing_ask=0.6)
        self.assertEqual(ev("aster_rec_vwap20_vert_fixed_a",
                            {"bars": {"SPY": vwap_bars()}, "options": wide, "positions": []}), [])  # debit/width .7 > .6

    def test_exit_planned_and_fixed_not_touch(self):
        v = {"bars": {"SPY": vwap_bars()}, "options": vwap_chain(),
             "positions": vwap_pos(held=5)}
        out = ev("aster_rec_vwap20_vert_fixed_a", v)
        self.assertEqual([o["kind"] for o in out], ["exit"])
        self.assertIn("planned", out[0]["reason"])
        v2 = {"bars": {"SPY": vwap_bars()}, "options": vwap_chain(),
              "positions": vwap_pos(held=2)}
        self.assertEqual(ev("aster_rec_vwap20_vert_fixed_a", v2), [])  # dip bar close 293 < entry*1.02 and fixed anyway

    def test_exit_touch(self):
        bars = [dict(x) for x in vwap_bars()]
        bars[-1].update({"h": 300.0, "l": 299.0, "c": 300.0})  # 300 >= 293*1.02
        v = {"bars": {"SPY": bars}, "options": vwap_chain(),
             "positions": vwap_pos(held=2)}
        out = ev("aster_rec_vwap20_vert_touch_a", v)
        self.assertEqual([o["kind"] for o in out], ["exit"])
        self.assertIn("touch", out[0]["reason"])
        self.assertEqual(ev("aster_rec_vwap20_vert_fixed_a", v), [])  # fixed does NOT touch-exit


# ------------------------------------------------------------------ XSP
def xsp_weekly():
    fridays = [date(2025, 10, 3) - timedelta(days=7 * i) for i in range(20)][::-1]
    out = []
    for i, f in enumerate(fridays):
        c = 560.0 + 2 * i
        out.append({"week_end": f.isoformat(), "o": c - 1, "h": c + 5,
                    "l": c - 5, "c": c, "complete": True})
    return out


def xsp_chain(short_bid=4.0, long_ask=1.5, adj_lo_mid=6.0, adj_hi_mid=7.0):
    out = []
    for k in range(560, 605, 5):
        bid, ask = 1.0, 1.2
        if k == 590: bid, ask = short_bid, short_bid + 0.2
        if k == 585: bid, ask = long_ask - 0.2, long_ask
        if k == 580: bid, ask = long_ask - 0.2, long_ask
        if k == 595: bid, ask = adj_lo_mid - 0.2, adj_lo_mid + 0.2
        if k == 600: bid, ask = adj_hi_mid - 0.2, adj_hi_mid + 0.2
        out.append({"symbol": f"XSP251010P{k}", "underlying": "XSP",
                    "right": "put", "expiry": "2025-10-10", "strike": float(k),
                    "bid": bid, "ask": ask, "bid_size": 50, "ask_size": 50})
    return out


def xsp_view(digital_hist=0.30, **kw):
    hist = [{"week_end": (date(2025, 10, 3) - timedelta(days=7 * (i + 1))).isoformat(),
             "value": digital_hist} for i in range(30)]
    return {"options": xsp_chain(**kw), "positions": [],
            "calendar": {"first_session_of_week": True, "session": "2025-10-06",
                         "previous_session": "2025-10-03",
                         "weekly_pm_expiry": "2025-10-10"},
            "xsp_state": {"weekly_bars": xsp_weekly(), "prior_digitals": hist,
                          "adjacent_put_symbols": ["XSP251010P595", "XSP251010P600"]}}


def xsp_ctx(sid, now="2025-10-06T10:02:00"):
    return ctx(sid, session="2025-10-06", now=now)


def xsp_pos(expiry="2025-10-10"):
    legs = [{"symbol": "XSP251010P585", "underlying": "XSP", "right": "put",
             "expiry": expiry, "strike": 585.0, "ratio": 1,
             "exercise_style": "european"},
            {"symbol": "XSP251010P590", "underlying": "XSP", "right": "put",
             "expiry": expiry, "strike": 590.0, "ratio": -1,
             "exercise_style": "european"}]
    return [{"symbol": "XSP251010P590", "qty": 1, "avg_price": 2.5,
             "entry_spot": 598.0, "legs": legs, "opened_at": "2025-10-06"}]


class TestXSP(unittest.TestCase):
    def test_entry_calm_a(self):
        out = ev("aster_xsp_pcs_calm_a", xsp_view(), xsp_ctx("aster_xsp_pcs_calm_a"))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["kind"], "entry")
        strikes = sorted(l["strike"] for l in out[0]["legs"])
        self.assertEqual(strikes, [585.0, 590.0])  # short 590 target, calm width exactly 5
        self.assertEqual(out[0]["qty"], 1)         # $300 risk / $251.30 max loss

    def test_entry_calm_b_unaffordable_then_cheap(self):
        self.assertEqual(ev("aster_xsp_pcs_calm_b", xsp_view(), xsp_ctx("aster_xsp_pcs_calm_b")), [])
        cheap = xsp_view(short_bid=4.6, long_ask=0.4)  # credit 4.20, loss $81.30
        out = ev("aster_xsp_pcs_calm_b", cheap, xsp_ctx("aster_xsp_pcs_calm_b"))
        self.assertEqual(len(out), 1); self.assertEqual(out[0]["qty"], 1)
        a = ev("aster_xsp_pcs_calm_a", cheap, xsp_ctx("aster_xsp_pcs_calm_a"))
        self.assertEqual(a[0]["qty"], 3)  # $300 / $81.30

    def test_graded_between_median_and_p75(self):
        v = xsp_view()
        hist = ([{"week_end": (date(2025, 10, 3) - timedelta(days=7 * (i + 1))).isoformat(),
                  "value": 0.25} for i in range(15)]
                + [{"week_end": (date(2025, 10, 3) - timedelta(days=7 * (i + 16))).isoformat(),
                    "value": 0.45} for i in range(15)])
        v["xsp_state"]["prior_digitals"] = hist  # median .35, p75 .45
        v["options"] = xsp_chain(adj_lo_mid=6.0, adj_hi_mid=8.0)  # digital .40
        for c in v["options"]:  # graded legs are 585 short / 580 long here
            if c["strike"] == 585.0: c["bid"], c["ask"] = 4.0, 4.2
            if c["strike"] == 580.0: c["bid"], c["ask"] = 1.3, 1.5
        self.assertEqual(ev("aster_xsp_pcs_calm_a", v, xsp_ctx("aster_xsp_pcs_calm_a")), [])
        out = ev("aster_xsp_pcs_graded_a", v, xsp_ctx("aster_xsp_pcs_graded_a"))
        self.assertEqual(len(out), 1)
        self.assertEqual(sorted(l["strike"] for l in out[0]["legs"]), [580.0, 585.0])

    def test_refusals(self):
        hot = xsp_view(adj_lo_mid=6.0, adj_hi_mid=7.75)  # digital .35 >= p75 .30
        self.assertEqual(ev("aster_xsp_pcs_calm_a", hot, xsp_ctx("aster_xsp_pcs_calm_a")), [])
        self.assertEqual(ev("aster_xsp_pcs_graded_a", hot, xsp_ctx("aster_xsp_pcs_graded_a")), [])
        v = xsp_view()
        self.assertEqual(ev("aster_xsp_pcs_calm_a", v, xsp_ctx("aster_xsp_pcs_calm_a", now="2025-10-06T10:06:00")), [])  # window
        v2 = xsp_view(); v2["calendar"]["first_session_of_week"] = False
        self.assertEqual(ev("aster_xsp_pcs_calm_a", v2, xsp_ctx("aster_xsp_pcs_calm_a")), [])
        v3 = xsp_view(); v3["xsp_state"]["prior_digitals"] = v3["xsp_state"]["prior_digitals"][:20]
        self.assertEqual(ev("aster_xsp_pcs_calm_a", v3, xsp_ctx("aster_xsp_pcs_calm_a")), [])  # <26 digitals
        v4 = xsp_view(); v4["xsp_state"]["weekly_bars"][-1]["week_end"] = "2025-09-25"
        self.assertEqual(ev("aster_xsp_pcs_calm_a", v4, xsp_ctx("aster_xsp_pcs_calm_a")), [])  # stale weekly state

    def test_settle_exit_only_at_expiry(self):
        v = xsp_view(); v["positions"] = xsp_pos()
        self.assertEqual(ev("aster_xsp_pcs_calm_a", v, ctx("aster_xsp_pcs_calm_a", session="2025-10-08", now="2025-10-08T12:00:00")), [])
        out = ev("aster_xsp_pcs_calm_a", v, ctx("aster_xsp_pcs_calm_a", session="2025-10-10", now="2025-10-10T16:05:00"))
        self.assertEqual([o["kind"] for o in out], ["exit"])
        self.assertTrue(out[0]["settle"]); self.assertIn("official_PM_expiry", out[0]["reason"])


# ------------------------------------------------------------- public spot
def spot_bars(sym_last, n=60, base=None):
    out = []
    for i in range(n - 1):
        b = dict(base or {"o": 20.0, "h": 20.2, "l": 19.8, "c": 20.0, "v": 1000.0})
        b["t"] = float(i * 14400); out.append(b)
    last = dict(sym_last); last["t"] = float((n - 1) * 14400); out.append(last)
    return out


class TestPublicSpot(unittest.TestCase):
    def test_link_entry(self):
        bars = spot_bars({"o": 20.5, "h": 21.2, "l": 20.4, "c": 21.0, "v": 3000.0})
        out = ev("aster_pub_link_ai_volume", {"bars": {"LINKUSDT|4Hour": bars}, "positions": []})
        self.assertEqual(len(out), 1); self.assertEqual(out[0]["kind"], "entry")
        self.assertEqual(out[0]["qty"], 476)  # 100% of $10k slice / 21.0
        self.assertEqual(out[0]["symbol"], "LINKUSDT")

    def test_link_refusals(self):
        bars = spot_bars({"o": 20.5, "h": 21.2, "l": 20.4, "c": 21.0, "v": 1500.0})
        self.assertEqual(ev("aster_pub_link_ai_volume", {"bars": {"LINKUSDT|4Hour": bars}, "positions": []}), [])  # no spike
        bear = spot_bars({"o": 20.5, "h": 20.6, "l": 19.0, "c": 19.5, "v": 3000.0})
        self.assertEqual(ev("aster_pub_link_ai_volume", {"bars": {"LINKUSDT|4Hour": bear}, "positions": []}), [])  # bearish is NOT a short entry (long-only spot)
        short_hist = spot_bars({"o": 20.5, "h": 21.2, "l": 20.4, "c": 21.0, "v": 3000.0}, n=30)
        self.assertEqual(ev("aster_pub_link_ai_volume", {"bars": {"LINKUSDT|4Hour": short_hist}, "positions": []}), [])  # warmup <50

    def test_link_exits(self):
        pos = [{"symbol": "LINKUSDT", "qty": 476, "avg_price": 20.0, "bars_held": 5}]
        flat = spot_bars({"o": 20.0, "h": 20.2, "l": 19.8, "c": 20.0, "v": 1000.0})
        out = ev("aster_pub_link_ai_volume", {"bars": {"LINKUSDT|4Hour": flat}, "positions": pos})
        self.assertEqual([o["kind"] for o in out], ["exit"]); self.assertIn("bars5", out[0]["reason"])
        pos2 = [{"symbol": "LINKUSDT", "qty": 476, "avg_price": 20.0, "bars_held": 2}]
        bear = spot_bars({"o": 20.5, "h": 20.6, "l": 19.0, "c": 19.5, "v": 3000.0})
        out = ev("aster_pub_link_ai_volume", {"bars": {"LINKUSDT|4Hour": bear}, "positions": pos2})
        self.assertEqual([o["kind"] for o in out], ["exit"]); self.assertIn("counterpart", out[0]["reason"])

    def test_enj_entry_and_refusal(self):
        bars = spot_bars({"o": 20.0, "h": 25.2, "l": 19.9, "c": 25.0, "v": 1000.0}, n=30,
                         base={"o": 20.0, "h": 20.3, "l": 19.9, "c": 20.1, "v": 1000.0})
        out = ev("aster_pub_enj_iu_body", {"bars": {"ENJUSDT|4Hour": bars}, "positions": []})
        self.assertEqual(len(out), 1); self.assertEqual(out[0]["qty"], 400)
        small = spot_bars({"o": 20.0, "h": 20.6, "l": 19.9, "c": 20.5, "v": 1000.0}, n=30,
                          base={"o": 20.0, "h": 20.3, "l": 19.9, "c": 20.1, "v": 1000.0})
        self.assertEqual(ev("aster_pub_enj_iu_body", {"bars": {"ENJUSDT|4Hour": small}, "positions": []}), [])

    def test_enj_opposite_exit(self):
        pos = [{"symbol": "ENJUSDT", "qty": 400, "avg_price": 20.0, "bars_held": 2}]
        bear = spot_bars({"o": 25.0, "h": 25.2, "l": 19.9, "c": 20.0, "v": 1000.0}, n=30,
                         base={"o": 20.0, "h": 20.3, "l": 19.9, "c": 20.1, "v": 1000.0})
        out = ev("aster_pub_enj_iu_body", {"bars": {"ENJUSDT|4Hour": bear}, "positions": pos})
        self.assertEqual([o["kind"] for o in out], ["exit"]); self.assertIn("opposite", out[0]["reason"])

    def test_enj_atr_trailing_exit(self):
        bars = []
        for i in range(40):
            c = 20.0 if i < 30 else 24.0
            bars.append({"t": float(i * 14400), "o": c, "h": c + 0.5, "l": c - 0.5,
                         "c": c, "v": 1000.0})
        bars[-1] = {"t": float(39 * 14400), "o": 23.0, "h": 23.5, "l": 20.8, "c": 23.0, "v": 1000.0}
        pos = [{"symbol": "ENJUSDT", "qty": 400, "avg_price": 20.0, "bars_held": 10}]
        out = ev("aster_pub_enj_iu_body", {"bars": {"ENJUSDT|4Hour": bars}, "positions": pos})
        self.assertEqual([o["kind"] for o in out], ["exit"]); self.assertIn("atr_trailing_stop", out[0]["reason"])
        bars[-1] = {"t": float(39 * 14400), "o": 23.0, "h": 23.5, "l": 22.5, "c": 23.0, "v": 1000.0}
        self.assertEqual(ev("aster_pub_enj_iu_body", {"bars": {"ENJUSDT|4Hour": bars}, "positions": pos}), [])


# ------------------------------------------------------------------ E2E
class TestRegistryAndE2E(unittest.TestCase):
    IDS = ["aster_rec_vwap20_vert_fixed_a", "aster_rec_vwap20_vert_fixed_b",
           "aster_rec_vwap20_vert_touch_a", "aster_rec_vwap20_vert_touch_b",
           "aster_xsp_pcs_calm_a", "aster_xsp_pcs_calm_b",
           "aster_xsp_pcs_graded_a", "aster_xsp_pcs_graded_b",
           "aster_pub_link_ai_volume", "aster_pub_enj_iu_body"]

    def test_config_rows_and_inputs(self):
        cfg = {s["id"]: s for s in json.load(open(os.path.join(ROOT, "config/sleeves.json")))["sleeves"]}
        for sid in self.IDS:
            self.assertIn(sid, cfg)
            self.assertEqual(cfg[sid]["slice"]["capital_usd"], 10000.0)
            self.assertEqual(cfg[sid]["module"], f"adapters3.{sid}")
        self.assertIn("xsp_state", cfg["aster_xsp_pcs_calm_a"]["inputs"])

    def test_xsp_unfed_without_regime_producer(self):
        from desk3.registry import Registry
        from desk3.aster_b4 import PRODUCERS_XSP
        reg = Registry()
        for p in PRODUCERS_XSP:
            if p["name"] not in reg.producers:
                reg.register_producer(p["name"], p["outputs"], p["freshness_sla_s"])
        reg.register_sleeve("aster_xsp_pcs_calm_a", ("options", "positions", "xsp_state"))
        reg.mark_produced("bars", ts=1000.0); reg.mark_produced("options_chain", ts=1000.0)
        reg.mark_produced("broker_readback", ts=1000.0)
        fed = reg.fed_states(now=1100.0)
        self.assertEqual(fed["aster_xsp_pcs_calm_a"]["state"], "UNFED")
        self.assertIn("xsp_state", fed["aster_xsp_pcs_calm_a"]["missing"])

    def test_e2e_recovery_round_trip(self):
        from desk3.broker import FakeBroker
        b = FakeBroker(prices={"SPY251023C00295000": 0.5, "SPY251023C00300000": 0.3})
        e = ev("aster_rec_vwap20_vert_fixed_a",
               {"bars": {"SPY": vwap_bars()}, "options": vwap_chain(), "positions": []})[0]
        for leg in e["legs"]:
            b.submit_order(f"v3-b4-e-{leg['symbol']}", leg["symbol"], leg["side"], e["qty"], "market")
            b.get_order_by_client_id(f"v3-b4-e-{leg['symbol']}")
        self.assertNotEqual(b.get_positions(), {})
        x = ev("aster_rec_vwap20_vert_fixed_a",
               {"bars": {"SPY": vwap_bars()}, "options": vwap_chain(),
                "positions": vwap_pos(held=5)})[0]
        self.assertEqual(x["kind"], "exit")
        for leg in x["legs"]:
            b.submit_order(f"v3-b4-x-{leg['symbol']}", leg["symbol"], leg["side"], e["qty"], "market")
            b.get_order_by_client_id(f"v3-b4-x-{leg['symbol']}")
        self.assertEqual(b.get_positions(), {})

    def test_e2e_xsp_round_trip_to_settle(self):
        from desk3.broker import FakeBroker
        b = FakeBroker(prices={"XSP251010P590": 4.1, "XSP251010P585": 1.4})
        e = ev("aster_xsp_pcs_calm_a", xsp_view(), xsp_ctx("aster_xsp_pcs_calm_a"))[0]
        for leg in e["legs"]:
            b.submit_order(f"v3-b4-e-{leg['symbol']}", leg["symbol"], leg["side"], e["qty"], "market")
            b.get_order_by_client_id(f"v3-b4-e-{leg['symbol']}")
        self.assertNotEqual(b.get_positions(), {})
        v = xsp_view(); v["positions"] = xsp_pos()
        s = ev("aster_xsp_pcs_calm_a", v,
               ctx("aster_xsp_pcs_calm_a", session="2025-10-10", now="2025-10-10T16:05:00"))[0]
        self.assertTrue(s["settle"])
        for leg in s["legs"]:  # settlement closes both legs on the paper book
            b.submit_order(f"v3-b4-s-{leg['symbol']}", leg["symbol"], leg["side"], s["qty"], "market")
            b.get_order_by_client_id(f"v3-b4-s-{leg['symbol']}")
        self.assertEqual(b.get_positions(), {})

    def test_e2e_link_round_trip(self):
        from desk3.broker import FakeBroker
        b = FakeBroker(prices={"LINKUSDT": 21.0})
        bars = spot_bars({"o": 20.5, "h": 21.2, "l": 20.4, "c": 21.0, "v": 3000.0})
        e = ev("aster_pub_link_ai_volume", {"bars": {"LINKUSDT|4Hour": bars}, "positions": []})[0]
        b.submit_order("v3-b4-link-e", "LINKUSDT", "buy", e["qty"], "market")
        b.get_order_by_client_id("v3-b4-link-e")
        self.assertNotEqual(b.get_positions(), {})
        pos = [{"symbol": "LINKUSDT", "qty": e["qty"], "avg_price": 21.0, "bars_held": 5}]
        x = ev("aster_pub_link_ai_volume", {"bars": {"LINKUSDT|4Hour": bars}, "positions": pos})[0]
        b.submit_order("v3-b4-link-x", "LINKUSDT", "sell", x["qty"], "market")
        b.get_order_by_client_id("v3-b4-link-x")
        self.assertEqual(b.get_positions(), {})


if __name__ == "__main__":
    unittest.main()
