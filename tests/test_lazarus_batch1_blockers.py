"""Lazarus batch-1 blockers: 1h,1d,1w,1dc,1wa,s_1dg,s_1wlab,s_1wsw,
s_1wc_micro,s_1wc_ml — fire-consumer sleeves (desk3/lazarus.py).
Fail direction: pre-build these modules did not exist (ImportError).
Each sleeve: entry on fresh matching fire, designed exits fire,
refusals refuse (stale fire, QQQ not red, cap mismatch, slots full).
"""
import importlib, json, os, sys, tempfile, unittest
from datetime import datetime, timedelta, timezone
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
IDS = ["1h","1d","1w","1dc","1wa","s_1dg","s_1wlab","s_1wsw","s_1wc_micro","s_1wc_ml"]
NOW = datetime(2026,10,23,14,0,tzinfo=timezone.utc)

def mod(sid): return importlib.import_module(f"adapters3.laz_{sid}")
def bars(sym, closes):
    return {f"{sym}|1Day":[{"t":f"2026-10-{20+i:02d}T14:00:00Z","o":c,"h":c,"l":c,"c":c,"v":1000} for i,c in enumerate(closes)]}
def fire(sid, sym="AAA", age_min=10, price=10.0, **kw):
    f={"sleeve_id":sid,"symbol":sym,"side":"buy","price":price,
       "fired_at":(NOW-timedelta(minutes=age_min)).isoformat(),"qqq_red":True,"stock_red":True}
    f.update(kw); return f
def view(fires=None, positions=None, extra_bars=None, now=NOW):
    v={"now":now.isoformat(),"lazarus_fires":fires or [],"positions":positions or [],"bars":{}}
    if extra_bars: v["bars"].update(extra_bars)
    return v
def ctx(sd=None): return {"sleeve_id":"x","state_dir":sd or tempfile.mkdtemp(),"cycle_id":"fx","snapshot_hash":"fx"}
def pos(sym="AAA", qty=10, avg=10.0, days_ago=1):
    return {"symbol":sym,"qty":qty,"avg_price":avg,"opened_at":(NOW-timedelta(days=days_ago)).isoformat()}

class TestEntries(unittest.TestCase):
    def test_all_entries_fire(self):
        for sid in IDS:
            with self.subTest(sid=sid):
                out = mod(sid).evaluate(view([fire(sid)]), ctx())
                self.assertEqual(len(out),1,out); self.assertEqual(out[0]["kind"],"entry")
                self.assertEqual(out[0]["symbol"],"AAA"); self.assertGreater(out[0]["qty"],0)
    def test_no_fire_refuses(self):
        for sid in IDS:
            self.assertEqual(mod(sid).evaluate(view([]), ctx()), [])
    def test_stale_fire_refuses(self):
        for sid in IDS:
            self.assertEqual(mod(sid).evaluate(view([fire(sid, age_min=60*24*30)]), ctx()), [])
    def test_wrong_sleeve_fire_refuses(self):
        self.assertEqual(mod("1d").evaluate(view([fire("1w")]), ctx()), [])
    def test_qqq_down_refusal(self):
        for sid in ["1d","1w","1dc","1wa","s_1wsw"]:
            self.assertEqual(mod(sid).evaluate(view([fire(sid, qqq_red=False)]), ctx()), [], sid)
    def test_1h_both_red_and_30min(self):
        self.assertEqual(mod("1h").evaluate(view([fire("1h", stock_red=False)]), ctx()), [])
        self.assertEqual(mod("1h").evaluate(view([fire("1h", age_min=31)]), ctx()), [])
        self.assertEqual(len(mod("1h").evaluate(view([fire("1h", age_min=29)]), ctx())),1)
    def test_cap_tier_filters(self):
        self.assertEqual(mod("1wa").evaluate(view([fire("1wa", cap_tier="large")]), ctx()), [])
        self.assertEqual(len(mod("1wa").evaluate(view([fire("1wa", cap_tier="small")]), ctx())),1)
        self.assertEqual(len(mod("s_1wc_ml").evaluate(view([fire("s_1wc_ml", cap_tier="large")]), ctx())),1)
        self.assertEqual(mod("s_1wc_micro").evaluate(view([fire("s_1wc_micro", cap_tier="small")]), ctx()), [])
    def test_slots_full_refuses(self):
        many=[pos(sym=f"S{i}", days_ago=1) for i in range(6)]
        self.assertEqual(mod("1d").evaluate(view([fire("1d")], positions=many), ctx()), [])
    def test_config_and_inputs(self):
        cfg=json.load(open(os.path.join(ROOT,"config","sleeves.json")))
        rows={r["id"]:r for r in cfg["sleeves"]}
        for sid in IDS:
            self.assertIn(sid, rows); self.assertEqual(list(mod(sid).INPUTS), rows[sid]["inputs"])
            self.assertEqual(rows[sid]["module"], f"adapters3.laz_{sid}")

class TestExits(unittest.TestCase):
    def test_stop15(self):
        # F3-LAZARUS-EXITS-20261115 (KG-7): 1w stop widened 0.15->0.30,
        # 1wa and s_1wlab stops dropped; they leave this list. 1w's
        # widened stop is asserted in test_lazarus_exit_calibration_f3.
        for sid in ["1d","s_1wsw","s_1wc_micro","s_1wc_ml"]:
            out=mod(sid).evaluate(view([], [pos(avg=100.0)], bars("AAA",[100,84])), ctx())
            self.assertEqual(len(out),1,sid); self.assertIn("stop15",out[0]["reason"])
    def test_no_stop_sleeves_hold_through_dip(self):
        # 1wa / s_1wlab joined the no-stop set in F3-LAZARUS-EXITS-20261115.
        for sid in ["1dc","s_1dg","1wa","s_1wlab"]:
            out=mod(sid).evaluate(view([], [pos(avg=100.0, days_ago=1)], bars("AAA",[100,50])), ctx())
            self.assertEqual(out,[],sid)
    def test_target20_and_partial30_1d(self):
        out=mod("1d").evaluate(view([], [pos(avg=100.0)], bars("AAA",[100,121])), ctx())
        self.assertIn("target20",out[0]["reason"])
        out=mod("1d").evaluate(view([], [pos(avg=100.0, qty=10)], bars("AAA",[100,131])), ctx())
        self.assertIn("partial30",out[0]["reason"]); self.assertEqual(out[0]["qty"],5)
    def test_time_exits(self):
        cases=[("1d",60),("1dc",30),("s_1dg",30),("s_1wlab",200),("s_1wsw",200),("1w",400),("1wa",400),("s_1wc_micro",400),("s_1wc_ml",400)]
        for sid,days in cases:
            out=mod(sid).evaluate(view([], [pos(avg=10.0, days_ago=days)], bars("AAA",[10,10])), ctx())
            self.assertEqual(len(out),1,(sid,out)); self.assertIn("time_exit",out[0]["reason"])
    def test_1h_target_from_fire_state(self):
        sd=tempfile.mkdtemp()
        mod("1h").evaluate(view([fire("1h", target_price=12.0)]), ctx(sd))
        out=mod("1h").evaluate(view([], [pos(avg=10.0)], bars("AAA",[10,12.5])), ctx(sd))
        self.assertEqual(len(out),1); self.assertIn("target",out[0]["reason"])
    def test_held_position_not_reentered(self):
        out=mod("1w").evaluate(view([fire("1w")], [pos(days_ago=1)], bars("AAA",[10,10])), ctx())
        self.assertEqual(out,[])

if __name__=="__main__": unittest.main()
