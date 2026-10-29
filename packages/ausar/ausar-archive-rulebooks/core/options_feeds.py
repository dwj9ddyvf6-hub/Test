"""Wave-2 options package producer (2026-10-15).

ONE options data door for the seven Wave-2 sleeves, built on the
Alpaca options market-data conventions in the desk's records:
contracts under GET /v2/options/contracts, quotes/snapshots under
/v1beta1/options/... with feed=indicative (see AGENTS.md Alpaca
options quirks). Production fetchers live in tools/run_live.py; every
fetcher here is injectable for tests.

SCOPE per sleeve (universes/selection from the ported specs ONLY):

  iron_condor   WIRED — chains+quotes for its CONFIG WATCHLIST
                (13 names in the sleeve itself), current IV by the
                sleeve docstring's own definition (BS inversion of
                the nearest 30-45 DTE ATM call mid, using the sleeve's
                own implied_vol), IV history persisted in sleeve
                state (one observation per session, appended AFTER
                evaluation via the dispatch stamp_state writer —
                the sleeve's rank reads prior observations only, so
                the series stays causal), earnings distance from the
                desk earnings calendar, VIX from the ^VIX daily door.
  qqq_put_ladder WIRED — QQQ put chain quotes (symbol/expiration/
                strike/delta/bid/ask) for expirations 0-52 DTE, spot
                + closes from Alpaca SIP daily bars, buying_power
                from the broker account (options_buying_power),
                layers/week_opened from the sleeve's persisted state
                (the writer is core.dispatch's ladder sync on fills).
                posture: the old ladder read it from an external
                "brain" plan ((plan.brain.level) in
                aurelia_ladder_broker.py) that has no lean-desk
                source — supplied as "unknown", the old default when
                the plan was absent. Effect, exactly as ported: new
                layers stay blocked (posture_unknown) while layer
                management (closes / challenged rolls) still
                evaluates. equity_pending: the lean desk has no
                equity-ticket system; False is the truthful value
                (the ported decide() ignores it for the add test).
  free_opt_tail WIRED-PARTIAL — underlying_return for SPY (the old
                monitor underlying: aurelia_free_options.run() built
                its monitor quote from the SPY indicative snapshot),
                from SIP daily bars (today's close vs prior close),
                plus the supply constructor's option `quote`
                (FREEOPT-COMPLETE, below).
  free_opt_wheel WIRED — cash from the broker account, plus the
                constructor's `quote` (carrying its strike) when the
                cash covers that strike's assignment.
  free_opt_release WIRED-PARTIAL — events from the desk's verified
                macro calendar (desk/macro_events.json: FOMC/CPI
                dates verified against federalreserve.gov / bls.gov
                per the file's own note), mapped to the sleeve's
                {session, verified} shape, plus the constructor's
                straddle `package` on a verified-event session.
  free_opt_own_iv / free_opt_pair — the constructor's `package`
                (below): own_iv's straddle assembles only when the
                design's own entry gate computes true (causal
                realized vol over indicative IV by 2 points); the
                pair's legs attach only when the verbatim frozen
                hedge's own signal field is true, direction from
                its z sign.
  saty_day      WIRED (2026-10-21) — SPY calls + puts over a
                0-7 DTE fetch window (the sleeve filters to its
                own 2-4 DTE law and the ATM strike), plus the
                fresh-quotes door for its entry staleness gate
                (the snapshot door carries no quote timestamp).
  saty_sol      WIRED (2026-10-21) — SPY calls + puts over the
                same 0-7 DTE fetch window (the sleeve applies
                Sol's 2-4 calendar-DTE selection law), plus the
                fresh-quotes door for its contract validation and
                ask-based sizing.
  saty_sol_0dte WIRED (2026-10-22) — the 0DTE variant of
                saty_sol (User's ruling): same chains and
                fresh-quotes doors; the sleeve applies the same
                selection law with SAME-DAY expiry only.

RULEBOOK RECOVERED (EA2a, 2026-10-15, User's 10:44 order): the
rulebook was found in the Ausar archive payload on GitHub —
dwj9ddyvf6-hub/Agentic-Trading-Desk branch aurelia-paper-desk,
ausar-archive/ausar-receiver/original-payload/desk-source/
strategies/r19/options_rules.json (sha256 75bead6b…) — and ported
verbatim to config/options_rules.json. Its verdict on the five
free_opt_* parent books is the source's own: every one is
monitor_only=true, initial_capital=0, with a named input_blocker
(OPT_OWN_IV_RESIDUAL: own_contract_IV_history_and_independent_
out_of_sample_payout_model_required; OPT_RELEASE_CONVEXITY:
causal_announcement_phase_and_actual_contract_expected_payout_
inputs_required; OPT_STATIONARY_PAIR: clock_corrected_point_in_
time_pair_selection_and_priced_option_residual_required;
OPT_TAIL_STATE: separate_frozen_left_tail_and_both_tail_
predictors_and_own_IV_increment_required; OPT_WHEEL_LIFECYCLE:
American_assignment_and_physical_share_ownership_cycle_adapter_
required). The source engine enforces the same verdict
(r19_options.evaluate: a monitor_only book returns blocked;
option_inventory.assess_all skips monitor books; no package is
ever constructed for them — packages exist only for the 30 funded
trading books, none of which is a lean sleeve). This producer
therefore supplies each free_opt sleeve its rulebook book row
("rulebook_book") plus every sourceable input the source itself
supplied: the pair's frozen hedge (option_inputs._hedge, ported
verbatim below), the tail's underlying return, the wheel's cash,
the release events. The sleeves keep receiving NO fabricated
quote/package legs and fail closed inside their own ported rules —
now on the recovered source's evidence, not on a fence.

ACTIVATED (User's ruling, 2026-10-16, the X-3 item): the five
free_opt_* parent books are ACTIVE on this desk. The recovered
rulebook above stays the verbatim source record (the config is
never rewritten); the desk's book construction (_rulebook_book)
presents each of the five as an active book whose capital is the
source design's own FREE_OPTIONS package pool — aurelia_common
BUDGETS["FREE_OPTIONS"] = 100_000, the pool every port doc and
sleeve BUDGET_USD names — with sizing as the source specified it
(one contract per order/leg; the sleeves emit qty_hint=1). What
activation does NOT do: the source design contains no automated
contract-selection or package constructor for these five books
(evaluate() received quote/package as arguments; run() synthesized
only the SPY monitor quote and discarded the contract symbol), so
quote/package remain external inputs on the documented ctx
contract, supplied exactly as the source supplied them, and the
books fail closed in their own ported rules until a documented
input arrives. free_opt_parity is not a parent book and is not
activated: MODEL_TEST_ONLY by its own source design, forever.

SUPPLY CONSTRUCTOR (FREEOPT-COMPLETE, User's ruling, 2026-10-16):
the constructor the source design never contained is now built in
this producer (_freeopt_supply), on the desk's canonical doors —
contracts under /v2/options/contracts, latest quotes under
/v1beta1/options/quotes/latest (tools/run_live.alpaca_option_quotes,
the freshness-gate shape this family was always specified against),
snapshots under /v1beta1/options/snapshots, SIP daily bars for spot
and the session calendar. The design names no strike or expiry;
the constructor's uniform conventions are: underlying SPY (the
family's monitor underlying; the pair is SPY+QQQ, the frozen
hedge's own pair); expiry = the nearest listed expiry STRICTLY
AFTER the session whose selected strike carries two-sided quotes
(a same-day expiry cannot serve any of the books' designed holds;
if the nearest expiry is unquotable the book gets nothing — the
constructor never walks the chain shopping for a trade); strike =
the listed strike nearest the SIP spot (ATM — the ported spec's
own word for the straddle books, and the one selection that
carries no moneyness view for the others). Book gates are the
design's own: own_iv's package assembles only when a causal
realized-volatility forecast exceeds indicative IV by 2 points —
computed here as the trailing 20 sessions' realized vol from SIP
closes EXCLUDING the last (forming) bar, the causality convention
this producer's frozen hedge already uses, against indicative IV
inverted from the selected legs' snapshot mids by the desk's own
BS definition (the condor's implied_vol); the pair's legs attach
only when the frozen hedge's own signal field (|z| > 2) is true,
long the cheap underlying via a call and short the rich one via a
put (z sign decides), the shapes the desk's own drives carry;
release's straddle assembles only on a verified-event session;
the wheel's quote is fetched only when the broker cash covers the
selected strike's assignment (the sleeve re-checks it); the
tail's quote is fetched when the day return is at the sleeve's
own -3% threshold. Every piece fails closed independently: an
unassemblable input is ABSENT, never approximated. While a book
holds a position the producer also supplies its exit inputs —
snapshot quotes for the held contracts and the SPY session
calendar — and the sleeves evaluate their designed exits in
signal() (the desk's exit-evaluation home), under the source
manage_exits rule that an exit fires only with a two-sided quote
for the held contract.

FAIL-CLOSED: any fetch failure yields absent keys (never guessed
values); a snapshot without a two-sided quote contributes no quote;
IV inversion failure yields no IV (the sleeve's cold-start / rank
gates then block, as ported).

XT-3 (2026-10-16): the same door now also serves the directional
options sleeves whose entries had no producer at all — bilbo_options,
capitulation_options, ema_vwap_options, rsi_meanrev_options,
spx_premium, vix_hedge, leaps_momentum, fear_premium — via
_simple_chains_quotes (one underlying, one kind, one DTE window; the
chain/quotes shapes every one of those sleeves consumes) plus quotes
for every OCC recorded on the sleeve's held positions, so exit rules
evaluate on live marks. Windows/kinds are each sleeve's own ported
DTE law. Their non-options inputs (bars_5m, earnings, weekly_bars,
vix_closes, the momentum book) are produced by BarsUniverseProducer.

NOTE (reported, not redesigned): free_opt_tail's put test is the
substring check `"P" in quote.symbol` — the equity symbol "SPY"
itself contains "P", so on the old desk the SPY monitor quote could
satisfy the put test. Per the wave brief this weakness is reported,
not redesigned; it is also why this producer never supplies an
equity symbol as an option quote.
"""
import math
import re
from datetime import date, timedelta

_OCC = re.compile(r"^([A-Z]{1,6})(\d{6})([CP])(\d{8})$")

WAVE2_SLEEVES = ("free_opt_own_iv", "free_opt_pair", "free_opt_release",
                 "free_opt_tail", "free_opt_wheel", "qqq_put_ladder",
                 "iron_condor")
FREE_OPT_SLEEVES = WAVE2_SLEEVES[:5]

# The old free-options monitor underlying (aurelia_free_options.run()
# built its monitor quote from the SPY indicative snapshot).
TAIL_UNDERLYING = "SPY"
LADDER_UNDERLYING = "QQQ"
LADDER_DTE_MAX = 52          # sleeve DTE_HI; quotes beyond it are useless
CONDOR_DTE_LO, CONDOR_DTE_HI = 30, 45   # sleeve DTE_MIN/DTE_MAX


def parse_occ(symbol):
    m = _OCC.match(str(symbol or ""))
    if not m:
        return None
    yy, mm, dd = int(m.group(2)[:2]), int(m.group(2)[2:4]), int(m.group(2)[4:6])
    return {"root": m.group(1),
            "expiration": date(2000 + yy, mm, dd).isoformat(),
            "cp": m.group(3), "strike": int(m.group(4)) / 1000.0}


def _f(v):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if math.isfinite(f) else None


class OptionsProducer:
    """Injectable fetchers (production callables in tools/run_live.py):

      fetch_contracts(underlying, kind, exp_gte, exp_lte) -> [contracts]
        contract: {"symbol","strike","expiration","type","tradable"}
      fetch_snapshots(symbols) -> {OCC: snapshot}
        snapshot: {"bid","ask","delta"} (any field may be absent)
      fetch_quotes(symbols) -> {OCC: quote}
        quote: {"symbol","bp","ap","t","received_at"} — the
        v1beta1 latest-quotes door (the free_opt freshness shape)
      fetch_daily(symbols) -> {sym: [daily bars]}   (Alpaca SIP door)
      fetch_vix() -> (close, prev, asof, source) | None
      fetch_account() -> account dict | None (broker truth)
      earnings_doc / macro_doc: the desk calendar documents (dicts)
      state_store: SleeveStateStore for IV history + ladder layers.
    """

    def __init__(self, fetch_contracts=None, fetch_snapshots=None,
                 fetch_daily=None, fetch_vix=None, fetch_account=None,
                 earnings_doc=None, macro_doc=None, state_store=None,
                 fetch_books=None, fetch_quotes=None):
        self.fetch_contracts = fetch_contracts
        self.fetch_snapshots = fetch_snapshots
        self.fetch_quotes = fetch_quotes
        self.fetch_daily = fetch_daily
        self.fetch_vix = fetch_vix
        self.fetch_account = fetch_account
        self.earnings_doc = earnings_doc
        self.macro_doc = macro_doc
        self.state_store = state_store
        self.fetch_books = fetch_books
        self._books_cache = None
        self._basket_cache = None
        self._simple_cache = {}   # (session, sym, kind, lo, hi) -> (chain, quotes)
        self._fo_chain_cache = {} # (session, sym, kind) -> [contracts]
        self._chain_cache = {}    # (session, sym) -> (chains, quotes)
        self._ladder_cache = {}   # session -> quotes list
        self._daily_cache = {}    # session -> {sym: bars}
        self._acct_cache = {}     # session -> account | None
        self._vix_cache = {}      # session -> float | None
        # SCAN-TICK-OVERRUN (2026-10-23): the shared per-pass
        # market-data snapshot. One producer instance serves one
        # dispatcher assembly (one pass), so these session-keyed
        # caches ARE the per-tick snapshot the measurement drive
        # proved missing (EVIDENCE: fetch = 84.2% of a 1460.4s
        # roster sum against a 1320s watchdog budget; the same
        # contracts / snapshots / fresh quotes were refetched per
        # sleeve and per DTE window). Contracts are cached as an
        # interval union per (session, sym, kind): every expiry
        # interval is fetched at most once and a request is served
        # from the union, fetching only its uncovered sub-intervals.
        # Snapshots and fresh quotes are cached per (session, OCC)
        # — successful rows only, so an absent/failed input stays
        # absent for that call and retryable for the next, exactly
        # the old fail-closed semantics. Served values are the
        # fetched values untouched: sleeves receive byte-identical
        # inputs, fetched once.
        self._contracts_union = {}  # (session, sym, kind) -> {"intervals": [(gte, lte)], "rows": {occ: row}}
        self._snapshot_cache = {}   # (session, occ) -> snapshot dict
        self._fresh_cache = {}      # (session, occ) -> raw quote dict

    # -- shared doors ----------------------------------------------------
    def _daily(self, symbols, ctx):
        cache = self._daily_cache.setdefault(ctx.session, {})
        missing = [s for s in symbols if s not in cache]
        if missing and self.fetch_daily is not None:
            try:
                fetched = self.fetch_daily(missing) or {}
            except Exception:
                fetched = {}
            for s in missing:
                cache[s] = fetched.get(s) or []
        return {s: cache[s] for s in symbols if cache.get(s)}

    def _account(self, ctx):
        if ctx.session not in self._acct_cache:
            acct = None
            if self.fetch_account is not None:
                try:
                    acct = self.fetch_account()
                except Exception:
                    acct = None
            self._acct_cache[ctx.session] = acct if isinstance(acct, dict) else None
        return self._acct_cache[ctx.session]

    def _vix_close(self, ctx):
        if ctx.session not in self._vix_cache:
            v = None
            if self.fetch_vix is not None:
                try:
                    row = self.fetch_vix()
                    if row:
                        v = _f(row[0])
                except Exception:
                    v = None
            self._vix_cache[ctx.session] = v
        return self._vix_cache[ctx.session]

    # -- SCAN-TICK-OVERRUN shared snapshot doors --------------------------
    def _contracts(self, sym, kind, gte, lte, session):
        """Contracts for (sym, kind, [gte, lte]) served from the
        shared per-session interval union: each expiry interval is
        fetched at most once per session; a window already covered
        (fully or partly) fetches only its uncovered sub-intervals.
        Rows are deduped by OCC and filtered back to the requested
        window, so the returned list is exactly what a direct fetch
        of that window returns. A fetcher exception marks NOTHING
        covered (the next caller retries, as before) and yields no
        rows for the uncovered piece (fail closed)."""
        if self.fetch_contracts is None:
            return []
        try:
            lo_d = date.fromisoformat(str(gte)[:10])
            hi_d = date.fromisoformat(str(lte)[:10])
        except ValueError:
            try:
                return list(self.fetch_contracts(sym, kind, gte, lte)
                            or [])
            except Exception:
                return []
        if hi_d < lo_d:
            return []
        ent = self._contracts_union.setdefault(
            (session, sym, kind), {"intervals": [], "rows": {}})
        # Uncovered sub-intervals of [lo_d, hi_d] given the union.
        uncovered = []
        cur = lo_d
        for a, b in sorted(ent["intervals"]):
            if b < cur:
                continue
            if a > hi_d:
                break
            if a > cur:
                uncovered.append((cur, min(a - timedelta(days=1), hi_d)))
            cur = max(cur, b + timedelta(days=1))
            if cur > hi_d:
                break
        if cur <= hi_d:
            uncovered.append((cur, hi_d))
        for a, b in uncovered:
            try:
                rows = self.fetch_contracts(
                    sym, kind, a.isoformat(), b.isoformat()) or []
            except Exception:
                continue  # not covered: a later caller may retry
            for c in rows:
                occ = c.get("symbol") if isinstance(c, dict) else None
                if occ:
                    ent["rows"].setdefault(occ, c)
            ent["intervals"].append((a, b))
        out = []
        for occ, c in ent["rows"].items():
            exp = str(c.get("expiration") or "")[:10]
            if not exp:
                parsed = parse_occ(occ)
                exp = parsed["expiration"] if parsed else ""
            if exp and gte <= exp <= lte:
                out.append(c)
        return out

    def _snapshots(self, symbols, session=None):
        """{OCC: {bid, ask, delta}} for symbols with a usable snapshot.
        Batched at 100 (the v1beta1 snapshots convention); any batch
        failure drops only that batch (fail closed per contract).
        SCAN-TICK-OVERRUN: with a session, each OCC's successful
        snapshot is fetched at most once per session and served from
        the shared snapshot thereafter; absent OCCs are never
        cached, so a later caller still retries them (old semantics)."""
        out = {}
        if self.fetch_snapshots is None or not symbols:
            return out
        symbols = list(dict.fromkeys(symbols))
        missing = symbols
        if session is not None:
            missing = []
            for occ in symbols:
                snap = self._snapshot_cache.get((session, occ))
                if snap is not None:
                    out[occ] = snap
                else:
                    missing.append(occ)
        for i in range(0, len(missing), 100):
            batch = missing[i:i + 100]
            try:
                snaps = self.fetch_snapshots(batch) or {}
            except Exception:
                continue
            for occ, snap in snaps.items():
                if isinstance(snap, dict):
                    out[occ] = snap
                    if session is not None:
                        self._snapshot_cache[(session, occ)] = snap
        return {occ: out[occ] for occ in symbols if occ in out}

    # -- XT-3: generic chains/quotes for the directional sleeves ---------
    def _basket(self):
        if self._basket_cache is None:
            from core.bars_universe import load_universes
            self._basket_cache = list(
                load_universes().get("basket_41") or [])
        return self._basket_cache

    def _simple_chains_quotes(self, sym, kind, lo, hi, ctx):
        """(chain, quotes) for ONE underlying + kind over a DTE
        window — the shape the directional options sleeves consume:
        chain = [{"symbol", "strike", "expiration"}], quotes =
        {OCC: {"bid", "ask"}}. Cached per (session, sym, kind,
        window); fail closed per door (a failed contracts fetch
        yields no chain; a one-sided snapshot yields no quote)."""
        key = (ctx.session, sym, kind, lo, hi)
        if key in self._simple_cache:
            return self._simple_cache[key]
        chain, quotes = [], {}
        if self.fetch_contracts is not None:
            try:
                ref = date.fromisoformat(ctx.session)
            except ValueError:
                ref = None
            if ref is not None:
                gte = (ref + timedelta(days=lo)).isoformat()
                lte = (ref + timedelta(days=hi)).isoformat()
                rows = self._contracts(sym, kind, gte, lte, ctx.session)
                occs = []
                for c in rows:
                    occ = c.get("symbol")
                    parsed = parse_occ(occ)
                    if parsed is None:
                        continue
                    strike = _f(c.get("strike"))
                    chain.append({
                        "symbol": occ,
                        "strike": strike if strike is not None
                        else parsed["strike"],
                        "expiration": str(
                            c.get("expiration")
                            or parsed["expiration"])[:10]})
                    occs.append(occ)
                snaps = self._snapshots(sorted(set(occs)), ctx.session)
                for occ, snap in snaps.items():
                    bid, ask = _f(snap.get("bid")), _f(snap.get("ask"))
                    if bid is not None and ask is not None:
                        quotes[occ] = {"bid": bid, "ask": ask}
        self._simple_cache[key] = (chain, quotes)
        return chain, quotes

    def _held_occs(self, sleeve_id):
        """Every OCC recorded on the sleeve's held positions (single
        occ, spread legs, condor legs, structured legs, PMCC short) —
        exits read quotes for exactly these."""
        occs = set()
        if self.state_store is None:
            return occs
        try:
            ss = self.state_store.get(sleeve_id).get("sleeve_state") or {}
        except Exception:
            return occs

        def take(v):
            if isinstance(v, str) and parse_occ(v):
                occs.add(v)

        for entry in ss.values():
            if not isinstance(entry, dict):
                continue
            pos = entry.get("position")
            for src in (entry, pos if isinstance(pos, dict) else {}):
                for k in ("occ", "short_occ", "long_occ"):
                    take(src.get(k))
                spread = src.get("spread")
                if isinstance(spread, dict):
                    take(spread.get("short_occ"))
                    take(spread.get("long_occ"))
                condor = src.get("condor")
                if isinstance(condor, dict):
                    for k, v in condor.items():
                        if k.endswith("_occ"):
                            take(v)
                legs = src.get("legs")
                if isinstance(legs, list):
                    for leg in legs:
                        if isinstance(leg, dict):
                            take(leg.get("symbol"))
            pmcc = entry.get("pmcc_short")
            if isinstance(pmcc, dict):
                take(pmcc.get("occ"))
        return occs

    def _held_quotes(self, sleeve_id, session=None):
        quotes = {}
        snaps = self._snapshots(sorted(self._held_occs(sleeve_id)),
                                session)
        for occ, snap in snaps.items():
            bid, ask = _f(snap.get("bid")), _f(snap.get("ask"))
            if bid is not None and ask is not None:
                quotes[occ] = {"bid": bid, "ask": ask}
        return quotes

    def _held_syms(self, sleeve_id):
        if self.state_store is None:
            return []
        try:
            ss = self.state_store.get(sleeve_id).get("sleeve_state") or {}
        except Exception:
            return []
        return [s for s, e in ss.items()
                if isinstance(e, dict) and e.get("position")]

    def _xt3_extra(self, sleeve_id, ctx):
        """XT-3 (2026-10-16): chains/quotes for the directional
        options sleeves. Every window/kind is the sleeve's own
        ported DTE law; held-position OCCs always get quotes too, so
        exits evaluate on live marks even after the entry chain has
        moved on. chains/quotes are always returned (possibly empty)
        — the sleeves fail closed on empty chains themselves."""
        chains, quotes = {}, {}

        def serve(sym, kind, lo, hi):
            ch, qu = self._simple_chains_quotes(sym, kind, lo, hi, ctx)
            if ch:
                chains.setdefault(sym, []).extend(ch)
            quotes.update(qu)

        if sleeve_id == "bilbo_options":
            from sleeves.bilbo_options import CONFIG as BILBO_CFG
            for sym in BILBO_CFG.universe:
                serve(sym, "call", 14, 45)   # sleeve MIN_DTE/MAX_DTE 21-37
        elif sleeve_id == "saty_day":
            # saty_day (2026-10-21): SPY calls + puts over a fetch
            # window covering the sleeve's 2-4 DTE law (the sleeve
            # filters to the exact window and the ATM strike). The
            # fresh-quotes door is served alongside (below) — the
            # sleeve's entry staleness gate (D-3) reads quote
            # timestamps the snapshot door does not carry.
            serve("SPY", "call", 0, 7)
            serve("SPY", "put", 0, 7)
        elif sleeve_id == "shen_fade":
            # shen_fade (2026-10-22): SPY calls + puts over the
            # same 0-7 DTE fetch window as the saty sleeves; the
            # sleeve filters to the same-day expiry itself (its
            # 0DTE law) and the strike nearest spot. The
            # fresh-quotes door is served alongside (below) — the
            # sleeve's entry / bracket gates read quote
            # timestamps the snapshot door does not carry.
            serve("SPY", "call", 0, 7)
            serve("SPY", "put", 0, 7)
        elif sleeve_id in ("saty_sol", "saty_sol_0dte"):
            # saty_sol (2026-10-21): SPY calls + puts over the
            # same 0-7 DTE fetch window; the sleeve filters to its
            # own governing law (Sol's 2-4 calendar-DTE selection:
            # nearest expiry, nearest strike to spot). The
            # fresh-quotes door is served alongside (below) — the
            # sleeve validates the selected contract's quote and
            # sizes from its ask.
            # saty_sol_0dte (2026-10-22) rides the identical doors:
            # its law takes the SAME window and keeps only the
            # same-day expiry (the variant's one deviation).
            serve("SPY", "call", 0, 7)
            serve("SPY", "put", 0, 7)
        elif sleeve_id == "em_1587":
            # em_1587 (2026-10-22): SPY calls + puts over the
            # same 0-7 DTE fetch window; the sleeve filters to
            # its own law (0DTE, strike nearest spot — Azrael's
            # 15.87 Rule expressed in SPY 0DTE options). The
            # fresh-quotes door is served alongside (below) —
            # the sleeve's entry pricing and staleness gate
            # read it, like saty_day's.
            serve("SPY", "call", 0, 7)
            serve("SPY", "put", 0, 7)
        elif sleeve_id == "capitulation_options":
            for sym in self._basket():
                serve(sym, "call", 0, 10)    # sleeve DTE 0-7
        elif sleeve_id in ("ema_vwap_options", "rsi_meanrev_options"):
            for sym in self._basket():
                serve(sym, "call", 10, 35)   # sleeve DTE 14-30
        elif sleeve_id == "spx_premium":
            serve("XSP", "put", -7, 7)       # the sleeve filters to its week
        elif sleeve_id == "vix_hedge":
            serve("VXX", "call", 50, 120)    # sleeve DTE 60-110
        elif sleeve_id == "leaps_momentum":
            book = {}
            if self.state_store is not None:
                try:
                    book = self.state_store.get("momentum").get(
                        "meta", {}).get("momentum_book") or {}
                except Exception:
                    book = {}
            syms = sorted(set(book) | set(self._held_syms(sleeve_id)))
            for sym in syms:
                # PMCC shorts (25-38 DTE) and LEAPS (>= 365 DTE).
                serve(sym, "call", 20, 45)
                serve(sym, "call", 330, 760)
            for sym in list(chains):
                seen, dedup = set(), []
                for row in chains[sym]:
                    if row["symbol"] not in seen:
                        seen.add(row["symbol"])
                        dedup.append(row)
                chains[sym] = dedup
        elif sleeve_id == "fear_premium":
            from sleeves.fear_premium import rank_universe
            bars = self._daily(self._basket() + ["QQQ", "TQQQ"], ctx)
            syms = list(dict.fromkeys(
                rank_universe(bars) + self._held_syms(sleeve_id)))
            for sym in syms:
                serve(sym, "put", 18, 42)    # sleeve DTE 25-35 (±4)
        quotes.update(self._held_quotes(sleeve_id, ctx.session))
        out = {"chains": chains, "quotes": quotes}
        if sleeve_id in ("saty_day", "saty_sol", "saty_sol_0dte", "em_1587",
                         "shen_fade"):
            occs = sorted({c["symbol"] for c in chains.get("SPY", [])})
            fresh = {}
            for i in range(0, len(occs), 100):
                fresh.update(self._fo_quotes(occs[i:i + 100],
                                             ctx.session))
            out["fresh_quotes"] = fresh
        return out

    # -- iron_condor -------------------------------------------------------
    def _condor_chains_quotes(self, sym, ctx):
        key = (ctx.session, sym)
        if key in self._chain_cache:
            return self._chain_cache[key]
        chains, quotes = {}, {}
        if self.fetch_contracts is not None:
            try:
                ref = date.fromisoformat(ctx.session)
            except ValueError:
                ref = None
            if ref is not None:
                gte = (ref + timedelta(days=CONDOR_DTE_LO - 5)).isoformat()
                lte = (ref + timedelta(days=CONDOR_DTE_HI + 5)).isoformat()
                rows = []
                for kind in ("put", "call"):
                    rows.extend(self._contracts(
                        sym, kind, gte, lte, ctx.session))
                by_kind = {"put": [], "call": []}
                occs = []
                for c in rows:
                    occ = c.get("symbol")
                    kind = "put" if c.get("type") == "put" else \
                        "call" if c.get("type") == "call" else None
                    if not occ or kind is None:
                        parsed = parse_occ(occ)
                        if parsed is None:
                            continue
                        kind = "put" if parsed["cp"] == "P" else "call"
                        c = {**c, "strike": parsed["strike"],
                             "expiration": parsed["expiration"]}
                    by_kind[kind].append(
                        {"symbol": occ, "strike": c.get("strike"),
                         "expiration": c.get("expiration"),
                         "tradable": c.get("tradable", True)})
                    occs.append(occ)
                snaps = self._snapshots(sorted(set(occs)), ctx.session)
                for occ, snap in snaps.items():
                    bid, ask = _f(snap.get("bid")), _f(snap.get("ask"))
                    if bid is not None and ask is not None:
                        quotes[occ] = {"bid": bid, "ask": ask}
                chains = by_kind
        self._chain_cache[key] = (chains, quotes)
        return chains, quotes

    def _condor_iv(self, sym, ctx, chains, quotes, spot):
        """Current IV per the sleeve docstring's own definition: BS
        inversion (the sleeve's implied_vol) of the nearest 30-45 DTE
        ATM call mid. None on any failure (fail closed)."""
        if not spot or spot <= 0:
            return None
        try:
            ref = date.fromisoformat(ctx.session)
        except ValueError:
            return None
        cands = []
        for c in (chains or {}).get("call", []):
            exp = str(c.get("expiration") or "")[:10]
            try:
                dte = (date.fromisoformat(exp) - ref).days
                strike = float(c["strike"])
            except (TypeError, ValueError):
                continue
            if CONDOR_DTE_LO <= dte <= CONDOR_DTE_HI:
                cands.append((dte, abs(strike - spot), c, dte))
        if not cands:
            return None
        cands.sort(key=lambda x: (x[0], x[1]))
        _dte, _diff, contract, dte = cands[0]
        q = (quotes or {}).get(contract["symbol"]) or {}
        bid, ask = _f(q.get("bid")), _f(q.get("ask"))
        if bid is None or ask is None or bid <= 0 or ask < bid:
            return None
        from sleeves.iron_condor import implied_vol
        return implied_vol((bid + ask) / 2.0, float(spot),
                           float(contract["strike"]),
                           max(dte, 1) / 365.0, 0.04, "call")

    def _earnings_in_days(self, ctx):
        from core.event_feeds import earnings_from_doc
        dates, _fresh = earnings_from_doc(self.earnings_doc, ctx.now)
        try:
            ref = date.fromisoformat(ctx.session)
        except ValueError:
            return {}
        out = {}
        for sym, dstr in dates.items():
            if isinstance(dstr, str):
                try:
                    out[sym] = (date.fromisoformat(dstr[:10]) - ref).days
                except ValueError:
                    pass
        return out

    def _stored(self, sleeve_id, key, default):
        if self.state_store is None:
            return default
        try:
            v = self.state_store.get(sleeve_id).get(key)
        except Exception:
            return default
        return v if isinstance(v, type(default)) else default

    def _condor_extra(self, ctx):
        from sleeves.iron_condor import CONFIG as CONDOR_CFG
        watch = list(CONDOR_CFG.universe)
        bars = self._daily(watch, ctx)
        chains, quotes, iv_map = {}, {}, {}
        for sym in watch:
            ch, qu = self._condor_chains_quotes(sym, ctx)
            if ch.get("put") or ch.get("call"):
                chains[sym] = ch
            quotes.update(qu)
            bl = bars.get(sym) or []
            spot = _f(bl[-1].get("c")) if bl else None
            iv = self._condor_iv(sym, ctx, ch, qu, spot)
            if iv is not None:
                iv_map[sym] = iv
        history = self._stored("iron_condor", "iv_history", {})
        last = self._stored("iron_condor", "iv_history_last", {})
        extra = {"chains": chains, "quotes": quotes, "iv": iv_map,
                 "iv_history": {s: list(v) for s, v in history.items()},
                 "earnings_in_days": self._earnings_in_days(ctx),
                 "vix": self._vix_close(ctx)}
        # Causal IV series: today's observation is stamped AFTER the
        # sleeve evaluates (dispatch stamp_state writer), so the rank
        # the sleeve computes today uses prior observations only.
        stamp_hist, stamp_last = dict(history), dict(last)
        changed = False
        for sym, iv in iv_map.items():
            if stamp_last.get(sym) != ctx.session:
                stamp_hist[sym] = (list(stamp_hist.get(sym) or [])
                                   + [float(iv)])[-300:]
                stamp_last[sym] = ctx.session
                changed = True
        if changed:
            extra["stamp_state"] = {"iv_history": stamp_hist,
                                    "iv_history_last": stamp_last}
        return extra

    # -- qqq_put_ladder ----------------------------------------------------
    def _ladder_quotes(self, ctx):
        if ctx.session in self._ladder_cache:
            return self._ladder_cache[ctx.session]
        quotes = []
        if self.fetch_contracts is not None:
            try:
                ref = date.fromisoformat(ctx.session)
            except ValueError:
                ref = None
            if ref is not None:
                gte = ref.isoformat()
                lte = (ref + timedelta(days=LADDER_DTE_MAX)).isoformat()
                rows = self._contracts(
                    LADDER_UNDERLYING, "put", gte, lte, ctx.session)
                occs, meta = [], {}
                for c in rows:
                    occ = c.get("symbol")
                    parsed = parse_occ(occ)
                    if parsed is None:
                        continue
                    meta[occ] = {"symbol": occ,
                                 "expiration": c.get("expiration")
                                 or parsed["expiration"],
                                 "strike": _f(c.get("strike"))
                                 if c.get("strike") is not None
                                 else parsed["strike"]}
                    occs.append(occ)
                snaps = self._snapshots(sorted(set(occs)), ctx.session)
                for occ in sorted(meta):
                    snap = snaps.get(occ) or {}
                    bid, ask = _f(snap.get("bid")), _f(snap.get("ask"))
                    if bid is None or ask is None:
                        continue  # unquotable: the sleeve fails closed on it
                    row = dict(meta[occ])
                    row.update({"bid": bid, "ask": ask,
                                "delta": _f(snap.get("delta"))})
                    quotes.append(row)
        self._ladder_cache[ctx.session] = quotes
        return quotes

    def _ladder_extra(self, ctx):
        bars = self._daily([LADDER_UNDERLYING], ctx).get(LADDER_UNDERLYING) or []
        closes = [float(b["c"]) for b in bars
                  if _f(b.get("c")) is not None]
        acct = self._account(ctx)
        bp = None
        if acct is not None:
            bp = _f(acct.get("options_buying_power"))
            if not bp:
                # Alpaca paper reports options_buying_power="0" even
                # on a level-3 options account (verified live
                # 2026-10-15: obp "0", buying_power 87552.91, an XSP
                # spread held) — a literal 0 is a dead field, not a
                # cash fact; the cash-secured check uses buying_power.
                bp = _f(acct.get("buying_power"))
        week_opened = None
        if self.state_store is not None:
            try:
                w = self.state_store.get("qqq_put_ladder").get("week_opened")
                week_opened = w if isinstance(w, str) else None
            except Exception:
                week_opened = None
        return {
            "layers": list(self._stored("qqq_put_ladder", "layers", [])),
            "week_opened": week_opened,
            "quotes": self._ladder_quotes(ctx),
            "spot": closes[-1] if closes else None,
            "qqq_closes": closes[-10:],
            "buying_power": bp,
            "equity_pending": False,
            "posture": "unknown",  # no lean source for the brain plan; see docstring
        }

    # -- free_opt family (sourceable inputs only) ---------------------------
    def _release_events(self):
        events = []
        for e in (self.macro_doc or {}).get("events") or []:
            d = str(e.get("date") or "")[:10]
            if d:
                # The calendar's dates are verified against primary
                # sources per the file's own note (federalreserve.gov
                # / bls.gov) — that is the sleeve's "verified" flag.
                events.append({"session": d, "verified": True})
        return events

    # -- recovered rulebook (config/options_rules.json) -------------------
    _PRESERVES = {"free_opt_own_iv": "OPT_OWN_IV_RESIDUAL",
                  "free_opt_release": "OPT_RELEASE_CONVEXITY",
                  "free_opt_pair": "OPT_STATIONARY_PAIR",
                  "free_opt_tail": "OPT_TAIL_STATE",
                  "free_opt_wheel": "OPT_WHEEL_LIFECYCLE"}

    # ACTIVATION (User's ruling, 2026-10-16, the X-3 item): the five
    # parent books are desk-active. Capital is the source design's
    # own FREE_OPTIONS package pool — aurelia_common
    # BUDGETS["FREE_OPTIONS"] = 100_000 ("package pool"), the figure
    # every port doc and sleeve BUDGET_USD names; sizing is the
    # source's one contract per order/leg. The recovered config row
    # is never rewritten: the desk's construction carries the
    # source's input_blocker forward as recovered_input_blocker
    # (provenance), because the input it names remains an external
    # input by source design (see the module docstring).
    _ACTIVATED = frozenset(_PRESERVES.values())
    FREE_OPTIONS_POOL_USD = 100_000
    ACTIVATION_NOTE = ("activated by User's ruling 2026-10-16 "
                       "(X-3): desk-active at the FREE_OPTIONS "
                       "package pool; quote/package remain external "
                       "inputs per the source design")

    def _books(self):
        if self._books_cache is None:
            books = []
            if self.fetch_books is not None:
                try:
                    books = list(self.fetch_books() or [])
                except Exception:
                    books = []
            self._books_cache = books
        return self._books_cache

    def _rulebook_book(self, sleeve_id):
        want = self._PRESERVES.get(sleeve_id)
        for book in self._books():
            if book.get("strategy_id") == want or book.get("id") == want:
                row = {"id": book.get("id"),
                       "monitor_only": bool(book.get("monitor_only")),
                       "initial_capital": book.get("initial_capital"),
                       "input_blocker": book.get("input_blocker")}
                if want in self._ACTIVATED:
                    # The desk's book construction under User's
                    # 2026-10-16 activation ruling: the recovered
                    # source verdict stays on the row as provenance
                    # (recovered_*), the operating posture is active
                    # at the design's pool capital.
                    row.update({
                        "monitor_only": False,
                        "initial_capital": self.FREE_OPTIONS_POOL_USD,
                        "input_blocker": None,
                        "recovered_monitor_only": bool(
                            book.get("monitor_only")),
                        "recovered_initial_capital": book.get(
                            "initial_capital"),
                        "recovered_input_blocker": book.get(
                            "input_blocker"),
                        "activation": self.ACTIVATION_NOTE})
                return row
        return None

    def _frozen_hedge(self, ctx):
        """Verbatim desk/option_inputs._hedge (Agentic-Trading-Desk
        aurelia-paper-desk): freeze SPY/QQQ hedge from completed SIP
        closes; the last bar is not inside the fit. {} when the
        history cannot support the fit (the source's own shape)."""
        daily = self._daily(["SPY", "QQQ"], ctx)

        def closes(sym):
            from datetime import datetime, timezone
            out = {}
            for b in daily.get(sym) or []:
                raw_t = b.get("session") or b.get("t")
                if isinstance(raw_t, (int, float)):
                    sess = datetime.fromtimestamp(
                        float(raw_t), tz=timezone.utc).date().isoformat()
                else:
                    sess = str(raw_t or "")[:10]
                c = _f(b.get("c") if "c" in b else b.get("close"))
                if sess and c:
                    out[sess] = c
            return out

        spy, qqq = closes("SPY"), closes("QQQ")
        sessions = sorted(set(spy) & set(qqq))
        if len(sessions) < 62:
            return {}
        fit, last = sessions[-61:-1], sessions[-1]
        rs, rq = [], []
        for older, newer in zip(fit, fit[1:]):
            rs.append(spy[newer] / spy[older] - 1)
            rq.append(qqq[newer] / qqq[older] - 1)
        mean_s = sum(rs) / len(rs)
        var = sum((value - mean_s) ** 2 for value in rs) / len(rs)
        if var <= 0:
            return {}
        cov = sum((a - mean_s) * (b - sum(rq) / len(rq))
                  for a, b in zip(rs, rq)) / len(rs)
        beta = cov / var
        residual = [b - beta * a for a, b in zip(rs, rq)]
        center = sum(residual) / len(residual)
        scale = (sum((value - center) ** 2 for value in residual)
                 / len(residual)) ** 0.5
        live = (qqq[last] / qqq[fit[-1]] - 1) - beta * (spy[last] / spy[fit[-1]] - 1)
        z = (live - center) / scale if scale else 0.0
        return {"beta": beta, "z": z, "asof": fit[-1],
                "signal_session": last, "signal": abs(z) > 2,
                "reason": f"Hedge frozen through {fit[-1]}. "
                          f"Latest residual z is {z:.2f}."}

    def _tail_return(self, ctx):
        bars = self._daily([TAIL_UNDERLYING], ctx).get(TAIL_UNDERLYING) or []
        closes = [float(b["c"]) for b in bars if _f(b.get("c")) is not None]
        if len(closes) < 2 or closes[-2] <= 0:
            return None
        return closes[-1] / closes[-2] - 1.0

    # -- free_opt supply constructor (FREEOPT-COMPLETE, 2026-10-16) -------
    FO_EXPIRY_WINDOW_DAYS = 14
    FO_RV_SESSIONS = 20

    def _fo_contracts(self, sym, kind, ctx):
        """Listed contracts for (sym, kind) inside the selection
        window (session .. session+14d), cached per session. [] on
        any door failure (fail closed)."""
        key = (ctx.session, sym, kind)
        if key in self._fo_chain_cache:
            return self._fo_chain_cache[key]
        rows = []
        if self.fetch_contracts is not None:
            ref = None
            try:
                ref = date.fromisoformat(ctx.session)
            except ValueError:
                pass
            if ref is not None:
                raw = self._contracts(
                    sym, kind, ref.isoformat(),
                    (ref + timedelta(
                        days=self.FO_EXPIRY_WINDOW_DAYS)).isoformat(),
                    ctx.session)
                for c in raw:
                    occ = c.get("symbol")
                    parsed = parse_occ(occ)
                    if parsed is None:
                        continue
                    strike = _f(c.get("strike"))
                    rows.append({
                        "symbol": occ,
                        "strike": strike if strike is not None
                        else parsed["strike"],
                        "expiration": str(c.get("expiration")
                                          or parsed["expiration"])[:10]})
        self._fo_chain_cache[key] = rows
        return rows

    def _fo_spot(self, sym, ctx):
        bars = self._daily([sym], ctx).get(sym) or []
        closes = [float(b["c"]) for b in bars if _f(b.get("c")) is not None]
        return closes[-1] if closes else None

    def _fo_select(self, sym, kinds, ctx):
        """(expiry, strike, {kind: occ}): the nearest expiry strictly
        after the session listing every kind in `kinds`, at the
        listed strike nearest the SIP spot (for several kinds, a
        strike listed for all of them). None when the spot or the
        chain cannot support the selection — the constructor never
        walks past an unquotable expiry shopping for a trade."""
        spot = self._fo_spot(sym, ctx)
        if spot is None:
            return None
        by_kind = {k: self._fo_contracts(sym, k, ctx) for k in kinds}
        if any(not v for v in by_kind.values()):
            return None
        expiries = sorted({c["expiration"] for v in by_kind.values()
                           for c in v if c["expiration"] > ctx.session})
        for exp in expiries:
            strikes = None
            for k in kinds:
                ks = {c["strike"] for c in by_kind[k]
                      if c["expiration"] == exp}
                strikes = ks if strikes is None else strikes & ks
            if not strikes:
                continue
            strike = min(strikes, key=lambda s: (abs(s - spot), s))
            occs = {}
            for k in kinds:
                for c in by_kind[k]:
                    if c["expiration"] == exp and c["strike"] == strike:
                        occs[k] = c["symbol"]
                        break
            if len(occs) == len(kinds):
                return exp, strike, occs
        return None

    def _fo_quotes(self, occs, session=None):
        """{occ: quote} from the latest-quotes door, one call for
        the whole package (the legs' source stamps share the door's
        moment — the package_skew window is 30s). A leg enters the
        result only with a two-sided quote and both stamps; the
        sleeves re-check freshness themselves.
        SCAN-TICK-OVERRUN: with a session, each OCC's raw quote row
        is fetched at most once per session and served from the
        shared snapshot thereafter (the saty family's four sleeves
        previously refetched the identical 2,036-OCC SPY chain's
        fresh quotes once per sleeve); the two-sided/stamp
        validation below runs on the served row on every call, so
        validation semantics are unchanged. Rows the door did not
        return are never cached — a later caller retries them."""
        if self.fetch_quotes is None or not occs:
            return {}
        occs = list(dict.fromkeys(occs))
        rows = {}
        missing = occs
        if session is not None:
            missing = []
            for occ in occs:
                row = self._fresh_cache.get((session, occ))
                if row is not None:
                    rows[occ] = row
                else:
                    missing.append(occ)
        if missing:
            try:
                fetched = self.fetch_quotes(list(missing)) or {}
            except Exception:
                fetched = {}
            for occ, row in fetched.items():
                if isinstance(row, dict):
                    rows[occ] = row
                    if session is not None:
                        self._fresh_cache[(session, occ)] = row
        out = {}
        for occ in occs:
            q = rows.get(occ)
            if not isinstance(q, dict):
                continue
            bp, ap = _f(q.get("bp")), _f(q.get("ap"))
            t = q.get("t") or q.get("source_at")
            if bp is None or ap is None or bp <= 0 or ap < bp \
                    or not t or not q.get("received_at"):
                continue
            out[occ] = {"symbol": occ, "bp": bp, "ap": ap, "t": t,
                        "received_at": q.get("received_at")}
        return out

    @staticmethod
    def _fo_leg(occ, right, quote, underlying=None):
        leg = {"symbol": occ, "right": right, "ask": quote["ap"],
               "source_at": quote["t"]}
        if underlying is not None:
            leg["underlying"] = underlying
        return leg

    def _fo_package(self, sel, kinds_rights, session=None):
        """(gate_quote, legs) for a selection, from one quotes-door
        call; (None, None) unless EVERY leg is quotable — a package
        is never approximated from a partial quote set."""
        _exp, _strike, occs = sel
        quotes = self._fo_quotes([occs[k] for k, _r in kinds_rights],
                                 session)
        if len(quotes) < len(kinds_rights):
            return None, None
        legs = [self._fo_leg(occs[k], r, quotes[occs[k]])
                for k, r in kinds_rights]
        return quotes[occs[kinds_rights[0][0]]], legs

    def _fo_rv(self, sym, ctx):
        """Causal realized vol: log-return stdev over the last
        FO_RV_SESSIONS completed sessions — the final served bar
        (the forming/current session) is excluded, the causality
        convention this producer's frozen hedge already uses.
        Annualized sqrt(252), population stdev (hedge convention).
        None without the full history."""
        bars = self._daily([sym], ctx).get(sym) or []
        closes = [float(b["c"]) for b in bars if _f(b.get("c")) is not None]
        if len(closes) < self.FO_RV_SESSIONS + 2:
            return None
        # FO_RV_SESSIONS returns need FO_RV_SESSIONS+1 closes, ending
        # at the last completed close (final bar excluded).
        window = closes[-(self.FO_RV_SESSIONS + 2):-1]
        rets = [math.log(b / a) for a, b in zip(window, window[1:])
                if a > 0 and b > 0]
        if len(rets) < self.FO_RV_SESSIONS:
            return None
        mean = sum(rets) / len(rets)
        var = sum((r - mean) ** 2 for r in rets) / len(rets)
        return math.sqrt(var) * math.sqrt(252.0)

    def _fo_iv(self, occ, sym, ctx, expiry):
        """Indicative IV of one contract: BS inversion of its
        snapshot mid — the desk's own IV definition (the condor's
        implied_vol, as in _condor_iv). None on any failure."""
        parsed = parse_occ(occ)
        spot = self._fo_spot(sym, ctx)
        if parsed is None or spot is None:
            return None
        snap = self._snapshots([occ], ctx.session).get(occ) or {}
        bid, ask = _f(snap.get("bid")), _f(snap.get("ask"))
        if bid is None or ask is None or bid <= 0 or ask < bid:
            return None
        try:
            dte = (date.fromisoformat(expiry)
                   - date.fromisoformat(ctx.session)).days
        except ValueError:
            return None
        if dte <= 0:
            return None
        from sleeves.iron_condor import implied_vol
        return implied_vol((bid + ask) / 2.0, spot, parsed["strike"],
                           dte / 365.0, 0.04,
                           "call" if parsed["cp"] == "C" else "put")

    def _fo_session_dates(self, ctx):
        """The SPY SIP session calendar (ascending ISO dates) — the
        delivered-dates list the sleeves' session-count exits read
        (the P3 _sessions_since counting law)."""
        bars = self._daily([TAIL_UNDERLYING], ctx).get(
            TAIL_UNDERLYING) or []
        out = set()
        for b in bars:
            raw = b.get("session") or b.get("t")
            if isinstance(raw, (int, float)):
                from datetime import datetime, timezone
                out.add(datetime.fromtimestamp(
                    float(raw), tz=timezone.utc).date().isoformat())
            elif raw:
                out.add(str(raw)[:10])
        return sorted(out)

    def _wheel_call_needed(self, sleeve_id):
        """True while the wheel's served state holds an assigned
        shares record (the core derivation's wheel record) with no
        open short call record on the same underlying — the exact
        condition the sleeve's covered-call step reads back."""
        if self.state_store is None:
            return False
        try:
            ss = self.state_store.get(sleeve_id).get(
                "sleeve_state") or {}
        except Exception:
            return False
        shares_sym = None
        for sym, entry in ss.items():
            if not isinstance(entry, dict):
                continue
            pos = entry.get("position")
            if isinstance(pos, dict) and pos.get("wheel") == "assigned":
                try:
                    if float(pos.get("qty") or 0) > 0:
                        shares_sym = sym
                except (TypeError, ValueError):
                    continue
        if shares_sym is None:
            return False
        for sym, entry in ss.items():
            parsed = parse_occ(sym)
            if not parsed or parsed["cp"] != "C" \
                    or parsed["root"] != shares_sym:
                continue
            if not isinstance(entry, dict):
                continue
            pos = entry.get("position")
            if isinstance(pos, dict):
                try:
                    if float(pos.get("qty") or 0) < 0:
                        return False    # already covered
                except (TypeError, ValueError):
                    continue
        return True

    def _freeopt_supply(self, sleeve_id, ctx, out):
        """Assemble the constructor's quote/package extras (and the
        exit inputs) onto `out`, the extras extra_for composed for
        one of the five books. Every piece fails closed on its own:
        what the canonical doors cannot assemble is absent, and the
        sleeve's ported rules remain the only entry/exit law."""
        if self._held_syms(sleeve_id):
            quotes = self._held_quotes(sleeve_id, ctx.session)
            if quotes:
                out["quotes"] = quotes
            dates = self._fo_session_dates(ctx)
            if dates:
                out["session_dates"] = dates
        if self.fetch_quotes is None:
            return
        if sleeve_id == "free_opt_tail":
            ret = _f(out.get("underlying_return"))
            # The sleeve's own entry threshold gates the door call
            # (mirrored constant, as with the XT-3 windows); the
            # sleeve re-checks the return itself.
            if ret is not None and ret <= -0.03:
                sel = self._fo_select(TAIL_UNDERLYING, ("put",), ctx)
                if sel is not None:
                    q = self._fo_quotes([sel[2]["put"]], ctx.session).get(sel[2]["put"])
                    if q is not None:
                        out["quote"] = q
        elif sleeve_id == "free_opt_wheel":
            cash = _f(out.get("cash"))
            if cash is not None:
                sel = self._fo_select(TAIL_UNDERLYING, ("put",), ctx)
                if sel is not None and cash >= sel[1] * 100:
                    q = self._fo_quotes([sel[2]["put"]], ctx.session).get(sel[2]["put"])
                    if q is not None:
                        out["quote"] = {**q, "strike": sel[1]}
            # AUDIT3 Batch 4: the covered-call supply — while the
            # sleeve holds assigned wheel shares with no open
            # covering call, serve the call its covered-call step
            # sells (the family's own selection: nearest expiry
            # after the session, strike nearest spot, on the
            # monitor underlying the shares came from).
            if self._wheel_call_needed(sleeve_id):
                sel = self._fo_select(TAIL_UNDERLYING, ("call",), ctx)
                if sel is not None:
                    q = self._fo_quotes([sel[2]["call"]],
                                        ctx.session).get(
                        sel[2]["call"])
                    if q is not None:
                        out["call_quote"] = {**q, "strike": sel[1]}
        elif sleeve_id == "free_opt_own_iv":
            sel = self._fo_select(TAIL_UNDERLYING, ("call", "put"), ctx)
            if sel is not None:
                rv = self._fo_rv(TAIL_UNDERLYING, ctx)
                ivs = [self._fo_iv(sel[2][k], TAIL_UNDERLYING, ctx,
                                   sel[0]) for k in ("call", "put")]
                # The design's entry text, computed: a causal
                # realized-volatility forecast exceeding indicative
                # IV by 2 points. No gate, no package.
                if rv is not None and all(v is not None for v in ivs) \
                        and rv > sum(ivs) / len(ivs) + 0.02:
                    q, legs = self._fo_package(
                        sel, (("call", "call"), ("put", "put")),
                        ctx.session)
                    if legs:
                        out["quote"] = q
                        out["package"] = {"legs": legs}
        elif sleeve_id == "free_opt_release":
            dated = any(e.get("session") == ctx.session
                        and e.get("verified")
                        for e in out.get("events") or [])
            if dated:
                sel = self._fo_select(TAIL_UNDERLYING, ("call", "put"),
                                      ctx)
                if sel is not None:
                    q, legs = self._fo_package(
                        sel, (("call", "call"), ("put", "put")),
                        ctx.session)
                    if legs:
                        out["quote"] = q
                        out["package"] = {"legs": legs}
        elif sleeve_id == "free_opt_pair":
            hedge = (out.get("package") or {}).get("hedge") or {}
            z = _f(hedge.get("z"))
            # Legs attach only on the frozen hedge's own signal; the
            # direction is the residual's sign (z > 0: QQQ rich vs
            # SPY — long SPY via a call, short QQQ via a put).
            if hedge.get("signal") and z:
                rich, cheap = ("QQQ", "SPY") if z > 0 else ("SPY", "QQQ")
                plan = ((cheap, "call"), (rich, "put"))
                occs, ok = [], True
                for sym, kind in plan:
                    sel = self._fo_select(sym, (kind,), ctx)
                    if sel is None:
                        ok = False
                        break
                    occs.append((sym, kind, sel[2][kind]))
                if ok:
                    quotes = self._fo_quotes([o for _s, _k, o in occs],
                                             ctx.session)
                    if len(quotes) == len(occs):
                        out["package"] = {
                            "hedge": hedge, "hedge_frozen": True,
                            "legs": [self._fo_leg(o, k, quotes[o],
                                                  underlying=s)
                                     for s, k, o in occs]}
                        out["quote"] = quotes[occs[0][2]]

    # -- dispatcher feeds supplement ---------------------------------------
    def extra_for(self, sleeve_id, ctx):
        if sleeve_id == "iron_condor":
            return self._condor_extra(ctx)
        if sleeve_id == "qqq_put_ladder":
            return self._ladder_extra(ctx)
        if sleeve_id == "free_opt_tail":
            out = {}
            ret = self._tail_return(ctx)
            if ret is not None:
                out["underlying_return"] = ret
            book = self._rulebook_book(sleeve_id)
            if book:
                out["rulebook_book"] = book
            self._freeopt_supply(sleeve_id, ctx, out)
            return out
        if sleeve_id == "free_opt_wheel":
            out = {}
            acct = self._account(ctx)
            cash = _f((acct or {}).get("cash")) if acct else None
            if cash is not None:
                out["cash"] = cash
            book = self._rulebook_book(sleeve_id)
            if book:
                out["rulebook_book"] = book
            self._freeopt_supply(sleeve_id, ctx, out)
            return out
        if sleeve_id == "free_opt_release":
            out = {"events": self._release_events()}
            book = self._rulebook_book(sleeve_id)
            if book:
                out["rulebook_book"] = book
            self._freeopt_supply(sleeve_id, ctx, out)
            return out
        if sleeve_id == "free_opt_pair":
            # Source shape (aurelia run()): package = {"hedge": hedge}
            # when a frozen hedge exists; the supply constructor
            # attaches legs to that package only on the hedge's own
            # signal (FREEOPT-COMPLETE, above).
            out = {}
            hedge = self._frozen_hedge(ctx)
            if hedge:
                out["package"] = {"hedge": hedge, "hedge_frozen": True,
                                  "legs": []}
            book = self._rulebook_book(sleeve_id)
            if book:
                out["rulebook_book"] = book
            self._freeopt_supply(sleeve_id, ctx, out)
            return out
        if sleeve_id == "free_opt_own_iv":
            out = {}
            book = self._rulebook_book(sleeve_id)
            if book:
                out["rulebook_book"] = book
            self._freeopt_supply(sleeve_id, ctx, out)
            return out
        if sleeve_id in ("bilbo_options", "capitulation_options",
                         "ema_vwap_options", "rsi_meanrev_options",
                         "spx_premium", "vix_hedge", "leaps_momentum",
                         "fear_premium", "saty_day", "saty_sol",
                         "saty_sol_0dte", "em_1587", "shen_fade"):
            return self._xt3_extra(sleeve_id, ctx)
        return {}
