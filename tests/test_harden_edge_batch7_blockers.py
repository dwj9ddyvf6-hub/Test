"""Edge batch-7 blockers (ENH-ASTER-R19-B7/B11, 2026-10-24).

Binding leak: stale-signal entry. Pre-change, the R19 ENJ (batch7
engine) and LINK absorption_base (b11 engine) sleeves entered on the
latest completed 4h bar's signal at ANY age, sized off that bar's
stale close into a fixed 16h/96h hold. Treatment (switch default ON):
entries only inside the signal bar's freshness window (ENJ: age in
[0,900s], the sleeves' declared producer SLA; LINK: age <= 4h, one
bar interval, ENH-B8 gate serving the shared b11 engine). OFF
restores the pre-change rule exactly; the pre-change rule is the
shadow control and paired records are journaled on every gated
opportunity. Exits are never gated.

Fail-first: pre-change engines have no gate — the stale-refusal and
paired-record tests fail on the old code (verified by stash).
"""
import importlib, os, sys, tempfile, unittest
from datetime import datetime, timedelta, timezone
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
P = "aster_r19_enjusdt_"
ENJ = [P+"absorption_base_fixed16_volume1pct",
       P+"absorption_negative_funding_fixed16_fullcash",
       P+"absorption_negative_funding_fixed16_volume1pct",
       P+"absorption_nonnegative_funding_fixed16_fullcash",
       P+"absorption_nonnegative_funding_fixed16_volume1pct",
       P+"breakout_base_fixed16_fullcash",
       P+"breakout_base_fixed16_volume1pct",
       P+"negative_funding_squeeze_fixed16_fullcash",
       P+"negative_funding_squeeze_fixed16_volume1pct",
       P+"negative_funding_squeeze_fixed96_fullcash"]
LNK = ["aster_r19_linkusdt_absorption_base_fixed16_fullcash",
       "aster_r19_linkusdt_absorption_base_fixed16_volume1pct"]
NOW = datetime(2026, 10, 23, 16, 0, tzinfo=timezone.utc)


def abs_bars(sym_px=2.0, n=302):
    out = []
    for i in range(n):
        t = NOW - timedelta(hours=4 * (n - i)); o = c = sym_px; h = sym_px + 0.02; l = sym_px - 0.02; v = 1000.0
        if i == n - 2: o, c, h, l, v = sym_px, sym_px - 0.10, sym_px, sym_px - 0.12, 5000.0
        if i == n - 1: o, c = sym_px - 0.10, sym_px - 0.04
        out.append({"t": t.isoformat(), "o": o, "h": h, "l": l, "c": c, "v": v})
    return out


def brk_bars(n=25):
    out = []
    for i in range(n):
        t = NOW - timedelta(hours=4 * (n - i))
        c = 1.10 if i == n - 1 else 1.0
        out.append({"t": t.isoformat(), "o": 1.0, "h": 1.05, "l": 0.95, "c": c, "v": 100000.0})
    return out


def drive_enj(sid, brs, funding=-0.01, now=NOW, extra=None, positions=None):
    mod = importlib.import_module(f"adapters3.{sid}")
    view = {"now": now.isoformat(), "bars": {"ENJUSDT|4Hour": brs},
            "funding": {"ENJUSDT": funding} if funding is not None else {},
            "positions": positions or [],
            "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0},
            "params": {}, "extra": extra if extra is not None else {}, "session_fills": []}
    return mod.evaluate(view, {"sleeve_id": sid, "cycle_id": "fx", "state_dir": tempfile.mkdtemp()})


def drive_lnk(sid, brs, funding=-0.01, now=NOW, extra=None, positions=None):
    mod = importlib.import_module(f"adapters3.{sid}")
    view = {"now": now.isoformat(), "bars": {"LINKUSDT|4Hour": brs},
            "funding": {"LINKUSDT": funding} if funding is not None else {},
            "positions": positions or [],
            "slice": {"capital_usd": 10000.0, "cash_usd": 10000.0},
            "params": {}, "extra": extra if extra is not None else {}, "session_fills": []}
    return mod.evaluate(view, {"sleeve_id": sid, "cycle_id": "fx", "state_dir": tempfile.mkdtemp()})


def sig_bars(sid):
    return brk_bars() if ("breakout" in sid or "squeeze" in sid) else abs_bars()


class TestEnjFreshnessGate(unittest.TestCase):
    def test_fresh_signal_enters_all(self):
        for sid in ENJ:
            f = None if ("base" in sid) else -0.01
            if "nonnegative" in sid: f = 0.002
            out = drive_enj(sid, sig_bars(sid), funding=f)
            self.assertEqual(len(out), 1, sid); self.assertEqual(out[0].kind, "enter", sid)

    def test_stale_signal_refused_all(self):
        stale = NOW + timedelta(hours=2)  # signal age 2h > 900s window
        for sid in ENJ:
            f = None if ("base" in sid) else -0.01
            if "nonnegative" in sid: f = 0.002
            self.assertEqual(drive_enj(sid, sig_bars(sid), funding=f, now=stale), [], sid)

    def test_window_boundary(self):
        sid = ENJ[5]
        self.assertEqual(len(drive_enj(sid, brk_bars(), funding=None,
                                       now=NOW + timedelta(seconds=900))), 1)
        self.assertEqual(drive_enj(sid, brk_bars(), funding=None,
                                   now=NOW + timedelta(seconds=901)), [])

    def test_forming_bar_refused(self):
        sid = ENJ[5]  # last bar not yet closed: age < 0
        self.assertEqual(drive_enj(sid, brk_bars(), funding=None,
                                   now=NOW - timedelta(hours=2)), [])

    def test_switch_off_restores_prechange_exactly(self):
        stale = NOW + timedelta(hours=2)
        for sid in ENJ:
            f = None if ("base" in sid) else -0.01
            if "nonnegative" in sid: f = 0.002
            extra = {"aster_r19_improve": {sid: {"signal_window": False}}}
            out = drive_enj(sid, sig_bars(sid), funding=f, now=stale, extra=extra)
            self.assertEqual(len(out), 1, sid)

    def test_paired_journal_record(self):
        j = {"records": []}
        extra = {"aster_r19_exp_journal": j}
        out = drive_enj(ENJ[5], brk_bars(), funding=None,
                        now=NOW + timedelta(hours=2), extra=extra)
        self.assertEqual(out, [])
        self.assertEqual(len(j["records"]), 1)
        r = j["records"][0]
        self.assertEqual(r["control"], "enter")
        self.assertEqual(r["treatment"], "refused_stale_signal")
        self.assertAlmostEqual(r["signal_age_s"], 7200.0)

    def test_exit_never_gated(self):
        pos = [{"symbol": "ENJUSDT", "qty": 5000.0, "avg_price": 1.0,
                "opened_at": (NOW - timedelta(hours=20)).isoformat()}]
        out = drive_enj(ENJ[7], brk_bars(), now=NOW + timedelta(hours=12), positions=pos)
        self.assertEqual([o.kind for o in out], ["exit"])


class TestLinkFreshnessGate(unittest.TestCase):
    def test_fresh_enters_and_stale_refused(self):
        for sid in LNK:
            self.assertEqual(len(drive_lnk(sid, abs_bars(20.0), funding=None)), 1, sid)
            self.assertEqual(drive_lnk(sid, abs_bars(20.0), funding=None,
                                       now=NOW + timedelta(hours=12)), [], sid)

    def test_switch_off_restores_and_journal_pairs(self):
        j = []
        extra = {"aster_edge": {LNK[0]: {"stale_signal_gate": False}},
                 "aster_edge_journal": j}
        out = drive_lnk(LNK[0], abs_bars(20.0), funding=None,
                        now=NOW + timedelta(hours=12), extra=extra)
        self.assertEqual(len(out), 1)
        j2 = []
        drive_lnk(LNK[0], abs_bars(20.0), funding=None, now=NOW + timedelta(hours=12),
                  extra={"aster_edge_journal": j2})
        self.assertEqual(j2[0]["enhanced"], "refuse_stale_signal")
        self.assertEqual(j2[0]["shadow_faithful"], "enter")

    def test_link_exit_never_gated(self):
        pos = [{"symbol": "LINKUSDT", "qty": 100.0, "avg_price": 20.0,
                "opened_at": (NOW - timedelta(hours=20)).isoformat()}]
        out = drive_lnk(LNK[0], abs_bars(20.0), funding=None,
                        now=NOW + timedelta(hours=12), positions=pos)
        self.assertEqual([o.kind for o in out], ["exit"])


if __name__ == "__main__":
    unittest.main()
