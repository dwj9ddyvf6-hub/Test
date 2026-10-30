from __future__ import annotations
import json, os

MAX_JOURNAL_BYTES = int(os.environ.get("MUSE_JOURNAL_MAX_BYTES", "5000000"))

def _rotate_if_needed(path):
    """Bounded growth (CURE D8): rotate path -> path.1 (single generation,
    overwritten) once it exceeds MAX_JOURNAL_BYTES. Append-only semantics
    within a generation are preserved; readers use tail_lines."""
    try:
        if os.path.exists(path) and os.path.getsize(path) >= MAX_JOURNAL_BYTES:
            os.replace(path, path + ".1")
    except OSError:
        pass

def append_line(path, record: dict):
    """Single O_APPEND write of one JSON line. Never read-modify-write (DESIGN §3d)."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    _rotate_if_needed(path)
    line = json.dumps(record, separators=(",",":"), sort_keys=True) + "\n"
    fd = os.open(path, os.O_WRONLY|os.O_CREAT|os.O_APPEND, 0o644)
    try: os.write(fd, line.encode())
    finally: os.close(fd)

def tail_lines(path, n=200):
    if not os.path.exists(path): return []
    with open(path, "rb") as fh:
        fh.seek(0, os.SEEK_END); size = fh.tell()
        block = min(size, max(8192, n*512)); fh.seek(size-block); data = fh.read().decode(errors="replace")
    lines = [l for l in data.splitlines() if l.strip()]
    out=[]
    for l in lines[-n:]:
        try: out.append(json.loads(l))
        except json.JSONDecodeError: pass
    return out

def positions_from_journal(path):
    """Rebuild open positions from fill events in own journal (netting)."""
    pos={}
    for rec in tail_lines(path, 100000):
        if rec.get("event")!="fill": continue
        sym=rec["symbol"]; qty=float(rec["qty"]) * (1 if rec.get("side")=="buy" else -1)
        cur=pos.get(sym)
        if cur is None:
            pos[sym]={"symbol":sym,"qty":qty,"avg_price":float(rec.get("price",0)),"opened_at":rec.get("ts"),"intent_id":rec.get("intent_id"),
                      "exit_rules":rec.get("exit_rules"),"stop_px":rec.get("stop_price"),"target":rec.get("target"),**{k: rec.get(k) for k in ("condor","entry_credit","spread","entry_debit","expiry","occ","box_lo","box_hi","datr14_prior","entry_spot","kind","debit") if rec.get(k) is not None}}
        else:
            newq=cur["qty"]+qty
            if qty>0 and cur["qty"]>=0 and newq!=0: cur["avg_price"]=(cur["avg_price"]*cur["qty"]+float(rec.get("price",0))*qty)/newq
            cur["qty"]=newq
            if newq==0: del pos[sym]; continue
    return [p for p in pos.values() if p["qty"]!=0]
