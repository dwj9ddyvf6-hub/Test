import os,sys,unittest,json,tempfile
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,ROOT)
CTX={"session":"2026-10-24","now":"2026-10-24T15:00:00"}
CRYPTO="aster_link_nfs_norm_vol"
TENSOR=["aster_tensor_beta_cash_all_25","aster_tensor_c1_cash_all_25","aster_tensor_c1_delay_all_25","aster_tensor_c1_reserve_all_25","aster_tensor_c1_cash_cool_25","aster_tensor_c1_delay_cool_25","aster_tensor_c1_reserve_cool_25","aster_tensor_c1_cash_hot_25","aster_tensor_c1_delay_hot_25"]
def ev(sid,v,ctx=None):
    import importlib; return importlib.import_module(f"adapters3.{sid}").evaluate(v,dict(ctx or CTX))
def bars4h(closes_high=10.0,last_close=11.0,vol=100000):
    b=[{"t":f"h{i}","o":10,"h":closes_high,"l":9,"c":10,"v":vol} for i in range(20)]
    b.append({"t":"h20","o":10,"h":last_close,"l":9,"c":last_close,"v":vol}); return b
def cview(funding=-0.001,bars=None,positions=None):
    return {"now":CTX["now"],"bars":{"LINKUSDT":bars if bars is not None else bars4h()},"funding":{"LINKUSDT":funding} if funding is not None else {},"positions":positions or [],"extra":{}}
def fire(sid,sym="AAA",price=4.0,date="2026-10-23",**kw):
    f={"sleeve_id":sid,"symbol":sym,"signal":"buy-cyan","date":date,"price":price,"ret60":40,"vol20":0.1,"adv_usd":3000000,"atr_ratio":0.5}
    f.update(kw); return f
def tview(sid,fires,positions=None,barsmap=None):
    return {"now":CTX["now"],"tensor":{"fires":fires},"bars":barsmap or {},"positions":positions or [],"extra":{}}
class T(unittest.TestCase):
    # --- crypto ---
    def test_crypto_entry_volume_cap(self):
        o=ev(CRYPTO,cview()); self.assertEqual(len(o),1); self.assertEqual(o[0]["kind"],"entry")
        # min(1% of 100000=1000 units, 10000/11=909.09) -> cash binds
        self.assertAlmostEqual(o[0]["qty"],909.090909,places=4)
        o=ev(CRYPTO,cview(bars=bars4h(vol=1000))); self.assertAlmostEqual(o[0]["qty"],10.0)  # 1% vol binds
    def test_crypto_refusals(self):
        self.assertEqual(ev(CRYPTO,cview(funding=0.001)),[])  # non-negative funding
        self.assertEqual(ev(CRYPTO,cview(funding=None)),[])   # missing funding = no entry
        self.assertEqual(ev(CRYPTO,cview(bars=bars4h(last_close=9.5))),[])  # no breakout
        self.assertEqual(ev(CRYPTO,cview(bars=bars4h()[:10])),[])  # insufficient bars
    def test_crypto_exit_normalization(self):
        pos=[{"symbol":"LINKUSDT","qty":50,"avg_price":10.0,"hours_held":4}]
        o=ev(CRYPTO,cview(funding=0.0,positions=pos)); self.assertEqual(len(o),1); self.assertIn("funding_normalization",o[0]["reason"])
        o=ev(CRYPTO,cview(funding=-0.002,positions=pos)); self.assertEqual(o,[])  # still negative: hold
    def test_crypto_exit_deadline_without_funding(self):
        pos=[{"symbol":"LINKUSDT","qty":50,"avg_price":10.0,"hours_held":96}]
        o=ev(CRYPTO,cview(funding=None,positions=pos)); self.assertEqual(len(o),1); self.assertIn("deadline_96h",o[0]["reason"])
        pos[0]["hours_held"]=95; self.assertEqual(ev(CRYPTO,cview(funding=None,positions=pos)),[])
    # --- tensor entries ---
    def test_c1_cash_entry_and_ticket(self):
        sid="aster_tensor_c1_cash_all_25"; o=ev(sid,tview(sid,[fire(sid)])); self.assertEqual(len(o),1); self.assertEqual(o[0]["qty"],100)  # $400/$4
    def test_beta_entry(self):
        sid="aster_tensor_beta_cash_all_25"; f=fire(sid,sym="BBB",price=20.0,signal="m2-beta-cohort",m2_qualified=True)
        o=ev(sid,tview(sid,[f])); self.assertEqual(len(o),1); self.assertEqual(o[0]["qty"],20)
        f["m2_qualified"]=False; self.assertEqual(ev(sid,tview(sid,[f])),[])
    def test_c1_gate_refusals(self):
        sid="aster_tensor_c1_cash_all_25"
        # AMENDED 2026-11-12 (GATE-CURE-20261112, STRICTNESS-CENSUS
        # proposal 4): the all variants' close cap is removed and
        # ret60 relaxes 31 -> 0, so price 5.01 and ret60 30 now
        # ENTER; the remaining gates still refuse, and ret60 below
        # the new 0 floor still refuses. Pre-amendment pin preserved
        # in ~/workspace/.gatecure-20261112/pre/tests/.
        # AMENDED AGAIN 2026-11-14 (STRICTNESS-ROUND2-COMPLETION-
        # 20261114, CADENCE-SWEEPS S3 row R2): the all trio takes
        # the swept registered form — buy-cyan marker removed,
        # ret60 floor restored to 31 — so a buy-green (marker-free)
        # fire now ENTERS and ret60 30 / 0 now REFUSE. The
        # marker-required behavior survives on the cool variant
        # (test_cool_hot_split and the round-2 completion
        # blockers). Pre-amendment copy preserved in
        # ~/workspace/.gatecure-20261114/pre/tests/.
        for kw in ({"price":5.01},{"signal":"buy-green"}):
            self.assertEqual(len(ev(sid,tview(sid,[fire(sid,**kw)]))),1,kw)
        for kw in ({"ret60":30},{"ret60":0},{"ret60":-1},{"vol20":0.06},{"adv_usd":1999999}):
            self.assertEqual(ev(sid,tview(sid,[fire(sid,**kw)])),[],kw)
        self.assertEqual(ev(sid,tview(sid,[])),[])
    def test_cool_hot_split(self):
        cool="aster_tensor_c1_cash_cool_25"; hot="aster_tensor_c1_cash_hot_25"
        self.assertEqual(len(ev(cool,tview(cool,[fire(cool,atr_ratio=0.5)]))),1)
        self.assertEqual(ev(cool,tview(cool,[fire(cool,atr_ratio=1.5)])),[])
        self.assertEqual(len(ev(hot,tview(hot,[fire(hot,atr_ratio=1.5)]))),1)
        self.assertEqual(ev(hot,tview(hot,[fire(hot,atr_ratio=0.5)])),[])
        f=fire(cool); del f["atr_ratio"]; self.assertEqual(ev(cool,tview(cool,[f])),[])  # missing atr fail-closed
    def test_delay_and_reserve_wait_one_session(self):
        for sid in ("aster_tensor_c1_delay_all_25","aster_tensor_c1_reserve_all_25"):
            self.assertEqual(ev(sid,tview(sid,[fire(sid,date="2026-10-24")])),[],sid)  # same session: wait
            self.assertTrue(any(i["kind"]=="entry" for i in ev(sid,tview(sid,[fire(sid,date="2026-10-23")]))),sid)
        sid="aster_tensor_c1_cash_all_25"; self.assertEqual(len(ev(sid,tview(sid,[fire(sid,date="2026-10-24")]))),1)  # cash: no wait
    def test_reserve_qqq_funding_exit(self):
        sid="aster_tensor_c1_reserve_cool_25"
        pos=[{"symbol":"QQQ","qty":10,"avg_price":400.0,"sessions_held":3}]
        v=tview(sid,[fire(sid)],positions=pos,barsmap={"QQQ":[{"t":"d","o":400,"h":400,"l":400,"c":400,"v":1}]})
        o=ev(sid,v); kinds=[(i["symbol"],i["kind"]) for i in o]; self.assertIn(("QQQ","exit"),kinds); self.assertIn(("AAA","entry"),kinds)
    def test_slots_and_duplicate_refusals(self):
        sid="aster_tensor_c1_cash_all_25"
        pos=[{"symbol":f"S{i}","qty":1,"avg_price":1.0,"sessions_held":1} for i in range(25)]
        self.assertEqual(ev(sid,tview(sid,[fire(sid)],positions=pos)),[])
        pos=[{"symbol":"AAA","qty":1,"avg_price":4.0,"sessions_held":1}]
        self.assertEqual(ev(sid,tview(sid,[fire(sid)],positions=pos)),[])
    # --- tensor exits ---
    def test_week52_exit_all_tensor_and_no_price_stop(self):
        for sid in TENSOR:
            pos=[{"symbol":"AAA","qty":10,"avg_price":4.0,"sessions_held":260}]
            v=tview(sid,[],positions=pos,barsmap={"AAA":[{"t":"d","o":4,"h":4,"l":4,"c":4,"v":1}]})
            if sid.startswith("aster_tensor_c1_reserve"):
                pos=[{"symbol":"AAA","qty":10,"avg_price":4.0,"sessions_held":260}]; v["positions"]=pos
            o=ev(sid,v); self.assertEqual(len(o),1,sid); self.assertIn("week52_deadline",o[0]["reason"],sid)
            pos2=[{"symbol":"AAA","qty":10,"avg_price":4.0,"sessions_held":10}]
            v2=tview(sid,[],positions=pos2,barsmap={"AAA":[{"t":"d","o":1,"h":1,"l":1,"c":1,"v":1}]})  # -75%: NO stop by design
            self.assertEqual(ev(sid,v2),[],sid)
    def test_config_inputs_unfed_funding(self):
        cfg=json.load(open(os.path.join(ROOT,"config","sleeves.json")))
        rows={s["id"]:s for s in cfg["sleeves"]}
        for sid in [CRYPTO]+TENSOR:
            self.assertIn(sid,rows); self.assertEqual(rows[sid]["slice"]["capital_usd"],10000.0)
        self.assertEqual(rows[CRYPTO]["inputs"],["bars","funding","positions"])  # funding producer absent -> UNFED, never fake-fed
        from desk3.registry import Registry
        r=Registry(); r.register_producer("bars",("bars",),900); r.register_producer("tensor_bundle",("tensor",),86400); r.register_producer("broker_readback",("positions",),900)
        r.register_sleeve(CRYPTO,rows[CRYPTO]["inputs"]); r.register_sleeve(TENSOR[1],rows[TENSOR[1]]["inputs"])
        for p in ("bars","tensor_bundle","broker_readback"): r.mark_produced(p,1000.0)
        st=r.fed_states(1000.0); self.assertEqual(st[CRYPTO]["state"],"UNFED"); self.assertEqual(st[TENSOR[1]]["state"],"FED")
    def test_e2e_roundtrip_fake_broker(self):
        from desk3.broker import FakeBroker
        from desk3.dispatcher import Dispatcher
        sid="aster_tensor_c1_cash_all_25"
        broker=FakeBroker(prices={"AAA":4.0}); disp=Dispatcher(tempfile.mkdtemp(),broker,slices={sid:{"capital_usd":10000.0,"cash_usd":10000.0}},price_lookup=lambda s:4.0)
        entry=ev(sid,tview(sid,[fire(sid)]))[0]; r=disp.process_intent(entry,sid); self.assertEqual(r["status"],"filled")
        self.assertEqual(broker.get_positions(),{"AAA":100.0})
        pos=[{"symbol":"AAA","qty":100,"avg_price":4.0,"sessions_held":260}]
        xv=tview(sid,[],positions=pos,barsmap={"AAA":[{"t":"d","o":4,"h":4,"l":4,"c":4,"v":1}]}); xv["now"]="2027-10-23T15:00:00"
        exit_i=ev(sid,xv,ctx={"session":"2027-10-23","now":"2027-10-23T15:00:00"})[0]
        r=disp.process_intent(exit_i,sid); self.assertEqual(r["status"],"filled"); self.assertEqual(broker.get_positions(),{})
if __name__=="__main__": unittest.main()
