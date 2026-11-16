"""Blockers: Aster batch 2 (pead x4, core_reserve x2, recovery RSI2 long fixed/touch x4) — ASTER-B2-1.
Source: archive r19_options.py + options_rules.json books OPT_PEAD_*, OPT_QQQ95_*, OPT_RSI2_*.
Fail direction: pre-build none of adapters3.aster_* exist (imports error)."""
import importlib, json, os, sys, unittest
from datetime import date, timedelta
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,ROOT)
EPOCH=date(1970,1,1); START=date(2025,1,1)
def bars(closes,start=START,vol=10000):
    return [{"t":float(((start+timedelta(days=i))-EPOCH).days*86400),"o":c,"h":c*1.001,"l":c*.999,"c":c,"v":vol} for i,c in enumerate(closes)]
def ctx(sid,session="2025-10-06",**kw):
    c={"sleeve_id":sid,"session":session,"now":session+"T09:37:00","equity":10000.0}; c.update(kw); return c
def ev(sid,view,c=None):
    return importlib.import_module(f"adapters3.{sid}").evaluate(view,c or ctx(sid))
def rsi2_series(n=210):
    # uptrend above SMA200 with final dip -> RSI2<10: long rise then sharp 2-day drop
    cl=[100+0.5*i for i in range(n-3)]+[200.0,190.0,180.0]
    return cl
def chain(sym="SPY",spot=180.0,right="call",dte=17,delta=0.55,ask=0.4,bid=0.35,strike=None,wing_ask=0.25,wing_bid=0.2):
    exp=(date(2025,10,6)+timedelta(days=dte)).isoformat(); strike=strike or spot
    out=[{"symbol":f"{sym}251023C00180000","underlying":sym,"right":right,"expiry":exp,"strike":strike,"delta":delta if right=="call" else -delta,"bid":bid,"ask":ask,"bid_size":50,"ask_size":50}]
    ws=strike+5 if right=="call" else strike-5
    out.append({"symbol":f"{sym}WING","underlying":sym,"right":right,"expiry":exp,"strike":ws,"delta":0.3 if right=="call" else -0.3,"bid":wing_bid,"ask":wing_ask,"bid_size":50,"ask_size":50})
    return out
def opt_pos(sid,held=0,entry_spot=180.0,structure="long"):
    legs=[{"symbol":"SPY251023C00180000","underlying":"SPY","right":"call","expiry":"2025-10-23","strike":180.0,"ratio":1}]
    if structure=="vertical": legs.append({"symbol":"SPYWING","underlying":"SPY","right":"call","expiry":"2025-10-23","strike":185.0,"ratio":-1})
    return [{"symbol":"SPY251023C00180000","qty":2,"avg_price":2.0,"entry_spot":entry_spot,"sessions_held":held,"legs":legs,"opened_at":"2025-10-06"}]
IDS=["aster_pead_long_a","aster_pead_long_b","aster_pead_vertical_a","aster_pead_vertical_b","aster_core_rsi2_long","aster_core_rsi2_vertical","aster_rec_rsi2_long_fixed_a","aster_rec_rsi2_long_fixed_b","aster_rec_rsi2_long_touch_a","aster_rec_rsi2_long_touch_b"]
class TestRegistry(unittest.TestCase):
    def test_config_rows_and_inputs(self):
        cfg={s["id"]:s for s in json.load(open(os.path.join(ROOT,"config/sleeves.json")))["sleeves"]}
        for sid in IDS:
            self.assertIn(sid,cfg); self.assertEqual(cfg[sid]["slice"]["capital_usd"],10000.0)
            self.assertEqual(cfg[sid]["module"],f"adapters3.{sid}")
            for k in ("bars","options","positions"): self.assertIn(k,cfg[sid]["inputs"])
        self.assertIn("earnings_events",cfg["aster_pead_long_a"]["inputs"])
class TestRecovery(unittest.TestCase):
    def view(self):
        return {"bars":{"SPY":bars(rsi2_series())},"options":chain(),"positions":[]}
    def test_entry_fixed_a_and_b_risk_sizing(self):
        a=ev("aster_rec_rsi2_long_fixed_a",self.view()); b=ev("aster_rec_rsi2_long_fixed_b",self.view())
        self.assertEqual(len(a),1); self.assertEqual(a[0]["kind"],"entry")
        # A risk $200, B risk $50; per-contract ~$200.65 -> A qty>=B qty
        self.assertGreaterEqual(a[0]["qty"],b[0]["qty"]); self.assertGreaterEqual(b[0]["qty"],1)
    def test_entry_vertical(self):
        # vertical sleeves are in batch 3 for recovery; here core vertical entry proves vertical shape
        v={"bars":{"QQQ":bars(rsi2_series())},"options":chain("QQQ"),"positions":[{"symbol":"QQQ","qty":52,"avg_price":180.0}]}
        out=ev("aster_core_rsi2_vertical",v)
        self.assertEqual(len(out),1); self.assertEqual(len(out[0]["legs"]),2)
    def test_refusals(self):
        self.assertEqual(ev("aster_rec_rsi2_long_fixed_a",{"bars":{},"options":chain(),"positions":[]}),[])  # warmup
        flat={"bars":{"SPY":bars([100.0]*210)},"options":chain(spot=100.0),"positions":[]}
        self.assertEqual(ev("aster_rec_rsi2_long_fixed_a",flat),[])  # no dip / not above SMA pattern
        self.assertEqual(ev("aster_rec_rsi2_long_fixed_a",{"bars":{"SPY":bars(rsi2_series())},"options":[],"positions":[]}),[])  # no contract
        bad=chain(); bad[0]["ask"]=20.0; bad[0]["bid"]=19.0  # premium cap exceeded
        self.assertEqual(ev("aster_rec_rsi2_long_fixed_b",{"bars":{"SPY":bars(rsi2_series())},"options":bad,"positions":[]}),[])
    def test_exit_fixed_planned_not_touch(self):
        v={"bars":{"SPY":bars([185.0]*10)},"options":chain(),"positions":opt_pos("x",held=5)}
        out=ev("aster_rec_rsi2_long_fixed_a",v); self.assertEqual([o["kind"] for o in out],["exit"]); self.assertIn("planned",out[0]["reason"])
        v2={"bars":{"SPY":bars([185.0]*10)},"options":chain(),"positions":opt_pos("x",held=2)}
        self.assertEqual(ev("aster_rec_rsi2_long_fixed_a",v2),[])  # +2.7% touch does NOT exit fixed
    def test_exit_touch(self):
        v={"bars":{"SPY":bars([185.0]*10)},"options":chain(),"positions":opt_pos("x",held=2)}
        out=ev("aster_rec_rsi2_long_touch_a",v); self.assertEqual([o["kind"] for o in out],["exit"]); self.assertIn("touch",out[0]["reason"])
        v2={"bars":{"SPY":bars([181.0]*10)},"options":chain(),"positions":opt_pos("x",held=2)}
        self.assertEqual(ev("aster_rec_rsi2_long_touch_a",v2),[])  # below +2%
        v3={"bars":{"SPY":bars([170.0]*10)},"options":chain(),"positions":opt_pos("x",held=5)}
        self.assertEqual([o["kind"] for o in ev("aster_rec_rsi2_long_touch_a",v3)],["exit"])  # planned at hold
class TestPead(unittest.TestCase):
    def view(self, surprise=-0.05, threshold=-0.02):
        evv={"symbol":"ACME","event_id":"E1","surprise":surprise,"threshold":threshold,"spot_at_signal":50.0,"mean20_dollar_volume":5000000,"entry_session":"2025-10-06","event_date":"2025-10-01"}
        return {"bars":{"ACME":bars([50.0]*30)},"options":chain("ACME",spot=50.0,right="put",strike=50.0,dte=28),"positions":[],"earnings_events":[evv]}
    def test_entry_long_put(self):
        out=ev("aster_pead_long_a",self.view()); self.assertEqual(len(out),1); self.assertEqual(out[0]["legs"][0]["right"],"put")
    def test_entry_vertical(self):
        out=ev("aster_pead_vertical_b",self.view()); self.assertEqual(len(out),1); self.assertEqual(len(out[0]["legs"]),2)
    def test_refusals(self):
        self.assertEqual(ev("aster_pead_long_a",self.view(surprise=0.03)),[])  # above 20th pct
        v=self.view(); v["earnings_events"][0]["mean20_dollar_volume"]=500000; self.assertEqual(ev("aster_pead_long_a",v),[])
        v=self.view(); v["earnings_events"][0]["spot_at_signal"]=4.0; self.assertEqual(ev("aster_pead_long_a",v),[])
        v=self.view(); v["earnings_events"][0]["entry_session"]="2025-10-07"; self.assertEqual(ev("aster_pead_long_a",v),[])
        v=self.view(); v["earnings_events"]=[]; self.assertEqual(ev("aster_pead_long_a",v),[])
    def test_exit_planned_hold10(self):
        p=opt_pos("x",held=10); p[0]["legs"][0]["right"]="put"
        v={"bars":{"SPY":bars([180.0]*10)},"options":chain(),"positions":p}
        self.assertEqual([o["kind"] for o in ev("aster_pead_long_a",v)],["exit"])
        p=opt_pos("x",held=9); v["positions"]=p; self.assertEqual(ev("aster_pead_long_a",v),[])
class TestCore(unittest.TestCase):
    def test_core_initial_entry_95pct(self):
        v={"bars":{"QQQ":bars([100.0]*210)},"options":chain("QQQ",spot=100.0),"positions":[]}
        out=ev("aster_core_rsi2_long",v); self.assertEqual(len(out),1); self.assertEqual(out[0]["symbol"],"QQQ"); self.assertAlmostEqual(out[0]["qty"]*100,9500,delta=200)
    def test_core_no_exit_and_option_entry_when_core_held(self):
        v={"bars":{"QQQ":bars(rsi2_series())},"options":chain("QQQ"),"positions":[{"symbol":"QQQ","qty":52,"avg_price":180.0}]}
        out=ev("aster_core_rsi2_long",v); self.assertEqual(len(out),1); self.assertEqual(out[0]["kind"],"entry"); self.assertNotEqual(out[0]["symbol"],"QQQ")
class TestE2E(unittest.TestCase):
    def test_round_trip_fake_broker(self):
        from desk3.broker import FakeBroker
        from desk3.dispatcher import Dispatcher
        import inspect
        # Drive entry intent through FakeBroker submit/read-back, then exit to flat.
        b=FakeBroker(prices={"SPY251023C00180000":2.0})
        view={"bars":{"SPY":bars(rsi2_series())},"options":chain(),"positions":[]}
        e=ev("aster_rec_rsi2_long_fixed_a",view)[0]
        r=b.submit_order("v3-test-1",e["symbol"],"buy",e["qty"],"market")
        got=b.get_order_by_client_id("v3-test-1"); self.assertIn(got.get("status"),("filled","closed","accepted","new"))
        v2={"bars":{"SPY":bars([185.0]*10)},"options":chain(),"positions":opt_pos("x",held=5)}
        x=ev("aster_rec_rsi2_long_fixed_a",v2)[0]; self.assertEqual(x["kind"],"exit")
        b.submit_order("v3-test-2",x["symbol"],"sell",e["qty"],"market"); b.get_order_by_client_id("v3-test-2")
        self.assertEqual(b.get_positions(),{})  # round-trip to flat
if __name__=="__main__": unittest.main()
