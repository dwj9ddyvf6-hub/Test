#!/usr/bin/env python3
"""Refresh the Agent Debate data file.

Register triple (the adopted spec format for lineup builds, written
before this build started):
Standing rule: NO DISCLAIMER COPY (the owner, 2026-10-28): no
disclaimer-style copy on any reader surface of any tool, in pages or
generated data, ever.

Evidence class: only records the terminal already publishes. For
each of the three index funds (SPY, QQQ, IWM): the Second Opinion's
per-family readings (price, prints and positioning, each with its
own stance word and figures), the Morning Map's walls and flip
level, the Flow Board's net premium figures for the freshest
session (the tape's call-side and put-side net premium and their
difference), and the Regime Dial's published market reading. The
Proving Ground's published vocabulary supplies this page's proving
state label.

Reconstruction choices: the debate is staged per fund as the
strongest case the records make for prices rising and the strongest
case for prices falling. A published reading is counted once, under
the tool that published it, and it points the way its own record
points: a family whose stance word is positive points to rising,
cautious points to falling, mixed points neither way; the Morning
Map points to falling when its flip level sits above the spot price
and to rising when it sits below; the Flow Board's difference
(call-side net minus put-side net) points to rising when positive
and to falling when negative; the Regime Dial points the way its
published reading reads. No claim appears in either case that is
not a published reading, no figure is restated differently than its
source published it, and the page issues no verdict or lean of its
own: the closing panel per fund states the count of readings each
way exactly as counted here and names the specific readings that
would have to flip to change that count. Where a case has no
supporting reading on record, that side carries no claims and says
so in plain words.

What a figure is, in plain words, printed on the page: a reading is
one tool's published take on one part of the evidence for a fund on
the trading day; the count is simply how many of the counted
readings point each way.

Fail-closed rules:
- If any published record read here is missing, the refresh stops.
- If the Morning Map's session does not agree with the
  positioning card session the Second Opinion carries for every
  fund (its per-fund dix_date), the refresh stops.
- If a fund is missing from any record, or a family stance word is
  not one the Second Opinion uses, the refresh stops.
- If the Second Opinion's prints figures disagree with the Flow
  Board's freshest-session figures for the same fund (call-side,
  put-side, or their sum against the published net), the refresh
  stops.
- If the Second Opinion's positioning figures disagree with the
  Morning Map's spot, walls or flip level for the same fund, or
  their above/below relationship disagrees, the refresh stops.
- If the Regime Dial's position check does not carry the S&P 500
  fund's spot and flip as the Second Opinion published them, the
  refresh stops.
- If the Proving Ground's vocabulary does not carry the proving
  state, the refresh stops.
- If any assembled string carries internal wording (file names or
  record jargon), the refresh stops.

Honesty rules:
- Dates and times are read off the records, never from the clock,
  so running this script twice produces the same file, byte for
  byte.
- The page's closing panels report the records' count only; they
  never turn it into a call, a forecast or a recommendation.

Usage: python3 refresh_agentdebate.py
"""

import json
import os
import sys
from datetime import date

try:
    import terminal_common as _tc
except ImportError:  # refresh stays runnable standalone
    _tc = None

HERE = os.path.dirname(os.path.abspath(__file__))
SO_PATH = os.path.join(HERE, "second-opinion", "data.json")
MM_PATH = os.path.join(HERE, "morning-map", "data.json")
FB_PATH = os.path.join(HERE, "flow-board", "data.json")
RD_PATH = os.path.join(HERE, "regime-dial", "data.json")
PROVING_PATH = os.path.join(HERE, "proving-ground", "data.json")
OUT_PATH = os.path.join(HERE, "agent-debate", "data.json")

FUNDS = ["SPY", "QQQ", "IWM"]
STANCES = {"positive", "mixed", "cautious"}
BANNED = [".json", "data file", "morgue", "ledger", "sleeve", "gex",
          "dataset", "desk", "vendor snapshot"]


def fail(msg):
    print("refresh_agentdebate: STOP: " + msg, file=sys.stderr)
    sys.exit(1)


def load(path, label):
    if not os.path.exists(path):
        fail("missing published record: " + label)
    with open(path) as f:
        return json.load(f)


def money(v):
    v = int(round(v))
    if v < 0:
        return "-$" + format(-v, ",")
    return "$" + format(v, ",")


def num(v):
    if float(v) == int(v):
        return format(int(v), ",")
    return format(v, ",.2f").rstrip("0").rstrip(".")


def long_date(iso):
    d = date.fromisoformat(iso)
    return d.strftime("%A, %B ") + str(d.day) + d.strftime(", %Y")


def side_of_stance(stance):
    return {"positive": "rising", "cautious": "falling"}.get(stance, "neither")


def main():
    so = load(SO_PATH, "Second Opinion")
    mm = load(MM_PATH, "Morning Map")
    fb = load(FB_PATH, "Flow Board")
    rd = load(RD_PATH, "Regime Dial")
    pg = load(PROVING_PATH, "Proving Ground")

    session = so.get("session")
    if not session:
        fail("Second Opinion carries no session")
    # The Morning Map's session is the positioning card's data
    # session (open interest as of that close), which is the
    # session the Second Opinion's positioning family carries as
    # its dix_date: the card is built the next morning for the
    # scored session, so its data session is one session behind
    # the scored session by the morgue's rhythm. Equality with
    # the scored session was the old gate and refused every
    # coherent evening once the scored run advanced same-day
    # (BOARD-POSTCLOSE-20261031). The gate that means something
    # is agreement with the positioning card session the Second
    # Opinion itself carries, per fund, checked below once the
    # fund readings are loaded (AGENTDEBATE-CARD-SESSION-20261031).
    mm_session = mm.get("session")
    if not mm_session:
        fail("Morning Map carries no session")
    # Flow Board is a tape family publication: its freshest
    # session is the tape session, one fresher than the scored
    # session every evening by the morgue's rhythm. The debate
    # joins the Flow Board cell AT the scored session (checked
    # per fund below, fail-closed when absent), so the gate
    # that means something is freshness, never equality (the
    # tape family defect class cured in stream D; hookup cure,
    # 2026-10-29).
    if (fb.get("freshest_session") or "") < session:
        fail("Flow Board freshest session is older than the Second Opinion session")
    # Regime Dial publishes a standing reading, not session
    # figures: its freshest_session is the oldest counting
    # check's session by construction, so it can never equal
    # the scored session. Its gate is the published reading
    # itself, checked below (hookup cure, 2026-10-29).

    proving = None
    for st in pg.get("states", []):
        if st.get("key") == "proving":
            proving = st
    if not proving:
        fail("Proving Ground vocabulary does not carry the proving state")

    so_names = {n["symbol"]: n for n in so.get("names", [])}
    mm_idx = {i["symbol"]: i for i in mm.get("indexes", [])}
    fb_rows = {r["underlying"]: r for r in fb.get("rows", [])}

    regime = rd.get("reading") or {}
    regime_kind = regime.get("kind")
    regime_sentence = regime.get("sentence")
    if not regime_kind or not regime_sentence:
        fail("Regime Dial carries no published reading")
    if regime_kind == "Trending down":
        regime_side = "falling"
    elif regime_kind == "Trending up":
        regime_side = "rising"
    else:
        regime_side = "neither"
    pos_check = None
    for c in rd.get("checks", []):
        if c.get("id") == "position":
            pos_check = c
    if not pos_check:
        fail("Regime Dial carries no position check")

    funds = []
    for sym in FUNDS:
        n = so_names.get(sym)
        if not n:
            fail("Second Opinion carries no reading for " + sym)
        ix = mm_idx.get(sym)
        if not ix:
            fail("Morning Map carries no card for " + sym)
        row = fb_rows.get(sym)
        if not row:
            fail("Flow Board carries no row for " + sym)
        # Second Opinion's prints family is built from the
        # freshest tape card, so its figures join the Flow
        # Board cell at the tape family's freshest session,
        # not at the scored session: joining at the scored
        # session compared two different days' prints and
        # refused every coherent evening (hookup cure,
        # 2026-10-29).
        cell = None
        for c in row.get("cells", []):
            if c.get("session") == fb.get("freshest_session"):
                cell = c
        if not cell:
            fail("Flow Board carries no freshest-session figures for " + sym)

        price, prints, pos = n.get("price"), n.get("prints"), n.get("positioning")
        if not price or not prints or not pos:
            fail("Second Opinion reading for " + sym + " is missing a family")
        if pos.get("dix_date") != mm_session:
            fail("Morning Map session disagrees with the positioning card "
                 "session the Second Opinion carries for " + sym)
        for fam in (price, prints, pos):
            if fam.get("stance") not in STANCES:
                fail("unknown stance word in the Second Opinion reading for " + sym)
        directional = [price["stance"], prints["stance"], pos["stance"]]
        if n.get("directional") != directional:
            fail("Second Opinion direction list disagrees with its family stances for " + sym)

        # Cross-record parity: prints vs the Flow Board tape figures.
        if int(prints["call_net_premium"]) != int(cell["call_net_premium_usd"]):
            fail("call-side net premium disagrees between records for " + sym)
        if int(prints["put_net_premium"]) != int(cell["put_net_premium_usd"]):
            fail("put-side net premium disagrees between records for " + sym)
        if int(prints["net_premium"]) != int(cell["call_net_premium_usd"]) + int(cell["put_net_premium_usd"]):
            fail("net premium does not add up between records for " + sym)
        if int(prints["prints"]) != int(cell["prints_examined"]):
            fail("print count disagrees between records for " + sym)

        # Cross-record parity: positioning vs the Morning Map card.
        # The Second Opinion's positioning family is built from
        # the card itself, so its spot is the card's snapshot
        # spot; the Morning Map page also publishes the session
        # close as its headline spot (MAP-SPOT-BASIS-20261031),
        # kept on the card as snapshot_spot. Parity runs against
        # the snapshot spot, the basis both records share.
        card_spot = ix.get("snapshot_spot", ix["spot"])
        if float(pos["spot"]) != float(card_spot):
            fail("spot disagrees between records for " + sym)
        if float(pos["call_wall"]) != float(ix["call_wall"]["value"]):
            fail("call wall disagrees between records for " + sym)
        if float(pos["put_wall"]) != float(ix["put_wall"]["value"]):
            fail("put wall disagrees between records for " + sym)
        if round(float(ix["flip"]["value"]), 2) != float(pos["flip"]):
            fail("flip level disagrees between records for " + sym)
        mm_side_word = ix["flip"].get("side")
        if bool(pos["below_flip"]) != (mm_side_word == "above"):
            fail("flip relationship disagrees between records for " + sym)

        if sym == "SPY":
            # The Regime Dial's position check is built from the
            # Morning Map's published spot (the session close,
            # MAP-SPOT-BASIS-20261031) and flip, so it is checked
            # against the Morning Map's published figures, not
            # the positioning card's snapshot spot.
            fig = pos_check.get("figure", "")
            if num(ix["spot"]) not in fig or num(pos["flip"]) not in fig:
                fail("Regime Dial position check disagrees with the published spot and flip")

        readings = []  # (key, plain name, side, claim text, source in plain words)

        readings.append((
            "price", "the price reading", side_of_stance(price["stance"]),
            "The price reading's own word is \"" + price["stance"] + "\": a score of " +
            num(price["score"]) + " of 100, a close of " + num(price["close"]) + ", with " +
            str(price["confirming"]) + " of " + str(price["checks_total"]) +
            " checks confirming, and the fund " +
            ("qualified" if price["qualified"] else "did not qualify") + " on those checks.",
            "the Second Opinion"))

        readings.append((
            "prints", "the prints reading", side_of_stance(prints["stance"]),
            "The prints reading's own word is \"" + prints["stance"] + "\": " +
            format(int(prints["prints"]), ",") + " prints with a net premium of " +
            money(prints["net_premium"]) + " (call side " + money(prints["call_net_premium"]) +
            ", put side " + money(prints["put_net_premium"]) + ").",
            "the Second Opinion"))

        readings.append((
            "positioning", "the positioning reading", side_of_stance(pos["stance"]),
            "The positioning reading's own word is \"" + pos["stance"] + "\": the spot price of " +
            num(pos["spot"]) + " sits " + ("below" if pos["below_flip"] else "above") +
            " the flip level of " + num(pos["flip"]) + ", with the call wall at " +
            num(pos["call_wall"]) + " and the put wall at " + num(pos["put_wall"]) + ".",
            "the Second Opinion"))

        mm_side = "falling" if mm_side_word == "above" else "rising"
        readings.append((
            "morning_map", "the Morning Map's walls and flip", mm_side,
            "The Morning Map puts the flip level " + num(ix["flip"]["distance_pct"]) +
            "% " + mm_side_word + " the spot price of " + num(ix["spot"]) +
            ", the call wall at " + num(ix["call_wall"]["value"]) +
            " and the put wall at " + num(ix["put_wall"]["value"]) + ".",
            "the Morning Map"))

        diff = int(cell["difference_usd"])
        tape_side = "rising" if diff > 0 else ("falling" if diff < 0 else "neither")
        readings.append((
            "tape", "the tape's net premium figures", tape_side,
            "On the tape, the call side's net premium minus the put side's net premium for " +
            "the session is " + money(diff) + " (call side " +
            money(cell["call_net_premium_usd"]) + ", put side " +
            money(cell["put_net_premium_usd"]) + ").",
            "the Flow Board"))

        readings.append((
            "regime", "the Regime Dial's market reading", regime_side,
            "The published market reading reads: \"" + regime_sentence + "\"",
            "the Regime Dial"))

        rising = [r for r in readings if r[2] == "rising"]
        falling = [r for r in readings if r[2] == "falling"]
        neither = [r for r in readings if r[2] == "neither"]

        def case(readings_):
            return [{"claim": r[3], "source": r[4]} for r in readings_]

        if len(rising) > len(falling):
            lean_words = ("The published readings lean toward rising, " +
                          str(len(rising)) + " to " + str(len(falling)) + ".")
        elif len(falling) > len(rising):
            lean_words = ("The published readings lean toward falling, " +
                          str(len(falling)) + " to " + str(len(rising)) + ".")
        else:
            lean_words = ("The published readings are evenly split, " +
                          str(len(rising)) + " each way.")
        if neither:
            lean_words += (" " + str(len(neither)) + " of the counted readings point " +
                           "neither way: " + ", ".join(r[1] for r in neither) + ".")

        if len(falling) != len(rising):
            lead = falling if len(falling) > len(rising) else rising
            lead_word = "falling" if len(falling) > len(rising) else "rising"
            other_word = "rising" if lead_word == "falling" else "falling"
            needed = (abs(len(falling) - len(rising)) // 2) + 1
            change_words = (
                "That count is the records' count, not this page's own call. It would "
                "change only if the published readings themselves changed: for the count "
                "to lean toward " + other_word + " instead, at least " + str(needed) +
                " of the readings that now point to " + lead_word + " would have to flip "
                "to " + other_word + ": " + ", ".join(r[1] for r in lead) + ". One reading "
                "flipping moves the count by one each way.")
        else:
            change_words = (
                "That count is the records' count, not this page's own call. It would "
                "change only if the published readings themselves changed: any one of "
                "the counted readings flipping would move the count by one each way: " +
                ", ".join(r[1] for r in readings) + ".")

        funds.append({
            "symbol": sym,
            "rising_case": case(rising),
            "falling_case": case(falling),
            "rising_none_words": ("No published reading on record supports prices rising for " +
                                  sym + ": none of the counted readings below points that way.")
            if not rising else None,
            "falling_none_words": ("No published reading on record supports prices falling for " +
                                   sym + ": none of the counted readings below points that way.")
            if not falling else None,
            "count_rising": len(rising),
            "count_falling": len(falling),
            "count_neither": len(neither),
            "counted_names": [r[1] for r in readings],
            "closing_words": lean_words,
            "change_words": change_words,
        })

    # Chart counts (2026-10-31 chart cure): the per-fund reading
    # counts this page already assembles, copied into the top-level
    # counts block the record producer and chart renderer draw from
    # on sibling pages (flow-tape, state-analogue). No new numbers:
    # every value is a fund's own count_rising / count_falling.
    counts = {}
    for f in funds:
        sym = f["symbol"].lower()
        counts[sym + "_readings_pointing_to_rising"] = f["count_rising"]
        counts[sym + "_readings_pointing_to_falling"] = f["count_falling"]

    out = {
        "tool": "Agent Debate",
        "counts": counts,
        "session": session,
        "session_long": long_date(session),
        "published_at_utc": fb.get("published_at_utc"),
        "source": ("The Second Opinion's readings for the three index funds, the Morning "
                   "Map's walls and flip levels, the Flow Board's net premium figures and "
                   "the Regime Dial's published market reading, each read exactly as "
                   "published"),
        "receipt": ("Debate for the trading day of " + long_date(session) + ": 3 funds, " +
                    "6 published readings counted per fund, every claim tied to the "
                    "figure its own tool published"),
        "proving_state": proving["words"],
        "proving_note": proving["definition"],
        "how_counted": ("Each counted reading is one tool's published take: the Second "
                        "Opinion's price, prints and positioning readings, the Morning "
                        "Map's walls and flip, the Flow Board's net premium figures and "
                        "the Regime Dial's market reading. A reading points the way its "
                        "own record points; this page adds no reading of its own."),
        "funds": funds,
    }

    blob = json.dumps(out, ensure_ascii=False).lower()
    for bad in BANNED:
        if bad in blob:
            fail("internal wording in assembled output: " + bad)

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    tmp = OUT_PATH + ".tmp"
    with open(tmp, "w") as f:
        out = _tc.stamp_for_script(out, __file__) if _tc is not None else out
        json.dump(out, f, indent=1, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, OUT_PATH)
    print("refresh_agentdebate: wrote " + OUT_PATH)


if __name__ == "__main__":
    main()
