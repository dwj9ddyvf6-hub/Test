"""Signals: ONE pure function per sleeve, resolved from config/sleeves.json (source.producer). A signal function takes the pass inputs
(already-loaded producer files; no I/O, no clock) and returns normalized fires:
  {key, sym, lane, fire_bar, D, close, plan{stop_pct, max_bars, rest, scheme}, strategy, shadow, source}
Producers (research plane, unchanged, read-only): tracker (canonical Tensor v698), lab_live books, sleeve_feed composer (alt-data tags,
Q07 cells), cl_live, sleeve_midna. Lab-book routing is ported natively here (sleeve_feed 1.0.4 Feed.lab) and parity-checked."""
def plan(n, scheme=None, stop=99.0, rest="time"):
    return dict(scheme=scheme or f"no stop / time exit {n}", stop_pct=stop, max_bars=int(n), rest=rest)
def _norm_feed(f, shadow=False, source=""):
    pl = next(iter((f.get("cal_plans") or {}).values()), None) or {}
    return dict(key=f["key"], sym=f["sym"], lane=f["lane"], fire_bar=f.get("fire_bar"), D=f.get("D") or str(f.get("fire_bar"))[:10], close=f.get("close"),
                plan=dict(scheme=pl.get("scheme"), stop_pct=pl.get("stop_pct", 99.0), max_bars=pl.get("max_bars"), rest=pl.get("rest", "time"),
                          first_target_pct=pl.get("first_target_pct")), strategy=f.get("strategy"), shadow=shadow, source=source, size_class=f.get("size_class"))
def feed_lane(lane, file_key, shadow=False):
    """fires of `lane` from a composed producer file (sleeve_fires_v1 / desk_extra_fires_v1 / midna_fires_v1)."""
    def fn(I):
        o = I.get(file_key)
        if o is None: return []
        return [_norm_feed(f, shadow, file_key) for f in o.get("fires", []) if f.get("lane") == lane and f.get("tradeable", True)]
    fn.__name__ = f"feed_lane[{file_key}:{lane}]"; return fn
def tracker_lane(kind):
    """Main 1h/1d/1w: tracker tradeable fires (canonical Tensor v698 engine, yahoo:canonical bars only)."""
    def fn(I):
        o = I.get("fires_main")
        if o is None: return []
        out = []; seen = set()
        for f in list(o.get("fires", [])) + list(I.get("fires_main_log") or []):   # latest run + the tracker fire log (fires_log_v3.csv) inside the 5-session window
            if f.get("key") in seen or str(f.get("time_et", ""))[:10] < I.get("oldest_fire_day", "0000"): continue
            seen.add(f.get("key"))
            if f.get("lane") != kind or str(f.get("tradeable")).lower() != "true" or not str(f.get("bar_source", "")).startswith("yahoo"): continue
            out.append(dict(key=f["key"], sym=f["symbol"], lane=kind, fire_bar=f["time_et"], D=str(f["time_et"])[:10], close=float(f["entry_ref"]) if f.get("entry_ref") not in (None, "") else None,
                            plan=plan(float(f.get("max_hold_bars") or 0), (f.get("calibrated_plans") or "")[:80], float(f.get("stop_pct") or 99.0)), strategy=f.get("active_units"), shadow=False, source="tracker"))
        return out
    fn.__name__ = f"tracker_lane[{kind}]"; return fn
def lab_route(lane):
    """native port of sleeve_feed 1.0.4 Feed.lab() for s_1dg / s_1wlab / s_1wsw / s_rules_1d / s_rules_1w."""
    def fn(I):
        books, oldest = I.get("lab_books") or {}, I.get("oldest_fire_day", "0000"); out = {}
        for name, J in sorted(books.items()):
            job = f"{J['lane']}-{J['signal']}-{J['universe']}"; weekly = J["lane"] == "1W"; FH = {x["id"]: x.get("horizon") for x in J.get("frozen_rules") or []}
            for x in J["fires"]:
                if x["day"] < oldest: continue
                books_ = ([f"lab {job} rule search"] if x.get("search") else []) + ([f"lab {job} boosted trees"] if x.get("gbm") else [])
                fb = x["day"] if weekly else f"{x['day']} 09:30:00-04:00"
                def add(k, ln, n, strat, why):
                    if ln != lane: return
                    if k in out: out[k]["why"] = sorted(set(out[k]["why"]) | set(why)); return
                    out[k] = dict(key=k, sym=x["sym"], lane=ln, fire_bar=fb, D=x["day"], close=None, plan=plan(n), strategy=strat, shadow=False, source="lab_books", why=why)
                if books_:
                    if job == "1D-green-full" and x.get("gbm"): add(f"{x['sym']}:s_1dg:x:{x['day']}", "s_1dg", 21, "Lab 1D Green trees (test)", books_)
                    elif job in ("1W-cyan-full", "1W-cyan-covered"): add(f"{x['sym']}:s_1wlab:x:{x['day']}", "s_1wlab", 126, "Lab 1W Cyan books (test)", books_)
                    elif job == "1W-swing-covered" and x.get("search"): add(f"{x['sym']}:s_1wsw:x:{x['day']}", "s_1wsw", 126, "Lab 1W Swing covered (test)", [b for b in books_ if "search" in b])
                for rid in x.get("frozen") or []:
                    H = int(FH.get(rid) or (126 if weekly else 21)); ln = "s_rules_1w" if weekly else "s_rules_1d"
                    add(f"{x['sym']}:{ln}:x:{x['day']}:H{H}", ln, H + 1, "Lab rule (test)", [f"lab rule {rid}"])
        return list(out.values())
    fn.__name__ = f"lab_route[{lane}]"; return fn
LAB_LANES = ("s_1dg", "s_1wlab", "s_1wsw", "s_rules_1d", "s_rules_1w")
def resolve(s):
    """sleeve config row -> its signal function (or None for dead / exit-only rows)."""
    lid, acct = s["id"], s["account"]
    if s["state"] == "dead": return None
    if acct == "MAIN":
        if lid in ("1h", "1d", "1w"): return tracker_lane(lid)
        return feed_lane(lid, "fires_main_extra")
    if lid in LAB_LANES: return lab_route(lid)
    if lid.startswith("s_mn_"): return feed_lane(lid, "fires_midna", shadow=s["state"] == "shadow")
    return feed_lane(lid, "fires_sleeve", shadow=s["state"] == "shadow")
def valid_fire(f):
    need = ("key", "sym", "lane", "fire_bar", "D", "plan", "shadow")
    return all(k in f and f[k] is not None for k in need) and isinstance(f["plan"], dict) and f["plan"].get("max_bars") is not None
