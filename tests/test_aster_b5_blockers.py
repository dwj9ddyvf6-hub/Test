"""Blockers ASTER-B5: Aster batch 5 (ADAUSDT spot sleeves).

Faithful ports of archive r19_crypto.py + absorption/signals.py
(absorption / breakout / funding families, fixed-16 exit, 4h entry
delay in bar terms) and public_source_sleeves.py tomazetti_rsi2
(hourly RSI2). Fixture drives prove entry, the designed exit, and
refusals through evaluate(view, ctx); registry + config rows asserted;
E2E round-trip to flat on the FakeBroker per family.
"""
import importlib, json, os, sys, tempfile, unittest
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

NOW = datetime(2026, 10, 23, 20, 0, tzinfo=timezone.utc)
IDS = ["aster_pub_rsi2_ada",
       "aster_abs_base_ada_fullcash", "aster_abs_base_ada_vol1pct",
       "aster_abs_neg_ada_fullcash", "aster_abs_neg_ada_vol1pct",
       "aster_abs_nonneg_ada_fullcash", "aster_abs_nonneg_ada_vol1pct",
       "aster_breakout_ada_fullcash", "aster_breakout_ada_vol1pct",
       "aster_squeeze_ada_fullcash"]
FUNDING_IDS = [i for i in IDS if "neg_ada" in i or "nonneg" in i
               or "squeeze" in i]


def _iso(dt):
    return dt.isoformat().replace("+00:00", "Z")


def _mk4(specs):
    """specs: list of (o, c, v, h, l) oldest-first; last bar closes at NOW."""
    n = len(specs)
    out = []
    for i, (o, c, v, h, l) in enumerate(specs):
        out.append({"t": _iso(NOW - timedelta(hours=4 * (n - i))),
                    "o": o, "h": h, "l": l, "c": c, "v": v})
    return out


def _flat_spec(n, price=1.0, vol=1000.0):
    return [(price, price, vol, price * 1.001, price * 0.999)] * n


def _flat4(n, price=1.0, vol=1000.0):
    return _mk4(_flat_spec(n, price, vol))


def _absorption_bars(entry_vol=1000.0):
    specs = _flat_spec(300)
    specs.append((1.0, 0.95, 3000.0, 1.001, 0.949))      # shock
    specs.append((0.95, 1.02, 1500.0, 1.021, 0.949))     # confirm = signal
    specs.append((1.02, 1.02, entry_vol, 1.021, 1.019))  # entry interval
    return _mk4(specs)


def _breakout_bars(entry_vol=1000.0):
    specs = [(1.0, 1.0, 1000.0, 1.01, 0.99)] * 300
    specs.append((1.0, 1.05, 2000.0, 1.06, 0.99))       # signal
    specs.append((1.05, 1.05, entry_vol, 1.06, 1.04))    # entry interval
    return _mk4(specs)


def _funding(rate):
    settled = NOW - timedelta(hours=5)
    return {"ADAUSDT": [{"rate": rate, "settled_at": _iso(settled),
                         "received_at": _iso(settled + timedelta(minutes=30)),
                         "observed_public_endpoint": True}]}


def _rsi2_bars(dip=True):
    closes = [0.60 + 0.0016 * i for i in range(250)]
    if dip:
        closes += [closes[-1] - 0.02 * k for k in range(1, 5)]
    start = NOW - timedelta(hours=len(closes))
    out, prev = [], closes[0]
    for i, c in enumerate(closes):
        o = prev
        out.append({"t": _iso(start + timedelta(hours=i)), "o": o,
                    "h": max(o, c) * 1.001, "l": min(o, c) * 0.999,
                    "c": c, "v": 1000.0})
        prev = c
    return out


def _view(sid, bars4=None, bars1h=None, funding=None, positions=None):
    v = {"now": _iso(NOW), "bars": {}, "positions": positions or [],
         "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0}}
    if bars4 is not None:
        v["bars"]["ADAUSDT|4Hour"] = bars4
    if bars1h is not None:
        v["bars"]["ADAUSDT|1Hour"] = bars1h
    if funding is not None:
        v["funding"] = funding
    return v


def ev(sid, view):
    mod = importlib.import_module(f"aster_sleeves.{sid}")
    return mod.evaluate(view, {"sleeve_id": sid})


class TestRsi2(unittest.TestCase):
    SID = "aster_pub_rsi2_ada"

    def test_entry_fires_and_sizes_full_slice(self):
        bars = _rsi2_bars()
        out = ev(self.SID, _view(self.SID, bars1h=bars))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["kind"], "entry")
        self.assertEqual(out[0]["symbol"], "ADAUSDT")
        self.assertEqual(out[0]["qty"], int(10000.0 // bars[-1]["c"]))

    def test_exit_close_above_sma5(self):
        bars = _rsi2_bars(dip=False)
        pos = [{"symbol": "ADAUSDT", "qty": 5000, "avg_price": 0.90,
                "opened_at": _iso(NOW - timedelta(hours=30)),
                "sleeve_id": self.SID}]
        out = ev(self.SID, _view(self.SID, bars1h=bars, positions=pos))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["kind"], "exit")
        self.assertEqual(out[0]["qty"], 5000)

    def test_refusals(self):
        # no dip: RSI never oversold
        self.assertEqual(ev(self.SID, _view(self.SID,
                                            bars1h=_rsi2_bars(dip=False))), [])
        # insufficient history for SMA200
        self.assertEqual(ev(self.SID, _view(self.SID,
                                            bars1h=_rsi2_bars()[:100])), [])


class TestAbsorption(unittest.TestCase):
    def test_base_entry_fullcash_and_volcap(self):
        bars = _absorption_bars()
        out = ev("aster_abs_base_ada_fullcash",
                 _view("aster_abs_base_ada_fullcash", bars4=bars))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["qty"], 9794)  # floor(10000/(1.02*1.001))
        bars_v = _absorption_bars(entry_vol=50000.0)
        out_v = ev("aster_abs_base_ada_vol1pct",
                   _view("aster_abs_base_ada_vol1pct", bars4=bars_v))
        self.assertEqual(len(out_v), 1)
        self.assertEqual(out_v[0]["qty"], 500)  # 1% of prior-interval volume

    def test_funding_filters(self):
        bars = _absorption_bars()
        neg = _view("aster_abs_neg_ada_fullcash", bars4=bars,
                    funding=_funding(-0.0005))
        self.assertEqual(len(ev("aster_abs_neg_ada_fullcash", neg)), 1)
        nonneg_on_neg = _view("aster_abs_nonneg_ada_fullcash", bars4=bars,
                              funding=_funding(-0.0005))
        self.assertEqual(ev("aster_abs_nonneg_ada_fullcash", nonneg_on_neg), [])
        pos_f = _funding(0.0005)
        self.assertEqual(len(ev("aster_abs_nonneg_ada_fullcash",
                                _view("aster_abs_nonneg_ada_fullcash",
                                      bars4=bars, funding=pos_f))), 1)
        self.assertEqual(ev("aster_abs_neg_ada_fullcash",
                            _view("aster_abs_neg_ada_fullcash",
                                  bars4=bars, funding=pos_f)), [])
        # missing funding refuses (never assumed zero)
        self.assertEqual(ev("aster_abs_nonneg_ada_fullcash",
                            _view("aster_abs_nonneg_ada_fullcash",
                                  bars4=bars)), [])

    def test_refusal_no_confirmation_and_warmup(self):
        bars = _flat4(302)  # no shock/confirm sequence
        self.assertEqual(ev("aster_abs_base_ada_fullcash",
                            _view("aster_abs_base_ada_fullcash",
                                  bars4=bars)), [])
        short = _absorption_bars()[-10:]  # far below 300 indicator bars
        self.assertEqual(ev("aster_abs_base_ada_fullcash",
                            _view("aster_abs_base_ada_fullcash",
                                  bars4=short)), [])


class TestBreakoutSqueeze(unittest.TestCase):
    def test_breakout_entry_and_volcap(self):
        bars = _breakout_bars()
        out = ev("aster_breakout_ada_fullcash",
                 _view("aster_breakout_ada_fullcash", bars4=bars))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["qty"], 9514)  # floor(10000/(1.05*1.001))
        bars_v = _breakout_bars(entry_vol=50000.0)
        out_v = ev("aster_breakout_ada_vol1pct",
                   _view("aster_breakout_ada_vol1pct", bars4=bars_v))
        self.assertEqual(out_v[0]["qty"], 500)

    def test_breakout_refusal_flat_market(self):
        self.assertEqual(ev("aster_breakout_ada_fullcash",
                            _view("aster_breakout_ada_fullcash",
                                  bars4=_flat4(302))), [])

    def test_squeeze_needs_negative_funding(self):
        bars = _breakout_bars()
        self.assertEqual(len(ev("aster_squeeze_ada_fullcash",
                                _view("aster_squeeze_ada_fullcash",
                                      bars4=bars,
                                      funding=_funding(-0.0005)))), 1)
        self.assertEqual(ev("aster_squeeze_ada_fullcash",
                            _view("aster_squeeze_ada_fullcash",
                                  bars4=bars, funding=_funding(0.0005))), [])
        self.assertEqual(ev("aster_squeeze_ada_fullcash",
                            _view("aster_squeeze_ada_fullcash",
                                  bars4=bars)), [])


class TestFixed16Exit(unittest.TestCase):
    def test_deadline_exit_all_families(self):
        for sid in IDS[1:]:
            pos = [{"symbol": "ADAUSDT", "qty": 100, "avg_price": 1.0,
                    "opened_at": _iso(NOW - timedelta(hours=17)),
                    "sleeve_id": sid}]
            out = ev(sid, _view(sid, positions=pos))  # no bars/funding at all
            self.assertEqual(len(out), 1, sid)
            self.assertEqual(out[0]["kind"], "exit", sid)
            self.assertIn("fixed16", out[0]["reason"], sid)

    def test_no_early_exit(self):
        sid = "aster_breakout_ada_fullcash"
        pos = [{"symbol": "ADAUSDT", "qty": 100, "avg_price": 1.0,
                "opened_at": _iso(NOW - timedelta(hours=15)),
                "sleeve_id": sid}]
        self.assertEqual(ev(sid, _view(sid, bars4=_flat4(10),
                                       positions=pos)), [])


class TestRegistryConfig(unittest.TestCase):
    def test_config_rows_match_inputs(self):
        from desk3.aster_b5 import config_rows
        rows = {r["id"]: r for r in config_rows()}
        self.assertEqual(sorted(rows), sorted(IDS))
        cfg = json.loads((os.path.join(ROOT, "config", "sleeves.json"))
                         .read() if False else
                         open(os.path.join(ROOT, "config",
                                           "sleeves.json")).read())
        by_id = {r["id"]: r for r in cfg["sleeves"]}
        for sid in IDS:
            self.assertIn(sid, by_id, sid)
            self.assertEqual(by_id[sid]["inputs"], rows[sid]["inputs"], sid)
            self.assertEqual(by_id[sid]["slice"]["capital_usd"], 10000.0, sid)
            mod = importlib.import_module(f"aster_sleeves.{sid}")
            self.assertEqual(list(mod.INPUTS), rows[sid]["inputs"], sid)
        for sid in FUNDING_IDS:
            self.assertIn("funding", rows[sid]["inputs"], sid)


class TestE2E(unittest.TestCase):
    def _roundtrip(self, sid, entry_view, exit_view):
        from desk3.broker import FakeBroker
        from desk3.dispatcher import Dispatcher
        tmp = tempfile.mkdtemp()
        broker = FakeBroker(prices={"ADAUSDT": 1.05})
        d = Dispatcher(tmp, broker,
                       slices={sid: {"capital_usd": 10000.0,
                                     "cash_usd": 10000.0}},
                       price_lookup=lambda s: 1.05)
        entries = ev(sid, entry_view)
        self.assertEqual(len(entries), 1, sid)
        r = d.process_intent(entries[0], sid)
        self.assertEqual(r["status"], "filled", (sid, r))
        self.assertIn("ADA/USD", broker.get_positions())  # BLOCKED-EXIT-20261029: broker dialect at the door
        exits = ev(sid, exit_view)
        self.assertEqual(len(exits), 1, sid)
        r2 = d.process_intent(exits[0], sid)
        self.assertEqual(r2["status"], "filled", (sid, r2))
        self.assertEqual(broker.get_positions(), {}, sid)

    def test_roundtrips_per_family(self):
        # public_recipe: entry on dip, exit on close > SMA5
        entry_r = ev("aster_pub_rsi2_ada",
                     _view("aster_pub_rsi2_ada", bars1h=_rsi2_bars()))
        pos_r = [{"symbol": "ADAUSDT", "qty": entry_r[0]["qty"],
                  "avg_price": 0.92,
                  "opened_at": _iso(NOW - timedelta(hours=30)),
                  "sleeve_id": "aster_pub_rsi2_ada"}]
        self._roundtrip("aster_pub_rsi2_ada",
                        _view("aster_pub_rsi2_ada", bars1h=_rsi2_bars()),
                        _view("aster_pub_rsi2_ada",
                              bars1h=_rsi2_bars(dip=False), positions=pos_r))
        # absorption_base + breakout_base + squeeze: entry, then the
        # held position ages past its saved 16h deadline -> flat.
        cases = [
            ("aster_abs_base_ada_fullcash",
             _view("aster_abs_base_ada_fullcash", bars4=_absorption_bars()),
             None),
            ("aster_breakout_ada_fullcash",
             _view("aster_breakout_ada_fullcash", bars4=_breakout_bars()),
             None),
            ("aster_squeeze_ada_fullcash",
             _view("aster_squeeze_ada_fullcash", bars4=_breakout_bars(),
                   funding=_funding(-0.0005)), None),
            ("aster_abs_neg_ada_fullcash",
             _view("aster_abs_neg_ada_fullcash", bars4=_absorption_bars(),
                   funding=_funding(-0.0005)), None),
            ("aster_abs_nonneg_ada_fullcash",
             _view("aster_abs_nonneg_ada_fullcash",
                   bars4=_absorption_bars(), funding=_funding(0.0005)), None),
        ]
        for sid, entry_view, _ in cases:
            entry = ev(sid, entry_view)
            self.assertEqual(len(entry), 1, sid)
            pos = [{"symbol": "ADAUSDT", "qty": entry[0]["qty"],
                    "avg_price": 1.0,
                    "opened_at": _iso(NOW - timedelta(hours=17)),
                    "sleeve_id": sid}]
            self._roundtrip(sid, entry_view, _view(sid, positions=pos))


if __name__ == "__main__":
    unittest.main()
