#!/usr/bin/env python3
"""Regression blocker for the Midna's Book strip (BOOK-STRIP-20261104).

Covers the strip's failure classes: a draft or an expired card
leaking onto the public hub as a live card, a trigger or invalidation
misread from the journal's own fields, the strip carrying stale
figures when the book's record cannot be read (it must publish a
dated unavailable state instead), the hub injection duplicating or
breaking the hub's ruled structure, and the change watcher missing
an edit to the book's ledger or journal (or republishing when
nothing changed). Run standalone: python3 test_book_strip_20261104.py
(exit 0 = pass).
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

SITE = Path(__file__).resolve().parent
BOOK = Path(os.path.expanduser("~/workspace/midna-book"))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gen = load("refresh_book_strip", SITE / "refresh_book_strip.py")

MINI_JOURNAL = """# Journal

## 2026-11-04 08:00 ET · ENTRY · J-20261104-91
- Instrument: TEST
- Invalidation: a close below 10.00, stated before size
- Levels: trigger, a 30-minute hold above 12.50 on volume; Window: Wed to Thu 2026-11-05 close; untriggered by then, the card expires
- Size math: share count 40 shares
- Decision: CONDITIONAL CARD, SIGNED. Fill only if the trigger is met
- Fill (appended when priced): pending; UNFILLED unless a fill is recorded

## 2026-11-04 · ENTRY (DRAFT, unsigned) · J-20261104-D9
- Instrument: DRFT
- Invalidation: a close below 1.00
- Levels: trigger, a 30-minute hold above 2.00; Window: Wed 2026-11-04 only
- Size math: share count 10 shares
- Decision: DRAFT CONDITIONAL CARD, unsigned
- Fill (appended when priced): pending

## 2026-11-02 08:00 ET · ENTRY · J-20261102-91
- Instrument: OLDC
- Invalidation: a close below 5.00
- Levels: trigger, a 30 minute hold above 6.00 on volume confirming
- Size math: share count 20 shares
- Decision: CONDITIONAL CARD. Fill only if the trigger is met
- Fill (appended when priced): pending; UNFILLED unless a fill is recorded
"""


def main() -> int:
    fails = []

    # Parser mechanics on a synthetic journal.
    entries = gen.parse_journal(MINI_JOURNAL)
    cards = gen.live_cards(entries, date(2026, 11, 4))
    syms = [c["symbol"] for c in cards]
    if syms != ["TEST"]:
        fails.append("mini journal live cards %r, want ['TEST']" % syms)
    elif cards[0]["trigger"] != 12.50 or \
            cards[0]["invalidation"] != 10.00 or \
            cards[0]["shares"] != 40 or \
            cards[0]["expiry"] != "2026-11-05":
        fails.append("mini journal card misread: %r" % cards[0])

    # Dated pin on the real journal, read as of 2026-11-04: the
    # morning's three live cards, exactly as the book's own midday
    # read names them, with their written triggers and lines.
    real = gen.parse_journal(
        (BOOK / "JOURNAL.md").read_text(encoding="utf-8"))
    cards = {c["symbol"]: c for c in
             gen.live_cards(real, date(2026, 11, 4))}
    want = {"AEP": (132.17, 127.22, "2026-11-05"),
            "EXPD": (206.23, 196.19, "2026-11-04"),
            "ABBV": (294.89, 282.68, "2026-11-04")}
    if set(cards) != set(want):
        fails.append("real journal live cards %r, want %r"
                     % (sorted(cards), sorted(want)))
    else:
        for sym, (trig, inv, exp) in want.items():
            c = cards[sym]
            if (c["trigger"], c["invalidation"], c["expiry"]) != \
                    (trig, inv, exp):
                fails.append("card %s misread: %r" % (sym, c))
    actions = gen.recent_actions(real, {"fills": []})
    shop = [a for a in actions if "SHOP" in a["line"]]
    if not shop or "89" not in shop[0]["line"] or \
            "next book pass" not in shop[0]["line"]:
        fails.append("SHOP action missing or mis-stated: %r" % actions)

    # The daily pull window ends the morning after the last
    # completed session: a window reaching past the present moment
    # is refused by the read route's recent-SIP rule (403).
    if gen._pull_end("2026-11-03") != "2026-11-04T05:00:00Z":
        fails.append("pull end wrong: %r" % gen._pull_end("2026-11-03"))

    # BOOK-STRIP-BENCH-WINDOW-20261104: the pull end is capped at
    # the present moment, so an evening generation (whose nominal
    # morning-after end is still in the future) still gets its
    # benchmark window instead of a refused pull and an omitted
    # comparison line. Pre-cure there is no cap helper at all.
    if gen._cap_end("2026-11-05T05:00:00Z", "2026-11-05T02:21:00Z") != \
            "2026-11-05T02:21:00Z":
        fails.append("future pull end not capped at now: %r"
                     % gen._cap_end("2026-11-05T05:00:00Z",
                                    "2026-11-05T02:21:00Z"))
    if gen._cap_end("2026-11-04T05:00:00Z", "2026-11-05T02:21:00Z") != \
            "2026-11-04T05:00:00Z":
        fails.append("past pull end moved by the cap: %r"
                     % gen._cap_end("2026-11-04T05:00:00Z",
                                    "2026-11-05T02:21:00Z"))

    # Live behaviour, the defect itself: a benchmark pull for the
    # freshest completed session succeeds at generation time,
    # evening included (pre-cure it is refused after the 17:00 ET
    # session roll and the strip omits its comparison line).
    from datetime import datetime as _dt2
    through_now = gen.freshest_session(_dt2.now(gen.ET))
    got = gen.benchmark("SPY", date(2026, 10, 30), through_now)
    if not got or got[1] != through_now:
        fails.append("live benchmark pull failed for session %s: %r"
                     % (through_now, got))

    # BOOK-STRIP-CARD-EVENING-20261104: on the real journal, the
    # cards expiring 2026-11-04 (EXPD, ABBV) are live in the
    # afternoon of their expiry day and gone after its close,
    # while the card expiring 2026-11-05 (AEP) stays live.
    from datetime import datetime as _dt
    afternoon = _dt(2026, 11, 4, 15, 0, tzinfo=gen.ET)
    evening = _dt(2026, 11, 4, 16, 30, tzinfo=gen.ET)
    day_syms = {c["symbol"] for c in
                gen.live_cards(real, date(2026, 11, 4),
                               now_et=afternoon)}
    eve_syms = {c["symbol"] for c in
                gen.live_cards(real, date(2026, 11, 4),
                               now_et=evening)}
    if day_syms != {"AEP", "EXPD", "ABBV"}:
        fails.append("expiry-day afternoon cards %r, want "
                     "['ABBV', 'AEP', 'EXPD']" % sorted(day_syms))
    if eve_syms != {"AEP"}:
        fails.append("expiry-day evening cards %r, want ['AEP']"
                     % sorted(eve_syms))

    # Position fields (BOOK-STRIP-POSITION-FIELDS-20261104): a
    # position whose opening fill and journal invalidation exist
    # renders with its entry price and exit line populated: from
    # the position record's own fields in the book's schema
    # (entry_fill, invalidation_close_below), derived from the
    # ledger's opening fill and the journal entry that opened it
    # when the position record does not restate them, and stated
    # plainly in the line when neither exists anywhere.
    POS_JOURNAL = """# Journal

## 2026-11-04 12:35 ET · ENTRY · J-20261104-08
- Instrument: SHOP
- Invalidation: a close below 149.34, the print day range top, stated before size
- Decision: BUY 89 SHOP at the charter fill price
- Fill (appended when priced): Filled at $151.6458
"""

    def pos_ledger(position, fills):
        return {
            "book": "midna", "cash": 86503.52,
            "starting_equity": 100000.0, "inception": "2026-10-30",
            "positions": [position], "fills": fills,
            "equity_history": [
                {"date": "2026-11-04", "equity": 100123.19}],
        }

    SHOP_FILL = {"symbol": "SHOP", "side": "buy", "qty": 89,
                 "decision_id": "J-20261104-08",
                 "fill_price": 151.6458,
                 "bar_ts": "2026-11-04T17:35:00Z"}

    def state_for(ledger_obj, journal_text):
        with tempfile.TemporaryDirectory() as td:
            bdir = Path(td)
            (bdir / "ledger.json").write_text(
                json.dumps(ledger_obj), encoding="utf-8")
            (bdir / "JOURNAL.md").write_text(
                journal_text, encoding="utf-8")
            gen.BOOK_DIR = bdir
            try:
                return gen.build_state(gen.datetime.now(gen.ET))
            finally:
                gen.BOOK_DIR = BOOK

    real_mark, real_bench = gen.mark_for, gen.benchmark
    gen.mark_for = lambda sym, now: (153.03,
                                     "the November 4, 2026 close")
    gen.benchmark = lambda sym, inc, through: None
    try:
        own = state_for(pos_ledger(
            {"symbol": "SHOP", "qty": 89, "entry_fill": 151.6458,
             "decision_id": "J-20261104-08",
             "invalidation_close_below": 149.34,
             "opened": "2026-11-04"}, [SHOP_FILL]), POS_JOURNAL)
        rows = own.get("positions") or []
        if len(rows) != 1 or rows[0].get("entry_price") != 151.6458 \
                or rows[0].get("invalidation") != 149.34 \
                or rows[0].get("entry_date") != "2026-11-04":
            fails.append("position's own fields dropped: %r" % rows)
        elif "in at 151.65" not in rows[0]["line"] or \
                "Out on a close below 149.34" not in rows[0]["line"]:
            fails.append("position line missing entry or exit: %r"
                         % rows[0]["line"])
        derived = state_for(pos_ledger(
            {"symbol": "SHOP", "qty": 89,
             "decision_id": "J-20261104-08",
             "opened": "2026-11-04"}, [SHOP_FILL]), POS_JOURNAL)
        rows = derived.get("positions") or []
        if len(rows) != 1 or rows[0].get("entry_price") != 151.6458 \
                or rows[0].get("invalidation") != 149.34:
            fails.append("position fields not derived from the "
                         "fill and journal: %r" % rows)
        bare = state_for(pos_ledger(
            {"symbol": "SHOP", "qty": 89, "opened": "2026-11-04"},
            []), MINI_JOURNAL)
        rows = bare.get("positions") or []
        if len(rows) != 1 or rows[0].get("entry_price") is not None \
                or rows[0].get("invalidation") is not None:
            fails.append("unsourced position fields invented: %r"
                         % rows)
        elif "entry price is not in the book's record" not in \
                rows[0]["line"] or \
                "No exit line is recorded" not in rows[0]["line"]:
            fails.append("unsourced position not stated plainly: %r"
                         % rows[0]["line"])
        # Dated pin on the real book: the SHOP position opened
        # 2026-11-04 renders with its fill price and invalidation.
        gen.BOOK_DIR = BOOK
        live = gen.build_state(gen.datetime.now(gen.ET))
        rows = [r for r in (live.get("positions") or [])
                if r.get("symbol") == "SHOP"]
        if len(rows) != 1 or rows[0].get("entry_price") != 151.6458 \
                or rows[0].get("invalidation") != 149.34:
            fails.append("real SHOP position fields wrong: %r" % rows)
    finally:
        gen.mark_for, gen.benchmark = real_mark, real_bench
        gen.BOOK_DIR = BOOK

    # Fail-closed: an unreadable book record yields a dated
    # unavailable state, never figures.
    with tempfile.TemporaryDirectory() as td:
        gen.BOOK_DIR = Path(td)
        state = gen.build_state(gen.datetime.now(gen.ET))
        if state.get("state") != "unavailable" or \
                "unavailable" not in state.get("unavailable_line", ""):
            fails.append("unavailable state wrong: %r" % state)
        gen.BOOK_DIR = BOOK

    # Hub injection: once, idempotent, and no <h2> of its own (the
    # hub restructure splits the page at its first <h2>). The
    # fixture is a pre-strip hub carrying the two anchors; the live
    # hub is pinned separately below.
    with tempfile.TemporaryDirectory() as td:
        hub_copy = Path(td) / "index.html"
        hub_copy.write_text(
            "<html><head><script src=\"shared.js\" defer></script>"
            "</head><body><div class=\"wrap\">\n"
            "<h1>Free Market Tools</h1></div></body></html>",
            encoding="utf-8")
        if not gen.ensure_hub(hub_copy):
            fails.append("ensure_hub did not inject into a hub copy")
        text = hub_copy.read_text(encoding="utf-8")
        if text.count('id="book-strip"') != 1 or \
                text.count('src="book-strip.js"') != 1:
            fails.append("strip section or script tag not exactly once")
        section = text[text.index('id="book-strip"'):]
        section = section[:section.index("</section>")]
        if "<h2" in section:
            fails.append("strip section carries an <h2>")
        if gen.ensure_hub(hub_copy):
            fails.append("ensure_hub not idempotent")
    live_hub = (SITE / "index.html").read_text(encoding="utf-8")
    if live_hub.count('id="book-strip"') != 1 or \
            live_hub.count('src="book-strip.js"') != 1:
        fails.append("live hub does not carry the strip exactly once")
    elif live_hub.index('id="book-strip"') > \
            live_hub.index("<h1>Free Market Tools</h1>"):
        fails.append("strip section is not above the hub headline")

    # Watcher trigger logic on copies: change publishes once,
    # no-change stays silent, a later edit publishes again, and a
    # failed publish is not recorded as done.
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        book = root / "book"
        home = root / "home"
        book.mkdir()
        (book / "ledger.json").write_text(
            (BOOK / "ledger.json").read_text(encoding="utf-8"),
            encoding="utf-8")
        (book / "JOURNAL.md").write_text(
            (BOOK / "JOURNAL.md").read_text(encoding="utf-8"),
            encoding="utf-8")
        ok_sync = root / "ok_sync.py"
        ok_sync.write_text("# stand-in publisher\n", encoding="utf-8")
        hub_copy = root / "hub.html"
        hub_copy.write_text(
            (SITE / "index.html").read_text(encoding="utf-8"),
            encoding="utf-8")
        env = dict(os.environ)
        env["BOOK_STRIP_BOOK_DIR"] = str(book)
        env["BOOK_STRIP_HOME"] = str(home)
        env["BOOK_STRIP_OUT"] = str(root / "data.json")
        env["BOOK_STRIP_HUB"] = str(hub_copy)
        env["BOOK_STRIP_SYNC_CMD"] = \
            "%s %s" % (sys.executable, ok_sync)

        def watch(envx):
            return subprocess.run(
                [sys.executable, str(SITE / "watch_book_strip.py")],
                capture_output=True, text=True, env=envx, timeout=300)

        r1 = watch(env)
        if r1.returncode != 0 or "REPUBLISHED" not in r1.stdout:
            fails.append("watcher first run: rc=%d out=%r"
                         % (r1.returncode, r1.stdout[-200:]))
        r2 = watch(env)
        if "NO-CHANGE" not in r2.stdout:
            fails.append("watcher second run not NO-CHANGE: %r"
                         % r2.stdout[-200:])
        with open(book / "JOURNAL.md", "a", encoding="utf-8") as fh:
            fh.write("\n")
        r3 = watch(env)
        if "REPUBLISHED" not in r3.stdout:
            fails.append("watcher missed a journal edit: %r"
                         % r3.stdout[-200:])
        fail_sync = root / "fail_sync.py"
        fail_sync.write_text("raise SystemExit(3)\n", encoding="utf-8")
        env_fail = dict(env)
        env_fail["BOOK_STRIP_SYNC_CMD"] = \
            "%s %s" % (sys.executable, fail_sync)
        with open(book / "ledger.json", "a", encoding="utf-8") as fh:
            fh.write("\n")
        r4 = watch(env_fail)
        state = json.loads((home / "watcher-state.json").read_text())
        import hashlib
        if hashlib.sha256(
                (book / "ledger.json").read_bytes()).hexdigest() == \
                state["hashes"]["ledger.json"]:
            fails.append("watcher recorded a failed publish as done")

    for f in fails:
        print("FAIL: " + f)
    print("book strip tests: %s (%d failures)"
          % ("PASS" if not fails else "FAIL", len(fails)))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
