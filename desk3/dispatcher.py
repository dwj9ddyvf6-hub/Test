"""Dispatcher (V3-SCOPE §7.4): the ONE writer to the paper door.
Per-sleeve virtual slices with intent-time buying-power checks (v2
semantics), idempotent v3-namespaced client order ids, fills ONLY from
broker read-back — a submit ACK is never a fill."""
from __future__ import annotations
import contextlib, fcntl, json, os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from .journal import append_line, read_lines
from .models import validate_intent, client_order_id, \
    client_order_id_untruncated, IntentError, OCC_RE

ET = ZoneInfo("America/New_York")
# BROKER-PENDING-DRAIN-20261026: per-cycle drain cap. One drained entry
# costs at most 3 bounded submit attempts + 1 read-back (~1s of retry
# backoff in the worst transient case), so 20 entries bound the added
# pre-dispatch latency to ~20s inside a 60s cycle and can never starve
# new intents; leftovers stay in the store for the next cycle (a
# same-session backlog still clears at 20/cycle = 1200/hour).
DRAIN_CAP = 20
# Soft cap on live pending entries: the store holds ONLY live entries
# (terminal outcomes and stale-session entries are removed, and both
# files are compacted on every removal), so file size tracks the live
# backlog, never the day's history.
MAX_PENDING_ENTRIES = 1000
# DRAIN-HOLD-20261104: a pending entry that has burned this many
# submit attempts across drains ends drained_terminal
# (attempts_exhausted) instead of retrying forever; 25 attempts at
# the drain cadence is far past any transient class observed live.
MAX_DRAIN_ATTEMPTS = 25


def _broker_unavailable_class(status):
    """DRAIN-CLASS-20261026: the broker-unavailable class — a
    transport/HTTP failure that is NEVER a terminal broker answer:
    no HTTP status at all (network/connection error), 403 (e.g.
    Alpaca 40310000 insufficient buying power — an account-state
    answer that can clear, not a rejection of the intent), 429, and
    5xx. Everything else with an HTTP status is a parsed broker
    response outside this class (e.g. 422 validation) and may be
    terminal. This ONE classifier serves both places the dispatcher
    distinguishes the classes: the bounded in-call retry and the
    pending drain."""
    if status is None:
        return True
    try:
        status = int(status)
    except (TypeError, ValueError):
        return False
    return status in (403, 429) or status >= 500


# CANONICAL-DIALECT-20261030: the symbol translator lives in ONE
# place, desk3/broker_dialect.py, shared by emission (aster_batch1,
# aster_crypto) and by this door defence. It began as the
# BLOCKED-EXIT-20261029 door defence (perp/spot archive forms
# ADAUSDT, ADAUSD are not Alpaca symbols; the broker dialect is
# BASE/USD, diagnosis E9a/E9b: ADA/USD active+tradable, ADAUSDT 404)
# and was widened to the Coinbase dashed form (BTC-USD) when the
# aster_batch1 emission translator was folded into the same module.
# The names below stay as re-exports: existing blockers import them
# from here.
from .broker_dialect import (  # noqa: E402
    CRYPTO_BASES as _CRYPTO_BASES,
    normalize_broker_symbol as _normalize_broker_symbol,
    is_crypto_symbol as _is_crypto_symbol,
    broker_time_in_force as _broker_time_in_force)


# BLOCKED-EXIT-20261029: 40310000 is shared by three DIFFERENT broker
# answers. Only one of them (insufficient buying power) is an
# account-state answer that can clear; the others are terminal
# verdicts about THIS intent/order pair, proven live 2026-10-29:
# "potential wash trade detected" (an opposite-side order rests),
# "insufficient qty available / held_for_orders" (a resting close
# already reserves the position), "position intent mismatch" (422),
# "insufficient balance" (crypto close against a zero balance).
# Retrying them burned 378 attempts on phantom exits; they are never
# retried and never re-queued.
_TERMINAL_403_MARKERS = ("potential wash trade",
                         "insufficient qty available",
                         "held_for_orders",
                         "position intent mismatch",
                         "insufficient balance")


def _terminal_broker_answer(status, body):
    """True when the broker's answer is a terminal verdict about this
    intent (see _TERMINAL_403_MARKERS), as opposed to the transient
    broker-unavailable class. Body may ride the exception's .body or
    its message text."""
    if status != 403:
        return False
    text = str(body or "")
    return any(m in text for m in _TERMINAL_403_MARKERS)


_POSITION_INTENTS = ("buy_to_open", "buy_to_close",
                     "sell_to_open", "sell_to_close")

# EXIT-REASON-FIELDS-20261115: the closed strategy-reason enum for
# exit records. Vein 3 dig S1 (2026-11-15) proved zero of 1,526
# dispatcher exit fills carried a strategy reason anywhere (fills,
# journals, broker orders): sleeves state their exit triggers only
# as prose ("{sid}_stop15", "time_exit_40s", "aster_deadline_
# fixed16 held=16.0h"), so the WHY of every fleet exit was
# ungradable. The classifier below is the single funnel that maps
# an exit intent's own prose and fields into the enum at emission;
# every exit-record writer (cycle journal intent record, _reject
# rows, the fill row, sweep-imported fills) stamps through it or
# through the unknown_with_cause form it defines.
EXIT_REASONS = ("stop", "target", "horizon", "signal_flip",
                "manual", "pooled_close", "unknown_with_cause")
_CLOSE_INTENTS = ("buy_to_close", "sell_to_close")


def is_exit_intent(intent):
    """The D-GATE-20261025 exit predicate, shared by every writer
    that stamps an exit record: the exit kind, or a closing
    position_intent. Side alone never makes an exit."""
    return intent.get("kind") == "exit" or intent.get(
        "position_intent") in _CLOSE_INTENTS


def _exit_num(text, key):
    m = _re.search(key + r"=([0-9]+(?:\.[0-9]+)?)", text)
    if not m:
        return None
    try:
        return float(m.group(1))
    except ValueError:
        return None


def classify_exit_reason(intent, sleeve_id=None):
    """Classify an exit intent's strategy reason into EXIT_REASONS
    from the intent's own fields and reason prose. Returns
    (exit_reason, detail): detail carries the triggering values
    the path knows (stop price and its distance from the reference
    price, target price, horizon sessions, sessions held, the
    flipping signal's sleeve) and, for unknown_with_cause, the
    named cause plus the unclassified prose verbatim. A path that
    cannot classify stamps unknown_with_cause; omitting the field
    is the defect this cures."""
    text = str(intent.get("reason") or "")
    low = text.lower()
    detail = {}
    if text:
        detail["reason_text"] = text
    declared = intent.get("exit_reason")
    if declared in EXIT_REASONS and declared != "unknown_with_cause":
        return declared, detail
    m_held = _re.search(r"held=([0-9]+(?:\.[0-9]+)?)(h)?", low)
    if m_held:
        detail["held"] = float(m_held.group(1))
        if m_held.group(2):
            detail["held_unit"] = "hours"
    else:
        age = _exit_num(low, "age_sessions")
        if age is not None:
            detail["held"] = age
            detail["held_unit"] = "sessions"
    # Origin classes outrank trigger words: a manual or pooled
    # close may mention a stop without being one.
    if "manual" in low:
        return "manual", detail
    if "pooled" in low or "flatten" in low:
        return "pooled_close", detail
    stop_px = _exit_num(low, "stop")
    if stop_px is None:
        stop_px = intent.get("stop_price") or intent.get("stop")
    if stop_px is not None:
        try:
            detail["stop_price"] = float(stop_px)
        except (TypeError, ValueError):
            pass
    if "stop" in low:
        ref = _exit_num(low, "last")
        if ref is None:
            ref = intent.get("price_hint") or intent.get(
                "limit_price")
        if detail.get("stop_price") and ref:
            try:
                detail["stop_distance_frac"] = abs(
                    float(ref) - detail["stop_price"]) / float(ref)
            except (TypeError, ValueError, ZeroDivisionError):
                pass
        return "stop", detail
    tgt_px = _exit_num(low, "target")
    if tgt_px is None:
        tgt_px = intent.get("target")
    if tgt_px is not None:
        try:
            detail["target_price"] = float(tgt_px)
        except (TypeError, ValueError):
            pass
    if "target" in low or "take_profit" in low \
            or "take-profit" in low \
            or ("partial" in low and "trail" in low):
        if "partial" in low:
            detail["partial"] = True
        return "target", detail
    m_exp = _re.search(r"expiry=([0-9]{4}-[0-9]{2}-[0-9]{2})", low)
    if m_exp:
        detail["expiry"] = m_exp.group(1)
    m_hor = _re.search(r"time_exit_([0-9]+)s", low)
    if m_hor:
        detail["horizon_sessions"] = float(m_hor.group(1))
    if any(w in low for w in ("expiry", "settle", "deadline",
                              "horizon", "time_exit", "holding_bars",
                              "held=", "age_sessions", "max_hold",
                              "time_stop", "time stop")):
        return "horizon", detail
    if any(w in low for w in ("flip", "signal", "reversal", "cross",
                              "invalidation", "no_longer")):
        detail["signal"] = sleeve_id
        return "signal_flip", detail
    detail["cause"] = ("unclassified_sleeve_reason" if text
                       else "no_reason_on_exit_intent")
    return "unknown_with_cause", detail


def exit_reason_fields(intent, sleeve_id=None):
    """The record fields an exit writer stamps: {} for a non-exit
    intent, else exit_reason plus exit_detail, always both keys,
    so a reader can distinguish a cured record from a pre-cure
    one by the keys' presence alone."""
    if not is_exit_intent(intent):
        return {}
    reason, detail = classify_exit_reason(intent, sleeve_id)
    return {"exit_reason": reason, "exit_detail": detail}


def _cash_multiplier(symbol):
    """READINESS-DSP2-20261112: the ONE cash multiplier rule, the
    same one reconcile documents as OPTIONS-MULTIPLIER-SPEND
    (desk3/reconcile.py journal_derived): an OCC symbol's price is
    the per-share premium and its qty is contracts, so cash moves
    qty x price x 100. Equity and crypto stay x1. The dispatcher's
    entry cost, its reservation, and its fill cash updates all run
    through this helper; pre-cure they ran at x1 while reconcile
    and the CSP branch of process_intent applied x100, so an
    options entry was BP-checked and booked at 1/100 of its cost.
    """
    from .reconcile import _is_occ_symbol
    return 100.0 if _is_occ_symbol(symbol) else 1.0

import re as _re

_USDT_PAIR_SHAPE = _re.compile(r"^[A-Z0-9]{2,10}USDT$")


def _untranslatable_pair_shape(sym):
    """True when the symbol has a proven foreign crypto-pair SHAPE
    (the desk's own dialect definitions in desk3/models.py, plus
    the bare USDT pair form for unknown bases) yet the canonical
    translator left it unchanged, so the broker knows no such
    asset. Deliberately shape-bound, not suffix-bound: a Kraken
    perp symbol like PF_ADAUSD matches none of these shapes (the
    underscore namespace is a different venue's contract, and the
    kraken sleeves' e2e contract dispatches it), so it passes
    exactly as it did pre-cure; an equity-shaped symbol passes
    too. Caught by the first gate run of this cure
    (test_harden_cure_batch3 kraken e2e), narrowed same pass."""
    if not isinstance(sym, str) or "/" in sym:
        return False
    if _normalize_broker_symbol(sym) != sym:
        return False
    from .models import BARE_CRYPTO_USD_RE, COINBASE_PRODUCT_RE
    return bool(BARE_CRYPTO_USD_RE.match(sym)
                or COINBASE_PRODUCT_RE.match(sym)
                or _USDT_PAIR_SHAPE.match(sym))


def _intent_recorded_symbol(symbol):
    """INTENT-RECORDED-UNLISTED-20261116: True for symbols proven
    unlistable at the broker, whose entries exist to be graded as
    intents: ENJ/USD (42210000 asset-not-found, captured live
    repeatedly since 2026-10-31; Alpaca lists no ENJ pair) and the
    PF_ Kraken perpetual-futures keys (Alpaca lists no PF_
    contracts; PF-DOOR-20261104 proved the verdict deterministic).
    The sleeves emitting them are registered intent-graded: their
    roster rows state they evaluate and forward-grade from the
    dispatcher record, with execution failing closed at the broker
    seam. Recording the intent at the door IS their registered
    form; a broker submission adds only the 422 rows (71 distinct
    intents on Sunday 2026-11-15)."""
    if not isinstance(symbol, str):
        return False
    if symbol.startswith("PF_"):
        return True
    return _normalize_broker_symbol(symbol) == "ENJ/USD"


# ENJ-PAPER-20261116 (desk full audit escalation 2, owner ruling
# 2026-11-16 09:22 ET "Fix them"): the 22-sleeve ENJ class. ENJ/USD
# is proven unlisted at Alpaca (42210000 asset-not-found since
# 2026-10-31), so the class could evaluate on the desk's real Kraken
# spot tape yet never trade: entries were consumed as
# intent_recorded rows and exits terminated against an empty broker
# book. The class's execution form is now the free_kraken paper
# form, in-family with free_kraken_enj_spot's own Kraken book:
# intents from these sleeves in ENJ/USD are filled at the desk by
# the dispatcher against the Kraken feed price the intent carries
# (price_hint from the tape; limit_price, then the dispatcher's
# price_lookup, as fallbacks), journaled as ordinary fill rows
# stamped venue="kraken_paper" with their feed provenance, and
# booked into the sleeve's own slice exactly as a broker fill is.
# No ENJ intent from the class ever reaches submit_order. The
# PF_ class keeps the INTENT-RECORDED-UNLISTED-20261116 form
# untouched (a separate escalation), and test doubles keep the
# FakeBroker behavior the kraken e2e contracts pin.
ENJ_PAPER_SLEEVES = frozenset({
    "aster_abs_enj_4h",
    "aster_enj_nfs_fixed96_vol",
    "aster_enj_nfs_lost_full",
    "aster_enj_nfs_lost_vol",
    "aster_enj_nfs_norm_full",
    "aster_enj_nfs_norm_vol",
    "aster_enj_nfs_normfail_full",
    "aster_enj_nfs_normfail_vol",
    "aster_pub_enj_iu_body",
    "aster_r19_enjusdt_absorption_base_fixed16_fullcash",
    "aster_r19_enjusdt_absorption_base_fixed16_volume1pct",
    "aster_r19_enjusdt_absorption_negative_funding_fixed16_fullcash",
    "aster_r19_enjusdt_absorption_negative_funding_fixed16_volume1pct",
    "aster_r19_enjusdt_absorption_nonnegative_funding_fixed16_fullcash",
    "aster_r19_enjusdt_absorption_nonnegative_funding_fixed16_volume1pct",
    "aster_r19_enjusdt_breakout_base_fixed16_fullcash",
    "aster_r19_enjusdt_breakout_base_fixed16_volume1pct",
    "aster_r19_enjusdt_negative_funding_squeeze_fixed16_fullcash",
    "aster_r19_enjusdt_negative_funding_squeeze_fixed16_volume1pct",
    "aster_r19_enjusdt_negative_funding_squeeze_fixed96_fullcash",
    "free_kraken_enj_spot",
    "fwd_alpaca_enj_iu_body",
    # T474U-CRYPTO-PORT-20261116: the three t474u ENJ twins join the
    # class with the faithful port (desk3/t474u_crypto.py); same
    # Kraken spot tape, same journal-derived own book.
    "crypto_bratr_enj",
    "crypto_mfi_enj",
    "crypto_stdev_enj",
})
ENJ_PAPER_VENUE = "kraken_paper"


def _enj_paper_class(sleeve_id, symbol):
    """True when (sleeve, symbol) belongs to the ENJ paper class:
    one of the 22 ENJ sleeves trading ENJ/USD in any broker-dialect
    spelling (post-dialect intents carry the normalized form)."""
    if sleeve_id not in ENJ_PAPER_SLEEVES:
        return False
    if not isinstance(symbol, str):
        return False
    return _normalize_broker_symbol(symbol) == "ENJ/USD"


def _preflight_violation(intent, sleeve_id):
    """DOOR-PREFLIGHT-20261030: the A4 checklist (RESEARCH-R1 A4) for
    the field shapes this desk has PROVEN the broker 422s on, checked
    locally after dialect translation and before any submit, so a
    deterministic validation verdict is named at the door instead of
    burned on the wire. Returns a short reason string, or None when
    the intent is wire-clean under the proven rules. Deliberately
    conservative: only shapes with a captured 422 body or Alpaca's
    own error guide behind them reject here. stop_price riding on a
    market/limit intent is NOT a violation (the door never forwards
    it on those types; sleeves carry it as reference data), and a
    truncated client_order_id is NOT rejected (the COID-DEDUPE-
    20261031 ruling dropped the duplicated sleeve segment so
    constructed ids no longer reach the cap; a warning is
    journaled by the caller instead if one ever still does)."""
    sym = intent.get("symbol")
    if not isinstance(sym, str) or not sym:
        return "preflight_symbol_missing"
    if "|" in sym:
        # Captured live 2026-10-27: asset "AG|1Hour" not found.
        return "preflight_symbol_timeframe_suffix"
    if _untranslatable_pair_shape(sym):
        # A foreign-dialect pair the canonical translator cannot map
        # (unknown base): the broker knows no such asset.
        return "preflight_symbol_untranslatable_dialect"
    if sym == "ENJ/USD" and intent.get("kind") != "exit" \
            and intent.get("position_intent") not in (
                "buy_to_close", "sell_to_close") \
            and "enj" not in str(sleeve_id or "").lower():
        # CURE1-UNLISTED-20261102: ENJ/USD is PROVEN unlisted at the
        # broker (42210000 asset-not-found, captured live 2026-10-31
        # from free_kraken_enj_spot and again from s_mn_macd, a
        # multi-symbol sleeve that is not an ENJ sleeve; the owner
        # parked all 22 ENJ sleeves on this basis, BUGLOG
        # ENJ-ASSET-NOT-LISTED-20261030 / ENJ-PARK-20261031). An
        # entry in this symbol can never fill, so it is named at
        # the door instead of burned on the wire. Exits pass: a
        # held position must always be closable.
        # CURE2-ENJ-PREFLIGHT-SCOPE-20261102: the rule is scoped to
        # sleeves that are not ENJ-domiciled, which is the class
        # its root cause names. As first landed it also rejected
        # the 22 ENJ-domiciled sleeves (every roster id carrying
        # "enj"), breaking their e2e roundtrip blocker
        # (test_aster_batch7_blockers) and pre-judging the owner's
        # unpark condition: those sleeves are parked at the roster
        # level while ENJ is unlisted and never reach the door;
        # if the owner unparks them on listing, the door must not
        # still reject their own symbol.
        return "preflight_symbol_asset_not_listed"
    if intent.get("time_in_force") in ("cls", "opg") and (
            OCC_RE.match(sym) or _is_crypto_symbol(sym)):
        # OVERNIGHT-AUCTION-20261116 (B0-3): mirror of the
        # validate_intent auction admission — an auction tif on a
        # non-equity symbol that somehow reaches the dispatcher is
        # refused locally and never reaches the wire.
        return "preflight_auction_tif_on_non_equity"
    otype = intent.get("order_type", "market")
    if otype == "market" and intent.get("limit_price") is not None:
        # Alpaca error guide: market orders require no limit price
        # (40010001); the door forwards limit_price whenever set.
        return "preflight_market_with_limit_price"
    if _is_crypto_symbol(sym) \
            and intent.get("time_in_force", "day") not in ("gtc", "ioc"):
        # Captured live 2026-10-27: invalid crypto time_in_force.
        return "preflight_crypto_time_in_force"
    pi = intent.get("position_intent")
    if pi is not None and pi not in _POSITION_INTENTS:
        # Alpaca: invalid position_intent specified (40010001).
        return "preflight_position_intent_invalid"
    return None


def _preflight_warnings(intent, sleeve_id):
    """Non-rejecting preflight findings, journaled beside the submit
    so the record carries them without changing live behavior."""
    out = []
    if len(client_order_id_untruncated(
            sleeve_id, intent.get("intent_id"))) > 127:
        out.append("client_order_id_truncated_at_127")
    return out


def _session_today():
    """Session date = the America/New_York calendar date, today."""
    return datetime.now(ZoneInfo("America/New_York")).date().isoformat()


class PendingStore:
    """Durable pending-intent store (BROKER-PENDING-DRAIN-20261026):
    the SINGLE source of truth for intents whose submit exhausted the
    in-call retry. Two files under state/, flock-guarded like the
    runner's own files:
      broker_pending.jsonl — append log of persisted entries;
      broker_pending.json  — rewritten snapshot of LIVE entries only.
    The snapshot is authoritative; the JSONL is compaction-rewritten
    to the live set on every removal so neither file can grow without
    bound across a pathological day."""

    def __init__(self, state):
        self.jsonl = os.path.join(state, "broker_pending.jsonl")
        self.snapshot = os.path.join(state, "broker_pending.json")
        self.lock_path = os.path.join(state, "broker_pending.lock")

    @contextlib.contextmanager
    def _locked(self):
        os.makedirs(os.path.dirname(self.lock_path), exist_ok=True)
        fh = open(self.lock_path, "a+")
        try:
            fcntl.flock(fh, fcntl.LOCK_EX)
            yield
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)
            fh.close()

    def _load_unlocked(self):
        if os.path.exists(self.snapshot):
            try:
                with open(self.snapshot) as fh:
                    rows = json.load(fh)
                if isinstance(rows, list):
                    return [r for r in rows if isinstance(r, dict)]
            except (ValueError, OSError):
                pass
        # Fallback (snapshot missing/corrupt): rebuild from the append
        # log, last write per client_order_id wins.
        by_coid = {}
        for r in read_lines(self.jsonl):
            if r.get("client_order_id"):
                by_coid[r["client_order_id"]] = r
        return list(by_coid.values())

    def _write_snapshot_unlocked(self, entries):
        tmp = self.snapshot + ".tmp"
        with open(tmp, "w") as fh:
            json.dump(entries, fh, sort_keys=True)
        os.replace(tmp, self.snapshot)

    def _compact_unlocked(self, entries):
        tmp = self.jsonl + ".tmp"
        with open(tmp, "w") as fh:
            for e in entries:
                fh.write(json.dumps(e, separators=(",", ":"),
                                    sort_keys=True) + "\n")
        os.replace(tmp, self.jsonl)
        self._write_snapshot_unlocked(entries)

    def load(self):
        if not os.path.exists(self.snapshot) \
                and not os.path.exists(self.jsonl):
            return []
        with self._locked():
            return self._load_unlocked()

    def add(self, entry):
        with self._locked():
            entries = self._load_unlocked()
            entries = [e for e in entries
                       if e.get("client_order_id")
                       != entry["client_order_id"]]
            entries.append(entry)
            # DRAIN-HOLD-20261104: MAX_PENDING_ENTRIES was declared
            # but never enforced; enforce it by dropping the
            # OLDEST live entries (the front of the list) and
            # compacting both files to the surviving set.
            if len(entries) > MAX_PENDING_ENTRIES:
                entries = entries[-MAX_PENDING_ENTRIES:]
                self._compact_unlocked(entries)
                return entries
            append_line(self.jsonl, entry)
            self._write_snapshot_unlocked(entries)
            return entries

    def update(self, entry):
        with self._locked():
            entries = self._load_unlocked()
            entries = [entry if e.get("client_order_id")
                       == entry["client_order_id"] else e
                       for e in entries]
            self._compact_unlocked(entries)
            return entries

    def remove(self, coid):
        with self._locked():
            entries = [e for e in self._load_unlocked()
                       if e.get("client_order_id") != coid]
            self._compact_unlocked(entries)
            return entries


# CONSTANTS-DERIVATIONS-20261116: bp_buffer_frac = 0.02 — DERIVED
# (route-4 derivation adopted 2026-11-16; this Dispatcher is the
# source of truth for the default, config/sleeves.json rows carry
# the same value per sleeve). Derivation: 2% of each slice is
# reserved against fees, slippage, and signal-to-fill price
# movement between intent and fill. Origin: entered with CORE
# commit 638b70c (v2 lineage); the 2026-11-16 provenance hunt found
# no source derivation for 0.02 in any BUGLOG/FIDELITY/doc.
# Falsifier / replacement test: a measured intent-to-fill cost
# study on the desk's own fills — if measured all-in cost per fill
# is materially below 2% of slice over a counted sample, the
# buffer is re-derived from that measurement.
class Dispatcher:
    def __init__(self, root, broker, slices=None, price_lookup=None,
                 session_date=None, now_fn=None,
                 virtual_book_mode="off", virtual_book_canaries=None):
        self.root = os.path.abspath(root)
        self.broker = broker
        # VIRTUAL-BOOK staging (SLEEVE-VIRTUAL-BOOK-DIVERGENCE cure,
        # NO-PARTIALS DRIVE 2026-11-11): "off" = pre-cure behaviour;
        # "log" = dual-read only (every exit is compared against the
        # sleeve's journal-derived book and divergences are journaled
        # and censused; NO decision changes); "canary" = enforcement
        # for the sleeves named in virtual_book_canaries only;
        # "fleet" = enforcement for every sleeve. Enforcement gives a
        # sleeve its OWN true position at the exit pre-flight: an
        # exit for a position the sleeve does not own terminates
        # locally instead of drawing the broker's 42210000, and an
        # exit larger than the sleeve's own position is clamped to
        # what the sleeve owns. It changes whose book a sleeve reads,
        # never what a sleeve decides.
        self.virtual_book_mode = virtual_book_mode or "off"
        self.virtual_book_canaries = set(virtual_book_canaries or ())
        self._vb_book = None
        self._vb_divergences = []
        self._vb_divergence_count = 0
        # DRAIN-HOLD-20261104: injectable ET clock for the drain's
        # options-hours hold; production passes nothing and reads
        # the real clock (cycle.py constructs one Dispatcher per
        # cycle, so the value is always fresh).
        self._now_fn = now_fn or (lambda: datetime.now(ET))
        self.state = os.path.join(self.root, "state")
        os.makedirs(self.state, exist_ok=True)
        self.djournal = os.path.join(self.state, "dispatcher.jsonl")
        # Session scope for the pending store: an explicit date pins
        # the session (tests); otherwise the ET date at construction.
        self.session_date = session_date or _session_today()
        self.pending_store = PendingStore(self.state)
        # EXIT-STORM-DEDUPE-20261111 (CR-3): per-session suppression
        # store for terminal exit verdicts (see _storm_check).
        self._storm_path = os.path.join(
            self.state, "exit_storm_suppression.json")
        self._storm = None
        self.price_lookup = price_lookup or (lambda sym: None)
        self.slices = {}
        for sid, s in (slices or {}).items():
            # READINESS-CYC3-20261112: a slice spec may carry a
            # positions seed (cycle.py builds it from the
            # journal-derived book, so the slice mirror opens the
            # cycle holding what prior cycles actually hold). No
            # seed = the empty book, exactly as before.
            _seed_pos = {}
            for _sym, _row in (s.get("positions") or {}).items():
                _seed_pos[_sym] = {
                    "symbol": _row.get("symbol", _sym),
                    "qty": float(_row.get("qty") or 0.0),
                    "avg_price": float(_row.get("avg_price") or 0.0)}
            self.slices[sid] = {"capital_usd": float(s["capital_usd"]),
                                "cash_usd": float(s["cash_usd"]),
                                "reserved_usd": 0.0, "positions": _seed_pos,
                                "bp_buffer_frac": float(s.get("bp_buffer_frac", 0.02))}
        self._seen = None
        self._book_cache = None  # BLOCKED-EXIT-20261029 exit pre-flight
        # CSP-PREFLIGHT-20261104: options buying power, fetched at
        # most once per Dispatcher (it is per-cycle); False means
        # not fetched yet, None means the broker cannot report it.
        self._obp_cache = False
        self._pending = []  # (intent, sleeve_id) queued while door is down
        self.halted_sleeves = set()  # A15: reconcile discrepancy halts
        # HALT-SYMBOL-SCOPE-20261116: None means no scope information
        # was supplied (the legacy contract: a halted sleeve's
        # entries halt on every symbol, exactly as the pre-cure
        # blockers pin). When cycle.py supplies the reconcile
        # report's halted_scopes, this becomes {sleeve: {normalized
        # symbols}} and an entry halts only on its own discrepant
        # symbol. A halted sleeve with no scope row keeps the
        # sleeve-wide halt (fail closed, never silently narrower).
        self.halted_scopes = None
        self.cash_halt = False
        # HALT-CONTEXT-20261030: the full reconcile report that set
        # the halts above (cycle.py assigns it), so a reconcile_halt
        # reject row can carry the discrepancy that caused it. A gate
        # whose reject rows cannot explain themselves is a defect
        # independent of the fill bug (RESEARCH-R1 B4).
        self.reconcile_report = None

    def _index(self):
        if self._seen is not None:
            return
        self._seen = set()
        # JOURNAL-ROTATION-LEDGER-20261108: the duplicate index
        # reads every journal generation (desk3.journal's reader
        # contract), not only the current file: after a rotation
        # the pre-rotation intent ids are still spent, and an
        # index that forgets them re-admits duplicates the
        # journal already decided.
        from .journal import journal_generations
        for gen in journal_generations(self.djournal):
            for r in read_lines(gen):
                # READINESS-DSP1-20261112: broker_rejected_terminal
                # is an indexed verdict — a deterministic broker
                # rejection spends the intent id permanently, so a
                # rebuilt dispatcher never re-presents it (the
                # drain doubled 144 intents before this cure
                # precisely because the index never learned it).
                if r.get("event") in ("order_submitted", "intent_rejected",
                                      "intent_duplicate", "fill",
                                      "broker_rejected_terminal",
                                      "intent_recorded"):
                    self._seen.add(r.get("intent_id"))

    def journal_events(self):
        return read_lines(self.djournal)

    def pending_entries(self):
        """Live pending entries: the durable store is the source of
        truth; the in-memory queue is only its same-instance mirror."""
        stored = self.pending_store.load()
        if stored:
            return stored
        return [{"intent": dict(i), "sleeve_id": s,
                 "client_order_id": client_order_id(s, i.get("intent_id")),
                 "session_date": self.session_date, "attempts": 0,
                 "last_error": None} for i, s in self._pending]

    def drain_pending(self, cap=None):
        """BROKER-PENDING-DRAIN-20261026: drain the persistent store.
        Called at the START of each dispatch cycle (cycle.py, before
        new intents) and by retry_pending(). Per entry:
        - stale session (not today): NEVER submitted; removed and
          journaled expired_unsent (a day intent must never fire into
          a later session). The stale sweep is not charged to the cap
          (no broker calls).
        - reconcile-halted sleeve (entry intents only): NOT submitted
          while halted; stays pending, journaled pending_drain_deferred.
        - otherwise re-run the SAME process_intent path (all gates:
          slice BP, D-GATE, duplicate index) under the ORIGINAL
          client_order_id — the broker dedupes by that id, so a
          double drain submits/fills once.
        Terminal outcomes remove the entry (fill/submit -> drained;
        a genuine terminal broker rejection or gate rejection ->
        drained_terminal); broker-unavailable-class failures
        (403/429/5xx/network — DRAIN-CLASS-20261026) are NEVER
        terminal: the entry stays in the store, journaled
        drained_deferred with the error, for the next cycle.
        At most `cap` same-session entries are attempted per call."""
        cap = DRAIN_CAP if cap is None else cap
        results = []
        attempted = 0
        for entry in self.pending_entries():
            intent = entry.get("intent") or {}
            sleeve_id = entry.get("sleeve_id")
            coid = entry.get("client_order_id") or client_order_id(
                sleeve_id, intent.get("intent_id"))
            iid = intent.get("intent_id")
            # OVERNIGHT-AUCTION-20261116 (B0-4): an intent carrying
            # an auction deadline whose moment has passed at drain
            # time is NEVER submitted — a cls intent drained after
            # its cutoff is broker-rejected, and one drained after
            # 19:00 ET would queue for the WRONG session's auction.
            # It closes here, journaled by name, not charged to the
            # cap (no broker calls). Intents without the field, and
            # deadlines that do not parse, drain exactly as before.
            _deadline = intent.get("auction_deadline_et")
            if _deadline:
                try:
                    _dl = datetime.fromisoformat(
                        str(_deadline).replace("Z", "+00:00"))
                    if _dl.tzinfo is None:
                        _dl = _dl.replace(tzinfo=ET)
                    _now = self._now_fn()
                    if _now.tzinfo is None:
                        _now = _now.replace(tzinfo=ET)
                    _expired = _now >= _dl
                except (ValueError, TypeError):
                    _expired = False
                if _expired:
                    self.pending_store.remove(coid)
                    self._pending = [(i, s) for i, s in self._pending
                                     if i.get("intent_id") != iid]
                    append_line(self.djournal,
                                {"event": "auction_intent_expired",
                                 "intent_id": iid, "sleeve": sleeve_id,
                                 "symbol": intent.get("symbol"),
                                 "time_in_force":
                                     intent.get("time_in_force"),
                                 "auction_deadline_et": _deadline})
                    results.append(
                        {"status": "auction_intent_expired",
                         "intent_id": iid, "client_order_id": coid})
                    continue
            if entry.get("session_date") != self.session_date:
                self.pending_store.remove(coid)
                self._pending = [(i, s) for i, s in self._pending
                                 if i.get("intent_id") != iid]
                append_line(self.djournal,
                            {"event": "expired_unsent", "intent_id": iid,
                             "sleeve": sleeve_id, "client_order_id": coid,
                             "session_date": entry.get("session_date")})
                results.append({"status": "expired_unsent",
                                "intent_id": iid, "client_order_id": coid})
                continue
            # DRAIN-HOLD-20261104: an entry that has exhausted its
            # drain attempts ends here, named, instead of retrying
            # forever. Not charged to the cap (no broker calls).
            if int(entry.get("attempts") or 0) >= MAX_DRAIN_ATTEMPTS:
                self.pending_store.remove(coid)
                self._pending = [(i, s) for i, s in self._pending
                                 if i.get("intent_id") != iid]
                append_line(self.djournal,
                            {"event": "drained_terminal",
                             "intent_id": iid, "sleeve": sleeve_id,
                             "client_order_id": coid,
                             "reason": "attempts_exhausted",
                             "attempts": int(entry.get("attempts") or 0)})
                results.append({"status": "drained_terminal",
                                "intent_id": iid, "client_order_id": coid,
                                "reason": "attempts_exhausted"})
                continue
            # DRAIN-HOLD-20261104: a queued OCC market order drained
            # while the options market is closed can only draw the
            # door's deterministic market-hours 422, which is NOT in
            # the broker-unavailable class, so the attempt would end
            # drained_terminal and the entry would be lost (the
            # 2026-11-03 overnight SPY put exits survived only
            # because their sleeves re-emit every cycle). Hold the
            # entry instead: deferred by name, kept in the store,
            # not charged to the cap. In-hours behaviour is
            # unchanged; limit orders are not held (they rest).
            if intent.get("order_type", "market") == "market" and \
                    OCC_RE.match(intent.get("symbol") or ""):
                from .broker import options_market_open
                if not options_market_open(self._now_fn()):
                    append_line(self.djournal,
                                {"event": "pending_drain_deferred",
                                 "intent_id": iid, "sleeve": sleeve_id,
                                 "client_order_id": coid,
                                 "reason": "options_market_closed_hold"})
                    results.append(
                        {"status": "deferred", "intent_id": iid,
                         "client_order_id": coid,
                         "reason": "options_market_closed_hold"})
                    continue
            # DRAIN-INTENT-MISMATCH-20261110 (W4, DSK-12): an exit
            # whose broker answer was a deterministic position-
            # intent mismatch (422 code 42210000, "position intent
            # mismatch, inferred: X, specified: Y") is NEVER
            # re-presented as-is. 27 such rejections landed in 48 h
            # (106 rows all-time in the current journal generation,
            # every one paired with a drained_terminal
            # exit_satisfied_no_broker_position once the drain's
            # re-check saw the by-then-flat broker book): the exit
            # process_intent already returned its broker-book
            # verdict and consumed the intent, yet the raw 422
            # failure path ALSO persisted the entry, so each drained
            # copy re-ran process_intent, was re-rejected locally
            # by the pre-flight, and its SECOND 422 pair came from
            # the drain re-presenting the ORIGINAL intent against
            # the cache the first attempt had left warm (and, when
            # an account-level position existed, from the pre-flight
            # clamping to a remainder the broker had reserved).
            # Hold the entry instead: deferred by name, kept in the
            # store, not charged to the cap; the next cycle's drain
            # re-checks it against a fresh broker book, where the
            # exit either reaches the broker as a true close or
            # terminates locally as satisfied / already-resting.
            if "position intent mismatch" in str(
                    entry.get("last_error") or ""):
                append_line(self.djournal,
                            {"event": "pending_drain_deferred",
                             "intent_id": iid, "sleeve": sleeve_id,
                             "client_order_id": coid,
                             "reason":
                                 "position_intent_mismatch_hold"})
                results.append(
                    {"status": "deferred", "intent_id": iid,
                     "client_order_id": coid,
                     "reason": "position_intent_mismatch_hold"})
                continue
            # DRAIN-INTENT-MISMATCH-20261110 (W4, DSK-12): an exit
            # whose broker answer was a deterministic position-
            # intent mismatch (422 code 42210000, "position intent
            # mismatch, inferred: X, specified: Y") is NEVER
            # re-presented as-is. 27 such rejections landed in 48 h
            # (106 rows all-time in the current journal generation,
            # every one paired with a drained_terminal
            # exit_satisfied_no_broker_position once the drain's
            # re-check saw the by-then-flat broker book): the exit
            # process_intent already returned its broker-book
            # verdict and consumed the intent, yet the raw 422
            # failure path ALSO persisted the entry, so each drained
            # copy re-ran process_intent, was re-rejected locally
            # by the pre-flight, and its SECOND 422 pair came from
            # the drain re-presenting the ORIGINAL intent against
            # the cache the first attempt had left warm (and, when
            # an account-level position existed, from the pre-flight
            # clamping to a remainder the broker had reserved).
            # Hold the entry instead: deferred by name, kept in the
            # store, not charged to the cap; the next cycle's drain
            # re-checks it against a fresh broker book, where the
            # exit either reaches the broker as a true close or
            # terminates locally as satisfied / already-resting.
            if "position intent mismatch" in str(
                    entry.get("last_error") or ""):
                append_line(self.djournal,
                            {"event": "pending_drain_deferred",
                             "intent_id": iid, "sleeve": sleeve_id,
                             "client_order_id": coid,
                             "reason":
                                 "position_intent_mismatch_hold"})
                results.append(
                    {"status": "deferred", "intent_id": iid,
                     "client_order_id": coid,
                     "reason": "position_intent_mismatch_hold"})
                continue
            if attempted >= cap:
                continue
            attempted += 1
            is_exit = intent.get("kind") == "exit" or intent.get(
                "position_intent") in ("buy_to_close", "sell_to_close")
            if not is_exit and (self._halt_applies(
                    sleeve_id, intent.get("symbol")) or self.cash_halt):
                _drow = {"event": "pending_drain_deferred",
                         "intent_id": iid, "sleeve": sleeve_id,
                         "client_order_id": coid,
                         "reason": "reconcile_halt"}
                _drow.update(self._halt_context(sleeve_id))
                append_line(self.djournal, _drow)
                results.append({"status": "deferred", "intent_id": iid,
                                "client_order_id": coid,
                                "reason": "reconcile_halt"})
                continue
            r = self.process_intent(dict(intent), sleeve_id,
                                    _from_drain=True)
            self._pending = [(i, s) for i, s in self._pending
                             if i.get("intent_id") != iid]
            if r["status"] in ("filled", "submitted"):
                self.pending_store.remove(coid)
                append_line(self.djournal,
                            {"event": "drained", "intent_id": iid,
                             "sleeve": sleeve_id, "client_order_id": coid,
                             "result": r["status"]})
            elif r["status"] == "duplicate":
                self.pending_store.remove(coid)
                append_line(self.djournal,
                            {"event": "drained", "intent_id": iid,
                             "sleeve": sleeve_id, "client_order_id": coid,
                             "result": "duplicate"})
            elif r["status"] in ("rejected", "recorded") or (
                    r["status"] == "queued" and not r.get("transient", True)):
                self.pending_store.remove(coid)
                reason = r.get("reason") or r.get("last_error") or "terminal"
                append_line(self.djournal,
                            {"event": "drained_terminal", "intent_id": iid,
                             "sleeve": sleeve_id, "client_order_id": coid,
                             "reason": str(reason)})
                r = {"status": "drained_terminal", "intent_id": iid,
                     "client_order_id": coid, "reason": str(reason)}
            elif r["status"] == "queued":
                # DRAIN-CLASS-20261026: broker-unavailable class —
                # NEVER terminal. Entry stays in the store (updated
                # by process_intent) for the next cycle in this
                # session; the deferral is journaled with the error.
                err = str(r.get("last_error") or "broker_unavailable")
                append_line(self.djournal,
                            {"event": "drained_deferred", "intent_id": iid,
                             "sleeve": sleeve_id, "client_order_id": coid,
                             "error": err})
                r = {"status": "drained_deferred", "intent_id": iid,
                     "client_order_id": coid, "error": err}
            results.append(r)
        return results

    def retry_pending(self):
        """Re-process queued intents after door recovery — now the
        persistent drain (BROKER-PENDING-DRAIN-20261026). Idempotent:
        the _seen index + broker client-order-id dedup make a second
        fill for the same intent impossible."""
        return self.drain_pending()

    def _apply_broker_dialect(self, intent, sleeve_id):
        """BLOCKED-EXIT-20261029: translate the intent's symbol to
        the broker dialect (ADAUSDT -> ADA/USD) and the crypto TIF
        (day -> gtc; crypto rejects "day" with a 422, cured at
        emission for aster_batch1 on 2026-10-27, enforced here at
        the door for every sleeve). Mutates the intent dict (callers
        pass a copy); journals every translation."""
        raw_sym = intent.get("symbol")
        nsym = _normalize_broker_symbol(raw_sym)
        if nsym != raw_sym:
            append_line(self.djournal,
                        {"event": "symbol_normalized",
                         "intent_id": intent.get("intent_id"),
                         "sleeve": sleeve_id,
                         "from_symbol": raw_sym, "to_symbol": nsym})
            intent["symbol"] = nsym
        # CANONICAL-DIALECT-20261030: the crypto TIF rule (day is a
        # 422 on crypto) resolves through the shared translator.
        intent["time_in_force"] = _broker_time_in_force(
            str(intent.get("symbol")),
            intent.get("time_in_force", "day"))
        return intent

    def _virtual_book(self):
        """The journal-derived per-sleeve book (VIRTUAL-BOOK staging).

        Built once per Dispatcher (one cycle) from every journal
        generation, then kept current by _vb_note_fill for fills this
        dispatcher journals itself. Fills imported by the reconcile
        sweep bypass this dispatcher and are picked up next cycle,
        when a fresh Dispatcher re-derives from the journals.
        """
        if self._vb_book is None:
            from .journal import journal_generations
            from .virtual_book import derive_book_from_journals
            raw = self._vb_seed_raw()
            if raw is None:
                raw = derive_book_from_journals(
                    journal_generations(self.djournal))
            # Journal generations span the pre-dialect era: keys are
            # re-keyed to the broker dialect the exit pre-flight
            # speaks, merging any split cells for the same position.
            book = {}
            for (sleeve, symbol), cell in raw.items():
                key = (sleeve, _normalize_broker_symbol(symbol))
                merged = book.setdefault(key, {"qty": 0.0, "fills": 0})
                merged["qty"] += cell["qty"]
                merged["fills"] += cell["fills"]
            self._vb_book = book
        return self._vb_book

    def _vb_seed_raw(self):
        """A1-SEED-20261114: seed the derived book from the durable
        fill ledger (state/fill_ledger: immutable segments plus a
        hash-verified manifest, built by desk3.fill_ledger each
        cycle before dispatch) instead of the rotating dispatcher
        journal generations. Journal generations are bounded (five
        files); a fill that rotates out silently shrinks the derived
        book and shows up as an unexplained dual-read residual. The
        ledger is the durable form of the same fills. Returns the
        raw derived book, or None when the ledger is absent or its
        manifest does not verify -- the caller then falls back to
        the journal generations, the pre-A1 source, unchanged."""
        try:
            import glob as _glob
            from .fill_ledger import verify_ledger
            from .virtual_book import derive_book, iter_journal_rows
            ledger_dir = os.path.join(self.state, "fill_ledger")
            if not os.path.isdir(ledger_dir):
                return None
            if not verify_ledger(ledger_dir).get("ok"):
                return None
            segments = sorted(_glob.glob(
                os.path.join(ledger_dir, "fills-*.jsonl")))
            if not segments:
                return None
            return derive_book(iter_journal_rows(segments))
        except Exception:
            return None

    def _vb_note_fill(self, sleeve_id, symbol, side, qty):
        if self._vb_book is None:
            return
        from .virtual_book import _signed_qty
        key = (sleeve_id, symbol)
        cell = self._vb_book.setdefault(key, {"qty": 0.0, "fills": 0})
        cell["qty"] += _signed_qty(
            {"side": side, "qty": qty})
        cell["fills"] += 1

    def _vb_enforcing(self, sleeve_id):
        if self.virtual_book_mode == "fleet":
            return True
        if self.virtual_book_mode == "canary":
            return sleeve_id in self.virtual_book_canaries
        return False

    def virtual_book_census(self):
        """The cycle's dual-read census for the roll (log modes)."""
        if self.virtual_book_mode == "off":
            return None
        book = self._virtual_book()
        return {
            "mode": self.virtual_book_mode,
            "derived_positions": sum(
                1 for cell in book.values() if cell["qty"] != 0.0),
            "dual_read_divergences": self._vb_divergence_count,
            "divergences": self._vb_divergences[:50],
        }

    def _exit_book(self):
        """BLOCKED-EXIT-20261029: the broker book for exit pre-flight
        — positions keyed by NORMALIZED symbol, plus resting orders.
        Cached per Dispatcher instance (one cycle's dispatch shares
        one read); invalidated whenever this dispatcher submits, so
        a close it just rested is visible to the next exit."""
        if self._book_cache is None:
            positions = {}
            for sym, qty in (self.broker.get_positions() or {}).items():
                positions[_normalize_broker_symbol(sym)] = float(qty)
            orders = []
            for o in (self.broker.get_open_orders() or []):
                if isinstance(o, dict):
                    orders.append(o)
            self._book_cache = (positions, orders)
        return self._book_cache

    # EXIT-STORM-DEDUPE-20261111 (CR-3, DIAGNOSIS.md S4): eleven
    # sleeves re-emit the same exit every cycle for a lot the broker
    # book does not hold for them (or holds fully reserved by a
    # resting close), and each re-emission journaled a fresh
    # terminal rejection (532 intent_rejected rows in one 200 KB
    # tail of the live journal, 2026-11-11). The verdicts are
    # correct; the storm is the defect. The first verdict of the two
    # storm classes is journaled exactly as before and recorded
    # here, keyed by (sleeve, symbol) for THIS session only. A later
    # same-session exit for the same key is answered from the
    # CURRENT broker book: unchanged book (still no position, or
    # still fully covered by resting closes) -> consumed as
    # exit_storm_suppressed with one journal row per key per
    # session; changed book -> the suppression clears and the exit
    # is decided on its merits, so a real exit can never be
    # swallowed by an old verdict.
    def _storm_load(self):
        if self._storm is not None:
            return self._storm
        data = {}
        try:
            with open(self._storm_path) as f:
                raw = json.load(f)
            if isinstance(raw, dict) \
                    and raw.get("session") == self.session_date:
                data = raw.get("keys") or {}
        except (OSError, ValueError):
            data = {}
        self._storm = data
        return data

    def _storm_save(self):
        try:
            tmp = self._storm_path + ".tmp"
            with open(tmp, "w") as f:
                json.dump({"session": self.session_date,
                           "keys": self._storm or {}}, f)
            os.replace(tmp, self._storm_path)
        except OSError:
            pass

    def _storm_note(self, sleeve_id, symbol, reason):
        keys = self._storm_load()
        k = f"{sleeve_id}|{symbol}"
        if k not in keys:
            keys[k] = {"reason": reason, "journaled": False}
            self._storm_save()

    def _storm_check(self, sleeve_id, symbol, positions, open_orders):
        keys = self._storm_load()
        k = f"{sleeve_id}|{symbol}"
        rec = keys.get(k)
        if rec is None:
            return None
        pos = positions.get(symbol, 0.0)
        reason = rec.get("reason")
        if reason == "exit_satisfied_no_broker_position":
            if pos == 0:
                return rec
        elif reason == "exit_already_resting_at_broker":
            if pos != 0:
                close_side = "sell" if pos > 0 else "buy"
                resting = 0.0
                for o in open_orders:
                    if _normalize_broker_symbol(
                            o.get("symbol")) != symbol:
                        continue
                    if o.get("side") != close_side:
                        continue
                    try:
                        resting += float(o.get("qty") or 0) \
                            - float(o.get("filled_qty") or 0)
                    except (TypeError, ValueError):
                        continue
                if abs(pos) - resting <= 1e-9:
                    return rec
        elif reason == "exit_blocked_opposite_side_resting":
            # CURE-DC2-20261113: the verdict stands while any
            # opposite-side order still rests on the symbol (a
            # close submitted into it draws the deterministic
            # wash-trade 403); it clears the cycle the order is
            # gone, and the exit is decided on its merits.
            if pos != 0:
                close_side = "sell" if pos > 0 else "buy"
                opp_side = "buy" if close_side == "sell" else "sell"
                for o in open_orders:
                    if _normalize_broker_symbol(
                            o.get("symbol")) != symbol:
                        continue
                    if o.get("side") == opp_side:
                        return rec
        # The book state behind the verdict changed: the verdict
        # no longer stands and the exit is decided on its merits.
        del keys[k]
        self._storm_save()
        return None

    def _storm_result(self, intent, sleeve_id, rec):
        if not rec.get("journaled"):
            append_line(self.djournal, {
                "event": "exit_storm_suppressed",
                "intent_id": intent.get("intent_id"),
                "sleeve": sleeve_id, "symbol": intent["symbol"],
                "suppressed_reason": rec.get("reason"),
                "session": self.session_date})
            rec["journaled"] = True
            self._storm_save()
        self._index()
        self._seen.add(intent.get("intent_id"))
        return {"status": "rejected", "reason": "exit_storm_suppressed",
                "intent_id": intent.get("intent_id"),
                "suppressed_reason": rec.get("reason")}

    def _reconcile_exit(self, intent, sleeve_id):
        """BLOCKED-EXIT-20261029: reconcile ONE exit intent against
        the broker book of record BEFORE it can reach the wire.
        Sleeve virtual books diverge from the single netted broker
        account (diagnosis 2026-10-29 §6): exits arrived as
        sell_to_close of longs that are shorts or nothing at the
        broker, were inferred sell_to_open by the broker, and were
        margin-refused as new positions (40310000) forever. Rules:
        - symbol is normalized to the broker dialect first;
        - no broker position in the symbol: the exit is already
          satisfied — terminally rejected, NEVER submitted (a submit
          would OPEN a position, proven by diagnosis E6);
        - the close side/intent are DERIVED from the real position's
          sign (short -> buy/buy_to_close, long -> sell/sell_to_close)
          and the qty is clamped to the position size net of qty
          already reserved by resting close-side orders;
        - resting close-side orders already cover the whole
          position: the exit is already in flight — terminally
          rejected, never resubmitted (resubmission was the
          held_for_orders 403 class).
        Returns a terminal result dict, or None when the (possibly
        rewritten) intent may proceed to submit. Only active when
        the broker is the live book (PaperDoor.live_book); test
        doubles opt in explicitly."""
        iid = intent.get("intent_id")
        if not getattr(self.broker, "live_book", False):
            return None
        if not (hasattr(self.broker, "get_positions")
                and hasattr(self.broker, "get_open_orders")):
            return None
        positions, open_orders = self._exit_book()
        pos = positions.get(intent["symbol"], 0.0)
        # EXIT-STORM-DEDUPE-20261111: a same-session repeat of an
        # exit whose terminal verdict the current book still
        # supports is consumed here, before any further journaling.
        _storm = self._storm_check(sleeve_id, intent["symbol"],
                                    positions, open_orders)
        if _storm is not None:
            return self._storm_result(intent, sleeve_id, _storm)
        # VIRTUAL-BOOK staging: dual-read every exit against the
        # sleeve's own journal-derived book. In log mode this changes
        # NOTHING below; divergences are journaled and censused. In
        # canary/fleet mode the sleeve's own position governs: no
        # owned position -> the exit terminates locally with its own
        # named reason instead of reaching the broker as a phantom
        # close (the 42210000 class); a netted sign mismatch can
        # never be closed against the aggregate and terminates by
        # name; an oversized exit is clamped to the sleeve's own
        # quantity via _vb_cap in the eff_qty computation below.
        _vb_cap = None
        if self.virtual_book_mode != "off":
            from .virtual_book import exit_divergence, sleeve_positions
            _div = exit_divergence(self._virtual_book(), sleeve_id,
                                   intent["symbol"], pos)
            if _div is not None:
                self._vb_divergence_count += 1
                if len(self._vb_divergences) < 200:
                    self._vb_divergences.append(_div)
                append_line(self.djournal,
                            {"event": "virtual_book_dual_read",
                             "intent_id": iid, **_div})
            if self._vb_enforcing(sleeve_id):
                _derived = sleeve_positions(
                    self._virtual_book(), sleeve_id).get(
                        intent["symbol"], 0.0)
                if _derived == 0.0 and pos != 0.0:
                    append_line(self.djournal,
                                {"event": "virtual_book_enforced",
                                 "intent_id": iid, "sleeve": sleeve_id,
                                 "symbol": intent["symbol"],
                                 "action": "reject_no_sleeve_position",
                                 "broker_qty": pos})
                    return self._reject(
                        intent, sleeve_id,
                        "exit_satisfied_no_sleeve_position")
                if pos != 0.0 and _derived * pos < 0:
                    append_line(self.djournal,
                                {"event": "virtual_book_enforced",
                                 "intent_id": iid, "sleeve": sleeve_id,
                                 "symbol": intent["symbol"],
                                 "action": "reject_netted_sign_mismatch",
                                 "derived_qty": _derived,
                                 "broker_qty": pos})
                    return self._reject(
                        intent, sleeve_id,
                        "exit_netted_against_broker_book")
                if pos != 0.0:
                    _vb_cap = abs(_derived)
        if pos == 0:
            self._storm_note(sleeve_id, intent["symbol"],
                             "exit_satisfied_no_broker_position")
            return self._reject(
                intent, sleeve_id, "exit_satisfied_no_broker_position")
        close_side = "sell" if pos > 0 else "buy"
        close_intent = "sell_to_close" if pos > 0 else "buy_to_close"
        opp_side = "buy" if close_side == "sell" else "sell"
        resting = 0.0
        opp_resting = 0.0
        for o in open_orders:
            if _normalize_broker_symbol(o.get("symbol")) != intent["symbol"]:
                continue
            try:
                _rem = float(o.get("qty") or 0) \
                    - float(o.get("filled_qty") or 0)
            except (TypeError, ValueError):
                continue
            if o.get("side") == close_side:
                resting += _rem
            elif o.get("side") == opp_side:
                opp_resting += _rem
        uncovered = abs(pos) - resting
        if uncovered <= 1e-9:
            self._storm_note(sleeve_id, intent["symbol"],
                             "exit_already_resting_at_broker")
            return self._reject(
                intent, sleeve_id, "exit_already_resting_at_broker")
        # CURE-DC2-20261113: an opposite-side order resting on the
        # symbol makes this close unsubmittable — Alpaca answers
        # every such submit with the deterministic 40310000
        # "potential wash trade detected" (live 2026-11-13: 93
        # rows, BTC/USD closes against the stuck BTC buy order).
        # Terminate locally under the same storm class the
        # submit-error path notes, so re-emissions are suppressed
        # while the order rests and released when it clears,
        # instead of paying for the same verdict every cycle.
        if opp_resting > 1e-9:
            self._storm_note(sleeve_id, intent["symbol"],
                             "exit_blocked_opposite_side_resting")
            return self._reject(
                intent, sleeve_id,
                "exit_blocked_opposite_side_resting")
        eff_qty = min(float(intent["qty"]), uncovered)
        if _vb_cap is not None:
            eff_qty = min(eff_qty, _vb_cap)
        if intent.get("side") != close_side \
                or intent.get("position_intent") != close_intent \
                or eff_qty != float(intent["qty"]):
            append_line(self.djournal,
                        {"event": "exit_reconciled_to_broker_book",
                         "intent_id": iid, "sleeve": sleeve_id,
                         "symbol": intent["symbol"],
                         "broker_position": pos,
                         "resting_close_qty": resting,
                         "from_side": intent.get("side"),
                         "from_position_intent":
                             intent.get("position_intent"),
                         "from_qty": intent.get("qty"),
                         "to_side": close_side,
                         "to_position_intent": close_intent,
                         "to_qty": eff_qty})
        intent["side"] = close_side
        intent["position_intent"] = close_intent
        intent["qty"] = eff_qty
        return None

    def slice_for(self, sid):
        return self.slices.setdefault(
            sid, {"capital_usd": 0.0, "cash_usd": 0.0, "reserved_usd": 0.0,
                  "positions": {}, "bp_buffer_frac": 0.02})

    def _halt_context(self, sleeve_id):
        """HALT-CONTEXT-20261030: the discrepancy rows behind a
        reconcile halt for one sleeve: every report discrepancy that
        names the sleeve, plus any cash discrepancy, with the
        cash_halt flag. Empty when no report was supplied (direct
        Dispatcher use in tests keeps the old row shape)."""
        rep = self.reconcile_report or {}
        discs = []
        for d in rep.get("discrepancies") or []:
            if d.get("kind") == "cash" \
                    or sleeve_id in (d.get("sleeves") or []):
                discs.append(d)
        return {"discrepancies": discs,
                "cash_halt": bool(self.cash_halt)}

    def _halt_applies(self, sleeve_id, symbol):
        """HALT-SYMBOL-SCOPE-20261116: does the reconcile position
        halt cover this sleeve's entry in this symbol? With scope
        rows supplied, only the discrepant symbol itself halts (the
        2026-11-15 BTC/USD row must not freeze the same sleeves'
        SPY and QQQ entries). Without scope rows the legacy
        sleeve-wide halt stands, and a halted sleeve missing from
        the scope map also keeps it: narrowing a halt requires the
        report's own evidence, never an inference."""
        if sleeve_id not in self.halted_sleeves:
            return False
        if not self.halted_scopes:
            return True
        syms = self.halted_scopes.get(sleeve_id)
        if syms is None:
            return True
        return _normalize_broker_symbol(symbol) in syms

    def _options_buying_power(self):
        """CSP-PREFLIGHT-20261104: the broker-reported options
        buying power, fetched at most once per Dispatcher and
        cached. Returns None when the broker cannot report it
        (missing method, missing field, or a failed read): the
        CSP gate then does not apply."""
        if self._obp_cache is not False:
            return self._obp_cache
        value = None
        try:
            acct = self.broker.get_account()
            raw = (acct or {}).get("options_buying_power")
            if raw is not None:
                value = float(raw)
        except Exception:
            value = None
        self._obp_cache = value
        return value

    def _reject_stamp(self, intent):
        """D-01-REJECT-PAYLOAD-20261115 (spec W5D-REJECT-PAYLOAD-SPEC
        sections 3 to 5): the gradeable identity of a rejected
        intent, stamped on EVERY intent_rejected row from the intent
        itself at reject time. One helper, every reject site: _reject
        merges it and the inline insufficient_options_bp_csp site
        merges it; a future site that writes an intent_rejected row
        without it is a defect, not a variant. Read-only on the
        intent, O(1), and it changes no reject logic, reason,
        ordering, or order flow.

        reference_price precedence, first match wins: intent
        price_hint, then limit_price, then stop_price, each only
        when present and greater than 0, then the dispatcher's own
        last held quote mid for the symbol (the _quote_mids mapping,
        when this dispatcher holds one; the production dispatcher
        holds none today, so that step simply does not fire), then
        null with source "unavailable". Never backfilled from bars
        or the fill ledger.

        Never silent omission: every stamped key is present on
        every row. A genuinely unavailable graded field (symbol,
        side, kind, qty, reference_price) is an explicit null, its
        name is listed in missing_fields, and missing_reason says
        why in plain words; a malformed qty or kind (the bad_qty /
        bad_kind path) is stamped null on the same rule."""
        intent = intent if isinstance(intent, dict) else {}
        missing = []
        reasons = []

        def _absent(field, carried, malformed):
            missing.append(field)
            reasons.append(malformed if carried else
                           f"intent carried no {field}")

        symbol = intent.get("symbol")
        if not isinstance(symbol, str) or not symbol:
            _absent("symbol", symbol is not None,
                    "intent symbol was malformed")
            symbol = None
        side = intent.get("side")
        if side not in ("buy", "sell"):
            _absent("side", side is not None,
                    "intent side was malformed")
            side = None
        kind = intent.get("kind")
        if kind not in ("entry", "exit"):
            _absent("kind", kind is not None,
                    "intent kind was malformed")
            kind = None
        qty = intent.get("qty")
        if isinstance(qty, bool) \
                or not isinstance(qty, (int, float)) or qty <= 0:
            _absent("qty", qty is not None,
                    "intent qty was malformed")
            qty = None
        reference_price = None
        reference_price_source = "unavailable"
        for key, source in (("price_hint", "intent_price_hint"),
                            ("limit_price", "intent_limit_price"),
                            ("stop_price", "intent_stop_price")):
            value = intent.get(key)
            if isinstance(value, (int, float)) \
                    and not isinstance(value, bool) and value > 0:
                reference_price = float(value)
                reference_price_source = source
                break
        if reference_price is None:
            held = getattr(self, "_quote_mids", None)
            value = held.get(symbol) if isinstance(held, dict) \
                and symbol is not None else None
            if isinstance(value, (int, float)) \
                    and not isinstance(value, bool) and value > 0:
                reference_price = float(value)
                reference_price_source = \
                    "dispatcher_quote_mid_at_reject"
        if reference_price is None:
            missing.append("reference_price")
            reasons.append("no price on intent and no quote held "
                           "at reject time")
        now = self._now_fn()
        if now.tzinfo is None:
            now = now.replace(tzinfo=ET)
        return {"ts_utc": now.astimezone(timezone.utc).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"),
                "symbol": symbol, "side": side, "kind": kind,
                "qty": qty, "reference_price": reference_price,
                "reference_price_source": reference_price_source,
                "missing_fields": missing,
                "missing_reason": "; ".join(reasons) if missing
                else None,
                "stamp_version": 1}

    def _reject(self, intent, sleeve_id, reason, ref_price=None):
        # INTENT-LOG-FIELDS-20261115: every rejection record carries
        # the intent's symbol, side, and reference price at emission.
        # Pre-cure rows carried only event, intent_id, sleeve and
        # reason, so the rejected population (773 insufficient_
        # slice_bp entry blocks in the Lane 3 census) could never be
        # graded as a shadow portfolio. ref_price resolves from the
        # caller's authoritative price when one was computed (the
        # buying-power gate passes its own price), else the intent's
        # limit_price, else its price_hint, else None (no reference
        # price existed at that gate; the key is still present).
        if ref_price is None:
            ref_price = intent.get("limit_price") \
                or intent.get("price_hint")
        row = {"event": "intent_rejected",
               "intent_id": intent.get("intent_id"),
               "sleeve": sleeve_id, "reason": reason,
               "symbol": intent.get("symbol"),
               "side": intent.get("side"),
               "ref_price": ref_price}
        # EXIT-REASON-FIELDS-20261115: a rejected exit records its
        # strategy reason too, so the refused-exit population is
        # gradable beside the filled one.
        row.update(exit_reason_fields(intent, sleeve_id))
        row.update(self._reject_stamp(intent))
        if reason == "reconcile_halt":
            # HALT-CONTEXT-20261030: name the symbol and both
            # quantities behind the gate, from the gate's own record.
            row.update(self._halt_context(sleeve_id))
            row["symbol"] = intent.get("symbol")
        append_line(self.djournal, row)
        self._index()
        self._seen.add(intent.get("intent_id"))
        return {"status": "rejected", "reason": reason,
                "intent_id": intent.get("intent_id")}

    def sweep_fills(self):
        """FILL-CAPTURE-20261030: import fills the submit-time
        read-back missed (see desk3/reconcile.py
        sweep_unjournaled_fills for the root cause). Safe on brokers
        without a read-back: returns a named no-op result."""
        if not hasattr(self.broker, "get_order_by_client_id"):
            return {"checked": 0, "imported_rows": 0,
                    "imported_qty": 0.0, "still_unfilled": 0,
                    "errors": [{"error": "broker_has_no_readback"}]}
        from .reconcile import sweep_unjournaled_fills
        return sweep_unjournaled_fills(self.state, self.broker)

    def _paper_fill_enj(self, intent, sleeve_id, is_exit):
        """ENJ-PAPER-20261116: fill one ENJ-class intent in the
        free_kraken paper form. The fill price is the Kraken feed
        price the intent itself carries (limit_price, else
        price_hint — every ENJ engine stamps its tape price there —
        else the dispatcher's snapshot price_lookup); a class intent
        with no feed price fails closed by name, exactly as an
        unpriced entry fails at the buying-power gate. Entries face
        the same slice buying-power check a broker entry faces
        (cost vs cash net of reservations; no reservation is taken,
        the fill is immediate). Exits reconcile against the sleeve's
        OWN slice position — the paper book is the book of record
        for this class, the broker book can never hold ENJ — and
        clamp to the held quantity, journaling the clamp. The slice
        cash/position update mirrors the broker fill branch's signed
        rule verbatim, and the journaled row is an ordinary fill row
        plus the venue/provenance stamp, so seed_slices,
        own_book_positions, the fill ledger and the conversion
        grader's fill loader all read it through their existing
        paths. Reconcile partitions these rows out of the broker
        comparison by their venue stamp (desk3/reconcile.py
        journal_paper_book): they are claims on the paper book,
        never on the broker."""
        iid = intent.get("intent_id")
        sl = self.slice_for(sleeve_id)
        coid = client_order_id(sleeve_id, iid)
        sym = intent["symbol"]
        if intent.get("limit_price"):
            price, price_source = float(intent["limit_price"]), \
                "limit_price"
        elif intent.get("price_hint"):
            price, price_source = float(intent["price_hint"]), \
                "price_hint"
        else:
            looked = self.price_lookup(sym)
            if looked is None:
                return self._reject(
                    intent, sleeve_id,
                    "paper_fill_no_price" if is_exit
                    else "no_price_for_bp")
            price, price_source = float(looked), "price_lookup"
        if not (price > 0):
            return self._reject(
                intent, sleeve_id,
                "paper_fill_no_price" if is_exit else "no_price_for_bp")
        try:
            qty = float(intent["qty"])
        except (TypeError, ValueError):
            qty = 0.0
        if qty <= 0:
            return self._reject(intent, sleeve_id,
                                "paper_fill_bad_qty")
        clamped = False
        if not is_exit:
            cost = price * qty * _cash_multiplier(sym)
            available = sl["cash_usd"] - sl["reserved_usd"]
            if cost > available:
                return self._reject(intent, sleeve_id,
                                    "insufficient_slice_bp",
                                    ref_price=price)
            fill_qty = qty
        else:
            pos = sl["positions"].get(sym)
            held = float(pos["qty"]) if pos else 0.0
            if held == 0.0:
                return self._reject(intent, sleeve_id,
                                    "exit_satisfied_no_paper_position")
            close_side = "sell" if held > 0 else "buy"
            if intent.get("side") != close_side:
                return self._reject(intent, sleeve_id,
                                    "paper_exit_side_mismatch")
            fill_qty = min(qty, abs(held))
            clamped = fill_qty != qty
        signed = fill_qty if intent["side"] == "buy" else -fill_qty
        mult = _cash_multiplier(sym)
        sl["cash_usd"] -= signed * price * mult
        pos = sl["positions"].setdefault(
            sym, {"symbol": sym, "qty": 0.0, "avg_price": 0.0})
        if not is_exit:
            newq = pos["qty"] + signed
            if newq:
                pos["avg_price"] = (pos["avg_price"] * pos["qty"]
                                    + price * signed) / newq
            pos["qty"] = newq
        else:
            pos["qty"] += signed
        if pos["qty"] == 0:
            del sl["positions"][sym]
        row = {"event": "fill", "intent_id": iid,
               "sleeve": sleeve_id, "client_order_id": coid,
               "symbol": sym, "side": intent["side"],
               "qty": fill_qty, "price": price,
               "position_intent": intent.get("position_intent"),
               "ts": datetime.now(timezone.utc).isoformat(),
               "venue": ENJ_PAPER_VENUE,
               "feed_source": "kraken_public_spot",
               "pair": "ENJUSD",
               "fill_price_source": price_source}
        if clamped:
            row["qty_clamped_to_paper_position"] = True
            row["requested_qty"] = qty
        row.update(exit_reason_fields(intent, sleeve_id))
        append_line(self.djournal, row)
        self._vb_note_fill(sleeve_id, sym, intent["side"], fill_qty)
        self._index()
        self._seen.add(iid)
        return {"status": "filled", "intent_id": iid,
                "client_order_id": coid, "qty": fill_qty,
                "price": price, "venue": ENJ_PAPER_VENUE}

    def process_intent(self, intent, sleeve_id, _from_drain=False):
        self._index()
        iid = intent.get("intent_id")
        if iid in self._seen:
            append_line(self.djournal, {"event": "intent_duplicate",
                                        "intent_id": iid, "sleeve": sleeve_id})
            return {"status": "duplicate", "intent_id": iid}
        try:
            validate_intent(intent)
        except IntentError as e:
            return self._reject(intent, sleeve_id, str(e))
        sl = self.slice_for(sleeve_id)
        # D-GATE-20261025: an exit is the exit kind or a closing
        # position_intent ONLY. Side alone never makes an exit: a
        # sell_to_open ENTRY faces the reconcile halt and the slice
        # buying-power gate exactly like a buy_to_open entry.
        is_exit = intent["kind"] == "exit" or intent.get(
            "position_intent") in ("buy_to_close", "sell_to_close")
        # CURE-DC3-20261113: a close-shaped intent that arrives
        # WITHOUT any position_intent declaration takes the exit
        # path when the broker book of record holds the position
        # it closes. Classification was the ONLY door to the exit
        # protections (pre-flight, storm dedupe, virtual book):
        # leaps_momentum's undeclared QQQ sells — an economic
        # close of the 14 QQQ the book held, fully reserved by
        # another sleeve's resting close — burned a deterministic
        # terminal 403 per cycle on the entry path (69 rows on
        # 2026-11-13) while every classified exit to the same
        # book was intercepted locally. The broker infers exactly
        # this close for an undeclared intent: position_intent
        # reaches the wire, and absent one the inference is the
        # broker's, so the door's classification now agrees with
        # the book of record. A DECLARED intent is never
        # rewritten; an oversize or position-less shape is
        # untouched; only the exact close shape (closing side,
        # qty <= |book position|) is reclassified, and the
        # reclassification is journaled with its evidence.
        if not is_exit and intent.get("position_intent") is None \
                and getattr(self.broker, "live_book", False) \
                and hasattr(self.broker, "get_positions") \
                and hasattr(self.broker, "get_open_orders"):
            _bp, _bo = self._exit_book()
            _bpos = _bp.get(
                _normalize_broker_symbol(intent.get("symbol")), 0.0)
            if _bpos != 0.0:
                _cs = "sell" if _bpos > 0 else "buy"
                try:
                    _q = float(intent.get("qty") or 0)
                except (TypeError, ValueError):
                    _q = 0.0
                if intent.get("side") == _cs \
                        and 0.0 < _q <= abs(_bpos) + 1e-9:
                    intent = dict(intent)
                    intent["position_intent"] = (
                        "sell_to_close" if _bpos > 0
                        else "buy_to_close")
                    is_exit = True
                    append_line(self.djournal, {
                        "event": "intent_reclassified_close_shape",
                        "intent_id": iid, "sleeve": sleeve_id,
                        "symbol": intent.get("symbol"),
                        "side": intent.get("side"), "qty": _q,
                        "kind": intent.get("kind"),
                        "broker_position": _bpos,
                        "to_position_intent":
                            intent["position_intent"]})
        if not is_exit and (self._halt_applies(sleeve_id,
                                               intent.get("symbol"))
                            or self.cash_halt):
            # A15: a reconcile discrepancy halts NEW ENTRIES for the
            # affected sleeve only; exits always pass.
            # HALT-SYMBOL-SCOPE-20261116: a position discrepancy
            # halts only entries in its own symbol.
            return self._reject(intent, sleeve_id, "reconcile_halt")
        # BLOCKED-EXIT-20261029: every intent is translated to the
        # broker dialect, and every EXIT is reconciled against the
        # broker book of record, before any gate or submit below.
        intent = self._apply_broker_dialect(dict(intent), sleeve_id)
        # DOOR-PREFLIGHT-20261030: proven-422 field shapes are
        # rejected locally with a named reason and never reach the
        # wire (the historical Oct 27 and Oct 29 payloads are the
        # blocker fixtures). Warnings ride the journal, not the gate.
        _violation = _preflight_violation(intent, sleeve_id)
        if _violation is not None:
            return self._reject(intent, sleeve_id, _violation)
        for _warn in _preflight_warnings(intent, sleeve_id):
            append_line(self.djournal,
                        {"event": "preflight_warning",
                         "intent_id": iid, "sleeve": sleeve_id,
                         "warning": _warn,
                         "symbol": intent.get("symbol")})
        if getattr(self.broker, "live_book", False) \
                and _enj_paper_class(sleeve_id, intent.get("symbol")):
            # ENJ-PAPER-20261116: the ENJ class fills here, in the
            # free_kraken paper form, before the broker-book exit
            # reconciliation (whose book can never hold ENJ) and
            # before any submit path. Entries and exits alike: a
            # paper position must be closable in the same form it
            # opened. Scoped to the live book exactly like the
            # INTENT-RECORDED seam below; the PF_ class and every
            # non-ENJ sleeve continue past this point unchanged.
            return self._paper_fill_enj(intent, sleeve_id, is_exit)
        if is_exit:
            _terminal = self._reconcile_exit(intent, sleeve_id)
            if _terminal is not None:
                return _terminal
        cost = 0.0
        if not is_exit:
            price = intent.get("limit_price") or intent.get("price_hint") \
                or self.price_lookup(intent["symbol"])
            if price is None:
                return self._reject(intent, sleeve_id, "no_price_for_bp")
            # READINESS-DSP2-20261112: an OCC entry's cost is
            # premium x contracts x 100 (see _cash_multiplier); the
            # reservation below and its releases charge this same
            # figure, so the gate and the book agree to the cent.
            cost = float(price) * float(intent["qty"]) \
                * _cash_multiplier(intent["symbol"])
            available = sl["cash_usd"] - sl["reserved_usd"]
            if cost > available:
                # INTENT-LOG-FIELDS-20261115: the gate's own price is
                # the blocked entry's reference price; pass it so the
                # rejection record can be marked forward.
                return self._reject(intent, sleeve_id,
                                    "insufficient_slice_bp",
                                    ref_price=price)
            sl["reserved_usd"] += cost * (1 + sl.get("bp_buffer_frac", 0.02))
            # CSP-PREFLIGHT-20261104: a sell_to_open on an OCC
            # symbol is cash-secured at the broker: it needs
            # strike x 100 x contracts of collateral, less the
            # premium received. On 2026-11-03 qqq_put_ladder
            # re-presented a put needing ~$1,040,231 against an
            # options buying power under that figure and drew 57
            # broker 403 rows for a verdict the account state
            # already determined. Refuse it locally by name. When
            # the broker cannot report options buying power, no
            # gate applies: an unanswerable question must not
            # become a new failure mode.
            if intent.get("position_intent") == "sell_to_open" and \
                    OCC_RE.match(intent["symbol"] or ""):
                obp = self._options_buying_power()
                if obp is not None:
                    strike = int(intent["symbol"][-8:]) / 1000.0
                    qty = float(intent["qty"])
                    required = strike * 100.0 * qty
                    premium = float(price) * 100.0 * qty
                    if required - premium > obp:
                        row = {"event": "intent_rejected",
                               "intent_id": iid, "sleeve": sleeve_id,
                               "reason": "insufficient_options_bp_csp",
                               "symbol": intent["symbol"],
                               # INTENT-LOG-FIELDS-20261115: same
                               # field contract as _reject's rows.
                               "side": intent.get("side"),
                               "ref_price": price,
                               "required_collateral_usd":
                                   round(required - premium, 2),
                               "options_buying_power_usd": obp}
                        # D-01-REJECT-PAYLOAD-20261115: the inline
                        # site carries the identical stamp.
                        row.update(self._reject_stamp(intent))
                        append_line(self.djournal, row)
                        self._index()
                        self._seen.add(iid)
                        return {"status": "rejected",
                                "reason": "insufficient_options_bp_csp",
                                "intent_id": iid}
        coid = client_order_id(sleeve_id, iid)
        if not is_exit and getattr(self.broker, "live_book", False) \
                and _intent_recorded_symbol(intent.get("symbol")):
            # INTENT-RECORDED-UNLISTED-20261116: an intent-graded
            # sleeve's entry in a proven-unlisted symbol is recorded
            # as an intent and consumed here; it is never submitted
            # to the broker. Pre-cure these entries passed every
            # local gate and burned a broker 422 pair each (Sunday
            # 2026-11-15: 71 distinct intents, 142 broker rows, on
            # ENJ/USD and PF_ADAUSD). The recorded row carries every
            # field the conversion grader's intent loader reads, and
            # load_intent_entries accepts this event beside the
            # historical broker_rejected_terminal rows, so the
            # grader's input population is unchanged. Scoped to the
            # live book: test doubles model other doors (the kraken
            # e2e contracts dispatch these symbols through a
            # FakeBroker by design). Exits are untouched: a held
            # position must always be closable. The slice
            # reservation taken by the BP gate above is released:
            # no order exists.
            if cost:
                sl["reserved_usd"] = max(
                    0.0, sl["reserved_usd"]
                    - cost * (1 + sl.get("bp_buffer_frac", 0.02)))
            append_line(self.djournal, {
                "event": "intent_recorded",
                "intent_id": iid, "sleeve": sleeve_id,
                "client_order_id": coid,
                "reason": "intent_recorded_unlisted_symbol",
                "symbol": intent.get("symbol"),
                "side": intent.get("side"),
                "qty": intent.get("qty"),
                "kind": intent.get("kind"),
                "position_intent": intent.get("position_intent"),
                "order_type": intent.get("order_type", "market"),
                "time_in_force": intent.get("time_in_force", "day")})
            self._index()
            self._seen.add(iid)
            return {"status": "recorded",
                    "reason": "intent_recorded_unlisted_symbol",
                    "intent_id": iid, "client_order_id": coid}
        # BROKER-BURST-20261026: bounded in-call retry for
        # broker-unavailable-class submit failures (HTTP 403 / 429 /
        # 5xx / connection errors — DRAIN-CLASS-20261026 unified the
        # classifier in _broker_unavailable_class: 403 joined the
        # class because Alpaca's 40310000 is an account-state answer,
        # not a rejection of the intent; the 2026-10-26 bursts failed
        # ~80% of submits interleaved with successes from the first
        # intent of the cycle, i.e. per-request transients, not a
        # rate-limit onset). The retry happens inside this call, at
        # the intent's own dispatch moment — no sleeve's evaluation
        # is delayed or paced (R-5). An HTTP error outside the class
        # (e.g. 422 validation) is never retried: it would fail
        # identically. The same client_order_id is reused, so a submit
        # that reached the broker before its response was lost is
        # deduped by the broker, never doubled.
        submit_error = None
        submit_transient = True
        attempts_made = 0
        for attempt in range(3):
            attempts_made = attempt + 1
            try:
                self.broker.submit_order(
                    coid, intent["symbol"], intent["side"], intent["qty"],
                    intent.get("order_type", "market"),
                    limit_price=intent.get("limit_price"),
                    time_in_force=intent.get("time_in_force", "day"),
                    # BLOCKED-EXIT-20261029: the intent's declared
                    # position_intent reaches the wire (the door
                    # dropped it before this cure — the broker then
                    # inferred opens from closes). stop_price rides
                    # only on stop order types; on market/limit
                    # intents it stays sleeve reference data.
                    position_intent=intent.get("position_intent"),
                    stop_price=(intent.get("stop_price")
                                if "stop" in str(intent.get(
                                    "order_type", "market")) else None))
                submit_error = None
                # Our resting-order set just changed; the next exit's
                # pre-flight must re-read the book.
                self._book_cache = None
                break
            except Exception as e:  # noqa: BLE001 - classified below
                submit_error = e
                # BLOCKED-EXIT-20261029: a terminal 403 subclass
                # (wash trade / qty held / intent mismatch / balance)
                # is a verdict about THIS intent, not broker
                # unavailability: never retried, never re-queued.
                submit_transient = _broker_unavailable_class(
                    getattr(e, "status", None)) and not \
                    _terminal_broker_answer(
                        getattr(e, "status", None),
                        getattr(e, "body", None) or str(e))
                if not submit_transient or attempt == 2:
                    break
                import time as _time
                _time.sleep(0.25 if attempt == 0 else 0.75)
        if submit_error is not None:
            # Door down: queue for retry, NO fill is recorded (fills come
            # only from read-back after a successful submit). The error
            # is JOURNALED (type + HTTP status) — before this cure the
            # exception was swallowed whole and the burst's cause was
            # unrecoverable from the record.
            # BROKER-PENDING-DRAIN-20261026: the queue is now DURABLE.
            # The full intent + sleeve + ORIGINAL client_order_id +
            # session date + attempt count + last error are persisted
            # to the pending store BEFORE returning, so a Dispatcher
            # rebuilt next cycle (cycle.py builds one per cycle) drains
            # from the store instead of discarding the intent. The
            # slice reservation is released: no order exists at the
            # broker, and the drain re-runs the BP gate from scratch.
            if not is_exit and cost:
                sl["reserved_usd"] = max(
                    0.0, sl["reserved_usd"]
                    - cost * (1 + sl.get("bp_buffer_frac", 0.02)))
            # EXIT-STORM-DEDUPE-20261111: a terminal broker answer
            # of the held-for-orders class on an EXIT (the
            # leaps_momentum wire shape: the position is fully
            # reserved by a resting close) records the same
            # suppression key as the local resting verdict, so the
            # sleeve's next-cycle re-emission is answered from the
            # book instead of reaching the wire every cycle.
            if is_exit and _terminal_broker_answer(
                    getattr(submit_error, "status", None),
                    getattr(submit_error, "body", None)
                    or str(submit_error)):
                _err_text = str(getattr(submit_error, "body", None)
                                or submit_error)
                if "held_for_orders" in _err_text \
                        or "insufficient qty available" in _err_text:
                    self._storm_note(
                        sleeve_id, intent["symbol"],
                        "exit_already_resting_at_broker")
                elif "potential wash trade" in _err_text:
                    # CURE-DC2-20261113: a wash-trade verdict the
                    # pre-flight could not see (the opposite order
                    # rested after its book read) records the
                    # opposite-side storm class, whose check
                    # re-reads the current book before honouring
                    # it — the verdict becomes learnable instead
                    # of a per-cycle storm.
                    self._storm_note(
                        sleeve_id, intent["symbol"],
                        "exit_blocked_opposite_side_resting")
            # DRAIN-INTENT-MISMATCH-20261110 (W4, DSK-12): a submit
            # whose broker answer is a position-intent mismatch is
            # a DETERMINISTIC verdict about this intent against the
            # CURRENT broker book, exactly like a 422 validation: it
            # already arrives as HTTP 422 code 42210000. It must not
            # take the broker-unavailable queue path below: queueing
            # it re-presents the same intent to the drain, whose
            # re-check then saw the flattened book and journaled a
            # second, contradictory terminal pair for one consumption
            # (27 wire rejections in 48 h, the census's DSK-12).
            # The exit is consumed HERE, terminally, with the
            # broker's verdict named; the sleeve re-emits a fresh
            # exit next cycle if its own book still holds the
            # position. The marker is matched against the broker's
            # body/message text, the same evidence _terminal_broker_
            # answer reads for 403s.
            _mismatch = "position intent mismatch" in str(
                getattr(submit_error, "body", None) or submit_error)
            if _mismatch:
                append_line(self.djournal, {
                    "event": "broker_rejected_terminal",
                    "intent_id": iid, "sleeve": sleeve_id,
                    "client_order_id": coid,
                    "http_status": getattr(submit_error, "status",
                                           None),
                    "broker_code": 42210000,
                    "broker_message": "position intent mismatch "
                                      "(terminal at first answer; "
                                      "never queued)",
                    "symbol": intent.get("symbol"),
                    "side": intent.get("side"),
                    "qty": intent.get("qty"),
                    "kind": intent.get("kind"),
                    "position_intent": intent.get(
                        "position_intent"),
                    "order_type": intent.get("order_type", "market"),
                    "time_in_force": intent.get(
                        "time_in_force", "day")})
                return {"status": "rejected",
                        "reason": "position_intent_mismatch_terminal",
                        "intent_id": iid,
                        "client_order_id": coid}
            # DRAIN-INTENT-MISMATCH-20261110 (W4, DSK-12): a submit
            # whose broker answer is a position-intent mismatch is
            # a DETERMINISTIC verdict about this intent against the
            # CURRENT broker book, exactly like a 422 validation: it
            # already arrives as HTTP 422 code 42210000. It must not
            # take the broker-unavailable queue path below: queueing
            # it re-presents the same intent to the drain, whose
            # re-check then saw the flattened book and journaled a
            # second, contradictory terminal pair for one consumption
            # (27 wire rejections in 48 h, the census's DSK-12).
            # The exit is consumed HERE, terminally, with the
            # broker's verdict named; the sleeve re-emits a fresh
            # exit next cycle if its own book still holds the
            # position. The marker is matched against the broker's
            # body/message text, the same evidence _terminal_broker_
            # answer reads for 403s.
            _mismatch = "position intent mismatch" in str(
                getattr(submit_error, "body", None) or submit_error)
            if _mismatch:
                append_line(self.djournal, {
                    "event": "broker_rejected_terminal",
                    "intent_id": iid, "sleeve": sleeve_id,
                    "client_order_id": coid,
                    "http_status": getattr(submit_error, "status",
                                           None),
                    "broker_code": 42210000,
                    "broker_message": "position intent mismatch "
                                      "(terminal at first answer; "
                                      "never queued)",
                    "symbol": intent.get("symbol"),
                    "side": intent.get("side"),
                    "qty": intent.get("qty"),
                    "kind": intent.get("kind"),
                    "position_intent": intent.get(
                        "position_intent"),
                    "order_type": intent.get("order_type", "market"),
                    "time_in_force": intent.get(
                        "time_in_force", "day")})
                return {"status": "rejected",
                        "reason": "position_intent_mismatch_terminal",
                        "intent_id": iid,
                        "client_order_id": coid}
            err = f"{type(submit_error).__name__}:{submit_error}"
            # READINESS-DSP1-20261112 (DEFECT-HUNT DSP-1): the
            # pending store is written ONLY for the transient
            # broker-unavailable class. A non-transient failure is a
            # deterministic verdict about this intent (422
            # validation; a terminal 403 subclass): persisting it
            # made the next cycle's drain submit the identical
            # payload a second time and draw the identical verdict
            # (live 2026-11-12: 445 terminal rows over 301 intents,
            # 144 with exactly 2). Terminal answers are consumed
            # below, after the journal rows.
            if submit_transient:
                if _from_drain:
                    prior = next(
                        (e for e in self.pending_store.load()
                         if e.get("client_order_id") == coid), None)
                    entry = {"intent": dict(intent), "sleeve_id": sleeve_id,
                             "client_order_id": coid,
                             "session_date": (prior or {}).get(
                                 "session_date", self.session_date),
                             "attempts": int((prior or {}).get("attempts", 0))
                             + attempts_made,
                             "last_error": err,
                             "queued_at": (prior or {}).get("queued_at")
                             or datetime.now(timezone.utc).isoformat()}
                    if prior is not None:
                        self.pending_store.update(entry)
                    else:
                        self.pending_store.add(entry)
                        self._pending.append((dict(intent), sleeve_id))
                else:
                    self.pending_store.add(
                        {"intent": dict(intent), "sleeve_id": sleeve_id,
                         "client_order_id": coid,
                         "session_date": self.session_date,
                         "attempts": attempts_made, "last_error": err,
                         "queued_at": datetime.now(timezone.utc).isoformat()})
                    self._pending.append((dict(intent), sleeve_id))
            append_line(self.djournal, {"event": "broker_unavailable",
                                        "intent_id": iid, "sleeve": sleeve_id,
                                        "client_order_id": coid,
                                        "error": err,
                                        # BROKER-422-BODY-20261027: the
                                        # broker response body (names the
                                        # failing field on a 422) and the
                                        # exact submitted payload, so a
                                        # rejection is diagnosable from
                                        # the journal alone.
                                        "error_body": getattr(
                                            submit_error, "body", None),
                                        "kind": intent.get("kind"),
                                        "position_intent": intent.get(
                                            "position_intent"),
                                        "symbol": intent.get("symbol"),
                                        "side": intent.get("side"),
                                        "qty": intent.get("qty"),
                                        "order_type": intent.get(
                                            "order_type", "market"),
                                        "limit_price": intent.get(
                                            "limit_price"),
                                        "time_in_force": intent.get(
                                            "time_in_force", "day")})
            if getattr(submit_error, "status", None) == 422:
                # TERMINAL-422-JOURNAL-20261030: a 422 is a
                # deterministic verdict about this payload, not door
                # unavailability. It keeps the broker_unavailable row
                # above (the drain-class contract three committed
                # blockers read) AND gains its own terminal event
                # carrying the parsed code and message, so censuses
                # count 422s directly instead of re-parsing bodies.
                # DRAIN-INTENT-MISMATCH-20261110: the position-
                # intent mismatch 422 no longer reaches this branch
                # (it returns terminally above); every other 422
                # keeps this exact behavior.
                # DRAIN-INTENT-MISMATCH-20261110: the position-
                # intent mismatch 422 no longer reaches this branch
                # (it returns terminally above); every other 422
                # keeps this exact behavior.
                _code, _msg = None, None
                try:
                    _parsed = json.loads(
                        getattr(submit_error, "body", None) or "")
                    if isinstance(_parsed, dict):
                        _code = _parsed.get("code")
                        _msg = _parsed.get("message")
                except (ValueError, TypeError):
                    _msg = getattr(submit_error, "body", None)
                append_line(self.djournal, {
                    "event": "broker_rejected_terminal",
                    "intent_id": iid, "sleeve": sleeve_id,
                    "client_order_id": coid, "http_status": 422,
                    "broker_code": _code, "broker_message": _msg,
                    "symbol": intent.get("symbol"),
                    "side": intent.get("side"),
                    "qty": intent.get("qty"),
                    "kind": intent.get("kind"),
                    "position_intent": intent.get(
                        "position_intent"),
                    "order_type": intent.get("order_type", "market"),
                    "time_in_force": intent.get(
                        "time_in_force", "day")})
            elif not submit_transient:
                # READINESS-DSP1-20261112: a terminal non-422 answer
                # (the terminal 403 subclasses) gains the same
                # terminal event, so the verdict is on the record
                # the duplicate index reads.
                _code, _msg = None, None
                try:
                    _parsed = json.loads(
                        getattr(submit_error, "body", None) or "")
                    if isinstance(_parsed, dict):
                        _code = _parsed.get("code")
                        _msg = _parsed.get("message")
                except (ValueError, TypeError):
                    _msg = getattr(submit_error, "body", None)
                append_line(self.djournal, {
                    "event": "broker_rejected_terminal",
                    "intent_id": iid, "sleeve": sleeve_id,
                    "client_order_id": coid,
                    "http_status": getattr(submit_error, "status",
                                           None),
                    "broker_code": _code, "broker_message": _msg,
                    "symbol": intent.get("symbol"),
                    "side": intent.get("side"),
                    "qty": intent.get("qty"),
                    "kind": intent.get("kind"),
                    "position_intent": intent.get(
                        "position_intent"),
                    "order_type": intent.get("order_type", "market"),
                    "time_in_force": intent.get(
                        "time_in_force", "day")})
            if not submit_transient:
                # READINESS-DSP1-20261112: the verdict consumes the
                # intent HERE. Nothing was persisted above, and the
                # index add makes a same-instance re-presentation a
                # duplicate; a rebuilt dispatcher's index learns the
                # verdict from the broker_rejected_terminal row
                # (now an indexed event, see _index).
                self._index()
                self._seen.add(iid)
                return {"status": "rejected",
                        "reason": "broker_rejected_terminal",
                        "intent_id": iid,
                        "client_order_id": coid,
                        "transient": False, "last_error": err}
            return {"status": "queued", "intent_id": iid,
                    "client_order_id": coid,
                    "transient": submit_transient, "last_error": err}
        append_line(self.djournal, {"event": "order_submitted", "intent_id": iid,
                                    "sleeve": sleeve_id, "client_order_id": coid,
                                    "symbol": intent["symbol"]})
        self._seen.add(iid)
        # Fills ONLY from broker read-back.
        order = self.broker.get_order_by_client_id(coid)
        if order.get("status") != "filled":
            return {"status": "submitted", "intent_id": iid,
                    "client_order_id": coid}
        fill_qty = float(order.get("filled_qty", intent["qty"]))
        fill_px = float(order.get("filled_avg_price") or 0.0)
        # READINESS-DSP2-20261112: ONE signed fill update for both
        # branches. A fill's signed quantity is +qty on a buy and
        # -qty on a sell; cash moves -(signed x price x multiplier)
        # and the position moves by the signed quantity. The
        # pre-cure code debited every entry fill and credited every
        # exit fill at x1: a sell_to_open was booked as a long
        # position bought with cash, and an options fill moved
        # 1/100 of its true cash. Under the signed rule a buy
        # debits, a sell_to_open credits the premium and books a
        # negative position, a sell_to_close credits, and a
        # buy_to_close debits and closes the short toward zero —
        # for equity (x1) the figures are exactly the pre-cure ones
        # on the long paths the old code modeled.
        _signed_fill = fill_qty if intent["side"] == "buy" \
            else -fill_qty
        _mult = _cash_multiplier(intent["symbol"])
        if not is_exit:
            sl["reserved_usd"] = max(
                0.0, sl["reserved_usd"] - cost * (1 + sl.get("bp_buffer_frac", 0.02)))
            sl["cash_usd"] -= _signed_fill * fill_px * _mult
            pos = sl["positions"].setdefault(
                intent["symbol"], {"symbol": intent["symbol"], "qty": 0.0,
                                   "avg_price": 0.0})
            newq = pos["qty"] + _signed_fill
            if newq:
                pos["avg_price"] = (pos["avg_price"] * pos["qty"]
                                    + fill_px * _signed_fill) / newq
            pos["qty"] = newq
            if pos["qty"] == 0:
                del sl["positions"][intent["symbol"]]
        else:
            sl["cash_usd"] -= _signed_fill * fill_px * _mult
            pos = sl["positions"].get(intent["symbol"])
            if pos:
                pos["qty"] += _signed_fill
                if pos["qty"] == 0:
                    del sl["positions"][intent["symbol"]]
        # HARDEN-CURE3: a fill row must carry its session timestamp
        # and position_intent — state/session_fills (the session_fills
        # producer's source) cannot prove a fill's session without
        # them, so session-aware sleeves starved on untimestamped rows.
        # EXIT-REASON-FIELDS-20261115: an exit fill carries its
        # strategy reason and triggering values, classified from
        # the intent at fill time (the fill ledger copies fill
        # rows verbatim, so the stamp propagates). Entry fills
        # carry neither key, exactly as pre-cure.
        _fill_row = {"event": "fill", "intent_id": iid,
                     "sleeve": sleeve_id,
                     "client_order_id": coid,
                     "symbol": intent["symbol"],
                     "side": intent["side"], "qty": fill_qty,
                     "price": fill_px,
                     "position_intent":
                         intent.get("position_intent"),
                     "ts": datetime.now(
                         timezone.utc).isoformat()}
        _fill_row.update(exit_reason_fields(intent, sleeve_id))
        append_line(self.djournal, _fill_row)
        # VIRTUAL-BOOK staging: this dispatcher's cached derived
        # book learns its own fills immediately (sweep-imported fills
        # are re-derived next cycle).
        self._vb_note_fill(sleeve_id, intent["symbol"], intent["side"],
                           fill_qty)
        return {"status": "filled", "intent_id": iid, "client_order_id": coid,
                "qty": fill_qty, "price": fill_px}
