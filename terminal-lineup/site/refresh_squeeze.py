#!/usr/bin/env python3
"""Refresh the Squeeze Watch data file.

Register triple (the adopted spec format for lineup builds, written
before this build started):

Evidence class: the real short-interest readings on record: a
point-in-time file of settlement readings (shares sold short and
shares outstanding per name, per settlement date, with the
publication date of each reading), cross-checked against the
provenance record of the same gathering (which carries, per name,
the same settlement date, the short interest share recomputed from
its own figures, and the days to cover the gathering reported).
Two further records bound what this page may claim: the published
squeeze pane in the studies card and in the published feed (both
carry the same empty state and the same vendor figures), and the
published feed's short-volume lane stamp (which states plainly
the daily short-volume store's real day count and range).

Reconstruction choices, stated as ours: (1) The published squeeze
score is NOT computed here. Its formula ranks names by percentiles
inside the set of names that pass its gate, and on the data on
record that set holds 2 names; a percentile rank of 2 names
against each other is not the published cross-section, so this
page is a watch list, not a ranked score list, and no score is
shown. (2) A name is flagged only for the one part of the
published gate the readings themselves decide: short interest at
or above 15% of the shares outstanding, and not above 120% (the
formula treats anything above 120% as a data error). The flag
says "above the 15% bar" and nothing more; the gate's price and
volume tests are not assembled on record and are not claimed.
(3) Short interest change is shown only for the names that carry
readings at both settlements on record, and it is the change in
shares sold short between those two settlements; names with one
reading show a plain not-on-record state for the change, never a
zero. (4) Coverage is counted against the names the gatherings
covered: the readings file is cumulative across gathers and the
gathering's board rotates, so the page lists every name with a
reading at the freshest settlement that at least one current
record still carries, each cross-checked against whichever
record carries it (the latest gathering record, the
short-interest store, or both, which must agree where they
overlap). A name no current record carries has rotated out:
it is not listed, and it is counted and named in the coverage
block as rotated out, never silently dropped. Earlier text
counted against one static gathering of 50 names, 20 with
readings; that board is gone and the count with it (cure
SQUEEZE-ROTATION-20261108).
(5) Freshness follows the formula's own stated rule: a settlement
reading older than 40 days is stale. The page carries the
settlement date on every row and shows the stale state plainly
once the freshest settlement passes that age. (6) A tally with
fewer than 30 events shows its counts and no percentage. The
tallies here (20 names covered, 2 above the bar) are counts only;
the per-name figures are measurements, each printed with its
settlement date, and the vendor's figures are printed as the
vendor's, labelled as such.

Scope: this page shows only the markers the records carry: short
interest as a share of the shares outstanding, days to cover, and,
where two settlements exist, the change in shares sold short.
Short volume share is shown per name for the freshest stored
day of the daily short-volume store (started 2026-10-29, gap
G9), beside each name's short interest; a name missing from
that day shows no share, never a zero. The cost of borrowing
shares has no route on record and is shown as a plain
not-available state with the reason, never as a zero, and no
substitute measure is used in its place.

Fail-closed rules: if the readings file and the provenance record
disagree on any name both carry (settlement date, short interest
share or days to cover), if the short-interest store's figures
disagree with the readings or with the provenance record on any
name they share, if the provenance record carries figures for a
name the readings file does not hold at all, if no record carries
a usable days to cover for a listed name, if the studies card and the published feed disagree on
the squeeze pane's state or on the vendor's figures, if the
permanent log's squeeze entries disagree with that state, if the
short-volume lane's stamp disagrees with the days actually
stored in the daily short-volume store, if a reading's share recomputes above
the 120% data-error line, or if any name lacks a reading at the
freshest settlement, the refresh stops and publishes nothing.
All timestamps come from the sources, never the clock, so
running this script twice produces the same file.

Usage: python3 refresh_squeeze.py
"""

import gzip
import json
import os
import sys
from datetime import date

try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE_DIR = os.path.expanduser("~/workspace/morgue/output")
PIT_PATH = os.path.join(SOURCE_DIR, "short_interest_pit.jsonl")
PROVENANCE_PATH = os.path.join(SOURCE_DIR, "inst_bundle_provenance.json")
STUDIES_PATH = os.path.join(SOURCE_DIR, "studies_card.json")
FEED_PATH = os.path.join(SOURCE_DIR, "morgue-feed.json")
LOG_PATH = os.path.join(SOURCE_DIR, "ledger.jsonl")
SHORTVOL_DIR = os.path.expanduser(
    "~/workspace/morgue/state/morgue/shortvol")
SI_STORE_PATH = os.path.expanduser(
    "~/workspace/morgue/state/morgue/short_interest_nasdaq.json")
OUT_PATH = os.path.join(HERE, "squeeze-watch", "data.json")

SI_BAR_PCT = 15.0
SI_ERROR_OVER_PCT = 120.0
STALE_AFTER_DAYS = 40
THIN_THRESHOLD = 30

SOURCE_WORDS = ("The twice-monthly short interest readings "
                "published by Nasdaq from the market-wide short "
                "interest collection, with each company's shares "
                "outstanding from its own public filings")


def shortvol_shares(store_dir, day):
    """{symbol: short share pct} for one stored FINRA day, from
    the daily short-volume store (the G9 cure's store). A name
    missing from the day is absent from the dict, never zero."""
    path = os.path.join(store_dir, f"{day}.json.gz")
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        doc = json.load(fh)
    if doc.get("date") != day:
        raise ValueError(f"stored day {day} calls itself "
                         f"{doc.get('date')}")
    out = {}
    for sym, pair in (doc.get("names") or {}).items():
        if isinstance(pair, (list, tuple)) and len(pair) == 2 \
                and pair[1] and pair[1] > 0:
            out[sym] = round(pair[0] / pair[1] * 100.0, 1)
    return out


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def fail(message):
    print(f"Squeeze Watch refresh: {message}", file=sys.stderr)
    return 1


def build():
    for path in (PIT_PATH, PROVENANCE_PATH, STUDIES_PATH, FEED_PATH,
                 LOG_PATH):
        if not os.path.exists(path):
            return fail(f"source not found: {path}")

    with open(PIT_PATH, encoding="utf-8") as fh:
        readings = [json.loads(line) for line in fh if line.strip()]
    if not readings:
        return fail("the readings file is empty; refusing to "
                    "publish.")
    provenance = load_json(PROVENANCE_PATH)
    studies = load_json(STUDIES_PATH)
    feed = load_json(FEED_PATH)
    with open(LOG_PATH, encoding="utf-8") as fh:
        log_rows = [json.loads(line) for line in fh if line.strip()]

    # --- The published squeeze pane: the studies card and the
    # published feed must agree exactly, and the permanent log's
    # entries must carry the same state. The pane is empty on
    # record; if it ever fills, this page's shape must be
    # revisited, so a filled pane fails closed here. ---
    card_pane = studies.get("squeeze") or {}
    feed_pane = feed.get("squeeze") or {}
    if card_pane != feed_pane:
        return fail("the studies record and the published summary "
                    "disagree on the squeeze pane; refusing to "
                    "publish.")
    if card_pane.get("state") != "no_data" or card_pane.get("rows"):
        return fail("the published squeeze pane is no longer "
                    "empty; this watch list's shape must be "
                    "revisited before publishing.")
    calibration = card_pane.get("vendor_calibration") or {}
    for key in ("top10_plus20_in_5_sessions",
                "top10_minus20_in_5_sessions", "base_plus20",
                "base_minus20", "top10_median_5d_return"):
        if not isinstance(calibration.get(key), (int, float)):
            return fail(f"the vendor calibration figure {key} is "
                        "missing; refusing to publish.")
    pane_rows = [r for r in log_rows
                 if r.get("component") == "squeeze-pane"]
    if not pane_rows:
        return fail("the permanent log holds no squeeze pane "
                    "entries; refusing to publish.")
    for r in pane_rows:
        v = r.get("value") or {}
        if v.get("state") != "no_data" or v.get("gated_n") != 0:
            return fail("a permanent log squeeze entry disagrees "
                        "with the published pane's empty state; "
                        "refusing to publish.")

    # --- The short-volume lane, revisited 2026-10-29 (the G9
    # cure started the store): the lane stamp must describe the
    # stored days exactly, and each name's short-volume share for
    # the freshest stored day is published beside its short
    # interest. A name missing from that day carries no share,
    # never a zero. ---
    lane = ((feed.get("lanes") or {}).get("lanes") or {}).get(
        "short_volume") or {}
    try:
        sv_days = sorted(n[:-8] for n in os.listdir(SHORTVOL_DIR)
                         if n.endswith(".json.gz"))
    except OSError:
        sv_days = []
    if not sv_days or lane.get("status") != "ok" \
            or lane.get("days") != len(sv_days) \
            or lane.get("first_date") != sv_days[0] \
            or lane.get("last_date") != sv_days[-1]:
        return fail("the short-volume lane stamp does not "
                    "describe the stored days; refusing to "
                    "publish until they agree.")
    sv_day = sv_days[-1]
    try:
        sv_shares = shortvol_shares(SHORTVOL_DIR, sv_day)
    except (OSError, ValueError, EOFError):
        return fail(f"the stored short-volume day {sv_day} "
                    "cannot be read; refusing to publish.")

    # --- Readings: group by name, find the freshest settlement,
    # and recompute every share from its own figures. ---
    by_name = {}
    for r in readings:
        sym = r.get("symbol")
        if not sym or not r.get("settlement_date"):
            return fail("a reading carries no name or settlement "
                        "date; refusing to publish.")
        if not r.get("si_shares") or not r.get("float_shares"):
            return fail(f"the reading for {sym} is missing its "
                        "share counts; refusing to publish.")
        by_name.setdefault(sym, {})[r["settlement_date"]] = r
    # The freshest settlement and the publication vintage are
    # computed further down, over the listed names only: which
    # names are listed depends on the provenance record and the
    # store, read next.

    # --- The provenance record: a snapshot of the LATEST gather,
    # whose board rotates, where the readings file is cumulative
    # across gathers (RC-24). The two coverage sets therefore
    # legitimately differ once the board has rotated (cure
    # SQUEEZE-ROTATION-20261108; proven 2026-11-08: the record
    # carries 19 names with figures, the readings 34, and every
    # overlapping figure agrees exactly). What still binds,
    # enforced per name below: every figure the record carries
    # must agree with the readings, and a name the record
    # carries figures for but the readings file does not hold
    # at all is a genuine disagreement. ---
    bundle = {k: v for k, v in provenance.items() if k != "_meta"}
    if not bundle:
        return fail("the gathering record names no companies; "
                    "refusing to publish.")
    prov_with_si = {}
    for sym, entry in bundle.items():
        si = (entry or {}).get("si") or {}
        if "days_to_cover" in si:
            prov_with_si[sym] = si
    for sym in prov_with_si:
        if sym not in by_name:
            return fail("the gathering record carries figures "
                        f"for {sym} but the readings file holds "
                        "no reading for it; refusing to publish.")

    # --- The Nasdaq store cross-check (RC-24 cure): every name
    # the store serves must be accounted for on this page,
    # either with a reading above or named here with its basis
    # gap. The store carries rows for CENTA and PDBC, but no
    # shares-outstanding basis is on record for either, so no
    # share of float can be computed for them; they are named,
    # never silently dropped and never given a figure. The
    # store is also the second carrier of days to cover: the
    # per-name loop below takes the figure from whichever
    # record carries the name and refuses when both carry it
    # and disagree. ---
    if not os.path.exists(SI_STORE_PATH):
        return fail("the short-interest store is missing; "
                    "refusing to publish.")
    si_store = load_json(SI_STORE_PATH)
    store_names = si_store.get("names") or {}
    store_rows = {}
    for sym, rows in store_names.items():
        if isinstance(rows, dict):
            rows = rows.get("rows") or []
        store_rows[sym] = {r.get("settlement_date"): r
                           for r in rows or []}
    basis_gap = []
    for sym in sorted(store_names):
        if sym in by_name:
            continue
        rows = store_names[sym]
        if isinstance(rows, dict):
            rows = rows.get("rows") or []
        entry = bundle.get(sym) or {}
        if entry.get("shares_outstanding"):
            return fail(f"the store serves {sym} and a shares "
                        "basis is on record, but the readings "
                        "file carries no reading for it; refusing "
                        "to publish.")
        basis_gap.append({
            "symbol": sym,
            "settlements_on_record": len(rows),
            "freshest_settlement": max(
                (r["settlement_date"] for r in rows),
                default=None),
            "reason": ("The short-interest store carries "
                       "readings for this name, but no shares-"
                       "outstanding basis is on record for it, "
                       "so no share of float can be computed."),
        })

    # --- Listing scope (cure SQUEEZE-ROTATION-20261108,
    # completed 2026-11-08): the readings file is cumulative
    # across gathers, but the provenance record describes only
    # the latest gather and the store is rewritten by its own
    # collection (si_daily) for the gathering's current names
    # only. A name a gather rotated out is therefore carried,
    # in time, by NO current record: no cross-check maintains
    # its figures and no carrier maintains its days to cover.
    # Such a name leaves the page. It is counted and named in
    # the coverage block as rotated out, never silently
    # dropped, and its readings stay in the append-only file
    # untouched. Every name at least one current record DOES
    # carry stays listed and fully checked below, and fails
    # closed on any disagreement, including a carrier that
    # carries the name but no usable days to cover. ---
    carried = set(prov_with_si) | set(store_rows)
    listed = {sym: m for sym, m in by_name.items()
              if sym in carried}
    if not listed:
        return fail("no reading is carried by the gathering "
                    "record or the store; refusing to publish "
                    "an unchecked list.")
    rotated_out = sorted(set(by_name) - set(listed))
    settlements = sorted({d for m in listed.values() for d in m})
    freshest = settlements[-1]
    # Publication dates are per gather vintage (RC-24 cure,
    # 2026-10-30): the store now carries every settlement, and
    # later gathers admit older settlements on their own
    # retrieval dates, so vintages legitimately differ across
    # settlements. They also differ WITHIN the freshest
    # settlement once the gathering's board has rotated (cure
    # SQUEEZE-ROTATION-20261108): the producer stamps each
    # reading with its admission date (its own test names the
    # field "retrieval = admission"), the board the gather
    # covers rotates, and a rotated-in name's backfilled history
    # carries the later gather's date at every settlement,
    # including the freshest (proven 2026-11-08: settlement
    # 2026-10-15 carries 20 readings admitted 2026-10-26 and 14
    # admitted 2026-11-08, figures in exact agreement across
    # both records). The rule that still binds: every freshest
    # reading carries a publication date, and the page's
    # published date is the LATEST of them, so the page never
    # claims its readings were public before the last of them
    # was admitted.
    freshest_rows = [r for m in listed.values()
                     for d, r in m.items() if d == freshest]
    if any(not r.get("publication_date") for r in freshest_rows):
        return fail("a reading at the freshest settlement "
                    "carries no publication date; refusing to "
                    "publish.")
    published_date = max(r["publication_date"]
                         for r in freshest_rows)

    names = []
    cross_checked = 0
    for sym in sorted(listed):
        own = listed[sym]
        if freshest not in own:
            return fail(f"{sym} carries no reading at the freshest "
                        f"settlement ({freshest}); refusing to "
                        "publish a mixed-date list.")
        cur = own[freshest]
        si_pct = 100.0 * cur["si_shares"] / cur["float_shares"]
        if si_pct > SI_ERROR_OVER_PCT:
            return fail(f"{sym}'s short interest share recomputes "
                        f"above the {SI_ERROR_OVER_PCT:.0f}% "
                        "data-error line; refusing to publish.")
        # Cross-checks (cure SQUEEZE-ROTATION-20261108): the
        # gathering record and the store each carry only their
        # own names now, so each name is checked against every
        # record that carries it, and the two records must agree
        # where they overlap (on 2026-11-08 they agreed exactly
        # on all five names both carry, and the store's share
        # counts agreed with the readings on all twenty it
        # carries). A name no record cross-checks still stands
        # on the readings file's own integrity: append-only,
        # first vintage wins, every share recomputed above.
        prov = prov_with_si.get(sym)
        store_row = store_rows.get(sym, {}).get(freshest)
        if store_row is not None and \
                store_row.get("si_shares") != cur["si_shares"]:
            return fail(f"the short-interest store's share "
                        f"count for {sym} at the freshest "
                        "settlement disagrees with the readings; "
                        "refusing to publish.")
        dtc = None
        if prov is not None:
            if prov.get("settlement_date") != freshest:
                return fail(f"the gathering record's settlement "
                            f"for {sym} disagrees with the "
                            "readings; refusing to publish.")
            if abs(prov.get("si_pct_of_shares_out", -1)
                   - si_pct) > 1e-6:
                return fail(f"the gathering record's short "
                            f"interest share for {sym} disagrees "
                            "with the readings; refusing to "
                            "publish.")
            dtc = prov.get("days_to_cover")
            cross_checked += 1
        if store_row is not None:
            sdtc = store_row.get("days_to_cover")
            if isinstance(sdtc, (int, float)) and sdtc > 0:
                if dtc is not None and \
                        abs(float(dtc) - float(sdtc)) > 1e-9:
                    return fail(f"the gathering record and the "
                                f"short-interest store disagree "
                                f"on days to cover for {sym}; "
                                "refusing to publish.")
                dtc = sdtc
        if not isinstance(dtc, (int, float)) or dtc <= 0:
            return fail(f"no record carries a usable days to "
                        f"cover for {sym}; refusing to publish.")
        change = None
        prior_settlement = None
        earlier = [d for d in own if d < freshest]
        if earlier:
            prior_settlement = max(earlier)
            prior = own[prior_settlement]
            change = cur["si_shares"] / prior["si_shares"] - 1.0
        names.append({
            "symbol": sym,
            "si_pct_of_float": round(si_pct, 2),
            "si_shares": int(cur["si_shares"]),
            "float_shares": int(cur["float_shares"]),
            "days_to_cover": round(float(dtc), 2),
            "settlement_date": freshest,
            "published_date": cur.get("publication_date"),
            "above_si_bar": si_pct >= SI_BAR_PCT,
            "si_change": (None if change is None
                          else round(change, 4)),
            "prior_settlement_date": prior_settlement,
            "short_volume_share_pct": sv_shares.get(sym),
            "short_volume_session": sv_day,
        })
    names.sort(key=lambda n: (-n["si_pct_of_float"], n["symbol"]))

    above = [n for n in names if n["above_si_bar"]]
    reference_date = (feed.get("generated_at_utc") or "")[:10]
    if not reference_date:
        return fail("the published summary carries no generation "
                    "date to date this page against; refusing to "
                    "publish.")
    age_days = (date.fromisoformat(reference_date)
                - date.fromisoformat(freshest)).days

    data = {
        "tool": "Squeeze Watch",
        "state": "watching",
        "settlement_date": freshest,
        "published_date": published_date,
        "settlements_on_record": settlements,
        "source": SOURCE_WORDS,
        "si_bar_pct": SI_BAR_PCT,
        "stale_after_days": STALE_AFTER_DAYS,
        "thin_threshold": THIN_THRESHOLD,
        "thin": len(names) < THIN_THRESHOLD,
        "settlement_age_days_at_record": age_days,
        "stale_at_record": age_days > STALE_AFTER_DAYS,
        "coverage": {
            "names_covered": len(names),
            "names_cross_checked": cross_checked,
            "names_in_latest_gathering": len(bundle),
            "names_in_store": len(store_names),
            "names_without_float_basis": len(basis_gap),
            "names_rotated_out": len(rotated_out),
            "above_bar": len(above),
            "with_prior_reading": sum(
                1 for n in names if n["si_change"] is not None),
        },
        "rotated_out_names": rotated_out,
        "basis_gap_names": basis_gap,
        "names": names,
        "vendor_calibration": {
            "label": "The vendor's own figures for its "
                     "top-ranked names",
            "top10_plus20_in_5_sessions":
                calibration["top10_plus20_in_5_sessions"],
            "top10_minus20_in_5_sessions":
                calibration["top10_minus20_in_5_sessions"],
            "base_plus20": calibration["base_plus20"],
            "base_minus20": calibration["base_minus20"],
            "top10_median_5d_return":
                calibration["top10_median_5d_return"],
        },
        "short_volume": {
            "session": sv_day,
            "days_on_record": len(sv_days),
            "first_day": sv_days[0],
            "names_with_share": sum(
                1 for n in names
                if n["short_volume_share_pct"] is not None),
            "source": "The daily short-sale volume files "
                      "published for every stock after each "
                      "trading day's close, stored per name "
                      "since the 2026-10-29 cure of gap G9",
        },
        "not_available": [
            {"marker": "Cost of borrowing shares",
             "state": "not_available",
             "reason": "No source for borrowing costs is on "
                       "record, so there is no borrowing cost "
                       "to show."},
        ],
        "receipt": {
            "settlement_date": freshest,
            "published_date": published_date,
            "source": SOURCE_WORDS,
            "coverage": (
                f"{len(names)} names carry a short interest "
                f"reading at the settlement of {freshest}; "
                f"{cross_checked} of them are cross-checked "
                f"against the latest gathering record"
                + (f" and the rest against the short-interest "
                   f"store" if len(names) > cross_checked
                   else "")
                + f", and the two records agree on every name "
                f"both carry. {len(above)} of the {len(names)} "
                f"readings are at or above the "
                f"{SI_BAR_PCT:.0f}% bar"
                + (f". {len(rotated_out)} further names carry "
                   f"readings from earlier gathers, but no "
                   f"current record carries them, so they are "
                   f"not listed" if rotated_out else "")),
        },
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"Wrote {OUT_PATH} ({len(names)} names, {len(above)} "
          f"above the bar, settlement {freshest}, published "
          f"{published_date})")
    return 0


if __name__ == "__main__":
    sys.exit(build())
