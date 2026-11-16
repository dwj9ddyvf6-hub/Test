"""Blockers: HARDEN Edge batch 12 — Tensor C1/G4 execution-price
revalidation (ENH-TENSOR13/14-REPRICE-20261024).

Binding leak: entry gates + ticket sizing used the signal-time fire
price while the market order fills at the current price; delay and
reserve sleeves execute >=1 session after the fire, so the design
price cap (C1 <=5, G4 <=10) could be violated at execution and qty
could overshoot the ticket. Treatment (default ON): when a current
bar exists, revalidate cap + size off the latest close; paired shadow
control (fire-price rule) recorded on the entry intent's
enhance_exp. Switch OFF restores the pre-change rule exactly.
Fail direction: on pre-change engines these tests fail (entries use
fire price / enter above cap); proven by stash 2026-10-24.
"""
import importlib, os, sys, unittest
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,ROOT)
CTX={"session":"2026-10-24","now":"2026-10-24T15:00:00"}
B13=["aster_tensor_c1_delay_all_25","aster_tensor_c1_delay_cool_25","aster_tensor_c1_delay_hot_25",
     "aster_tensor_c1_reserve_all_25","aster_tensor_c1_reserve_cool_25"]
B14C1=["aster_tensor_c1_reserve_hot_25"]
B14G4=["aster_tensor_g4_cash_all_10","aster_tensor_g4_cash_all_25","aster_tensor_g4_cash_cool_25",
       "aster_tensor_g4_cash_hot_25","aster_tensor_g4_delay_all_25","aster_tensor_g4_delay_cool_25"]
ALL=B13+B14C1+B14G4
def ev(sid,v,ctx=None):
    return importlib.import_module(f"adapters3.{sid}").evaluate(v,dict(ctx or CTX))
def bar(px): return [{"t":"d","o":px,"h":px,"l":px,"c":px,"v":1000}]
def c1fire(sid,price=4.0,atr=0.5):
    return {"sleeve_id":sid,"symbol":"AAA","signal":"buy-cyan","date":"2026-10-23",
            "price":price,"ret60":40,"vol20":0.1,"adv_usd":3000000,"atr_ratio":atr}
def g4fire(price=8.0,atr=0.5):
    return {"symbol":"ABC","signal":"buy-green","price":price,"depth60":80.0,"ret60":5.0,
            "vol20":0.12,"adv_usd":3000000,"atr_ratio":atr,"date":"2026-10-23"}
def view(fires,barsmap=None):
    return {"now":CTX["now"],"tensor":{"fires":fires},"bars":barsmap or {},"positions":[],"extra":{}}
def atr_for(sid):
    return 1.5 if sid.endswith("_hot_25") else 0.5
def off_ctx(sid):
    c=dict(CTX); c["enhance"]={sid:{"exec_reprice":False}}; return c

class T(unittest.TestCase):
    def test_c1_above_cap_current_price_refused_all(self):
        # AMENDED 2026-11-12 (GATE-CURE-20261112, STRICTNESS-CENSUS
        # proposal 4): the C1 all variants no longer carry a close
        # cap, so the revalidation follows the registered gate:
        # capped variants (cool, hot, batch14 reserve_hot) still
        # refuse at cur 6.0; the all variants now enter sized off
        # the current close. Pre-amendment pin preserved in
        # ~/workspace/.gatecure-20261112/pre/tests/.
        capped=["aster_tensor_c1_delay_cool_25","aster_tensor_c1_delay_hot_25",
                "aster_tensor_c1_reserve_cool_25"]+B14C1
        uncapped=["aster_tensor_c1_delay_all_25","aster_tensor_c1_reserve_all_25"]
        for sid in capped+uncapped:
            f=c1fire(sid,atr=atr_for(sid)) if sid in B13 else {
                "symbol":"AAA","signal":"buy-cyan","price":4.0,"ret60":40.0,"vol20":0.1,
                "adv_usd":5000000,"atr_ratio":1.5,"date":"2026-10-23"}
            o=ev(sid,view([f],{"AAA":bar(6.0)}))
            if sid in capped:
                self.assertEqual(o,[],sid)  # cur 6.0 > C1 cap 5: treatment refuses
            else:
                ent=[i for i in o if i["kind"]=="entry"]
                self.assertEqual(len(ent),1,sid)
                self.assertEqual(ent[0]["qty"],66,sid)  # 400//6.0 current close
    def test_c1_switch_off_restores_fire_price_rule(self):
        for sid in B13+B14C1:
            f=c1fire(sid,atr=atr_for(sid)) if sid in B13 else {
                "symbol":"AAA","signal":"buy-cyan","price":4.0,"ret60":40.0,"vol20":0.1,
                "adv_usd":5000000,"atr_ratio":1.5,"date":"2026-10-23"}
            o=ev(sid,view([f],{"AAA":bar(6.0)}),ctx=off_ctx(sid))
            self.assertEqual(len(o),1,sid)
            ent=[i for i in o if i["kind"]=="entry"][0]
            self.assertEqual(ent["qty"],100,sid)  # 400//4.0 fire price, pre-change
            self.assertEqual(ent["price_hint"],4.0,sid)
    def test_c1_reprice_sizes_off_current_close(self):
        for sid in B13+B14C1:
            f=c1fire(sid,atr=atr_for(sid)) if sid in B13 else {
                "symbol":"AAA","signal":"buy-cyan","price":4.0,"ret60":40.0,"vol20":0.1,
                "adv_usd":5000000,"atr_ratio":1.5,"date":"2026-10-23"}
            o=ev(sid,view([f],{"AAA":bar(4.5)}))
            ent=[i for i in o if i["kind"]=="entry"][0]
            self.assertEqual(ent["qty"],88,sid)  # 400//4.5, not 400//4.0=100
            self.assertEqual(ent["price_hint"],4.5,sid)
            rec=ent["enhance_exp"]["records"][-1]
            self.assertEqual((rec["control_qty"],rec["treatment_qty"]),(100,88),sid)
    def test_g4_reprice_and_cap_all(self):
        tickets={"aster_tensor_g4_cash_all_10":1000}
        for sid in B14G4:
            tk=tickets.get(sid,400)
            o=ev(sid,view([g4fire(atr=atr_for(sid))],{"ABC":bar(9.0)}))
            ent=[i for i in o if i["kind"]=="entry"][0]
            self.assertEqual(ent["qty"],tk//9,sid)
            self.assertEqual(ev(sid,view([g4fire(atr=atr_for(sid))],{"ABC":bar(10.5)})),[],sid)  # > G4 cap 10
            o=ev(sid,view([g4fire(atr=atr_for(sid))],{"ABC":bar(10.5)}),ctx=off_ctx(sid))
            ent=[i for i in o if i["kind"]=="entry"][0]
            self.assertEqual(ent["qty"],tk//8,sid)  # OFF: fire-price rule exactly
    def test_no_current_bar_preserves_legacy_path(self):
        for sid in ALL:
            f=c1fire(sid,atr=atr_for(sid)) if sid in B13 else (
                {"symbol":"AAA","signal":"buy-cyan","price":4.0,"ret60":40.0,"vol20":0.1,
                 "adv_usd":5000000,"atr_ratio":1.5,"date":"2026-10-23"} if sid in B14C1
                else g4fire(atr=atr_for(sid)))
            o=ev(sid,view([f]))
            self.assertTrue(any(i["kind"]=="entry" for i in o),sid)

if __name__=="__main__": unittest.main()
