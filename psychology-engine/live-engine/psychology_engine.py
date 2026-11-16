
#!/usr/bin/env python3
"""Psychology Engine v1 core. Design: research_notes/psychology-engine-2026-10-30/ENGINE-DESIGN.md
No em dashes anywhere in outputs. History inputs backfilled; ledger never backfilled."""
import bisect, csv, hashlib, io, json, os, re, sys, time, zipfile
from datetime import date, datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.abspath(__file__))
SERIES = os.path.join(ROOT, "history", "series")
GAUGES = os.path.join(ROOT, "history", "gauges")
PROV = os.path.join(ROOT, "history", "provenance", "PULL-LOG.md")
RAW = os.path.join(ROOT, "live", "raw")
OUT = os.path.join(ROOT, "output")
TODAY = date.today().isoformat()
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) psychology-engine/1.0"}

def log_pull(series, route, rows, span, note):
    os.makedirs(os.path.dirname(PROV), exist_ok=True)
    with open(PROV, "a", encoding="utf-8") as fh:
        fh.write(f"- {TODAY} | {series} | route: {route} | rows: {rows} | span: {span} | {note}\n")

def fetch(url, timeout=60, binary=False):
    # curl transport: proven in this environment (proxy aware); python
    # requests timed out on FRED and Cboe through the egress proxy.
    import subprocess, time as _t
    last = None
    for attempt in range(3):
        # No browser user agent by default: FRED stalls on a Chrome UA
        # through this proxy and answers instantly with the default one.
        out = subprocess.run(["curl", "-sL", "--fail", "--max-time", str(timeout), url],
                             capture_output=True, timeout=timeout + 15)
        if out.returncode == 0:
            return out.stdout if binary else out.stdout.decode("utf-8", "replace")
        last = RuntimeError(f"curl exit {out.returncode} for {url}")
        _t.sleep(3 * (attempt + 1))
    raise last

def save_raw(collector, name, content):
    d = os.path.join(RAW, collector, TODAY)
    os.makedirs(d, exist_ok=True)
    mode = "wb" if isinstance(content, bytes) else "w"
    with open(os.path.join(d, name), mode) as fh:
        fh.write(content)
    return os.path.join(d, name)

def sha(b):
    if isinstance(b, str): b = b.encode()
    return hashlib.sha256(b).hexdigest()

REQUIRED_HEADER = ["series:", "source:", "source_url_or_route:", "retrieved:", "last_pull:",
                   "revision_policy:", "as_of_meaning:", "archive_claim:", "downloaded_span:",
                   "breaks:", "transforms:", "file_sha256:"]

def _stored_span_and_count(fname):
    """(span, count) of data rows already stored for fname, or ("absent", 0)."""
    rows = read_series(fname)
    if not rows:
        return "absent", 0
    key = list(rows[0].keys())[0]
    dates = [str(r[key]) for r in rows]
    return f"{min(dates)} to {max(dates)}", len(rows)

def write_series(fname, header, columns, rows):
    """header: dict with keys matching REQUIRED_HEADER prefixes. rows: list of dicts.

    Preservation rule (2026-10-30 cure): an empty row set never overwrites
    stored data. A failed or empty pull must not destroy history that a
    previous good pull landed; the caller records the failure in the pull
    log and the stored series stays as it was."""
    os.makedirs(SERIES, exist_ok=True)
    path = os.path.join(SERIES, fname)
    if not rows:
        span, n = _stored_span_and_count(fname)
        if n:
            return path, span, n
    span = "absent"
    if rows:
        dates = [str(r[columns[0]]) for r in rows]
        span = f"{min(dates)} to {max(dates)}"
    lines = []
    for req in REQUIRED_HEADER:
        key = req.rstrip(":")
        lines.append(f"# {req} {header.get(key, '')}")
    lines = [l for l in lines if l and not l.startswith("# downloaded_span:")]
    lines.insert(8, f"# downloaded_span: {span}")
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write("\n".join(lines) + "\n")
        w = csv.DictWriter(fh, fieldnames=columns)
        w.writeheader()
        seen = set()
        for r in rows:
            k = str(r[columns[0]])
            if k in seen: continue
            seen.add(k)
            w.writerow({c: r.get(c, "") for c in columns})
    return path, span, len(seen)

def write_absent(fname, header):
    """Record an honest absence ONLY where no data is stored. If a previous
    pull landed rows, this is a no-op that preserves them: an absence note
    describes a series that was never obtained, it must never erase one
    that was. Returns (path, span, count) of what is actually stored."""
    return write_series(fname, header, ["date", "value"], [])

def preserve_series(fname, header):
    """Failure-path replacement for write_absent in collector exception
    handlers. A transient pull failure is recorded by the caller in the
    pull log; the stored series (good history if any, an absence note if
    none) is left exactly as it was. Returns (path, span, count)."""
    os.makedirs(SERIES, exist_ok=True)
    span, n = _stored_span_and_count(fname)
    if n:
        return os.path.join(SERIES, fname), span, n
    return write_absent(fname, header)

def read_series(fname):
    path = os.path.join(SERIES, fname)
    if not os.path.exists(path): return []
    rows = []
    with open(path, encoding="utf-8") as fh:
        data = [l for l in fh if not l.startswith("#") and l.strip()]
    for r in csv.DictReader(data):
        rows.append(r)
    return rows

def check_header(path):
    """Provenance checker: returns list of problems (empty means pass)."""
    problems = []
    with open(path, encoding="utf-8") as fh:
        head = []
        for line in fh:
            if line.startswith("#"): head.append(line)
            else: break
    text = "".join(head)
    for req in REQUIRED_HEADER:
        if req not in text: problems.append(f"missing provenance field {req}")
    # duplicate natural keys
    rows = []
    with open(path, encoding="utf-8") as fh:
        data = [l for l in fh if not l.startswith("#")]
    try:
        rd = list(csv.DictReader(data))
        if rd:
            key0 = list(rd[0].keys())[0]
            seen = set()
            for r in rd:
                if r[key0] in seen: problems.append(f"duplicate natural key {r[key0]}")
                seen.add(r[key0])
    except Exception as e:
        problems.append(f"unparseable: {e}")
    return problems

def expanding_percentiles(values):
    """values: list of floats in date order. Returns expanding percentile per uniform rule."""
    out, s = [], []
    for v in values:
        bisect.insort(s, v)
        rank = bisect.bisect_right(s, v)
        out.append(100.0 * rank / len(s))
    return out

def full_pct(history, v):
    if not history: return None
    return 100.0 * bisect.bisect_right(sorted(history), v) / len(history)

def zone(p):
    if p is None: return "insufficient history"
    for hi, name in [(2,"Extreme fear"),(5,"Severe fear"),(20,"Fear"),(40,"Cautious"),
                     (60,"Neutral"),(80,"Confident"),(95,"Greed"),(98,"Severe greed")]:
        if p < hi: return name
    return "Extreme greed"

def fnum(x):
    try:
        if x is None or x == "": return None
        return float(x)
    except Exception: return None

HDR = lambda **kw: kw
