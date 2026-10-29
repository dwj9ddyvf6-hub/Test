"""instOwnership and instActivity from the SEC's Form 13F Data Sets (bulk quarterly files; never per-filer crawling).

Ported from Silicon's inst_13f.py, with these changes:
  - the zip is aggregated ONCE per quarter into a small per-CUSIP table (shares, filings, the issuer-name spellings seen),
    cached under cache/morgue/13f/ and re-used; the name-to-ticker join runs on the table, so a change in the wanted
    names never re-reads 100 MB;
  - option rows are left out (PUTCALL non-empty: their share count is the underlying notional, not a holding): Silicon's
    ownership summed them in;
  - a name that two or more roster tickers share (GOOG and GOOGL are both 'Alphabet Inc.') is ambiguous and joins none,
    where Silicon gave it to whichever ticker came first;
  - the zip comes from the SEC through the desk's data layer (declared User-Agent, shared pacing), its URL found by the
    data set's naming rule rather than hard-coded to one quarter.
13F is quarterly, filed up to 45 days after quarter end: the vintage travels with the leaf. The CUSIP-to-ticker join is by
normalised issuer name, with the coverage it achieves PUBLISHED (names_resolved of names_wanted); an unresolved or ambiguous
name stays None, never guessed. 'filings' counts a manager's accessions (an amendment counts again), not distinct managers."""
import io
import json
import os
import re
import zipfile
from datetime import date, timedelta

from . import board, cache_path

INFOTABLE = "INFOTABLE.TSV"
NAMES_KEPT = 5


def normalize_name(name):
    s = re.sub(r"[^A-Z0-9 ]", " ", (name or "").upper())
    for suffix in (" INC", " CORP", " CORPORATION", " CO", " COMPANY", " LTD", " LLC", " PLC", " HOLDINGS", " GROUP"):
        if s.endswith(suffix):
            s = s[: -len(suffix)]
    return re.sub(r"\s+", " ", s).strip()


def name_key(name):
    """de-spaced, suffix-stripped match key: some filers strip the spaces from issuer names ('CARDINALHEALTHINC'). Filer
    abbreviations ('CISCO SYS' for Cisco Systems) do not resolve under it: those names stay unmatched by design."""
    n = normalize_name(name).replace(" ", "")
    for suffix in ("INC", "CORP", "LTD", "PLC", "CO"):
        if n.endswith(suffix) and len(n) > len(suffix) + 2:
            n = n[: -len(suffix)]
            break
    return n


def aggregate_zip(zip_source):
    """Stream one 13F Data Set zip's INFOTABLE.tsv (memory-bounded) -> {cusip: {"shares","filings","names":{key: rows}}}.
    Share rows only (SSHPRNAMTTYPE == 'SH'; PRN rows are principal), option rows (PUTCALL set) excluded. A manager's
    filing is counted once per CUSIP where its rows are contiguous (the file lists a filing's rows together); the rare
    return of an accession already closed counts again and sets `contiguous` false."""
    zf = zipfile.ZipFile(zip_source)
    member = next((n for n in zf.namelist() if n.upper().endswith(INFOTABLE)), None)
    if member is None:
        raise ValueError("no INFOTABLE.tsv in the 13F data set zip")
    agg, last_acc, closed, cur, ids = {}, {}, set(), None, {}
    contiguous = True
    keys = {}                                              # issuer name -> its match key (the same few thousand spellings recur)
    with zf.open(member) as fh:
        text = io.TextIOWrapper(fh, encoding="utf-8", errors="replace")
        header = text.readline().rstrip("\n").split("\t")
        col = {name: i for i, name in enumerate(header)}
        tcol = col.get("SSHPRNAMTTYPE", col.get("SSHPRNTYPE"))
        pcol = col.get("PUTCALL")
        ci, ni, si, ai = col["CUSIP"], col["NAMEOFISSUER"], col["SSHPRNAMT"], col["ACCESSION_NUMBER"]
        for line in text:
            p = line.rstrip("\n").split("\t")
            if len(p) < len(header) or p[tcol] != "SH" or (pcol is not None and p[pcol].strip()):
                continue
            try:
                shares = float(p[si])
            except ValueError:
                continue
            acc = ids.setdefault(p[ai], len(ids))
            if acc != cur:
                if cur is not None:
                    closed.add(cur)
                if acc in closed:
                    contiguous = False
                cur = acc
            a = agg.get(p[ci])
            if a is None:
                a = agg[p[ci]] = {"shares": 0.0, "filings": 0, "names": {}}
            a["shares"] += shares
            if last_acc.get(p[ci]) != acc:
                a["filings"] += 1
                last_acc[p[ci]] = acc
            k = keys.get(p[ni])
            if k is None:
                k = keys[p[ni]] = name_key(p[ni])
            if k:
                a["names"][k] = a["names"].get(k, 0) + 1
    for a in agg.values():
        a["names"] = dict(sorted(a["names"].items(), key=lambda kv: -kv[1])[:NAMES_KEPT])
    return agg, {"rows_contiguous": contiguous, "accessions": len(ids)}


def resolve(agg, wanted):
    """join the aggregate to tickers by issuer name -> ({cusip: symbol}, stats).
    wanted: {symbol: company name}. A name two tickers share is ambiguous; a ticker matching more than one CUSIP is
    dropped; both are counted, never guessed."""
    by_key, shared = {}, set()
    for sym, name in wanted.items():
        k = name_key(name)
        if not k:
            continue
        if k in by_key and by_key[k] != sym:
            shared.add(k)
        by_key.setdefault(k, sym)
    sym_cusips = {}
    for cusip, a in agg.items():
        for k in a["names"]:
            if k in by_key and k not in shared:
                sym_cusips.setdefault(by_key[k], set()).add(cusip)
    cmap, ambiguous = {}, 0
    for sym, cs in sym_cusips.items():
        if len(cs) > 1:
            ambiguous += 1
            continue
        cmap[next(iter(cs))] = sym
    return cmap, {"names_wanted": len(wanted), "names_resolved": len(cmap), "ambiguous_symbols": ambiguous,
                  "shared_names": len(shared)}


def ownership_activity(cur, prev, shares_out, cusip_map):
    """-> {symbol: {instOwnership, instActivity, ownership_pct, share_change_pct, filing_change, filings}} keyed only
    where the CUSIP resolves and shares outstanding are known. instOwnership is the cross-sectional percentile of the
    ownership share; instActivity the mean of board.lin(QoQ share change %, -20, 20) and board.lin(filings change,
    -10, 10)."""
    by_sym = {}
    for cusip, a in cur.items():
        sym = cusip_map.get(cusip)
        if not sym or not shares_out.get(sym):
            continue
        p = (prev or {}).get(cusip)
        by_sym[sym] = {"ownership_pct": a["shares"] / shares_out[sym] * 100.0, "agg_shares": a["shares"],
                       "share_change_pct": ((a["shares"] / p["shares"] - 1.0) * 100.0 if p and p["shares"] else None),
                       "filing_change": (a["filings"] - p["filings"]) if p else None, "filings": a["filings"]}
    own = {s: v["ownership_pct"] for s, v in by_sym.items()}
    for sym, v in by_sym.items():
        v["instOwnership"] = board.pct_rank(own, sym) if len(own) >= 2 else None
        parts = []
        if v["share_change_pct"] is not None:
            parts.append(board.lin(v["share_change_pct"], -20, 20))
        if v["filing_change"] is not None:
            parts.append(board.lin(v["filing_change"], -10, 10))
        v["instActivity"] = (sum(parts) / len(parts)) if parts else None
    return by_sym


# ---- the data sets' naming and the per-quarter cache ------------------------------------------------------------------

def period_files(today, count=4):
    """the data set periods to look for, newest first: SEC publishes 3-month sets named 01mar2026-31may2026_form13f.zip
    (March-May, June-August, September-November, December-February). -> [(label, file name)]"""
    out = []
    y = today.year
    starts = []
    for yy in (y, y - 1, y - 2):
        for mm in (12, 9, 6, 3):
            starts.append(date(yy, mm, 1))
    for s in sorted(starts, reverse=True):
        if s > today:
            continue
        e_month = s.month + 2
        e_year = s.year + (1 if e_month > 12 else 0)
        e_month = e_month - 12 if e_month > 12 else e_month
        nxt = date(e_year + (1 if e_month == 12 else 0), 1 if e_month == 12 else e_month + 1, 1)
        end = nxt - timedelta(days=1)
        label = f"{s.isoformat()}..{end.isoformat()}"
        out.append((label, f"{s.strftime('%d%b%Y').lower()}-{end.strftime('%d%b%Y').lower()}_form13f.zip", end))
        if len(out) >= count:
            break
    return out


def agg_path(root, label):
    return cache_path(root, "13f", f"agg_{label.replace('..', '_')}.json")


def load_agg(root, label):
    try:
        with open(agg_path(root, label), encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def save_agg(root, label, agg, meta):
    p = agg_path(root, label)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump({"label": label, "meta": meta, "cusips": agg}, fh, separators=(",", ":"))
    os.replace(tmp, p)
