import os,sys,unittest,json
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,ROOT)
def bars(sym,px,n=30,drift=0.0):
    return [{"t":f"2026-10-{1+i//5:02d}-{(i%28)+1:02d}","o":px,"h":px,"l":px,"c":px+drift*i,"v":1000} for i in range(n)]
def daily(sym,closes):
    return [{"t":f"2026-09-{i+1:02d}" if i<30 else f"2026-10-{i-29:02d}","o":c,"h":c,"l":c,"c":c,"v":1000} for i,c in enumerate(closes)]
CTX={"session":"2026-10-24","now":"2026-10-24T15:00:00"}
def fire(sid,sym,fam,tf,price,date="2026-10-23"):
    return {"sleeve_id":sid,"symbol":sym,"family":fam,"timeframe":tf,"date":date,"price":price}
def view(sid,fires,extra=None,barsmap=None,positions=None):
    v={"now":"2026-10-24T15:00:00","midna_fires":fires,"bars":barsmap or {},"positions":positions or [],"extra":extra or {}}
    return v
class T(unittest.TestCase):
    def ev(self,sid,v):
        import importlib; return importlib.import_module(f"adapters3.{sid}").evaluate(v,dict(CTX))
    # entries
    def test_breadth_entry(self):
        v=view("s_mn_w_cyan_breadth",[fire("s_mn_w_cyan_breadth","AAA","cyan","1W",10.0)],extra={"breadth_pct":0.6},barsmap={"AAA":daily("AAA",[10]*30)})
        o=self.ev("s_mn_w_cyan_breadth",v); self.assertEqual(len(o),1); self.assertEqual(o[0]["qty"],100); self.assertEqual(o[0]["kind"],"entry")
    def test_breadth_refusal_low_and_missing(self):
        for ex in ({"breadth_pct":0.4},{}):
            v=view("s_mn_w_cyan_breadth",[fire("s_mn_w_cyan_breadth","AAA","cyan","1W",10.0)],extra=ex,barsmap={"AAA":daily("AAA",[10]*30)})
            self.assertEqual(self.ev("s_mn_w_cyan_breadth",v),[])
    def test_vix_entry_and_refusals(self):
        v=view("s_mn_w_cyan_vix",[fire("s_mn_w_cyan_vix","BBB","cyan","1W",20.0)],extra={"vix_close":18},barsmap={"BBB":daily("BBB",[20]*30)})
        self.assertEqual(len(self.ev("s_mn_w_cyan_vix",v)),1)
        for vx in (10,30):
            v["extra"]={"vix_close":vx}; self.assertEqual(self.ev("s_mn_w_cyan_vix",v),[])
    def test_green_band_entry_and_band_refusal(self):
        v=view("s_mn_d_green_band",[fire("s_mn_d_green_band","CCC","green","1D",15.0)],barsmap={"CCC":daily("CCC",[15]*30)})
        o=self.ev("s_mn_d_green_band",v); self.assertEqual(o[0]["qty"],66)
        v=view("s_mn_d_green_band",[fire("s_mn_d_green_band","CCC","green","1D",25.0)],barsmap={"CCC":daily("CCC",[25]*30)})
        self.assertEqual(self.ev("s_mn_d_green_band",v),[])
    def test_green_smh_entry_and_calm_refusal(self):
        smh=daily("SMH",[100]*25)
        v=view("s_mn_w_green_smh",[fire("s_mn_w_green_smh","DDD","green","1W",10.0)],barsmap={"DDD":daily("DDD",[10]*30),"SMH":smh})
        self.assertEqual(len(self.ev("s_mn_w_green_smh",v)),1)
        smh2=daily("SMH",[100]*24+[120]); v["bars"]["SMH"]=smh2; self.assertEqual(self.ev("s_mn_w_green_smh",v),[])
    def test_hourly1w_entry(self):
        v=view("s_mn_hourly_1w",[fire("s_mn_hourly_1w","EEE","cyan","1W",50.0)],barsmap={"EEE":daily("EEE",[50]*30)})
        o=self.ev("s_mn_hourly_1w",v); self.assertEqual(o[0]["qty"],20)
    # exits
    def test_time_exits(self):
        cases=[("s_mn_w_cyan_breadth",126),("s_mn_w_cyan_vix",252),("s_mn_d_green_band",21),("s_mn_w_green_smh",126),("s_mn_hourly_1w",260)]
        for sid,hold in cases:
            pos=[{"symbol":"AAA","qty":10,"avg_price":10.0,"sessions_held":hold}]
            v=view(sid,[],barsmap={"AAA":daily("AAA",[10]*30)},positions=pos)
            o=self.ev(sid,v); self.assertEqual(len(o),1,sid); self.assertEqual(o[0]["kind"],"exit")
            pos[0]["sessions_held"]=hold-1; v["positions"]=pos
            self.assertEqual(self.ev(sid,v),[],sid)
    def test_hourly_stop_exit_and_no_stop_others(self):
        pos=[{"symbol":"EEE","qty":10,"avg_price":100.0,"sessions_held":1}]
        v=view("s_mn_hourly_1w",[],barsmap={"EEE":daily("EEE",[80])},positions=pos)
        o=self.ev("s_mn_hourly_1w",v); self.assertIn("stop_15pct",o[0]["reason"])
        v2=view("s_mn_w_cyan_breadth",[],barsmap={"EEE":daily("EEE",[80])},positions=pos)
        self.assertEqual(self.ev("s_mn_w_cyan_breadth",v2),[])
    def test_refusals_no_fire_stale_wrong_family_max1(self):
        v=view("s_mn_d_green_band",[],barsmap={"CCC":daily("CCC",[15]*30)}); self.assertEqual(self.ev("s_mn_d_green_band",v),[])
        v=view("s_mn_d_green_band",[fire("s_mn_d_green_band","CCC","green","1D",15.0,date="2026-09-01")],barsmap={"CCC":daily("CCC",[15]*30)}); self.assertEqual(self.ev("s_mn_d_green_band",v),[])
        v=view("s_mn_d_green_band",[fire("s_mn_d_green_band","CCC","cyan","1D",15.0)],barsmap={"CCC":daily("CCC",[15]*30)}); self.assertEqual(self.ev("s_mn_d_green_band",v),[])
    def test_config_and_inputs(self):
        cfg=json.load(open(os.path.join(ROOT,"config","sleeves.json")))
        # CURE-6-RECONCILIATION-20261114 (parent board decision):
        # the four s_mn fire consumers are bundle consumers — their
        # engine desk3/lazarus_midna declares INPUTS=(tensor,bars,
        # positions) — so config declares tensor for all five rows,
        # in sync with the adapters. Lane A's same-day redeclaration
        # to midna_fires (UNPARK-REGISTRY) was superseded on that
        # engine evidence; the hourly midna_signals product belongs
        # to s_mn_hourly / s_mn_nostop, not these rows.
        _exp={"s_mn_w_cyan_breadth":["tensor","bars","positions"],"s_mn_w_cyan_vix":["tensor","bars","positions"],"s_mn_d_green_band":["tensor","bars","positions"],"s_mn_w_green_smh":["tensor","bars","positions"],"s_mn_hourly_1w":["tensor","bars","positions"]}
        for sid in ["s_mn_w_cyan_breadth","s_mn_w_cyan_vix","s_mn_d_green_band","s_mn_w_green_smh","s_mn_hourly_1w"]:
            rows=[s for s in cfg["sleeves"] if s["id"]==sid]; self.assertEqual(len(rows),1,sid)
            self.assertEqual(rows[0]["slice"]["capital_usd"],1000.0); self.assertEqual(rows[0]["inputs"],_exp[sid])
            import importlib; m=importlib.import_module(f"adapters3.{sid}")
            self.assertEqual(tuple(rows[0]["inputs"]),m.INPUTS)
    def test_tensor_bundle_substitution_channel(self):
        v={"now":"2026-10-24T15:00:00","tensor":{"fires":[fire("s_mn_d_green_band","CCC","green","1D",15.0)]},"bars":{"CCC":daily("CCC",[15]*30)},"positions":[],"extra":{}}
        self.assertEqual(len(self.ev("s_mn_d_green_band",v)),1)
if __name__=="__main__": unittest.main()
