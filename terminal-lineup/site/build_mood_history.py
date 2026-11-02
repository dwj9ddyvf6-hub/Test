#!/usr/bin/env python3
"""Market Mood composite recorder (R2, 2026-11-02): the psychology
engine's live state files ARE the dated composite record. This producer
copies {date, composite_percentile, regime} from every
psychology-engine/live/state/*.json into
site/market-mood/composite-history.json, sorted by date, deduped.
Re-run on each refresh; the C4 strip accrues one point per session.
It invents nothing: a session with no state file gets no point."""
import json, sys
from pathlib import Path
SITE = Path(__file__).resolve().parent
SRC = SITE.parent/"psychology-engine"/"live"/"state"
def main():
    pts={}
    for f in sorted(SRC.glob("*.json")):
        try: d=json.loads(f.read_text())
        except Exception: continue
        if d.get("date") and isinstance(d.get("composite_percentile"),(int,float)):
            pts[d["date"]]={"date":d["date"],"composite":d["composite_percentile"],"regime":d.get("regime") or ""}
    out=[pts[k] for k in sorted(pts)]
    (SITE/"market-mood"/"composite-history.json").write_text(json.dumps({"points":out,"source":"psychology-engine/live/state"},indent=1))
    print(f"mood history: {len(out)} dated points")
    return 0
if __name__=="__main__": sys.exit(main())
