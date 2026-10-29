"""Author_altdata_run: one per-source alt-data run (the jobs of Author_altdata.py), run as a script by the research venv, which has
the vendored producers' libraries (pandas, pyarrow). The network part is this file's; every feature is still computed by the
vendored research code (WIKI_LIVE/features.py, ALTDATA_LIVE/plugins/finra_flow.py and form4_insider.py,
DESK_INTEGRATION/w_swing_live/w_swing_feed.py), unchanged, on the materialized research root.

usage: python Author_altdata_run.py {wiki|finra|sec|wswing|options} --research <root>/inputs/lazarus --scratch <root>/cache/Author/scratch
                                    --state <root>/cache/Author/altdata --now EPOCH --deadline EPOCH
The User-Agent arrives in ALTDATA_USER_AGENT (Author_altdata.switches, already through the personal-email guard). The last
stdout line is the run's JSON summary. Exit 0 ok, 3 refused (403 / 429 / 503 or a challenge page, or a proxy refusal), 4 cut
(the deadline came first, or too few titles came back), 1 error.

The client (Polite): one request at a time, at most one a second per host across processes (an flock'd stamp per host under
<state>/pace), the honest User-Agent and nothing else that identifies a person, gzip. A 404 is "absent". A 403, 429 or 503
stops the source for this run (with the host's Retry-After), and so does a page that is not the data asked for (a challenge or
login page). A proxy that refuses the tunnel (403 / 407) is never retried. Another 5xx or a transport error is retried once,
five seconds later.

wiki (Wikimedia page views; the vendored WIKI_LIVE/collector.py's request, window and store, at 1/s instead of 4/s):
  * one request per mapped title (hd_newdata wiki_map.csv) for days [newest stored day - 7, yesterday UTC], as the collector;
  * incremental: <state>/wiki_progress.json lists the titles already fetched for this window's last day, so a run that was
    cut or refused resumes where it stopped, and a run for a day already complete sends nothing;
  * the store data/wiki_pv_live.parquet takes each 100 titles' rows at once (dedup on (sym, date), the latest fetch wins);
  * once the window's titles are in (failed <= max(10, 5%): the collector's own rule), the vendored features.py runs and the
    heartbeat WIKI_LIVE/jobs/heartbeat.json says ok with daily.sh's fields; otherwise the features stay as they were and the
    heartbeat says fail with why (its last_success_et and asof stay: the sleeve feed's freshness rule then fails closed).
wswing: the vendored w_swing_feed `run`, offline: WSW_NO_NET=1 (no Yahoo), SC_NO_NET=1 (the SEC shares snapshot), and the split
  events it would ask Yahoo for read from the tracker's own cached Yahoo 1d payloads (<scratch>/shadow/work/data/1d/<SYM>.json,
  fetched with events=div,splits): the same events, no request. A symbol without a payload has no split source (band unknown:
  its cells fail closed, the feed's own rule).
sec, finra: the vendored plug-ins' fetch replaced by Polite (sec: form4_insider's Fetcher; finra: the CNMS daily files and the
  ATS weeks), then their own build. Both stay off in config/altdata.json (SOURCES.md)."""
import argparse
import datetime as dt
import fcntl
import gzip
import json
import os
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

TZ = "America/New_York"
ACCEPT = {"json": "application/json", "text": "text/plain,*/*;q=0.5", "any": "*/*"}
EXIT_REFUSED, EXIT_CUT = 3, 4


class Refused(Exception):
    """the source (or the proxy) said no: stop this source for this run."""

    def __init__(self, why, status=None, retry_after=None, body=b""):
        super().__init__(why)
        self.status, self.retry_after, self.body = status, retry_after, body or b""


class Failed(Exception):
    """a request failed twice (5xx or transport)."""


def _retry_after(headers):
    v = (headers or {}).get("Retry-After") if headers else None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def challenge(body, ctype, expect):
    """a 200 that is not the data asked for: an HTML page (a challenge, a login, an error page) where JSON or text was asked."""
    if expect == "any":
        return False
    head = (body or b"")[:200].lstrip().lower()
    if "html" in (ctype or "").lower() or head.startswith(b"<!doctype html") or head.startswith(b"<html"):
        return True
    return expect == "json" and not head.startswith((b"{", b"["))


# a host that asks for a slower pace than one request a second (SqueezeMetrics: DAT-12, one file a day; at most one per 5 s),
# kept at least as slow as the desk data hub's entry for it (desk/data/http.py _LIMITS)
HOST_GAP_S = {"squeezemetrics.com": 5.0, "www.squeezemetrics.com": 5.0}


class Polite:
    """the alt-data jobs' HTTP client (see the module docstring)."""

    def __init__(self, ua, pace_dir, opener=None, sleep=time.sleep, clock=time.time, timeout=60, min_interval=1.0):
        if not ua:
            raise ValueError("no User-Agent: the job passes the guarded one in ALTDATA_USER_AGENT")
        self.ua, self.pace_dir, self.sleep, self.clock, self.timeout, self.gap = ua, pace_dir, sleep, clock, timeout, min_interval
        self.open = opener or urllib.request.build_opener().open
        self.lock = threading.Lock()
        self.stats = {"requests": 0, "bytes": 0, "status": {}, "retries": 0}

    def _count(self, k, n=1):
        with self.lock:
            self.stats["status"][str(k)] = self.stats["status"].get(str(k), 0) + n

    def _pace(self, host):
        os.makedirs(self.pace_dir, exist_ok=True)
        with open(os.path.join(self.pace_dir, host), "a+") as fh:
            fcntl.flock(fh, fcntl.LOCK_EX)
            fh.seek(0)
            txt = fh.read().strip()
            try:
                last = float(txt) if txt else 0.0
            except ValueError:
                last = 0.0
            gap = max(self.gap, HOST_GAP_S.get(host, 0.0))
            wait = last + gap - self.clock()
            if wait > 0:
                self.sleep(min(wait, gap))
            fh.seek(0)
            fh.truncate()
            fh.write(repr(self.clock()))
            fh.flush()

    def request(self, url, data=None, headers=None, expect="json"):
        """-> (body bytes, response headers) or (None, headers) for a 404; raises Refused or Failed."""
        host = urllib.parse.urlsplit(url).hostname or "?"
        for attempt in (0, 1):
            self._pace(host)
            with self.lock:
                self.stats["requests"] += 1
            rq = urllib.request.Request(url, data=data, headers=dict({"User-Agent": self.ua, "Accept": ACCEPT[expect],
                                                                     "Accept-Encoding": "gzip"}, **(headers or {})))
            try:
                with self.open(rq, timeout=self.timeout) as r:
                    body, hdr = r.read(), dict(r.headers.items())
            except urllib.error.HTTPError as e:
                self._count(e.code)
                try:
                    eb = e.read()[:2000]
                except Exception:
                    eb = b""
                if e.code == 404:
                    return None, dict((e.headers or {}).items())
                if e.code == 407:
                    raise Refused(f"the proxy refused {host} ({e.code}): not retried", e.code)
                if e.code in (403, 429, 503):
                    raise Refused(f"{host} answered {e.code}: stopped", e.code, _retry_after(e.headers), eb)
                if e.code >= 500 and attempt == 0:
                    self.stats["retries"] += 1
                    self.sleep(5)
                    continue
                raise Failed(f"{host} answered {e.code} for {url.split('?')[0][:120]}")
            except urllib.error.URLError as e:
                msg = str(getattr(e, "reason", e))
                if "Tunnel connection failed" in msg:
                    self._count("proxy")
                    raise Refused(f"the proxy refused the tunnel to {host} ({msg[:60]}): not retried")
                self._count("net")
                if attempt == 0:
                    self.stats["retries"] += 1
                    self.sleep(5)
                    continue
                raise Failed(f"{host}: {msg[:120]}")
            except OSError as e:
                self._count("net")
                if attempt == 0:
                    self.stats["retries"] += 1
                    self.sleep(5)
                    continue
                raise Failed(f"{host}: {type(e).__name__} {str(e)[:100]}")
            if (hdr.get("Content-Encoding") or "").lower() == "gzip":
                body = gzip.decompress(body)
            self._count(200)
            with self.lock:
                self.stats["bytes"] += len(body)
            if challenge(body, hdr.get("Content-Type"), expect):
                raise Refused(f"{host} sent a page that is not the data asked for (content-type {hdr.get('Content-Type')}): "
                              "a challenge or login page; stopped", 200)
            return body, hdr
        raise Failed(f"{host}: no answer")


def now_et_str(clock=None):
    """the producers' own stamp format ('%Y-%m-%d %H:%M:%S ET', the box clock in New York)."""
    from zoneinfo import ZoneInfo
    t = dt.datetime.fromtimestamp(clock if clock is not None else time.time(), tz=ZoneInfo(TZ))
    return t.strftime("%Y-%m-%d %H:%M:%S ET")


def _write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path + ".tmp", "w") as f:
        json.dump(obj, f, indent=1, default=str)
    os.replace(path + ".tmp", path)


def _read_json(path, default=None):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


# ------------------------------------------------------------------------------------------------------------ wiki
def wiki_window(store_last_day, research_end, today_utc):
    """the collector's window: (newest stored day - 7 days | research end - 29 days, yesterday UTC) as dates."""
    end = today_utc - dt.timedelta(days=1)
    start = (store_last_day - dt.timedelta(days=7)) if store_last_day is not None else (research_end - dt.timedelta(days=29))
    return start, end


def wiki_todo(titles, progress, start, end):
    """(the titles still to fetch for this window, the progress record). A record of another window's last day starts over;
    one of the same window resumes (its start is kept, so every title of a window covers the same days)."""
    if not progress or progress.get("end") != str(end):
        progress = {"end": str(end), "start": str(start), "done": [], "empty404": [], "failed": []}
    seen = set(progress["done"]) | set(progress["empty404"])
    return [(s, t) for s, t in titles if s not in seen], progress


def wiki_url(api, title, start, end):
    """WIKI_LIVE/collector.py's URL: the title unquoted then quoted with no safe characters."""
    t = urllib.parse.quote(urllib.parse.unquote(title), safe="")
    return api.format(t=t, a=start.strftime("%Y%m%d"), b=end.strftime("%Y%m%d"))


def wiki_complete(n_titles, progress):
    """the collector's success rule: every title answered, failures <= max(10, 5%)."""
    answered = len(progress["done"]) + len(progress["empty404"]) + len(progress["failed"])
    return answered >= n_titles and len(progress["failed"]) <= max(10, 0.05 * n_titles)


def _merge_store(pd, path, rows, fetched):
    N = pd.DataFrame(rows, columns=["sym", "title", "date", "views"])
    N["date"] = pd.to_datetime(N.date, format="%Y%m%d")
    N["views"] = N.views.astype("int32")
    N["fetched_utc"] = fetched
    if os.path.exists(path):
        N = pd.concat([pd.read_parquet(path), N], ignore_index=True)
    N = N.sort_values("fetched_utc").drop_duplicates(["sym", "date"], keep="last").sort_values(["sym", "date"]).reset_index(drop=True)
    N.to_parquet(path + ".tmp", compression="zstd", index=False)
    os.replace(path + ".tmp", path)
    return N


def wiki_heartbeat(wl, status, note, start_et, clock=None):
    """WIKI_LIVE/jobs/daily.sh's hb(): status, note and stamps; on ok also the fetch and features summaries and the success
    stamp. A failed run keeps the last success's fields (the record says when the data was last good)."""
    p = os.path.join(wl, "jobs", "heartbeat.json")
    h = _read_json(p, {}) or {}
    fl = os.path.join(wl, "jobs", "failures.log")
    fails = sum(1 for _ in open(fl)) if os.path.exists(fl) else 0
    h.update(status=status, note=note, last_attempt_start_et=start_et, last_update_et=now_et_str(clock),
             failures_logged_total=fails, producer="Author_altdata wiki (desk job)")
    if status == "ok":
        f = _read_json(os.path.join(wl, "data", "fetch_last.json"), {}) or {}
        s = _read_json(os.path.join(wl, "out", "features_last.json"), {}) or {}
        h.update(last_success_et=h["last_update_et"],
                 fetch={k: f.get(k) for k in ("window", "titles", "ok", "empty404", "failed", "http429", "retries", "live_last_day",
                                              "seconds")},
                 asof_date=s.get("latest_asof"), views_thru=s.get("views_thru"), stale_days=s.get("stale_days"),
                 rows_written=s.get("rows_written"), history_rows=s.get("history_rows"), mapped=s.get("mapped"),
                 with_data_1d=s.get("with_data_1d"), wiki_cov=s.get("wiki_cov"), by_band=s.get("by_band"), flags=s.get("flags"),
                 outputs=[os.path.join(wl, "out", x) for x in ("wiki_features_latest.parquet", "wiki_features_history.parquet",
                                                               "wiki_attention_latest.json")])
    else:
        with open(fl, "a") as f:
            f.write(f"{now_et_str(clock)} Author_altdata wiki FAIL: {note}\n")
    _write_json(p, h)
    return h


def run_wiki(a, client, out):
    import pandas as pd
    wl = os.path.join(a.research, "WIKI_LIVE")
    sys.path.insert(0, wl)
    import common as W                                    # the materialized WIKI_LIVE/common.py (paths under the research root)
    os.makedirs(os.path.join(wl, "data"), exist_ok=True)
    start_et = now_et_str(a.now)
    if os.path.exists(os.path.join(wl, "jobs", "PAUSE")):
        out.update(skipped="WIKI_LIVE/jobs/PAUSE present")
        return 0
    M = W.load_map()
    titles = list(zip(M.sym, M.title))
    today_utc = dt.datetime.fromtimestamp(a.now, tz=dt.timezone.utc).date()
    last = pd.read_parquet(W.LIVE_PV, columns=["date"]).date.max().date() if os.path.exists(W.LIVE_PV) else None
    start, end = wiki_window(last, W.RESEARCH_END.date(), today_utc)
    prog_p = os.path.join(a.state, "wiki_progress.json")
    todo, prog = wiki_todo(titles, _read_json(prog_p), start, end)
    start = dt.date.fromisoformat(prog["start"])
    fetched = pd.Timestamp(a.now, unit="s").tz_localize(None)
    rows, added, http429, stop = [], 0, 0, None
    t0 = time.time()

    def flush():
        nonlocal rows, added
        if rows:
            _merge_store(pd, W.LIVE_PV, rows, fetched)
            added += len(rows)
            rows = []
        _write_json(prog_p, prog)
    try:
        for i, (sym, title) in enumerate(todo):
            if time.time() > a.deadline:
                stop = "cut: the run's deadline came first"
                break
            try:
                body, _ = client.request(wiki_url(W.API, title, start, end), expect="json")
            except Failed as e:
                prog["failed"].append(sym)
                out.setdefault("errors", []).append(str(e)[:120])
                continue
            if body is None:
                prog["empty404"].append(sym)
            else:
                for it in json.loads(body).get("items") or []:
                    rows.append((sym, title, it["timestamp"][:8], it["views"]))
                prog["done"].append(sym)
            if (i + 1) % 100 == 0:
                flush()
    except Refused as e:
        stop, out["refused"] = f"refused: {e}", str(e)
        out["retry_after_s"] = e.retry_after
        http429 = int(e.status == 429)
    flush()
    st = dict(ok=len(prog["done"]), empty404=len(prog["empty404"]), failed=len(prog["failed"]))
    live = pd.read_parquet(W.LIVE_PV, columns=["sym", "date"]) if os.path.exists(W.LIVE_PV) else None
    info = dict(run_utc=fetched.isoformat(), window=[str(start), str(end)], titles=len(titles), **st, retries=client.stats["retries"],
                http429=http429, failed_syms=prog["failed"][:50], rows_added=added, requests=client.stats["requests"],
                todo_at_start=len(todo),
                live_rows=None if live is None else int(len(live)), live_syms=None if live is None else int(live.sym.nunique()),
                live_last_day=None if live is None else str(live.date.max().date()), seconds=round(time.time() - t0, 1),
                user_agent=client.ua)
    _write_json(os.path.join(wl, "data", "fetch_last.json"), info)
    out.update(fetch=info, http=client.stats)
    if stop or not wiki_complete(len(titles), prog):
        why = stop or f"incomplete: {st['ok'] + st['empty404']} of {len(titles)} titles answered, {st['failed']} failed"
        wiki_heartbeat(wl, "fail", why, start_et, a.now)
        out["status"] = "fail"
        out["why"] = why
        return EXIT_REFUSED if out.get("refused") else EXIT_CUT
    asof_to = dt.datetime.fromtimestamp(a.now, tz=dt.timezone.utc).astimezone(__import__("zoneinfo").ZoneInfo(TZ)).date()
    rem = max(60, int(a.deadline - time.time()))
    r = subprocess.run([sys.executable, os.path.join(wl, "features.py"), "--asof-to", str(asof_to)], cwd=wl,
                       capture_output=True, text=True, timeout=rem)
    if r.returncode != 0:
        why = f"features.py rc {r.returncode}: {(r.stderr or r.stdout or '')[-200:]}"
        wiki_heartbeat(wl, "fail", why, start_et, a.now)
        out.update(status="fail", why=why)
        return 1
    hb = wiki_heartbeat(wl, "ok", "collector (desk job, 1 req/s) + features done", start_et, a.now)
    os.makedirs(os.path.join(wl, "jobs", "state"), exist_ok=True)
    open(os.path.join(wl, "jobs", "state", f"done_{asof_to}"), "w").close()
    out.update(status="ok", asof_date=hb.get("asof_date"), views_thru=hb.get("views_thru"), wiki_cov=hb.get("wiki_cov"))
    return 0


# ---------------------------------------------------------------------------------------------------------- wswing
def tracker_splits(scratch, sym):
    """w_swing_feed.yahoo_splits' answer, from the tracker's cached Yahoo 1d payload (chart events=div,splits): sorted
    [(ET date, numerator / denominator)], [] for none, None when the payload is missing or unreadable."""
    from zoneinfo import ZoneInfo
    p = os.path.join(scratch, "shadow", "work", "data", "1d", f"{sym.replace('^', '_')}.json")
    try:
        with open(p) as f:
            j = json.load(f)
        res = (j.get("chart", {}).get("result") or [{}])[0]
    except (OSError, ValueError, AttributeError, IndexError):
        return None
    ev = (res.get("events") or {}).get("splits") or {}
    out = []
    for v in ev.values():
        if v.get("denominator"):
            d = dt.datetime.fromtimestamp(int(v["date"]), tz=dt.timezone.utc).astimezone(ZoneInfo(TZ)).strftime("%Y-%m-%d")
            out.append((d, float(v["numerator"]) / float(v["denominator"])))
    return sorted(out)


def run_wswing(a, out):
    os.environ["WSW_NO_NET"] = "1"
    sys.path.insert(0, os.path.join(a.research, "DESK_INTEGRATION", "w_swing_live"))
    import w_swing_feed as WF
    WF.yahoo_splits = lambda sym, today: tracker_splits(a.scratch, sym)
    argv, sys.argv = sys.argv, ["w_swing_feed.py", "run"]
    try:
        rc = WF.main()
    finally:
        sys.argv = argv
    J = _read_json(os.path.join(WF.OUT, "w_swing_status_latest.json"), {}) or {}
    out.update(status=J.get("status"), week=J.get("as_of_week_end"), n_fires=J.get("n_fires"), inputs=J.get("inputs"))
    return rc or 0


# ------------------------------------------------------------------------------------------------------------- sec
def run_sec(a, client, out):
    sys.path.insert(0, os.path.join(a.research, "ALTDATA_LIVE", "plugins"))
    import common as AC
    import form4_insider as F4

    class PoliteFetcher:                               # form4_insider's Fetcher interface on the polite client
        def __init__(self, *k, **kw):
            pass

        def get(self, url):
            return client.request(url, expect="any")[0]

        def stats(self):
            return dict(client.stats)
    F4.Fetcher, AC.UA_SEC = PoliteFetcher, client.ua
    try:
        out["summary"] = F4.run_nightly()
    except Refused as e:
        AC.heartbeat("form4_insider", status="fail", error=str(e)[:300])
        out.update(refused=str(e), retry_after_s=e.retry_after)
        return EXIT_REFUSED
    except Exception as e:
        AC.heartbeat("form4_insider", status="fail", error=str(e)[:300])
        raise
    out["status"] = "ok"
    return 0


# ----------------------------------------------------------------------------------------------------------- finra
def run_finra(a, client, out):
    import pandas as pd
    sys.path.insert(0, os.path.join(a.research, "ALTDATA_LIVE", "plugins"))
    import common as AC
    import finra_flow as FF
    T = pd.Timestamp(dt.datetime.fromtimestamp(a.now, tz=__import__("zoneinfo").ZoneInfo(TZ)).date())
    notes, new_sv, new_ats = [], {}, {}
    try:
        cached = [pd.Timestamp(os.path.basename(f)[:8]) for f in os.listdir(FF.SVD) if f.endswith(".parquet")]
        last = max(cached) if cached else pd.Timestamp("2026-09-30")
        for d in [d for d in FF.sessions() if last < d <= T]:
            if time.time() > a.deadline:
                notes.append("cut at the deadline")
                break
            try:
                b, _ = client.request(FF.SV_URL.format(d=d), expect="text")
            except Refused as e:                   # the CDN answers 403 AccessDenied for a day not yet published
                if e.status == 403 and b"AccessDenied" in e.body:
                    notes.append(f"CNMS {d.date()} not published yet")
                    break
                raise
            if b is None or not b.startswith(b"Date|"):
                notes.append(f"CNMS {d.date()} not published yet")
                break
            import io
            x = pd.read_csv(io.BytesIO(b), sep="|", dtype={"Date": str, "Symbol": str})
            x = x[x.Date.str.fullmatch(r"\d{8}", na=False)][["Date", "Symbol", "ShortVolume", "TotalVolume"]]
            x.columns = ["date", "sym", "short_vol", "total_vol"]
            x["date"] = pd.to_datetime(x.date).dt.date
            x["short_vol"], x["total_vol"] = x.short_vol.astype("float32"), x.total_vol.astype("float32")
            f = f"{FF.SVD}/{d:%Y%m%d}.parquet"
            x.to_parquet(f + ".tmp", index=False, compression="zstd")
            os.replace(f + ".tmp", f)
            new_sv[str(d.date())] = len(x)
        st_p = os.path.join(a.state, "finra_ats.json")
        st = _read_json(st_p, {}) or {}
        weekly = float(st.get("repulled_at") or 0) < a.now - 6 * 86400    # revisable weeks re-pulled once a week
        for wk in pd.date_range(T - pd.Timedelta(days=70), T - pd.Timedelta(days=14), freq="W-MON"):
            f = f"{FF.ATD}/{wk.date()}.parquet"
            if os.path.exists(f) and not (weekly and (T - wk).days <= 60):
                continue
            rows, off, tot = [], 0, None
            while True:
                body = {"limit": 5000, "offset": off, "fields": ["issueSymbolIdentifier", "weekStartDate", "totalWeeklyShareQuantity",
                        "totalWeeklyTradeCount", "totalNotionalSum", "initialPublishedDate", "lastUpdateDate", "tierIdentifier"],
                        "compareFilters": [{"compareType": "equal", "fieldName": "weekStartDate", "fieldValue": str(wk.date())},
                                           {"compareType": "equal", "fieldName": "summaryTypeCode", "fieldValue": "ATS_W_SMBL"}]}
                b, h = client.request(FF.ATS_URL, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"},
                                      expect="json")
                r = json.loads(b) if b and b.strip() else []
                tot = int({k.lower(): v for k, v in (h or {}).items()}.get("record-total", 0) or 0)
                rows += r
                off += 5000
                if not r or off >= tot:
                    break
            if rows:
                d = pd.DataFrame(rows)
                d = d[d.tierIdentifier != "OTCE"]
                d["fetched_et"] = now_et_str(a.now)
                d.to_parquet(f + ".tmp", index=False, compression="zstd")
                os.replace(f + ".tmp", f)
            new_ats[str(wk.date())] = len(rows) or -1
        if weekly:
            _write_json(st_p, {"repulled_at": a.now})
        info = FF.build()
    except Refused as e:
        AC.heartbeat("finra_flow", status="fail", error=str(e)[:300])
        out.update(refused=str(e), retry_after_s=e.retry_after, sv_new=new_sv, ats_new=new_ats)
        return EXIT_REFUSED
    except Exception as e:
        AC.heartbeat("finra_flow", status="fail", error=str(e)[:300])
        raise
    info.update(sv_new=new_sv, ats_new=new_ats, notes=notes, http=client.stats)
    _write_json(os.path.join(FF.OUT, "finra_flow_last.json"), info)
    AC.heartbeat("finra_flow", status="ok", error=None, finished_et=now_et_str(), **{k: v for k, v in info.items() if k != "outputs"})
    out.update(status="ok", **{k: info.get(k) for k in ("sv_last", "ats_last_week", "ats_z26_latest")})
    return 0


# ------------------------------------------------------------------------------------------------------------- options
def _gamma_low_of(pd, df):
    """the vendored parity's gamma_low of a DIX frame (date, gex): rolling-252 rank (120 minimum) <= 0.30"""
    g = df.set_index("date").sort_index().gex
    return g.rolling(252, min_periods=120).rank(pct=True).le(0.30).astype(float)


def run_options(a, client, out):
    """options_market (the market level of the vendored options_bundle, SqueezeMetrics' DIX file): the desk job squeezemetrics
    fetched the file and built the rows (desk/data/squeezemetrics.py options_market_rows); this writes them as the lanes read
    them (ALTDATA_LIVE/out/options_market_{latest,history}.parquet, history merged on asof_date, new rows win), the
    heartbeat (plugins.options_bundle) and, where the frozen research GAMMA/data/DIX.csv is on the research root, the parity
    marker the composer requires (gamma_low.match_rate: research's gamma_low against this series on every session)."""
    import pandas as pd
    path = getattr(a, "squeeze", None)
    doc = _read_json(path, None) if path else None
    if not doc or not doc.get("rows"):
        out["error"] = "no SqueezeMetrics options_market input: the desk job squeezemetrics has not written one"
        return 1
    ao = os.path.join(a.research, "ALTDATA_LIVE")
    outd = os.path.join(ao, "out")
    os.makedirs(outd, exist_ok=True)
    cols = ["asof_date", "gex_date", "gex_stale", "gex", "dix", "gex_pct252", "gamma_low", "first_seen_et", "computed_et"]
    M = pd.DataFrame(doc["rows"])[cols]
    for c in ("asof_date", "gex_date"):
        M[c] = pd.to_datetime(M[c]).dt.date
    M["gex_stale"] = M.gex_stale.astype("int64")
    M["gamma_low"] = M.gamma_low.astype(object)
    hp = os.path.join(outd, "options_market_history.parquet")
    H = M
    if os.path.exists(hp):
        H = pd.concat([pd.read_parquet(hp), M], ignore_index=True).drop_duplicates(["asof_date"], keep="last")
    H = H.sort_values("asof_date").reset_index(drop=True)
    for name, df in (("options_market_latest", H.iloc[[-1]].reset_index(drop=True)), ("options_market_history", H)):
        f = os.path.join(outd, name + ".parquet")
        df.to_parquet(f + ".tmp", index=False, compression="zstd")
        os.replace(f + ".tmp", f)
    last = H.iloc[-1]
    info = dict(asof_latest=str(last.asof_date), gex_date=str(last.gex_date), gex_stale=int(last.gex_stale),
                gamma_low_latest=None if last.gamma_low is None or last.gamma_low != last.gamma_low else bool(last.gamma_low),
                rows=int(len(H)))
    rp = os.path.join(a.research, "GAMMA", "data", "DIX.csv")
    if os.path.exists(rp) and doc.get("series"):
        Dr = pd.read_csv(rp, parse_dates=["date"])
        Dl = pd.DataFrame(doc["series"], columns=["date", "price", "dix", "gex"])
        Dl["date"] = pd.to_datetime(Dl.date)
        ar, al = _gamma_low_of(pd, Dr), _gamma_low_of(pd, Dl)
        days = list(pd.bdate_range(Dr.date.min() + pd.Timedelta(days=400), Dr.date.max()))
        x = ar.reindex(days, method="ffill") == al.reindex(days, method="ffill")
        pp = os.path.join(outd, "parity_options_bundle.json")
        rep = _read_json(pp, {}) or {}
        rep["generated_et"] = now_et_str(a.now)
        rep["gamma_low"] = dict(sessions=len(days), match=int(x.sum()), match_rate=round(float(x.mean()), 6) if len(days) else None,
                                note="research GAMMA/data/DIX.csv gamma_low vs this series (desk/data/squeezemetrics.py), weekdays")
        _write_json(pp, rep)
        info["parity_match_rate"] = rep["gamma_low"]["match_rate"]
    else:
        info["parity"] = "not written: no GAMMA/data/DIX.csv on the research root" if not os.path.exists(rp) else "no series"
    hb = os.path.join(ao, "heartbeat.json")
    h = _read_json(hb, {}) or {}
    stamp = now_et_str(a.now)
    h.setdefault("plugins", {}).setdefault("options_bundle", {}).update(status="ok", error=None, market_level="squeezemetrics",
                                                                        last_update_et=stamp, **{k: info[k] for k in ("asof_latest", "gex_date")})
    h["last_update_et"] = stamp
    _write_json(hb, h)
    out.update(status="ok", **info)
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("job", choices=["wiki", "finra", "sec", "wswing", "options"])
    ap.add_argument("--research", required=True)
    ap.add_argument("--scratch", required=True)
    ap.add_argument("--state", required=True)
    ap.add_argument("--now", type=float, default=None)
    ap.add_argument("--deadline", type=float, default=None)
    ap.add_argument("--squeeze", default=None)
    a = ap.parse_args(argv)
    a.now = a.now or time.time()
    a.deadline = a.deadline or (time.time() + 3000)
    os.makedirs(a.state, exist_ok=True)
    out, rc = {"job": a.job}, 1
    try:
        if a.job == "wswing":
            rc = run_wswing(a, out)
        elif a.job == "options":
            rc = run_options(a, None, out)
        else:
            client = Polite(os.environ.get("ALTDATA_USER_AGENT", ""), os.path.join(a.state, "pace"))
            rc = {"wiki": run_wiki, "finra": run_finra, "sec": run_sec}[a.job](a, client, out)
    except Exception as e:
        out["error"] = f"{type(e).__name__}: {str(e)[:300]}"
        rc = 1
    sys.stdout.flush()
    print(json.dumps(out, default=str), flush=True)
    return rc


if __name__ == "__main__":
    sys.exit(main())
