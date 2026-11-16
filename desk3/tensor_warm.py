"""Tensor bundle warmer (R4 TENSOR WARMER, MIDNA RULING 2026-10-25;
audit OPEN #6).

The production-path producer for the Tensor bundle file the batch-2
readers in desk3/producers.py serve (cache/tensor/bundle.json ->
keys "tensor" / "tensor_fires" / "tensor_daily20"). Ported from
muse-desk-v2 runtime/tensor_warm.py @3593668, which ran the
faithfully ported femto-lean producer (core/tensor_feeds.py
TensorProducer) on the warmer side; v3's core/tensor_feeds.py and the
vendored engine (vendor/tensor_exact.py + vendor/tensor_exact/,
hash-pinned v698) and canonical feed (vendor/canonical_bars.py) are
byte-identical ports of the v2 files — the Tensor ENGINE is a hard
rail: never modified, invoked exactly as v2 invoked it
(exact_swing_signal over core.data.tensor_bars, the single canonical
door; swing_lookback=4 entry / 1 exit, inside TensorProducer).

Bundle = {"session", "generated_at",
          "sleeves": {"tensor_swing":   {"tensor_signals": [...],
                                         "tensor_exit": {...}},
                      "tensor_red_dip": {"tensor_signals": [...],
                                         "qqq_day_return": ...,
                                         "day_returns": {...},
                                         "nyse_holidays": [...]}},
          "fires": [...]}
"fires" is the engine's own confirmed-swing signal list (the same
rows the sleeves channel carries) — the bundle's documented fires
channel (producers.py). Consumers gate on their own feature fields
and fail closed on rows that lack them (aster_batch14._passes /
aster_batch15.g4_passes return False on missing fields), so serving
the engine's rows never fake-fires an Aster book.

Since the TENSOR-SERVE-SHAPE cure (2026-11-12) the bundle also
carries the canonical native product built by desk3/tensor_native
over the producer's evaluated universe: "tensor_analysis"
(per-symbol prepared r19 records), "tensor_census" (the enrollment
assessment the G4 event bridge gates on), "tensor_universe", and
per-symbol 1h native state panels under symbol keys
({SYM: {"frame": "1h", "features": [rows]}} — the shape
aster_batch1._tensor_panels reads). Fires for symbols with an
analysis record are stamped with the record's markers and feature
fields; the rest keep the CURE-3 envelope values and fail their
feature gates closed, by the sleeves' own design. The serve-side
half of the cure (the tensor_G4_events bridge into view["extra"])
is desk3/producers.TensorG4Events.

"tensor_daily20" is deliberately NOT written: its rows are the
Aster daily feature pipeline's product (archive
source/backend/tensor_daily_models.py + tensor_state_repair
native/state features), which is not on this box (the Ausar archive
was relocated to GitHub 2026-10-25) and was never an output of the
v698 producer v2 ran. The D20 sleeves stay UNFED by name on that
key — named missing input, never a fabricated rows map.

Day returns ride the runner's own SIP daily bars: v2 read its bar
cache's 1Day bars; v3's equivalent cache is state/warm_bars.json
(desk3/warm.py WarmBars product). The warmer only READS that cache —
one bars source of truth, unchanged.

Registry: producers.register_all registers TensorWarmer (below) as
"tensor_warmer" BEFORE the bundle-file readers, so a bundle built in
a cycle's warm phase is served by the readers in the same cycle.
The warmer contributes no snapshot keys itself ({}); it rebuilds at
most once per WARM_INTERVAL_S (plus one session-roll rebuild when
the persisted bundle's session is older than the cycle's session —
TENSOR-STALE-SESSION-WARMER-20261116, see TensorWarmer) and backs
off FAIL_BACKOFF_S after a failed build, so a down canonical feed
degrades to a named producer_error, not a per-cycle retry storm. Every producer failure
is fail-closed per symbol inside TensorProducer (no signals — never
a substitute feed). gold_diamond is NOT supplied — annotation-only
(Decision #109), no lean source exists.
"""
from __future__ import annotations
import json, os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
TENSOR_SLEEVES = ("tensor_swing", "tensor_red_dip")
WARM_INTERVAL_S = 3600   # rebuild at most once per hour
FAIL_BACKOFF_S = 900     # after a failed build, wait 15 min


class _ProducerCtx:
    """The ctx shape core.tensor_feeds.TensorProducer.extra_for reads:
    .session (YYYY-MM-DD) and .extra (carrying sleeve_state so the
    tensor_swing exit view covers exactly the held symbols)."""

    def __init__(self, session, extra=None):
        self.session = session
        self.extra = extra or {}


def _sleeve_state(root, sleeve_id):
    """{SYM: {"position": {...}}} from the sleeve's own journal — the
    same positions the runner serves the sleeve. {} when the sleeve
    holds nothing."""
    from runtime.journal import positions_from_journal
    jpath = os.path.join(root, "state", sleeve_id, "journal.jsonl")
    out = {}
    for p in positions_from_journal(jpath):
        out[p["symbol"]] = {"position": {
            "qty": p.get("qty"), "entry_px": p.get("avg_price"),
            "entry_date": str(p.get("opened_at") or "")[:10]}}
    return out


def _fetch_daily_from_warm_cache(root):
    """fetch_daily(symbols) -> {sym: [bar dicts]} reading ONLY the
    runner's warm-bars cache (state/warm_bars.json): the "SYM|1Day"
    series, falling back to the bare "SYM" series. {} per symbol
    when the cache lacks it (the producer fails closed per symbol).
    """
    try:
        with open(os.path.join(root, "state", "warm_bars.json")) as fh:
            bars = (json.load(fh) or {}).get("bars") or {}
    except (OSError, ValueError):
        bars = {}

    def fetch_daily(symbols):
        out = {}
        for s in symbols:
            rows = bars.get(f"{s}|1Day") or bars.get(s) or []
            out[s] = [dict(b) for b in rows if isinstance(b, dict)]
        return out

    return fetch_daily


def build_bundle(root, session=None, producer=None, fetch_daily=None):
    """Compute both sleeves' extras via TensorProducer and persist
    the bundle in the cache. Returns the persisted payload."""
    from core.tensor_feeds import TensorProducer
    from runtime.cache import BarCache
    root = os.path.abspath(root)
    cache = BarCache(os.path.join(root, "cache"))
    session = session or datetime.now(ET).date().isoformat()
    if producer is None:
        producer = TensorProducer(
            fetch_daily=fetch_daily or _fetch_daily_from_warm_cache(root),
            memo_path=os.path.join(root, "state",
                                   "tensor_signals_memo.json"))
    sleeves = {}
    for sid in TENSOR_SLEEVES:
        extra = {}
        if sid == "tensor_swing":
            extra = {"sleeve_state": _sleeve_state(root, sid)}
        sleeves[sid] = producer.extra_for(sid, _ProducerCtx(session, extra))
    payload = {"session": session,
               "generated_at": datetime.now(timezone.utc).isoformat(),
               "sleeves": sleeves,
               "fires": [_enrich_fire(f) for f in
                         (sleeves["tensor_swing"].get("tensor_signals")
                          or [])]}
    _apply_native_pass(root, payload,
                       fetch_daily or _fetch_daily_from_warm_cache(root))
    cache.write_tensor_bundle(payload)
    _archive_build(root, payload)
    return payload


def _apply_native_pass(root, payload, fetch_daily):
    """TENSOR-SERVE-SHAPE cure, bundle side (2026-11-12;
    TENSOR-FIRE-PATH.md CURE-3 feature half, CURE-4, CURE-5):
    desk3/tensor_native builds the canonical r19 native product
    over the producer's evaluated universe — per-symbol prepared
    analysis (weekly features + engine markers), the enrollment
    census, 1h native state panels under symbol keys (the shape
    aster_batch1._tensor_panels reads) — and stamps each fire with
    its symbol's markers and feature fields. The pass is fail-soft
    by construction: any failure leaves the base bundle (swing
    channel + CURE-3 envelope) served exactly as before and is
    NAMED on the payload (tensor_native_error / per-symbol census
    reasons and tensor_native_skips), never silent."""
    try:
        from desk3 import tensor_native
        universe = []
        try:
            memo_path = os.path.join(root, "state",
                                     "tensor_signals_memo.json")
            with open(memo_path) as fh:
                memo = json.load(fh)
            if isinstance(memo, dict) and isinstance(memo.get("rows"),
                                                     dict):
                universe = sorted(memo["rows"].keys())
        except (OSError, ValueError):
            universe = []
        # FIX-F4-20261115: the analysis universe is the memo's rows
        # UNION the bundle's own fire symbols. A fire whose symbol is
        # outside the memo universe previously got no analysis record
        # at all, so apply_native_to_fire left its feature cells empty
        # and every variant consumer failed it closed on missing
        # cells — the serving route starved the fire the bundle
        # itself carried. Unioning attempts analysis for every fired
        # symbol; symbols that fail warmup still get no record (the
        # census names them), exactly as before.
        fire_syms = {f["symbol"] for f in payload["fires"]
                     if isinstance(f, dict) and f.get("symbol")}
        universe = sorted(set(universe) | fire_syms)
        if not universe:
            return
        try:
            daily_map = fetch_daily(universe) or {}
        except Exception:
            daily_map = {}
        # The native products are stamped at the bundle's own
        # generated_at (its decision time), never at the pass's
        # wall-clock end: the census receipt discipline
        # (received_at <= bundle generated_at) is what lets the
        # serve-side bridge assess the census in the very cycle the
        # bundle is built, whose producer clock predates the build.
        build_now = datetime.fromisoformat(
            str(payload["generated_at"]).replace("Z", "+00:00"))
        products = tensor_native.build_native_products(
            root, universe, daily_map, build_now)
        payload["tensor_universe"] = universe
        if products["analysis"]:
            payload["tensor_analysis"] = products["analysis"]
        if products["census"]:
            payload["tensor_census"] = products["census"]
        for sym, rows in products["panels"].items():
            payload[sym] = {"frame": "1h", "features": rows}
        if products["analysis"]:
            payload["fires"] = [
                tensor_native.apply_native_to_fire(
                    f, products["analysis"].get(f.get("symbol")))
                if isinstance(f, dict) else f
                for f in payload["fires"]]
        if products["skips"]:
            payload["tensor_native_skips"] = products["skips"]
    except Exception as e:  # named on the payload, never silent
        payload["tensor_native_error"] = f"{type(e).__name__}:{e}"


def _enrich_fire(fire):
    """CURE-3 envelope layer (2026-11-11): the variant families read
    the fire's own facts under different key names than the swing
    engine writes (TENSOR-FIRE-PATH.md Sections 3.1-3.3) — price for
    entry, date / signal_end for bar_date, fired_at / ts for the
    epoch t. Each fire in the bundle's fires channel gains those
    names, derived ONLY from its own values; every original key is
    preserved verbatim and a fire lacking a source value gains
    nothing for that key. The FEATURE fields (markers, native_close,
    depth60, ret60, vol20, dv20, atr_ratio) are deliberately NOT
    derived here: the joint lane's canonical answer (Claude's field
    answer; GrokBot md2, grokbot-inbox:2026-11-11-tensor-fire-md2)
    is that those need a feature producer with a verified canonical
    mapping, never guessed fields. The sleeves' own channel
    (sleeves.tensor_swing.tensor_signals) keeps the engine rows
    untouched; only the fires copies are enriched."""
    if not isinstance(fire, dict):
        return fire
    out = dict(fire)
    if out.get("price") is None and out.get("entry") is not None:
        out["price"] = out["entry"]
    bar_date = out.get("bar_date")
    if bar_date:
        if not out.get("date"):
            out["date"] = bar_date
        if not out.get("signal_end"):
            out["signal_end"] = bar_date
    t = out.get("t")
    if isinstance(t, (int, float)) and t:
        if out.get("ts") is None:
            out["ts"] = t
        if not out.get("fired_at"):
            try:
                out["fired_at"] = datetime.fromtimestamp(
                    t, timezone.utc).isoformat()
            except (OverflowError, OSError, ValueError):
                pass
    return out


def _archive_build(root, payload):
    """D-RUN-1 / CURE-2 (2026-11-11): per-session evidence of the fire
    path's own runs. The live bundle and the signals memo are both
    overwritten in place, which made "one bundle per session, no
    missed, no duplicated" unprovable for past sessions. Every build
    now leaves: a WRITE-ONCE archive copy of the bundle
    (cache/tensor/archive/bundle-<session>.json — the first build of
    a session is the archived one; later same-session rebuilds update
    only the live bundle), a WRITE-ONCE archive of the session's
    signals memo when the memo on disk belongs to this session
    (state/tensor_memo_archive/memo-<session>.json), and one appended
    line in state/tensor_bundle_history.jsonl carrying {session,
    generated_at, symbols_evaluated, fires}. Archiving never breaks a
    build: a failure here leaves the live bundle served and is
    recorded on the history line attempt only."""
    session = payload["session"]
    try:
        arch_dir = os.path.join(root, "cache", "tensor", "archive")
        os.makedirs(arch_dir, exist_ok=True)
        arch_path = os.path.join(arch_dir, f"bundle-{session}.json")
        if not os.path.exists(arch_path):
            with open(arch_path, "w") as fh:
                json.dump(payload, fh)
    except OSError:
        pass
    symbols_evaluated = None
    try:
        memo_path = os.path.join(root, "state", "tensor_signals_memo.json")
        with open(memo_path) as fh:
            memo = json.load(fh)
        if isinstance(memo, dict) and memo.get("session") == session:
            rows = memo.get("rows")
            if isinstance(rows, dict):
                symbols_evaluated = len(rows)
            memo_dir = os.path.join(root, "state", "tensor_memo_archive")
            os.makedirs(memo_dir, exist_ok=True)
            memo_arch = os.path.join(memo_dir, f"memo-{session}.json")
            if not os.path.exists(memo_arch):
                with open(memo_arch, "w") as fh:
                    json.dump(memo, fh)
    except (OSError, ValueError):
        pass
    try:
        hist_path = os.path.join(root, "state",
                                 "tensor_bundle_history.jsonl")
        with open(hist_path, "a") as fh:
            fh.write(json.dumps({
                "session": session,
                "generated_at": payload["generated_at"],
                "symbols_evaluated": symbols_evaluated,
                "fires": len(payload["fires"])}) + "\n")
    except OSError:
        pass


def _bundle_stamp(root, now):
    """(age_s, session) of the persisted bundle per its own stamps,
    or (None, None) when no parseable bundle exists. session is the
    bundle's "session" string, or None for the pre-warmer shape."""
    try:
        with open(os.path.join(root, "cache", "tensor",
                               "bundle.json")) as fh:
            doc = json.load(fh)
        when = datetime.fromisoformat(
            str(doc["generated_at"]).replace("Z", "+00:00"))
    except (OSError, ValueError, KeyError, TypeError):
        return None, None
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    sess = doc.get("session")
    return (now - when).total_seconds(), \
        sess if isinstance(sess, str) and sess else None


def _bundle_age_s(root, now):
    """Age of the persisted bundle per its generated_at stamp, or
    None when no parseable bundle exists."""
    return _bundle_stamp(root, now)[0]


def _builder_takes_session(builder):
    """True when the builder accepts a session keyword (the
    build_bundle shape). Builders with the legacy builder(root)
    shape are called with the root alone, exactly as before."""
    try:
        import inspect
        params = inspect.signature(builder).parameters
    except (TypeError, ValueError):
        return False
    return "session" in params or any(
        p.kind == inspect.Parameter.VAR_KEYWORD
        for p in params.values())


class TensorWarmer:
    """Producer-shaped warmer: (pctx) -> {} always (it contributes
    no snapshot keys; the bundle-file readers serve them). Rebuilds
    the bundle when it is missing, older than WARM_INTERVAL_S, or —
    TENSOR-STALE-SESSION-WARMER-20261116 — carrying a session older
    than the cycle's ET session, regardless of age: the readers
    (desk3/producers.py TensorBundleFile, CURE-1 2026-11-11) refuse
    such a bundle by name (stale_bundle_session:<session>), so an
    age-only trigger left every cycle that started after ET
    midnight, while the bundle was built less than an hour before
    midnight, with no servable bundle at all (proven live Sat
    2026-11-14 05:07-05:31Z and Mon 2026-11-16 05:06Z; see
    BUGLOG_2026-11-16.md). One freshness rule, shared by warmer
    and readers. The build is stamped with the CYCLE's session,
    derived from the producer context's now, never a wall-clock
    date read mid-build. A failed build sets last_error (named in
    producer_errors by the cycle, B3 law) and backs off
    FAIL_BACKOFF_S."""

    def __init__(self, root, builder=None, warm_interval_s=WARM_INTERVAL_S,
                 fail_backoff_s=FAIL_BACKOFF_S):
        self.root = root
        self.builder = builder or build_bundle
        self.warm_interval_s = warm_interval_s
        self.fail_backoff_s = fail_backoff_s
        self.last_error = None
        self._last_attempt = None

    def __call__(self, pctx):
        now = (pctx or {}).get("now") or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        cycle_session = now.astimezone(ET).date().isoformat()
        age, sess = _bundle_stamp(self.root, now)
        # Session-stale is a rebuild trigger on its own: a present
        # session strictly older than the cycle's session is one
        # the readers will refuse, however fresh its stamp is. A
        # sessionless bundle keeps the legacy age-only behaviour
        # (it cannot prove staleness either way — the readers'
        # own rule, mirrored).
        session_stale = sess is not None and sess < cycle_session
        if age is not None and age < self.warm_interval_s \
                and not session_stale:
            self.last_error = None
            return {}
        if self._last_attempt is not None and \
                (now - self._last_attempt).total_seconds() < \
                self.fail_backoff_s:
            return {}
        self._last_attempt = now
        try:
            if _builder_takes_session(self.builder):
                self.builder(self.root, session=cycle_session)
            else:
                self.builder(self.root)
        except Exception as e:  # fail closed: readers keep serving
            # the previous bundle or UNFED-by-name when none exists
            self.last_error = f"{type(e).__name__}:{e}"
            return {}
        self.last_error = None
        return {}


if __name__ == "__main__":
    import sys
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    payload = build_bundle(root)
    print(json.dumps({
        "session": payload["session"],
        "tensor_swing_signals":
            len(payload["sleeves"]["tensor_swing"]["tensor_signals"]),
        "tensor_exit_symbols":
            len(payload["sleeves"]["tensor_swing"]["tensor_exit"]),
        "tensor_red_dip_signals":
            len(payload["sleeves"]["tensor_red_dip"]["tensor_signals"]),
        "qqq_day_return":
            payload["sleeves"]["tensor_red_dip"]["qqq_day_return"],
        "day_returns":
            len(payload["sleeves"]["tensor_red_dip"]["day_returns"]),
        "fires": len(payload["fires"]),
    }, indent=1))
    sys.exit(0)
