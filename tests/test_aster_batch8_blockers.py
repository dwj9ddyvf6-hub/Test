"""Aster batch 8 blockers (ASTER-B8): 7x negative_funding_squeeze ENJUSDT
(fixed96 vol; lost_breakout full/vol; normalization_failure full/vol;
normalization full/vol) + 3x etf (CORE25 98/150, DRIFT1 98).
Oracle = archive r19_crypto.py/r19_etf.py + crypto_rules/etf_rules +
TSV education fields (ASTER-BUILD-MAP batch 8):
NFS entry = completed 4h close > highest high of prior 20 bars AND an
actually available funding observation < 0. Exits: fixed96 deadline;
lost_breakout = close below stored breakout level; normalization =
funding >= 0; normalization_failure = funding >= 0 AND close below prior
3 bars' lowest low, plus 4h execution delay; installed max deadline 96h
for every structural policy, firing even when inputs are missing.
Sizing: fullcash = slice cash less 10bp fee; volume1pct = min(fullcash,
1% of preceding 4h volume). ETF: 126-session leader (ties alphabetical),
CORE25 = 75% QQQ + 25% leader, DRIFT1 = leader only with unchanged
shares when the incumbent leader is still held; monthly, 09:35-09:40 ET,
whole shares, sells before buys, no price stop/target.
Fail-first: adapters absent pre-build => errors."""
import importlib, json, os, sys, unittest
from datetime import datetime, timedelta, timezone
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,ROOT)
CRYPTO=["aster_enj_nfs_fixed96_vol","aster_enj_nfs_lost_full","aster_enj_nfs_lost_vol",
 "aster_enj_nfs_normfail_full","aster_enj_nfs_normfail_vol","aster_enj_nfs_norm_full","aster_enj_nfs_norm_vol"]
ETF=["aster_etf_core25_c098","aster_etf_core25_m150","aster_etf_drift1_c098"]
IDS=CRYPTO+ETF
NOW=datetime(2026,10,23,16,0,tzinfo=timezone.utc)
def bars(n=25, breakout=True, vol=100000.0, close=1.0, hi=1.05):
    out=[]
    for i in range(n):
        t=NOW-timedelta(hours=4*(n-i))
        c=1.10 if (breakout and i==n-1) else close
        out.append({"t":t.isoformat(),"o":close,"h":hi,"l":0.95,"c":c,"v":vol})
    return out
def drive(sid, brs=None, funding=-0.01, positions=None, cash=10000.0):
    mod=importlib.import_module(f"adapters3.{sid}")
    view={"now":NOW.isoformat(),"bars":{"ENJUSDT|4Hour":brs if brs is not None else bars()},
          "funding":{"ENJUSDT":funding} if funding is not None else {},
          "positions":positions or [],"slice":{"capital_usd":10000.0,"cash_usd":cash},
          "params":{},"extra":{},"session_fills":[]}
    return mod.evaluate(view,{"sleeve_id":sid,"session":"2026-10-23"})
def pos(hours=20, qty=5000.0, **kw):
    d={"symbol":"ENJUSDT","qty":qty,"avg_price":1.0,"opened_at":(NOW-timedelta(hours=hours)).isoformat(),"breakout_level":1.05}
    d.update(kw); return [d]
class TestCryptoEntries(unittest.TestCase):
    def test_entry_fullcash(self):
        o=drive("aster_enj_nfs_lost_full"); self.assertEqual(len(o),1); self.assertEqual(o[0]["kind"],"entry")
        self.assertAlmostEqual(o[0]["qty"],10000*0.999/1.10,places=4)
    def test_entry_volume_cap(self):
        for sid in ("aster_enj_nfs_fixed96_vol","aster_enj_nfs_norm_vol"):
            o=drive(sid); self.assertEqual(len(o),1,sid); self.assertAlmostEqual(o[0]["qty"],1000.0,4,sid)
    def test_all_seven_enter(self):
        for sid in CRYPTO: self.assertEqual(len(drive(sid)),1,sid)
class TestCryptoRefusals(unittest.TestCase):
    def test_no_breakout(self): self.assertEqual(drive(CRYPTO[0],brs=bars(breakout=False)),[])
    def test_positive_funding(self): self.assertEqual(drive(CRYPTO[0],funding=0.001),[])
    def test_zero_funding_not_negative(self): self.assertEqual(drive(CRYPTO[0],funding=0.0),[])
    def test_missing_funding(self): self.assertEqual(drive(CRYPTO[0],funding=None),[])
    def test_short_history(self): self.assertEqual(drive(CRYPTO[0],brs=bars(n=20)),[])
    def test_occupied(self): self.assertEqual(drive(CRYPTO[0],positions=pos(hours=1)),[])
class TestCryptoExits(unittest.TestCase):
    def test_fixed96_deadline(self):
        self.assertEqual(len(drive("aster_enj_nfs_fixed96_vol",positions=pos(hours=97))),1)
        self.assertEqual(drive("aster_enj_nfs_fixed96_vol",positions=pos(hours=20)),[])
    def test_lost_breakout_exit(self):
        b=bars(breakout=False); b[-1]["c"]=1.02
        for sid in ("aster_enj_nfs_lost_full","aster_enj_nfs_lost_vol"):
            self.assertEqual(len(drive(sid,brs=b,positions=pos(hours=2))),1,sid)
        b[-1]["c"]=1.06  # still above breakout level: hold
        self.assertEqual(drive("aster_enj_nfs_lost_full",brs=b,positions=pos(hours=2)),[])
    def test_normalization_exit(self):
        for sid in ("aster_enj_nfs_norm_full","aster_enj_nfs_norm_vol"):
            self.assertEqual(len(drive(sid,funding=0.0,positions=pos(hours=2))),1,sid)
            self.assertEqual(drive(sid,funding=-0.01,positions=pos(hours=2)),[],sid)
    def test_norm_failure_exit_after_delay(self):
        b=bars(breakout=False); b[-1]["c"]=0.90; b[-1]["l"]=0.90; b[-1]["t"]=(NOW-timedelta(hours=12)).isoformat()
        for sid in ("aster_enj_nfs_normfail_full","aster_enj_nfs_normfail_vol"):
            self.assertEqual(len(drive(sid,brs=b,funding=0.002,positions=pos(hours=20))),1,sid)
    def test_norm_failure_no_exit_before_delay(self):
        b=bars(breakout=False); b[-1]["c"]=0.90
        self.assertEqual(drive("aster_enj_nfs_normfail_full",brs=b,funding=0.002,positions=pos(hours=2)),[])
    def test_norm_failure_needs_both_legs(self):
        b=bars(breakout=False); b[-1]["c"]=0.90; b[-1]["t"]=(NOW-timedelta(hours=12)).isoformat()
        self.assertEqual(drive("aster_enj_nfs_normfail_full",brs=b,funding=-0.002,positions=pos(hours=20)),[])
    def test_structural_deadline_96(self):
        for sid in CRYPTO[1:]:
            self.assertEqual(len(drive(sid,positions=pos(hours=97))),1,sid)
    def test_deadline_survives_missing_inputs(self):
        o=drive("aster_enj_nfs_lost_full",brs=[],funding=None,positions=pos(hours=100)); self.assertEqual(len(o),1)
# ---- ETF ----
def fb(px,n=130,start=None):
    return [{"t":f"2026-01-{(i%28)+1:02d}","o":px,"h":px,"l":px,"c":(start if (start is not None and i==n-127) else px),"v":1000} for i in range(n)]
def basket(leader="XLK"):
    syms=["QQQ","SPY","SMH","XLB","XLC","XLE","XLF","XLI","XLK","XLP","XLRE","XLU","XLV","XLY"]
    m={s:fb(100.0) for s in syms}
    if leader: m[leader]=fb(120.0,start=100.0)
    return m
CTX={"session":"2026-10-01","now":"2026-10-01T09:36:00","slice":{"capital_usd":10000.0}}
def ev(sid,v,ctx=None): return importlib.import_module(f"adapters3.{sid}").evaluate(v,dict(ctx or CTX))
def V(barsmap,positions=None,now="2026-10-01T09:36:00",extra=None):
    return {"now":now,"bars":barsmap,"positions":positions or [],"quotes":{},"extra":extra or {}}
class TestEtf(unittest.TestCase):
    def test_core25_entry_98(self):
        o=ev("aster_etf_core25_c098",V(basket()))
        got={x["symbol"]:x["qty"] for x in o}; self.assertEqual(got,{"QQQ":73,"XLK":20})  # .75*.98*10000/100=73.5->73 ; .25*.98*10000/120=20.4->20
    def test_core25_entry_150(self):
        o=ev("aster_etf_core25_m150",V(basket()))
        got={x["symbol"]:x["qty"] for x in o}; self.assertEqual(got,{"QQQ":112,"XLK":31})
    def test_core25_qqq_leads_combines(self):
        o=ev("aster_etf_core25_c098",V(basket(leader="QQQ")))
        self.assertEqual(len(o),1); self.assertEqual(o[0]["symbol"],"QQQ"); self.assertEqual(o[0]["qty"],81)  # .98*10000/120 (leader price 120)
    def test_drift1_entry(self):
        o=ev("aster_etf_drift1_c098",V(basket())); self.assertEqual(len(o),1)
        self.assertEqual(o[0]["symbol"],"XLK"); self.assertEqual(o[0]["qty"],81)  # .98*10000/120=81.6->81
    def test_drift1_retains_unchanged_shares(self):
        p=[{"symbol":"XLK","qty":50,"avg_price":110.0,"entry_date":"2026-09-02"}]
        self.assertEqual(ev("aster_etf_drift1_c098",V(basket(),positions=p)),[])
    def test_drift1_rotates_when_leader_changes(self):
        p=[{"symbol":"XLK","qty":81,"avg_price":120.0,"entry_date":"2026-09-02"}]
        o=ev("aster_etf_drift1_c098",V(basket(leader="XLE"),positions=p))
        sells=[x for x in o if x["side"]=="sell"]; self.assertEqual(sells[0]["symbol"],"XLK"); self.assertEqual(sells[0]["qty"],81)
        self.assertLess(o.index(sells[0]),min(o.index(x) for x in o if x["side"]=="buy"))
    def test_refusals_window_history_same_month(self):
        self.assertEqual(ev("aster_etf_core25_c098",V(basket(),now="2026-10-01T10:00:00")),[])
        self.assertEqual(ev("aster_etf_core25_c098",V({"QQQ":fb(100.0,n=10)})),[])
        p=[{"symbol":"QQQ","qty":10,"avg_price":100.0,"entry_date":"2026-10-01"}]
        self.assertEqual(ev("aster_etf_core25_c098",V(basket(),positions=p)),[])
class TestRegistryAndE2E(unittest.TestCase):
    def test_config_rows_and_inputs(self):
        from desk3.aster_batch8 import config_rows
        rows={r["id"]:r for r in config_rows()}; self.assertEqual(sorted(rows),sorted(IDS))
        cfg=json.load(open(os.path.join(ROOT,"config","sleeves.json"))); have={r["id"]:r for r in cfg["sleeves"]}
        for sid in IDS:
            self.assertIn(sid,have); self.assertEqual(have[sid]["inputs"],rows[sid]["inputs"])
            self.assertEqual(have[sid]["slice"]["capital_usd"],10000.0)
            self.assertEqual(tuple(importlib.import_module(f"adapters3.{sid}").INPUTS),tuple(rows[sid]["inputs"]))
    def test_crypto_unfed_declared(self):
        from desk3.aster_batch8 import PRODUCERS
        self.assertNotIn("funding",[o for p in PRODUCERS for o in p["outputs"]])  # no funding producer in v3 yet => UNFED by registry, never fake-fed
    def test_e2e_crypto_roundtrip_to_flat(self):
        from desk3.broker import FakeBroker
        b=FakeBroker(prices={"ENJUSDT":10.0})
        brs=bars(); 
        for r in brs: r["h"]=9.5; r["o"]=9.0; r["l"]=8.5; r["c"]=9.0
        brs[-1]["c"]=10.0
        o=drive("aster_enj_nfs_fixed96_vol",brs=brs)
        self.assertEqual(len(o),1); self.assertEqual(o[0]["qty"],999.0)  # min(1%vol=1000, fullcash 9990/10=999)
        for i in o: b.get_order_by_client_id(b.submit_order(f"b8-{i['intent_id']}",i["symbol"],i["side"],i["qty"],"market")["client_order_id"])
        self.assertEqual(b.get_positions(),{"ENJUSDT":999.0})
        ex=drive("aster_enj_nfs_fixed96_vol",positions=pos(hours=100,qty=999.0))
        for i in ex: b.get_order_by_client_id(b.submit_order(f"b8x-{i['intent_id']}",i["symbol"],i["side"],i["qty"],"market")["client_order_id"])
        self.assertEqual(b.get_positions(),{})
    def test_e2e_etf_entry_and_rotation_exit(self):
        from desk3.broker import FakeBroker
        b=FakeBroker(prices={"QQQ":100.0,"XLK":120.0,"XLE":100.0})
        o=ev("aster_etf_core25_c098",V(basket()))
        for i in o: b.get_order_by_client_id(b.submit_order(f"b8e-{i['intent_id']}",i["symbol"],i["side"],i["qty"],"market")["client_order_id"])
        self.assertEqual(b.get_positions(),{"QQQ":73.0,"XLK":20.0})
        p=[{"symbol":"QQQ","qty":73,"avg_price":100.0,"entry_date":"2026-09-02"},{"symbol":"XLK","qty":20,"avg_price":120.0,"entry_date":"2026-09-02"}]
        o2=ev("aster_etf_core25_c098",V(basket(leader="XLE"),positions=p))
        for i in o2: b.get_order_by_client_id(b.submit_order(f"b8r-{i['intent_id']}",i["symbol"],i["side"],i["qty"],"market")["client_order_id"])
        self.assertNotIn("XLK",b.get_positions())
if __name__=="__main__": unittest.main()
