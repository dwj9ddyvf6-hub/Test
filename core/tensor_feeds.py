"""Tensor signals producer (2026-10-15, R2 wiring).

THE missing producer: live dispatch never populated
context.extra["tensor_signals"], so tensor_swing / tensor_red_dip
evaluated on empty signals every tick (fail-closed inert). This
producer follows the Wave-1B producer pattern (core/bars_universe.py):
injectable fetchers for tests, production callables in
tools/run_live.py, per-session caching, every failure fail-closed
(no signals for that symbol — never a substitute feed).

Signal production mirrors the old desk's canonical Tensor path
(scan_and_trade.detect_signals + swing_watch_13, Decision #108):
  * bars come ONLY through core.data.tensor_bars — the single
    Tensor door over the vendored canonical feed (Decision #108);
  * the pinned v698 engine (vendor tensor_exact) evaluates the
    series with swing_lookback=4 (old EXACT_SWING_LOOKBACK: the last
    5 closed bars, point-in-time each);
  * only CONFIRMED swings map to signals, newest per symbol;
  * the 200-bar production gate applies (SPEC S5: below it the
    warm-up is not production-equivalent — symbol skipped);
  * signal-age policy (old desk, 2026-09-28): a swing whose
    confirmationAgeBars exceeds 3 is stale — never chased;
  * "extended" is the old desk's extension_vs_high_pct > 0 test
    (last close at/above the 20-bar high = extended context);
    tensor_swing drops extended candidates itself — the producer
    only labels, exactly as the old signal carried the field.
Rows carry the shape both sleeves consume: {symbol, decision,
confidence, phenotype, regime, extended, bar_date, entry, stop,
target}. decision is "TRADE" for a confirmed in-age swing (the
lean dispatch has no gate layer; sleeve-internal rules remain the
strategy). entry/stop/target are the old desk's detect_signals
conversion of the same engine decision, carried verbatim: entry =
the close of the canonical bar at the swing event's timestamp,
stop = the swing's own invalidation level, target = the swing's
own target. A swing event whose timestamp has no canonical bar is
not a signal (the old mapping skips it identically).

tensor_red_dip's other feeds ride along from the same producer:
qqq_day_return / day_returns (latest daily close vs the prior
close, via the injected daily fetcher — the desk's SIP daily door)
and nyse_holidays (core.data calendar). gold_diamond is NOT
supplied: no lean source exists for the stamp, and it is
annotation-only (Decision #109) — the sleeve tolerates its absence.

Exit view (M-TS1 cure, 2026-10-15): the old runner's
manage_positions evaluated two rules over held Tensor positions —
a bearish engine trigger (the pinned engine re-run at
swing_lookback=EXIT_LOOKBACK_BARS on the canonical series) and a
20-closed-bar time stop counted on the same series. The producer
supplies both inputs for tensor_swing as extra["tensor_exit"]:
{SYM: {bearish_exit, bearish_reason, last_close, bar_ts}} —
bearish_exit_trigger below is the old function ported verbatim;
the time-stop count itself is the sleeve's (it owns the position
records). Fail-closed per symbol, exactly as the old runner
skipped a symbol whose bars were unavailable.

AUDIT-20261018-CURE2: the exit view is computed ONLY for symbols
tensor_swing actually holds. The pre-cure producer re-ran the
exit engine over the full 41-name universe on every pass (the
desk is process-per-pass, so the in-process cache never saved
it) even when the sleeve held nothing — the sleeve only ever
reads rows for its sleeve_state positions. Holdings resolve
from the explicit held argument, else the producer's injected
state_store (the same sleeve_state the dispatcher serves the
sleeve), else fail closed: no holdings source, no evaluation.
"""
import hashlib
import json
import pathlib
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
TENSOR_SLEEVES = ("tensor_swing", "tensor_red_dip")
MIN_BARS = 200            # SPEC S5 production gate (old R-015)
SWING_LOOKBACK = 4        # old EXACT_SWING_LOOKBACK (last 5 closed bars)
MAX_SIGNAL_AGE_BARS = 3   # old desk signal-age policy (2026-09-28)
EXIT_LOOKBACK_BARS = 1    # old EXIT_LOOKBACK_BARS (bearish exit: last 2 closed bars)
EXIT_MIN_BARS = 10        # old manage_positions: fewer bars -> no exit evaluation
EXIT_BAR_WINDOW = 300     # bar stamps supplied per symbol (>> the 20-bar horizon)


def _engine():
    v = pathlib.Path(__file__).resolve().parent.parent / "vendor"
    if str(v) not in sys.path:
        sys.path.insert(0, str(v))
    import tensor_exact
    return tensor_exact


def newest_diag(res):
    """The engine result's NEWEST diagnostics row in the
    latest_diag shape (slow/fast state + vote split as of the
    newest bar), or None when the engine printed no
    diagnostics. Pure: reads the engine's OUTPUT only
    (Decision #108 — the engine itself is untouched).

    GESTALT G4 (2026-10-17): signals_from_engine attaches this
    to a confirmed-swing row, but the tensor_timeframes item
    needs the snapshot for EVERY evaluated name — the producer
    records it in the memo even when no swing confirms (on
    2026-10-17 all 41 basket rows were null and the item could
    never fire)."""
    diags = {d.get("timestamp"): d
             for d in (res.get("diagnostics") or [])}
    keys = [k for k in diags if k is not None]
    if not keys:
        return None
    lts = max(keys)
    latest = diags[lts] or {}
    return {"t": lts,
            "bar_date": datetime.fromtimestamp(
                int(lts), tz=ET).date().isoformat()
            if lts is not None else None,
            "slow": latest.get("slowState"),
            "fast": latest.get("fastState"),
            "bull_votes": latest.get("bullishVotes"),
            "bear_votes": latest.get("bearishVotes")}


def signals_from_engine(symbol, bars, res):
    """Pure mapping: engine result -> the newest in-age confirmed
    swing as a tensor_signals row, or None. Mirrors the old desk's
    detect_signals field mapping (confirmed only; votes from the
    diagnostics row at the swing's timestamp)."""
    diags = {d.get("timestamp"): d for d in (res.get("diagnostics") or [])}
    by_ts = {b["t"]: b for b in bars or []}
    best = None
    for ev in res.get("swings") or []:
        s = ev.get("swing") or {}
        if not s.get("confirmed"):
            continue
        age = s.get("confirmationAgeBars")
        if age is not None and float(age) > MAX_SIGNAL_AGE_BARS:
            continue  # stale swing: never chase (old age policy)
        src = by_ts.get(ev.get("timestamp"))
        if src is None:
            continue  # no canonical bar at the swing's timestamp:
            # not a signal (old detect_signals skips it identically)
        d = diags.get(ev.get("timestamp"), {})
        row = {
            "symbol": str(symbol).upper(),
            "decision": "TRADE",
            "confidence": int(s.get("score", 0) or 0),
            "phenotype": s.get("phenotype"),
            "regime": ev.get("regime"),
            "bar_date": None,
            "t": ev.get("timestamp"),
            "bull_votes": d.get("bullishVotes"),
            "bear_votes": d.get("bearishVotes"),
            # The old desk's conversion (scan_and_trade.detect_signals):
            # entry = close of the canonical bar at the swing's
            # timestamp; stop/target = the swing decision's own levels.
            "entry": float(src["c"]),
            "stop": s.get("invalidation"),
            "target": s.get("target"),
            "_age": float(age) if age is not None else None,
        }
        if best is None or (row["t"] or 0) >= (best["t"] or 0):
            best = row
    if best is None:
        return None
    if best["t"] is not None:
        best["bar_date"] = datetime.fromtimestamp(
            int(best["t"]), tz=ET).date().isoformat()
    # Stage 5 (2026-10-16): the consideration record's
    # tensor_timeframes item reads the engine's own NEWEST
    # diagnostics row — the slow/fast state machine's state and
    # the vote split as of the newest bar — attached here, desk
    # code reading the engine's OUTPUT (the engine itself is
    # untouched, Decision #108; additive field, the "extended"
    # precedent). Absent when the engine printed no diagnostics.
    _nd = newest_diag(res)
    if _nd is not None:
        best["latest_diag"] = _nd
    # extension label: last close at/above the 20-bar high (old desk)
    try:
        hi20 = max(float(b["h"]) for b in bars[-20:])
        best["extended"] = bool(hi20 > 0 and float(bars[-1]["c"]) >= hi20)
    except Exception:
        best["extended"] = False
    best.pop("_age", None)
    return best


def bearish_exit_trigger(res):
    """Pure port of the old runner's bearish_exit_trigger
    (alpaca-swing-desk scan_and_trade.py), verbatim logic: does the
    exact-engine result demand a bearish exit? Evaluates the last two
    closed bars' swing events. EXIT if on either bar ANY of:
      - swings[].swing.bearishConflict is True
      - diagnostics[].bearishVotes > diagnostics[].bullishVotes
      - "consensus-sell" in diagnostics[].enrichmentIds (bearish
        5-of-7 vote)

    NOTE (old desk, Decision #12 rollback, 2026-09-30): the
    red-diamond-in-blue clause was REMOVED after measurement showed
    it destroyed -127bp per fired trade; it is NOT reintroduced
    here. Returns (trigger: bool, reason: str|None). Never raises.
    """
    try:
        swings = res.get("swings") or []
        diags = {d.get("timestamp"): d for d in (res.get("diagnostics") or [])}
        for ev in swings[-2:]:
            s = ev.get("swing") or {}
            ts = ev.get("timestamp")
            if s.get("bearishConflict"):
                return True, "bearish conflict on bar %s" % ts
            d = diags.get(ts) or {}
            bull = d.get("bullishVotes")
            bear = d.get("bearishVotes")
            if (bull is not None and bear is not None
                    and bear > bull):
                return True, ("bear votes %d > bull votes %d on bar %s"
                              % (bear, bull, ts))
            if "consensus-sell" in (d.get("enrichmentIds") or []):
                return True, "consensus-sell (bearish 5-of-7) on bar %s" % ts
    except Exception:
        pass
    return False, None


def _series_key(symbol, bars):
    """Content key for one symbol's canonical series. The engine
    is a deterministic function of the bars and the mapping is
    pure, so identical series bytes => identical signal row
    (P5 cross-pass memo, 2026-10-15)."""
    blob = json.dumps([symbol, bars], sort_keys=True,
                      separators=(",", ":"), default=str)
    return hashlib.sha256(blob.encode()).hexdigest()


def _day_return(bars):
    """Latest close vs prior close (fraction), or None."""
    try:
        closes = [float(b["c"]) for b in bars if b.get("c") is not None]
        if len(closes) < 2 or closes[-2] == 0:
            return None
        return closes[-1] / closes[-2] - 1.0
    except Exception:
        return None


class TensorProducer:
    """fetch_canonical(symbol)->[bars] (default: core.data's single
    Tensor door), run_engine(symbol, bars)->engine dict (default:
    the pinned v698 wrapper), fetch_daily(symbols)->{sym:[bars]}
    for the red-dip day returns. All injectable for tests."""

    def __init__(self, universes=None, fetch_canonical=None,
                 run_engine=None, fetch_daily=None, run_engine_exit=None,
                 memo_path=None, state_store=None):
        if universes is None:
            from core.bars_universe import load_universes
            universes = load_universes()
        # Tensor's trading universe ONLY (Decision #38): the 41-name basket.
        self.universe = list(universes.get("basket_41") or [])
        self.fetch_canonical = fetch_canonical
        self.run_engine = run_engine
        self.fetch_daily = fetch_daily
        self.run_engine_exit = run_engine_exit
        # P5 (2026-10-15): optional cross-pass memo of evaluated
        # signals, keyed by canonical-series content. The desk is
        # process-per-pass, so the in-process cache alone re-pays
        # the full engine cost (~2.8s/symbol x 41) on EVERY pass
        # even when no symbol's series changed; a series changes
        # only on a new hourly close or a vendor revision, and
        # either changes the key and forces a real evaluation.
        self.memo_path = (pathlib.Path(memo_path)
                          if memo_path is not None else None)
        # AUDIT-20261018-CURE2: the sleeve-state store the exit
        # view reads tensor_swing's holdings from when the caller
        # does not pass them explicitly (the BarsUniverseProducer
        # ._held pattern; wired in tools/run_live). None in tests
        # that pass held= explicitly.
        self.state_store = state_store
        self._sig_cache = {}    # session -> [rows]
        self._ret_cache = {}    # session -> (qqq_ret, {sym: ret})
        self._bars_cache = {}   # session -> {sym: bars|None}
        self._exit_cache = {}   # (session, held tuple) -> {sym: row}

    def _canonical(self, symbol):
        if self.fetch_canonical is not None:
            return self.fetch_canonical(symbol)
        from core.data import tensor_bars
        return tensor_bars(symbol)

    def _run(self, symbol, bars):
        if self.run_engine is not None:
            return self.run_engine(symbol, bars)
        return _engine().exact_swing_signal(
            symbol, bars, swing_lookback=SWING_LOOKBACK)

    def _run_exit(self, symbol, bars):
        if self.run_engine_exit is not None:
            return self.run_engine_exit(symbol, bars)
        if self.run_engine is not None:
            return self.run_engine(symbol, bars)
        return _engine().exact_swing_signal(
            symbol, bars, swing_lookback=EXIT_LOOKBACK_BARS)

    def _bars_for(self, session, sym):
        """Canonical bars fetched at most once per symbol per session;
        the entry scan and the exit view share the one fetch (single
        Tensor door — the same series serves both, as on the old
        desk). A failed fetch caches None: fail closed, no retry
        storm within the session."""
        cache = self._bars_cache.setdefault(session, {})
        if sym not in cache:
            try:
                cache[sym] = self._canonical(sym)
            except Exception:
                cache[sym] = None
        return cache[sym]

    def _load_memo(self, session):
        """{sym: {"key":..., "row":...}} for THIS session, or
        None when no memo is configured; {} on any read problem
        (a corrupt memo must fail soft to plain evaluation)."""
        if self.memo_path is None:
            return None
        try:
            data = json.loads(self.memo_path.read_text())
            if not isinstance(data, dict) or data.get("session") != session:
                return {}
            rows = data.get("rows")
            return rows if isinstance(rows, dict) else {}
        except Exception:
            return {}

    def _save_memo(self, session, memo):
        if self.memo_path is None:
            return
        try:
            self.memo_path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.memo_path.with_suffix(".tmp")
            tmp.write_text(json.dumps({"session": session, "rows": memo}))
            tmp.replace(self.memo_path)
        except Exception:
            pass  # memo is an optimization; never break the pass

    def signals(self, session):
        if session in self._sig_cache:
            return self._sig_cache[session]
        memo = self._load_memo(session)
        dirty = False
        rows = []
        for sym in self.universe:
            row = None
            try:
                bars = self._bars_for(session, sym)
                if bars and len(bars) >= MIN_BARS:
                    # production gate passed (short/absent series
                    # are skipped below, never approximated)
                    key = _series_key(sym, bars)
                    hit = (memo or {}).get(sym)
                    if isinstance(hit, dict) \
                            and hit.get("key") == key \
                            and "diag" in hit:
                        row = hit.get("row")
                    else:
                        # GESTALT G4: a memo entry written
                        # before the diagnostics cure (matching
                        # key, no "diag") re-evaluates ONCE —
                        # the engine is deterministic on the
                        # same series, so the row is unchanged
                        # and the entry gains its snapshot.
                        res = self._run(sym, bars)
                        row = signals_from_engine(sym, bars, res)
                        if memo is not None:
                            memo[sym] = {
                                "key": key, "row": row,
                                "diag": newest_diag(res)}
                            dirty = True
            except Exception:
                # feed/engine failure: fail closed per symbol, and
                # the failed symbol is NEVER memoized (it retries
                # next pass, exactly as without the memo)
                row = None
            if row is not None:
                rows.append(row)
        if dirty:
            self._save_memo(session, memo)
        self._sig_cache[session] = rows
        return rows

    def _held_from_state_store(self):
        """tensor_swing's held symbols from the injected state
        store — the same sleeve_state positions the dispatcher
        serves the sleeve itself (build_extra), so the exit view
        covers exactly the symbols the sleeve will look up.
        [] when no store is wired or the store is unreadable
        (fail closed: evaluate nothing)."""
        if self.state_store is None:
            return []
        try:
            ss = self.state_store.get("tensor_swing").get(
                "sleeve_state") or {}
        except Exception:
            return []
        return [str(s).upper() for s, e in ss.items()
                if isinstance(e, dict) and e.get("position")]

    def exit_view(self, session, held=None):
        """{SYM: exit facts} for tensor_swing's held positions
        (M-TS1): the old runner's manage_positions inputs, computed
        once per (session, held set) over the same canonical series
        the entry scan consumed — the bearish-exit trigger (pinned
        engine at EXIT_LOOKBACK_BARS + bearish_exit_trigger), the
        last canonical close (the sleeve's close-evaluated target
        test), and the bar stamps the 20-bar time stop counts on.
        Fail-closed per symbol: fewer than EXIT_MIN_BARS bars or any
        failure -> the symbol is ABSENT and the sleeve evaluates
        nothing for it (the old runner skipped such symbols too;
        the broker disaster stop is unaffected).

        AUDIT-20261018-CURE2: ONLY held symbols are evaluated.
        `held` resolves from the explicit argument, else the
        injected state_store, else nothing is evaluated — the
        pre-cure loop over the full 41-name universe on every
        process-per-pass tick evaluated dozens of unheld symbols
        whose rows no consumer ever read."""
        if held is None:
            held = self._held_from_state_store()
        targets = list(dict.fromkeys(
            str(s).upper() for s in (held or []) if s))
        cache_key = (session, tuple(targets))
        if cache_key in self._exit_cache:
            return self._exit_cache[cache_key]
        view = {}
        for sym in targets:
            try:
                bars = self._bars_for(session, sym)
                if not bars or len(bars) < EXIT_MIN_BARS:
                    continue
                trig, reason = bearish_exit_trigger(
                    self._run_exit(sym, bars))
                view[sym] = {
                    "bearish_exit": bool(trig),
                    "bearish_reason": reason,
                    "last_close": float(bars[-1]["c"]),
                    "bar_ts": [b["t"] for b in bars[-EXIT_BAR_WINDOW:]],
                }
            except Exception:
                continue  # fail closed per symbol
        self._exit_cache[cache_key] = view
        return view

    def _returns(self, ctx):
        if ctx.session in self._ret_cache:
            return self._ret_cache[ctx.session]
        qqq_ret, day_rets = None, {}
        if self.fetch_daily is not None:
            try:
                dmap = self.fetch_daily(["QQQ"] + self.universe) or {}
            except Exception:
                dmap = {}
            qqq_ret = _day_return(dmap.get("QQQ") or [])
            for sym in self.universe:
                r = _day_return(dmap.get(sym) or [])
                if r is not None:
                    day_rets[sym] = r
        self._ret_cache[ctx.session] = (qqq_ret, day_rets)
        return qqq_ret, day_rets

    def extra_for(self, sleeve_id, ctx):
        if sleeve_id not in TENSOR_SLEEVES:
            return {}
        extra = {"tensor_signals": self.signals(ctx.session)}
        if sleeve_id == "tensor_swing":
            # AUDIT-20261018-CURE2: when the caller's context
            # carries sleeve_state, its positions ARE the holdings
            # (the harness/dispatch shape); otherwise exit_view
            # resolves holdings from the injected state_store.
            ctx_extra = getattr(ctx, "extra", None) or {}
            held = None
            if isinstance(ctx_extra.get("sleeve_state"), dict):
                held = [str(s).upper()
                        for s, e in ctx_extra["sleeve_state"].items()
                        if isinstance(e, dict) and e.get("position")]
            extra["tensor_exit"] = self.exit_view(ctx.session,
                                                  held=held)
        if sleeve_id == "tensor_red_dip":
            from core.data import nyse_holidays
            try:
                year = int(str(ctx.session)[:4])
            except ValueError:
                year = datetime.now(tz=ET).year
            extra["nyse_holidays"] = sorted(
                d.isoformat() for d in nyse_holidays(year))
            qqq_ret, day_rets = self._returns(ctx)
            extra["qqq_day_return"] = qqq_ret
            extra["day_returns"] = day_rets
        return extra
