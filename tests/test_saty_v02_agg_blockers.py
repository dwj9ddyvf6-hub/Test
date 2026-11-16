"""Blockers R6-AGG (2026-10-25): the production-side 5Min -> 10Min
aggregation cache for saty_gpt_v02 (desk3/saty_v02_agg.py, wired in
adapters3/saty_gpt_v02.py).

Fail direction: on the pre-cure tree desk3.saty_v02_agg does not exist
and adapters3 serves the raw view, so the identity/wiring tests fail
(collection error + assertion). The golden-battery property pinned
here: pre-aggregated 10Min door rows are EXACTLY the strategy's own
normalize+resample output, and full evaluations through both doors
produce identical intents; anomalies decline (None) so the caller
falls back to the untouched original path."""
import importlib, os, sys, tempfile, unittest
from datetime import date, datetime, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from zoneinfo import ZoneInfo
ET = ZoneInfo("America/New_York")


def _b5(day, k, px, off="-04:00"):
    mins = 9 * 60 + 30 + k * 5
    return {"t": f"{day.isoformat()}T{mins // 60:02d}:{mins % 60:02d}:00{off}",
            "o": px, "h": px + 1, "l": px - 1, "c": px + 0.5, "v": 100.0}


def _epoch_rows(rows):
    out = []
    for r in rows:
        t = r["t"]
        if isinstance(t, str):
            t = datetime.fromisoformat(t.replace("Z", "+00:00")).timestamp()
        out.append({"t": t, "o": r["o"], "h": r["h"], "l": r["l"],
                    "c": r["c"], "v": r.get("v") or 0.0})
    return out


def _oracle(rows5, daily=()):
    from sleeves.saty_gpt_v02 import _session_obj, _door_rows, _shape
    from core.saty_gpt_v02 import normalize_intraday_bars
    from core.saty_gpt_v02.data import Calendar, resample_intraday
    from core.data import is_trading_day
    raw5 = _shape(_epoch_rows(rows5))
    draw = _shape(_epoch_rows(list(daily)))
    days = sorted({datetime.fromtimestamp(b[0], tz=ET).date() for b in raw5}
                  | {datetime.fromtimestamp(b[0], tz=ET).date() for b in draw})
    cal = Calendar([_session_obj(d) for d in days if is_trading_day(d)])
    obs = normalize_intraday_bars("SPY", _door_rows(raw5), "5m", cal, feed="sip")
    return [{"t": o.bar.start.timestamp(), "o": o.bar.open, "h": o.bar.high,
             "l": o.bar.low, "c": o.bar.close, "v": o.bar.volume}
            for o in resample_intraday(obs, "10m", cal)]


def _rth(days, base=500.0):
    out, seq, d = [], [], date(2026, 10, 23)
    while len(seq) < days:
        if d.weekday() < 5:
            seq.append(d)
        d -= timedelta(days=1)
    for di, day in enumerate(sorted(seq)):
        px = base + di * 0.7
        for k in range(78):
            mins = 13 * 60 + 30 + k * 5
            px += 0.02
            out.append({"t": f"{day.isoformat()}T{mins // 60:02d}:{mins % 60:02d}:00Z",
                        "o": px, "h": px + 0.4, "l": px - 0.4, "c": px + 0.1, "v": 5000.0})
    return out


def _daily(n):
    days, d = [], date(2026, 10, 22)
    while len(days) < n:
        if d.weekday() < 5:
            days.append(d)
        d -= timedelta(days=1)
    return [{"t": f"{x.isoformat()}T04:00:00Z", "o": 400.0, "h": 402.0,
             "l": 398.0, "c": 400.5, "v": 20000.0} for x in reversed(days)]


class TestAggregateIdentity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.agg = importlib.import_module("desk3.saty_v02_agg")

    def test_full_day_matches_oracle(self):
        rows = [_b5(date(2026, 10, 23), k, 500 + k) for k in range(78)]
        self.assertEqual(self.agg.aggregate_5m_to_10m(rows), _oracle(rows))

    def test_gaps_and_extended_hours_match_oracle(self):
        rows = [_b5(date(2026, 10, 23), k, 500 + k) for k in range(78)
                if k not in (10, 25, 26)]
        rows += [{"t": "2026-10-23T08:00:00-04:00", "o": 1, "h": 1, "l": 1, "c": 1, "v": 5},
                 {"t": "2026-10-23T16:05:00-04:00", "o": 1, "h": 1, "l": 1, "c": 1, "v": 5}]
        self.assertEqual(self.agg.aggregate_5m_to_10m(rows), _oracle(rows))

    def test_early_close_matches_oracle(self):
        ec = date(2026, 11, 27)
        rows = []
        for k in range(60):
            mins = 9 * 60 + 30 + k * 5
            rows.append({"t": f"{ec.isoformat()}T{mins // 60:02d}:{mins % 60:02d}:00-05:00",
                         "o": 100 + k, "h": 101 + k, "l": 99 + k, "c": 100.5 + k, "v": 10})
        self.assertEqual(self.agg.aggregate_5m_to_10m(rows), _oracle(rows))

    def test_multi_session_matches_oracle(self):
        rows = _rth(30)
        self.assertEqual(self.agg.aggregate_5m_to_10m(rows), _oracle(rows, _daily(120)))

    def test_duplicate_in_session_declines(self):
        rows = [_b5(date(2026, 10, 23), k, 500 + k) for k in range(78)]
        self.assertIsNone(self.agg.aggregate_5m_to_10m(rows + [rows[3]]))

    def test_unparseable_declines(self):
        rows = [_b5(date(2026, 10, 23), k, 500 + k) for k in range(10)]
        rows.append({"t": "not-a-time", "o": 1, "h": 1, "l": 1, "c": 1, "v": 1})
        self.assertIsNone(self.agg.aggregate_5m_to_10m(rows))

    def test_cache_bounded(self):
        self.agg._cache.clear()
        for i in range(self.agg.CACHE_MAX + 3):
            rows = [_b5(date(2026, 10, 23), k, 500 + k + i * 1000) for k in range(4)]
            self.agg.cached_aggregate_10m(rows)
        self.assertLessEqual(len(self.agg._cache), self.agg.CACHE_MAX)


class TestEntrypointWiring(unittest.TestCase):
    def _view(self):
        return {"now": "2026-10-23T15:30:00-04:00",
                "bars": {"SPY|5Min": _rth(30), "SPY|1Day": _daily(120),
                         "SPY": _daily(120)},
                "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0},
                "session_fills": []}

    def test_preaggregate_rewrites_view(self):
        mod = importlib.import_module("adapters3.saty_gpt_v02")
        v = mod._preaggregated_view(self._view())
        self.assertNotIn("SPY|5Min", v["bars"])
        self.assertEqual(v["extra"]["bars_10m"]["SPY"],
                         _oracle(self._view()["bars"]["SPY|5Min"], _daily(120)))

    def test_producer_door_not_overridden(self):
        mod = importlib.import_module("adapters3.saty_gpt_v02")
        v = self._view(); v["extra"] = {"bars_10m": {"SPY": [{"t": 1.0}]}}
        self.assertIs(mod._preaggregated_view(v), v)

    def test_anomaly_view_untouched(self):
        mod = importlib.import_module("adapters3.saty_gpt_v02")
        v = self._view()
        v["bars"]["SPY|5Min"] = v["bars"]["SPY|5Min"] + [v["bars"]["SPY|5Min"][3]]
        self.assertIs(mod._preaggregated_view(v), v)

    def test_evaluate_identical_both_doors(self):
        mod3 = importlib.import_module("adapters3.saty_gpt_v02")
        from adapters3._snapshot_ctx import SnapshotSleeveContext
        import adapters.saty_gpt_v02 as v2a
        view = self._view()
        out_agg = mod3.evaluate(view, {"sleeve_id": "saty_gpt_v02",
                                       "state_dir": tempfile.mkdtemp()})
        sctx = SnapshotSleeveContext("saty_gpt_v02", view,
                                     {"state_dir": tempfile.mkdtemp()})
        sctx._journal = os.path.join(sctx._state_dir, "journal.jsonl")
        out_orig = v2a.evaluate(sctx)
        self.assertEqual(out_agg, out_orig)


class TestWarmBarsParseCache(unittest.TestCase):
    """R6 companion cure: WarmBars re-parsed its 18MB cache file every
    cycle (1.32s measured). The (mtime_ns, size)-keyed memo serves the
    identical parsed dict for an unchanged file and re-parses on any
    rewrite — freshness semantics untouched."""

    def _producer(self, tmp, bars, fetched):
        import json as _json
        from datetime import timezone
        from desk3.warm import WarmBars
        os.makedirs(os.path.join(tmp, "state"), exist_ok=True)
        path = os.path.join(tmp, "state", "warm_bars.json")
        with open(path, "w") as fh:
            _json.dump({"fetched_at": fetched.isoformat(), "bars": bars}, fh)
        return WarmBars(tmp), path

    def test_unchanged_file_serves_identical_object(self):
        from datetime import datetime, timezone
        now = datetime(2026, 10, 25, 20, 0, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as tmp:
            wb, _ = self._producer(tmp, {"SPY": [{"t": "x"}]}, now)
            a = wb._read_cache(now)
            b = wb._read_cache(now)
            self.assertIs(a, b)  # no second parse (fails pre-cure)
            self.assertEqual(a, {"SPY": [{"t": "x"}]})

    def test_rewrite_is_reparsed_and_staleness_holds(self):
        import json as _json
        from datetime import datetime, timedelta, timezone
        now = datetime(2026, 10, 25, 20, 0, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as tmp:
            wb, path = self._producer(tmp, {"SPY": [1]}, now)
            self.assertEqual(wb._read_cache(now), {"SPY": [1]})
            with open(path, "w") as fh:
                _json.dump({"fetched_at": now.isoformat(),
                            "bars": {"SPY": [2, 2]}}, fh)
            st = os.stat(path)
            os.utime(path, ns=(st.st_atime_ns, st.st_mtime_ns + 1_000_000))
            self.assertEqual(wb._read_cache(now), {"SPY": [2, 2]})
            later = now + timedelta(seconds=wb.max_age_s + 1)
            self.assertIsNone(wb._read_cache(later))


if __name__ == "__main__":
    unittest.main()
