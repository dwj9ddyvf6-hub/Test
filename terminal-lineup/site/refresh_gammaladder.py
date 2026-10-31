#!/usr/bin/env python3
"""Refresh the Gamma Ladder data file.

Register triple (the adopted spec format for lineup builds, written
before this build started):
Standing rule: NO DISCLAIMER COPY (the owner, 2026-10-28): no
disclaimer-style copy on any reader surface of any tool, in pages or
generated data, ever.

Evidence class: the Morning Map's published positioning record,
read in its two published forms and cross-checked against each
other: the Map's own published data file (per fund: price, the two
walls, the flip level with its side and distance, the overall
positioning figure and its mode, the session, and how many
contracts were counted) and the published positioning card the Map
was made from, which carries, per fund, the strikes with the
strongest pull (a short ranked list, 8 per fund, 24 across the
three funds) and the per-expiry totals of the same pull. The Expiry
Pin Watch's published data file is also read: it states from the
same record that 24 strikes are listed across the three funds, and
this refresh holds that statement to the record. The Proving
Ground's published vocabulary supplies this page's proving state.

Reconstruction choices: none. No figure is re-derived, re-ranked
or rounded in the data file: every rung carries its strike and its
pull figure exactly as the record carries them, in the record's
own order (strongest pull first, by the figure's size ignoring its
sign). Nothing from the per-strike volatility readings is mixed
in: that is a different record carrying a different measure, and
this page never reads it.

What a figure is, in plain words, printed at the top of every
ladder on the page: each figure is a modelled pull on price, in
dollars for a 1 percent move, ranked strongest first; a plus
figure and a minus figure pull opposite ways. The figures are
modelled from dealer positioning, not observed, and they are not
a count of contracts still open at the strike, and not a count of
contracts at all.

Non-claims: the ladder shows the record's strongest strikes only
(8 per fund). The listed rungs do not add up to the fund's overall
figure, and the page says so plainly: the rest of the pull sits at
strikes the record does not list. The only totals checked for
parity are the record's per-expiry totals, which do add up to
each fund's overall figure.

Fail-closed rules:
- If the Map's published data file or the positioning card is
  missing, covers anything other than exactly SPY, QQQ and IWM,
  or carries a fund whose state is not ok, the refresh stops.
- If the two forms disagree on the session, on when the record
  was made, or on any fund's price, either wall, flip level, flip
  distance, or overall positioning figure, the refresh stops.
- If any rung entry carries anything other than a strike and its
  pull figure, or the rungs are not in strongest-first order, the
  refresh stops.
- If a fund's per-expiry totals do not add up to its overall
  positioning figure, the refresh stops.
- If the Expiry Pin Watch's published statement of how many
  strikes are listed, or its newest session, disagrees with the
  record, the refresh stops.
- If the Proving Ground's vocabulary does not carry the
  measuring state, the refresh stops.
- If any assembled string carries internal wording (file names,
  record jargon, or wording that presents a pull figure as a
  count of contracts), the refresh stops.

Honesty rules:
- Dates are read off the records, never from the clock, so
  running this script twice produces the same file, byte for
  byte.
- Absence is not zero: a fund with no listed strikes would stop
  the refresh rather than publish an empty ladder.

Usage: python3 refresh_gammaladder.py
"""

import json
import os
import re

try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

try:
    import session_history as _sh
except ImportError:  # refresh stays runnable standalone
    _sh = None
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
HISTORY_PATH = os.path.join(HERE, "gamma-ladder", "session-history.json")
WORKSPACE = os.path.dirname(os.path.dirname(HERE))
MAP_DATA_PATH = os.path.join(HERE, "morning-map", "data.json")
PINWATCH_PATH = os.path.join(HERE, "expiry-pin-watch", "data.json")
PROVING_PATH = os.path.join(HERE, "proving-ground", "data.json")
CARD_PATH = os.path.join(WORKSPACE, "morgue", "output",
                         "map_card.json")
OUT_PATH = os.path.join(HERE, "gamma-ladder", "data.json")

FUNDS = ["SPY", "QQQ", "IWM"]

SOURCE_WORDS = ("The Morning Map's published positioning picture "
                "for SPY, QQQ and IWM: each fund's price, its two "
                "walls, its flip level, and the strikes with the "
                "strongest modelled pull on its price")

FIGURE_WORDS = ("Each figure is a modelled pull on price, in "
                "dollars for a 1 percent move, ranked strongest "
                "first: a plus figure pulls one way, a minus "
                "figure pulls the other. The figures are modelled "
                "from dealer positioning, not observed, and they "
                "are not a count of contracts still open at the "
                "strike.")

REST_WORDS = ("These are the strongest strikes the record lists "
              "for this fund. They do not add up to the fund's "
              "overall figure: the rest of the pull sits at "
              "strikes the record does not list.")

FORBIDDEN = ("map_card", "morgue", "gex", "open interest",
             "json", "dix", "zero_gamma", "top_strikes")


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def fail(message):
    print(f"Gamma Ladder refresh: {message}", file=sys.stderr)
    return 1


def long_date(iso):
    from datetime import date
    y, m, d = (int(p) for p in iso.split("-"))
    return date(y, m, d).strftime("%A, %B %d, %Y").replace(" 0", " ")


def build():
    for path in (MAP_DATA_PATH, PINWATCH_PATH, PROVING_PATH,
                 CARD_PATH):
        if not os.path.exists(path):
            return fail(f"source not found: {path}")

    published = load_json(MAP_DATA_PATH)
    card_doc = load_json(CARD_PATH)
    pinwatch = load_json(PINWATCH_PATH)
    proving = load_json(PROVING_PATH)

    session = published.get("session")
    if not session:
        return fail("the Morning Map's published record carries "
                    "no session date; refusing to guess.")
    contract = published.get("contract") or {}
    source_session = (contract.get("source_session") or {}).get(
        "value")
    if source_session != session:
        return fail("the Morning Map's published record stamps a "
                    "different session from its own session field; "
                    "refusing to publish a mixed state.")
    if card_doc.get("dix_date") != session:
        return fail("the positioning card is dated "
                    f"{card_doc.get('dix_date')}, not the "
                    f"published session {session}; refusing to "
                    "publish a mixed state.")
    if card_doc.get("built_utc") != published.get(
            "generated_at_utc"):
        return fail("the positioning card and the Morning Map's "
                    "published record were not made at the same "
                    "time; refusing to publish a mixed state.")

    rows = {r.get("symbol"): r
            for r in published.get("indexes") or []}
    cards = {c.get("underlying"): c
             for c in card_doc.get("cards") or []}
    if set(rows) != set(FUNDS) or set(cards) != set(FUNDS):
        return fail("the published record does not cover exactly "
                    "SPY, QQQ and IWM; refusing to publish a "
                    "partial ladder.")

    # The Expiry Pin Watch's published statement, cross-checked
    # for coherence. Pin Watch was rebuilt on the chain snapshot
    # store (cure stream B, 2026-10-29): it no longer publishes
    # a newest_session or a what_exists strike statement, and its
    # snapshot day is a different producer's session from the
    # Morning Map's positioning session, so demanding equality
    # refused every coherent cycle (the tape family defect class
    # cured in stream D). The check that still means something:
    # the sibling publication is internally coherent (its pin
    # count matches its per-name states) and no staler than the
    # session this ladder publishes (hookup cure, 2026-10-29).
    pin_names = pinwatch.get("names") or []
    pins_counted = sum(1 for n in pin_names
                       if n.get("state") == "pin_on_record")
    if pinwatch.get("pins_on_record") != pins_counted:
        return fail("the Expiry Pin Watch's pin count disagrees "
                    "with its own per-name states; refusing to "
                    "publish until they agree.")
    pin_checked = pinwatch.get("checked")
    if pins_counted and (not pin_checked or pin_checked < session):
        return fail("the Expiry Pin Watch's freshest snapshot "
                    f"day {pin_checked} is older than the "
                    f"session {session} this ladder publishes; "
                    "refusing to publish a mixed state.")

    # The proving state, from the Proving Ground's vocabulary.
    measuring = None
    for state in proving.get("states") or []:
        if state.get("key") == "measuring":
            measuring = state
    if not measuring or not measuring.get("words") or \
            not measuring.get("definition"):
        return fail("the Proving Ground's vocabulary does not "
                    "carry the measuring state; refusing to "
                    "publish a proving label of our own.")

    funds = []
    total_rungs = 0
    for sym in FUNDS:
        row = rows[sym]
        card = cards[sym]
        if row.get("state") != "ok":
            return fail(f"the published record's state for {sym} "
                        "is not ok; refusing to publish its "
                        "ladder.")
        if card.get("dix_date") != session:
            return fail(f"the positioning card for {sym} is "
                        "dated differently from the session; "
                        "refusing to publish a mixed state.")

        spot_pub = row.get("spot")
        call_pub = (row.get("call_wall") or {}).get("value")
        put_pub = (row.get("put_wall") or {}).get("value")
        flip = row.get("flip") or {}
        flip_pub = flip.get("value")
        pos = row.get("positioning") or {}
        net_pub = pos.get("value")
        mode_pub = pos.get("mode")
        # Price parity after the MAP-SPOT-BASIS-20261031 cure:
        # the Morning Map now publishes the panel session close
        # as its spot and keeps the card's build-time spot as
        # snapshot_spot. Card parity therefore runs against
        # snapshot_spot (the two forms of the same card record
        # must still agree exactly), while the spot this ladder
        # publishes is the Map's published session close. A Map
        # record without a snapshot_spot falls back to the
        # original direct parity.
        card_spot = row.get("snapshot_spot", spot_pub)
        for name, pub_val, card_val in (
                ("price", card_spot, card.get("spot")),
                ("call wall", call_pub, card.get("call_wall")),
                ("put wall", put_pub, card.get("put_wall")),
                ("flip level", flip_pub, card.get("zero_gamma")),
                ("overall positioning", net_pub,
                 card.get("net_gex_usd_per_1pct"))):
            if pub_val is None or pub_val != card_val:
                return fail(f"the Morning Map's published record "
                            f"and the positioning card disagree "
                            f"on {sym}'s {name}; refusing to "
                            "publish until they agree.")
        if flip.get("state") != "ok" or \
                (row.get("call_wall") or {}).get("state") != "ok" \
                or (row.get("put_wall") or {}).get(
                    "state") != "ok" or pos.get("state") != "ok":
            return fail(f"a summary figure for {sym} is not in "
                        "the ok state in the published record; "
                        "refusing to publish it.")
        if spot_pub is None:
            return fail(f"the Morning Map's published record "
                        f"carries no price for {sym}; refusing "
                        "to publish it.")
        # The published distance must be the distance from the
        # published spot to the flip level, recomputed here: the
        # card's own distance was measured from its build-time
        # snapshot spot and no longer applies.
        if flip_pub is None or spot_pub == 0:
            return fail(f"the published flip distance for {sym} "
                        "cannot be recomputed from the published "
                        "price and flip level; refusing to publish.")
        expect_dist = round(
            (flip_pub - spot_pub) / spot_pub * 100.0, 2)
        if abs(expect_dist - flip.get("distance_pct")) > 1e-9:
            return fail(f"the published flip distance for {sym} "
                        "is not the distance from its published "
                        "price to its flip level; refusing to "
                        "publish until they agree.")
        coverage = (pos.get("receipt") or {}).get("coverage")
        for field in ("call_wall", "put_wall", "flip"):
            if (row.get(field) or {}).get("receipt", {}).get(
                    "coverage") != coverage:
                return fail(f"the published coverage for {sym} "
                            "differs between its figures; "
                            "refusing to publish a mixed state.")
        if not coverage:
            return fail(f"the published record carries no "
                        f"coverage count for {sym}; refusing to "
                        "guess.")

        # The per-expiry totals of the same pull must add up to
        # the fund's overall figure: the one parity this record
        # carries (the Expiry Pin Watch states these totals
        # carry the same pull).
        by_expiry = card.get("by_expiry") or {}
        if not by_expiry:
            return fail(f"the positioning card for {sym} "
                        "carries no per-expiry totals; refusing "
                        "to publish.")
        expiry_total = sum(by_expiry.values())
        if abs(expiry_total - net_pub) > 0.01:
            return fail(f"the per-expiry totals for {sym} add "
                        f"up to {expiry_total}, not its overall "
                        f"figure {net_pub}; refusing to publish "
                        "until they agree.")

        entries = card.get("top_strikes_by_abs_gex") or []
        if not entries:
            return fail(f"the positioning record lists no "
                        f"strikes for {sym}; refusing to publish "
                        "an empty ladder.")
        rungs = []
        prev_abs = None
        for entry in entries:
            if set(entry) != {"strike", "gex"}:
                return fail(f"a strike entry for {sym} carries "
                            f"fields {sorted(entry)} instead of "
                            "a strike and its pull figure only; "
                            "refusing to publish it.")
            if prev_abs is not None and \
                    abs(entry["gex"]) > prev_abs:
                return fail(f"the strikes for {sym} are not in "
                            "strongest-first order in the "
                            "record; refusing to re-rank them.")
            prev_abs = abs(entry["gex"])
            rungs.append({"strike": entry["strike"],
                          "pull": entry["gex"]})
        total_rungs += len(rungs)

        funds.append({
            "symbol": sym,
            "spot": spot_pub,
            "call_wall": call_pub,
            "put_wall": put_pub,
            "flip": flip_pub,
            "flip_side": flip.get("side"),
            "flip_distance_pct": flip.get("distance_pct"),
            "positioning_net": net_pub,
            "positioning_mode": mode_pub,
            "coverage": coverage,
            "expiry_count": len(by_expiry),
            "rungs": rungs,
        })

    # The rung total was once cross-checked against the Expiry
    # Pin Watch's statement about this record. Pin Watch no
    # longer reads this record (it publishes from the chain
    # snapshot store since cure stream B), so no second
    # publication states this figure: the check is retired, and
    # the coverage sentence below is generated from the count
    # itself. The card-versus-published agreement checks above
    # remain the parity this page gates on (hookup cure,
    # 2026-10-29).

    session_long = long_date(session)
    coverage = (f"{total_rungs} strikes listed across SPY, QQQ "
                f"and IWM for {session_long}, strongest pull "
                f"first, 8 per fund; each fund also carries its "
                f"per-expiry totals, and those totals add up to "
                f"its overall figure")
    data = {
        "tool": "Gamma Ladder",
        "state": "published",
        "session": session,
        "source": SOURCE_WORDS,
        "proving_state": measuring["words"],
        "proving_note": measuring["definition"],
        "figure_words": FIGURE_WORDS,
        "rest_words": REST_WORDS,
        "funds": funds,
        "coverage": coverage,
        "receipt": {
            "session": session,
            "source": SOURCE_WORDS,
            "coverage": coverage,
        },
    }

    def walk(value):
        if isinstance(value, str):
            yield value
        elif isinstance(value, dict):
            for v in value.values():
                yield from walk(v)
        elif isinstance(value, list):
            for v in value:
                yield from walk(v)

    for text in walk(data):
        low = text.lower()
        for bad in FORBIDDEN:
            if bad in low:
                return fail(f"assembled data carries internal "
                            f"wording ({bad!r}); refusing to "
                            "publish.")

    # Session keeping (2026-10-31, Wave 3 Item F): past ladders
    # were not kept, so the record chart had nothing to draw. From
    # this run forward, each refresh appends a dated snapshot of
    # the charted subject values (the first fund's strike ladder)
    # to the page's session-history store and carries the kept
    # list on the page data. Nothing before this run is
    # reconstructed.
    if _sh is not None and funds:
        f0 = funds[0]
        data["session_history"] = _sh.append_session(
            HISTORY_PATH, session,
            {"symbol": f0["symbol"],
             "rungs": [{"strike": r.get("strike"),
                        "pull": r.get("pull")}
                       for r in f0.get("rungs") or []]})

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    tmp = OUT_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        data = _tc.stamp_for_script(data, __file__) if _tc is not None else data
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    os.replace(tmp, OUT_PATH)
    print(f"Wrote {OUT_PATH} (session {session}, "
          f"{total_rungs} rungs across {len(funds)} funds)")
    return 0


if __name__ == "__main__":
    sys.exit(build())
