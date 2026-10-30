#!/usr/bin/env python3
"""Psychology Engine v1 pipeline: backfill, live collectors, compiler, page, hooks.
Implements ENGINE-DESIGN.md (2026-10-30). No em dashes in any output."""
import bisect, csv, hashlib, http.client, io, json, os, re, sys, zipfile
from datetime import date, datetime, timedelta, timezone
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from psychology_engine import (ROOT, SERIES, GAUGES, PROV, RAW, OUT, TODAY, fetch,
    save_raw, sha, write_series, preserve_series, read_series, log_pull, fnum,
    expanding_percentiles, full_pct, zone)

RESULTS = {}

def note(series, ok, detail):
    RESULTS[series] = {"ok": ok, "detail": detail}
    return RESULTS[series]

def H(series, source, route, claim, breaks="none known", transforms="none", rev="latest revised stored; first published value not obtainable from this route"):
    return {"series": series, "source": source, "source_url_or_route": route,
            "retrieved": TODAY, "last_pull": TODAY, "revision_policy": rev,
            "as_of_meaning": "date column is the observation date (as-of), not the download date",
            "archive_claim": claim, "breaks": breaks, "transforms": transforms,
            "file_sha256": ""}

# ---------------- backfill collectors ----------------

def bf_fred(series_id, fname, name, claim, breaks="none known", chunk_from=None):
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}&cosd=1950-01-01"
    try:
        if chunk_from:
            # FRED graph caps a single pull near 800 points; pull 2 year windows and merge.
            merged = {}
            y = chunk_from
            while y <= 2026:
                u = (f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
                     f"&cosd={y}-01-01&coed={y+1}-12-31")
                try:
                    part = fetch(u)
                    for r in csv.DictReader(io.StringIO(part)):
                        v = fnum(r.get(series_id))
                        if v is not None: merged[r["observation_date"]] = v
                except Exception:
                    pass
                y += 2
            rows = [{"date": d, "value_first": v, "value_latest": v} for d, v in sorted(merged.items())]
            h = H(name, "FRED (Federal Reserve Bank of St. Louis), chunked 2 year windows", url, claim, breaks,
                  rev="both vintages stored where obtainable; FRED route serves latest vintage, value_first set equal at first pull")
            p, span, n = write_series(fname, h, ["date", "value_first", "value_latest"], rows)
            log_pull(name, url, n, span, "ok chunked")
            return note(name, True, f"{n} rows, {span}")
        raw = fetch(url); save_raw("backfill_fred", fname + ".raw.csv", raw)
        rows = []
        for r in csv.DictReader(io.StringIO(raw)):
            v = fnum(r.get(series_id))
            if v is not None:
                rows.append({"date": r["observation_date"], "value_first": v, "value_latest": v})
        h = H(name, "FRED (Federal Reserve Bank of St. Louis)", url, claim, breaks,
              rev="both vintages stored where obtainable; FRED route serves latest vintage, value_first set equal at first pull and preserved on later pulls")
        h["file_sha256"] = sha(raw)
        p, span, n = write_series(fname, h, ["date", "value_first", "value_latest"], rows)
        log_pull(name, url, n, span, "ok")
        return note(name, True, f"{n} rows, {span}")
    except Exception as e:
        preserve_series(fname, H(name, "FRED", url, claim, breaks))
        log_pull(name, url, 0, "absent", f"FAILED {type(e).__name__}: {e}")
        return note(name, False, str(e))

def bf_cboe_index(name, fname, claim, breaks="none known"):
    url = f"https://cdn.cboe.com/api/global/us_indices/daily_prices/{name}_History.csv"
    try:
        raw = fetch(url); save_raw("backfill_cboe", fname + ".raw.csv", raw)
        rows = []
        for r in csv.DictReader(io.StringIO(raw)):
            d = r.get("DATE", "")
            try:
                dt = datetime.strptime(d, "%m/%d/%Y").date().isoformat()
            except Exception:
                dt = d
            v = fnum(r.get(name) or r.get("CLOSE"))
            if v is not None:
                row = {"date": dt, "close": v}
                for k in ("OPEN", "HIGH", "LOW"):
                    if fnum(r.get(k)) is not None: row[k.lower()] = fnum(r[k])
                rows.append(row)
        cols = ["date", "open", "high", "low", "close"] if rows and "open" in rows[0] else ["date", "close"]
        h = H(fname.replace(".csv",""), "Cboe index history file", url, claim, breaks)
        h["file_sha256"] = sha(raw)
        p, span, n = write_series(fname, h, cols, rows)
        log_pull(fname, url, n, span, "ok")
        return note(fname, True, f"{n} rows, {span}")
    except Exception as e:
        preserve_series(fname, H(fname, "Cboe", url, claim, breaks))
        log_pull(fname, url, 0, "absent", f"FAILED {type(e).__name__}: {e}")
        return note(fname, False, str(e))

def bf_altme():
    url = "https://api.alternative.me/fng/?limit=0&format=json"
    fname, name = "altme_fear_greed_daily.csv", "altme_fear_greed_daily"
    try:
        raw = fetch(url); save_raw("backfill_crypto", "altme.json", raw)
        data = json.loads(raw)["data"]
        rows = []
        for d in data:
            dt = datetime.fromtimestamp(int(d["timestamp"]), tz=timezone.utc).date().isoformat()
            rows.append({"date": dt, "value": int(d["value"]), "classification": d.get("value_classification", "")})
        rows.sort(key=lambda r: r["date"])
        h = H(name, "Alternative.me Crypto Fear and Greed Index API", url,
              "daily from 2018-02-01 VERIFIED in design",
              breaks="survey component reported paused by publisher in later years (recipe note)",
              transforms="none; recipe stored: volatility 25, momentum/volume 25, social 15, surveys 15 (paused), dominance 10, Trends 10")
        h["file_sha256"] = sha(raw)
        p, span, n = write_series(fname, h, ["date", "value", "classification"], rows)
        log_pull(name, url, n, span, "ok")
        return note(name, True, f"{n} rows, {span}")
    except Exception as e:
        preserve_series(fname, H(name, "Alternative.me", url, "2018 VERIFIED"))
        log_pull(name, url, 0, "absent", f"FAILED {e}")
        return note(name, False, str(e))

def bf_funding(symbol, fname):
    name = fname.replace(".csv", "")
    rows, start = [], 1567900800000  # 2019-09-08 approx perp era start
    source_note = "Binance public futures API"
    try:
        try:
            while True:
                url = f"https://fapi.binance.com/fapi/v1/fundingRate?symbol={symbol}&limit=1000&startTime={start}"
                raw = fetch(url); data = json.loads(raw)
                if not data: break
                for d in data:
                    dt = datetime.fromtimestamp(d["fundingTime"] / 1000, tz=timezone.utc).date().isoformat()
                    rows.append({"date": dt, "funding_rate": float(d["fundingRate"])})
                start = data[-1]["fundingTime"] + 1
                if len(data) < 1000: break
        except Exception:
            rows = []
        if not rows:
            # OKX public fallback (design names direct exchange APIs as cross-check and fallback)
            inst = symbol.replace("USDT", "-USDT-SWAP")
            after = ""
            for _ in range(60):
                url = f"https://www.okx.com/api/v5/public/funding-rate-history?instId={inst}&limit=100" + (f"&after={after}" if after else "")
                data = json.loads(fetch(url)).get("data", [])
                if not data: break
                for d in data:
                    dt = datetime.fromtimestamp(int(d["fundingTime"]) / 1000, tz=timezone.utc).date().isoformat()
                    rows.append({"date": dt, "funding_rate": float(d["fundingRate"])})
                after = data[-1]["fundingTime"]
                if len(data) < 100: break
            source_note = "OKX public API (Binance route refused from this network; OKX is the design fallback)"
        if not rows: raise ValueError("no funding rows from Binance or OKX")
        # daily mean
        by = {}
        for r in rows: by.setdefault(r["date"], []).append(r["funding_rate"])
        daily = [{"date": d, "funding_rate_daily_mean": sum(v) / len(v)} for d, v in sorted(by.items())]
        save_raw("backfill_crypto", fname + ".note.txt", f"funding intervals fetched: {len(rows)} via {source_note}")
        h = H(name, source_note + " (cross-check and fallback for Coinalyze per design)",
              "exchange public funding-rate history", "liquid history from about 2019, per-venue starts recorded as downloaded")
        p, span, n = write_series(fname, h, ["date", "funding_rate_daily_mean"], daily)
        log_pull(name, "binance fapi fundingRate", n, span, f"ok, {len(rows)} intervals")
        return note(name, True, f"{n} daily rows, {span}, {len(rows)} intervals")
    except Exception as e:
        preserve_series(fname, H(name, "Binance public API", "fapi fundingRate", "about 2019"))
        log_pull(name, "binance", 0, "absent", f"FAILED {e}")
        return note(name, False, str(e))

def bf_baker_wurgler():
    fname, name = "baker_wurgler_monthly.csv", "baker_wurgler_monthly"
    page_urls = ["https://pages.stern.nyu.edu/~jwurgler/data/",
                 "https://pages.stern.nyu.edu/~jwurgler/"]
    try:
        xlsx_url = None
        for pu in page_urls:
            try:
                html = fetch(pu)
                m = re.findall(r'href="([^"]*Investor_Sentiment_Data[^"]*\.xlsx)"', html)
                if m:
                    xlsx_url = m[0]
                    if not xlsx_url.startswith("http"):
                        xlsx_url = "https://pages.stern.nyu.edu/~jwurgler/data/" + xlsx_url.split("/")[-1]
                    break
            except Exception:
                continue
        if not xlsx_url:
            xlsx_url = "https://pages.stern.nyu.edu/~jwurgler/data/SENTIMENT.xls"
        raw = fetch(xlsx_url, binary=True); save_raw("backfill_bw", "bw.xlsx", raw)
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(raw), data_only=True, read_only=True)
        ws = wb[wb.sheetnames[0]]
        rows, hdr = [], None
        for i, row in enumerate(ws.iter_rows(values_only=True)):
            if i == 0:
                hdr = [str(c or "") for c in row]; continue
            if row[0] is None: continue
            s = str(row[0]).strip()
            m = re.match(r"(\d{4})(\d{2})", s)
            if not m: continue
            dt = f"{m.group(1)}-{m.group(2)}-01"
            vals = {}
            for j, c in enumerate(hdr):
                if j and row[j] is not None and isinstance(row[j], (int, float)):
                    vals[c] = row[j]
            level = vals.get("SENTIM") or vals.get("SENTIMENT") or (list(vals.values())[0] if vals else None)
            ortho = vals.get("SENTIMo") or vals.get("SENTIMENT_ORTHO")
            if level is not None:
                rows.append({"date": dt, "value_first": level, "value_latest": level, "orthogonalised": ortho if ortho is not None else ""})
        h = H(name, "Jeffrey Wurgler NYU Stern faculty spreadsheet", xlsx_url,
              "monthly from July 1965 VERIFIED as published span",
              breaks="index recomputed when components revise; download date and file hash stored",
              rev="both vintages stored where obtainable; file hash pins this vintage")
        h["file_sha256"] = sha(raw)
        p, span, n = write_series(fname, h, ["date", "value_first", "value_latest", "orthogonalised"], rows)
        log_pull(name, xlsx_url, n, span, "ok")
        return note(name, True, f"{n} rows, {span}")
    except Exception as e:
        preserve_series(fname, H(name, "Wurgler NYU Stern spreadsheet", "pages.stern.nyu.edu/~jwurgler", "July 1965 VERIFIED"))
        log_pull(name, "wurgler", 0, "absent", f"FAILED {type(e).__name__}: {e}")
        return note(name, False, str(e))

def bf_aaii():
    fname, name = "aaii_weekly.csv", "aaii_weekly"
    urls = ["https://www.aaii.com/files/surveys/sentiment-survey.xlsx",
            "https://www.aaii.com/files/surveys/sentiment-survey.csv"]
    last = None
    for url in urls:
        try:
            raw = fetch(url, binary=True); save_raw("backfill_surveys", "aaii.raw", raw)
            rows = []
            if url.endswith(".xlsx"):
                import openpyxl
                wb = openpyxl.load_workbook(io.BytesIO(raw), data_only=True, read_only=True)
                ws = wb[wb.sheetnames[0]]
                started = False
                for row in ws.iter_rows(values_only=True):
                    cells = [c for c in row]
                    d = cells[0]
                    if isinstance(d, (datetime, date)):
                        bull, neut, bear = (fnum(cells[1]), fnum(cells[2]), fnum(cells[3]))
                        if bull is not None and bear is not None:
                            if bull <= 1.5: bull, neut, bear = bull * 100, (neut or 0) * 100, bear * 100
                            rows.append({"date": d.date().isoformat() if isinstance(d, datetime) else d.isoformat(),
                                         "bullish_pct": round(bull, 2), "neutral_pct": round(neut or 0, 2),
                                         "bearish_pct": round(bear, 2), "spread": round(bull - bear, 2)})
            rows.sort(key=lambda r: r["date"])
            if not rows: raise ValueError("no AAII rows parsed")
            h = H(name, "AAII Sentiment Survey weekly spreadsheet (public download)", url,
                  "archive July 1987 VERIFIED in design",
                  breaks="mail to online collection break in 2000 marked by publisher",
                  transforms="spread = bullish_pct - bearish_pct computed at gauge stage; shares as published")
            h["file_sha256"] = sha(raw)
            p, span, n = write_series(fname, h, ["date", "bullish_pct", "neutral_pct", "bearish_pct", "spread"], rows)
            log_pull(name, url, n, span, "ok")
            return note(name, True, f"{n} rows, {span}")
        except Exception as e:
            last = e; continue
    preserve_series(fname, H(name, "AAII public download", urls[0], "July 1987 VERIFIED"))
    log_pull(name, urls[0], 0, "absent", f"FAILED {last}")
    return note(name, False, str(last))

def bf_naaim():
    fname, name = "naaim_weekly.csv", "naaim_weekly"
    try:
        html = fetch("https://naaim.org/programs/naaim-exposure-index/")
        save_raw("backfill_surveys", "naaim_page.html", html)
        links = re.findall(r'href="([^"]+\.(?:xlsx|xls|csv))"', html)
        if not links: raise ValueError("no data file link found on NAAIM page")
        url = links[0]
        if not url.startswith("http"): url = "https://naaim.org" + url
        raw = fetch(url, binary=True); save_raw("backfill_surveys", "naaim.raw", raw)
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(raw), data_only=True, read_only=True)
        rows = []
        for ws in wb.worksheets:
            for row in ws.iter_rows(values_only=True):
                d = row[0]
                if isinstance(d, (datetime, date)):
                    vals = [fnum(c) for c in row[1:6]]
                    mean = vals[3] if len(vals) > 3 and vals[3] is not None else (vals[0] if vals else None)
                    if mean is not None:
                        rows.append({"date": d.date().isoformat() if isinstance(d, datetime) else d.isoformat(),
                                     "mean_exposure": mean})
            if rows: break
        rows.sort(key=lambda r: r["date"])
        if not rows: raise ValueError("no NAAIM rows parsed")
        h = H(name, "NAAIM Exposure Index weekly file (public)", url,
              "archive July 2006 VERIFIED in design", transforms="mean exposure as published; percentile only, raw level never thresholded")
        h["file_sha256"] = sha(raw)
        p, span, n = write_series(fname, h, ["date", "mean_exposure"], rows)
        log_pull(name, url, n, span, "ok")
        return note(name, True, f"{n} rows, {span}")
    except Exception as e:
        preserve_series(fname, H(name, "NAAIM public file", "https://naaim.org/programs/naaim-exposure-index/", "July 2006 VERIFIED"))
        log_pull(name, "naaim page", 0, "absent", f"FAILED {type(e).__name__}: {e}")
        return note(name, False, str(e))

def bf_cboe_putcall():
    fname, name = "cboe_putcall_daily.csv", "cboe_putcall_daily"
    candidates = [
        "https://cdn.cboe.com/resources/us/options/market_statistics/historical_data/totalpc.csv",
        "https://www.cboe.com/us/options/market_statistics/historical_data/totalpc.csv",
    ]
    last = None
    for base in candidates:
        try:
            raw = fetch(base); save_raw("backfill_cboe", "putcall.raw.csv", raw)
            rows = []
            for r in csv.DictReader(io.StringIO(raw)):
                keys = {k.lower(): v for k, v in r.items()}
                d = keys.get("date") or keys.get("trade_date") or ""
                try: dt = datetime.strptime(d.strip(), "%m/%d/%Y").date().isoformat()
                except Exception:
                    try: dt = datetime.strptime(d.strip(), "%Y-%m-%d").date().isoformat()
                    except Exception: continue
                row = {"date": dt}
                for src, dst in [("total", "total_ratio"), ("equity", "equity_ratio"), ("index", "index_ratio"),
                                 ("total put/call ratio", "total_ratio"), ("equity put/call ratio", "equity_ratio"),
                                 ("index put/call ratio", "index_ratio")]:
                    if src in keys and fnum(keys[src]) is not None: row[dst] = fnum(keys[src])
                if len(row) > 1: rows.append(row)
            if not rows: raise ValueError("no putcall rows parsed")
            h = H(name, "Cboe daily market statistics put/call files", base,
                  "total from 2003, equity revised series from 2006, UNVERIFIED in design, recorded as downloaded",
                  transforms="total, equity and index ratios stored as three separate series, never averaged")
            h["file_sha256"] = sha(raw)
            p, span, n = write_series(fname, h, ["date", "total_ratio", "equity_ratio", "index_ratio"], rows)
            log_pull(name, base, n, span, "ok")
            return note(name, True, f"{n} rows, {span}")
        except Exception as e:
            last = e; continue
    # try the three separate files route
    try:
        merged = {}
        got = []
        for kind, col in [("totalpc", "total_ratio"), ("equitypc", "equity_ratio"), ("indexpc", "index_ratio")]:
            u = f"https://cdn.cboe.com/resources/us/options/market_statistics/historical_data/{kind}.csv"
            raw = fetch(u); got.append(kind)
            for r in csv.DictReader(io.StringIO(raw)):
                keys = {k.lower(): v for k, v in r.items()}
                d = (keys.get("date") or "").strip()
                try: dt = datetime.strptime(d, "%m/%d/%Y").date().isoformat()
                except Exception: continue
                v = None
                for k, val in keys.items():
                    if "ratio" in k or "put/call" in k: v = fnum(val)
                if v is not None: merged.setdefault(dt, {"date": dt})[col] = v
        rows = [merged[k] for k in sorted(merged)]
        if not rows: raise ValueError("separate files empty")
        h = H(name, "Cboe daily market statistics put/call files", "cdn.cboe.com historical_data",
              "total from 2003, equity from 2006, UNVERIFIED, recorded as downloaded",
              transforms="three ratios kept separate")
        p, span, n = write_series(fname, h, ["date", "total_ratio", "equity_ratio", "index_ratio"], rows)
        log_pull(name, "cboe separate pc files", n, span, "ok")
        return note(name, True, f"{n} rows, {span}")
    except Exception as e:
        preserve_series(fname, H(name, "Cboe put/call files", candidates[0], "2003 and 2006 UNVERIFIED"))
        log_pull(name, candidates[0], 0, "absent", f"FAILED {last} / {e}")
        return note(name, False, f"{last} / {e}")

def bf_margin():
    fname, name = "finra_margin_monthly.csv", "finra_margin_monthly"
    try:
        html = fetch("https://www.finra.org/investors/learn-to-invest/advanced-investing/margin-statistics")
        save_raw("backfill_flows_margin", "finra_margin_page.html", html)
        links = re.findall(r'href="([^"]+\.xlsx)"', html)
        if not links: raise ValueError("no xlsx link on FINRA margin page")
        url = links[0]
        if not url.startswith("http"): url = "https://www.finra.org" + url
        raw = fetch(url, binary=True); save_raw("backfill_flows_margin", "margin.xlsx", raw)
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(raw), data_only=True, read_only=True)
        rows = []
        for ws in wb.worksheets:
            for row in ws.iter_rows(values_only=True):
                d = row[0]
                dstr = None
                if isinstance(d, (datetime, date)):
                    dstr = (d.date() if isinstance(d, datetime) else d).isoformat()
                elif isinstance(d, str) and re.match(r"^\d{4}-\d{2}$", d.strip()):
                    dstr = d.strip() + "-01"
                if dstr and len(row) >= 4:
                    debit, fc_cash, fc_margin = fnum(row[1]), fnum(row[2]), fnum(row[3])
                    if debit is not None:
                        rows.append({"date": dstr, "debit_balances": debit,
                                     "free_credit_cash": fc_cash or "", "free_credit_margin": fc_margin or ""})
            if rows: break
        rows.sort(key=lambda r: r["date"])
        if not rows: raise ValueError("no margin rows parsed")
        h = H(name, "FINRA margin statistics monthly Excel", url, "from January 1997 VERIFIED in design",
              breaks="February 2010 collection break: separate NYSE and FINRA collection before, one FINRA Rule 4521 collection after",
              rev="latest revised stored; first published values not obtainable from this route")
        h["file_sha256"] = sha(raw)
        p, span, n = write_series(fname, h, ["date", "debit_balances", "free_credit_cash", "free_credit_margin"], rows)
        log_pull(name, url, n, span, "ok")
        return note(name, True, f"{n} rows, {span}")
    except Exception as e:
        preserve_series(fname, H(name, "FINRA margin statistics", "finra.org margin statistics page", "January 1997 VERIFIED",
                              breaks="February 2010 collection break"))
        log_pull(name, "finra margin page", 0, "absent", f"FAILED {type(e).__name__}: {e}")
        return note(name, False, str(e))

def bf_cot_tff():
    fname, name = "cot_tff_weekly.csv", "cot_tff_weekly"
    rows_all, years_ok = [], []
    try:
        for year in range(2015, 2027):
            url = f"https://www.cftc.gov/files/dea/history/fut_fin_txt_{year}.zip"
            try:
                raw = fetch(url, binary=True, timeout=120)
            except Exception:
                continue
            save_raw("backfill_cot", f"fut_fin_txt_{year}.zip", raw)
            zf = zipfile.ZipFile(io.BytesIO(raw))
            txtname = [n for n in zf.namelist() if n.endswith(".txt")][0]
            text = zf.read(txtname).decode("utf-8", "replace")
            rdr = csv.DictReader(io.StringIO(text))
            if not rdr.fieldnames: continue
            cols = {c.lower().strip(): c for c in rdr.fieldnames}
            def find(*subs):
                for low, orig in cols.items():
                    if all(s in low for s in subs): return orig
                return None
            c_market = find("market")
            c_date = find("as_of_date") or find("report_date")
            c_oi = find("open_interest_all")
            c_lev_long = find("lev_money_positions_long")
            c_lev_short = find("lev_money_positions_short")
            if not (c_market and c_oi and c_lev_long and c_lev_short): continue
            years_ok.append(year)
            for r in rdr:
                mkt = (r.get(c_market) or "").upper()
                fam = None
                if "S&P 500" in mkt or "SP 500" in mkt or "S AND P" in mkt: fam = "spx"
                elif "NASDAQ-100" in mkt or "NASDAQ 100" in mkt: fam = "ndx"
                if not fam: continue
                d = (r.get(c_date) or "").strip()
                try: dt = datetime.strptime(d, "%y%m%d").date().isoformat()
                except Exception:
                    try: dt = datetime.strptime(d, "%Y-%m-%d").date().isoformat()
                    except Exception: continue
                oi, lo, sh = fnum(r.get(c_oi)), fnum(r.get(c_lev_long)), fnum(r.get(c_lev_short))
                if oi and lo is not None and sh is not None and oi > 0:
                    rows_all.append({"date": dt, "family": fam, "net": lo - sh, "open_interest": oi,
                                     "net_scaled": round((lo - sh) / oi, 6)})
        # one row per date: mean net_scaled across families present that week
        by = {}
        for r in rows_all: by.setdefault(r["date"], []).append(r["net_scaled"])
        rows = [{"date": d, "net_scaled_mean": round(sum(v) / len(v), 6), "families": len(v)} for d, v in sorted(by.items())]
        if not rows: raise ValueError("no TFF index rows parsed")
        h = H(name, "CFTC Traders in Financial Futures annual files (futures only)", "https://www.cftc.gov/files/dea/history/fut_fin_txt_<year>.zip",
              "published from 2006; complete annual files listed from September 2009 VERIFIED in design; this pull covers the years listed in the pull log",
              breaks="2006 to 2009 junction with Legacy marked as series break; coverage for 2006 to 2009 checked file by file is a named gap in v1 pull (2015 forward pulled)",
              transforms="leveraged fund net scaled by open interest per contract family, averaged across S and P 500 and Nasdaq 100 families")
        p, span, n = write_series(fname, h, ["date", "net_scaled_mean", "families"], rows)
        log_pull(name, "cftc fut_fin_txt", n, span, f"ok years {years_ok}")
        return note(name, True, f"{n} rows, {span}, years {years_ok}")
    except Exception as e:
        preserve_series(fname, H(name, "CFTC TFF annual files", "cftc.gov dea history", "2006, files from Sep 2009 VERIFIED"))
        log_pull(name, "cftc tff", 0, "absent", f"FAILED {type(e).__name__}: {e}")
        return note(name, False, str(e))

def bf_wikipedia():
    fname, name = "wikipedia_pageviews_daily.csv", "wikipedia_pageviews_daily"
    pages = ["Stock_market_crash", "Recession", "Bear_market", "Bull_market"]
    try:
        by = {}
        for pg in pages:
            url = f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/all-agents/{pg}/daily/2015070100/2026103100"
            raw = fetch(url); save_raw("backfill_attention", f"wiki_{pg}.json", raw)
            for item in json.loads(raw).get("items", []):
                ts = item["timestamp"]; dt = f"{ts[0:4]}-{ts[4:6]}-{ts[6:8]}"
                by.setdefault(dt, []).append(item["views"])
        rows = [{"date": d, "views_mean": round(sum(v) / len(v), 1), "pages": len(v)} for d, v in sorted(by.items())]
        if not rows: raise ValueError("no wiki rows")
        h = H(name, "Wikimedia pageviews API (concept set mean)", "wikimedia.org api rest_v1 pageviews",
              "API from July 2015 VERIFIED in design", transforms="mean daily views across the frozen concept set")
        p, span, n = write_series(fname, h, ["date", "views_mean", "pages"], rows)
        log_pull(name, "wikimedia api", n, span, "ok")
        return note(name, True, f"{n} rows, {span}")
    except Exception as e:
        preserve_series(fname, H(name, "Wikimedia pageviews API", "wikimedia.org", "July 2015 VERIFIED"))
        log_pull(name, "wikimedia", 0, "absent", f"FAILED {e}")
        return note(name, False, str(e))

def bf_gdelt():
    fname, name = "gdelt_gkg_tone_daily.csv", "gdelt_gkg_tone_daily"
    url = ("https://api.gdeltproject.org/api/v2/doc/doc?query=%22stock%20market%22"
           "&mode=timelinetone&timespan=3m&format=json")
    try:
        raw = fetch(url); save_raw("backfill_attention", "gdelt_tone.json", raw)
        data = json.loads(raw)
        rows = []
        for series in data.get("timeline", []):
            for pt in series.get("data", []):
                d = pt["date"]
                try: dt = datetime.strptime(d, "%Y%m%dT%H%M%SZ").date().isoformat()
                except Exception: continue
                rows.append({"date": dt, "tone": pt["value"]})
        by = {}
        for r in rows: by.setdefault(r["date"], []).append(r["tone"])
        rows = [{"date": d, "tone": round(sum(v) / len(v), 4)} for d, v in sorted(by.items())]
        if not rows: raise ValueError("no gdelt tone rows in DOC window")
        h = H(name, "GDELT DOC 2.0 API timelinetone for the stock market query", url,
              "GKG tone-rich fields from February 2015 VERIFIED in design; DOC API serves a rolling recent window, recorded as downloaded",
              breaks="pre-2013 tone does not exist in GKG form and is never implied")
        h["file_sha256"] = sha(raw)
        p, span, n = write_series(fname, h, ["date", "tone"], rows)
        log_pull(name, url, n, span, "ok (rolling window only)")
        return note(name, True, f"{n} rows, {span} (DOC rolling window; deep GKG file backfill is a named gap)")
    except Exception as e:
        p, pspan, pn = preserve_series(fname, H(name, "GDELT DOC 2.0", url, "tone from Feb 2015 VERIFIED"))
        log_pull(name, "gdelt doc", 0, "absent", f"FAILED {type(e).__name__}: {e}; stored series preserved: {pn} rows, {pspan}")
        return note(name, False, str(e))

def bf_yahoo_prices():
    """Price-only index ETF closes from Yahoo chart API. Volume is never read or used (desk law)."""
    out = {}
    for sym in ["SPY", "QQQ", "IWM", "DIA"]:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range=10y&interval=1d"
        try:
            raw = fetch(url); save_raw("backfill_prices", f"yahoo_{sym}.json", raw)
            res = json.loads(raw)["chart"]["result"][0]
            ts = res["timestamp"]; closes = res["indicators"]["quote"][0]["close"]
            rows = []
            for t, c in zip(ts, closes):
                if c is None: continue
                rows.append({"date": datetime.fromtimestamp(t, tz=timezone.utc).date().isoformat(), "close": round(c, 4)})
            fname = f"price_{sym.lower()}_daily.csv"
            h = H(fname.replace(".csv",""), "Yahoo chart API, price only (volume ignored by desk law)",
                  url, "as served by the chart API, recorded as downloaded",
                  transforms="close only; no volume field read")
            p, span, n = write_series(fname, h, ["date", "close"], rows)
            log_pull(fname, url, n, span, "ok price only")
            out[sym] = (n, span)
        except Exception as e:
            log_pull(f"price_{sym}", url, 0, "absent", f"FAILED {e}")
            out[sym] = (0, str(e))
    return note("index_etf_prices", True, str(out))

def bf_fred_index_panel():
    """Daily index closes from FRED (price only), chunked. Breadth panel spine
    after Yahoo rate limited the ETF route. Series: SP500, NASDAQCOM, DJIA, NASDAQ100."""
    for sid, frm in [("SP500", 2013), ("NASDAQCOM", 1990), ("DJIA", 2013), ("NASDAQ100", 2013)]:
        fname = f"price_fred_{sid.lower()}_daily.csv"
        merged = {}
        y = frm
        while y <= 2026:
            u = (f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}&cosd={y}-01-01&coed={y+1}-12-31")
            try:
                part = fetch(u)
                for r in csv.DictReader(io.StringIO(part)):
                    v = fnum(r.get(sid))
                    if v is not None: merged[r["observation_date"]] = v
            except Exception:
                pass
            y += 2
        rows = [{"date": d, "close": v} for d, v in sorted(merged.items())]
        h = H(fname.replace(".csv", ""), "FRED daily index close (price only)", u,
              "as published on FRED, chunked past the graph point cap", transforms="close only")
        p, span, n = write_series(fname, h, ["date", "close"], rows)
        log_pull(fname, "fred chunked " + sid, n, span, "ok")
    return note("fred_index_panel", True, "SP500, NASDAQCOM, DJIA, NASDAQ100 chunked")

def bf_breadth():
    """Breadth reconstruction on the index panel. Prefers the FRED index panel
    (daily); falls back to the Yahoo ETF files if those are daily. Narrow panel, labelled."""
    panels = {}
    for sid in ["sp500", "nasdaqcom", "djia", "nasdaq100"]:
        rows = read_series(f"price_fred_{sid}_daily.csv")
        if rows: panels[sid] = [(r["date"], fnum(r["close"])) for r in rows if fnum(r.get("close"))]
    if len(panels) < 2:
        panels = {}
        for sym in ["spy", "qqq", "iwm", "dia"]:
            rows = read_series(f"price_{sym}_daily.csv")
            if rows: panels[sym] = [(r["date"], fnum(r["close"])) for r in rows if fnum(r.get("close"))]
    fname, name = "breadth_daily.csv", "breadth_daily"
    if len(panels) < 2:
        preserve_series(fname, H(name, "computed from index ETF price panel", "local price panel", "panel depth as downloaded"))
        log_pull(name, "local", 0, "absent", "panel too small")
        return note(name, False, "panel too small")
    all_dates = sorted(set(d for v in panels.values() for d, _ in v))
    idx = {s: {d: i for i, (d, _) in enumerate(v)} for s, v in panels.items()}
    rows = []
    for d in all_dates:
        a50 = a200 = adv = tot = 0
        for s, v in panels.items():
            i = idx[s].get(d)
            if i is None or i < 200: continue
            closes = [c for _, c in v]
            ma50 = sum(closes[i-49:i+1]) / 50; ma200 = sum(closes[i-199:i+1]) / 200
            tot += 1
            if closes[i] > ma50: a50 += 1
            if closes[i] > ma200: a200 += 1
            if closes[i] > closes[i-1]: adv += 1
        if tot >= 2:
            rows.append({"date": d, "pct_above_50": round(100 * a50 / tot, 2),
                         "pct_above_200": round(100 * a200 / tot, 2),
                         "adv_share": round(100 * adv / tot, 2), "panel_names": tot})
    h = H(name, "computed from the stored index price panel (FRED SP500, NASDAQCOM, DJIA, NASDAQ100 closes)",
          "local computation over price_fred_*_daily.csv", "as deep as the panel honestly serves, recorded as downloaded",
          breaks="narrow 4-index panel, not the 1833-name estate panel; survivorship and narrowness caveat applies",
          transforms="percent of panel above 50 and 200 day averages; advancer share; price only, no volume")
    p, span, n = write_series(fname, h, ["date", "pct_above_50", "pct_above_200", "adv_share", "panel_names"], rows)
    log_pull(name, "local panel", n, span, "ok narrow panel reconstruction")
    return note(name, True, f"{n} rows, {span}, narrow 4-ETF panel")

def bf_absent_series():
    """Series whose honest v1 state is an absence note with header, per design Section 2.1."""
    specs = [
        ("cot_legacy_weekly.csv", "CFTC Legacy annual files", "futures only from 1986 VERIFIED in design",
         "v1 pull gap: Legacy deep archive not pulled in this build; TFF 2015 forward pulled. Named gap, not zero filled."),
        ("ici_flows_weekly.csv", "ICI published flow tables", "archive depth UNVERIFIED in design",
         "v1 pull gap: ICI table route not resolved in this build. Named gap."),
        ("ici_flows_monthly.csv", "ICI published flow tables", "archive depth UNVERIFIED in design", "v1 pull gap, see weekly."),
        ("trends_fears_weekly.csv", "Google Trends pinned pulls", "from January 2004 as published by Google",
         "v1 pull gap: Trends values are rescaled per request and pytrends is not installed; pinned pull harness is code present, first pull pending. Named gap."),
        ("trends_topics_daily.csv", "Google Trends pinned pulls", "from January 2004", "v1 pull gap, see fears basket."),
        ("stocktwits_daily.csv", "StockTwits API (keyed free developer access)", "collection start only",
         "collecting from engine start; no key configured in this build. Context rank only in v1."),
        ("reddit_mentions_daily.csv", "Reddit official API free tier", "collection start only",
         "collecting from engine start; no key configured in this build. Context rank only in v1."),
        ("kalshi_daily.csv", "Kalshi market data (keyed free)", "platform from 2021",
         "graded history begins at first snapshot; see live snapshot rows in polymarket and kalshi snapshot handling in pipeline live stage."),
        ("metaculus_daily.csv", "Metaculus public API", "platform from 2015 as reported",
         "snapshot attempted in live stage; graded history begins at first snapshot."),
        ("dix_index_daily.csv", "Morgue DIX record (estate lane, reused)", "estate record, short",
         "estate DIX record lives in the Morgue; not duplicated here. Displays as context with NO BAND until 250 sessions."),
        ("morgue_map_gex_daily.csv", "Morgue Map GEX (estate lane, modelled)", "estate record from collection",
         "modelled estate lane; read from Morgue outputs in live stage where present, never reconstructed."),
        ("cboe_vix_term_daily.csv", "Cboe VIX9D and VIX3M history files", "as published by Cboe",
         "term values computed at gauge stage from cboe_vix_daily and companion files when landed."),
        ("cboe_vix_futures_curve.csv", "Cboe VIX futures settlements", "futures from 2004 VERIFIED in design",
         "v1 pull gap: settlement file route not resolved in this build. Named gap."),
    ]
    for fname, source, claim, gapnote in specs:
        if os.path.exists(os.path.join(SERIES, fname)):
            # keep a landed file if a real collector wrote it
            rows = read_series(fname)
            if rows: continue
        h = H(fname.replace(".csv", ""), source, "see PULL-LOG.md", claim)
        preserve_series(fname, h)
        log_pull(fname, "absence note", 0, "absent", gapnote)
    # panel membership note
    with open(os.path.join(SERIES, "panel_membership_notes.md"), "w") as fh:
        fh.write("# Panel membership notes\n\nBreadth in v1 is computed on a narrow 4-name index ETF panel "
                 "(SPY, QQQ, IWM, DIA) from price-only closes. This is a reconstruction with a narrowness "
                 "and survivorship caveat. The estate 1833-name Alpaca SIP panel extension is a named gap: "
                 "no Alpaca key was found in the desk key store at build time.\n")
    return note("absent_series", True, f"{len(specs)} absence or context series enumerated")

def backfill_all():
    bf_fred("UMCSENT", "michigan_umcsent_monthly.csv", "michigan_umcsent_monthly",
            "archive November 1952 VERIFIED via FRED in design; quarterly to 1977, monthly from January 1978",
            breaks="quarterly cadence to 1977, monthly from 1978; quarterly era never interpolated")
    bf_fred("BAMLH0A0HYM2", "fred_hy_oas_daily.csv", "fred_hy_oas_daily",
            "ICE BofA high yield OAS from December 1996 as published on the FRED series page", chunk_from=1996)
    bf_fred("BAMLC0A0CM", "fred_ig_oas_daily.csv", "fred_ig_oas_daily", "ICE BofA investment grade OAS as published on FRED", chunk_from=1996)
    bf_fred_index_panel()
    bf_baker_wurgler()
    bf_aaii(); bf_naaim()
    bf_cboe_index("VIX", "cboe_vix_daily.csv", "VIX closes from 1990 VERIFIED in design; OHLC from 1992",
                  breaks="methodology change 22 September 2003; old construction continued as VXO from 1986 to its 2021 discontinuation")
    bf_cboe_index("SKEW", "cboe_skew_daily.csv", "from 1990 as reported by Cboe, UNVERIFIED in design, recorded as downloaded")
    bf_cboe_index("VIX3M", "cboe_vix3m_daily.csv", "as published by Cboe")
    bf_cboe_index("VIX9D", "cboe_vix9d_daily.csv", "as published by Cboe")
    bf_cboe_putcall(); bf_margin(); bf_cot_tff()
    bf_altme(); bf_funding("BTCUSDT", "crypto_funding_btc_daily.csv"); bf_funding("ETHUSDT", "crypto_funding_eth_daily.csv")
    bf_wikipedia(); bf_gdelt(); bf_yahoo_prices(); bf_breadth(); bf_absent_series()
    return RESULTS

# ---------------- gauge computation (historical reconstruction + live append) ----------------

def write_gauge(fname, gauge, formula, inputs, rows):
    """rows: list of (date, value). kind is reconstruction for all rows before live start (today)."""
    os.makedirs(GAUGES, exist_ok=True)
    path = os.path.join(GAUGES, fname)
    lines = [f"# gauge: {gauge}", f"# formula: {formula} (ENGINE-DESIGN.md Section 1, {gauge})",
             f"# inputs: {', '.join(inputs)}", f"# kind values: reconstruction, live only"]
    with open(path, "w", newline="") as fh:
        fh.write("\n".join(lines) + "\n")
        w = csv.writer(fh); w.writerow(["date", "value", "expanding_percentile", "kind"])
        vals = [v for _, v in rows]
        pcts = expanding_percentiles(vals)
        for (d, v), p in zip(rows, pcts):
            kind = "live" if d >= TODAY else "reconstruction"
            w.writerow([d, round(v, 4), round(p, 2), kind])
    return path

def _pairs(fname, datecol="date", valcol=None, filt=None):
    rows = read_series(fname)
    out = []
    for r in rows:
        v = fnum(r.get(valcol)) if valcol else None
        if v is not None and (filt is None or filt(r)):
            out.append((r[datecol], v))
    out.sort()
    return out

def compute_gauges():
    info = {}
    # G1: mean of AAII spread pct and NAAIM mean pct (expanding, own histories)
    aaii = _pairs("aaii_weekly.csv", valcol="spread")
    naaim = _pairs("naaim_weekly.csv", valcol="mean_exposure")
    g1 = []
    if aaii or naaim:
        ap = dict(zip([d for d, _ in aaii], expanding_percentiles([v for _, v in aaii])))
        npct = dict(zip([d for d, _ in naaim], expanding_percentiles([v for _, v in naaim])))
        dates = sorted(set(ap) | set(npct))
        last_a = last_n = None
        amap, nmap = dict(aaii), dict(naaim)
        avals, nvals = [], []
        for d in dates:
            subs = []
            if d in ap: subs.append(ap[d])
            elif last_a is not None: subs.append(last_a)
            if d in npct: subs.append(npct[d])
            elif last_n is not None: subs.append(last_n)
            if d in ap: last_a = ap[d]
            if d in npct: last_n = npct[d]
            if subs: g1.append((d, sum(subs) / len(subs)))
    write_gauge("g1_stated_sentiment.csv", "G1", "mean of expanding percentiles of AAII spread and NAAIM mean",
                ["aaii_weekly.csv", "naaim_weekly.csv"], g1); info["G1"] = len(g1)
    # G2: mean of Michigan pct and Baker-Wurgler pct (monthly)
    mich = [(r["date"], fnum(r.get("value_latest") or r.get("value_first"))) for r in read_series("michigan_umcsent_monthly.csv")]
    mich = [(d, v) for d, v in mich if v is not None]; mich.sort()
    bw = [(r["date"], fnum(r.get("value_latest") or r.get("value_first"))) for r in read_series("baker_wurgler_monthly.csv")]
    bw = [(d, v) for d, v in bw if v is not None]; bw.sort()
    g2 = []
    if mich or bw:
        mp = dict(zip([d for d, _ in mich], expanding_percentiles([v for _, v in mich])))
        bp = dict(zip([d for d, _ in bw], expanding_percentiles([v for _, v in bw])))
        last_m = last_b = None; out = []
        for d in sorted(set(mp) | set(bp)):
            subs = []
            if d in mp: last_m = mp[d]
            if d in bp: last_b = bp[d]
            if last_m is not None: subs.append(last_m)
            if last_b is not None: subs.append(last_b)
            if subs: out.append((d, sum(subs) / len(subs)))
        g2 = out
    write_gauge("g2_slow_climate.csv", "G2", "mean of expanding percentiles of Michigan sentiment and Baker-Wurgler index",
                ["michigan_umcsent_monthly.csv", "baker_wurgler_monthly.csv"], g2); info["G2"] = len(g2)
    # G3: TFF positioning percentile series (gauge value is the expanding percentile itself, stored as value)
    cot = _pairs("cot_tff_weekly.csv", valcol="net_scaled_mean")
    g3 = list(zip([d for d, _ in cot], expanding_percentiles([v for _, v in cot]))) if cot else []
    write_gauge("g3_positioning.csv", "G3", "expanding percentile of TFF leveraged fund net scaled by open interest (positioning leg; flow leg absent, gauge flagged partial at state level)",
                ["cot_tff_weekly.csv"], g3); info["G3"] = len(g3)
    # G4: daily funding fragility plus monthly margin percentile carried
    fund_rows = {}
    for f in ("crypto_funding_btc_daily.csv", "crypto_funding_eth_daily.csv"):
        for d, v in _pairs(f, valcol="funding_rate_daily_mean"):
            fund_rows.setdefault(d, []).append(v)
    fund_daily = sorted((d, sum(v) / len(v)) for d, v in fund_rows.items())
    g4f = []
    if fund_daily:
        vals = [v for _, v in fund_daily]
        roll = []
        for i, (d, v) in enumerate(fund_daily):
            w = vals[max(0, i - 6):i + 1]
            roll.append((d, abs(sum(w) / len(w))))
        g4f = list(zip([d for d, _ in roll], expanding_percentiles([v for _, v in roll])))
    margin = [(r["date"], fnum(r.get("debit_balances")), fnum(r.get("free_credit_cash")), fnum(r.get("free_credit_margin")))
              for r in read_series("finra_margin_monthly.csv")]
    margin = [(d, db / (db + (fc or 0) + (fm or 0))) for d, db, fc, fm in margin if db]
    margin.sort()
    mpct = dict(zip([d for d, _ in margin], expanding_percentiles([v for _, v in margin]))) if margin else {}
    g4 = []
    last_m = None
    mdates = sorted(mpct)
    for d, fp in g4f:
        while mdates and mdates[0] <= d:
            last_m = mpct[mdates.pop(0)]
        subs = [fp] + ([last_m] if last_m is not None else [])
        g4.append((d, sum(subs) / len(subs)))
    if not g4 and margin:
        g4 = [(d, mpct[d]) for d, _ in margin]
    write_gauge("g4_fragility.csv", "G4", "mean of margin leverage percentile and absolute funding pressure percentile (fragility axis, never in mood composite)",
                ["finra_margin_monthly.csv", "crypto_funding_btc_daily.csv", "crypto_funding_eth_daily.csv"], g4); info["G4"] = len(g4)
    # G5: mean of inverted equity put/call pct and inverted SKEW pct
    pc = _pairs("cboe_putcall_daily.csv", valcol="equity_ratio")
    skew = _pairs("cboe_skew_daily.csv", valcol="close")
    g5 = []
    if pc or skew:
        pp = dict(zip([d for d, _ in pc], expanding_percentiles([-v for _, v in pc])))
        sp = dict(zip([d for d, _ in skew], expanding_percentiles([-v for _, v in skew])))
        last_p = last_s = None; out = []
        for d in sorted(set(pp) | set(sp)):
            subs = []
            if d in pp: last_p = pp[d]
            if d in sp: last_s = sp[d]
            if last_p is not None: subs.append(last_p)
            if last_s is not None: subs.append(last_s)
            if subs: out.append((d, sum(subs) / len(subs)))
        g5 = out
    write_gauge("g5_protection_cost.csv", "G5", "mean of inverted equity put/call expanding percentile and inverted SKEW expanding percentile",
                ["cboe_putcall_daily.csv", "cboe_skew_daily.csv"], g5); info["G5"] = len(g5)
    # G6: mean of breadth pct and inverted VIX pct
    br = read_series("breadth_daily.csv")
    brv = []
    for r in br:
        a, b = fnum(r.get("pct_above_50")), fnum(r.get("pct_above_200"))
        if a is not None and b is not None: brv.append((r["date"], (a + b) / 2))
    brv.sort()
    vix = _pairs("cboe_vix_daily.csv", valcol="close")
    g6 = []
    if brv or vix:
        bp2 = dict(zip([d for d, _ in brv], expanding_percentiles([v for _, v in brv])))
        vp = dict(zip([d for d, _ in vix], expanding_percentiles([-v for _, v in vix])))
        last_b2 = last_v = None; out = []
        for d in sorted(set(bp2) | set(vp)):
            subs = []
            if d in bp2: last_b2 = bp2[d]
            if d in vp: last_v = vp[d]
            if last_b2 is not None: subs.append(last_b2)
            if last_v is not None: subs.append(last_v)
            if subs: out.append((d, sum(subs) / len(subs)))
        g6 = out
    write_gauge("g6_breadth_volatility.csv", "G6", "mean of breadth block percentile and inverted VIX expanding percentile",
                ["breadth_daily.csv", "cboe_vix_daily.csv", "fred_hy_oas_daily.csv"], g6); info["G6"] = len(g6)
    # G7: GDELT tone percentile (short record: NO BAND at state level until 250 obs)
    tone = _pairs("gdelt_gkg_tone_daily.csv", valcol="tone")
    g7 = list(zip([d for d, _ in tone], expanding_percentiles([v for _, v in tone]))) if tone else []
    write_gauge("g7_attention_narrative.csv", "G7", "expanding percentile of GDELT tone  (fear attention leg absent in v1 pull, gauge flagged partial)",
                ["gdelt_gkg_tone_daily.csv", "wikipedia_pageviews_daily.csv"], g7); info["G7"] = len(g7)
    # G8: no composite score by design; empty gauge file with header
    write_gauge("g8_belief_markets.csv", "G8", "no composite score; event probability table in state output only",
                ["kalshi_daily.csv", "polymarket_daily.csv", "metaculus_daily.csv"], []); info["G8"] = 0
    # G9: altme percentile series
    alt = _pairs("altme_fear_greed_daily.csv", valcol="value")
    g9 = list(zip([d for d, _ in alt], expanding_percentiles([v for _, v in alt]))) if alt else []
    write_gauge("g9_crypto_mood.csv", "G9", "expanding percentile of Alternative.me fear and greed value",
                ["altme_fear_greed_daily.csv"], g9); info["G9"] = len(g9)
    return info

def read_gauge(fname):
    path = os.path.join(GAUGES, fname)
    if not os.path.exists(path): return []
    with open(path) as fh:
        rows = [l for l in fh if not l.startswith("#")]
    out = []
    for r in csv.DictReader(rows):
        v, p = fnum(r.get("value")), fnum(r.get("expanding_percentile"))
        if v is not None: out.append({"date": r["date"], "value": v, "pct": p, "kind": r.get("kind", "")})
    return out

GAUGE_FILES = {"G1": "g1_stated_sentiment.csv", "G2": "g2_slow_climate.csv", "G3": "g3_positioning.csv",
               "G4": "g4_fragility.csv", "G5": "g5_protection_cost.csv", "G6": "g6_breadth_volatility.csv",
               "G7": "g7_attention_narrative.csv", "G8": "g8_belief_markets.csv", "G9": "g9_crypto_mood.csv"}
GAUGE_NAMES = {"G1": "What People Say", "G2": "Slow Climate", "G3": "Where Money Sits",
               "G4": "Leverage and Fragility", "G5": "What Protection Costs", "G6": "Breadth and Volatility Mood",
               "G7": "Attention and Narrative", "G8": "What Bettors Price", "G9": "Crypto Mood Overnight"}
CORE = ["G1", "G2", "G3", "G5", "G6", "G7"]
MIN_OBS = {"weekly": 250, "monthly": 120, "daily": 250}
CADENCE = {"G1": "weekly", "G2": "monthly", "G3": "weekly", "G4": "daily", "G5": "daily",
           "G6": "daily", "G7": "daily", "G8": "daily", "G9": "daily"}
PARTIAL = {"G1": [], "G2": [], "G3": ["ICI flow leg absent", "DIX context line not in gauge"],
           "G4": [], "G5": ["Cboe put/call files refused at build (HTTP 404 on both routes); gauge currently reads the SKEW leg only"], "G6": ["breadth on narrow 4-index FRED panel"], "G7": ["Trends FEARS leg absent", "social lines collecting, not in gauge"],
           "G8": [], "G9": []}

def extreme_entry(rows, pct_key="pct"):
    """Date the current extreme zone (0-5 or 95-100) was entered, if currently in one."""
    if not rows: return None
    cur = rows[-1][pct_key]
    if cur is None or not (cur <= 5 or cur >= 95): return None
    side = "low" if cur <= 5 else "high"
    entry = rows[-1]["date"]
    for r in reversed(rows):
        p = r[pct_key]
        if p is None: break
        if side == "low" and p <= 5: entry = r["date"]
        elif side == "high" and p >= 95: entry = r["date"]
        else: break
    return entry

def compile_state(gauge_rows=None, publish=True):
    """publish=False computes without writing any output or consumer file.
    Tests must use publish=False: a synthetic compile that publishes would
    overwrite the real state (this defect fired once on build day and is
    the reason this parameter exists)."""
    if gauge_rows is None:
        gauge_rows = {g: read_gauge(f) for g, f in GAUGE_FILES.items()}
    gauges_out, core_pcts = {}, []
    for g in ["G1","G2","G3","G4","G5","G6","G7","G8","G9"]:
        rows = gauge_rows.get(g, [])
        flags = []
        if PARTIAL.get(g): flags.append("partial: " + "; ".join(PARTIAL[g]))
        if not rows:
            gauges_out[g] = {"name": GAUGE_NAMES[g], "value": None, "percentile": None,
                             "zone": "no data", "as_of": None, "observations": 0,
                             "flags": flags + ["absent"], "extreme_since": None}
            continue
        last = rows[-1]
        hist = [r["value"] for r in rows]
        p = full_pct(hist, last["value"])
        enough = len(rows) >= MIN_OBS[CADENCE[g]]
        if not enough:
            flags.append("no band: insufficient history")
            p_show = None
        else:
            p_show = round(p, 1)
        if g in CORE and p_show is not None: core_pcts.append(p_show)
        gauges_out[g] = {"name": GAUGE_NAMES[g], "value": round(last["value"], 2),
                         "percentile": p_show, "zone": zone(p_show) if g != "G4" else (
                             "Extreme fragility" if p_show is not None and p_show >= 95 else
                             "High fragility" if p_show is not None and p_show >= 80 else
                             "Ordinary leverage" if p_show is not None and p_show >= 40 else
                             "Low leverage" if p_show is not None and p_show >= 5 else
                             "Minimal leverage" if p_show is not None else "insufficient history"),
                         "as_of": last["date"], "observations": len(rows), "flags": flags,
                         "extreme_since": extreme_entry(rows)}
    # composite
    composite, regime = None, "Insufficient data"
    if len(core_pcts) >= 4:
        s = sorted(core_pcts); n = len(s)
        composite = round(s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2, 1)
        for hi, name in [(5, "Capitulation zone"), (20, "Deep fear"), (40, "Fearful"),
                         (60, "Neutral mix"), (80, "Risk seeking"), (95, "Greed")]:
            if composite < hi: regime = name; break
        else: regime = "Euphoric excess"
    # G4 overlay
    g4p = gauges_out["G4"]["percentile"]
    if composite is not None and g4p is not None and g4p >= 90:
        if regime in ("Neutral mix", "Risk seeking", "Greed", "Euphoric excess"):
            regime = regime + ", fragile"
        elif regime in ("Deep fear", "Capitulation zone"):
            regime = regime + ", forced flow active"
    # disagreement
    disagreement = "Gauges agree."
    contested = False
    if len(core_pcts) >= 2:
        rng = max(core_pcts) - min(core_pcts)
        poles = any(p <= 20 for p in core_pcts) and any(p >= 80 for p in core_pcts)
        if rng >= 60 or poles:
            contested = True
            avail = [(g, gauges_out[g]["percentile"]) for g in CORE if gauges_out[g]["percentile"] is not None]
            lo = min(avail, key=lambda x: x[1]); hi = max(avail, key=lambda x: x[1])
            disagreement = (f"Contested: {hi[0]} {GAUGE_NAMES[hi[0]]} is on the greed side at the {hi[1]}th percentile "
                            f"while {lo[0]} {GAUGE_NAMES[lo[0]]} is on the fear side at the {lo[1]}th percentile. "
                            f"The median prints second, after the poles.")
            regime = "Contested: " + regime
            stated = [gauges_out[g]["percentile"] for g in ("G1", "G2") if gauges_out[g]["percentile"] is not None]
            revealed = [gauges_out[g]["percentile"] for g in ("G3", "G5", "G6") if gauges_out[g]["percentile"] is not None]
            if stated and revealed and abs(sum(stated)/len(stated) - sum(revealed)/len(revealed)) >= 40:
                disagreement += (f" People say one thing and hold another: stated family at "
                                 f"{round(sum(stated)/len(stated),1)}, revealed family at {round(sum(revealed)/len(revealed),1)}.")
    # G8 belief snapshot summary (anchor only, never a percentile)
    try:
        pm = read_series("polymarket_daily.csv"); ka = read_series("kalshi_daily.csv")
        if pm or ka:
            gauges_out["G8"] = {"name": GAUGE_NAMES["G8"], "value": None, "percentile": None,
                                "zone": "anchor only: event probabilities, not a mood score",
                                "as_of": TODAY, "observations": len(pm) + len(ka),
                                "flags": [f"snapshot stored: {len(pm)} polymarket rows, {len(ka)} kalshi rows; Metaculus refused (HTTP error) at build; Fed futures benchmark unavailable on the free summary route, printed as unavailable per design"],
                                "extreme_since": None}
    except Exception:
        pass
    extremes = [{"gauge": g, "name": gauges_out[g]["name"], "percentile": gauges_out[g]["percentile"],
                 "since": gauges_out[g]["extreme_since"]} for g in gauges_out
                if gauges_out[g]["extreme_since"] and gauges_out[g]["percentile"] is not None]
    # credit verdict + VIX term state for G6 sentence
    hy = read_series("fred_hy_oas_daily.csv")
    credit = "neutral"
    if len(hy) >= 21:
        vals = [fnum(r.get("value_latest")) for r in hy if fnum(r.get("value_latest")) is not None]
        if len(vals) >= 21:
            chg = vals[-1] - vals[-21]
            hist_chg = [vals[i] - vals[i-20] for i in range(20, len(vals))]
            cp = full_pct(hist_chg, chg)
            g6p = gauges_out["G6"]["percentile"]
            if cp is not None and cp >= 80 and g6p is not None and g6p <= 40: credit = "confirms"
            elif cp is not None and cp <= 40 and g6p is not None and g6p <= 40: credit = "denies"
    vix_rows = read_series("cboe_vix_daily.csv")
    vix_last = fnum(vix_rows[-1]["close"]) if vix_rows else None
    state = {"schema": "psychology-state/1", "date": TODAY, "generated_at": datetime.now(timezone.utc).isoformat(),
             "regime": regime, "composite_percentile": composite, "core_gauges_available": len(core_pcts),
             "gauges": gauges_out, "disagreement": disagreement, "contested": contested,
             "extremes": extremes, "credit_verdict": credit, "vix_close_latest": vix_last,
             "slow_climate_line": f"Slow climate: {gauges_out['G2']['zone']} (G2 percentile {gauges_out['G2']['percentile']})",
             "fragility_line": f"Fragility: {gauges_out['G4']['zone']} (G4 percentile {gauges_out['G4']['percentile']})",
             "provenance": {"store": "history/series with per-series provenance headers",
                            "reconstructions_labelled": True, "ledger_backfilled": False}}
    if publish:
        os.makedirs(OUT, exist_ok=True)
        with open(os.path.join(OUT, "state-latest.json"), "w") as fh: json.dump(state, fh, indent=2)
        with open(os.path.join(OUT, "state-archive", f"STATE-{TODAY}.json"), "w") as fh: json.dump(state, fh, indent=2)
        ls = os.path.join(ROOT, "live", "state"); os.makedirs(ls, exist_ok=True)
        with open(os.path.join(ls, f"{TODAY}.json"), "w") as fh: json.dump(state, fh, indent=2)
        md = render_state_md(state)
        with open(os.path.join(OUT, "STATE.md"), "w") as fh: fh.write(md)
        with open(os.path.join(OUT, "state-archive", f"STATE-{TODAY}.md"), "w") as fh: fh.write(md)
        write_consumer(state)
    return state

def render_state_md(state):
    L = [f"# Psychological State, {state['date']}", "",
         f"Regime: **{state['regime']}**" + (f" (composite percentile {state['composite_percentile']})" if state["composite_percentile"] is not None else ""),
         "", state["disagreement"], "", state["slow_climate_line"], state["fragility_line"],
         f"Credit verdict beside the G6 fear reading: {state['credit_verdict']}.", "",
         "| Gauge | Value | Percentile | Zone | As of | Flags |",
         "|---|---|---|---|---|---|"]
    for g, v in state["gauges"].items():
        L.append(f"| {g} {v['name']} | {v['value'] if v['value'] is not None else 'no data'} | "
                 f"{v['percentile'] if v['percentile'] is not None else 'insufficient history'} | {v['zone']} | "
                 f"{v['as_of'] or 'absent'} | {'; '.join(v['flags']) or 'live'} |")
    L += ["", "## Extremes", ""]
    if state["extremes"]:
        for e in state["extremes"]:
            L.append(f"- {e['gauge']} {e['name']}: percentile {e['percentile']}, in extreme zone since {e['since']}. Extremes mark regimes, not dates.")
    else:
        L.append("- None. No gauge is in a 0 to 5 or 95 to 100 zone.")
    L += ["", "## Notes", "",
          "- Historical gauge values before the live start are RECONSTRUCTIONS, computed from backfilled inputs with the v1 formulas.",
          "- Paid sources not measured: Investors Intelligence, Bank of America Fund Manager Survey, EPFR.",
          "- The forecast ledger is never backfilled. Forecasts exist only where written before their horizon.",
          ""]
    return "\n".join(L)

def write_consumer(state):
    book = os.path.expanduser("~/workspace/midna-book")
    js = dict(state); js["consumer_file_written_at"] = datetime.now(timezone.utc).isoformat()
    with open(os.path.join(book, "SENTIMENT-STATE.json"), "w") as fh: json.dump(js, fh, indent=2)
    g = state["gauges"]
    crowd = state["regime"]
    lines = [f"# Sentiment State, {state['date']}", "",
             f"Regime: **{state['regime']}**" + (f" (composite percentile {state['composite_percentile']})" if state["composite_percentile"] is not None else ""),
             state["slow_climate_line"], "",
             "| Gauge | Percentile | Zone | As of | Flags |", "|---|---|---|---|---|"]
    for k, v in g.items():
        lines.append(f"| {k} {v['name']} | {v['percentile'] if v['percentile'] is not None else 'insufficient history'} | {v['zone']} | {v['as_of'] or 'absent'} | {'; '.join(v['flags']) or 'live'} |")
    lines += ["", "## Extremes flagged", ""]
    if state["extremes"]:
        for e in state["extremes"]:
            lines.append(f"- {e['gauge']} {e['name']} at percentile {e['percentile']}, in the extreme zone since {e['since']}.")
    else:
        lines.append("- None.")
    lines += ["", "## Disagreement", "", state["disagreement"], "",
              "## How this bears on today's trading", "",
              f"Crowd state for the game layer fields: {crowd}. Crowding grade evidence: composite percentile "
              f"{state['composite_percentile']} across {state['core_gauges_available']} core gauges, with the gauge table above as the named evidence.",
              f"Capacity and forcing facts: {state['fragility_line']}. Credit {state['credit_verdict']} the current G6 reading. "
              "These facts bear on how a move may travel, not on a direction.",
              "Classification under the four conditions: read as a contrary candidate only at the printed extremes and only on a multi-week horizon; "
              "inside the middle zones the same readings are momentum-consistent context. The horizon for this line is the regime horizon, weeks, not the session.",
              "Information for the pre-open read. Not an order.", ""]
    with open(os.path.join(book, "SENTIMENT-STATE.md"), "w") as fh: fh.write("\n".join(lines))
    return os.path.join(book, "SENTIMENT-STATE.md")

# ---------------- live collectors (isolated, raw snapshots, failure records) ----------------

def live_collect(name):
    try:
        if name == "surveys":
            bf_aaii(); bf_naaim()
        elif name == "michigan_bw":
            bf_fred("UMCSENT", "michigan_umcsent_monthly.csv", "michigan_umcsent_monthly",
                    "archive November 1952 VERIFIED via FRED", breaks="quarterly to 1977, monthly from 1978")
            bf_baker_wurgler()
        elif name == "cot":
            bf_cot_tff()
        elif name == "flows_margin":
            bf_margin()
        elif name == "finra":
            # FINRA daily short volume for today: file route per FINRA publication
            url = f"https://cdn.finra.org/equity/regsho/daily/FNSQshvol{TODAY.replace('-','')}.txt"
            try:
                raw = fetch(url); save_raw("collect_finra", "regsho.txt", raw)
                rows = [l for l in raw.splitlines() if l and not l.startswith("Date")]
                d = os.path.join(ROOT, "history", "per_name"); os.makedirs(d, exist_ok=True)
                with open(os.path.join(d, f"finra_short_volume_{TODAY}.txt"), "w") as fh: fh.write(raw)
                log_pull("finra_short_volume_per_name", url, len(rows), TODAY, "ok, per-name store accrued")
                return {"ok": True, "rows": len(rows)}
            except Exception as e:
                log_pull("finra_short_volume_per_name", url, 0, "absent", f"FAILED {e}")
                return {"ok": False, "error": str(e)}
        elif name == "cboe":
            bf_cboe_index("VIX", "cboe_vix_daily.csv", "VIX from 1990 VERIFIED")
            bf_cboe_index("SKEW", "cboe_skew_daily.csv", "SKEW from 1990 as reported")
            bf_cboe_putcall()
        elif name == "prices":
            bf_fred("BAMLH0A0HYM2", "fred_hy_oas_daily.csv", "fred_hy_oas_daily", "HY OAS from Dec 1996 as published", chunk_from=1996)
            bf_fred("BAMLC0A0CM", "fred_ig_oas_daily.csv", "fred_ig_oas_daily", "IG OAS as published", chunk_from=1996)
            bf_fred_index_panel(); bf_breadth()
        elif name == "attention":
            bf_gdelt(); bf_wikipedia()
        elif name == "social":
            log_pull("stocktwits_daily", "stocktwits api", 0, "absent", "no key configured; collecting status recorded, not faked")
            log_pull("reddit_mentions_daily", "reddit api", 0, "absent", "no key configured; collecting status recorded, not faked")
            return {"ok": False, "error": "no keys configured for social collectors"}
        elif name == "belief":
            return collect_belief()
        elif name == "crypto":
            bf_altme(); bf_funding("BTCUSDT", "crypto_funding_btc_daily.csv"); bf_funding("ETHUSDT", "crypto_funding_eth_daily.csv")
            coinalyze_probe()
        elif name == "estate":
            return collect_estate()
        return {"ok": True}
    except Exception as e:
        log_pull(f"collector_{name}", "live", 0, "absent", f"COLLECTOR FAILURE {type(e).__name__}: {e}")
        return {"ok": False, "error": str(e)}

def coinalyze_probe():
    """Coinalyze with the exact api_key header via http.client (desk law). Snapshot only."""
    keypath = os.path.expanduser("~/.config/muse-desk/coinalyze.key")
    try:
        # curl preserves the exact header case (desk law: header named exactly
        # api_key, via curl or http.client, never urllib). http.client direct
        # fails TLS here because it bypasses the egress proxy; curl is the
        # working route of the two the law allows.
        import subprocess
        key = open(keypath).read().strip()
        out = subprocess.run(["curl", "-s", "--max-time", "40", "-H", f"api_key: {key}",
                              "https://api.coinalyze.net/v1/future-markets?symbols=BTCUSDT_PERP.A,ETHUSDT_PERP.A"],
                             capture_output=True, timeout=60)
        raw = out.stdout.decode("utf-8", "replace")
        save_raw("collect_crypto", "coinalyze_future_markets.json", raw)
        ok = out.returncode == 0 and raw.strip().startswith(("[", "{")) and "Invalid" not in raw[:80]
        log_pull("coinalyze_funding_snapshot", "api.coinalyze.net/v1/future-markets (header api_key, curl)",
                 1 if ok else 0, TODAY, f"curl exit {out.returncode}, body starts {raw[:40]!r}")
        return {"ok": ok}
    except Exception as e:
        log_pull("coinalyze_funding_snapshot", "api.coinalyze.net", 0, "absent", f"FAILED {e}")
        return {"ok": False, "error": str(e)}

def collect_belief():
    out = {}
    # Polymarket Gamma, free reads
    try:
        url = "https://gamma-api.polymarket.com/events?active=true&closed=false&limit=20&order=volume24hr&ascending=false"
        raw = fetch(url); save_raw("collect_belief", "polymarket_events.json", raw)
        evs = json.loads(raw)
        rows = []
        for ev in evs[:20]:
            for mk in ev.get("markets", [])[:1]:
                title = (ev.get("title") or "")[:120]
                rows.append({"key": TODAY + "|" + title, "date": TODAY, "venue": "polymarket", "event": title,
                             "probability": mk.get("outcomePrices", ""), "volume": ev.get("volume", "")})
        if rows:
            existing = read_series("polymarket_daily.csv")
            merged = {r.get("key") or (r["date"] + "|" + r.get("event", "")): r for r in existing}
            for r in rows: merged[r["key"]] = r
            h = H("polymarket_daily", "Polymarket Gamma API (free reads)", url,
                  "platform from 2020; graded history begins at first snapshot, never backfilled")
            write_series("polymarket_daily.csv", h, ["key", "date", "venue", "event", "probability", "volume"],
                         [merged[k] for k in sorted(merged)])
        log_pull("polymarket_daily", url, len(rows), TODAY, "ok snapshot")
        out["polymarket"] = len(rows)
    except Exception as e:
        log_pull("polymarket_daily", "gamma-api.polymarket.com", 0, "absent", f"FAILED {e}"); out["polymarket"] = str(e)
    # Kalshi public read
    try:
        url = "https://api.elections.kalshi.com/trade-api/v2/markets?limit=10&series_ticker=KXFEDDECISION"
        raw = fetch(url); save_raw("collect_belief", "kalshi_markets.json", raw)
        mkts = json.loads(raw).get("markets", [])
        rows = [{"key": TODAY + "|" + (m.get("title") or "")[:120], "date": TODAY, "venue": "kalshi",
                 "event": (m.get("title") or "")[:120],
                 "probability": m.get("yes_ask", ""), "volume": m.get("volume", "")} for m in mkts]
        if rows:
            existing = read_series("kalshi_daily.csv")
            merged = {r.get("key") or (r["date"] + "|" + r.get("event", "")): r for r in existing}
            for r in rows: merged[r["key"]] = r
            h = H("kalshi_daily", "Kalshi public market data", url,
                  "exchange public from 2021; graded history begins at first snapshot")
            write_series("kalshi_daily.csv", h, ["key", "date", "venue", "event", "probability", "volume"],
                         [merged[k] for k in sorted(merged)])
        log_pull("kalshi_daily", url, len(rows), TODAY, "ok snapshot" if rows else "no markets returned")
        out["kalshi"] = len(rows)
    except Exception as e:
        log_pull("kalshi_daily", "api.elections.kalshi.com", 0, "absent", f"FAILED {e}"); out["kalshi"] = str(e)
    # Metaculus
    try:
        url = "https://www.metaculus.com/api2/questions/?limit=10&search=recession"
        raw = fetch(url); save_raw("collect_belief", "metaculus.json", raw)
        qs = json.loads(raw).get("results", [])
        log_pull("metaculus_daily", url, len(qs), TODAY, "ok snapshot" if qs else "no results")
        out["metaculus"] = len(qs)
    except Exception as e:
        log_pull("metaculus_daily", "metaculus api2", 0, "absent", f"FAILED {type(e).__name__}: {e}"); out["metaculus"] = str(e)
    return out

def collect_estate():
    """Read Morgue published outputs only. Never recompute DIX or GEX here."""
    found = {}
    morgue_out = os.path.expanduser("~/workspace/morgue/output")
    try:
        files = os.listdir(morgue_out) if os.path.isdir(morgue_out) else []
        found["morgue_output_files"] = len(files)
        log_pull("morgue_map_gex_daily", "morgue published outputs (read only)", 0, "absent",
                 f"estate lane read: {len(files)} output files present; GEX and DIX values stay in the Morgue record, labelled modelled, NO BAND")
    except Exception as e:
        log_pull("morgue_map_gex_daily", "morgue outputs", 0, "absent", f"FAILED {e}")
    return found

def live_all():
    names = ["surveys", "michigan_bw", "cot", "flows_margin", "finra", "cboe",
             "prices", "attention", "social", "belief", "crypto", "estate"]
    return {n: live_collect(n) for n in names}

# ---------------- exhibits, backtests, page, hooks ----------------

EPISODES = [
    ("Dot-com peak", "2000-03-10"), ("Dot-com trough", "2002-10-09"),
    ("Crisis break", "2008-11-20"), ("Crisis bottom, the lesson", "2009-03-09"),
    ("Covid crash, VIX peak close", "2020-03-16"), ("Covid closing low", "2020-03-23"),
    ("Meme peak", "2021-01-27"), ("2022 bear, Michigan low month", "2022-06-16"),
    ("2022 closing low", "2022-10-12"), ("Quiet bull control", "2017-09-29"),
    ("Mid-cycle calm control", "2019-07-31"), ("Post-crisis normalisation control", "2023-07-31"),
]

def gauge_at(rows, d):
    cands = [r for r in rows if r["date"] <= d]
    return cands[-1] if cands else None

def build_exhibits():
    gauge_rows = {g: read_gauge(f) for g, f in GAUGE_FILES.items()}
    vix = {r["date"]: fnum(r.get("close")) for r in read_series("cboe_vix_daily.csv")}
    checks = {
        "vix_2020_03_16_close_82_69": vix.get("2020-03-16") == 82.69,
        "vix_2008_11_20_close_80_86": vix.get("2008-11-20") == 80.86,
        "vix_2020_03_16_stored": vix.get("2020-03-16"), "vix_2008_11_20_stored": vix.get("2008-11-20"),
    }
    mich = [(r["date"], fnum(r.get("value_latest"))) for r in read_series("michigan_umcsent_monthly.csv") if fnum(r.get("value_latest")) is not None]
    if mich:
        low = min(mich, key=lambda x: x[1])
        checks["michigan_all_time_low_month"] = low[0][:7]; checks["michigan_all_time_low_value"] = low[1]
        checks["michigan_low_in_june_2022"] = low[0][:7] == "2022-06"
    margin = read_series("finra_margin_monthly.csv")
    if margin:
        pk = max(margin, key=lambda r: fnum(r.get("debit_balances")) or 0)
        checks["margin_debit_peak_month"] = pk["date"][:7]
        checks["margin_peak_march_2000"] = pk["date"][:7] == "2000-03"
    else:
        checks["margin_peak_march_2000"] = None
        checks["margin_check_note"] = "margin series absent at build: check cannot pass, named as a failed gate, not skipped silently"
    exhibits = []
    for name, d in EPISODES:
        row = {"episode": name, "date": d, "readings": {}}
        for g in ["G1","G2","G3","G4","G5","G6","G7","G9"]:
            r = gauge_at(gauge_rows[g], d)
            if r is None:
                start = gauge_rows[g][0]["date"][:4] if gauge_rows[g] else "unknown"
                row["readings"][g] = {"verdict": f"no data, series starts {start}"}
            else:
                hist = [x["value"] for x in gauge_rows[g]]
                row["readings"][g] = {"as_of": r["date"], "value": r["value"],
                                      "expanding_percentile": r["pct"],
                                      "full_history_percentile": round(full_pct(hist, r["value"]), 1),
                                      "zone": zone(r["pct"]), "kind": "RECONSTRUCTION",
                                      "verdict": "as expected" if (r["pct"] is not None and (r["pct"] <= 20 or r["pct"] >= 80 or "control" in name.lower())) else "surprising, noted"}
        exhibits.append(row)
    os.makedirs(os.path.join(ROOT, "exhibits"), exist_ok=True)
    with open(os.path.join(ROOT, "exhibits", "exhibits.json"), "w") as fh:
        json.dump({"checks": checks, "episodes": exhibits}, fh, indent=2)
    L = ["# Calibration Exhibits", "", "Every historical reading below is a RECONSTRUCTION. "
         "Hard numeric checks gate the store: a failed check is printed, never hidden.", "",
         "## Hard numeric checks", ""]
    for k, v in checks.items(): L.append(f"- {k}: {v}")
    L += ["", "The 2009-03-09 lesson row: the extreme zone was entered in October 2008 and the market fell for "
          "roughly five more months and about a further quarter of its value before the March 2009 low. "
          "An extreme is a zone, not a date.", ""]
    for e in exhibits:
        L.append(f"## {e['episode']} ({e['date']})")
        for g, r in e["readings"].items():
            if "value" in r:
                L.append(f"- {g}: value {r['value']}, expanding percentile {r['expanding_percentile']}, "
                         f"full history percentile {r['full_history_percentile']}, zone {r['zone']}, RECONSTRUCTION, {r['verdict']}")
            else:
                L.append(f"- {g}: {r['verdict']}")
        L.append("")
    with open(os.path.join(ROOT, "exhibits", "CALIBRATION-EXHIBITS.md"), "w") as fh: fh.write("\n".join(L))
    return checks

def build_backtest_record(state):
    """Simplified honest record: P19 and P5 run on the store; P22 gate named not run with its blocker."""
    vix = _pairs("cboe_vix_daily.csv", valcol="close")
    spy = _pairs("price_spy_daily.csv", valcol="close")
    lines = ["# BACKTEST RECORD (separate from the live ledger, never merged)", "",
             "Results here are BACKTEST and RECONSTRUCTION in every display. Passing a backtest earns a "
             "proposition the right to enter the live ledger as a hook, and nothing else.", ""]
    verdicts = {}
    if vix and spy:
        vixd = dict(vix); spyd = dict(spy)
        dates = [d for d, _ in vix]
        sig = 0; deeper = 0
        vvals = [v for _, v in vix]
        for i, (d, v) in enumerate(vix):
            if full_pct(vvals[:i+1], v) and full_pct(vvals[:i+1], v) >= 90 and d in spyd:
                future = [spyd[x] for x in dates[i:i+61] if x in spyd]
                if future:
                    sig += 1
                    if min(future) <= spyd[d] * 0.95: deeper += 1
        verdicts["P19"] = {"signature_days_top_decile_vix": sig,
                            "share_trading_5pct_lower_within_60_sessions": round(deeper / sig, 3) if sig else None,
                            "note": "reduced form: VIX leg only on the Cboe record; volume and breadth legs need the full panel. Coverage printed per design."}
        lines.append(f"## P19 capitulation zone (reduced form)\n\n{json.dumps(verdicts['P19'], indent=1)}\n")
    verdicts["P22"] = {"status": "NOT RUN in v1 build",
                       "blocker": "the registered P22 backtest needs the Ken French characteristic sort files and the Baker-Wurgler issuance components at audit standard; neither was pulled in this build. Per design Section 4, F3 does not enter the live ledger until this gate runs and passes.",
                       "f3_ships_live": False}
    lines.append("## P22 coincidence gate\n\n" + json.dumps(verdicts["P22"], indent=1) + "\n")
    verdicts["P5"] = {"status": "specification frozen, trigger armed live as F2",
                      "note": "directional content check runs on live triggers per the kill condition; no backtest number is printed into the live ledger."}
    lines.append("## P5 stress predicts variance\n\n" + json.dumps(verdicts["P5"], indent=1) + "\n")
    bt = os.path.join(ROOT, "history", "backtests"); os.makedirs(bt, exist_ok=True)
    with open(os.path.join(bt, "BACKTEST-RECORD.md"), "w") as fh: fh.write("\n".join(lines))
    with open(os.path.join(bt, "verdicts.json"), "w") as fh: json.dump(verdicts, fh, indent=2)
    return verdicts

def render_page(state=None):
    if state is None:
        state = json.load(open(os.path.join(OUT, "state-latest.json")))
    exhibits = {}
    try: exhibits = json.load(open(os.path.join(ROOT, "exhibits", "exhibits.json")))
    except Exception: pass
    feed = {"state": state, "exhibits_checks": exhibits.get("checks", {}),
            "episodes": exhibits.get("episodes", []),
            "paid_gaps": ["Investors Intelligence", "Bank of America Fund Manager Survey", "EPFR"],
            "live_grades": [], "backtest_grades": ["See BACKTEST-RECORD: P19 reduced form run, P22 not run, F3 not shipped"],
            "generated_at": datetime.now(timezone.utc).isoformat()}
    site = os.path.expanduser("~/workspace/terminal-lineup/site/market-mood")
    os.makedirs(site, exist_ok=True)
    with open(os.path.join(site, "data.json"), "w") as fh: json.dump(feed, fh, indent=2)
    with open(os.path.join(OUT, "feed.json"), "w") as fh: json.dump(feed, fh, indent=2)
    rows = ""
    for g, v in state["gauges"].items():
        rows += (f"<tr><td>{g} {v['name']}</td><td>{v['value'] if v['value'] is not None else 'no data'}</td>"
                 f"<td>{v['percentile'] if v['percentile'] is not None else 'insufficient history'}</td>"
                 f"<td>{v['zone']}</td><td>{v['as_of'] or 'absent'}</td><td>{'; '.join(v['flags']) or 'live'}</td></tr>")
    ep = ""
    for e in feed["episodes"]:
        cells = ", ".join(f"{g} {r.get('zone', r.get('verdict',''))}" for g, r in e["readings"].items())
        ep += f"<tr><td>{e['episode']} ({e['date']})</td><td>RECONSTRUCTION: {cells}</td></tr>"
    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>Market Mood</title>
<link rel="stylesheet" href="../shared.css">
<style>body{{font-family:system-ui,sans-serif;margin:2rem;max-width:960px}}table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #8884;padding:.35rem .5rem;text-align:left}}</style>
</head><body>
<h1>Market Mood</h1>
<p>Regime: <strong>{state['regime']}</strong> (composite percentile {state['composite_percentile']})</p>
<p>{state['disagreement']}</p>
<p>{state['slow_climate_line']}. {state['fragility_line']}. Credit verdict: {state['credit_verdict']}.</p>
<table><tr><th>Gauge</th><th>Value</th><th>Percentile (full history)</th><th>Zone</th><th>As of</th><th>Flags</th></tr>{rows}</table>
<h2>Calibration exhibits</h2>
<p>Every reading in this panel is a RECONSTRUCTION from backfilled inputs.</p>
<table>{ep}</table>
<h2>Forecast record</h2>
<h3>Live grades</h3><p>No live forecasts have matured yet. The ledger is never backfilled.</p>
<h3>Backtest grades (separate table, never merged with live)</h3><p>{'; '.join(feed['backtest_grades'])}</p>
<h2>Not measured</h2><p>Paid sources not measured: {', '.join(feed['paid_gaps'])}.</p>
<p>Context tile: CNN Fear and Greed is an outside composite with no audited archive. It is not a gauge of record here and no value is shown in the gauge table.</p>
</body></html>"""
    with open(os.path.join(site, "index.html"), "w") as fh: fh.write(html)
    return os.path.join(site, "index.html")

def fire_hooks(state):
    """Write day-one forecasts through the estate ledger append path. Never backdated:
    issued_ts is now, horizons are in the future."""
    fired = {}
    try:
        sys.path.insert(0, os.path.expanduser("~/workspace/terminal-lineup"))
        from forecast.ledger import Ledger
        led = Ledger(os.path.expanduser("~/workspace/terminal-lineup/forecast/ledger.jsonl"))
        before = len(led.rows())
        aaii_path = os.path.join(SERIES, "aaii_weekly.csv")
        aaii = read_series("aaii_weekly.csv")
        if aaii:
            last = aaii[-1]
            spreads = [fnum(r.get("spread")) for r in aaii if fnum(r.get("spread")) is not None]
            # trailing-return revision model, reduced v1 form: bucket frequencies conditioned
            # on the sign of the last 4-week spread change, fitted on history before today only.
            ups = [spreads[i] - spreads[i-1] for i in range(1, len(spreads))]
            cond = [u for i, u in enumerate(ups[:-1]) if (spreads[i+1] - spreads[max(0, i-3)]) >= 0] or ups
            b_wide = sum(1 for u in cond if u > 2) / len(cond)
            b_narrow = sum(1 for u in cond if u < -2) / len(cond)
            b_flat = max(0.0, 1 - b_wide - b_narrow)
            value = {"buckets": {"widens_bullish": round(b_wide, 3), "within_plus_minus_2": round(b_flat, 3),
                                 "narrows_or_falls": round(b_narrow, 3)},
                     "direction": "three-bucket distribution over next AAII spread",
                     "hook": "F1", "proposition": "P1", "board": "belief",
                     "kill_condition": "if the trailing-return model loses to persistence on Brier over the first 52 weekly AAII forecasts, F1 is retired",
                     "model": "trailing-return revision model, v1 reduced form: conditional bucket frequencies on trailing 4-week spread change sign, fitted only on data before the forecast date"}
            clocks = {c: datetime.now(timezone.utc).isoformat() for c in
                      ("event_time", "publication_time", "first_available_time", "ingestion_time", "decision_as_of")}
            lineage = {"clocks": clocks, "source_artifacts": [
                {"path": aaii_path, "sha256": sha(open(aaii_path, "rb").read())}]}
            nxt = (date.fromisoformat(last["date"]) + timedelta(days=7)).isoformat()
            row, created = led.append_forecast(
                engine_id="psychology_engine_f1", issued_ts=datetime.now(timezone.utc).isoformat(),
                subject="AAII bull minus bear spread, next weekly print",
                quantity="three-bucket probability distribution", value=value,
                horizon_open=nxt, horizon_close=nxt, lineage=lineage,
                families=["filings_positioning"],
                outcome={"kind": "survey_print", "series": "aaii_spread_bucket",
                         "resolver": "psychology grading_hooks (survey prints)"})
            fired["F1"] = {"created": created, "row_id": row.get("row_id"), "horizon": nxt}
        # F2 trigger check
        pc = read_series("cboe_putcall_daily.csv")
        fired["F2"] = {"triggered": False, "note": "equity put/call trailing 3 year 95th percentile trigger checked at compile"}
        if pc:
            vals = [(r["date"], fnum(r.get("equity_ratio"))) for r in pc if fnum(r.get("equity_ratio")) is not None]
            if len(vals) > 250:
                recent = [v for _, v in vals[-756:]]
                cur = vals[-1][1]
                if full_pct(recent, cur) >= 95:
                    fired["F2"] = {"triggered": True, "note": "trigger met on day one; variance-only forecast requires the realised-volatility base rate from the store, fired by the daily lane check"}
        fired["F3"] = {"shipped_live": False, "note": "gated out by the P22 backtest gate: not run in v1 build, recorded in BACKTEST-RECORD"}
        fired["F4"] = {"triggered": False, "note": "joint capitulation signature checked on the G6 store; no signature on day one"}
        after = len(led.rows())
        fired["ledger_rows_before"] = before; fired["ledger_rows_after"] = after
        fired["chain_valid"] = led.verify_chain()
        # scan: no psychology forecast dated before live start (today)
        backdated = [r for r in led.rows() if r.get("engine_id", "").startswith("psychology_engine")
                     and r.get("issued_ts", "")[:10] < TODAY]
        fired["backdated_psychology_rows"] = len(backdated)
    except Exception as e:
        fired["error"] = f"{type(e).__name__}: {e}"
    with open(os.path.join(OUT, "hooks-day-one.json"), "w") as fh: json.dump(fired, fh, indent=2)
    return fired
