#!/usr/bin/env python3
"""C15 producer (R2, 2026-11-02): store each screen page's current row set
so the NEXT session can compute NEW badges honestly. Writes
site/rowsets.json {slug: {session, rows:[labels]}}. A row label is the
first identifying field of an object in any array in the page's own
data.json. Re-running in the same session overwrites with the same set;
badges only appear when a later session's rendered rows differ from the
stored set of an earlier session. Never fabricates a prior set: the
first stored set is the baseline and yields no badges for its session."""
import json, sys
from pathlib import Path
SITE = Path(__file__).resolve().parent
IDKEYS = ["symbol","name","id","title","sector","holder","ticker","label"]
def labels(data):
    out=set()
    def walk(v,depth):
        if depth>3: return
        if isinstance(v,list):
            for r in v:
                if isinstance(r,dict):
                    for k in IDKEYS:
                        if r.get(k) is not None and not isinstance(r[k],(dict,list)):
                            out.add(str(r[k])[:60]); break
                walk(r,depth+1)
        elif isinstance(v,dict):
            for x in v.values(): walk(x,depth+1)
    walk(data,0)
    return sorted(out)[:400]
def main():
    store={}
    for d in sorted(SITE.iterdir()):
        f=d/"data.json"
        if not d.is_dir() or not f.exists(): continue
        try: data=json.loads(f.read_text())
        except Exception: continue
        sess=None
        for k in ("session","session_date","as_of","date"):
            if isinstance(data.get(k),str): sess=data[k][:10]; break
        if not sess and isinstance(data.get("state"),dict): sess=str(data["state"].get("date") or "")[:10] or None
        rows=labels(data)
        if rows: store[d.name]={"session":sess,"rows":rows}
    (SITE/"rowsets.json").write_text(json.dumps(store,indent=1,sort_keys=True))
    print(f"rowsets: {len(store)} pages stored")
    return 0
if __name__=="__main__": sys.exit(main())
