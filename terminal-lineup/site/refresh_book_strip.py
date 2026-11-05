#!/usr/bin/env python3
"""Refresh the Midna's Book strip data file (BOOK-STRIP-20261104).

The hub (site/index.html) carries a book strip as its first content
section, rendered by site/book-strip.js from this refresher's output,
site/book-strip/data.json. The strip shows the state of Midna's own
simulated $100,000 paper book (~/workspace/midna-book): equity and
cash, performance against SPY and QQQ since the book's inception,
open positions, live conditional cards, and the latest fills and
exits. It is a reader surface: plain words, and it says plainly that
the book is simulated.

Sources, read exactly as they stand: the book's ledger of record
(ledger.json: cash, positions, fills, equity history) and its journal
of record (JOURNAL.md: signed conditional cards with their triggers,
invalidations and windows, and the buy/sell decisions). Current
prices (benchmark closes, position marks) come only from the
sanctioned Alpaca read route (the local-alpaca-paper bars CLI, SIP
feed); a price that cannot be fetched is never invented: the
benchmark line is omitted with a note, and a position shows its
entry with no mark.

Fail-closed rules: if the ledger cannot be read or does not parse,
this refresher still writes the data file, in a dated "unavailable"
state, so the strip shows that the book data is unavailable as of a
named time instead of silently carrying stale numbers. Exit 0 when
the data file was written (either state), 2 when it could not be
written at all.

The hub section and script tag are producer-owned here, injected
once and guarded, in the same pattern as refresh_hub.py's marked
injections: the section sits in the hub's prefix, which
refresh_hub.py's restructure preserves verbatim, and it carries no
<h2> of its own, because the restructure splits the page at its
first <h2>.

Usage: python3 refresh_book_strip.py
Test hooks (used by test_book_strip_20261104.py): the environment
variables BOOK_STRIP_BOOK_DIR, BOOK_STRIP_OUT and BOOK_STRIP_HUB
redirect the book directory, the output file and the hub file.
"""

import json
import os
import re
import subprocess
import sys
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

ET = ZoneInfo("America/New_York")
BOOK_DIR = Path(os.environ.get(
    "BOOK_STRIP_BOOK_DIR",
    os.path.expanduser("~/workspace/midna-book")))
OUT_PATH = Path(os.environ.get(
    "BOOK_STRIP_OUT", str(HERE / "book-strip" / "data.json")))
HUB_PATH = Path(os.environ.get("BOOK_STRIP_HUB", str(HERE / "index.html")))
BARS_CLI = os.path.expanduser(
    "~/workspace/custom-skills/local-alpaca-paper/bin/alpaca_get_bars_1h.py")

MONTHS = ["January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November",
          "December"]


def _atomic_write(path: Path, text: str) -> None:
    tmp = path.with_name(path.name + ".atomic-tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def money(v) -> str:
    v = float(v)
    if abs(v - round(v)) < 0.005:
        return "$%s" % format(int(round(v)), ",")
    return "$%s" % format(v, ",.2f")


def price(v) -> str:
    return format(float(v), ",.2f")


def pct(v) -> str:
    return "%+.2f%%" % (float(v) * 100.0)


def plain_date(d: date) -> str:
    return "%s %d, %d" % (MONTHS[d.month - 1], d.day, d.year)


def stamp_et(now: datetime) -> str:
    now = now.astimezone(ET)
    hour = now.hour % 12 or 12
    ampm = "AM" if now.hour < 12 else "PM"
    return "%s, %d:%02d %s ET" % (plain_date(now.date()), hour,
                                  now.minute, ampm)


def freshest_session(now: datetime) -> str:
    try:
        from completed_session import freshest_completed_session
        return freshest_completed_session(now)
    except Exception:
        day = now.astimezone(ET).date()
        if day.weekday() < 5 and now.astimezone(ET).time().hour >= 17:
            return day.isoformat()
        day -= timedelta(days=1)
        while day.weekday() >= 5:
            day -= timedelta(days=1)
        return day.isoformat()


# ---------------------------------------------------------------- bars

def fetch_bars(symbol: str, timeframe: str, start: str, end: str):
    """Bars from the sanctioned read route, or None on any failure."""
    try:
        out = subprocess.run(
            [BARS_CLI, "--symbol", symbol, "--timeframe", timeframe,
             "--feed", "sip", "--start", start, "--end", end,
             "--limit", "10000"],
            capture_output=True, text=True, timeout=180)
    except Exception:
        return None
    if out.returncode != 0:
        return None
    at = out.stdout.find("[")
    if at < 0:
        return None
    try:
        bars = json.loads(out.stdout[at:])
    except Exception:
        return None
    return bars if isinstance(bars, list) else None


def _pull_end(through: str) -> str:
    """End of a daily pull that covers the session `through`: the
    next morning at 05:00Z. The read route refuses a window whose
    end runs past the present moment (its recent-SIP rule answers
    403), so a pull never reaches beyond the last completed
    session's own morning-after."""
    return (date.fromisoformat(through)
            + timedelta(days=1)).isoformat() + "T05:00:00Z"


def _cap_end(end: str, cap_z: str) -> str:
    """A pull window never reaches into the read route's recent-SIP
    blind spot: the route answers 403 ("subscription does not
    permit querying recent SIP data") for a window whose end is in
    the future or within about 15 minutes of the present moment.
    _pull_end's morning-after is still hours ahead when the strip
    is generated in the evening, which cost the benchmark line
    every evening (BOOK-STRIP-BENCH-WINDOW-20261104). Capping at
    the present moment less the estate's established 20-minute
    buffer loses nothing: no daily bar exists past the last
    completed session's close, so the capped window still covers
    the session in full."""
    return min(end, cap_z)


def benchmark(symbol: str, inception: date, through: str):
    """(pct, end_date) for a benchmark from its inception-date close
    to the freshest completed session's close, or None."""
    start = (inception - timedelta(days=7)).isoformat() + "T00:00:00Z"
    end = _cap_end(_pull_end(through),
                   (datetime.now(timezone.utc)
                    - timedelta(minutes=20)).strftime(
                       "%Y-%m-%dT%H:%M:%SZ"))
    bars = fetch_bars(symbol, "1D", start, end)
    if not bars:
        return None
    by_date = {}
    for b in bars:
        try:
            by_date[b["t"][:10]] = float(b["c"])
        except Exception:
            continue
    days = sorted(d for d in by_date if d <= through)
    if len(days) < 1:
        return None
    start_day = None
    for d in days:
        if d >= inception.isoformat():
            start_day = d
            break
    if start_day is None:
        return None
    end_day = days[-1]
    if by_date[start_day] == 0:
        return None
    return (by_date[end_day] / by_date[start_day] - 1.0, end_day)


def mark_for(symbol: str, now: datetime):
    """(mark, as_of_words) from the freshest bars the route serves,
    or (None, None). Tries recent 10-minute bars first (end capped
    20 minutes back, the panel cure), then the last daily close."""
    end = now.astimezone(timezone.utc) - timedelta(minutes=20)
    start = end - timedelta(hours=8)
    bars = fetch_bars(symbol, "10Min",
                      start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                      end.strftime("%Y-%m-%dT%H:%M:%SZ"))
    if bars:
        try:
            last = bars[-1]
            t = datetime.fromisoformat(
                last["t"].replace("Z", "+00:00")).astimezone(ET)
            hour = t.hour % 12 or 12
            ampm = "AM" if t.hour < 12 else "PM"
            return float(last["c"]), "%s, %d:%02d %s ET" % (
                plain_date(t.date()), hour, t.minute, ampm)
        except Exception:
            pass
    through = freshest_session(now)
    end_d = _pull_end(through)
    start_d = (date.fromisoformat(through)
               - timedelta(days=10)).isoformat() + "T00:00:00Z"
    bars = fetch_bars(symbol, "1D", start_d, end_d)
    if bars:
        try:
            last = [b for b in bars if b["t"][:10] <= through][-1]
            return float(last["c"]), "the %s close" % plain_date(
                date.fromisoformat(last["t"][:10]))
        except Exception:
            pass
    return None, None


# ---------------------------------------------------------------- journal

FIELD_RE = re.compile(r"^- ([A-Za-z][A-Za-z0-9 ()]*?): (.*)$")


def _field(fields, name):
    """A journal field by its plain name; fields whose written name
    carries a parenthetical (Fill (appended when priced)) answer to
    their plain name too."""
    if name in fields:
        return fields[name]
    for key, value in fields.items():
        if key.startswith(name + " ("):
            return value
    return ""
HEAD_RE = re.compile(
    r"^(\d{4})-(\d{2})-(\d{2})(?: (\d{2}):(\d{2}) ET)? · ([A-Z]+)"
    r"( \(DRAFT, unsigned\))? · (J-\d{8}-[A-Z0-9]+)\s*$")


def parse_journal(text: str):
    entries = []
    for chunk in re.split(r"^## ", text, flags=re.M)[1:]:
        head, _, body = chunk.partition("\n")
        m = HEAD_RE.match(head.strip())
        if not m:
            continue
        fields = {}
        for line in body.splitlines():
            fm = FIELD_RE.match(line)
            if fm:
                fields[fm.group(1).strip()] = fm.group(2).strip()
        entries.append({
            "date": date(int(m.group(1)), int(m.group(2)),
                         int(m.group(3))),
            "time": (m.group(4), m.group(5)),
            "type": m.group(6),
            "draft": bool(m.group(7)),
            "id": m.group(8),
            "fields": fields,
        })
    return entries


def _first_number_after(text: str, word: str):
    m = re.search(word + r"[^0-9]*([\d,]+\.?\d*)", text)
    if not m:
        return None
    try:
        return float(m.group(1).replace(",", ""))
    except ValueError:
        return None


def card_expiry(entry) -> date:
    """The card's expiry date from its own written window; a card
    with no dated window is a day card and expires on its own date
    (the book's written pattern: KDP, 2026-11-02)."""
    levels = _field(entry["fields"], "Levels")
    decision = _field(entry["fields"], "Decision")
    dated = []
    for m in re.finditer(r"(\d{4})-(\d{2})-(\d{2}) close",
                         levels + " " + decision):
        dated.append(date(int(m.group(1)), int(m.group(2)),
                          int(m.group(3))))
    if dated:
        return max(dated)
    if "Window" in levels:
        days = [date(int(a), int(b), int(c)) for a, b, c in
                re.findall(r"(\d{4})-(\d{2})-(\d{2})", levels)]
        if days:
            return max(days)
    return entry["date"]


def live_cards(entries, today: date, now_et=None):
    """Signed conditional cards whose written window has not closed.
    Drafts are not cards until a later entry signs them under their
    own id, so drafts never appear here. A card expiring today is
    live until today's close: once the generation moment is past
    16:00 ET on the expiry date the card is done, and showing it
    for the rest of the evening would present an expired card as
    live (BOOK-STRIP-CARD-EVENING-20261104). Callers that pass no
    moment get the date-only rule."""
    cards = []
    for e in entries:
        if e["type"] != "ENTRY" or e["draft"]:
            continue
        decision = _field(e["fields"], "Decision")
        if not decision.startswith("CONDITIONAL CARD"):
            continue
        if "DRAFT" in decision[:40]:
            continue
        expiry = card_expiry(e)
        if expiry < today:
            continue
        if (expiry == today and now_et is not None
                and now_et.time() >= time(16, 0)):
            continue
        f = e["fields"]
        symbol = (_field(f, "Instrument")).strip()
        levels = _field(f, "Levels")
        trigger = _first_number_after(levels, "hold above")
        if trigger is None:
            trigger = _first_number_after(levels, "trigger")
        invalidation = _first_number_after(
            _field(f, "Invalidation"), "below")
        shares = None
        sm = re.search(r"share count (\d+) shares",
                       _field(f, "Size math"))
        if sm:
            shares = int(sm.group(1))
        hm = re.search(r"(\d+)[ -]minute hold", levels)
        hold = int(hm.group(1)) if hm else None
        if expiry == today:
            expiry_words = "Expires at today's close (%s)" % plain_date(
                expiry)
        else:
            expiry_words = "Expires at the %s close" % plain_date(expiry)
        line = "%s: buy %s if the price holds above %s%s; out on a " \
               "close below %s. %s." % (
                   symbol,
                   ("%d shares" % shares) if shares else "a probe",
                   price(trigger) if trigger else "?",
                   (" for %d minutes" % hold) if hold else "",
                   price(invalidation) if invalidation else "?",
                   expiry_words)
        cards.append({
            "id": e["id"], "symbol": symbol, "shares": shares,
            "trigger": trigger, "invalidation": invalidation,
            "expiry": expiry.isoformat(), "line": line,
        })
    return cards


def _fill_status(fill_text: str) -> str:
    m = re.search(r"[Ff]illed at \$?([\d,]+\.?\d*)", fill_text or "")
    if m:
        return "filled at $%s" % m.group(1)
    if "PENDING" in (fill_text or "").upper():
        return "the fill price is priced at the next book pass"
    if "UNFILLED" in (fill_text or "").upper() or \
            "no fill" in (fill_text or "").lower():
        return "not filled"
    return ""


def _when(entry) -> str:
    d = plain_date(entry["date"])
    if entry["time"][0]:
        hour = int(entry["time"][0]) % 12 or 12
        ampm = "AM" if int(entry["time"][0]) < 12 else "PM"
        return "%s, %d:%s %s ET" % (d, hour, entry["time"][1], ampm)
    return d


def recent_actions(entries, ledger, limit=5):
    actions = []
    seen = set()
    fills = ledger.get("fills") or []
    if isinstance(fills, list):
        for fl in reversed(fills):
            if not isinstance(fl, dict):
                continue
            symbol = fl.get("symbol") or fl.get("ticker") or ""
            shares = fl.get("shares") or fl.get("qty") or ""
            side = (fl.get("side") or "").lower()
            pr = fl.get("price") or fl.get("fill_price")
            when = fl.get("date") or fl.get("datetime") or ""
            if not symbol:
                continue
            seen.add((symbol, str(shares)))
            actions.append({
                "when": str(when),
                "line": "%s %s %s shares at %s" % (
                    "Bought" if side.startswith("b") else "Sold",
                    shares, symbol,
                    ("$" + price(pr)) if pr else "the charter price"),
            })
    for e in reversed(entries):
        if len(actions) >= limit:
            break
        decision = _field(e["fields"], "Decision")
        m = re.match(r"(BUY|SELL) (\d+) ([A-Z][A-Z.]*)", decision)
        if not m:
            continue
        side, shares, symbol = m.group(1), int(m.group(2)), m.group(3)
        if (symbol, str(shares)) in seen:
            continue
        seen.add((symbol, str(shares)))
        status = _fill_status(_field(e["fields"], "Fill"))
        line = "%s %d %s" % (
            "Buy decided:" if side == "BUY" else "Sell decided:",
            shares, symbol)
        if status:
            line += " (%s)" % status
        actions.append({"when": _when(e), "line": line})
    return actions[:limit]


# ---------------------------------------------------------------- ledger

def _pick(d, *keys):
    for k in keys:
        if isinstance(d, dict) and d.get(k) not in (None, ""):
            return d[k]
    return None


def _opening_fill(ledger, position, symbol):
    """The fill that opened this position, from the ledger's own
    fills: the fill carrying the position's decision id when there
    is one, else the first buy fill in the position's symbol."""
    fills = ledger.get("fills") or []
    if not isinstance(fills, list):
        return None
    did = _pick(position, "decision_id", "decision", "journal_id")
    first_buy = None
    for fl in fills:
        if not isinstance(fl, dict):
            continue
        if str(_pick(fl, "symbol", "ticker")) != str(symbol):
            continue
        if did and fl.get("decision_id") == did:
            return fl
        if first_buy is None and \
                (fl.get("side") or "").lower().startswith("b"):
            first_buy = fl
    return first_buy


def _journal_invalidation(entries, decision_id):
    """The invalidation written on the journal entry that opened
    the position (its J-id), read the way live_cards reads a
    card's: the number after "below" in its Invalidation field."""
    if not decision_id:
        return None
    for e in entries or ():
        if e.get("id") == decision_id:
            return _first_number_after(
                _field(e["fields"], "Invalidation"), "below")
    return None


def position_rows(ledger, entries, now):
    raw = ledger.get("positions") or []
    items = []
    if isinstance(raw, dict):
        items = [dict(v, symbol=k) if isinstance(v, dict) else {}
                 for k, v in raw.items()]
    elif isinstance(raw, list):
        items = [p for p in raw if isinstance(p, dict)]
    rows = []
    for p in items:
        symbol = _pick(p, "symbol", "ticker", "instrument")
        if not symbol:
            continue
        shares = _pick(p, "shares", "qty", "quantity")
        # The ledger's position records name these fields in the
        # book's own schema (entry_fill, invalidation_close_below);
        # a record that does not restate them is completed from
        # the opening fill and the journal entry that opened it.
        entry_price = _pick(p, "entry_price", "avg_entry_price",
                            "entry_fill", "fill_price", "price")
        entry_date = _pick(p, "entry_date", "date", "opened")
        invalidation = _pick(p, "invalidation",
                             "invalidation_close_below", "stop")
        if entry_price is None or entry_date is None:
            fill = _opening_fill(ledger, p, symbol)
            if fill is not None:
                if entry_price is None:
                    entry_price = _pick(fill, "fill_price", "price")
                if entry_date is None:
                    ts = _pick(fill, "date", "bar_ts",
                               "decision_ts", "datetime")
                    if ts:
                        entry_date = str(ts)[:10]
        if invalidation is None:
            invalidation = _journal_invalidation(
                entries, _pick(p, "decision_id", "decision",
                               "journal_id"))
        mark, mark_as_of = mark_for(str(symbol), now)
        row = {
            "symbol": str(symbol), "shares": shares,
            "entry_price": entry_price, "entry_date": entry_date,
            "invalidation": invalidation, "mark": mark,
            "mark_as_of": mark_as_of,
        }
        parts = ["%s: %s shares" % (symbol, shares)]
        if entry_price:
            parts.append("in at %s" % price(entry_price))
        if entry_date:
            try:
                parts.append("on %s" % plain_date(
                    date.fromisoformat(str(entry_date)[:10])))
            except ValueError:
                parts.append("on %s" % entry_date)
        line = ", ".join(parts) + "."
        if mark and entry_price:
            upct = mark / float(entry_price) - 1.0
            row["unrealized_pct"] = upct
            line += " Now %s (%s), as of %s." % (
                price(mark), pct(upct), mark_as_of)
        elif mark:
            line += " Now %s, as of %s." % (price(mark), mark_as_of)
        else:
            line += " A current price could not be fetched, so no " \
                    "mark is shown."
        if not entry_price:
            line += " Its entry price is not in the book's " \
                    "record, so no gain or loss is shown."
        if invalidation:
            line += " Out on a close below %s." % price(invalidation)
        else:
            line += " No exit line is recorded in the book's " \
                    "record for this position."
        row["line"] = line
        rows.append(row)
    return rows


# ---------------------------------------------------------------- state

def build_state(now: datetime) -> dict:
    generated = stamp_et(now)
    try:
        ledger = json.loads(
            (BOOK_DIR / "ledger.json").read_text(encoding="utf-8"))
        journal_text = (BOOK_DIR / "JOURNAL.md").read_text(
            encoding="utf-8")
    except Exception as exc:
        return {
            "state": "unavailable",
            "generated_at_et": generated,
            "title": "Midna's Book",
            "unavailable_line":
                "Book data unavailable as of %s: the book's own "
                "record could not be read (%s). No figures are shown "
                "rather than old ones." % (generated,
                                           type(exc).__name__),
        }
    entries = parse_journal(journal_text)
    today = now.astimezone(ET).date()
    inception = date.fromisoformat(
        str(ledger.get("inception", "2026-10-30"))[:10])
    starting = float(ledger.get("starting_equity") or 100000.0)
    cash = float(ledger.get("cash") or 0.0)
    positions = position_rows(ledger, entries, now)
    if positions and all(p["mark"] for p in positions):
        equity = cash + sum(float(p["shares"]) * float(p["mark"])
                            for p in positions)
    elif positions:
        hist = ledger.get("equity_history") or []
        equity = float(hist[-1]["equity"]) if hist else cash
    else:
        equity = cash
    book_pct = equity / starting - 1.0 if starting else 0.0
    through = freshest_session(now)
    bench_bits = []
    bench = {}
    for sym in ("SPY", "QQQ"):
        got = benchmark(sym, inception, through)
        if got:
            bench[sym.lower() + "_pct"] = got[0]
            bench_bits.append("%s %s" % (sym, pct(got[0])))
    perf = "Since %s: the book %s" % (plain_date(inception),
                                      pct(book_pct))
    if bench_bits:
        perf += " · " + " · ".join(bench_bits) + \
            " (index closes through %s)" % plain_date(
                date.fromisoformat(through))
    else:
        perf += " · the index comparison could not be fetched this " \
                "run and is left out rather than guessed"
    cards = live_cards(entries, today, now_et=now.astimezone(ET))
    actions = recent_actions(entries, ledger)
    state = {
        "state": "ok",
        "generated_at_et": generated,
        "title": "Midna's Book",
        "simulated_note":
            "A simulated $100,000 paper trading book, run by Midna, "
            "this terminal's own trader. It is not real money. Every "
            "figure below comes straight from the book's own ledger "
            "and journal, orders, cards, fills and all.",
        "equity": equity, "cash": cash,
        "equity_line": "Equity %s · Cash %s" % (money(equity),
                                                money(cash)),
        "performance_line": perf,
        "bench": bench,
        "positions": positions,
        "positions_line": None if positions else
            "No open positions. The book is flat.",
        "cards": cards,
        "cards_line": None if cards else
            "No live cards right now: nothing is waiting on a price.",
        "actions": actions,
        "actions_line": None if actions else
            "No fills or exits yet.",
        "flat": not positions,
        "source_line": "Source: the book's ledger and journal, read "
                       "at %s." % generated,
    }
    try:
        import terminal_common as _tc
        state = _tc.stamp_for_script(state, __file__)
    except Exception:
        pass
    return state


# ---------------------------------------------------------------- hub

STRIP_STYLE = (
    "<style>\n"
    "#book-strip{border:2px solid #0b3b46;border-radius:10px;"
    "background:#eef5f2;padding:16px 18px;margin:0 0 22px}\n"
    "#book-strip .bs-title{font-size:20px;font-weight:700;"
    "margin:0 0 4px;color:#0b3b46}\n"
    "#book-strip .bs-note{margin:0 0 10px;max-width:46em}\n"
    "#book-strip .bs-stats{font-weight:600;margin:0 0 4px}\n"
    "#book-strip .bs-perf{margin:0 0 10px}\n"
    "#book-strip .bs-h{font-weight:700;margin:12px 0 4px;"
    "color:#0b3b46}\n"
    "#book-strip ul{margin:0 0 4px;padding-left:20px}\n"
    "#book-strip .bs-src{margin:10px 0 0;font-size:13.5px;"
    "color:#5b6b75}\n"
    "</style>\n")

STRIP_SECTION = (
    "<section id=\"book-strip\">\n" + STRIP_STYLE +
    "<p class=\"bs-title\">Midna's Book</p>\n"
    "<p class=\"bs-note\">A simulated $100,000 paper trading book. "
    "Its latest record loads here.</p>\n"
    "</section>\n")


def ensure_hub(hub_path: Path) -> bool:
    """Inject the strip section and its script tag once, guarded.
    Returns True when the hub was changed."""
    try:
        hub = hub_path.read_text(encoding="utf-8")
    except OSError:
        return False
    out = hub
    if 'src="book-strip.js"' not in out:
        anchor = '<script src="shared.js" defer></script>'
        if anchor in out:
            out = out.replace(
                anchor, anchor + '\n<script src="book-strip.js" '
                'defer></script>', 1)
    if 'id="book-strip"' not in out:
        anchor = '<div class="wrap">'
        if anchor in out:
            out = out.replace(anchor, anchor + "\n" + STRIP_SECTION, 1)
    if out != hub:
        _atomic_write(hub_path, out)
        return True
    return False


def main() -> int:
    now = datetime.now(ET)
    state = build_state(now)
    try:
        OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        _atomic_write(OUT_PATH, json.dumps(state, indent=1,
                                           sort_keys=True) + "\n")
    except OSError as exc:
        print("FAIL: book strip data file could not be written: %s"
              % exc)
        return 2
    ensure_hub(HUB_PATH)
    print("book strip refreshed: state=%s equity=%s positions=%d "
          "cards=%d actions=%d" % (
              state.get("state"), state.get("equity"),
              len(state.get("positions") or []),
              len(state.get("cards") or []),
              len(state.get("actions") or [])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
