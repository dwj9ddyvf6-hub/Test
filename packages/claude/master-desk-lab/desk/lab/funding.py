"""CRY-E2a (AUDIT_CRY.md CRY-E2; exp1 item 6): Kraken's and the Binance-relayed funding signs side by side at each
Binance settlement, for the R19 crypto books' ADA and LINK. Logging only: nothing reads it but the lab's report.

  capture(root, now)  in the loop's pass (the decision tape's record(), desk/lab/quotes.py): Kraken's hourly funding
                      prints as the loop's own feed already holds them (desk/feedlib/kraken.py, read every pass by the
                      femto Kraken sleeves' feed kraken_funding:<PF_...>), persisted to state/lab/funding/kraken.json
                      (the last KEEP_PRINTS prints a perpetual) whenever a newer print is there. It fetches nothing and
                      imports nothing new: with no Kraken feed loaded in the process there is nothing to keep.
  pair(root, now)     in the nightly lab job, cache-only: each settlement the relay recorded
                      (cache/binance_funding_relay.json, desk/feedlib/binance_funding_relay.py: Binance's own rate,
                      relayed by CoinGecko, the interval's last estimate) beside the sum of Kraken's relative rates over
                      the same interval (the prints stamped after its start and at or before its settlement): one row a
                      settlement in state/lab/funding/signs.jsonl, written once. A settlement whose Kraken prints are
                      not all kept is logged with Kraken's sign None and why.
  report(rows)        per symbol: the agreement share and, beside, the share where |Binance| > 2e-5; descriptive until
                      40 settlements; then the pre-registered rule.
The sum of Kraken's 8 hourly relative rates standing for Binance's 8-hour rate is AUDIT_CRY's MODEL ASSUMPTION."""
import json
import os
import sys
from datetime import datetime

from ..util import read_json, write_json_atomic

KRAKEN = {"ADAUSDT": "PF_ADAUSD", "LINKUSDT": "PF_LINKUSD"}     # the R19 books' symbols with a Kraken perpetual
KEEP_PRINTS = 168                                              # a week of hourly prints
LARGE = 2e-5                                                   # the audit's "rate exceeds 2e-05 in size"
_SEEN = {}                                                     # this process's newest print kept, per perpetual

ARMS = {
    "cry_e2a_funding_signs": {
        "source": "AUDIT_CRY.md CRY-E2 (E2a: a monitor, no trading)",
        "changes": "nothing trades: at each Binance settlement of ADAUSDT and LINKUSDT the lab logs the relayed "
                   "Binance rate's sign beside the sign of the sum of Kraken's hourly relative funding rates over the "
                   "same interval (PF_ADAUSD, PF_LINKUSD)",
        "kept": "every R19 book and its relay, untouched; the Kraken prints are the loop's own feed's, kept as read",
        "expected": "agreement well above chance, especially when the Binance rate exceeds 2e-5 in size, if a "
                    "positioning signal shows across venues: a lawful fallback if the relay is refused (owner "
                    "decision D1)",
        "rival": "venue-specific premium noise near Binance's clamp threshold, where most ADA and LINK rates sit",
        "rejection": "reject the fallback, and treat the funding split as venue noise, if agreement is below 80% "
                     "over at least 40 settlements per symbol (pre-registered; MODEL ASSUMPTION: the sum of Kraken's "
                     "8 hourly relative rates stands for Binance's 8-hour interval)",
        "min_n": 40, "min_agreement": 0.80,
    },
}


def _dir(root):
    return os.path.join(root, "state", "lab", "funding")


def _stamp(text):
    return datetime.fromisoformat(str(text).replace("Z", "+00:00")).timestamp()


def capture(root, now):
    """persist the loop's Kraken prints when a newer one is there -> the number of perpetuals written"""
    mod = sys.modules.get("desk.feedlib.kraken")
    if mod is None:
        return 0
    with mod._LOCK:
        got = {p: list(c["rates"]) for p in KRAKEN.values()
               for c in [mod._FUNDING.get(p)] if c and c.get("ok") and c.get("rates")}
    fresh = {p: r for p, r in got.items() if _SEEN.get((root, p)) != r[-1].get("timestamp")}
    if not fresh:
        return 0
    path = os.path.join(_dir(root), "kraken.json")
    doc = read_json(path, {}) or {}
    n = 0
    for p, rates in fresh.items():
        _SEEN[(root, p)] = rates[-1].get("timestamp")
        if ((doc.get(p) or {}).get("rates") or [{}])[-1].get("timestamp") == rates[-1].get("timestamp"):
            continue
        doc[p] = {"at": float(now), "rates": rates[-KEEP_PRINTS:]}
        n += 1
    if n:
        os.makedirs(_dir(root), exist_ok=True)
        write_json_atomic(path, doc)
    return n


def read(root):
    """every logged settlement row"""
    try:
        with open(os.path.join(_dir(root), "signs.jsonl")) as f:
            return [json.loads(line) for line in f if line.strip()]
    except (OSError, ValueError):
        return []


def _sign(x):
    return 0 if x == 0 else (1 if x > 0 else -1)


def pair(root, now):
    """log each settled relay record not yet logged beside Kraken's sign over its interval -> the new rows"""
    relay = read_json(os.path.join(root, "cache", "binance_funding_relay.json"), {}) or {}
    kr = read_json(os.path.join(_dir(root), "kraken.json"), {}) or {}
    done = {(r["symbol"], r["settle_at"]) for r in read(root)}
    out = []
    for sym, perp in sorted(KRAKEN.items()):
        h = int((relay.get("intervals") or {}).get(sym) or 8)
        prints = []
        for p in (kr.get(perp) or {}).get("rates") or ():
            try:
                prints.append((_stamp(p["timestamp"]), float(p["relativeFundingRate"])))
            except (KeyError, TypeError, ValueError):
                continue
        newest = max((t for t, _ in prints), default=None)
        for rec in (relay.get("records") or {}).get(sym) or ():
            s = float(rec["settle_at"])
            if s > now or (sym, rec["settle_at"]) in done:
                continue
            if newest is not None and newest < s and now - s < KEEP_PRINTS * 3600:
                continue                                   # Kraken's prints reach it later: the next run logs it
            got = [x for t, x in prints if s - h * 3600 < t <= s]
            row = {"symbol": sym, "kraken": perp, "settle_at": rec["settle_at"], "interval_h": h,
                   "binance_rate": rec.get("rate"), "binance_sign": _sign(float(rec.get("rate") or 0.0)),
                   "binance_observed_at": rec.get("observed_at"), "kraken_prints": len(got)}
            if len(got) >= h:
                k = sum(got)
                row.update(kraken_sum=round(k, 12), kraken_sign=_sign(k), agree=_sign(k) == row["binance_sign"])
            else:
                row.update(kraken_sum=None, kraken_sign=None, agree=None,
                           why="%d of %d hourly prints kept" % (len(got), h))
            out.append(row)
    if out:
        os.makedirs(_dir(root), exist_ok=True)
        with open(os.path.join(_dir(root), "signs.jsonl"), "a") as f:
            f.write("".join(json.dumps(r, sort_keys=True) + "\n" for r in out))
    return out


def report(rows):
    c = ARMS["cry_e2a_funding_signs"]
    out = {"contract": dict(c), "logged": len(rows), "by_symbol": {}}
    for sym in sorted({r["symbol"] for r in rows}):
        rs = [r for r in rows if r["symbol"] == sym and r.get("agree") is not None]
        big = [r for r in rs if abs(float(r.get("binance_rate") or 0.0)) > LARGE]
        st = {"n": len(rs), "unpaired": sum(1 for r in rows if r["symbol"] == sym and r.get("agree") is None),
              "agreement": round(sum(1 for r in rs if r["agree"]) / len(rs), 4) if rs else None,
              "n_large": len(big),
              "agreement_large": round(sum(1 for r in big if r["agree"]) / len(big), 4) if big else None}
        if len(rs) < c["min_n"]:
            st["status"] = "descriptive"
            st["note"] = "descriptive until %d settlements (%d so far); no rule is applied before" % (c["min_n"],
                                                                                                    len(rs))
        else:
            st["status"] = "rejected" if st["agreement"] < c["min_agreement"] else "not_rejected"
        out["by_symbol"][sym] = st
    return out
