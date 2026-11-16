"""Aster batch 6 blockers (ASTER-B6): 9x negative_funding_squeeze ADAUSDT
+ 1x absorption_base ENJUSDT. Archive staged tree absent on this box at
build time; oracle = TSV spec (ASTER-BUILD-MAP batch 6): NFS entry =
completed 4h close > highest high of prior 20 bars + observed funding <0;
absorption entry = TSV shock/confirm rule with >=300 bars; exits per
exit_policy (fixed16/fixed96 deadline, lost_breakout, normalization,
normalization_failure w/ 4h execution delay); sizing fullcash vs
volume1pct (1% of preceding 4h volume); fee 10bp. Fail-first: adapters
absent pre-build => errors."""
import importlib, json, os, sys, tempfile, unittest
from datetime import datetime, timedelta, timezone
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,ROOT)
P="aster_r19_"
IDS=[P+"adausdt_negative_funding_squeeze_fixed16_volume1pct",
 P+"adausdt_negative_funding_squeeze_fixed96_fullcash",
 P+"adausdt_negative_funding_squeeze_fixed96_volume1pct",
 P+"adausdt_negative_funding_squeeze_lost_breakout_fullcash",
 P+"adausdt_negative_funding_squeeze_lost_breakout_volume1pct",
 P+"adausdt_negative_funding_squeeze_normalization_failure_fullcash",
 P+"adausdt_negative_funding_squeeze_normalization_failure_volume1pct",
 P+"adausdt_negative_funding_squeeze_normalization_fullcash",
 P+"adausdt_negative_funding_squeeze_normalization_volume1pct",
 P+"enjusdt_absorption_base_fixed16_fullcash"]
NOW=datetime(2026,10,23,16,0,tzinfo=timezone.utc)
def bars(n=25, breakout=True, vol=100000.0):
    out=[]
    for i in range(n):
        t=NOW-timedelta(hours=4*(n-i))
        c=1.10 if (breakout and i==n-1) else 1.0
        out.append({"t":t.isoformat(),"o":1.0,"h":1.05,"l":0.95,"c":c,"v":vol})
    return out
def abs_bars():
    out=[]
    for i in range(302):
        t=NOW-timedelta(hours=4*(302-i)); o=c=2.0; h=2.02; l=1.98; v=1000.0
        if i==300: o,c,h,l,v=2.0,1.90,2.0,1.88,5000.0  # shock: bearish, vol spike, below EMA50
        if i==301: o,c=1.90,1.96  # confirm: bullish, above shock midpoint 1.94
        out.append({"t":t.isoformat(),"o":o,"h":h,"l":l,"c":c,"v":v})
    return out
def drive(sid, brs=None, funding=-0.01, positions=None, cash=10000.0, sym=None):
    mod=importlib.import_module(f"adapters3.{sid}")
    sym=sym or ("ENJUSDT" if "enjusdt" in sid else "ADAUSDT")
    view={"now":NOW.isoformat(),"bars":{f"{sym}|4Hour":brs if brs is not None else bars()},
          "funding":{sym:funding} if funding is not None else {},
          "positions":positions or [],"slice":{"capital_usd":10000.0,"cash_usd":cash},
          "params":{},"extra":{},"session_fills":[]}
    return mod.evaluate(view,{"sleeve_id":sid,"cycle_id":"fx","state_dir":tempfile.mkdtemp()})
def pos(hours=20, qty=5000.0, sym="ADAUSDT", **kw):
    d={"symbol":sym,"qty":qty,"avg_price":1.0,"opened_at":(NOW-timedelta(hours=hours)).isoformat(),"breakout_level":1.05}
    d.update(kw); return [d]
class TestEntries(unittest.TestCase):
    def test_nfs_entry_fullcash(self):
        out=drive(IDS[1]); self.assertEqual(len(out),1); self.assertEqual(out[0].kind,"enter")
        self.assertEqual(out[0].qty,int(10000*0.999/1.10))  # whole-unit floor (dispatcher rule)
    def test_nfs_entry_volume_cap(self):
        out=drive(IDS[0]); self.assertEqual(len(out),1); self.assertAlmostEqual(out[0].qty,1000.0)  # 1% of 100k vol
    def test_absorption_entry(self):
        out=drive(IDS[9],brs=abs_bars(),funding=None,sym="ENJUSDT"); self.assertEqual(len(out),1)
class TestRefusals(unittest.TestCase):
    def test_no_breakout_refuses(self): self.assertEqual(drive(IDS[1],brs=bars(breakout=False)),[])
    def test_positive_funding_refuses(self): self.assertEqual(drive(IDS[1],funding=0.001),[])
    def test_missing_funding_refuses(self): self.assertEqual(drive(IDS[1],funding=None),[])
    def test_short_history_refuses(self): self.assertEqual(drive(IDS[1],brs=bars(n=20)),[])
    def test_absorption_short_history_refuses(self): self.assertEqual(drive(IDS[9],brs=abs_bars()[:200],sym="ENJUSDT"),[])
    def test_occupied_refuses(self): self.assertEqual(drive(IDS[1],positions=pos(hours=1)),[])
class TestExits(unittest.TestCase):
    def test_fixed16_exit(self):
        out=drive(IDS[0],positions=pos(hours=17)); self.assertEqual([o.kind for o in out],["exit"])
    def test_fixed16_not_yet(self): self.assertEqual(drive(IDS[0],positions=pos(hours=8)),[])
    def test_fixed96_exit(self):
        self.assertEqual(len(drive(IDS[1],positions=pos(hours=97))),1); self.assertEqual(drive(IDS[1],positions=pos(hours=20)),[])
    def test_lost_breakout_exit(self):
        b=bars(breakout=False); b[-1]["c"]=1.02
        self.assertEqual(len(drive(IDS[3],brs=b,positions=pos(hours=2))),1)
    def test_normalization_exit(self):
        self.assertEqual(len(drive(IDS[7],funding=0.0,positions=pos(hours=2))),1)
        self.assertEqual(drive(IDS[7],funding=-0.01,positions=pos(hours=2)),[])
    def test_norm_failure_exit_after_delay(self):
        b=bars(breakout=False); b[-1]["c"]=0.90; b[-1]["l"]=0.90  # below prior-3 lowest low 0.95
        for bar in b: bar["t"]=(datetime.fromisoformat(bar["t"])-timedelta(hours=8)).isoformat()  # signal bar closed 8h ago: 4h bar + 4h delay met
        self.assertEqual(len(drive(IDS[5],brs=b,funding=0.002,positions=pos(hours=20))),1)
    def test_norm_failure_no_exit_before_delay(self):
        b=bars(breakout=False); b[-1]["c"]=0.90
        self.assertEqual(drive(IDS[5],brs=b,funding=0.002,positions=pos(hours=2)),[])
    def test_absorption_fixed16_exit(self):
        self.assertEqual(len(drive(IDS[9],brs=abs_bars(),funding=None,positions=pos(hours=17,sym="ENJUSDT"),sym="ENJUSDT")),1)
    def test_deadline_survives_missing_inputs(self):
        out=drive(IDS[3],brs=[],funding=None,positions=pos(hours=100)); self.assertEqual(len(out),1)
class TestRegistryAndE2E(unittest.TestCase):
    def test_config_rows_and_inputs(self):
        from desk3.aster_batch6 import config_rows
        rows={r["id"]:r for r in config_rows()}; self.assertEqual(sorted(rows),sorted(IDS))
        cfg=json.load(open(os.path.join(ROOT,"config","sleeves.json"))); have={r["id"]:r for r in cfg["sleeves"]}
        for sid in IDS:
            self.assertIn(sid,have); self.assertEqual(have[sid]["inputs"],rows[sid]["inputs"])
            self.assertEqual(list(importlib.import_module(f"adapters3.{sid}").INPUTS),rows[sid]["inputs"])
    def test_e2e_roundtrip_fake_broker(self):
        from desk3.broker import FakeBroker
        from desk3.dispatcher import Dispatcher
        sid=IDS[1]; out=drive(sid); self.assertEqual(len(out),1)
        tmp=tempfile.mkdtemp(); broker=FakeBroker(prices={"ADAUSDT":1.10})
        disp=Dispatcher(tmp,broker,slices={sid:{"capital_usd":11000.0,"cash_usd":11000.0}},price_lookup=lambda s:1.10)  # headroom for dispatcher's 2% BP buffer over the fullcash intent
        def as_dict(i,n):
            return {"intent_id":f"{sid}-e2e-{n}","kind":"entry" if i.kind=="enter" else "exit",
                    "symbol":i.symbol,"side":i.side,"qty":i.qty,"order_type":"market"}
        r=disp.process_intent(as_dict(out[0],1),sid); self.assertEqual(r["status"],"filled")
        held=disp.slice_for(sid)["positions"]; self.assertIn("ADA/USD",held)  # BLOCKED-EXIT-20261029: broker dialect at the door
        ex=drive(sid,positions=pos(hours=100,qty=held["ADA/USD"]["qty"]))
        r2=disp.process_intent(as_dict(ex[0],2),sid); self.assertEqual(r2["status"],"filled")
        self.assertEqual(disp.slice_for(sid)["positions"],{})
if __name__=="__main__": unittest.main()
