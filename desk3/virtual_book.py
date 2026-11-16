"""Per-sleeve virtual book: shadow read (SLEEVE-VIRTUAL-BOOK-DIVERGENCE).

The defect (parent of the BROKER-422-CLASS): sleeves read the AGGREGATE
broker book as their own. On Tue 2026-11-10 six sleeves each submitted a
sell_to_close for the same 13 SPY because each one saw the aggregate 13
as its position; the broker answered 42210000 (position intent
mismatch) 27 times across 15 sleeves, and the dispatcher exit guards
fired 3,094 times against positions the sleeves did not own.

The cure's semantics, landed here as a SHADOW READ only: a sleeve's
book is derived from its own dispatcher journal fills, nothing else.
This module is pure (rows in, books out) and is NOT imported by the
live dispatch path yet. The register row closes when a sleeve reads
its own journal-derived book in a live cycle; this increment exists so
that derivation has one proven implementation, fixture-tested against
the burst shape that produced the 422 class, instead of a design note.

Derivation rules (deliberately minimal):
- Only journal rows with event == "fill" move a book.
- A fill's signed quantity is +qty for side "buy", -qty for "sell".
- Fills carry sleeve and symbol in the journal (verified on the live
  journal's fill rows); rows missing either are skipped, never guessed.
- The aggregate book is the per-symbol sum across sleeves, i.e. what
  the broker book shows; it is computed here only for comparison.
"""

from collections import defaultdict


def _signed_qty(row):
    qty = row.get("qty")
    if qty is None:
        return 0.0
    qty = float(qty)
    side = (row.get("side") or "").lower()
    if side == "buy":
        return qty
    if side == "sell":
        return -qty
    return 0.0


def derive_book(rows):
    """rows: iterable of dispatcher journal row dicts.

    Returns {(sleeve, symbol): {"qty": float, "fills": int}} built from
    fill rows only.
    """
    qty = defaultdict(float)
    fills = defaultdict(int)
    for row in rows:
        if row.get("event") != "fill":
            continue
        sleeve = row.get("sleeve")
        symbol = row.get("symbol")
        if not sleeve or not symbol:
            continue
        key = (sleeve, symbol)
        qty[key] += _signed_qty(row)
        fills[key] += 1
    return {key: {"qty": qty[key], "fills": fills[key]} for key in qty}


def aggregate_book(book):
    """Per-symbol totals across sleeves (the broker-book view)."""
    agg = defaultdict(float)
    for (_sleeve, symbol), cell in book.items():
        agg[symbol] += cell["qty"]
    return dict(agg)


def sleeve_positions(book, sleeve):
    """The book one sleeve owns under the derivation: nonzero only."""
    return {
        symbol: cell["qty"]
        for (owner, symbol), cell in book.items()
        if owner == sleeve and cell["qty"] != 0.0
    }


def iter_journal_rows(journal_paths):
    """Stream journal rows from generation files, in path order.

    Malformed lines are skipped (journal generations carry a small
    number of torn tail lines); the derivation never guesses.
    """
    import json

    for path in journal_paths:
        try:
            handle = open(path, "r", encoding="utf-8")
        except OSError:
            continue
        with handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except ValueError:
                    continue


def derive_book_from_journals(journal_paths):
    """The full derived book from dispatcher journal generations."""
    return derive_book(iter_journal_rows(journal_paths))


def exit_divergence(book, sleeve, symbol, broker_qty):
    """One exit's dual-read comparison (VIRTUAL-BOOK live staging).

    The sleeve's aggregate-reading belief about its position in
    `symbol` is the broker book's `broker_qty` (the current live
    behaviour). Its derived position is what its own fills say.
    Returns None when the two agree (the common case: the sleeve
    owns exactly the aggregate, or neither exists), else a dict
    naming the divergence kind:
    - "no_sleeve_position": derived 0 while the broker book is
      nonzero — the 2026-11-10 burst shape; an aggregate-driven
      exit for this sleeve can only draw a 422 or open a position.
    - "sign_mismatch": derived and broker disagree in sign — the
      sleeve's position is netted against another sleeve's.
    - "qty_differs": same sign, different size — an aggregate-
      driven exit would close more (or less) than the sleeve owns.
    """
    derived = sleeve_positions(book, sleeve).get(symbol, 0.0)
    if derived == broker_qty:
        return None
    if derived == 0.0:
        kind = "no_sleeve_position"
    elif derived * broker_qty < 0:
        kind = "sign_mismatch"
    else:
        kind = "qty_differs"
    return {
        "sleeve": sleeve,
        "symbol": symbol,
        "derived_qty": derived,
        "broker_qty": broker_qty,
        "kind": kind,
    }


def netted_divergences(book):
    """Sleeve positions the aggregate book nets to zero.

    Shape: sleeve A is long and sleeve B is short the same symbol in
    offsetting size, so the aggregate reads flat while each sleeve's
    own book is nonzero. Any logic reading the aggregate (the current
    live behaviour) cannot see either position; the derived book can.
    Returns a sorted list of {"sleeve", "symbol", "derived_qty"}.
    """
    agg = aggregate_book(book)
    out = []
    for (sleeve, symbol), cell in sorted(book.items()):
        if cell["qty"] != 0.0 and agg.get(symbol, 0.0) == 0.0:
            out.append(
                {
                    "sleeve": sleeve,
                    "symbol": symbol,
                    "derived_qty": cell["qty"],
                    "aggregate_qty": 0.0,
                }
            )
    return out
