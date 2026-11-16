import os,sys,unittest,json,importlib
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,ROOT)
IDS=["aster_etf_leader1_m150","aster_etf_qld_buy_hold","aster_etf_qld_monthly","aster_etf_qqq_buy_hold","aster_etf_qqq_monthly_c098","aster_etf_qqq_monthly_m150","aster_etf_qqq_qld_buy_hold","aster_etf_qqq_qld_monthly","aster_etf_smh_hold_c098","aster_etf_smh_hold_m150"]
def bars(px,n=130,start=100.0):
    # first close = start, last = px (126-session return = px/start-1 approx using b[-127])
    out=[]
    for i in range(n):
        c=start if i<n-1 else px
        out.append({"t":f"2026-01-{(i%28)+1:02d}","o":c,"h":c,"l":c,"c":c,"v":1000})
    return out
def flat_bars(px,n=130):
    return [{"t":f"2026-01-{(i%28)+1:02d}","o":px,"h":px,"l":px,"c":px,"v":1000} for i in range(n)]
CTX={"session":"2026-10-01","now":"2026-10-01T09:36:00","slice":{"capital_usd":10000.0}}
def V(barsmap,positions=None,now="2026-10-01T09:36:00",extra=None):
    return {"now":now,"bars":barsmap,"positions":positions or [],"quotes":{},"extra":extra or {}}
def ev(sid,v,ctx=None): return importlib.import_module(f"adapters3.{sid}").evaluate(v,dict(ctx or CTX))
def ev2(sid,v,ctx=None):
    # WEIGHT-LAG-ACTIVE-20261031: aster_etf acts on the PREVIOUS
    # evaluation's targets. Clear stale pending state, then drive two
    # evaluations: the first computes weights and emits nothing, the
    # second acts on them. Returns (first, second).
    from desk3 import aster_etf
    aster_etf._PENDING_TARGETS.pop(sid,None)
    return ev(sid,v,ctx), ev(sid,v,ctx)
def basket(leader="XLK"):
    # HARDEN batch-1 fidelity cure: LEADER1 eligibility is the source's
    # 252-session window (r19_etf._scores), so leader fixtures carry 260.
    m={s:flat_bars(100.0,n=260) for s in ["QQQ","SPY","SMH","XLB","XLC","XLE","XLF","XLI","XLK","XLP","XLRE","XLU","XLV","XLY"]}
    m[leader]=bars(120.0,n=260)  # +20% over window vs flat 0%
    return m
class T(unittest.TestCase):
    def test_leader_entry_150(self):
        first,o=ev2("aster_etf_leader1_m150",V(basket()))
        self.assertEqual(first,[])  # weight lag: first evaluation emits nothing
        self.assertEqual(len(o),1); self.assertEqual(o[0]["symbol"],"XLK"); self.assertEqual(o[0]["qty"],125)  # 1.5*10000/120
        self.assertEqual(o[0]["kind"],"entry")
    def test_leader_tie_alphabetical(self):
        m=basket(); m["XLK"]=flat_bars(100.0,n=260)  # all flat -> tie -> QQQ first alphabetically among basket? QQQ<SMH<SPY<XLB...
        first,o=ev2("aster_etf_leader1_m150",V(m))
        self.assertEqual(first,[])  # weight lag: first evaluation emits nothing
        self.assertEqual(o[0]["symbol"],"QQQ")
    def test_leader_rotation_exit_to_flat(self):
        pos=[{"symbol":"XLK","qty":125,"avg_price":120.0,"entry_date":"2026-09-02"}]
        m=basket(leader="XLE"); m["XLK"]=flat_bars(120.0,n=260)
        first,o=ev2("aster_etf_leader1_m150",V(m,positions=pos,now="2026-10-01T09:36:00"))
        self.assertEqual(first,[])  # weight lag: first evaluation emits nothing
        sells=[x for x in o if x["side"]=="sell"]; buys=[x for x in o if x["side"]=="buy"]
        self.assertEqual(sells[0]["symbol"],"XLK"); self.assertEqual(sells[0]["qty"],125); self.assertEqual(sells[0]["kind"],"exit")
        self.assertLess(o.index(sells[0]),o.index(buys[0]))  # sells before buys
    def test_fixed_entries(self):
        cases={"aster_etf_qld_buy_hold":("QLD",100),"aster_etf_qld_monthly":("QLD",100),"aster_etf_qqq_buy_hold":("QQQ",100),
               "aster_etf_qqq_monthly_c098":("QQQ",98),"aster_etf_qqq_monthly_m150":("QQQ",150),
               "aster_etf_smh_hold_c098":("SMH",98),"aster_etf_smh_hold_m150":("SMH",150)}
        for sid,(sym,qty) in cases.items():
            first,o=ev2(sid,V({sym:flat_bars(100.0)}))
            self.assertEqual(first,[],sid)  # weight lag: first evaluation emits nothing
            self.assertEqual(len(o),1,sid); self.assertEqual(o[0]["qty"],qty,sid)
        first,o=ev2("aster_etf_qqq_qld_buy_hold",V({"QQQ":flat_bars(100.0),"QLD":flat_bars(50.0)}))
        self.assertEqual(first,[])  # weight lag: first evaluation emits nothing
        self.assertEqual({x["symbol"]:x["qty"] for x in o},{"QQQ":50,"QLD":100})
        first,o=ev2("aster_etf_qqq_qld_monthly",V({"QQQ":flat_bars(100.0),"QLD":flat_bars(50.0)}))
        self.assertEqual(first,[])  # weight lag: first evaluation emits nothing
        self.assertEqual({x["symbol"]:x["qty"] for x in o},{"QQQ":50,"QLD":100})
    def test_buy_hold_never_exits(self):
        for sid,sym in [("aster_etf_qld_buy_hold","QLD"),("aster_etf_qqq_buy_hold","QQQ"),("aster_etf_smh_hold_c098","SMH")]:
            pos=[{"symbol":sym,"qty":50,"avg_price":100.0,"entry_date":"2026-09-02"}]
            self.assertEqual(ev(sid,V({sym:flat_bars(50.0)},positions=pos,now="2026-11-02T09:36:00")),[],sid)
    def test_monthly_rebalance_reduce_and_no_churn_same_month(self):
        pos=[{"symbol":"QQQ","qty":150,"avg_price":100.0,"entry_date":"2026-09-02"}]
        first,o=ev2("aster_etf_qqq_monthly_c098",V({"QQQ":flat_bars(100.0)},positions=pos,now="2026-10-01T09:36:00"))
        self.assertEqual(first,[])  # weight lag: first evaluation emits nothing
        self.assertEqual(len(o),1); self.assertEqual(o[0]["side"],"sell"); self.assertEqual(o[0]["qty"],52)
        pos[0]["entry_date"]="2026-10-01"
        self.assertEqual(ev("aster_etf_qqq_monthly_c098",V({"QQQ":flat_bars(100.0)},positions=pos)),[])
    def test_refusals_window_and_missing_bars(self):
        # CR-1 (2026-11-11): flat BUY_HOLD sleeves joined the
        # same-session catch-up treatment, so at 10:00 ET an
        # evaluation with lagged targets pending now legitimately
        # emits. The refusal pin is the UNPRIMED first evaluation:
        # clear pending, then the outside-window call emits nothing.
        from desk3 import aster_etf as _ae
        _ae._PENDING_TARGETS.pop("aster_etf_qqq_buy_hold", None)
        self.assertEqual(ev("aster_etf_qqq_buy_hold",V({"QQQ":flat_bars(100.0)},now="2026-10-01T10:00:00")),[])
        self.assertEqual(ev("aster_etf_qqq_buy_hold",V({})),[])
        self.assertEqual(ev("aster_etf_leader1_m150",V({"QQQ":flat_bars(100.0,n=10)})),[])  # insufficient history
    def test_e2e_fake_broker_round_trip_to_flat(self):
        from desk3.broker import FakeBroker
        b=FakeBroker(prices={"XLK":120.0,"XLE":100.0})
        first,o=ev2("aster_etf_leader1_m150",V(basket()))
        self.assertEqual(first,[])  # weight lag: first evaluation emits nothing
        for i in o: b.get_order_by_client_id(b.submit_order(f"r1-{i['intent_id']}",i["symbol"],i["side"],i["qty"],"market")["client_order_id"])
        self.assertEqual(b.get_positions(),{"XLK":125.0})
        pos=[{"symbol":"XLK","qty":125,"avg_price":120.0,"entry_date":"2026-09-02"}]
        m=basket(leader="XLE"); m["XLK"]=flat_bars(120.0,n=260)
        first2,o2=ev2("aster_etf_leader1_m150",V(m,positions=pos))
        self.assertEqual(first2,[])  # weight lag: rotation targets held one evaluation
        b.prices["XLE"]=100.0
        for i in o2: b.get_order_by_client_id(b.submit_order(f"r2-{i['intent_id']}",i["symbol"],i["side"],i["qty"],"market")["client_order_id"])
        self.assertNotIn("XLK",b.get_positions())  # old leader flat after rotation exit
    def test_config_and_inputs(self):
        cfg=json.load(open(os.path.join(ROOT,"config","sleeves.json")))
        for sid in IDS:
            rows=[s for s in cfg["sleeves"] if s["id"]==sid]; self.assertEqual(len(rows),1,sid)
            self.assertEqual(rows[0]["slice"]["capital_usd"],10000.0)
            m=importlib.import_module(f"adapters3.{sid}"); self.assertEqual(tuple(rows[0]["inputs"]),m.INPUTS)
if __name__=="__main__": unittest.main()
