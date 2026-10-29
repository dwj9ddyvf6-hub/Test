"""The SEC cash-flow filing events and the fixed-relay / own-stock models the quant_research UIR and CRG rows run
(quant-research-backup@d170596b: R3 research-archives/2026-10-08-alpha-extraction-r3/events
EXECUTED_CONTIGUOUS_GUARD_PRODUCER.py and EVENT_ROWS.json; R8 research-archives/2026-10-08-ten-strategy-edge-research-r8
uir/run_experiments.py and crg/run_tests.py -- the lanes' executed free-data producers; vendored byte-exact under
desk/vendor/quant_research/r3/ and r8/).

Source events (R3 PREREGISTRATION): for CAT, DE and MSFT, the first current-vintage SEC accession per standalone
fiscal quarter, reconstructed CFO minus cash capex (NetCashProvidedByUsedInOperatingActivities and
PaymentsToAcquirePropertyPlantAndEquipment; year-to-date values less the previous quarter's as-of year-to-date), SEC
acceptance assumed public; the seasonal surprise = (this quarter - the prior-year same fiscal ordinal) / max(mean
absolute last 8 contiguous quarters, 1 USD), at least 4 contiguous prior quarters; the decision session = the first
NYSE close at or after acceptance, the trade the next open.
Rows: per event and receiver (UIR: CAT->DE, DE->CAT, MSFT->AAPL/AMZN/GOOGL/NVDA/AVGO/ORCL; CRG: the sender itself)
the six price features (sender / receiver decision-day and 20-session excess-SPY log returns, the receiver's
20-session volatility, the reaction discordance) and the receiver one-hot; labels the next-open to open-after-H
receiver return less the 50/50 QQQ/SPY return.
Models: monthly expanding ridge fits (training-only z-scores capped +-5, unpenalised intercept), labels ending before
the month's first session less a 21-session embargo, at least 24 source filings.
The account (R3 / R8): 95% gross, QQQ 47.5% / SPY 47.5% backbone; each active admitted receiver adds an equal share of
a sleeve min(45%, 15% x n) taken equally from the two benchmarks; a receiver stays active H sessions."""
import json
import math
import os
import time
from datetime import date, datetime, timedelta, timezone

import numpy as np

from ... import calendar as cal
from . import common as C

SENDERS = ("CAT", "DE", "MSFT")
EDGES = (("CAT", "DE"), ("DE", "CAT"), ("MSFT", "AAPL"), ("MSFT", "AMZN"), ("MSFT", "GOOGL"), ("MSFT", "NVDA"),
         ("MSFT", "AVGO"), ("MSFT", "ORCL"))
SYMBOLS = tuple(sorted(set(SENDERS) | {r for _, r in EDGES} | {"SPY", "QQQ"}))
ONEHOT = tuple(s for s in SYMBOLS if s not in ("SPY", "QQQ"))
CIK = {"CAT": "0000018230", "DE": "0000315189", "MSFT": "0000789019"}
CONCEPTS = {"cfo": "NetCashProvidedByUsedInOperatingActivities", "capex": "PaymentsToAcquirePropertyPlantAndEquipment"}
EPOCH = "2016-01-04"                    # the R2 panel's first session: decision indexes count from it
CACHE = "qr_relay_events.json"
VENDOR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "vendor",
                      "quant_research")
R3_ROWS = os.path.join(VENDOR, "r3", "events", "EVENT_ROWS.json")
_SESS = {}


# --------------------------------------------------------------------------------------------- sessions
def sessions(until=None):
    end = until or (date.today() + timedelta(days=400)).isoformat()
    if _SESS.get("end", "") < end:
        _SESS.update(end=end, days=C.sessions_between(EPOCH, end))
        _SESS["ix"] = {d: i for i, d in enumerate(_SESS["days"])}
    return _SESS["days"], _SESS["ix"]


def decision_session(accepted_utc):
    """the first NYSE close at or after the SEC acceptance."""
    t = datetime.fromisoformat(accepted_utc.replace("Z", "+00:00")).timestamp()
    d = cal._as_date(t)
    while not (C.is_session(d) and cal.session_close(d) >= t):
        d += timedelta(days=1)
    return d.isoformat()


# --------------------------------------------------------------------------------------------- source events
def quarter_versions(facts, accepted):
    """companyfacts (us-gaap) -> the earliest standalone-quarter versions [{quarter_start, quarter_end,
    fiscal_ordinal, cfo_usd, capex_usd, cfo_minus_capex_usd, label_available_utc, accn}] (R2's QUARTER_VERSIONS)."""
    gaap = (facts or {}).get("facts", {}).get("us-gaap", {})
    series = {}
    for key, concept in CONCEPTS.items():
        rows = ((gaap.get(concept) or {}).get("units") or {}).get("USD") or []
        series[key] = [r for r in rows if r.get("form") in ("10-Q", "10-K") and r.get("start") and r.get("end")]
    by_accn = {}
    for key, rows in series.items():
        for r in rows:
            by_accn.setdefault(r["accn"], {}).setdefault(key, []).append(r)
    reports = []
    for accn, got in by_accn.items():
        if set(got) != set(CONCEPTS) or accn not in accepted:
            continue
        end = max(r["end"] for r in got["cfo"])
        cur = {}
        for key in CONCEPTS:
            c = [r for r in got[key] if r["end"] == end]
            if not c:
                break
            r = min(c, key=lambda r: r["start"])                       # the year-to-date (longest) duration
            cur[key] = r
        if len(cur) != len(CONCEPTS):
            continue
        fp = cur["cfo"].get("fp")
        q = {"Q1": 1, "Q2": 2, "Q3": 3, "FY": 4}.get(fp)
        if q is None:
            continue
        reports.append({"accn": accn, "end": end, "start": cur["cfo"]["start"], "q": q, "fy": cur["cfo"].get("fy"),
                        "ytd": {k: float(cur[k]["val"]) for k in CONCEPTS}, "accepted": accepted[accn]})
    reports.sort(key=lambda r: (r["accepted"], r["accn"]))
    first, out = {}, []
    for r in reports:                                                     # the first accession per period end
        first.setdefault(r["end"], r)
    for end, r in sorted(first.items()):
        days = (date.fromisoformat(r["end"]) - date.fromisoformat(r["start"])).days
        if r["q"] == 1 and days <= 120:
            val = r["ytd"]
            qstart = r["start"]
        else:
            prev = [p for p in first.values() if p["start"] == r["start"] and p["end"] < r["end"]
                    and p["accepted"] <= r["accepted"]]
            if not prev:
                continue
            p = max(prev, key=lambda p: p["end"])
            val = {k: r["ytd"][k] - p["ytd"][k] for k in CONCEPTS}
            qstart = (date.fromisoformat(p["end"]) + timedelta(days=1)).isoformat()
        out.append({"quarter_start": qstart, "quarter_end": end, "fiscal_ordinal": r["q"], "cfo_usd": val["cfo"],
                    "capex_usd": val["capex"], "cfo_minus_capex_usd": val["cfo"] - val["capex"],
                    "label_available_utc": r["accepted"], "independent_current_accession": r["accn"],
                    "source_refs_sha256": r["accn"]})
    return out


def _ts(value):
    r = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if r.tzinfo is None:
        raise ValueError("Naive source availability")
    return r.astimezone(timezone.utc)


def surprise(row, prior):
    """R3 surprise(): an accession-linked seasonal reconstruction (restated as written)."""
    prior = [r for r in prior if _ts(r["label_available_utc"]) <= _ts(row["label_available_utc"])
             and r["quarter_end"] < row["quarter_end"]]
    prior = sorted(prior, key=lambda r: r["quarter_end"])
    suffix, next_row = [], row
    for previous in reversed(prior):
        contiguous = (date.fromisoformat(previous["quarter_end"]) + timedelta(days=1) ==
                      date.fromisoformat(next_row["quarter_start"])
                      and next_row["fiscal_ordinal"] == previous["fiscal_ordinal"] % 4 + 1)
        if not contiguous:
            break
        suffix.append(previous)
        next_row = previous
    prior = list(reversed(suffix))
    if len(prior) < 4:
        raise ValueError("LESS_THAN_FOUR_CONTIGUOUS_PRIOR_QUARTERS")
    seasonal = [r for r in prior if r["fiscal_ordinal"] == row["fiscal_ordinal"]
                and 230 <= (date.fromisoformat(row["quarter_end"]) - date.fromisoformat(r["quarter_end"])).days <= 500]
    if not seasonal:
        raise ValueError("PRIOR_YEAR_SAME_ORDINAL_MISSING")
    baseline = max(seasonal, key=lambda r: r["quarter_end"])
    scale = max(float(np.mean([abs(r["cfo_minus_capex_usd"]) for r in prior[-8:]])), 1.)
    return float((row["cfo_minus_capex_usd"] - baseline["cfo_minus_capex_usd"]) / scale)


def source_events(versions_by_sender):
    """[{source_id, sender, accepted_utc, quarter_end, surprise, decision_date}] (R3 load_sources' events)."""
    out = []
    for sender, versions in versions_by_sender.items():
        quarters = sorted(versions, key=lambda r: r["quarter_end"])
        for i, row in enumerate(quarters):
            try:
                value = surprise(row, quarters[:i])
            except ValueError:
                continue
            out.append({"source_id": f"{sender}|{row['independent_current_accession']}|{row['quarter_end']}",
                        "sender": sender, "accepted_utc": row["label_available_utc"], "quarter_end": row["quarter_end"],
                        "fiscal_ordinal": row["fiscal_ordinal"], "accession": row["independent_current_accession"],
                        "surprise": value, "decision_date": decision_session(row["label_available_utc"])})
    return sorted(out, key=lambda r: (r["decision_date"], r["source_id"]))


def run(root, now, fetch=None):
    """the job `qr_relay`: SEC companyfacts + filing acceptances of the senders -> cache/qr_relay_events.json."""
    from ...data.http import get
    from ...feedlib.edgar_buyback import user_agent
    fetch = fetch or (lambda url: get(url, headers={"User-Agent": user_agent()}, timeout=60))
    versions = {}
    for s in SENDERS:
        facts = fetch(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{CIK[s]}.json")
        sub = fetch(f"https://data.sec.gov/submissions/CIK{CIK[s]}.json")
        rec = (sub or {}).get("filings", {}).get("recent", {})
        accepted = {}
        for a, t, f in zip(rec.get("accessionNumber", []), rec.get("acceptanceDateTime", []), rec.get("form", [])):
            if f in ("10-Q", "10-K"):
                accepted[a] = t.replace(".000Z", "+00:00").replace("Z", "+00:00")
        for page in (sub or {}).get("filings", {}).get("files", []):
            older = fetch("https://data.sec.gov/submissions/" + page["name"])
            for a, t, f in zip(older.get("accessionNumber", []), older.get("acceptanceDateTime", []),
                               older.get("form", [])):
                if f in ("10-Q", "10-K"):
                    accepted[a] = t.replace(".000Z", "+00:00").replace("Z", "+00:00")
        versions[s] = quarter_versions(facts, accepted)
    ev = source_events(versions)
    p = os.path.join(root, "cache", CACHE)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p + ".tmp", "w") as f:
        json.dump({"events": ev, "computed_at": now, "versions": {s: len(v) for s, v in versions.items()}}, f)
    os.replace(p + ".tmp", p)
    return {"events": len(ev), "latest": ev[-1]["decision_date"] if ev else None}


def read_events(root):
    try:
        return (json.load(open(os.path.join(root, "cache", CACHE))) or {}).get("events") or []
    except (OSError, ValueError, TypeError):
        return []


def feed_events(f, s, now, arg):
    root = getattr(getattr(s, "engine", None), "root", None)
    return {"events": read_events(root)} if root else None


# --------------------------------------------------------------------------------------------- rows and models
def history_rows(family):
    if "rows" not in _SESS:
        _SESS["rows"] = json.load(open(R3_ROWS))
    return [r for r in _SESS["rows"] if r["family"] == family]


def price_features(closes, j, sender, receiver):
    """R3 price_features: closes {sym: {session index: close}} (all-adjusted)."""
    def close(k, s):
        return closes[s][k]

    def excess(a, b, s):
        return math.log(close(b, s) / close(a, s)) - math.log(close(b, "SPY") / close(a, "SPY"))
    sr, rr = excess(j - 1, j, sender), excess(j - 1, j, receiver)
    vol = float(np.std([math.log(close(k, receiver) / close(k - 1, receiver)) for k in range(j - 19, j + 1)], ddof=1))
    return [float(sr), float(rr), float(excess(j - 20, j, sender)), float(excess(j - 20, j, receiver)), vol,
            float(sr - rr)]


def onehot(receiver):
    return [float(receiver == s) for s in ONEHOT]


def fit(rows, key, ridge, feats=None):
    """R3 fit_ridge / R8 fit: training-only standardisation capped at +-5, ridge with an unpenalised intercept."""
    x = np.array([feats(r) if feats else r[key] for r in rows], float)
    y = np.array([r["target"] for r in rows], float)
    mu = x.mean(0)
    scale = x.std(0)
    scale[scale < 1e-12] = 1.
    z = np.c_[np.ones(len(x)), np.clip((x - mu) / scale, -5, 5)]
    pen = np.eye(z.shape[1]) * ridge
    pen[0, 0] = 0
    coef = np.linalg.solve(z.T @ z + pen, z.T @ y)
    return {"mu": mu.tolist(), "scale": scale.tolist(), "coef": coef.tolist(),
            "latest_label_exit_index": max(r["label_exit_index"] for r in rows)}


def predict(m, x):
    return float(np.r_[1, np.clip((np.array(x) - m["mu"]) / m["scale"], -5, 5)] @ m["coef"])


def month_cutoff(month):
    days, ix = sessions()
    first = next(d for d in days if d.startswith(month))
    return ix[first]


def basket(active):
    """the R3 / R8 funded account's weights for the active receivers."""
    n = len(active)
    sleeve = min(.45, .15 * n)
    w = {"SPY": (.95 - sleeve) / 2, "QQQ": (.95 - sleeve) / 2}
    if n:
        w.update({s: sleeve / n for s in sorted(active)})
    return w


def closes_from_frames(frames):
    """{sym: {session index: close}} from hub daily frames (all-adjusted closes)."""
    days, ix = sessions()
    out = {}
    for s, f in frames.items():
        out[s] = {ix[d.date().isoformat()]: float(c) for d, c in zip(f.index, f["c"]) if d.date().isoformat() in ix}
    return out


def live_rows(events, closes, family, horizon):
    """rows for the decision events whose features the closes cover (labels unknown)."""
    days, ix = sessions()
    out = []
    for e in events:
        j = ix.get(e["decision_date"])
        if j is None:
            continue
        receivers = [e["sender"]] if family == "CRG_own_stock" else [r for s, r in EDGES if s == e["sender"]]
        for rcv in receivers:
            try:
                p = price_features(closes, j, e["sender"], rcv)
            except (KeyError, ValueError, ZeroDivisionError):
                continue
            out.append({"source_id": e["source_id"], "sender": e["sender"], "receiver": rcv, "family": family,
                        "decision_date": e["decision_date"], "decision_index": j, "horizon": horizon,
                        "label_exit_index": j + 1 + horizon, "x_price": p + onehot(rcv),
                        "financial_surprise": float(e["surprise"])})
    return out


def label(opens, row):
    """R3's target: the receiver's next-open to open-after-H return less the 50/50 QQQ/SPY one (None until known)."""
    a, b = row["decision_index"] + 1, row["decision_index"] + 1 + row["horizon"]
    try:
        stock = opens[row["receiver"]][b] / opens[row["receiver"]][a] - 1
        bench = np.mean([opens[s][b] / opens[s][a] - 1 for s in ("SPY", "QQQ")])
    except KeyError:
        return None
    return float(stock - bench)


def priors(rows_hist, events):
    """{sender: [(decision_date, surprise)] ascending}: the R3 history rows' recorded surprises up to their last
    decision date, the live events after it."""
    seen = {}
    for r in rows_hist:
        seen[r["source_id"]] = (r["sender"], r["decision_date"], float(r["financial_surprise"]))
    seam = max(v[1] for v in seen.values()) if seen else ""
    allv = list(seen.values()) + [(e["sender"], e["decision_date"], float(e["surprise"])) for e in events or []
                                  if e["decision_date"] > seam]
    out = {}
    for s, d, v in sorted(allv, key=lambda x: (x[1], x[0])):
        out.setdefault(s, []).append((d, v))
    return out


# --------------------------------------------------------------------------------------------- the sleeve
from ...contract import Sleeve, SleeveConfig  # noqa: E402


class RelayBook(Sleeve):
    """a monthly-refit ridge policy over the filing events, traded through the R3 / R8 funded account."""
    SID, FAMILY_ROWS, POLICY, SOURCE = "", "", "", {}
    HORIZON, THRESHOLD, RIDGE, MIN_SOURCES = 20, 0.003, 10.0, 24

    def __init__(self):
        self.engine = None
        self.CONFIG = SleeveConfig(
            sleeve_id=self.SID, family="quant_research", cadence_s=300, universe=SYMBOLS, capital=1_000_000.0,
            schedule="rth",
            needs={"feeds": ["qr_relay"], "quotes": {"source": "equity", "symbols": list(SYMBOLS)},
                   "bars": [{"source": "equity", "interval": "1d", "n": 120, "symbols": list(SYMBOLS),
                             "key": "relay"}]},
            params={"policy": self.POLICY, "horizon": self.HORIZON, "threshold": self.THRESHOLD, "ridge": self.RIDGE,
                    "senders": list(SENDERS), "edges": [list(e) for e in EDGES], "min_sources": self.MIN_SOURCES,
                    "account": "95% gross, QQQ/SPY backbone, 15% per active name, sleeve <= 45%"},
            source=self.SOURCE, state_schema={"active": "dict", "decided": "str", "target": "dict",
                                              "sized": "dict|None", "log": "list"})   # None: decided, not yet sized

    def bind(self, engine):
        self.engine = engine

    def features(self, row, prior):
        """the policy's feature vector for a row; prior = the sender's strictly earlier surprises."""
        raise NotImplementedError

    def hist(self):
        return [r for r in history_rows(self.FAMILY_ROWS) if r["horizon"] == self.HORIZON]

    def training(self, events, closes, opens, cutoff):
        hist = self.hist()
        seam = max(r["decision_date"] for r in hist)
        live = live_rows([e for e in events if e["decision_date"] > seam], closes, self.FAMILY_ROWS, self.HORIZON)
        for r in live:
            r["target"] = label(opens, r)
        rows = hist + [r for r in live if r["target"] is not None]
        return [r for r in rows if r["label_exit_index"] < cutoff - 21]

    def score(self, rows, cand, events):
        """the month's fit on `rows` and its predictions for `cand` (R8's monthly forecasts)."""
        pri = priors(history_rows(self.FAMILY_ROWS), events)

        def before(r):
            return [v for d, v in pri.get(r["sender"], []) if d < r["decision_date"]]
        model = fit(rows, None, self.RIDGE, feats=lambda r: self.features(r, before(r)))
        return [(r, predict(model, self.features(r, before(r)))) for r in cand]

    def signal(self, view):
        st = dict(view.state or {})
        for k, v in (("active", {}), ("log", [])):
            st.setdefault(k, v)
        self._st = st
        now, day = float(view.now), view.session
        if not (cal.is_rth(now) and C.is_session(day)):
            return []
        days, ix = sessions()
        i = ix.get(day)
        if not i:
            return []
        d = days[i - 1]                                            # the decision close today's open trades on
        if st.get("decided") != d:
            evs = ((view.extra or {}).get("qr_relay") or {}).get("events")
            frames = {}
            for s, bl in ((view.extra or {}).get("bars_relay") or {}).items():
                f = C.frame(bl)
                if f is not None:
                    frames[s] = f
            if evs is None or any(s not in frames for s in SYMBOLS):
                st["log"] = (st["log"] + [{"at": day, "why": "events or bars pending"}])[-50:]
                return []
            closes = closes_from_frames(frames)
            opens = {s: {ix[t.date().isoformat()]: float(o) for t, o in zip(f.index, f["o"])
                         if t.date().isoformat() in ix} for s, f in frames.items()}
            last = st.get("decided") or days[max(0, i - 6)]
            for e in sorted((e for e in evs if last < e["decision_date"] <= d),
                            key=lambda e: (e["decision_date"], e["source_id"])):
                j = ix[e["decision_date"]]
                rows = self.training(evs, closes, opens, month_cutoff(e["decision_date"][:7]))
                if len({r["source_id"] for r in rows}) < self.MIN_SOURCES:
                    st["log"] = (st["log"] + [{"at": e["decision_date"], "why": "fewer than 24 mature sources"}])[-50:]
                    continue
                preds = self.score(rows, live_rows([e], closes, self.FAMILY_ROWS, self.HORIZON), evs)
                for r, v in preds:
                    if v > self.THRESHOLD:
                        st["active"][r["receiver"]] = {"expires": j + self.HORIZON, "source_id": e["source_id"]}
                st["log"] = (st["log"] + [{"at": e["decision_date"], "event": e["source_id"],
                                           "pred": {r["receiver"]: round(v, 5) for r, v in preds}}])[-50:]
            st["active"] = {s: v for s, v in st["active"].items() if v["expires"] > i - 1}
            st["decided"] = d
            st["target"] = basket(st["active"])
            st["sized"] = None
        if not st.get("sized"):
            t = C.target_shares(view, st["target"])
            if t is None:
                return []
            st["sized"] = t
        out, _ = C.rebalance(view, st["sized"], f"{self.SID}:{d}", f"{self.SID} {self.POLICY} basket")
        return out

    def update_state(self, view, intents):
        return getattr(self, "_st", None) or dict(view.state or {})
