"""v3 sleeve module for bb_rsi_divergence — faithful port (batch 1).

Strategy + v2 adapter are byte-identical copies under sleeves/ and
adapters/ (strategy hash-pinned by tests/test_port_batch1_blockers.py).
This module is only the v3 worker entrypoint: evaluate(view, ctx)
rebuilds the v2 SleeveContext from the cycle snapshot and delegates.
INPUTS is the producer-registry declaration for this sleeve.

CR-4 cure (2026-11-12): before delegating, the entrypoint scopes
sctx.positions to this sleeve's OWN journal-derived book. The v2
adapter builds slice_state (and therefore the sleeve's concurrency
cap) from ctx.positions, which the snapshot fills with the whole
broker account; the replay (CR4-REPLAY.md) proved the cap read
3 - 15 = -12 against a sleeve that has never held a position,
blocking a third of all evaluations and killing the only signal
it ever printed. The derivation is desk3.virtual_book's, the same
one the dispatcher's virtual-book dual-read uses. The cap itself
is untouched; what is counted changes. On any derivation failure
the account list is left exactly as it was: the cure may fail
back to the old behaviour, never past it.
"""
import importlib
import json
import os
from adapters3._snapshot_ctx import SnapshotSleeveContext

SLEEVE_ID = "bb_rsi_divergence"
INPUTS = ['bars', 'positions', 'quotes', 'session_fills']

_BOOK_CACHE = {"sig": None, "book": None}


def _derived_book(root):
    """The full dispatcher-journal-derived book, cached on the
    generation files' (path, size, mtime) signature: evaluations
    repeat every cycle and the derivation is a full journal scan."""
    from desk3.journal import journal_generations
    paths = journal_generations(
        os.path.join(root, "state", "dispatcher.jsonl"))
    sig = []
    for p in paths:
        try:
            st = os.stat(p)
            sig.append((p, st.st_size, st.st_mtime_ns))
        except OSError:
            sig.append((p, -1, -1))
    sig = tuple(sig)
    if _BOOK_CACHE["sig"] != sig:
        from desk3.virtual_book import derive_book_from_journals
        _BOOK_CACHE["book"] = derive_book_from_journals(paths)
        _BOOK_CACHE["sig"] = sig
    return _BOOK_CACHE["book"]


def own_positions(positions, own, planned_syms=()):
    """The account rows this sleeve actually owns, by any of the
    three sleeve-owned attributions: the row's own intent_id names
    this sleeve (the desk's readback carries the originating
    intent), the journal-derived book holds a nonzero quantity
    for the symbol, or the sleeve's persisted state carries an
    entry plan for the symbol (plans are written only for its own
    entries). Broker fields (avg_price, opened_at) are preserved
    from the account rows; everything unattributed is dropped,
    never netted or re-attributed."""
    own_syms = {sym for sym, qty in (own or {}).items() if qty}
    planned = set(planned_syms or ())
    out = []
    for p in positions or []:
        iid = str(p.get("intent_id") or "")
        if iid.startswith(SLEEVE_ID + "-") \
                or p.get("symbol") in own_syms \
                or p.get("symbol") in planned:
            out.append(p)
    return out


def _planned_symbols(state_dir):
    try:
        with open(os.path.join(state_dir,
                               "bb_rsi_state.json")) as fh:
            state = json.load(fh)
        return set((state.get("plans") or {}).keys())
    except (OSError, ValueError):
        return set()


def _scope_positions_to_own_book(sctx):
    try:
        root = os.path.dirname(os.path.dirname(sctx._state_dir))
        from desk3.virtual_book import sleeve_positions
        own = sleeve_positions(_derived_book(root), SLEEVE_ID)
        sctx.positions = own_positions(
            sctx.positions, own, _planned_symbols(sctx._state_dir))
    except Exception as exc:  # fail back to the old behaviour only
        sctx.logs.append(f"own_book_scope_failed: {exc!r}")


def evaluate(view, ctx):
    import importlib
    sctx = SnapshotSleeveContext(SLEEVE_ID, view, ctx)
    sctx._journal = os.path.join(sctx._state_dir, "journal.jsonl")
    _scope_positions_to_own_book(sctx)
    return importlib.import_module("adapters.bb_rsi_divergence").evaluate(sctx) or []
