"""Broker doors. PaperDoor is the ONLY trading network client shape in v3:
paper base URL enforced at construction, live env refused at startup
(credentials route identical to v2: ALPACA_KEY_ID env / Secure Vault
surrogate — values are read by the door process only, never logged,
never passed to workers). FakeBroker is the test double: fills exist
only when a read-back (get_order) reports them."""
from __future__ import annotations
import os
from .security import assert_paper_only, assert_paper_url, PAPER_BASE_URL


# FEE-CFEE-WALK-20261110 (TOTAL APPLICATION W4, census DSK-3/DSK-4):
# the broker activity types the reconcile cash expectation models.
# Every type the broker's /v2/account/activities endpoint can post
# belongs to exactly one class: COUNTED (its signed net_amount moves
# expected cash), or AUDITED-ZERO (a named non-cash or
# already-journalled class: fills are journalled, contract events
# and option assignment / exercise / expiry legs are position
# events whose cash twin, when one exists, posts as an activity in
# a counted class). A type the enumeration does not know is NEVER
# dropped silently: activity_type_audit() names it on the
# reconcile record, and the blocker test asserts this enumeration
# stays total, so the next omitted type is caught by the gate, not
# by a desk-wide halt (DSK-3 was CFEE: 836 USD rows, -$5,352.33,
# invisible to expected cash for days).
COUNTED_CASH_ACTIVITY_TYPES = frozenset({
    "FEE",   # CAT / REG regulatory fees on sell proceeds
    "CFEE",  # Coin Pair Transaction Fee (USD rows; in-kind rows
             # carry net_amount 0 and contribute nothing)
    "CSD", "CSW",      # cash sweep deposit / withdrawal
    "DIV", "DIVCGL", "DIVCGS", "DIVNRA", "DIVROC", "DIVTXW",
    "INT", "INTP",     # interest credited / paid
    "JNLS",            # journal securities-cash leg
    "ACATC", "ACATS",  # ACATS cash legs (the asset leg moves no cash)
    "FEEB",            # fee rebate credits
})
AUDITED_ZERO_ACTIVITY_TYPES = frozenset({
    "JNLC",   # journal cash: the epoch's funding deposit. The
              # baseline pair (slice_capital_total + cash_offset)
              # already carries the epoch's opening cash, so
              # counting JNLC double-counts it (the first cured
              # proof reconcile read expected cash exactly
              # $1,000,000 high on this leg alone, W4). A second
              # JNLC posting inside an epoch is a re-basing event:
              # it is the shape the enumeration review must catch
              # by name, and a new funding event re-bases the epoch
              # rather than entering the fee term.
    "FILL",   # journalled as fill rows; spend derives from them
    "OCT",    # option contract event marker; its cash leg posts
              # separately in a counted class
    "OPEXC", "OPASN", "OPXPL", "OPTRD",  # option exercise /
              # assignment / expiry / trade position events
    "SPLIT", "SPIN", "MERGER", "RIGHTS", "WARRANTS",  # corporate
              # actions: quantity events; any cash election posts
              # under DIV / CSD in a counted class
    "PTR",    # pass-through (regulatory fee passthrough marker)
    "NTC",    # non-trade correction marker
    "MACT",   # merger / acquisition activity marker
})
KNOWN_ACTIVITY_TYPES = (COUNTED_CASH_ACTIVITY_TYPES
                        | AUDITED_ZERO_ACTIVITY_TYPES)


def activity_type_audit(rows):
    """(counted_total, unknown) for one activity walk: the signed
    net_amount sum over the rows in COUNTED_CASH_ACTIVITY_TYPES
    (deduped by activity id), and the sorted set of activity types
    the enumeration does not know. Unknown types contribute NOTHING
    to the total: they are surfaced by name so the enumeration is
    extended deliberately, never defaulted into or out of the cash
    expectation by silence."""
    total, seen, unknown = 0.0, set(), set()
    for r in rows or []:
        t = r.get("activity_type")
        if t not in KNOWN_ACTIVITY_TYPES:
            if t is not None:
                unknown.add(str(t))
            continue
        if t not in COUNTED_CASH_ACTIVITY_TYPES:
            continue
        rid = r.get("id")
        if rid in seen:
            continue
        seen.add(rid)
        total += float(r.get("net_amount") or 0)
    return total, sorted(unknown)


def options_market_open(now_et):
    """OPTIONS-HOURS-20261104: the shared regular-session
    predicate (Mon-Fri 09:30-16:00 ET) for options market orders.
    PaperDoor.submit_order refuses locally outside it, and the
    dispatcher's drain holds queued options market orders while
    it is closed; both sides read the same rule from here."""
    from datetime import time as _dtime
    return now_et.weekday() < 5 and \
        _dtime(9, 30) <= now_et.time() < _dtime(16, 0)


class PaperDoor:
    # BLOCKED-EXIT-20261029: the live book of record. The dispatcher
    # reconciles EXIT intents against this broker's positions and
    # resting orders before anything reaches the wire (see
    # dispatcher._reconcile_exit); test doubles opt in explicitly.
    live_book = True

    def __init__(self, base_url=PAPER_BASE_URL, env=None, now_fn=None):
        assert_paper_only(env)
        assert_paper_url(base_url)
        self.base_url = base_url
        env = os.environ if env is None else env
        self._env = env
        self._key_id = env.get("ALPACA_KEY_ID")  # never logged
        # OPTIONS-HOURS-20261104: injectable ET clock for the
        # options market-hours refusal in submit_order.
        self._now_fn = now_fn

    def _headers(self):
        return {"APCA-API-KEY-ID": self._key_id or "",
                "APCA-API-SECRET-KEY": self._env.get("ALPACA_SECRET_KEY", "")}

    # Network methods are exercised only in live paper sessions (A9 phase);
    # the core platform's proofs run against FakeBroker through the same
    # submit/read-back interface.
    def submit_order(self, client_order_id, symbol, side, qty, order_type,
                     limit_price=None, time_in_force="day",
                     position_intent=None, stop_price=None):
        # PF-DOOR-20261104: PF_-prefixed symbols are Kraken futures
        # contract keys (the free_kraken sleeves' native instruments).
        # Alpaca lists no such asset — proven live 2026-11-03: every
        # PF_ADAUSD submit returned HTTP 422 code 42210000 "asset
        # PF_ADAUSD not found" (6 intents, 30 dispatcher rows). The
        # verdict is deterministic, so the door returns it locally in
        # the broker's own shape; dispatcher journaling, terminal-422
        # handling and pending behaviour are unchanged, minus the
        # wire call. FakeBroker is untouched: the kraken e2e contract
        # (a Kraken-door design) still dispatches PF_ in tests.
        if isinstance(symbol, str) and symbol.startswith("PF_"):
            import json as _json
            from .netfetch import FetchError
            raise FetchError(
                422, self.base_url + "/v2/orders",
                body=_json.dumps(
                    {"code": 42210000,
                     "message": f"asset {symbol} not found"}))
        # OPTIONS-HOURS-20261104: Alpaca options trade only in the
        # regular session (Mon-Fri 09:30-16:00 ET); an options MARKET
        # order submitted outside it draws a deterministic HTTP 422
        # ("options market orders are only allowed during market
        # hours" — 220 broker rows on 2026-11-03 evening from five
        # sleeves re-emitting the same SPY put exits). The door
        # returns that verdict locally. Scoped to the proven shape
        # only: OCC symbol + market type. Options limit orders rest
        # and equity market orders are queued by the broker, so both
        # still reach the wire; holidays/early closes keep the
        # broker itself as the backstop.
        if order_type == "market" and isinstance(symbol, str):
            from .models import OCC_RE
            if OCC_RE.match(symbol):
                from datetime import datetime
                from zoneinfo import ZoneInfo
                _now = (self._now_fn() if self._now_fn is not None
                        else datetime.now(ZoneInfo("America/New_York")))
                if _now.tzinfo is None:
                    _now = _now.replace(tzinfo=ZoneInfo("America/New_York"))
                _et = _now.astimezone(ZoneInfo("America/New_York"))
                if not options_market_open(_et):
                    import json as _json
                    from .netfetch import FetchError
                    raise FetchError(
                        422, self.base_url + "/v2/orders",
                        body=_json.dumps(
                            {"message": "options market orders are "
                                        "only allowed during market "
                                        "hours"}))
        # EGRESS-1: netfetch (http.client), not urllib — see
        # desk3/netfetch.py.
        # BLOCKED-EXIT-20261029: position_intent (and stop_price) now
        # reach the wire. Before this cure the body carried neither,
        # so the broker INFERRED intent from side + the real position:
        # a sell_to_close exit against a short/flat book was inferred
        # sell_to_open and margin-checked as a NEW short (HTTP 403
        # code 40310000 on every queued exit, 2026-10-29). With the
        # intent explicit, the broker validates the close against the
        # position instead of charging buying power for an open.
        import json
        from .netfetch import fetch_json
        body = {"symbol": symbol, "side": side, "qty": str(qty),
                "type": order_type, "time_in_force": time_in_force,
                "client_order_id": client_order_id}
        if limit_price is not None:
            body["limit_price"] = str(limit_price)
        if position_intent is not None:
            body["position_intent"] = position_intent
        if stop_price is not None:
            body["stop_price"] = str(stop_price)
        return fetch_json(
            self.base_url + "/v2/orders",
            headers={**self._headers(), "Content-Type": "application/json"},
            timeout=15, method="POST", body=json.dumps(body).encode())

    def get_order_by_client_id(self, client_order_id):
        # EGRESS-1: netfetch (http.client) — see desk3/netfetch.py.
        import urllib.parse
        from .netfetch import fetch_json
        q = urllib.parse.urlencode({"client_order_id": client_order_id})
        return fetch_json(
            self.base_url + "/v2/orders:by_client_order_id?" + q,
            headers=self._headers(), timeout=15)

    def list_orders(self, after_iso=None):
        """SWEEP-BATCH-20261104: the batch order read the fill
        sweep resolves against: all open orders plus closed orders
        submitted after `after_iso`, the closed side paged up to 4
        pages of 500 by advancing the `after` cursor. Returns
        {"open": [...], "closed": [...]} of raw broker order
        dicts. A non-list page ends paging rather than failing the
        read; the sweep's per-order fallback covers any gap."""
        import urllib.parse

        def _q(params):
            return "/v2/orders?" + urllib.parse.urlencode(params)

        opened = self._get(_q({"status": "open", "limit": 500}))
        closed = []
        after = after_iso
        for _ in range(4):
            params = {"status": "closed", "limit": 500,
                      "direction": "asc"}
            if after:
                params["after"] = after
            page = self._get(_q(params))
            if not isinstance(page, list) or not page:
                break
            closed.extend(page)
            if len(page) < 500:
                break
            last = page[-1].get("submitted_at") or \
                page[-1].get("created_at")
            if not last or last == after:
                break
            after = last
        return {"open": opened if isinstance(opened, list) else [],
                "closed": closed}

    def _get(self, path):
        # EGRESS-1: netfetch (http.client) — see desk3/netfetch.py.
        from .netfetch import fetch_json
        return fetch_json(self.base_url + path, headers=self._headers(),
                          timeout=15)

    def get_positions(self):
        """Read-back of record for reconcile: {SYM: qty}."""
        return {p["symbol"]: float(p["qty"])
                for p in self._get("/v2/positions")}

    def get_positions_snapshot(self):
        """Snapshot-shape positions (POS-SHAPE-20261026): the cycle
        snapshot contract is a LIST of canonical records
        {symbol, qty, avg_price} — the shape every fixture serves and
        every bridge/adapter consumes (p.get('qty'), p['symbol']).
        avg_price maps from Alpaca's avg_entry_price. get_positions()
        above keeps the reconcile dict shape and stays untouched."""
        return [{"symbol": p["symbol"], "qty": float(p["qty"]),
                 "avg_price": float(p.get("avg_entry_price") or 0)}
                for p in self._get("/v2/positions")]

    def get_account(self):
        acct = self._get("/v2/account")
        # FEED-EQUITY-20261031: equity fields ride along, not just
        # cash. The terminal feed's account block is built from
        # this record; when it carried only cash, no feed anywhere
        # carried desk equity and Friday grading could not
        # certify the desk week. Missing fields stay None, never
        # fabricated.
        def _f(key):
            v = acct.get(key)
            return float(v) if v is not None else None
        return {"cash": float(acct.get("cash") or 0),
                "equity": _f("equity"),
                "last_equity": _f("last_equity"),
                # ORDER-HOLD-CASH-20261108: the position market
                # value rides along so the cycle can derive cash
                # encumbered by open orders from the broker's own
                # identity (equity - cash - position_market_value);
                # reconcile names that hold on its cash row.
                "position_market_value": _f("position_market_value"),
                "long_market_value": _f("long_market_value"),
                "short_market_value": _f("short_market_value"),
                "buying_power": _f("buying_power"),
                # CSP-PREFLIGHT-20261104: the options buying power
                # the dispatcher's cash-secured-put gate reads.
                "options_buying_power": _f("options_buying_power"),
                "portfolio_value": _f("portfolio_value"),
                "status": acct.get("status")}

    def _walk_activities(self, after_iso):
        """FEE-CFEE-WALK-20261110: THE page_token walk over the
        generic activities endpoint, to EXHAUSTION, shared by the
        fee total and the CFEE evidence. The pre-cure walks each
        carried a 60-page cap (page_size 100 = 6,000 activities):
        invisible while the account was young, and the direct
        cause of DSK-4 (the fee walk stopped at activity 6,000 of
        14,317 on 2026-11-05, undercounting FEE by $104.19) and of
        the first-6,000 CFEE figure (-$2,146.87) that inherited the
        same truncation. Termination is proven, not capped: rows
        arrive in ascending id order and page_token advances to
        the last row's id, so the walk ends exactly when a page is
        short (< page_size) or empty, or when the id cursor stops
        advancing / repeats (a pathological broker page shape), in
        which case the rows gathered so far stand and the walk
        still terminates."""
        import urllib.parse
        rows_all, token = [], None
        while True:
            q = {"after": after_iso, "page_size": 100,
                 "direction": "asc"}
            if token:
                q["page_token"] = token
            rows = self._get("/v2/account/activities?"
                             + urllib.parse.urlencode(q))
            if not isinstance(rows, list) or not rows:
                break
            rows_all.extend(rows)
            last = rows[-1].get("id")
            if len(rows) < 100 or last is None or last == token:
                break
            token = last
        return rows_all

    def get_fees_total(self, after_iso):
        """CASH-RECONCILE-20261030: signed sum of broker FEE
        activities (CAT and REG regulatory fees on sell proceeds)
        since `after_iso`. These move broker cash without any fill,
        so the reconcile cash expectation must include them (proven
        live 2026-10-30: -223.71 across the epoch, against a 223.72
        unexplained cash residue).

        FEE-WALK-20261103 (root cause of the 2026-11-03 desk-wide
        cash halt): the original walk paged the typed FEE endpoint
        by advancing `after` to the max activity DATE of each page.
        At day granularity that silently drops every same-date row
        past the first page: live census 2026-11-03 showed 166 FEE
        rows totalling -243.93 while this walk returned -11.62.
        The FEE-WALK cure moved the walk to the page_token route
        over the generic activities endpoint, summing FEE rows
        only, deduped by activity id, under a 60-page cap.

        FEE-CFEE-WALK-20261110 (W4, DSK-3/DSK-4): two cures land.
        (1) The "CFEE is deliberately NOT summed here" premise is
        REFUTED on the full record: the 2026-11-10 exhaustive
        14,317-row activity walk closes the broker cash identity
        only with CFEE counted as a drain (journal fill prices
        equal GROSS execution prices, proven per-order against all
        335 heal imports at $0.00; the 2026-11-03 net-of-CFEE
        observation sampled the truncated first pages). This
        method now returns the signed sum over EVERY cash-moving
        activity type in COUNTED_CASH_ACTIVITY_TYPES (FEE and CFEE
        included); the value stays the broker_fees_usd term of the
        cash expectation and the method name is kept because
        cycle.py and the fixtures key on it. (2) The 60-page cap
        is GONE: the walk runs to exhaustion (DSK-4: the cap
        stopped the fee walk at activity 6,000 of 14,317,
        undercounting FEE by $104.19). The activity-type
        enumeration is audited on every walk:
        last_activity_type_audit carries the walked row count and
        the set of unenumerated types (empty when the enumeration
        is total); cycle.py names it on the reconcile record."""
        rows = self._walk_activities(after_iso)
        total, unknown = activity_type_audit(rows)
        self.last_activity_type_audit = {
            "rows_walked": len(rows), "unknown_types": unknown}
        return total

    def get_cfee_evidence(self, after_iso):
        """HALT-SCOPE-20261102: the live FILL + CFEE activity sets
        since `after_iso`, for reconcile's D1-CFEE known-item
        derivation. Only FILL and CFEE rows are returned; every
        other activity type is the fee total's business, not this
        derivation's. FEE-CFEE-WALK-20261110: the walk is the
        shared exhaustion walk (the pre-cure 60-page cap truncated
        this evidence at 6,000 activities too: the first-6,000
        CFEE sum, -$2,146.87, was cited as an evidence figure
        while the true epoch total is -$5,352.33)."""
        rows = self._walk_activities(after_iso)
        fills = [r for r in rows if r.get("activity_type") == "FILL"]
        cfee = [r for r in rows if r.get("activity_type") == "CFEE"]
        return {"fills": fills, "cfee": cfee}

    def get_open_orders(self):
        """BLOCKED-EXIT-20261029: resting orders at the broker (the
        dispatcher's exit pre-flight reads these so an exit whose
        close is already resting is never resubmitted — resubmission
        is what produced the 'insufficient qty available /
        held_for_orders' 403 class)."""
        return self._get("/v2/orders?status=open&limit=500")

    def cancel_order(self, order_id):
        # Alpaca answers a successful DELETE with 204 No Content —
        # an empty body fetch_json cannot parse (the cancel DID land
        # live 2026-10-29 while the parse error made it look failed).
        # Read bytes; an empty body is the success shape.
        from .netfetch import fetch_bytes
        raw = fetch_bytes(self.base_url + f"/v2/orders/{order_id}",
                          headers=self._headers(), timeout=15,
                          method="DELETE")
        if not raw:
            return {"id": order_id, "status": "canceled"}
        import json
        return json.loads(raw)


class FakeBroker:
    """In-memory paper broker. submit_order only ACKs; get_order_by_client_id
    is the read-back of record. fill_mode='filled' fills at the configured
    price on read-back; 'pending' never fills (proves ACK != fill)."""

    # BLOCKED-EXIT-20261029: a test double models a door, not the
    # live book, unless a test opts in (live_book = True) to exercise
    # the dispatcher's exit pre-flight reconciliation.
    live_book = False

    def __init__(self, prices=None, fill_mode="filled"):
        self.prices = prices or {}
        self.fill_mode = fill_mode
        self.orders = {}  # client_order_id -> order dict
        self.submit_count = 0
        self.positions = {}  # symbol -> qty, from filled read-backs
        self.cash = None     # set by tests/live harness when modelling cash
        self.fees_usd = 0.0  # CASH-RECONCILE-20261030 fee model

    def get_fees_total(self, after_iso):
        """Parity with PaperDoor (CASH-RECONCILE-20261030): the
        signed fee total the fixture models, default zero."""
        return float(self.fees_usd)

    def get_cfee_evidence(self, after_iso=None):
        """Parity with PaperDoor (HALT-SCOPE-20261102): the FILL +
        CFEE activity sets the fixture models via the
        fills_activities / cfee_activities attributes, default
        empty (no known item can be derived)."""
        return {"fills": list(getattr(self, "fills_activities", [])),
                "cfee": list(getattr(self, "cfee_activities", []))}

    def submit_order(self, client_order_id, symbol, side, qty, order_type,
                     limit_price=None, time_in_force="day",
                     position_intent=None, stop_price=None):
        if client_order_id in self.orders:  # broker-side idempotency
            return self.orders[client_order_id]
        self.submit_count += 1
        order = {"id": f"fake-{self.submit_count}",
                 "client_order_id": client_order_id, "symbol": symbol,
                 "side": side, "qty": qty, "status": "accepted",
                 # OVERNIGHT-AUCTION-20261116 (B0-5): record the
                 # order shape in parity with the PaperDoor wire
                 # body, so a read-back can prove what was
                 # submitted (the auction form lives in these two
                 # fields: type market, tif cls/opg).
                 "type": order_type, "time_in_force": time_in_force,
                 "position_intent": position_intent,
                 "stop_price": stop_price}
        self.orders[client_order_id] = order
        return order

    def get_open_orders(self):
        """Resting = accepted and not yet applied by a fill read-back."""
        return [dict(o) for o in self.orders.values()
                if not o.get("_applied")
                and o.get("status") in ("accepted", "new", "pending_new")]

    def cancel_order(self, order_id):
        for o in self.orders.values():
            if o.get("id") == order_id:
                o["status"] = "canceled"
                return o
        raise KeyError(order_id)

    def get_order_by_client_id(self, client_order_id):
        order = dict(self.orders[client_order_id])
        if self.fill_mode == "filled":
            order["status"] = "filled"
            order["filled_qty"] = order["qty"]
            order["filled_avg_price"] = self.prices.get(order["symbol"], 0.0)
            if not order.get("_applied"):
                signed = float(order["qty"]) * (1 if order["side"] == "buy" else -1)
                sym = order["symbol"]
                self.positions[sym] = self.positions.get(sym, 0.0) + signed
                if abs(self.positions[sym]) <= 1e-9:
                    del self.positions[sym]
                self.orders[client_order_id]["_applied"] = True
        return order

    def list_orders(self, after_iso=None):
        """SWEEP-BATCH-20261104 parity with PaperDoor: every known
        order in read-back shape (the same fill application as
        get_order_by_client_id, so positions move identically),
        partitioned open vs closed by status."""
        terminal = ("filled", "canceled", "cancelled", "expired",
                    "rejected")
        opened, closed = [], []
        for coid in list(self.orders):
            order = self.get_order_by_client_id(coid)
            if str(order.get("status") or "") in terminal:
                closed.append(order)
            else:
                opened.append(order)
        return {"open": opened, "closed": closed}

    def get_positions(self):
        return dict(self.positions)

    def get_positions_snapshot(self):
        """Parity with PaperDoor (POS-SHAPE-20261026): canonical LIST
        of {symbol, qty, avg_price}; avg_price from the prices map."""
        return [{"symbol": sym, "qty": float(qty),
                 "avg_price": float(self.prices.get(sym, 0.0))}
                for sym, qty in self.positions.items()]

    def get_account(self):
        # FEED-EQUITY-20261031 parity with PaperDoor: equity is
        # the modelled equity when a test sets it, else the cash
        # model, else None (never fabricated).
        equity = getattr(self, "equity", None)
        if equity is None:
            equity = self.cash
        return {"cash": self.cash, "equity": equity,
                "last_equity": getattr(self, "last_equity", None),
                # ORDER-HOLD-CASH-20261108 parity with PaperDoor:
                # fixtures model no position market value unless a
                # test sets it, so the cycle's hold derivation
                # stays uncomputed (None) rather than fabricated.
                "position_market_value": getattr(
                    self, "position_market_value", None),
                "long_market_value": getattr(
                    self, "long_market_value", None),
                "short_market_value": getattr(
                    self, "short_market_value", None),
                "buying_power": getattr(self, "buying_power", None),
                # CSP-PREFLIGHT-20261104 parity with PaperDoor.
                "options_buying_power": getattr(
                    self, "options_buying_power", None),
                "portfolio_value": equity,
                "status": "ACTIVE"}
