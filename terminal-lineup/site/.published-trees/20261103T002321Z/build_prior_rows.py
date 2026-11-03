#!/usr/bin/env python3
"""C15 producer (R2 2026-11-02; rotation cured in R2-CURE 2026-11-02):
store each screen page's row sets so NEW badges can be computed
honestly. Writes site/rowsets.json:
  {slug: {baseline_session, baseline_rows, latest_session, latest_rows}}

R2-CURE (row 4): the R2 producer overwrote the store with the current
session's set on every lane run, so at render time the stored session
tended to equal the page's session and the diff window raced the lane.
The store now ROTATES: baseline_* is the prior session's set and only
advances when a genuinely newer session lands, at which point the
previous latest_* set becomes the baseline. Re-running inside one
session updates latest_rows only; the baseline never moves. The
client (grok.js newBadgesR2) diffs rendered rows against baseline_*
only when baseline_session is earlier than the page's own session.
Legacy entries ({session, rows}) migrate in place: that set becomes
both the baseline and the latest set for its session. Nothing is ever
fabricated: the first stored set is its own session's baseline and
yields no badges for that session."""
import json, sys
from pathlib import Path
SITE = Path(__file__).resolve().parent
STORE = SITE / "rowsets.json"
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
def session_of(data):
    for k in ("session","session_date","as_of","date"):
        if isinstance(data.get(k),str): return data[k][:10]
    if isinstance(data.get("state"),dict):
        return str(data["state"].get("date") or "")[:10] or None
    return None
def rotate(old, sess, rows):
    """One page's store entry after seeing session `sess` with `rows`."""
    if not old:
        return {"baseline_session": sess, "baseline_rows": rows,
                "latest_session": sess, "latest_rows": rows,
                "session": sess, "rows": rows}
    base_s = old.get("baseline_session") or old.get("session")
    base_r = old.get("baseline_rows") or old.get("rows") or []
    late_s = old.get("latest_session") or old.get("session")
    late_r = old.get("latest_rows") or old.get("rows") or []
    if sess and late_s and sess > late_s:
        # A newer session landed: the previous latest set is now the
        # honest prior-session baseline.
        base_s, base_r = late_s, late_r
        late_s, late_r = sess, rows
    elif sess and late_s and sess == late_s:
        late_r = rows  # same session, fresher read of the same set
    elif not late_s:
        base_s, base_r, late_s, late_r = sess, rows, sess, rows
    # sess older than latest (stale data file): leave the store alone.
    return {"baseline_session": base_s, "baseline_rows": base_r,
            "latest_session": late_s, "latest_rows": late_r,
            "session": base_s, "rows": base_r}
def main():
    try:
        old_store = json.loads(STORE.read_text()) if STORE.exists() else {}
    except Exception:
        old_store = {}
    store={}
    for d in sorted(SITE.iterdir()):
        f=d/"data.json"
        if not d.is_dir() or not f.exists(): continue
        try: data=json.loads(f.read_text())
        except Exception: continue
        sess=session_of(data)
        rows=labels(data)
        if rows: store[d.name]=rotate(old_store.get(d.name), sess, rows)
    STORE.write_text(json.dumps(store,indent=1,sort_keys=True))
    print(f"rowsets: {len(store)} pages stored")
    return 0
if __name__=="__main__": sys.exit(main())
