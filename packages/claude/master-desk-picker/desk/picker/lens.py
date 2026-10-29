"""The eight lenses and Conviction 8 on the Fear-Day Buy List's cards (data only; desk/terminal/read/lenses.py).

SCOPE (InfinityBlade, 2026-10-27):
  Surface   this module; the picker cards' `lens` key (fearday.ALLOWED / CARD, the edition's contract line).
  Constraints  the same measure the board's cards carry (lenses.Board.read over the roster's stored reads): copied, not
            recomputed; no stage, word or tone (those belong to a board plan, which a picker card does not have); a
            card whose name has no measured read carries no `lens`, never a guess.
  Outcome   card["lens"] = {states, n, red, ok, cats, c8st, c8} where the roster has a read of the name.
  Proof     tests/test_picker_lens.py."""

KEYS = {"states", "n", "red", "ok", "cats", "c8st", "c8"}


def attach(block, board):
    """add `lens` to every card of the picker block that the lens board has a read for -> {"with": n, "without": [symbols]}"""
    got, miss = 0, []
    for lane in ("buy", "watch", "small"):
        for card in block.get(lane) or ():
            card.pop("lens", None)
            try:
                r = board.read(card["symbol"])
            except Exception:                                   # noqa: BLE001  (a lens never stops the edition)
                r = None
            if not r:
                miss.append(card["symbol"])
                continue
            card["lens"] = {k: r[k] for k in KEYS if k in r and (k != "c8" or r[k] is not None)}
            got += 1
    return {"with": got, "without": miss}
