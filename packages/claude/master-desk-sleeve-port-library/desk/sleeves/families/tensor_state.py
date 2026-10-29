"""Ausar Tensor state-repair books (2) — H1STATE (hourly) and WSTATE (weekly): the frozen R11 StateRepairPolicy over
the pinned v690 engine's seven signed vote channels. A name qualifies at a completed native bar when the full
seven-vote panel holds now and three bars ago, the vote balance repaired by >= 2 with >= 2 channels increasing,
close >= 5, mean 20-bar dollar volume >= 1M and ATR14 > 0 (20-bar cooldown per origin, consumed even when cash
or slots deny it); once every enrolled name (1,820 hourly / 1,813 weekly) has been assessed for that bar, the
qualifiers rank by repair + .01 balance + .001 clip(OBV slope5 / volume) and are bought at the next native open
inside 5 minutes, ten slots, each sized floor(min(10% equity, 1% of DV20, settled cash) / (price x 1.001)); each
is sold at the open 20 native bars after its entry bar.

Everything that decides is the source itself, vendored byte-exact (desk.feedlib.ts_source): the TensorRuntime
manager (backend/tensor_runtime.py: frame cycles, bounded acquisition, prefix merge, cooldown bootstrap, census,
ranked entries, observed-period exits), the policy (backend/tensor_strategy.py), the engine transport
(backend/tensor_engine.py + strategies/tensor_state_repair/engine, Node) and the books' corporate actions
(backend/tensor_actions.py TensorActions: Yahoo split / dividend events applied to the ledger, receivables,
current probes before entries), installed exactly as backend/tensor_cli.py installed them (ids
tensor_state_repair_1h_r12 / _1wk_r12, frozen enrollments, 256 reads per run, 300 s windows, exclude-unavailable
census policy, audited forward revisions, Yahoo bars, the engine pin, the verified ineligible assets; book policy
fees 0 / slippage 10 bps, 100,000 paper capital) and bound as backend/app.py bound them (TensorActions on the
runtime). Each cycle is the source supervisor's 15-second "strategies" job (backend/autonomy.py): corporate
actions, matured-exit service, fill pass, held-clock exit service, fill pass, run_once, fill pass — on the
production clock (None: every step reads the time itself). Its data come from the source's own Yahoo provider
(ported: desk.feedlib.ts_yahoo, through the desk's shared HTTP client) and its book is the source's local
strategy-book ledger (ported: desk.feedlib.ts_bridge — fresh-quote fills x (1 +- 10 bps), reserved cash, T+1
settled cash); the desk book replicates that ledger's holdings at the desk's venue. The job runs as the desk family
job `tensor_state` (desk/jobs.py: its own process at nice +10, the bulk HTTP lane, the loop's admission control);
each pass reads the ledger it writes through a read-only view (StateView).

Removed (operator / desk-wide, not the strategy's rules): the book halt, drawdown brake, symbol / gross exposure
caps and the portfolio capacity check; the operator enable step (installed enabled, as the inventory records).

Named divergences:
  * research seed: the installed books bound the R11 native research seed (runtime-data/research-seed-r11, the
    reconstructed 2-year hourly and 10-year daily/weekly bars pinned by strategies/research-input-manifest.json,
    preserved only in a release asset) as an immutable prefix; that input is not available here, so the books run
    as the runtime runs without one — the provider's own history (Yahoo 2y hourly / max weekly, the source of the
    same reconstructed bars) is the native prefix, with ordinals from its first bar (234-bar warm-up unchanged);
  * that history as the source's rules can read it (desk/feedlib/ts_yahoo.py named divergences "vendor placeholders"
    and "weekly window"): Yahoo's rows without prices in completed periods and its close points inside the hourly
    history are left out as evidence, and a weekly max read starts from the New York Monday ten years back (the
    seed's span). Without them Yahoo's two years refused 1,793 of H1STATE's 1,820 names and its weekly max 47 of
    WSTATE's 1,813 (2026-10-16/17: a ten-hour Yahoo hole on 2026-01-30 / 02-02, every early close's 12:30 and 13:00
    rows, Tuesday-labelled weeks, pre-1970 histories the runtime reads as unordered), so neither census could open
    entries; with them the runtime admits 1,814 of 1,814 hourly histories stored on 2026-10-16 and, read live on
    2026-10-18, 44 of those 47 weekly names (3 hold rows with inconsistent prices and stay refused);
  * supervisor: the source's supervisor ran the strategies job every 15 s (STRATEGY_POLL_SECONDS); here it is
    the family job tensor_state (cadence 15 s), which the loop launches at its tick (30 s by default) whenever the
    previous run has finished - one cycle per run; tests and parity run the same cycle inside the pass with an
    injected clock. While the regular session is closed and both censuses are assessed (none collecting), it
    cycles every 300 s (cadence): what a cycle does then is re-probe the Yahoo ex-date events of the books'
    traded, candidate and held names (16 a cycle, each again 300 s after its last probe) and retry the censuses'
    failed names, and every probe is due again at the next session open (tensor_actions._required_probe_at), so
    none of it can change an entry or exit before then. At 15 s a run cost 16 Yahoo requests and about 2.2 CPU-s
    every 30 s around the clock (2026-10-18: some 46,000 requests a weekend day against the loop's 2,900); the
    session, its opening window and every collecting census keep the source's cadence;
  * acknowledgement: the strategy's ledger fills at the observed Yahoo quote x (1 +- 10 bps) (its own record,
    which drives its equity, cash and slots); the desk executes the same holdings at its venue's prices;
  * clock: the provider's wall clock is the desk clock (the same instant live);
  * declared dividend payments: the source read them with a private credentials file
    (ASTER_ACTIONS_CREDENTIALS_FILE); here the same GET /v1/corporate-actions goes through the desk's Alpaca
    client (its own credentials; none are read here) — without one, receivables stay accrued as in the source;
  * cash in lieu: the source held a fractional split remainder as a claim that withheld the book's entries until
    an operator recorded its measured payment; the desk records it at the claim's fraction x the first observed
    post-split quote (TensorActions.record_verified_payment, evidence hashed), so entries resume.

Operational note (not a divergence of the rules): H1STATE's 1,820-name census for each completed hour must
finish inside the 5-minute opening window, as at the source. At the desk's shared Yahoo pace (0.35 s per request,
yielded to the trading loop) one hourly census takes over ten minutes, so the runtime records most hours'
candidates as expired, exactly as it did whenever its reads ran late; the census of a session's last hour completes
overnight, so H1STATE's entries at the 09:30 opening stand, and WSTATE's weekly census completes between Friday's
close and Monday's opening. The census keeps the source's cost: 1,820 Yahoo reads per completed regular-session
hour (about 12,700 a session, 256 per run) in the bulk lane. Alpaca's batched SIP hours
(desk/feedlib/canonical_alpaca.py) would cost about ten requests, but they are served 16 minutes after the hour,
past the same window, and differ from Yahoo's hourly prints, so the census keeps the source's provider.
"""
import hashlib
import json
import os
import sqlite3
import threading
from datetime import datetime, timezone
from decimal import Decimal
from urllib.parse import parse_qsl, urlsplit

from ... import calendar as cal
from ...contract import Intent, OrderSpec, Sleeve, SleeveConfig
from ...feedlib import ts_source as TS
from ...feedlib.ts_bridge import Store, TradingBridge, dump
from ...feedlib.ts_yahoo import YahooNative

UTC = timezone.utc
FEED = "tensor_state_desk"
SOURCE = {"repo": "codex-complete-archive", "ref": "artifacts/ausar-corrected-incomplete-2026-10-11",
          "commit": "9de774739ab1fd05a9a93f238d50425d4ceda487",
          "path": "digitalocean-pilot/2026-10-11/context/source/backend/tensor_runtime.py",
          "blob": "e8ee1e67aec13b6e6200c8c203042058656c3d43",
          "policy_blob": "d23c8b1feb0584e800f02664d83c99cfed6b5fe8", "engine_blob": "9e7fd634954660b956ee64c34d01e6c40bc04ee4",
          "actions_blob": "e2c4f543bfb0fb4e764f76160db329e8b8cbd5d5"}
BOOKS = (("ausar_h1state", "tensor_state_repair_1h_r12", "H1STATE", "1h", "Tensor hourly state repair"),
         ("ausar_wstate", "tensor_state_repair_1wk_r12", "WSTATE", "1wk", "Tensor weekly state repair"))
RESEARCH_COMMIT = "4b08cfddcc67d6542e7cb583223874f839cd8f2b"
CAPITAL_CENTS = 100000 * 100
CYCLE_S = 15                                        # backend/autonomy.py STRATEGY_POLL_SECONDS
CLOSED_CYCLE_S = 300                                # the session closed, both censuses assessed (supervisor)
SYNC = [bool(os.environ.get("DESK_TS_SYNC"))]       # tests: run the cycle inside the pass
TRANSPORT = [None]                                  # tests: a fake Yahoo chart transport
DATA = "https://data.alpaca.markets"


def source_dir():
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    return os.environ.get("DESK_TS_SOURCE_DIR") or os.path.join(root, "cache", "tensor_state")


def _sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def install_config(rid, sleeve, frame, book_id, symbols=None):
    """backend/tensor_cli.py install_all's configuration, without the unavailable research seed."""
    m = TS.vendored()
    root = m["tensor_runtime"].ROOT
    config = {"id": rid, "sleeve": sleeve, "book_id": book_id, "enabled": True, "max_fetch_per_run": 256,
              "opening_window_seconds": 300, "missing_data_policy": "exclude_unavailable_with_census_receipts",
              "forward_revision_policy": "retain_frozen_prefix_audit_minor", "expected_bar_provider": "yahoo",
              "engine_source_manifest_sha256": m["tensor_engine"].source_manifest_sha256(),
              "research_commit": RESEARCH_COMMIT,
              "verified_ineligible_file": "strategies/verified-ineligible-assets.json",
              "verified_ineligible_sha256": _sha(os.path.join(root, "strategies", "verified-ineligible-assets.json"))}
    if symbols is None:
        rel = f"strategies/enrollment-{frame}.json"
        config.update(universe_file=rel, universe_sha256=_sha(os.path.join(root, rel)))
    else:
        config["symbols"] = list(symbols)
    return config


def _actions_class():
    base = TS.vendored()["tensor_actions"].TensorActions

    class DeskActions(base):
        """TensorActions with its declared-payment reader bound to the desk's Alpaca client (named divergence)."""

        def __init__(self, store, trading, providers, transport=None, *, alpaca=None):
            self._desk_alpaca = alpaca
            super().__init__(store, trading, providers, transport,
                             payment_transport=self._declared_payments if alpaca is not None else None)

        def _payment_headers(self):
            # no credential is read here: the desk client authenticates its own GET
            return {"X-Desk-Reader": "alpaca-data-client"} if self._desk_alpaca is not None else None

        def _declared_payments(self, method, url, payload, headers):
            parts = urlsplit(url)
            if method != "GET" or payload is not None or f"{parts.scheme}://{parts.netloc}" != DATA or parts.path != "/v1/corporate-actions":
                raise TS.DeskError("Only the declared-payment GET is configured")
            return self._desk_alpaca._get(parts.path, dict(parse_qsl(parts.query)), host=DATA)

    return DeskActions


def settle_cash_in_lieu(actions, store, clock):
    """named divergence: a fractional split claim is paid at its fraction x the first observed post-split quote."""
    from ...feedlib.ts_source import cents, utc_clock
    clock, out = utc_clock(clock), []
    with store.connect() as con:
        claims = [dict(r) for r in con.execute(
            "SELECT c.*,a.effective_at FROM a_strategy_fractional_claims c JOIN a_strategy_actions a ON a.id=c.action_id "
            "WHERE c.status='awaiting_cash_in_lieu' AND a.status='applied' ORDER BY a.effective_at,c.action_id")]
        quotes = {r["symbol"]: dict(r) for r in con.execute("SELECT * FROM quotes")}
    for claim in claims:
        quote = quotes.get(claim["symbol"])
        if not quote or not utc_clock(claim["effective_at"]) <= utc_clock(quote["as_of"]) <= clock:
            continue
        amount = cents(Decimal(claim["quantity"]) * Decimal(quote["price"]))
        evidence = {"action_id": claim["action_id"], "symbol": claim["symbol"], "fractional_quantity": claim["quantity"],
                    "quote": {k: quote[k] for k in ("price", "as_of", "source")}, "amount_cents": amount,
                    "convention": "desk cash in lieu: fraction x first observed post-split quote"}
        digest = hashlib.sha256(dump(evidence).encode()).hexdigest()
        try:
            actions.record_verified_payment(claim["action_id"], utc_clock(quote["as_of"]),
                                            "desk cash in lieu: fraction x first observed post-split quote", digest,
                                            amount_cents=amount, clock=clock)
            out.append({"action_id": claim["action_id"], "amount_cents": amount})
        except TS.DeskError as exc:
            out.append({"action_id": claim["action_id"], "error": exc.detail})
    return out


class StateDesk:
    """one vendored TensorRuntime + TensorActions over its own store, the source's Yahoo provider and
    strategy-book ledger, cycled as the source supervisor's strategies job."""

    def __init__(self, directory, clock, transport=None, symbols=None, alpaca=None):
        TS.install_shims()
        os.makedirs(directory, exist_ok=True)
        self.clock = clock
        self.store = Store(os.path.join(directory, "tensor-state.sqlite3"))
        self.providers = YahooNative(self.store, clock, transport=transport)
        self.trading = TradingBridge(self.store)
        m = TS.vendored()
        self.runtime = m["tensor_runtime"].TensorRuntime(self.store, self.trading, self.providers)
        # backend/app.py: TensorActions(store, trading, providers), bound on the runtime; an injected transport is
        # handed to it explicitly (its fixture clock, as the source's own tests ran it)
        self.actions = _actions_class()(self.store, self.trading, self.providers,
                                        transport if transport is not None else None, alpaca=alpaca)
        self.runtime.actions = self.actions
        self.installs = {}
        for sid, rid, sleeve, frame, name in BOOKS:
            book = self.trading.create_book(name, CAPITAL_CENTS, client_id="r12-opening-capital-" + sleeve)
            self.runtime.install(install_config(rid, sleeve, frame, book, (symbols or {}).get(sleeve)))
            self.installs[sid] = {"id": rid, "book_id": book, "sleeve": sleeve, "frame": frame}
        self.last, self.error, self.cycles = None, None, 0
        self._lock = threading.Lock()

    def cycle(self, clock=None):
        """backend/autonomy.py _execute for kind "strategies" (clock None = production per-step clocks)."""
        at = None if clock is None else datetime.fromtimestamp(float(clock), UTC)
        with self._lock:
            out = {"at": (at or datetime.now(UTC)).isoformat()}
            try:
                out["corporate_actions"] = self.actions.run_once(clock=at, max_symbols=16)
            except Exception as exc:                   # the source job recorded it and continued its owed exits
                out["corporate_actions"] = {"error": f"{type(exc).__name__}: {str(exc)[:160]}"}
            out["cash_in_lieu"] = settle_cash_in_lieu(self.actions, self.store, at)
            out["matured_exits"] = self.runtime.service_exits(clock=at, acquire_native_clocks=False)
            out["matured_exit_process"] = self.trading.process(at)
            out["held_exits"] = self.runtime.service_exits(clock=at)
            out["held_exit_process"] = self.trading.process(at)
            out["strategies"] = self.runtime.run_once(clock=at)
            out["process"] = self.trading.process(at)
            self.last, self.cycles = out, self.cycles + 1
            return out


_DESKS = {}


def _alpaca(hub):
    client = getattr(getattr(hub, "alpaca", None), "c", None)
    return client if callable(getattr(client, "_get", None)) else None


def desk_for(clock, alpaca=None):
    key = source_dir()
    if key not in _DESKS:
        _DESKS[key] = StateDesk(key, clock, transport=TRANSPORT[0], alpaca=alpaca)
    return _DESKS[key]


class StateView:
    """what a desk pass reads: the ledger the job writes (holdings, quotes, account), no runtime, no acquisition."""

    def __init__(self, directory):
        path = os.path.join(directory, "tensor-state.sqlite3")
        if not os.path.exists(path):
            raise FileNotFoundError(path)
        self.store = Store(path)
        self.trading = TradingBridge(self.store)
        try:
            with self.store.connect() as con:
                rows = {r["id"]: r["book_id"] for r in con.execute("SELECT id, book_id FROM a_tensor_installations")}
        except sqlite3.OperationalError:
            rows = {}
        self.installs = {sid: {"id": rid, "book_id": rows[rid], "sleeve": sleeve, "frame": frame}
                         for sid, rid, sleeve, frame, _ in BOOKS if rid in rows}
        self.error = None


def state_desk(feeds, sleeve, now, arg):
    """FEED tensor_state_desk — the books' ledger as the job left it; in SYNC mode (tests) the job's cycle runs here
    once per pass."""
    if SYNC[0]:
        d = desk_for(feeds.clock, alpaca=_alpaca(getattr(feeds, "hub", None)))
        if d.last is None or d.last.get("pass") != now:
            d.cycle(now)
            d.last["pass"] = now
        return d
    try:
        view = StateView(source_dir())
    except FileNotFoundError:
        return None                                  # the job has not run yet
    return view if len(view.installs) == len(BOOKS) else None


def _job(engine):
    """job tensor_state: one run of the source supervisor's strategies job (backend/autonomy.py, kind "strategies")
    on the production clock, in its own process and HTTP lane (desk/jobs.py)."""
    d = StateDesk(source_dir(), engine.clock, transport=TRANSPORT[0], alpaca=_alpaca(getattr(engine, "hub", None)))
    out = d.cycle(None)
    s = out["strategies"]
    info = {"status": s.get("status"), "acquired": s.get("acquired"), "entries": s.get("entries"),
            "exits": s.get("exits") + out["matured_exits"].get("exits", 0) + out["held_exits"].get("exits", 0),
            "fills": sum(out[k].get("fills", 0) for k in ("matured_exit_process", "held_exit_process", "process")),
            "errors": (s.get("errors") or [])[:5],
            "cycles": [{k: c[k] for k in ("frame", "status", "cursor")} for c in s.get("cycles") or []]}
    for sid, inst in d.installs.items():
        info[sid] = d.trading.summary(inst["book_id"], engine.clock())
    return info


def cadence(rec, now):
    """seconds between the job's runs (desk/jobs.cadences): the source's CYCLE_S during the regular session and
    while any census collects or the last run recorded none; CLOSED_CYCLE_S while the session is closed and every
    census of the last run is assessed (complete, degraded or incomplete: all names read)"""
    if cal.is_rth(now):
        return CYCLE_S
    cycles = ((rec or {}).get("info") or {}).get("cycles") or []
    if len(cycles) < len(BOOKS) or any(c.get("status") not in ("complete", "degraded", "incomplete") for c in cycles):
        return CYCLE_S
    return CLOSED_CYCLE_S


FEEDS = {FEED: state_desk}
JOBS = {"tensor_state": ("always", CYCLE_S, _job, cadence)}


class StateBook(Sleeve):
    def __init__(self, sid, rid, sleeve, frame, name):
        self.install_id, self.frame = rid, frame
        m = TS.vendored()
        enrollment = json.load(open(os.path.join(m["tensor_runtime"].ROOT, "strategies", f"enrollment-{frame}.json")))["symbols"]
        self.CONFIG = SleeveConfig(
            sleeve_id=sid, family="tensor_state", cadence_s=30, universe=tuple(enrollment), capital=100000.0,
            schedule="rth", venue_pref="alpaca", needs={"feeds": [FEED]},
            params={"sleeve": sleeve, "frame": frame, "hold_native_bars": 20, "maximum_slots": 10,
                    "entry_cap_equity": 0.10, "entry_cap_native_dv": 0.01, "slippage_bps": 10},
            source=dict(SOURCE, installation_id=rid), state_schema={"mirrored": "dict"})

    def signal(self, view):
        d = view.extra.get(FEED)
        if d is None or self.CONFIG.sleeve_id not in d.installs:
            return []
        inst = d.installs[self.CONFIG.sleeve_id]
        target = d.trading.holdings(inst["book_id"])
        working = {p["inst"].split(":", 1)[1] for p in view.extra.get("pending_orders") or []}
        held = {k.split(":", 1)[1]: float(p["qty"]) for k, p in view.positions.items() if k.startswith("EQ:")}
        out = []
        with d.store.connect() as con:
            quotes = {r["symbol"]: float(r["price"]) for r in con.execute("SELECT symbol,price FROM quotes")}
        for sym in sorted(set(target) | set(held)):
            want, have = float(target.get(sym, 0)), held.get(sym, 0.0)
            if abs(want - have) < 1e-9 or sym in working:
                continue
            out.append(Intent("target", sym, qty=want, price_hint=quotes.get(sym),
                              signal_key=f"{self.install_id}:{sym}:{want:g}",
                              reason=f"{self.install_id}: replicate the strategy ledger's {want:g} {sym}",
                              order=OrderSpec(window_s=300)))
        s = d.trading.summary(inst["book_id"], view.now)
        out.append(Intent("signal", self.CONFIG.universe[0], reason=f"ledger equity {s['equity']:.2f}, "
                          f"{s['positions']} held, {s['fills']} fills, {s['active_intents']} active",
                          meta={"ledger": s, "error": d.error}, signal_key=f"ledger:{s['fills']}:{s['active_intents']}"))
        return out


def sleeves():
    return [StateBook(*b) for b in BOOKS]
