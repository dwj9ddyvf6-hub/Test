"""EDGE batch 6 blockers (ENH-B6, 2026-10-24): aster_pub_link_ai_volume,
aster_pub_rsi2_ada, 9x ADAUSDT NFS + 1x ENJUSDT absorption (aster_crypto).

ENHANCED (5):
- lost_breakout x2 + normalization_failure x2 (desk3/aster_crypto):
  binding leak = structural exits inspected ONLY the latest bar; a
  failure bar recovered by the next bar never exited, position rode
  to the 96h deadline. Treatment (enhance_trigger_latch, default ON)
  latches the scan over every post-entry bar (normalization_failure
  keeps its per-bar 4h execution delay). OFF = latest-bar-only exactly.
- aster_pub_link_ai_volume (desk3/aster_b4): binding leak = the
  designed 5-bar time exit read ONLY bars_held; a position row with
  opened_at but no bars_held held forever. Treatment
  (enhance_held_bars, default ON) derives held bars from opened_at
  over the bar series. OFF = bars_held-or-0 exactly.

VERIFY-ONLY (7): fixed16/fixed96 x3 + normalization x2 (exits are
time/state-based, re-read every evaluation — no event bar to miss),
ENJ absorption fixed16 (deadline exit + spec-exact entry), RSI2 ADA
(300s anti-stale entry window by design; state-based SMA5 exit).
ADA-WINDOW-20261116: the RSI2 window pin is amended in place below —
the cadence cure superseded the 300s window for this sleeve.
Pins below record the measured traces from proof/enhance/*.json.

Fail direction: pre-change, the latch/derivation behaviors and both
switch helpers are absent, so the ENHANCED tests fail; the
VERIFY-ONLY pins pass on both trees by design (they are evidence).
"""
import importlib, json, os, sys, tempfile, unittest
from datetime import datetime, timedelta, timezone
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
P = "aster_r19_"
LB = [P+"adausdt_negative_funding_squeeze_lost_breakout_fullcash",
      P+"adausdt_negative_funding_squeeze_lost_breakout_volume1pct"]
NF = [P+"adausdt_negative_funding_squeeze_normalization_failure_fullcash",
      P+"adausdt_negative_funding_squeeze_normalization_failure_volume1pct"]
NOW = datetime(2026, 10, 23, 16, 0, tzinfo=timezone.utc)


def bars(n=25, vol=100000.0):
    out = []
    for i in range(n):
        t = NOW - timedelta(hours=4*(n-i))
        out.append({"t": t.isoformat(), "o": 1.0, "h": 1.05, "l": 0.95,
                    "c": 1.0, "v": vol})
    return out


def drive(sid, brs=None, funding=-0.01, positions=None, enh=None, sd=None):
    mod = importlib.import_module(f"adapters3.{sid}")
    sym = "ENJUSDT" if "enjusdt" in sid else "ADAUSDT"
    ctx = {"sleeve_id": sid, "cycle_id": "fx",
           "state_dir": sd or tempfile.mkdtemp()}
    if enh is not None:
        ctx[sid] = {"enhance_trigger_latch": enh}
    view = {"now": NOW.isoformat(),
            "bars": {f"{sym}|4Hour": brs if brs is not None else bars()},
            "funding": {sym: funding} if funding is not None else {},
            "positions": positions or [],
            "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0},
            "params": {}, "extra": {}, "session_fills": []}
    return mod.evaluate(view, ctx), ctx


def pos(hours=20, **kw):
    d = {"symbol": "ADAUSDT", "qty": 5000.0, "avg_price": 1.0,
         "opened_at": (NOW - timedelta(hours=hours)).isoformat(),
         "breakout_level": 1.05}
    d.update(kw)
    return [d]


class TestLatchLostBreakout(unittest.TestCase):
    def _case(self):
        b = bars(); b[-4]["c"] = 1.02; b[-1]["c"] = 1.08  # failed, recovered
        return b

    def test_treatment_exits_on_latched_failure(self):
        for sid in LB:
            out, ctx = drive(sid, brs=self._case(), positions=pos(), enh=True)
            self.assertEqual([o.kind for o in out], ["exit"], sid)
            self.assertIn("latched", out[0].reason)
            rows = open(os.path.join(ctx["state_dir"],
                                     "enhance_journal.jsonl")).readlines()
            rec = json.loads(rows[-1])
            self.assertEqual(rec["control_exit"], False)
            self.assertEqual(rec["treatment_exit"], True)

    def test_control_and_off_hold(self):
        for sid in LB:
            out, _ = drive(sid, brs=self._case(), positions=pos(), enh=False)
            self.assertEqual(out, [], sid)  # latest bar recovered: no exit

    def test_latest_bar_failure_fires_both_rules(self):
        b = bars(); b[-1]["c"] = 1.02
        for sid in LB:
            for enh in (True, False):
                out, _ = drive(sid, brs=[dict(x) for x in b],
                               positions=pos(hours=2), enh=enh)
                self.assertEqual(len(out), 1, (sid, enh))

    def test_pre_entry_failure_bar_ignored(self):
        b = bars(); b[0]["c"] = 0.50; b[-1]["c"] = 1.08  # failure before entry
        for sid in LB:
            out, _ = drive(sid, brs=b, positions=pos(hours=2), enh=True)
            self.assertEqual(out, [], sid)


class TestLatchNormFailure(unittest.TestCase):
    def _case(self):
        b = bars()
        for x in b:
            x["t"] = (datetime.fromisoformat(x["t"])
                      - timedelta(hours=16)).isoformat()
        b[-3]["c"] = 0.90; b[-3]["l"] = 0.90  # failure bar, delay met
        b[-1]["c"] = 1.0                      # latest recovered
        return b

    def test_treatment_exits_control_holds(self):
        for sid in NF:
            out, _ = drive(sid, brs=self._case(), funding=0.002,
                           positions=pos(hours=40), enh=True)
            self.assertEqual([o.kind for o in out], ["exit"], sid)
            self.assertIn("latched", out[0].reason)
            out, _ = drive(sid, brs=self._case(), funding=0.002,
                           positions=pos(hours=40), enh=False)
            self.assertEqual(out, [], sid)

    def test_latch_respects_per_bar_delay(self):
        b = bars(); b[-1]["c"] = 0.90; b[-1]["l"] = 0.90  # delay NOT met
        for sid in NF:
            out, _ = drive(sid, brs=b, funding=0.002,
                           positions=pos(hours=40), enh=True)
            self.assertEqual(out, [], sid)

    def test_latch_needs_normalized_funding(self):
        for sid in NF:
            out, _ = drive(sid, brs=self._case(), funding=-0.01,
                           positions=pos(hours=40), enh=True)
            self.assertEqual(out, [], sid)


def spot_bars(last, n=60):
    out = []
    for i in range(n - 1):
        b = {"o": 20.0, "h": 20.2, "l": 19.8, "c": 20.0, "v": 1000.0}
        b["t"] = float(i * 14400); out.append(b)
    l = dict(last); l["t"] = float((n - 1) * 14400); out.append(l)
    return out


FLAT = {"o": 20.0, "h": 20.2, "l": 19.8, "c": 20.0, "v": 1000.0}


class TestLinkHeldBars(unittest.TestCase):
    def _run(self, positions, enh=None, brs=None):
        from desk3.aster_b4 import evaluate_link_ai_volume
        ctx = {"state_dir": tempfile.mkdtemp()}
        if enh is not None:
            ctx["aster_pub_link_ai_volume"] = {"enhance_held_bars": enh}
        return evaluate_link_ai_volume(
            {"bars": {"LINKUSDT|4Hour": brs or spot_bars(FLAT)},
             "positions": positions}, ctx, "aster_pub_link_ai_volume")

    def test_opened_at_only_position_time_exits_when_on(self):
        p = [{"symbol": "LINKUSDT", "qty": 476, "avg_price": 20.0,
              "opened_at": float(50 * 14400)}]  # 10 bars close after open
        out = self._run(p, enh=True)
        self.assertEqual([o["kind"] for o in out], ["exit"])
        self.assertIn("bars5", out[0]["reason"])

    def test_off_restores_held_forever(self):
        p = [{"symbol": "LINKUSDT", "qty": 476, "avg_price": 20.0,
              "opened_at": float(50 * 14400)}]
        self.assertEqual(self._run(p, enh=False), [])

    def test_bars_held_field_wins_both_rules(self):
        p2 = [{"symbol": "LINKUSDT", "qty": 476, "avg_price": 20.0,
               "bars_held": 2, "opened_at": float(50 * 14400)}]
        self.assertEqual(self._run(p2, enh=True), [])
        p5 = [{"symbol": "LINKUSDT", "qty": 476, "avg_price": 20.0,
               "bars_held": 5}]
        for enh in (True, False):
            self.assertEqual(len(self._run(p5, enh=enh)), 1)

    def test_entry_unchanged(self):
        spike = spot_bars({"o": 20.5, "h": 21.2, "l": 20.4, "c": 21.0,
                           "v": 3000.0})
        out = self._run([], brs=spike)
        self.assertEqual(out[0]["qty"], 476)


class TestVerifyOnlyPins(unittest.TestCase):
    def test_deadline_sleeves(self):
        f16 = P+"adausdt_negative_funding_squeeze_fixed16_volume1pct"
        out, _ = drive(f16, positions=pos(hours=17)); self.assertEqual(len(out), 1)
        out, _ = drive(f16, positions=pos(hours=8)); self.assertEqual(out, [])
        f96 = P+"adausdt_negative_funding_squeeze_fixed96_fullcash"
        out, _ = drive(f96, positions=pos(hours=97)); self.assertEqual(len(out), 1)
        out, _ = drive(f96, positions=pos(hours=20)); self.assertEqual(out, [])

    def test_normalization_is_state_based(self):
        for sid in (P+"adausdt_negative_funding_squeeze_normalization_fullcash",
                    P+"adausdt_negative_funding_squeeze_normalization_volume1pct"):
            out, _ = drive(sid, funding=0.0, positions=pos(hours=2))
            self.assertEqual(len(out), 1, sid)   # current print >= 0 exits
            out, _ = drive(sid, funding=-0.01, positions=pos(hours=2))
            self.assertEqual(out, [], sid)      # still negative: holds

    def test_rsi2_window_and_state_exit(self):
        from aster_sleeves._common import evaluate_rsi2
        base = datetime(2026, 10, 20, tzinfo=timezone.utc)
        closes = [100.0]*100 + [100.0 + 0.5*i for i in range(1, 101)] \
            + [147.0, 144.0, 141.0, 138.0]
        brs = [{"t": (base + timedelta(hours=i)).isoformat(), "o": c,
                "h": c*1.001, "l": c*0.999, "c": c, "v": 1000.0}
               for i, c in enumerate(closes)]
        lc = base + timedelta(hours=len(closes))
        v = {"now": lc.isoformat(), "bars": {"ADAUSDT|1Hour": brs},
             "positions": [], "slice": {"cash_usd": 10000.0}}
        out = evaluate_rsi2(v, {}, "aster_pub_rsi2_ada")
        self.assertEqual(len(out), 1); self.assertEqual(out[0]["qty"], 72)
        # ADA-WINDOW-20261116 pin amendment (dated estate form): the
        # 300s anti-stale pin below was superseded for THIS sleeve by
        # the ENH-ABS-WINDOW cadence cure — at the 3600s cadence the
        # 300s window made ~92% of designed signals unexecutable
        # (Phase E1 fixture proof). The pin now records the cadence
        # window: entry at exactly one cadence (inclusive, as in
        # evaluate_crypto) with the paired shadow record, refusal
        # beyond it. Original pin: +3600s -> [].
        v2 = dict(v); v2["now"] = (lc + timedelta(seconds=3600)).isoformat()
        out2 = evaluate_rsi2(v2, {}, "aster_pub_rsi2_ada")
        self.assertEqual(len(out2), 1); self.assertEqual(out2[0]["qty"], 72)
        self.assertEqual(out2[0]["enhance_exp"]["records"][0]["control"],
                         "no_entry_outside_300s_window")
        v3 = dict(v); v3["now"] = (lc + timedelta(seconds=3601)).isoformat()
        self.assertEqual(evaluate_rsi2(v3, {}, "aster_pub_rsi2_ada"), [])


if __name__ == "__main__":
    unittest.main()
