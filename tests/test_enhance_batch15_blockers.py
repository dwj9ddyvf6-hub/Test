"""ENH2 batch-15 blockers (Edge pass, second look).

ENHANCED (adapter-layer gates in desk3/enhance15.py, wired into the
v3 worker entrypoints only — the sha-pinned sleeves/ and adapters/
files and the line-pinned desk3/strategies/ files are untouched):
  ema_vwap stale_bar_gate, ema_vwap_options short_leg_spread_gate,
  free_kraken_ada_basis + free_kraken_link_basis pair_freshness_gate,
  free_kraken_enj_spot book_freshness_gate.
Each A/B drive proves the fail direction: gate ON refuses the leaky
entry, gate OFF (switch) restores the pre-change entry exactly, and
a fresh input enters with the gate ON.

VERIFY-ONLY probes (no code change): the seven remaining sleeves'
binding-leak class is already gated by their first Edge pass; each
probe drives the existing gate fresh (enters) vs stale/invalid
(refuses) to prove no second binding leak of that class remains.
"""
import importlib, os, sys, tempfile, unittest
from datetime import date, datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def drive(sid, bars=None, now="2026-10-23T15:00:00-04:00", extra=None,
          positions=None, params=None, capital=100000.0):
    mod = importlib.import_module(f"adapters3.{sid}")
    p = dict(params or {})
    if extra is not None:
        p["extra"] = extra
    view = {"now": now, "bars": bars or {}, "positions": positions or [],
            "slice": {"capital_usd": capital, "cash_usd": capital},
            "params": p, "session_fills": []}
    ctx = {"state_dir": tempfile.mkdtemp(prefix=f"b15-{sid}-"),
           "sleeve_id": sid, "cycle_id": "fixture"}
    return mod.evaluate(view, ctx)


def ev3(sid, now, extra=None, positions=None, bars=None):
    mod = importlib.import_module(f"desk3.sleeves.{sid}")
    view = {"now": now, "extra": extra or {}, "positions": positions or [],
            "bars": bars or {},
            "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0}}
    return mod.evaluate(view, {"sleeve_id": sid})


def biz_days(end, n):
    days, d = [], end
    while len(days) < n:
        if d.weekday() < 5:
            days.append(d)
        d -= timedelta(days=1)
    return sorted(days)


def daily(end, closes, vol=1000.0, last_hl=None):
    days = biz_days(end, len(closes))
    out = []
    for d, c in zip(days, closes):
        h = l = c
        if last_hl and d == days[-1]:
            h, l = last_hl
        out.append({"t": f"{d.isoformat()}T00:00:00Z", "o": float(c),
                    "h": float(h), "l": float(l), "c": float(c), "v": vol})
    return out


END = date(2026, 10, 22)
XYZ_BARS = daily(END, [100.0] * 34 + [97.0], last_hl=(100.0, 96.0))
OPT_CHAIN = {"XYZ": [
    {"symbol": "XYZ261112C00095000", "strike": 95.0, "expiration": "2026-11-12"},
    {"symbol": "XYZ261112C00105000", "strike": 105.0, "expiration": "2026-11-12"}]}
OPT_QUOTES = {"XYZ261112C00095000": {"bid": 1.95, "ask": 2.0},
              "XYZ261112C00105000": {"bid": 0.5, "ask": 0.6}}


def entries(out):
    return [i for i in out if i["kind"] == "entry"]


DEEP_BARS = daily(END, [100.0] * 34 + [90.0], last_hl=(100.0, 89.0))


class TestEmaVwapStaleBar(unittest.TestCase):
    def test_stale_bar_refused_on_enters_off_and_fresh(self):
        # 10% deviation: passes the v1 geometry gate, isolating ENH2.
        stale_now = "2026-11-20T15:00:00-05:00"  # last bar 29 days old
        out = drive("ema_vwap", {"XYZ|1Day": DEEP_BARS}, now=stale_now, params={"symbols": ["XYZ"]})
        self.assertEqual(entries(out), [])
        out = drive("ema_vwap", {"XYZ|1Day": DEEP_BARS}, now=stale_now, params={"symbols": ["XYZ"]},
                    extra={"ema_vwap_enh2": {"stale_bar_gate": False}})
        self.assertEqual(len(entries(out)), 1)
        out = drive("ema_vwap", {"XYZ|1Day": DEEP_BARS}, params={"symbols": ["XYZ"]})
        self.assertEqual(len(entries(out)), 1)


class TestEmaVwapOptionsShortLeg(unittest.TestCase):
    def test_blown_short_leg_refused_on_enters_off(self):
        quotes = dict(OPT_QUOTES)
        quotes["XYZ261112C00105000"] = {"bid": 0.05, "ask": 0.95}
        kw = dict(params={"symbols": ["XYZ"]},
                  extra={"chains": OPT_CHAIN, "quotes": quotes})
        self.assertEqual(entries(drive("ema_vwap_options",
                                       {"XYZ|1Day": XYZ_BARS}, **kw)), [])
        kw["extra"] = {"chains": OPT_CHAIN, "quotes": quotes,
                       "ema_vwap_options_enh2": {"short_leg_spread_gate": False}}
        self.assertEqual(len(entries(drive("ema_vwap_options",
                                           {"XYZ|1Day": XYZ_BARS}, **kw))), 2)
        out = drive("ema_vwap_options", {"XYZ|1Day": XYZ_BARS},
                    params={"symbols": ["XYZ"]},
                    extra={"chains": OPT_CHAIN, "quotes": OPT_QUOTES})
        self.assertEqual(len(entries(out)), 2)


def _basis_extra(t0, bps_list, bid, ask, spot=0.20):
    series = [{"t": t0 + i * 14400, "spot_close": spot,
               "perp_close": spot * (1 + b / 10000.0)}
              for i, b in enumerate(bps_list)]
    return {"basis": {"aligned": 3, "required": 3,
                      "decision": {"status": "READY", "reason": "fixture"},
                      "series": series},
            "quote": {"bid": bid, "ask": ask}}


class TestAdaBasisPairFreshness(unittest.TestCase):
    T0 = datetime(2026, 10, 23, 0, 0, tzinfo=timezone.utc).timestamp()

    def test_stale_pair_refused_on_enters_off_and_fresh(self):
        bid = 0.20 * 1.004
        extra = _basis_extra(self.T0, [0, 0, 40], bid, bid * 1.001)
        stale_now = datetime.fromtimestamp(
            self.T0 + 72 * 3600, tz=timezone.utc).isoformat()
        self.assertEqual(drive("free_kraken_ada_basis", {}, now=stale_now,
                               extra=extra), [])
        off = dict(extra)
        off["free_kraken_ada_basis_enh2"] = {"pair_freshness_gate": False}
        self.assertEqual(len(entries(drive(
            "free_kraken_ada_basis", {}, now=stale_now, extra=off))), 1)
        fresh_now = datetime.fromtimestamp(
            self.T0 + 12 * 3600, tz=timezone.utc).isoformat()
        self.assertEqual(len(entries(drive(
            "free_kraken_ada_basis", {}, now=fresh_now, extra=extra))), 1)


class TestLinkBasisPairFreshness(unittest.TestCase):
    T0 = datetime(2026, 10, 23, tzinfo=timezone.utc).timestamp()

    def _extra(self, bps, **kw):
        series = [{"t": self.T0 + i * 14400, "spot_close": 11.0,
                   "perp_close": 11.0 * (1 + b / 10000)}
                  for i, b in enumerate(bps)]
        ex = {"basis": {"aligned": 3, "required": 3,
                        "decision": {"status": "READY", "reason": "fixture"},
                        "series": series},
              "quote": {"bid": 11.044, "ask": 11.055}}
        ex.update(kw)
        return ex

    def test_stale_pair_refused_on_enters_off_and_fresh(self):
        stale_now = datetime.fromtimestamp(
            self.T0 + 72 * 3600, tz=timezone.utc).isoformat()
        self.assertEqual(ev3("free_kraken_link_basis", stale_now,
                             extra=self._extra([0, 0, 40])), [])
        off = self._extra([0, 0, 40],
                          free_kraken_link_basis_enh2={"pair_freshness_gate": False})
        self.assertEqual(len(entries(ev3(
            "free_kraken_link_basis", stale_now, extra=off))), 1)
        fresh_now = datetime.fromtimestamp(
            self.T0 + 12 * 3600, tz=timezone.utc).isoformat()
        self.assertEqual(len(entries(ev3(
            "free_kraken_link_basis", fresh_now,
            extra=self._extra([0, 0, 40])))), 1)


class TestEnjBookFreshness(unittest.TestCase):
    NOW = "2026-10-23T12:00:00+00:00"
    NOW_TS = datetime(2026, 10, 23, 12, 0, tzinfo=timezone.utc).timestamp()

    def _book(self, ts):
        return {"bids": [[str(1.0), str(300), int(ts)]],
                "asks": [[str(1.001), str(100), int(ts)]]}

    def test_stale_book_refused_on_enters_off_and_fresh(self):
        stale = {"book": self._book(self.NOW_TS - 7200)}
        self.assertEqual(ev3("free_kraken_enj_spot", self.NOW, extra=stale), [])
        off = {"book": self._book(self.NOW_TS - 7200),
               "free_kraken_enj_spot_enh2": {"book_freshness_gate": False}}
        self.assertEqual(len(entries(ev3(
            "free_kraken_enj_spot", self.NOW, extra=off))), 1)
        fresh = {"book": self._book(self.NOW_TS)}
        self.assertEqual(len(entries(ev3(
            "free_kraken_enj_spot", self.NOW, extra=fresh))), 1)


# ------------------------------------------------------- VERIFY probes
def _kraken_bars(sym_close=1.5):
    start = datetime(2026, 10, 19, 0, 0, tzinfo=timezone.utc)
    out = []
    for i in range(24):
        t = start + timedelta(hours=4 * i)
        c = 1.5 if i == 23 else 2.0
        lo = 1.4 if i == 23 else 1.9
        out.append({"t": t.strftime("%Y-%m-%dT%H:%M:%SZ"), "o": 2.0,
                    "h": 2.1, "l": lo, "c": c, "v": 100.0})
    return out


KRAKEN_NOW = "2026-10-23T04:00:00+00:00"
KRAKEN_QUOTE = {"quote": {"bid": 1.49, "ask": 1.51}}


class TestVerifyCrowdedFreshnessGates(unittest.TestCase):
    def _rates(self, latest_age_h):
        now_dt = datetime(2026, 10, 23, 4, 0, tzinfo=timezone.utc)
        base = now_dt - timedelta(days=80)
        rates = [{"timestamp": (base + timedelta(days=2 * i)).isoformat(),
                  "fundingRate": 0.0001} for i in range(39)]
        rates.append({"timestamp": (now_dt - timedelta(hours=latest_age_h)).isoformat(),
                      "fundingRate": 0.01})
        return rates

    def test_ada_crowded_stale_funding_refuses(self):
        extra = dict(KRAKEN_QUOTE)
        extra["funding_rates"] = self._rates(1)
        out = drive("free_kraken_ada_crowded",
                    {"PF_ADAUSD|240Min": _kraken_bars()}, now=KRAKEN_NOW,
                    extra=extra)
        self.assertEqual(len(entries(out)), 1)
        extra["funding_rates"] = self._rates(10)  # > FUNDING_MAX_AGE 2h
        out = drive("free_kraken_ada_crowded",
                    {"PF_ADAUSD|240Min": _kraken_bars()}, now=KRAKEN_NOW,
                    extra=extra)
        self.assertEqual(entries(out), [])


class TestVerifyBreakdownValidityGates(unittest.TestCase):
    def test_ada_breakdown_recovered_bid_refuses(self):
        out = drive("free_kraken_ada_breakdown",
                    {"PF_ADAUSD|240Min": _kraken_bars()}, now=KRAKEN_NOW,
                    extra={"quote": {"bid": 2.05, "ask": 2.06}})
        self.assertEqual(entries(out), [])
        out = drive("free_kraken_ada_breakdown",
                    {"PF_ADAUSD|240Min": _kraken_bars()}, now=KRAKEN_NOW,
                    extra=dict(KRAKEN_QUOTE))
        self.assertEqual(len(entries(out)), 1)


class TestVerifyOwnIvFreshness(unittest.TestCase):
    CALL = "SPY261030C00500000"
    PUT = "SPY261030P00500000"
    NOW_UTC = "2026-10-23T14:00:00+00:00"

    def _extra(self, ts):
        return {"quote": {"t": ts, "received_at": ts, "ap": 2.5, "bp": 2.4},
                "package": {"forecast": 25.0, "iv": 20.0, "legs": [
                    {"right": "call", "symbol": self.CALL, "ask": 2.5,
                     "source_at": self.NOW_UTC},
                    {"right": "put", "symbol": self.PUT, "ask": 2.4,
                     "source_at": self.NOW_UTC}]}}

    def test_fresh_enters_stale_refuses(self):
        out = ev3("free_opt_own_iv", "2026-10-23T10:00:00-04:00",
                  extra=self._extra(self.NOW_UTC))
        self.assertEqual(len(entries(out)), 2)  # straddle: 2 leg intents
        out = ev3("free_opt_own_iv", "2026-10-23T10:00:00-04:00",
                  extra=self._extra("2026-10-20T14:00:00+00:00"))
        self.assertEqual(entries(out), [])


if __name__ == "__main__":
    unittest.main()
