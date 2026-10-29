"""Vendored JavaScript / TypeScript sources executed, never reimplemented — the shared plumbing.

A runner under desk/feedlib/node/ imports a vendored source tree (desk/vendor/<namespace>/, byte-exact, git-blob
pins in desk/vendor/MANIFEST.json) and calls the source's own entry points; Node strips the TypeScript types and
desk/feedlib/node/ts_resolve.mjs only maps the sources' extensionless imports / path aliases to their files. This
module re-verifies every pin of the namespace before a run (any drift refuses to run), runs the runner on one JSON
document (stdin -> stdout, bounded heap) and shapes the desk's bar tapes the way the sources' providers received
them (the Yahoo chart API result)."""
import hashlib
import json
import os
import subprocess
from datetime import datetime

from ..util import ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VENDOR = os.path.join(ROOT, "vendor")
NODE_DIR = os.path.join(ROOT, "feedlib", "node")
HEAP = "--max-old-space-size=1024"
_OK = {}


class SourceError(RuntimeError):
    pass


def verify(prefix, min_files):
    """re-hash every vendored file under `prefix` against its MANIFEST pin (cached on mtime / size)."""
    man = json.load(open(os.path.join(VENDOR, "MANIFEST.json")))
    pins = {k: v["blob_sha"] for k, v in man.items() if k.startswith(prefix)}
    if len(pins) < min_files:
        raise SourceError("%s pins missing (%d < %d)" % (prefix, len(pins), min_files))
    for rel, sha in pins.items():
        p = os.path.join(VENDOR, rel)
        st = os.stat(p)
        key = (st.st_mtime_ns, st.st_size)
        if _OK.get(rel) == key:
            continue
        b = open(p, "rb").read()
        if hashlib.sha1(b"blob %d\0" % len(b) + b).hexdigest() != sha:
            raise SourceError("vendored source drifted: %s; refusing to run" % rel)
        _OK[rel] = key
    return len(pins)


def code_id(prefix, runner):
    """the identity of the code a runner executes: its vendored files' MANIFEST pins under `prefix` and the runner
    script itself. A result computed by other code is never reused for this code (desk/sleeves/monitor/reads.py)."""
    man = json.load(open(os.path.join(VENDOR, "MANIFEST.json")))
    pins = sorted((k, v["blob_sha"]) for k, v in man.items() if k.startswith(prefix))
    with open(os.path.join(NODE_DIR, runner), "rb") as f:
        script = hashlib.sha1(f.read()).hexdigest()
    return hashlib.sha1(json.dumps([pins, runner, script]).encode()).hexdigest()


def run(runner, payload, timeout=600):
    """one node process: payload on stdin, the runner's last stdout line parsed; {"ok": false} raises."""
    path = os.path.join(NODE_DIR, runner)
    try:
        p = subprocess.run(["node", HEAP, path], input=json.dumps(payload, allow_nan=False), capture_output=True,
                           text=True, timeout=timeout)
    except FileNotFoundError as e:
        raise SourceError("node is not available") from e
    except subprocess.TimeoutExpired as e:
        raise SourceError("%s timed out after %ss" % (runner, timeout)) from e
    try:
        res = json.loads((p.stdout or "").strip().splitlines()[-1])
    except (ValueError, IndexError) as e:
        raise SourceError("%s produced no JSON (exit %s): %s" % (runner, p.returncode, (p.stderr or "")[-300:])) \
            from e
    if not res.get("ok"):
        raise SourceError("%s error: %s" % (runner, str(res.get("error"))[:300]))
    return res


# Exchange-traded funds among the sources' universes. The desk's tapes carry no provider metadata, so a chart's
# instrument type / venue is classified here (a named divergence of every group that serves charts with it): an
# ETF trades on NYSE Arca ("PCX"), a "-USD" pair is a cryptocurrency ("CCC"), a "^" symbol an index, anything else
# an equity on Nasdaq ("NMS"). The sources only use the type to tell ETFs, equities, crypto and indexes apart and the
# venue to recognise a US listing, which every one of these classifications is.
ETFS = frozenset("""
SPY QQQ IWM DIA VOO VTI IVV RSP MDY EFA EEM EWZ EWJ FXI KWEB ASHR INDA EWT EWY
XLK XLF XLE XLV XLY XLP XLI XLB XLU XLRE XLC SMH SOXX XSD IGV SKYY CIBR HACK BOTZ ROBO ARKK ARKG ARKQ ARKW
KRE KBE XRT XHB ITB JETS XOP OIH XME TAN ICLN QCLN PBW LIT REMX URA URNM NLR COPX PICK SLX GDX GDXJ SIL SILJ
GLD IAU GLDM SLV PPLT PALL USO BNO UNG DBA DBC DBB CPER UUP FXE FXY FXB FXA FXC TLT IEF SHY TLH HYG JNK LQD AGG
BND TIP IBB XBI LABU LABD TQQQ SQQQ QLD QID SSO SDS UPRO SPXU SPXL SPXS SOXL SOXS TNA TZA FAS FAZ NUGT JNUG
DUST JDST UVXY SVXY VXX VIXY BITO BITX IBIT FBTC GBTC ETHA ETHE ETHV ARKB BITB HODL BRRR MSTU MSTX CONL NVDL
TSLL TSLQ NVDS AMDL GGLL METU NCIQ VNQ IYR XLRE ITA PPA XAR UFO ARKX MOO VEGI WEAT CORN SOYB
""".split())


def instrument(symbol):
    s = str(symbol).upper()
    if s.endswith("-USD"):
        return "CRYPTOCURRENCY", "CCC"
    if s.startswith("^"):
        return "INDEX", "SNP"
    if s in ETFS:
        return "ETF", "PCX"
    return "EQUITY", "NMS"


def chart_meta(symbol, bars, now, interval="1d"):
    """the chart meta fields the sources read, from the tape itself: identity, currency, timezone, the classified
    type / venue, the newest print as regularMarketPrice / Time (a daily bar's print at its session's close, never
    after `now`; an intraday bar's at its end), the prior session's close, and the current trading periods from the
    desk calendar."""
    from .. import calendar as cal
    it, ex = instrument(symbol)
    m = {"symbol": str(symbol).upper(), "currency": "USD", "exchangeTimezoneName": "America/New_York",
         "timezone": "EDT", "instrumentType": it, "exchangeName": ex, "fullExchangeName": ex, "priceHint": 2,
         "dataGranularity": interval}
    if bars:
        last = bars[-1]
        t = float(last["t"])
        if interval in ("1d", "1wk"):
            d = cal._as_date(t + 6 * 3600)
            close = cal.session_close(d) if cal.is_trading_day(d) else t
            mt = min(close, now)
        else:
            step = {"1m": 60, "2m": 120, "5m": 300, "15m": 900, "30m": 1800, "1h": 3600, "60m": 3600}.get(interval, 60)
            mt = min(t + step, now)
        m["regularMarketPrice"] = last.get("c")
        m["regularMarketTime"] = int(mt)
        if len(bars) > 1:
            m["previousClose"] = m["chartPreviousClose"] = bars[-2].get("c")
    d = cal._as_date(now)
    local = datetime.fromtimestamp(now, tz=ET)
    tz, off = local.tzname(), int(local.utcoffset().total_seconds())
    m["timezone"], m["gmtoffset"] = tz, off
    if cal.is_trading_day(d):
        op, cl = int(cal.session_open(d)), int(cal.session_close(d))
        m["currentTradingPeriod"] = {
            "pre": {"timezone": tz, "start": op - 19800, "end": op, "gmtoffset": off},
            "regular": {"timezone": tz, "start": op, "end": cl, "gmtoffset": off},
            "post": {"timezone": tz, "start": cl, "end": cl + 14400, "gmtoffset": off}}
    return m


def yahoo_chart(symbol, bars, meta=None):
    """desk bar dicts {t (s), o, h, l, c, v} -> one Yahoo chart API `result` (timestamp + indicators.quote[0]).
    The desk's tape holds completed bars; a missing volume print reaches the desk as 0."""
    ts, q = [], {"open": [], "high": [], "low": [], "close": [], "volume": []}
    for b in bars:
        ts.append(int(round(float(b["t"]))))
        q["open"].append(b.get("o"))
        q["high"].append(b.get("h"))
        q["low"].append(b.get("l"))
        q["close"].append(b.get("c"))
        q["volume"].append(b.get("v"))
    m = {"symbol": symbol}
    m.update(meta or {})
    return {"meta": m, "timestamp": ts, "indicators": {"quote": [q]}}
