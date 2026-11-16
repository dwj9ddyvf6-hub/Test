import os, sys, json, math, unittest, importlib, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)

IDS = {
 "aster_etf_drift1_m150": ("DRIFT1", 1.5, "R19_ETF_DRIFT1_M150"),
 "aster_etf_exsmh1_c098": ("EXSMH1", 0.98, "R19_ETF_EXSMH1_C098"),
 "aster_etf_exsmh1_m150": ("EXSMH1", 1.5, "R19_ETF_EXSMH1_M150"),
 "aster_etf_interval1_c098": ("INTERVAL1", 0.98, "R19_ETF_INTERVAL1_C098"),
 "aster_etf_interval1_m150": ("INTERVAL1", 1.5, "R19_ETF_INTERVAL1_M150"),
 "aster_etf_interval_core25_c098": ("INTERVAL_CORE25", 0.98, "R19_ETF_INTERVAL_CORE25_C098"),
 "aster_etf_interval_core25_m150": ("INTERVAL_CORE25", 1.5, "R19_ETF_INTERVAL_CORE25_M150"),
 "aster_etf_interval_drift1_c098": ("INTERVAL_DRIFT1", 0.98, "R19_ETF_INTERVAL_DRIFT1_C098"),
 "aster_etf_interval_drift1_m150": ("INTERVAL_DRIFT1", 1.5, "R19_ETF_INTERVAL_DRIFT1_M150"),
 "aster_etf_leader1_c098": ("LEADER1", 0.98, "R19_ETF_LEADER1_C098"),
}
UNIVERSE = ["QQQ","SPY","SMH","XLB","XLC","XLE","XLF","XLI","XLK","XLP","XLRE","XLU","XLV","XLY"]

def bars(closes, start="2025-01-02"):
    # 260 daily bars ending in Oct 2026; dates only need month of last bar
    out=[]
    for i,c in enumerate(closes):
        y = 2025 + (i//260); out.append({"t": f"2026-09-{(i%28)+1:02d}" if i>=232 else "2025-06-02","o":c,"h":c,"l":c,"c":c,"v":1000})
    return out

def series(base, growth):
    # 260 closes: flat then linear growth so 126-session log return = growth rank
    return [base*(1+growth*(i/259.0)) for i in range(260)]

def make_bars(winner="XLK", month="2026-10", smh_top=False):
    m={}
    for s in UNIVERSE:
        g = 0.05
        if s==winner: g=0.60
        if smh_top and s=="SMH": g=0.90
        m[f"{s}|1Day"]=bars(series(100.0,g))
        # fix last bar date to requested month
        m[f"{s}|1Day"][-1] = dict(m[f"{s}|1Day"][-1], t=f"{month}-15")
    return m

def view(barsmap, positions=None, cash=10000.0, secondary=None, now="2026-10-05T13:36:00+00:00", session="2026-10-05"):
    v={"now":now,"bars":barsmap,"positions":positions or [],
       "slice":{"capital_usd":10000.0,"cash_usd":cash},"extra":{}}
    if secondary is not None: v["bars_secondary"]=secondary
    return v

CTX={"session":"2026-10-05","now":"2026-10-05T13:36:00+00:00"}

def ev(sid, v, ctx=None):
    return importlib.import_module(f"adapters3.{sid}").evaluate(v, dict(ctx or CTX))

class T(unittest.TestCase):
    def test_leader_entry_c098_and_m150_qty_uncapped(self):
        b=make_bars("XLK")
        o=ev("aster_etf_leader1_c098", view(b))
        self.assertEqual(len(o),1); self.assertEqual(o[0]["symbol"],"XLK"); self.assertEqual(o[0]["kind"],"entry")
        self.assertEqual(o[0]["qty"], int(0.98*10000//o[0]["price_hint"]))
        b2=make_bars("XLK")
        o2=ev("aster_etf_interval1_m150", view(b2, secondary=b2)) if False else None
        # drift M150 sleeve is in this batch; leader M150 belongs to batch 10, use drift for leverage proof here
        o3=ev("aster_etf_drift1_m150", view(make_bars("XLK")))
        self.assertEqual(o3[0]["qty"], int(1.5*10000//o3[0]["price_hint"]))

    def test_exsmh_excludes_smh(self):
        b=make_bars("XLK", smh_top=True)
        o=ev("aster_etf_exsmh1_c098", view(b))
        self.assertEqual(o[0]["symbol"],"XLK")
        # control: leader picks SMH when it is top
        o2=ev("aster_etf_leader1_c098", view(b))
        self.assertEqual(o2[0]["symbol"],"SMH")

    def test_interval_requires_secondary_and_agreement(self):
        b=make_bars("XLK")
        self.assertEqual(ev("aster_etf_interval1_c098", view(b)), [])  # missing secondary -> refuse
        self.assertEqual(ev("aster_etf_interval1_c098", view(b, secondary={})), [])
        o=ev("aster_etf_interval1_c098", view(b, secondary=b))
        self.assertEqual(len(o),1); self.assertEqual(o[0]["symbol"],"XLK")
        # disagreeing secondary set (missing a symbol) -> refuse
        bad={k:v for k,v in b.items() if not k.startswith("SPY")}
        self.assertEqual(ev("aster_etf_interval1_c098", view(b, secondary=bad)), [])

    def test_interval_ambiguous_falls_back_qqq(self):
        # primary winner XLK barely, secondary winner SPY barely -> no robust leader, no incumbent -> QQQ
        b=make_bars("XLK"); s=make_bars("SPY")
        o=ev("aster_etf_interval1_c098", view(b, secondary=s))
        syms={i["symbol"] for i in o}; self.assertIn("QQQ", syms)

    def test_interval_core25_weights(self):
        b=make_bars("XLK")
        o=ev("aster_etf_interval_core25_c098", view(b, secondary=b))
        by={i["symbol"]:i["qty"] for i in o}
        self.assertEqual(set(by), {"XLK","QQQ"})
        px={s: b[f"{s}|1Day"][-1]["c"] for s in by}
        self.assertAlmostEqual(by["QQQ"]*px["QQQ"]/(0.98*10000), 0.75, delta=0.03)
        self.assertAlmostEqual(by["XLK"]*px["XLK"]/(0.98*10000), 0.25, delta=0.03)

    def test_drift_retains_unchanged_shares(self):
        b=make_bars("XLK")
        pos=[{"symbol":"XLK","qty":7,"avg_price":90.0,"signal_month":"2026-09"}]
        self.assertEqual(ev("aster_etf_drift1_m150", view(b, positions=pos, cash=2000.0)), [])
        self.assertEqual(ev("aster_etf_interval_drift1_c098", view(b, positions=pos, cash=2000.0, secondary=b)), [])
        # non-drift leader with same holding but wrong qty DOES rebalance in a new month
        o=ev("aster_etf_leader1_c098", view(b, positions=pos, cash=2000.0))
        self.assertTrue(o)

    def test_rotation_exit_sell_then_settle(self):
        # held XLK from last month, this month SPY wins -> only sell intent(s), no buys same eval
        b=make_bars("SPY", month="2026-10")
        pos=[{"symbol":"XLK","qty":10,"avg_price":100.0,"signal_month":"2026-09"}]
        o=ev("aster_etf_leader1_c098", view(b, positions=pos, cash=500.0))
        self.assertEqual(len(o),1); self.assertEqual(o[0]["kind"],"exit"); self.assertEqual(o[0]["symbol"],"XLK"); self.assertEqual(o[0]["qty"],10)

    def test_same_month_no_rebalance(self):
        b=make_bars("SPY", month="2026-10")
        pos=[{"symbol":"XLK","qty":10,"avg_price":100.0,"signal_month":"2026-10"}]
        self.assertEqual(ev("aster_etf_leader1_c098", view(b, positions=pos, cash=500.0)), [])

    def test_refusals_window_and_history(self):
        b=make_bars("XLK")
        v=view(b, now="2026-10-05T20:00:00+00:00")  # 16:00 ET, outside 09:35-09:40
        self.assertEqual(ev("aster_etf_leader1_c098", v), [])
        short={k: val[:100] for k,val in b.items()}
        self.assertEqual(ev("aster_etf_leader1_c098", view(short)), [])
        self.assertEqual(ev("aster_etf_leader1_c098", view({})), [])

    def test_m150_entry_drives(self):
        # ASTER-B9-2 census cure: the three M150 variants previously had
        # zero ev() drives (IDS/config assertion only). Each gets a real
        # per-sleeve entry drive at its own 1.5 gross target.
        b=make_bars("XLK", smh_top=True)  # SMH top but EXSMH excludes it
        o=ev("aster_etf_exsmh1_m150", view(b))
        self.assertEqual(len(o),1); self.assertEqual(o[0]["symbol"],"XLK"); self.assertEqual(o[0]["kind"],"entry")
        self.assertEqual(o[0]["qty"], int(1.5*10000//o[0]["price_hint"]))
        b=make_bars("XLK")
        o=ev("aster_etf_interval_core25_m150", view(b, secondary=b))
        by={i["symbol"]:i["qty"] for i in o}
        self.assertEqual(set(by), {"XLK","QQQ"}); self.assertTrue(all(i["kind"]=="entry" for i in o))
        px={s: b[f"{s}|1Day"][-1]["c"] for s in by}
        self.assertAlmostEqual(by["QQQ"]*px["QQQ"]/(1.5*10000), 0.75, delta=0.03)
        self.assertAlmostEqual(by["XLK"]*px["XLK"]/(1.5*10000), 0.25, delta=0.03)
        b=make_bars("XLK")
        o=ev("aster_etf_interval_drift1_m150", view(b, secondary=b))
        self.assertEqual(len(o),1); self.assertEqual(o[0]["symbol"],"XLK"); self.assertEqual(o[0]["kind"],"entry")
        self.assertEqual(o[0]["qty"], int(1.5*10000//o[0]["price_hint"]))

    def test_rotation_exit_all_batch9_ids(self):
        # ASTER-B9-2 census cure: rotation-exit proof parameterized over
        # ALL 10 batch-9 ids (previously driven only for leader1_c098).
        # Held XLK from last month; SPY wins this month -> sell-then-
        # settle: exactly one exit intent (XLK, full qty), no buys.
        for sid,(pol,gross,sm) in IDS.items():
            with self.subTest(sid=sid):
                b=make_bars("SPY", month="2026-10")
                pos=[{"symbol":"XLK","qty":10,"avg_price":100.0,"signal_month":"2026-09"}]
                kw={"secondary": b} if pol.startswith("INTERVAL") else {}
                o=ev(sid, view(b, positions=pos, cash=500.0, **kw))
                self.assertEqual(len(o),1, o); self.assertEqual(o[0]["kind"],"exit")
                self.assertEqual(o[0]["symbol"],"XLK"); self.assertEqual(o[0]["qty"],10)

    def test_config_and_inputs(self):
        cfg=json.load(open(os.path.join(ROOT,"config","sleeves.json")))
        for sid,(pol,gross,sm) in IDS.items():
            rows=[s for s in cfg["sleeves"] if s["id"]==sid]; self.assertEqual(len(rows),1,sid)
            r=rows[0]; self.assertEqual(r["slice"]["capital_usd"],10000.0,sid)
            self.assertEqual(r["params"]["policy"],pol,sid); self.assertEqual(r["params"]["gross_target"],gross,sid)
            self.assertEqual(r["params"]["source_id"],sm,sid)
            m=importlib.import_module(f"adapters3.{sid}")
            self.assertEqual(tuple(r["inputs"]), m.INPUTS, sid)
            if pol.startswith("INTERVAL"): self.assertIn("bars_secondary", m.INPUTS, sid)

    def test_e2e_roundtrip_to_flat_via_fake_broker(self):
        from desk3.broker import FakeBroker
        from desk3.dispatcher import Dispatcher
        sid="aster_etf_leader1_c098"
        b=make_bars("XLK")
        px={s: b[f"{s}|1Day"][-1]["c"] for s in UNIVERSE}
        with tempfile.TemporaryDirectory() as td:
            disp=Dispatcher(td, FakeBroker(prices=px), slices={sid:{"capital_usd":10000.0,"cash_usd":10000.0}},
                            price_lookup=lambda s: px.get(s))
            def cur_view(barsmap, month_session, now):
                sl=disp.slices[sid]
                pos=[dict(p, signal_month="2026-09") for p in sl["positions"].values()]
                return view(barsmap, positions=pos, cash=sl["cash_usd"], now=now, session=month_session)
            o=ev(sid, cur_view(b,"2026-10-05","2026-10-05T13:36:00+00:00"))
            self.assertEqual(len(o),1)
            r=disp.process_intent(o[0], sid); self.assertEqual(r["status"],"filled", r)
            self.assertIn("XLK", disp.slices[sid]["positions"])
            b2=make_bars("SPY", month="2026-11")
            px.update({s: b2[f"{s}|1Day"][-1]["c"] for s in UNIVERSE}); disp.broker.prices=px
            o2=ev(sid, cur_view(b2,"2026-11-02","2026-11-02T14:36:00+00:00"))
            self.assertTrue(o2 and all(i["kind"]=="exit" for i in o2), o2)
            for i in o2: self.assertEqual(disp.process_intent(i, sid)["status"],"filled")
            self.assertEqual(disp.slices[sid]["positions"], {})  # flat

if __name__=="__main__": unittest.main()
