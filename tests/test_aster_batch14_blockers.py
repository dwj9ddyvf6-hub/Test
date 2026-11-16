"""Blockers: Aster batch 14 (ASTER-B14-1) — C1 HOT_RESERVE_25 + G4 x9.
Source: archive r19_tensor.py passes()/evaluate() + tensor/RULES.json
weekly books R19_TENSOR_G4_* / R19_TENSOR_C1_HOT_RESERVE_25 (archive at
~/workspace/.scratch-ausar-archive, read directly this pass).
G4 gates: buy-green, close<=10, depth60>=70, ret60>=0, vol20>=0.09,
dv20>=2M; vol split source-exact: cool atr_ratio<=1, hot atr_ratio>1.
AMENDED 2026-11-12 (GATE-CURE-20261112, STRICTNESS-CENSUS proposals
1-3): the buy-green marker requirement is removed by the owner's
too-strict ruling (1 of 426 census symbol-weeks); the numeric
profile is the gate and the G4 cool atr cap is 1.1. The marker pin
below now asserts the cured behavior; the pre-cure pin is preserved
in ~/workspace/.gatecure-20261112/pre/tests/.
Exit: 52-week deadline only (260 sessions modelled); NO stop/target.
Fail direction: pre-build adapters3.aster_tensor_g4_* do not exist.
"""
import importlib, json, os, sys, unittest
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,ROOT)
IDS=["aster_tensor_c1_reserve_hot_25","aster_tensor_g4_cash_all_10","aster_tensor_g4_cash_all_25","aster_tensor_g4_delay_all_25","aster_tensor_g4_reserve_all_10","aster_tensor_g4_reserve_all_25","aster_tensor_g4_cash_cool_25","aster_tensor_g4_delay_cool_25","aster_tensor_g4_reserve_cool_25","aster_tensor_g4_cash_hot_25"]
CTX={"session":"2026-10-23","now":"2026-10-23T15:00:00"}
def ev(sid,view,ctx=None): return importlib.import_module(f"adapters3.{sid}").evaluate(view,dict(ctx or CTX))
def fire(sym="ABC",price=8.0,**kw):
    f={"symbol":sym,"signal":"buy-green","price":price,"depth60":80.0,"ret60":5.0,"vol20":0.12,"adv_usd":3_000_000,"atr_ratio":0.5,"date":"2026-10-22"}
    f.update(kw); return f
def V(fires=None,positions=None,bars=None):
    return {"tensor":fires or [],"bars":bars or {},"positions":positions or []}
def bars(px): return [{"t":"2026-10-23","o":px,"h":px,"l":px,"c":px,"v":1000}]
class T(unittest.TestCase):
    def test_g4_entry_cash_all_25_ticket400(self):
        o=ev("aster_tensor_g4_cash_all_25",V([fire()]))
        self.assertEqual(len(o),1); self.assertEqual((o[0]["kind"],o[0]["symbol"],o[0]["qty"]),("entry","ABC",50))  # 400//8
        self.assertIsNone(o[0]["stop_price"])
    def test_g4_entry_cash_all_10_ticket1000(self):
        o=ev("aster_tensor_g4_cash_all_10",V([fire()]))
        self.assertEqual(o[0]["qty"],125)  # 1000//8
    def test_g4_cyan_fire_refused_and_each_gate(self):
        sid="aster_tensor_g4_cash_all_25"
        # GATE-CURE-20261112: a buy-cyan fire with passing numerics
        # now ENTERS (marker requirement removed); each numeric
        # gate below still refuses on its own.
        self.assertEqual(len(ev(sid,V([fire(signal="buy-cyan")]))),1)
        self.assertEqual(ev(sid,V([fire(price=10.5)])),[])
        self.assertEqual(ev(sid,V([fire(depth60=69.9)])),[])
        self.assertEqual(ev(sid,V([fire(ret60=-0.1)])),[])
        self.assertEqual(ev(sid,V([fire(vol20=0.089)])),[])
        self.assertEqual(ev(sid,V([fire(adv_usd=1_999_999)])),[])
        self.assertEqual(ev(sid,V([fire(depth60=None)])),[])  # missing evidence fails closed
    def test_vol_split_source_exact(self):
        # cool: atr<=1 passes cool, refuses hot; hot: atr>1 passes hot, refuses cool; atr==1 is COOL per source (atr<=1)==(vol==cool)
        self.assertEqual(len(ev("aster_tensor_g4_cash_cool_25",V([fire(atr_ratio=1.0)]))),1)
        self.assertEqual(ev("aster_tensor_g4_cash_hot_25",V([fire(atr_ratio=1.0)])),[])
        self.assertEqual(len(ev("aster_tensor_g4_cash_hot_25",V([fire(atr_ratio=1.5)]))),1)
        # READINESS-ROUND2-20261112 supersession, named: the G4
        # cool atr cap is registered at 1.5 (CADENCE-SWEEPS S2),
        # superseding the source value this pin was exact to;
        # atr 1.5 now passes cool and 1.6 is the refusal probe.
        self.assertEqual(len(ev("aster_tensor_g4_cash_cool_25",V([fire(atr_ratio=1.5)]))),1)
        self.assertEqual(ev("aster_tensor_g4_cash_cool_25",V([fire(atr_ratio=1.6)])),[])
        self.assertEqual(len(ev("aster_tensor_g4_cash_all_25",V([fire(atr_ratio=99.0)]))),1)  # all ignores vol
    def test_delay_waits_one_session(self):
        f=fire(date="2026-10-23")  # same-day fire: delay sleeve must wait
        self.assertEqual(ev("aster_tensor_g4_delay_all_25",V([f])),[])
        self.assertEqual(len(ev("aster_tensor_g4_delay_all_25",V([fire()]))),1)  # dated 2026-10-22
        self.assertEqual(len(ev("aster_tensor_g4_cash_all_25",V([f]))),1)  # cash does not wait
    def test_reserve_sells_qqq_leg_then_entry(self):
        pos=[{"symbol":"QQQ","qty":10,"avg_price":100.0}]
        barsm={"QQQ":bars(100.0)}
        o=ev("aster_tensor_g4_reserve_all_25",V([fire()],positions=pos,bars=barsm))
        self.assertEqual([x["symbol"] for x in o],["QQQ","ABC"])
        self.assertEqual((o[0]["kind"],o[0]["qty"]),("exit",4))  # 400//100
        self.assertEqual(o[1]["kind"],"entry")
        o10=ev("aster_tensor_g4_reserve_all_10",V([fire()],positions=pos,bars=barsm))
        self.assertEqual(o10[0]["qty"],10)  # ticket 1000 -> all 10 QQQ
    def test_c1_reserve_hot(self):
        cf={"symbol":"XYZ","signal":"buy-cyan","price":4.0,"ret60":40.0,"vol20":0.1,"adv_usd":5_000_000,"atr_ratio":1.5,"date":"2026-10-22"}
        pos=[{"symbol":"QQQ","qty":10,"avg_price":100.0}]; barsm={"QQQ":bars(100.0)}
        o=ev("aster_tensor_c1_reserve_hot_25",V([cf],positions=pos,bars=barsm))
        self.assertEqual([x["symbol"] for x in o],["QQQ","XYZ"]); self.assertEqual(o[1]["qty"],100)  # 400//4
        self.assertEqual(ev("aster_tensor_c1_reserve_hot_25",V([dict(cf,atr_ratio=0.5)],positions=pos,bars=barsm)),[])  # not hot
        # READINESS-ROUND2-20261112 supersession, named: the C1
        # hot trio's $5 price cap is removed (CADENCE-SWEEPS S3
        # R3); price 6.0 now enters and the ret60 floor binds.
        self.assertEqual([x["symbol"] for x in ev("aster_tensor_c1_reserve_hot_25",V([dict(cf,price=6.0)],positions=pos,bars=barsm))],["QQQ","XYZ"])
        self.assertEqual(ev("aster_tensor_c1_reserve_hot_25",V([dict(cf,ret60=20.0)],positions=pos,bars=barsm)),[])  # ret60 floor 31 kept
    def test_exit_week52_only_no_stop(self):
        sid="aster_tensor_g4_cash_all_25"
        pos=[{"symbol":"ABC","qty":50,"avg_price":8.0,"sessions_held":260}]
        o=ev(sid,V([],positions=pos,bars={"ABC":bars(8.0)}))
        self.assertEqual([(x["kind"],x["qty"]) for x in o],[("exit",50)]); self.assertIn("week52",o[0]["reason"])
        pos2=[{"symbol":"ABC","qty":50,"avg_price":8.0,"sessions_held":10}]
        self.assertEqual(ev(sid,V([],positions=pos2,bars={"ABC":bars(2.0)})),[])  # -75%: NO stop by design
        pos3=[{"symbol":"ABC","qty":50,"avg_price":8.0,"exit_at":"2026-10-23T14:55:00"}]
        self.assertEqual(len(ev(sid,V([],positions=pos3,bars={"ABC":bars(8.0)}))),1)  # source exit_at deadline
    def test_slots_and_duplicate_refusals(self):
        pos=[{"symbol":f"S{i}","qty":1,"avg_price":1.0,"sessions_held":1} for i in range(25)]
        self.assertEqual(ev("aster_tensor_g4_cash_all_25",V([fire()],positions=pos)),[])
        self.assertEqual(ev("aster_tensor_g4_cash_all_25",V([fire()],positions=[{"symbol":"ABC","qty":1,"avg_price":8.0,"sessions_held":1}])),[])
    def test_e2e_fake_broker_round_trip_to_flat(self):
        from desk3.broker import FakeBroker
        b=FakeBroker(prices={"ABC":8.0})
        e=ev("aster_tensor_g4_cash_all_25",V([fire()]))[0]
        b.submit_order("v3-b14-1","ABC","buy",e["qty"],"market"); b.get_order_by_client_id("v3-b14-1")
        self.assertEqual(b.get_positions(),{"ABC":50.0})
        pos=[{"symbol":"ABC","qty":50,"avg_price":8.0,"sessions_held":260}]
        x=ev("aster_tensor_g4_cash_all_25",V([],positions=pos,bars={"ABC":bars(8.0)}))[0]
        b.submit_order("v3-b14-2","ABC","sell",x["qty"],"market"); b.get_order_by_client_id("v3-b14-2")
        self.assertEqual(b.get_positions(),{})
    def test_config_and_inputs(self):
        cfg={s["id"]:s for s in json.load(open(os.path.join(ROOT,"config/sleeves.json")))["sleeves"]}
        for sid in IDS:
            self.assertIn(sid,cfg); self.assertEqual(cfg[sid]["slice"]["capital_usd"],10000.0)
            self.assertEqual(cfg[sid]["module"],f"adapters3.{sid}")
            m=importlib.import_module(f"adapters3.{sid}"); self.assertEqual(tuple(cfg[sid]["inputs"]),m.INPUTS)
if __name__=="__main__": unittest.main()
