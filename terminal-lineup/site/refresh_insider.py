#!/usr/bin/env python3
"""Refresh the Insider Wire data file.

Register triple (the adopted spec format for lineup builds, written
before this build started):
Standing rule: NO DISCLAIMER COPY (the owner, 2026-10-28): no
disclaimer-style copy on any reader surface of any tool, in pages or
generated data, ever.

Evidence class: the insider section of the institutional bundle and
its provenance, cross-checked against the gathered transaction
entries the bundle was built from, and (since the RC-16 cure,
2026-10-30) against the per-trade row store built by the widened
gathering (morgue/insider_gather.py) from the same Form 4
documents, which the gathering now caches on disk. Four carriers
of the same figures for the board names: the bundle (a per-name
insider reading out of 100, or none), the provenance (per name,
the count of open-market buys and sells combined and the latest
filing date), the gathered entries themselves, and the per-trade
store rows (insider, role, transaction date, code, shares, price
per trade). Every published figure is recomputed from the entries
and must match the other carriers exactly, or the refresh stops.

Reconstruction choices: buys and sells are the open-market entries
only (purchase and sale codes), the same split the bundle's own
scoring code uses, and the gathering code is opened and checked for
that split, for its window (filings filed in the 183 days before the
gathering date) and for its per-name filing limit (the 20 most
recent filings) before anything is published, so the window printed
on the page is the window the code actually used. Dollar totals are
shares times price, summed per side. The reading out of 100 is the
bundle's own recorded reading for board names, republished only
after the recomputed reading matches it; for the widened names the
reading is computed by the same formula from their store rows.
Entries that are not open-market buys or sells (grants, option
exercises and the like) are counted only in the all-entries total,
never as buys or sells.

Per-trade record and cluster buying (RC-16 cure): the store rows
are published per name, so who traded, their role, the day and the
size of each trade are on the page. Cluster buying is checked on
that record under the declared rule the gathering publishes: at
least 3 distinct insiders making open-market purchases inside some
30-day window, counting by transaction date. Every name with a
record is checked; the page names the flagged names, or states
that the check ran and flagged none.

Non-claims: a name the lookup could not match carries no insider
record and is shown in that plain state, never as a zero. The
widened names beyond the board carry no bundle reading; their
reading is computed from their own rows by the same formula and
is labelled by the same rules.

Fail-closed rules: if the bundle, the provenance, the gathered
entries and the store disagree on any board name's count, latest
filing date, reading or per-trade rows; if a name appears in one
carrier and not another; if the gathered entries for the gathering
date are missing or ambiguous; if the per-trade store is missing,
stale against the gathering date, or not at per-trade grain; or if
the gathering or scoring code no longer carries the window, filing
limit or open-market split this page publishes, the refresh stops
and publishes nothing.

Honesty rules:
- Dates are read off the sources, never from the clock. All dates
  come from the sources, so running this script twice produces the
  same file.
- No percentages are computed from these counts: many names rest on
  few trades, so the page shows counts and dollar totals only (the
  thin-cell rule).

Usage: python3 refresh_insider.py
"""

import glob
import json
import os
import sys
from datetime import date, timedelta

try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE_DIR = os.path.expanduser("~/workspace/morgue/output")
CACHE_DIR = os.path.expanduser("~/workspace/morgue/data_cache/edgar")
BUNDLE_PATH = os.path.join(SOURCE_DIR, "inst_bundle.json")
PROV_PATH = os.path.join(SOURCE_DIR, "inst_bundle_provenance.json")
STORE_PATH = os.path.join(SOURCE_DIR, "insider_trades.json")
BUNDLE_CODE = os.path.expanduser("~/workspace/morgue/inst_bundle.py")
SCORE_CODE = os.path.expanduser("~/workspace/morgue/inst_edgar.py")
OUT_PATH = os.path.join(HERE, "insider-wire", "data.json")

WINDOW_DAYS = 183
FILING_LIMIT = 20

SOURCE_WORDS = ("Company ownership filings: the reports company "
                "officers and directors file with the Securities "
                "and Exchange Commission when their holdings change")
SUMMARY_WORDS = ("These summaries are built from the individual "
                 "trades on record, and the trades themselves are "
                 "listed under each name: who traded, their role, "
                 "the day, and the size of each trade.")
READING_WORDS = ("The reading out of 100 weighs the dollars bought "
                 "against the dollars sold in the open market: 50 "
                 "means the two sides balanced, higher means more "
                 "buying dollars, lower means more selling dollars. "
                 "It is shown only where at least two open-market "
                 "buys or sells are on record.")
CLUSTER_RULE_WORDS = ("Cluster buying means at least 3 different "
                      "insiders buying in the open market inside "
                      "some 30-day window, counting by the day of "
                      "each trade. Every name on record was checked "
                      "against that rule.")


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def fail(message):
    print(f"Insider Wire refresh: {message}", file=sys.stderr)
    return 1


def lin(x):
    return max(0.0, min(100.0, (x + 1.0) / 2.0 * 100.0))


def summarise_rows(rows):
    """The published summary for one name, computed from its
    per-trade rows (the same split and reading formula the bundle
    uses for the board names)."""
    open_mkt = [r for r in rows if r["code"] in ("P", "S")]
    buys = [r for r in open_mkt if r["code"] == "P"]
    sells = [r for r in open_mkt if r["code"] == "S"]
    buy_value = sum(r["shares"] * r["price"] for r in buys)
    sell_value = sum(r["shares"] * r["price"] for r in sells)
    if len(open_mkt) < 2 or (buy_value + sell_value) == 0:
        reading = None
    else:
        reading = lin((buy_value - sell_value)
                      / (buy_value + sell_value))
    return {
        "buys": {"count": len(buys),
                 "value_usd": round(buy_value, 2)},
        "sells": {"count": len(sells),
                  "value_usd": round(sell_value, 2)},
        "open_transactions": len(open_mkt),
        "all_entries": len(rows),
        "reading": reading,
    }


def rows_match(seed_txns, store_rows):
    """True when the store rows for a board name are exactly the
    gathered entries the bundle was built from, trade for trade."""
    def key(t):
        return (t.get("date"), t.get("insider"), t.get("code"),
                t.get("shares"), t.get("price"))
    return sorted(map(key, seed_txns), key=repr) == \
        sorted(map(key, store_rows), key=repr)


def cluster_words(flagged, checked):
    if flagged:
        return (f"Cluster buying was checked on all {checked} names "
                f"on record and flagged {len(flagged)}: "
                + ", ".join(flagged) + ". " + CLUSTER_RULE_WORDS)
    return (f"No name is flagged for cluster buying. Cluster buying "
            f"was checked on all {checked} names on record and none "
            f"met the rule. " + CLUSTER_RULE_WORDS)


def build():
    for path in (BUNDLE_PATH, PROV_PATH, BUNDLE_CODE, SCORE_CODE,
                 STORE_PATH):
        if not os.path.exists(path):
            return fail(f"source not found: {path}")

    # --- The window, filing limit and split, read from the code. ---
    with open(BUNDLE_CODE, "r", encoding="utf-8") as fh:
        bundle_code = fh.read()
    if "timedelta(days=183)" not in bundle_code:
        return fail("the gathering code no longer carries the "
                    "183-day filing window this page publishes; "
                    "refusing to publish a window the code does "
                    "not hold.")
    with open(SCORE_CODE, "r", encoding="utf-8") as fh:
        score_code = fh.read()
    if "limit: int = 20" not in score_code:
        return fail("the gathering code no longer carries the "
                    "20-filing limit this page publishes; refusing "
                    "to publish a limit the code does not hold.")
    if 't["code"] in ("P", "S")' not in score_code:
        return fail("the scoring code no longer splits open-market "
                    "buys and sells by the purchase and sale codes "
                    "this page publishes; refusing to guess.")

    bundle = load_json(BUNDLE_PATH)
    prov = load_json(PROV_PATH)
    meta = prov.get("_meta") or {}
    as_of = meta.get("as_of")
    if not as_of or meta.get("symbols") != len(bundle):
        return fail("the provenance carries no usable gathering "
                    "date or name count; refusing to guess.")
    names = sorted(bundle.keys())
    prov_names = sorted(k for k in prov.keys() if k != "_meta")
    if prov_names != names:
        return fail("the provenance and the bundle name different "
                    "sets of names; refusing to publish a "
                    "mismatched page.")

    # --- The per-trade store for exactly the gathering date. ---
    store = load_json(STORE_PATH)
    if store.get("grain") != "per_trade" \
            or store.get("as_of") != as_of:
        return fail(f"the per-trade store is at grain "
                    f"{store.get('grain')} dated "
                    f"{store.get('as_of')}, not per_trade dated "
                    f"{as_of}; refusing to publish a store that "
                    "does not match the gathering.")
    store_names = {n["symbol"]: n for n in store.get("names") or []}
    store_rows = {}
    for row in store.get("rows") or []:
        store_rows.setdefault(row["symbol"], []).append(row)
    for sym in names:
        if sym not in store_names:
            return fail(f"{sym}: the bundle carries this name but "
                        "the per-trade store does not; refusing to "
                        "publish a one-sided page.")

    # --- The gathered entries for exactly the gathering date. ---
    seed_paths = sorted(glob.glob(os.path.join(
        CACHE_DIR, f"seed_{as_of}.json")))
    if len(seed_paths) != 1:
        return fail(f"expected exactly one gathered-entries record "
                    f"dated {as_of}, found {len(seed_paths)}; "
                    "refusing to guess which one the bundle was "
                    "built from.")
    seed = load_json(seed_paths[0])
    if sorted(seed.keys()) != names:
        return fail("the gathered entries name a different set of "
                    "names than the bundle; refusing to publish a "
                    "mismatched page.")

    window_start = (date.fromisoformat(as_of)
                    - timedelta(days=WINDOW_DAYS)).isoformat()

    out_names = []
    totals = {"names_covered": len(names), "names_with_summary": 0,
              "names_not_on_record": 0, "open_buys": 0,
              "open_sells": 0, "open_transactions": 0,
              "names_in_store": len(store_names),
              "names_widened": 0, "per_trade_rows": 0,
              "clusters_flagged": 0, "names_cluster_checked": 0}
    flagged = []
    for sym in names:
        p = prov[sym]
        s = seed[sym]
        recorded_reading = bundle[sym].get("insiderActivity")
        if "insider" not in p:
            # No insider record: both other carriers must agree the
            # lookup failed, and the bundle must carry no reading.
            err = ((p.get("errors") or {}).get("edgar") or "")
            if "no CIK match" not in err \
                    or "no CIK match" not in (s.get("error") or "") \
                    or recorded_reading is not None:
                return fail(f"{sym}: the provenance carries no "
                            "insider record, but the other records "
                            "do not agree that the name could not "
                            "be matched; refusing to publish.")
            if store_names[sym].get("state") != "not_on_record":
                return fail(f"{sym}: the provenance carries no "
                            "insider record but the per-trade store "
                            "carries one; refusing to publish a "
                            "mismatched page.")
            totals["names_not_on_record"] += 1
            out_names.append({
                "symbol": sym, "state": "not_on_record",
                "summary": None, "trades": [], "cluster": None})
            continue
        if "error" in s or "transactions" not in s:
            return fail(f"{sym}: the provenance carries an insider "
                        "record but the gathered entries do not; "
                        "refusing to publish a one-sided page.")
        txns = s["transactions"]
        if any("insider" not in t or "date" not in t for t in txns):
            return fail(f"{sym}: the gathered entries are not at "
                        "per-trade grain (no insider or transaction "
                        "date); the gathering must re-run before "
                        "this page can publish the per-trade record.")
        rows = store_rows.get(sym) or []
        if not rows_match(txns, rows):
            return fail(f"{sym}: the per-trade store rows do not "
                        "match the gathered entries trade for "
                        "trade; refusing to publish a mismatched "
                        "page.")
        open_mkt = [t for t in txns if t["code"] in ("P", "S")]
        buys = [t for t in open_mkt if t["code"] == "P"]
        sells = [t for t in open_mkt if t["code"] == "S"]
        buy_value = sum(t["shares"] * t["price"] for t in buys)
        sell_value = sum(t["shares"] * t["price"] for t in sells)
        if len(open_mkt) != p["insider"]["n_transactions"]:
            return fail(f"{sym}: the provenance counts "
                        f"{p['insider']['n_transactions']} "
                        f"open-market trades but the gathered "
                        f"entries carry {len(open_mkt)}; refusing "
                        "to publish a mismatched page.")
        if s.get("latest_filing_date") \
                != p["insider"]["latest_filing_date"]:
            return fail(f"{sym}: the provenance's latest filing "
                        f"date {p['insider']['latest_filing_date']} "
                        f"does not match the gathered entries' "
                        f"{s.get('latest_filing_date')}; refusing "
                        "to publish a mismatched page.")
        if len(open_mkt) < 2 or (buy_value + sell_value) == 0:
            reading = None
        else:
            reading = lin((buy_value - sell_value)
                          / (buy_value + sell_value))
        if (reading is None) != (recorded_reading is None) or (
                reading is not None
                and abs(reading - recorded_reading) > 1e-6):
            return fail(f"{sym}: the reading recomputed from the "
                        f"gathered entries ({reading}) does not "
                        f"match the bundle's recorded reading "
                        f"({recorded_reading}); refusing to publish "
                        "a mismatched page.")
        cluster = store_names[sym].get("cluster")
        if not cluster or "state" not in cluster:
            return fail(f"{sym}: the per-trade store carries no "
                        "cluster check for this name; refusing to "
                        "publish an unchecked record.")
        totals["names_with_summary"] += 1
        totals["open_buys"] += len(buys)
        totals["open_sells"] += len(sells)
        totals["open_transactions"] += len(open_mkt)
        totals["per_trade_rows"] += len(rows)
        totals["names_cluster_checked"] += 1
        if cluster["state"] == "cluster_buying":
            totals["clusters_flagged"] += 1
            flagged.append(sym)
        out_names.append({
            "symbol": sym, "state": "summary",
            "summary": {
                "buys": {"count": len(buys),
                         "value_usd": round(buy_value, 2)},
                "sells": {"count": len(sells),
                          "value_usd": round(sell_value, 2)},
                "open_transactions": len(open_mkt),
                "all_entries": len(txns),
                "latest_filing_date":
                    p["insider"]["latest_filing_date"],
                "reading_out_of_100":
                    (round(reading, 1) if reading is not None
                     else None),
            },
            "trades": sorted(rows, key=lambda r: r["date"] or "",
                              reverse=True),
            "cluster": cluster})

    # --- The widened names: store only, summarised from rows. ---
    board_set = set(names)
    for sym in sorted(store_names):
        if sym in board_set:
            continue
        totals["names_widened"] += 1
        entry = store_names[sym]
        if entry.get("state") != "record":
            totals["names_not_on_record"] += 1
            out_names.append({
                "symbol": sym, "state": "not_on_record",
                "summary": None, "trades": [], "cluster": None})
            continue
        rows = store_rows.get(sym) or []
        if len(rows) != entry.get("rows"):
            return fail(f"{sym}: the per-trade store counts "
                        f"{entry.get('rows')} rows for this widened "
                        f"name but carries {len(rows)}; refusing to "
                        "publish a mismatched page.")
        summ = summarise_rows(rows)
        cluster = entry.get("cluster")
        if not cluster or "state" not in cluster:
            return fail(f"{sym}: the per-trade store carries no "
                        "cluster check for this widened name; "
                        "refusing to publish an unchecked record.")
        totals["names_with_summary"] += 1
        totals["open_buys"] += summ["buys"]["count"]
        totals["open_sells"] += summ["sells"]["count"]
        totals["open_transactions"] += summ["open_transactions"]
        totals["per_trade_rows"] += len(rows)
        totals["names_cluster_checked"] += 1
        if cluster["state"] == "cluster_buying":
            totals["clusters_flagged"] += 1
            flagged.append(sym)
        out_names.append({
            "symbol": sym, "state": "summary",
            "summary": {
                "buys": summ["buys"], "sells": summ["sells"],
                "open_transactions": summ["open_transactions"],
                "all_entries": summ["all_entries"],
                "latest_filing_date": entry.get("latest_filing_date"),
                "reading_out_of_100":
                    (round(summ["reading"], 1)
                     if summ["reading"] is not None else None),
            },
            "trades": sorted(rows, key=lambda r: r["date"] or "",
                              reverse=True),
            "cluster": cluster})

    flagged = sorted(flagged)
    # names_covered counts the names this page publishes (board
    # plus widened); the RC-16 widening grew the published set
    # without moving this total, and every consumer recount
    # refused the record (engine refresh cure, 2026-10-30).
    totals["names_covered"] = len(out_names)
    cluster_note = cluster_words(flagged, totals["names_cluster_checked"])
    coverage = (f"{totals['names_with_summary']} of the "
                f"{totals['names_in_store']} names checked carry an "
                f"insider record with its individual trades listed; "
                f"the other {totals['names_not_on_record']} could "
                "not be matched to a company record, so they carry "
                "no insider record. The checked names are the "
                f"{len(names)} board names plus "
                f"{totals['names_widened']} more from the full board.")

    data = {
        "tool": "Insider Wire",
        "as_of": as_of,
        "window_start": window_start,
        "window": ("Filings filed in the six months before the "
                   "gathering date, up to the 20 most recent filings "
                   "per name"),
        "source": SOURCE_WORDS,
        "summary_note": SUMMARY_WORDS,
        "cluster_note": cluster_note,
        "cluster_flagged": flagged,
        "reading_note": READING_WORDS,
        "coverage": coverage,
        "totals": totals,
        "names": out_names,
        "receipt": {
            "gathered": as_of,
            "window_start": window_start,
            "window": ("Filings filed in the six months before the "
                       "gathering date, up to the 20 most recent "
                       "filings per name"),
            "source": SOURCE_WORDS,
            "coverage": coverage,
        },
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"Wrote {OUT_PATH} ({totals['names_with_summary']} names "
          f"with an insider record, {totals['per_trade_rows']} "
          f"per-trade rows, {totals['open_buys']} buys and "
          f"{totals['open_sells']} sells kept separate, "
          f"{totals['clusters_flagged']} names flagged for cluster "
          f"buying of {totals['names_cluster_checked']} checked, "
          f"{totals['names_not_on_record']} names not on record, "
          f"gathered {as_of}, window from {window_start})")
    return 0


if __name__ == "__main__":
    sys.exit(build())
