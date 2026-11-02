#!/usr/bin/env python3
"""Chain snapshot collector (TastyTrade nested chains).

STORE CONTRACT (the shape the forecast engines already read; see
refresh_honestpop.py, refresh_chain.py, refresh_pinorescape.py,
refresh_gammaearningstrap.py, all of which read CHAINS_DIR):

  CHAINS_DIR = ~/workspace/morgue/state/morgue/chains
  Canonical daily file:  <CHAINS_DIR>/<SYM>/<YYYY-MM-DD>.json.gz
    (the latest capture of that ET day; consumers list *.json.gz in
    <CHAINS_DIR>/<SYM>/ and read the newest day)
  Intraday history:      <CHAINS_DIR>/<SYM>/intraday/<day>T<HHMMSS>Z.json.gz
    (one file per capture, never overwritten)
  Manifest:              <CHAINS_DIR>/manifest.jsonl
    (one JSON line per symbol per run, ok or error; failures are
    loud lines, never silent skips)

  Snapshot document (gzip JSON):
    {"underlying": "SPY", "day": "2026-10-29", "spot": 769.36,
     "spot_source": "yahoo chart regularMarketPrice (price only)",
     "captured_at_utc": "...", "captured_at_et": "...",
     "source": "tastytrade GET /option-chains/<SYM>/nested",
     "columns": ["occ", "oi", "volume", "iv"],
     "oi_date": null,
     "rows": [["SPY261029C00550000", null, null, null], ...]}
  OCC codes are stored space-stripped so the consumers' OCC regex
  parses them. The TastyTrade nested chain carries no open interest,
  no volume and no implied volatility: it is the layout source of
  record only. Content (2026-10-29 cure, chain_content.py): OI is
  MEASURED from Alpaca /v2/options/contracts (oi_date carried in
  the snapshot), volume is MEASURED from Alpaca indicative
  snapshot daily bars, and IV is MODELLED by Black-Scholes
  inversion of Alpaca indicative quote midpoints under stated
  assumptions, labelled MODELLED wherever stored or displayed.
  Enrichment covers expiries within 120 days (IV inside the
  0.75-1.25 moneyness band); outside scope the fields stay null
  (absent), never fabricated zeros. Engine 5 reads occ+iv; the
  modelled IV now reaches it, labelled as modelled in the ledger
  rows' provenance via field_sources.

Auth: TastyTrade credentials live ONLY in
~/.config/muse-desk/tastytrade.key (KEY=VALUE lines; never
printed, logged or copied). A fresh access token is minted per
run via POST /oauth/token with the required User-Agent header.
Read scope only: the TastyTrade endpoints called are
/oauth/token and /option-chains/<SYM>/nested. Alpaca reads go
through alpaca_lib (paper/data hosts, vault-backed secret).

Usage: python3 collect_chains.py [--force]
Without --force, runs outside Mon-Fri 09:30-16:00 America/New_York
(with a 5 minute dispatch tolerance at the open) store nothing and
exit 0. --force is for the seed/manual run.
"""

import gzip
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, time as dtime, timezone
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import terminal_common as _tc
except ImportError:  # collector stays runnable standalone
    _tc = None
try:
    import options_gate as _og
except ImportError:  # gate unavailable: snapshots label undated below
    _og = None
try:
    import chain_content as _ccx
except ImportError:  # content leg unavailable: layout-only snapshot
    _ccx = None

CHAINS_DIR = os.path.expanduser("~/workspace/morgue/state/morgue/chains")
MANIFEST_PATH = os.path.join(CHAINS_DIR, "manifest.jsonl")
KEY_PATH = os.path.expanduser("~/.config/muse-desk/tastytrade.key")
SYMBOLS = ("SPY", "QQQ", "IWM")
ET = ZoneInfo("America/New_York")
UA = "midna-desk/1.0"
OCC_RE = re.compile(r"^([A-Z]+)(\d{6})([CP])(\d{8})$")
OPEN_T = dtime(9, 25)   # 09:30 open minus 5 min dispatch tolerance
CLOSE_T = dtime(16, 0)


# ---- pure validation / shaping (unit-tested) --------------------------
def normalize_occ(raw):
    return (raw or "").replace(" ", "")


def validate_chain_payload(doc, symbol):
    """Validate a TastyTrade nested-chain payload. Returns stats
    {expirations, strikes, contracts, rows} where rows are the
    normalized OCC codes in chain order. Raises ValueError on any
    defect; nothing is stored from an invalid payload."""
    items = ((doc or {}).get("data") or {}).get("items") or []
    if len(items) != 1:
        raise ValueError(f"expected exactly 1 chain item, got {len(items)}")
    item = items[0]
    if item.get("underlying-symbol") != symbol:
        raise ValueError(
            f"payload underlying {item.get('underlying-symbol')!r} "
            f"!= requested {symbol}")
    expirations = item.get("expirations") or []
    if not expirations:
        raise ValueError("payload carries no expirations")
    rows = []
    seen = set()
    strike_rows = 0
    for exp in expirations:
        if not exp.get("expiration-date"):
            raise ValueError("an expiration carries no expiration-date")
        strikes = exp.get("strikes") or []
        if not strikes:
            raise ValueError(
                f"expiration {exp.get('expiration-date')} carries "
                "no strikes")
        strike_rows += len(strikes)
        for st in strikes:
            for side in ("call", "put"):
                code = normalize_occ(st.get(side))
                if not code:
                    raise ValueError(
                        f"strike {st.get('strike-price')} on "
                        f"{exp.get('expiration-date')} has no {side} "
                        "OCC symbol")
                m = OCC_RE.match(code)
                if not m or m.group(1) != symbol:
                    raise ValueError(f"OCC symbol {code!r} does not "
                                     f"parse as a {symbol} contract")
                if code in seen:
                    raise ValueError(f"OCC symbol {code} appears twice")
                seen.add(code)
                rows.append(code)
    if not rows:
        raise ValueError("payload carries no contracts")
    return {"expirations": len(expirations), "strikes": strike_rows,
            "contracts": len(rows), "rows": rows}


def snapshot_gate_block(n_contracts, iv_by_occ=None):
    """The options candidate gate state for one snapshot
    (options_gate.py, DEEP-PASS 3.1 item 3). No source here supplies
    a Greek timestamp, so every contract is undated: labelled in
    the open, never silently trusted, and nothing is refused on a
    timestamp no source supplies. IV is the MODELLED inversion
    (chain_content) where a quote midpoint supported one; the gate
    counts those as present IV and the rest as absent."""
    ivs = [None] * n_contracts
    if iv_by_occ:
        # gate counts only need the multiset of IV states
        present = [v for v in iv_by_occ.values() if v is not None]
        ivs = present + [None] * max(0, n_contracts - len(present))
    if _og is not None:
        summary = _og.gate_summary(
            [{"greek_ts": None, "iv": iv} for iv in ivs], None)
    else:
        ok = sum(1 for v in ivs if v is not None)
        summary = {"total": n_contracts, "admitted": n_contracts,
                   "refused": 0,
                   "greek_max_age_seconds": 4500, "iv_ceiling": 5.0,
                   "greek_states": {"fresh": 0, "stale": 0,
                                    "future": 0,
                                    "undated": n_contracts},
                   "iv_states": {"ok": ok, "absent": n_contracts - ok,
                                 "over_ceiling": 0, "invalid": 0}}
    summary["note"] = (
        "No source here supplies a Greek timestamp, so contracts "
        "are labelled undated. Implied volatility, where present, "
        "is MODELLED (Black-Scholes inversion of the indicative "
        "quote midpoint, assumptions in chain_content.py), never "
        "a measured market IV. A Greek older than 75 minutes, or "
        "an IV at or over 500 percent, refuses a candidate "
        "wherever a source does supply those fields.")
    return summary


def build_snapshot_doc(symbol, day, spot, spot_source, rows,
                       captured_utc, captured_et, spot_quote_ts=None,
                       spot_freshness=None, oi_by_occ=None,
                       volume_by_occ=None, iv_by_occ=None,
                       oi_date=None, content_meta=None):
    codes = sorted(rows)
    if _ccx is not None and (oi_by_occ or volume_by_occ or iv_by_occ):
        snap_rows, coverage = _ccx.merge_content(
            codes, oi_by_occ, volume_by_occ, iv_by_occ)
    else:
        snap_rows = [[code, None, None, None] for code in codes]
        coverage = {"contracts": len(codes), "with_oi": 0,
                    "with_volume": 0, "with_iv": 0}
    doc = {
        "underlying": symbol,
        "day": day,
        "spot": spot,
        "spot_source": spot_source,
        "spot_quote_ts": spot_quote_ts,
        "spot_freshness": spot_freshness,
        "captured_at_utc": captured_utc,
        "captured_at_et": captured_et,
        "source": f"tastytrade GET /option-chains/{symbol}/nested",
        "columns": ["occ", "oi", "volume", "iv"],
        "oi_date": oi_date,
        "options_gate": snapshot_gate_block(len(codes), iv_by_occ),
        "field_sources": {
            "occ": "measured: tastytrade nested chain layout",
            "oi": ("measured: alpaca /v2/options/contracts "
                   "open_interest, dated by oi_date" if oi_by_occ
                   else "absent: no OI source landed this capture"),
            "volume": ("measured: alpaca indicative snapshot "
                       "dailyBar volume" if volume_by_occ
                       else "absent: no volume source landed"),
            "iv": ("MODELLED: Black-Scholes inversion of alpaca "
                   "indicative quote midpoints (chain_content.py "
                   "assumptions); not a measured market IV"
                   if iv_by_occ else
                   "absent: no quote supported an inversion"),
        },
        "field_coverage": coverage,
        "rows": snap_rows,
    }
    if content_meta is not None:
        doc["content"] = content_meta
    return doc


def manifest_line(ts_utc, ts_et, symbol, status, stats=None,
                  nbytes=None, sha256=None, path=None, error=None,
                  content=None):
    line = {"ts_utc": ts_utc, "ts_et": ts_et, "symbol": symbol,
            "status": status}
    if stats is not None:
        line.update({"expirations": stats["expirations"],
                     "strikes": stats["strikes"],
                     "contracts": stats["contracts"]})
    if content is not None:
        line["content"] = content
    if nbytes is not None:
        line["bytes"] = nbytes
    if sha256 is not None:
        line["sha256"] = sha256
    if path is not None:
        line["path"] = path
    if error is not None:
        line["error"] = error
    return line


def in_market_window(now_et):
    if now_et.weekday() >= 5:
        return False
    return OPEN_T <= now_et.time() <= CLOSE_T


# ---- IO ----------------------------------------------------------------
def atomic_write_gz(path, doc):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path),
                               suffix=".tmp.gz")
    try:
        with os.fdopen(fd, "wb") as fh:
            with gzip.GzipFile(filename="", mode="wb", fileobj=fh,
                               mtime=0) as gz:
                gz.write(json.dumps(doc, sort_keys=True).encode())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    raw = open(path, "rb").read()
    return len(raw), hashlib.sha256(raw).hexdigest()


def append_manifest(line):
    os.makedirs(CHAINS_DIR, exist_ok=True)
    with open(MANIFEST_PATH, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(line, sort_keys=True) + "\n")


def curl_json(args, timeout=120):
    out = subprocess.run(["curl", "-sS", "--fail"] + args,
                         capture_output=True, text=True, timeout=timeout)
    if out.returncode != 0:
        raise RuntimeError(f"curl failed rc={out.returncode}: "
                           f"{out.stderr.strip()[:200]}")
    return json.loads(out.stdout)


def curl_to_file(url, headers, timeout=180):
    fd, tmp = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    try:
        args = ["curl", "-sS", "--fail", "-o", tmp]
        for h in headers:
            args += ["-H", h]
        args.append(url)
        out = subprocess.run(args, capture_output=True, text=True,
                             timeout=timeout)
        if out.returncode != 0:
            raise RuntimeError(f"curl failed rc={out.returncode}: "
                               f"{out.stderr.strip()[:200]}")
        with open(tmp, encoding="utf-8") as fh:
            return json.load(fh)
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass


def load_keys():
    kv = {}
    with open(KEY_PATH, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                kv[k.strip()] = v.strip()
    for need in ("TASTYTRADE_CLIENT_SECRET", "TASTYTRADE_REFRESH_TOKEN"):
        if not kv.get(need):
            raise RuntimeError(f"key file is missing {need}")
    return kv


def mint_token(kv):
    payload = json.dumps({
        "grant_type": "refresh_token",
        "refresh_token": kv["TASTYTRADE_REFRESH_TOKEN"],
        "client_secret": kv["TASTYTRADE_CLIENT_SECRET"]})
    doc = curl_json(["-X", "POST", "https://api.tastyworks.com/oauth/token",
                     "-H", "Content-Type: application/json",
                     "-H", f"User-Agent: {UA}", "-d", payload])
    tok = doc.get("access_token")
    if not tok:
        raise RuntimeError("token mint returned no access_token")
    return tok


def fetch_spot(symbol, now=None):
    """Fetch the live spot quote and gate it for freshness
    (terminal_common, 90 seconds, fail-closed). Returns
    (price, source, quote_ts_iso, freshness_state). The quote's own
    timestamp (regularMarketTime) is what is gated, never the fetch
    time, and no older cached price is ever substituted.

    Anchor rule (CHAIN-SPOT-ANCHOR-20261031): the gate is measured
    at the moment the spot response arrives, never at the run's
    start. The collector mints a token and downloads the full
    chain before fetching spot, so a run-start anchor compared
    every live quote against a minutes-old instant and, combined
    with the old zero lower bound on age, rejected quotes stamped
    seconds after the run began (37 of 42 captures lost on
    2026-10-30). Callers pass ``now`` only in tests; the live path
    leaves it None so the anchor is the fetch moment itself."""
    doc = curl_json(
        ["-A", "Mozilla/5.0",
         f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
         "?range=1d&interval=1m"], timeout=60)
    fetch_now = now if now is not None else datetime.now(timezone.utc)
    meta = doc["chart"]["result"][0]["meta"]
    price = meta.get("regularMarketPrice")
    if not isinstance(price, (int, float)) or price <= 0:
        raise RuntimeError(f"no usable spot price for {symbol}")
    quote_ts = meta.get("regularMarketTime")
    if _tc is not None:
        fresh = _tc.quote_freshness(quote_ts, now=fetch_now)
        return (float(price), "yahoo chart regularMarketPrice (price only)",
                fresh["quote_ts"], fresh["state"])
    return (float(price), "yahoo chart regularMarketPrice (price only)",
            None, "unchecked")


# ---- Alpaca content leg (measured OI/volume, MODELLED IV) --------------
IV_LEDGER_PATH = os.path.join(CHAINS_DIR, "iv_ledger_modelled.jsonl")
PAPER_URL = "https://paper-api.alpaca.markets"
DATA_URL = "https://data.alpaca.markets"


def _alpaca_request():
    sys.path.insert(0, os.path.expanduser(
        "~/workspace/custom-skills/local-alpaca-paper/bin"))
    from alpaca_lib import api_request
    return api_request


def fetch_alpaca_content(symbol, codes, spot, day, captured_dt):
    """Measured OI (contracts API, dated), measured volume and
    quote midpoints (indicative snapshots), and MODELLED IV
    inverted from the midpoints (chain_content). Scope: expiries
    within chain_content.ENRICH_EXPIRY_DAYS of the snapshot day
    for OI/volume; IV inside the moneyness band. Returns
    (oi_by_occ, volume_by_occ, iv_by_occ, oi_date, meta, quotes)
    where quotes maps occ -> {bid, ask, mid} for the IV ledger.
    Raises on transport failure; the caller records the failure
    in the snapshot instead of fabricating content."""
    if _ccx is None:
        raise RuntimeError("chain_content module unavailable")
    from datetime import timedelta
    api_request = _alpaca_request()
    target = [c for c in codes
              if _ccx.in_enrichment_window(c, day, spot)]
    target_set = set(target)
    # OI: paginate the contracts API over the enrichment window.
    oi_by_occ, oi_dates = {}, {}
    token = None
    lte = (datetime.fromisoformat(day).date()
           + timedelta(days=_ccx.ENRICH_EXPIRY_DAYS)).isoformat()
    while True:
        params = {"underlying_symbols": symbol, "status": "active",
                  "limit": 1000, "expiration_date_gte": day,
                  "expiration_date_lte": lte}
        if token:
            params["page_token"] = token
        resp = api_request("GET", f"{PAPER_URL}/v2/options/contracts",
                           params=params)
        for c in resp.get("option_contracts", []):
            occ = c.get("symbol")
            if occ not in target_set:
                continue
            raw = c.get("open_interest")
            try:
                oi = int(raw) if raw is not None else None
            except (TypeError, ValueError):
                oi = None
            if oi is not None:
                oi_by_occ[occ] = oi
                d = c.get("open_interest_date")
                if d:
                    oi_dates[d] = oi_dates.get(d, 0) + 1
        token = resp.get("next_page_token")
        if not token:
            break
    oi_date = (max(oi_dates, key=oi_dates.get) if oi_dates else None)
    # Quotes + volume: indicative snapshots in batches of 100.
    volume_by_occ, iv_by_occ, quotes = {}, {}, {}
    div = _ccx.DIV_YIELD.get(symbol, 0.0)
    for i in range(0, len(target), 100):
        batch = target[i:i + 100]
        resp = api_request(
            "GET", f"{DATA_URL}/v1beta1/options/snapshots",
            params={"symbols": ",".join(batch), "feed": "indicative"})
        for occ, snap in (resp.get("snapshots") or {}).items():
            bar = snap.get("dailyBar") or {}
            if isinstance(bar.get("v"), (int, float)):
                volume_by_occ[occ] = int(bar["v"])
            q = snap.get("latestQuote") or {}
            mid = _ccx.quote_mid(q.get("bp"), q.get("ap"))
            if mid is None or not _ccx.in_iv_band(occ, spot):
                continue
            p = _ccx.parse_occ(occ)
            if not p:
                continue
            iv = _ccx.implied_vol(
                mid, spot, p["strike"],
                _ccx.t_years(p["expiry"], captured_dt),
                p["is_call"], div)
            if iv is not None:
                iv_by_occ[occ] = round(iv, 4)
                quotes[occ] = {"bid": q.get("bp"), "ask": q.get("ap"),
                               "mid": round(mid, 4)}
    meta = {"enrichment_expiry_days": _ccx.ENRICH_EXPIRY_DAYS,
            "iv_moneyness_band": list(_ccx.IV_MONEYNESS),
            "oi_source": "alpaca /v2/options/contracts open_interest",
            "volume_source": "alpaca indicative snapshot dailyBar.v",
            "iv_source": _ccx.IV_MODEL_WORDS,
            "contracts_in_window": len(target)}
    return oi_by_occ, volume_by_occ, iv_by_occ, oi_date, meta, quotes


def append_iv_ledger(symbol, day, captured_utc, spot, snap_rows,
                     quotes):
    """Append this capture's MODELLED per-strike IV rows (with
    side, from the OCC code) to the modelled IV ledger, so skew
    is computable from a stored record. Duplicate guard on
    (date, occ): a re-capture the same day adds nothing.

    One-spot rule (cure IV-LEDGER-SPOT-20261031): the ledger is a
    daily record and its consumers (IV Weather, Skew Lens) fail
    closed when one (date, underlying) carries two spots, because
    each row's IV was inverted at the spot recorded with it. The
    first capture of a day therefore sets that day's spot for the
    underlying: a later same-day capture whose spot differs adds
    NO rows at all (its snapshot still stores in the intraday
    chain store, which carries its own spot per capture). A
    later capture at the same spot still contributes contracts
    the first capture did not carry."""
    rows = []
    for occ, _oi, _vol, iv in snap_rows:
        if iv is None or occ not in quotes:
            continue
        p = _ccx.parse_occ(occ)
        if not p:
            continue
        rows.append({"date": day, "captured_at_utc": captured_utc,
                     "underlying": symbol, "occ": occ,
                     "expiry": p["expiry"], "strike": p["strike"],
                     "side": p["side"], "iv": iv,
                     "iv_basis": _ccx.IV_BASIS,
                     "model": _ccx.IV_MODEL_WORDS,
                     "spot": spot,
                     "quote_bid": quotes[occ]["bid"],
                     "quote_ask": quotes[occ]["ask"],
                     "quote_mid": quotes[occ]["mid"]})
    if not rows:
        return 0
    seen = set()
    day_spots = set()
    if os.path.exists(IV_LEDGER_PATH):
        with open(IV_LEDGER_PATH, encoding="utf-8") as fh:
            for line in fh:
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                if r.get("date") == day:
                    seen.add(r.get("occ"))
                    if r.get("underlying") == symbol:
                        day_spots.add(r.get("spot"))
    if day_spots and spot not in day_spots:
        print(f"collect_chains: IV ledger keeps one spot per day "
              f"and name: {symbol} on {day} is already recorded at "
              f"{sorted(day_spots)}; this capture at {spot} adds "
              f"no ledger rows (its snapshot still stores)",
              file=sys.stderr)
        return 0
    fresh = [r for r in rows if r["occ"] not in seen]
    if fresh:
        os.makedirs(CHAINS_DIR, exist_ok=True)
        with open(IV_LEDGER_PATH, "a", encoding="utf-8") as fh:
            for r in fresh:
                fh.write(json.dumps(r, sort_keys=True) + "\n")
    return len(fresh)


STORE_README = """# Chain snapshot store

Written by `terminal-lineup/site/collect_chains.py` (TastyTrade
nested chains, SPY/QQQ/IWM, every 30 minutes in market hours).

Layout:
- `<SYM>/<YYYY-MM-DD>.json.gz`: canonical daily snapshot (latest
  capture of that ET day). This is the file the forecast engines
  read: Engine 5 Honest POP, Engine 11, Engine 27, Chain Explorer.
- `<SYM>/intraday/<day>T<HHMMSS>Z.json.gz`: every capture, kept.
- `manifest.jsonl`: one line per symbol per run with UTC and ET
  timestamps, expirations count, strikes count, contracts count,
  stored bytes and sha256; failures are recorded as status=error
  lines with the error named and a content block carrying
  iv_ledger_rows_added 0 with the error repeated as
  iv_ledger_error, so lost modelled IV accrual is named in the
  manifest itself.

Snapshot shape: {underlying, day, spot, spot_source, spot_quote_ts,
spot_freshness, captured_at_utc,
captured_at_et, source, columns: [occ, oi, volume, iv], oi_date,
options_gate, field_sources, field_coverage, content,
rows: [[occ, oi, volume, iv], ...]}. OCC codes are
space-stripped. The options_gate block records the candidate gate
(75 minute Greek freshness where a timestamp exists, undated
labelling where none does, IV ceiling 500 percent); no source
here supplies a Greek timestamp, so contracts are undated.
The spot quote is freshness-gated at capture (terminal_common,
90 seconds, fail-closed): in the market window a stale or missing
quote timestamp stores no snapshot and lands as a manifest error.
Field honesty (2026-10-29 content cure): the TastyTrade nested
chain still carries no open interest, volume or implied
volatility; it remains the layout source of record only. OI is
MEASURED from Alpaca's contracts API (dated by oi_date), volume
is MEASURED from Alpaca indicative snapshot daily bars, and IV
is MODELLED: Black-Scholes inversion of Alpaca indicative quote
midpoints under the assumptions stated in chain_content.py,
labelled MODELLED in field_sources and in the per-strike ledger
`iv_ledger_modelled.jsonl` written beside this README. Enrichment
covers expiries within 120 days of the snapshot day (IV inside
the 0.75-1.25 moneyness band); outside that scope the fields are
null (absent), never fabricated zeros. A failed Alpaca leg is
recorded as content.error in the snapshot and the layout still
stores; absence is never dressed as content.
"""


def ensure_store_readme():
    path = os.path.join(CHAINS_DIR, "README.md")
    if not os.path.exists(path):
        os.makedirs(CHAINS_DIR, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(STORE_README)


def main(argv):
    force = "--force" in argv
    now_utc = datetime.now(timezone.utc)
    now_et = now_utc.astimezone(ET)
    ts_utc = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
    ts_et = now_et.strftime("%Y-%m-%dT%H:%M:%S%z")
    if not force and not in_market_window(now_et):
        print(f"collect_chains: outside market window "
              f"({ts_et} ET); nothing stored")
        return 0
    day = now_et.strftime("%Y-%m-%d")
    stamp = now_utc.strftime("%Y-%m-%dT%H%M%SZ")
    ensure_store_readme()
    kv = load_keys()
    token = mint_token(kv)
    headers = [f"Authorization: Bearer {token}", f"User-Agent: {UA}"]
    failures = 0
    for symbol in SYMBOLS:
        try:
            doc = curl_to_file(
                f"https://api.tastyworks.com/option-chains/{symbol}/nested",
                headers)
            stats = validate_chain_payload(doc, symbol)
            # No now argument: the freshness gate anchors at the
            # spot fetch moment inside fetch_spot, not at this
            # run's start (CHAIN-SPOT-ANCHOR-20261031).
            spot, spot_source, spot_ts, spot_state = fetch_spot(symbol)
            if in_market_window(now_et) and spot_state != "fresh":
                # Fail closed in session: a stale or missing live
                # quote stores NO snapshot rather than presenting an
                # old price as current. The manifest error line names
                # it; the previous snapshot stays as the dated record
                # it is, never relabelled as this capture.
                raise RuntimeError(
                    f"spot quote for {symbol} is {spot_state} "
                    f"(quote_ts={spot_ts}); refusing to store a "
                    f"snapshot on a stale live quote")
            # Content leg: measured OI/volume + MODELLED IV from
            # Alpaca. A failure here never loses the layout accrual
            # and never fabricates content: it is named in the
            # snapshot's content block and in the manifest line.
            content_kwargs, content_meta, quotes = {}, None, {}
            try:
                (oi_map, vol_map, iv_map, oi_date, content_meta,
                 quotes) = fetch_alpaca_content(
                    symbol, stats["rows"], spot, day, now_utc)
                content_kwargs = {"oi_by_occ": oi_map,
                                  "volume_by_occ": vol_map,
                                  "iv_by_occ": iv_map,
                                  "oi_date": oi_date,
                                  "content_meta": content_meta}
            except Exception as cexc:
                content_meta = {"error": f"{type(cexc).__name__}: {cexc}"}
            snap = build_snapshot_doc(symbol, day, spot, spot_source,
                                      stats["rows"], ts_utc, ts_et,
                                      spot_quote_ts=spot_ts,
                                      spot_freshness=spot_state,
                                      **content_kwargs)
            if "content" not in snap and content_meta is not None:
                snap["content"] = content_meta
            intra = os.path.join(CHAINS_DIR, symbol, "intraday",
                                 f"{stamp}.json.gz")
            nbytes, sha = atomic_write_gz(intra, snap)
            canonical = os.path.join(CHAINS_DIR, symbol, f"{day}.json.gz")
            nbytes, sha = atomic_write_gz(canonical, snap)
            iv_rows = 0
            if quotes:
                iv_rows = append_iv_ledger(symbol, day, ts_utc, spot,
                                           snap["rows"], quotes)
            cov = snap["field_coverage"]
            append_manifest(manifest_line(
                ts_utc, ts_et, symbol, "ok", stats=stats,
                nbytes=nbytes, sha256=sha, path=canonical,
                content={"with_oi": cov["with_oi"],
                         "with_volume": cov["with_volume"],
                         "with_iv_modelled": cov["with_iv"],
                         "oi_date": snap.get("oi_date"),
                         "iv_ledger_rows_added": iv_rows,
                         **({"error": content_meta["error"]}
                            if content_meta and "error" in content_meta
                            else {})}))
            print(f"{symbol}: ok expirations={stats['expirations']} "
                  f"strikes={stats['strikes']} "
                  f"contracts={stats['contracts']} bytes={nbytes} "
                  f"sha256={sha} -> {canonical} "
                  f"content oi={cov['with_oi']} vol={cov['with_volume']} "
                  f"iv_modelled={cov['with_iv']} iv_ledger+={iv_rows}")
        except Exception as exc:  # loud in the manifest, never silent
            failures += 1
            # IV loss accounting (IV-LEDGER-LOSS-20261031): a failed
            # capture adds no modelled IV ledger rows, and that loss
            # is recorded on the manifest line itself, in the same
            # content block shape the success path uses, so a zero
            # accrual capture (or day) is a named event in one file
            # instead of an inference across the manifest and the
            # ledger.
            append_manifest(manifest_line(
                ts_utc, ts_et, symbol, "error",
                error=f"{type(exc).__name__}: {exc}",
                content={"iv_ledger_rows_added": 0,
                         "iv_ledger_error":
                             f"{type(exc).__name__}: {exc}"}))
            print(f"{symbol}: ERROR {type(exc).__name__}: {exc}",
                  file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
