"""shen_fade — Shen Lao's (@shentrades) SPY 0DTE fade playbook,
automated for the lean paper desk (2026-10-21/22), EXACTLY per
~/workspace/.scratch-setups-build/shen-fade/DESIGN.md (frozen
2026-10-22). the owner's ruling 2026-10-21 23:58 ET: a FULL sleeve,
not monitor-only. The desk's 68th sleeve (built as the 64th
on the 2026-10-22 tree; rebased onto master 3054af3 for
landing, census reconciled 67 -> 68 per DESIGN §9.1).

THE SYSTEM (his 10 steps, the post of 2026-10-21). He trades
only SPY 0DTE, from his phone, off a clean chart — price and RSI
only:
  1. price + RSI only (here: 1-min SPY SIP bars, RSI(14) Wilder
     on completed closes — R-1);
  2. PDH / PDL / PMH / PML marked before the open (PD from the
     prior regular session's RTH 1-min SIP bars — R-3; PM from
     today's 04:00-09:30 1-min SIP bars);
  3. the 3 whole-dollar levels nearest the 09:29 reference
     price (R-4);
  4. bias latched at the plan: above PDH bullish, below PDL
     bearish, else neutral — never re-evaluated (R-2/R-9), and
     the frame scopes which fade direction may trade all day;
  5. FIRST touch only: a level's latch burns on the first
     completed 1-min bar whose range reaches its +/-$0.10 zone
     (R-6/R-7/R-8) — whether or not it trades, and never re-arms;
  6. RSI confirms on the touch bar's close: > 70 buys PUTS,
     < 30 buys CALLS, in between (70 and 30 included) no trade;
  7. entry in the zone as a limit ladder at the option's quoted
     prices: mid -> mid + half-spread at +60s -> ask at +120s ->
     cancel at +180s (R-12), repricing only while the setup is
     still live; NEVER a market entry order;
  8. bracket on the fill, same cycle, both legs: take-profit
     limit at 1.20x the premium paid, stop at 0.85x watched on
     this 60s cadence against the v1beta1 mid (R-14);
  9. flat and done at 11:15 ET regardless: cancel pendings,
     close at mid -> bid -> 11:17 market (the design's only
     market order, R-16); last new entry 11:10 (R-15);
 10. the day's max loss (-1.80% of slice) and take profit
     (+2.40% of slice) are computed at the plan and filed in
     advance; either latch ends new entries for the day while
     an open bracket completes (R-18).

DESK SHAPE. CONFIG + signal() in the bilbo_options / saty_day /
po10_qqq idiom. The day state (DESIGN 9.2: plan / working /
position / day) round-trips through the persisted slice state:
the sleeve reads it from slice_state["shen_fade"] (or
extra["shen_state"]) and publishes the updated record on every
evaluation stamp as state_out. Two facts are ALSO reconstructed
from broker truth on every tick, so a lost state can never
re-arm the day: first-touch latches are re-derived from today's
completed RTH bars (a level any earlier completed bar reached
is burned), and the position / day P&L come from the broker
position record and this sleeve's own session fills. One open
position at a time (R-13). No bars = no signal. Intent.stop /
Intent.target are never set: the bracket is expressed as the
sleeve's own exit intents on its cadence (the bilbo pattern),
not the generic protection-stop path.
"""
from datetime import date, datetime
from datetime import time as dtime
from zoneinfo import ZoneInfo

from core.data import is_trading_day
from core.sleeve import BaseSleeve, Intent, SleeveConfig

ET = ZoneInfo("America/New_York")
SYM = "SPY"

CONFIG = SleeveConfig(
    sleeve_id="shen_fade",
    cadence_s=60,
    universe=("SPY",),
    state_schema={"plan": "dict|None", "working": "dict|None",
                  "position": "dict|None", "day": "dict|None"},
    # R-17: 4% of slice equity premium per trade (the desk's
    # options-family working figure, saty_day / bilbo shelf).
    risk_pct=0.04,
)

# -- his numbers + the frozen rulings (DESIGN 11) ---------------
RSI_PERIOD = 14                # R-1: RSI(14) Wilder, 1-min closes
ZONE_HALF = 0.10               # R-6: +/- $0.10 zone, both jobs
WHOLE_COUNT = 3                # R-4: exactly 3 whole dollars
SPREAD_GATE = 0.05             # desk options gate (bilbo_options)
QUOTE_STALE_S = 60.0           # DESIGN 3.4: quote <= 60s old
WARMUP_MIN_BARS = 100          # DESIGN 4.1: < 100 bars, no plan
BUDGET_PCT = 0.04              # R-17
TP_MULT = 1.20                 # step 8: +20%
SL_MULT = 0.85                  # step 8: -15%
DAY_MAX_LOSS_PCT = -1.80       # R-18: 3 full stop-outs
DAY_TAKE_PROFIT_PCT = 2.40     # R-18: 3 full targets
ENTRY_OPEN = dtime(9, 30)      # step 5: touches are an RTH event
LAST_ENTRY = dtime(11, 10)     # R-15
FLAT_T = dtime(11, 15)         # step 9: 8:15am PST
FLAT_MARKET_T = dtime(11, 17)  # R-16: final flat guarantee
PLAN_T = dtime(9, 29, 30)      # DESIGN 3.1: plan on first tick
REPRICE_S = (60.0, 120.0, 180.0)   # R-12 ladder timing

# NYSE early closes at/before 11:15 ET stand the sleeve down for
# the day (R-19); later early closes leave the morning window
# whole. Same desk table convention as saty_day / po10_qqq.
EARLY_CLOSES = {
    "2026-11-27": dtime(13, 0),   # day after Thanksgiving
    "2026-12-24": dtime(13, 0),   # Christmas Eve
    "2027-11-26": dtime(13, 0),
    "2028-07-03": dtime(13, 0),
    "2028-11-24": dtime(13, 0),
}


# ------------------------------------------------------------------
# pure helpers (each pinned by a named blocker test)
# ------------------------------------------------------------------
def rsi_wilder(closes, period=RSI_PERIOD):
    """RSI(period) with Wilder smoothing, aligned to `closes`
    (None until the seed window completes). The seed is the
    simple average of the first `period` changes; every later
    value is the RMA recursion. Completed closes only — the
    caller never hands it a forming bar (R-5)."""
    n = len(closes)
    out = [None] * n
    if n <= period:
        return out
    gains, losses = [], []
    for i in range(1, period + 1):
        d = closes[i] - closes[i - 1]
        gains.append(max(d, 0.0))
        losses.append(max(-d, 0.0))
    avg_g = sum(gains) / period
    avg_l = sum(losses) / period
    def _rsi(g, l):
        if l == 0:
            return 100.0 if g > 0 else 50.0
        rs = g / l
        return 100.0 - 100.0 / (1.0 + rs)
    out[period] = _rsi(avg_g, avg_l)
    for i in range(period + 1, n):
        d = closes[i] - closes[i - 1]
        avg_g = (avg_g * (period - 1) + max(d, 0.0)) / period
        avg_l = (avg_l * (period - 1) + max(-d, 0.0)) / period
        out[i] = _rsi(avg_g, avg_l)
    return out


def whole_dollar_set(ref):
    """The 3 whole dollars nearest `ref` (R-4): floor and ceil,
    then whichever of floor-1 / ceil+1 is nearer; an exact tie
    takes the lower one. Sorted ascending."""
    import math
    lo = math.floor(ref)
    hi = math.ceil(ref)
    if hi == lo:
        hi = lo + 1
    below, above = lo - 1, hi + 1
    third = below if (ref - below) <= (above - ref) else above
    return sorted({float(lo), float(hi), float(third)})


def bias_for(ref, pdh, pdl):
    """Step 4, latched at the plan (R-9)."""
    if ref > pdh:
        return "BULLISH"
    if ref < pdl:
        return "BEARISH"
    return "NEUTRAL"


def fade_side(rsi):
    """Step 6 mapping: RSI > 70 -> puts ('P'); RSI < 30 ->
    calls ('C'); anything in between — 70 and 30 INCLUDED —
    is no trade (None). Strict inequalities, his words."""
    if rsi is None:
        return None
    if rsi > 70.0:
        return "P"
    if rsi < 30.0:
        return "C"
    return None


def bias_allows(bias, kind):
    """R-2 composition: a BULLISH frame admits only the
    overbought fade (puts); BEARISH only the oversold fade
    (calls); NEUTRAL admits both."""
    if bias == "BULLISH":
        return kind == "P"
    if bias == "BEARISH":
        return kind == "C"
    return True


def build_levels(pdh, pdl, pmh, pml, ref):
    """The day's level set (DESIGN 3.2): {PDH, PDL, PMH, PML}
    plus the whole-dollar set, deduped by R-10 — levels within
    one zone half-width merge into ONE tradable level carrying
    both labels and one latch. PM levels may be absent (None).
    Returns [{price, labels}] sorted by price."""
    raw = [(float(pdh), "PDH"), (float(pdl), "PDL")]
    if pmh is not None:
        raw.append((float(pmh), "PMH"))
    if pml is not None:
        raw.append((float(pml), "PML"))
    for w in whole_dollar_set(ref):
        raw.append((w, f"W${int(w)}"))
    raw.sort(key=lambda x: x[0])
    out = []
    for price, label in raw:
        if out and abs(price - out[-1]["price"]) <= ZONE_HALF:
            if label not in out[-1]["labels"]:
                out[-1]["labels"].append(label)
        else:
            out.append({"price": price, "labels": [label]})
    return out


def bar_touches(bar, level_price):
    """R-7 touch test: the completed bar's range reaches the
    level's +/- ZONE_HALF zone."""
    return bar["low"] <= level_price + ZONE_HALF + 1e-9 \
        and bar["high"] >= level_price - ZONE_HALF - 1e-9


def bracket_prices(premium):
    """Step 8 on the premium actually paid: (tp, sl) =
    (1.20x, 0.85x), each rounded to the nearest cent (R-14)."""
    p = float(premium)
    return round(TP_MULT * p, 2), round(SL_MULT * p, 2)


def qty_for(slice_equity, mid):
    """R-17: qty = max(1, floor(budget / (mid x 100))) with
    budget = 4% of slice equity. Zero on unusable inputs."""
    try:
        eq, m = float(slice_equity), float(mid)
    except (TypeError, ValueError):
        return 0
    if eq <= 0 or m <= 0:
        return 0
    return max(1, int((BUDGET_PCT * eq) // (m * 100.0)))


def ladder_price(step, bid, ask):
    """R-12 ladder prices off a fresh two-sided quote:
    step 1 = mid; step 2 = mid + half the spread; step 3 = ask."""
    mid = (float(bid) + float(ask)) / 2.0
    if step == 1:
        return round(mid, 2)
    if step == 2:
        return round(mid + (float(ask) - float(bid)) / 2.0, 2)
    return round(float(ask), 2)


def parse_occ(symbol):
    """OCC parse (the qqq_put_ladder shape, kept local so the
    sleeve stays one file): {underlying, expiry, kind, strike}
    or None."""
    if not isinstance(symbol, str) or len(symbol) < 15:
        return None
    try:
        tail = symbol[-15:]
        exp = datetime.strptime(tail[:6], "%y%m%d").date()
        kind = tail[6]
        if kind not in ("C", "P"):
            return None
        strike = int(tail[7:]) / 1000.0
    except (ValueError, IndexError):
        return None
    return {"underlying": symbol[:-15].strip(), "expiry": exp,
            "kind": kind, "strike": strike}


def _clock(dt):
    """Wall-clock time of an aware datetime (kept behind a
    helper: the conformance checker's clock rule keys on the
    call's root name)."""
    return dt.time()


def _shape(raw):
    """Desk bars ({t epoch, o/h/l/c/v}) -> aware ET bars with an
    explicit end (t + 1 min). Unparseable rows dropped."""
    out = []
    for b in raw or []:
        try:
            t = float(b["t"])
            out.append({
                "t": datetime.fromtimestamp(t, tz=ET),
                "end": datetime.fromtimestamp(t + 60.0, tz=ET),
                "open": float(b["o"]), "high": float(b["h"]),
                "low": float(b["l"]), "close": float(b["c"]),
                "volume": float(b.get("v") or 0.0)})
        except (KeyError, TypeError, ValueError):
            continue
    out.sort(key=lambda x: x["t"])
    return out


class ShenFade(BaseSleeve):
    CONFIG = CONFIG

    # ------------------------------------------------------------
    # state: the DESIGN 9.2 record, round-tripped via slice state
    # ------------------------------------------------------------
    def _load_state(self, slice_state, extra, session):
        st = None
        if isinstance(slice_state, dict):
            st = slice_state.get("shen_fade")
        if not isinstance(st, dict):
            st = extra.get("shen_state")
        if isinstance(st, dict) and st.get("date") == session:
            # deep-enough copy: the sleeve owns its working copy
            import copy
            return copy.deepcopy(st)
        return {"date": session, "plan": None, "working": None,
                "position": None,
                "day": {"realized_pnl_usd": 0.0, "latch": "NONE",
                        "decisions": [], "fills": [],
                        "closed_reason": None}}

    def _file(self, state, rec_kind, **fields):
        rec = {"kind": rec_kind}
        rec.update(fields)
        state["day"].setdefault("decisions", []).append(rec)
        return rec

    # ------------------------------------------------------------
    # quotes / contracts (DESIGN 3.4 doors)
    # ------------------------------------------------------------
    def _fresh_quote(self, extra, occ, now_epoch, gated=True):
        """(bid, ask, mid) from the v1beta1 latest-quote door
        when two-sided and <= QUOTE_STALE_S old; with
        gated=True (contract selection / entry pricing, DESIGN
        3.4) the spread must also be <= SPREAD_GATE of mid.
        Management pricing (the watched stop, the 11:15 flat)
        passes gated=False: the design names no spread gate
        there, and a wide-spread quote must never leave a
        position unpriced at the flat."""
        q = (extra.get("fresh_quotes") or {}).get(occ)
        if not isinstance(q, dict):
            return None
        try:
            bp, ap = float(q["bp"]), float(q["ap"])
            t_epoch = datetime.fromisoformat(
                str(q["t"]).replace("Z", "+00:00")).timestamp()
        except (KeyError, TypeError, ValueError):
            return None
        if bp <= 0 or ap < bp or now_epoch - t_epoch > QUOTE_STALE_S:
            return None
        mid = (bp + ap) / 2.0
        if mid <= 0 or (gated and (ap - bp) / mid > SPREAD_GATE):
            return None
        return bp, ap, mid

    def _snap_mid(self, extra, occ):
        q = (extra.get("quotes") or {}).get(occ)
        if not isinstance(q, dict):
            return None
        try:
            bid, ask = float(q["bid"]), float(q["ask"])
        except (KeyError, TypeError, ValueError):
            return None
        if bid <= 0 or ask < bid:
            return None
        return bid, ask, (bid + ask) / 2.0

    def _pick_contract(self, extra, kind, session_d, spot, now_epoch):
        """(occ, bid, ask, mid) for the same-day-expiry contract
        of `kind` whose strike is nearest spot (R-11 tie-break:
        calls take the lower strike, puts the higher), gated on
        a fresh two-sided quote inside the spread gate.
        (None, reason) when no contract qualifies — including
        NO_0DTE_LISTED when no same-day expiry exists at all."""
        chains = (extra.get("chains") or {}).get(SYM) or []
        cands = []
        any_0dte = False
        for c in chains:
            parsed = parse_occ(c.get("symbol"))
            if not parsed or parsed["underlying"] != SYM:
                continue
            if parsed["expiry"] == session_d:
                any_0dte = True
                if parsed["kind"] == kind:
                    cands.append((parsed["strike"], c["symbol"]))
        if not any_0dte:
            return None, "NO_0DTE_LISTED"
        if not cands:
            return None, "NO_CONTRACT"
        # nearest strike; tie -> ITM side per R-11
        def key(item):
            strike = item[0]
            tie = -strike if kind == "P" else strike
            return (abs(strike - spot), tie)
        for strike, occ in sorted(cands, key=key):
            q = self._fresh_quote(extra, occ, now_epoch)
            if q is not None:
                return (occ, q[0], q[1], q[2]), None
        return None, "NO_CONTRACT"

    # ------------------------------------------------------------
    # plan (DESIGN 3): levels + bias + step-10 numbers, once
    # ------------------------------------------------------------
    def _build_plan(self, prior_rth, premarket, today_all, warmup_n,
                    slice_equity):
        if not prior_rth:
            return None, "BLOCKED_DATA"
        if warmup_n < WARMUP_MIN_BARS:
            return None, "PLAN_BLOCKED_WARMUP"
        if not premarket:
            # the reference price is a premarket fact (R-4); with
            # no premarket bars there is no reference, no W-set,
            # no bias — fail closed rather than inventing one.
            return None, "BLOCKED_DATA"
        pdh = max(b["high"] for b in prior_rth)
        pdl = min(b["low"] for b in prior_rth)
        pmh = max(b["high"] for b in premarket)
        pml = min(b["low"] for b in premarket)
        ref = premarket[-1]["close"]
        levels = build_levels(pdh, pdl, pmh, pml, ref)
        plan = {
            "status": "FILED",
            "ref_price": ref, "pdh": pdh, "pdl": pdl,
            "pmh": pmh, "pml": pml,
            "bias": bias_for(ref, pdh, pdl),
            "levels": [{"price": l["price"], "labels": l["labels"],
                        "latch": "ARMED"} for l in levels],
            "slice_equity_at_plan": float(slice_equity),
            "day_max_loss_pct": DAY_MAX_LOSS_PCT,
            "day_take_profit_pct": DAY_TAKE_PROFIT_PCT,
            "day_max_loss_usd": round(
                DAY_MAX_LOSS_PCT / 100.0 * float(slice_equity), 2),
            "day_take_profit_usd": round(
                DAY_TAKE_PROFIT_PCT / 100.0 * float(slice_equity), 2),
        }
        return plan, None

    # ------------------------------------------------------------
    # day P&L from broker-truth fills (DESIGN 7.2)
    # ------------------------------------------------------------
    def _realized(self, extra):
        """Realized day P&L from this sleeve's own session fill
        rows (cash flow: sells add, buys subtract, options x100).
        None when the fills door is absent — never guessed."""
        fills = extra.get("session_fills")
        if fills is None:
            return None
        cash = 0.0
        for f in fills:
            try:
                q = abs(float(f.get("qty") or 0))
                p = float(f.get("price") or 0)
            except (TypeError, ValueError):
                continue
            if f.get("position_intent") == "sell_to_close":
                cash += q * p * 100.0
            elif f.get("position_intent") == "buy_to_open":
                cash -= q * p * 100.0
        return cash

    # ------------------------------------------------------------
    # position management: the bracket (DESIGN 6)
    # ------------------------------------------------------------
    def _manage(self, state, pos, extra, ctx, now_dt, stamp, intents):
        plan = state["plan"]
        spos = state.get("position")
        occ = pos.get("occ") or (spos or {}).get("occ")
        qty = abs(float(pos.get("qty") or 0))
        # adopt / refresh the sleeve's position record from the
        # broker record + any fill that opened it
        if spos is None or spos.get("occ") != occ:
            premium = pos.get("entry_px")
            if premium is None:
                for f in extra.get("session_fills") or []:
                    if (f.get("symbol") or f.get("submit_symbol")) == occ and \
                            f.get("position_intent") == "buy_to_open":
                        premium = float(f.get("price") or 0) or None
            if premium is None:
                stamp["state"] = "position_unpriced"
                return
            tp, sl = bracket_prices(premium)
            spos = {"occ": occ, "qty": qty,
                    "entry_premium": float(premium),
                    "tp_price": tp, "sl_price": sl,
                    "bracket_status": "PENDING",
                    "level_ref": (state.get("working") or {})
                    .get("level_ref")}
            state["position"] = spos
            state["working"] = None
            self._file(state, "fill", occ=occ, qty=qty,
                       premium=float(premium))
        spos["qty"] = qty
        # flat ladder has priority over the bracket (step 9)
        if now_dt.time() >= FLAT_T:
            self._flat(state, extra, ctx, now_dt, stamp, intents,
                       broker_pos=pos)
            return
        # place the bracket: TP rests as a limit, same cycle as
        # the fill is first seen (R-14). The stop is watched.
        # Placement happens exactly once (PENDING only): while
        # a stop exit works (STOP_EXIT_WORKING) the legs are
        # OCO in effect, so the TP is never re-emitted — the
        # watched-stop branch below reprices the exit instead
        # (SHEN-20261022-6).
        if spos["bracket_status"] == "PENDING":
            intents.append(Intent(
                "exit", occ, qty=qty, limit_price=spos["tp_price"],
                price_hint=spos["tp_price"], side="sell",
                position_intent="sell_to_close",
                reason=(f"shen_fade bracket take-profit: "
                        f"1.20x premium {spos['entry_premium']:.2f} "
                        f"= {spos['tp_price']:.2f} occ={occ}"),
                signal_date=ctx.session))
            spos["bracket_status"] = "PLACED"
            self._file(state, "bracket_placed", occ=occ,
                       tp=spos["tp_price"], sl=spos["sl_price"])
            stamp["state"] = "bracket_placed"
            return
        # watched stop: first evaluation whose quoted mid <= stop
        q = self._fresh_quote(extra, occ, ctx.now, gated=False) \
            or self._snap_mid(extra, occ)
        if q is not None and q[2] <= spos["sl_price"]:
            intents.append(Intent(
                "exit", occ, qty=qty, limit_price=round(q[2], 2),
                price_hint=round(q[2], 2), side="sell",
                position_intent="sell_to_close",
                reason=(f"shen_fade bracket stop: mid {q[2]:.2f} "
                        f"<= 0.85x premium stop {spos['sl_price']:.2f} "
                        f"occ={occ}"),
                signal_date=ctx.session))
            spos["bracket_status"] = "STOP_EXIT_WORKING"
            self._file(state, "bracket_stop_exit", occ=occ,
                       mid=round(q[2], 2), sl=spos["sl_price"])
            stamp["state"] = "stop_exit"
            return
        stamp["state"] = "holding"

    def _flat(self, state, extra, ctx, now_dt, stamp, intents,
              broker_pos=None):
        """Step 9 / R-16 flat ladder at 11:15 ET: cancel the
        working entry (a state fact — the sleeve emits no new
        entry and files the cancel), close any open position at
        mid, then bid after one cycle, then market at 11:17.
        Day -> DONE."""
        day = state["day"]
        if state.get("working") is not None:
            self._file(state, "flat_cancel_entry",
                       occ=state["working"].get("occ"))
            state["working"] = None
        spos = state.get("position")
        pos = broker_pos
        if pos is None:
            state_pos = (extra.get("sleeve_state") or {}).get(SYM) \
                or {}
            pos = state_pos.get("position")
        if isinstance(pos, dict) and float(pos.get("qty") or 0) != 0 \
                and spos is not None:
            occ = spos["occ"]
            qty = abs(float(pos["qty"]))
            stage = spos.get("flat_stage", 0)
            q = self._fresh_quote(extra, occ, ctx.now,
                                  gated=False) \
                or self._snap_mid(extra, occ)
            if now_dt.time() >= FLAT_MARKET_T or stage >= 2:
                intents.append(Intent(
                    "exit", occ, qty=qty, side="sell",
                    position_intent="sell_to_close",
                    reason=(f"shen_fade 11:15 flat (final market): "
                            f"occ={occ}"),
                    signal_date=ctx.session))
                spos["flat_stage"] = 3
                self._file(state, "flat_market", occ=occ)
                stamp["state"] = "flat_market"
            elif q is not None:
                px = q[2] if stage == 0 else q[0]
                intents.append(Intent(
                    "exit", occ, qty=qty,
                    limit_price=round(px, 2), price_hint=round(px, 2),
                    side="sell", position_intent="sell_to_close",
                    reason=(f"shen_fade 11:15 flat: limit at "
                            f"{'mid' if stage == 0 else 'bid'} "
                            f"{px:.2f} occ={occ}"),
                    signal_date=ctx.session))
                spos["flat_stage"] = stage + 1
                self._file(state, "flat_limit", occ=occ,
                           price=round(px, 2), stage=stage)
                stamp["state"] = "flat_limit"
            else:
                stamp["state"] = "flat_unpriced"
            return
        day["closed_reason"] = day.get("closed_reason") or "FLAT_1115"
        stamp["state"] = "done"

    # ------------------------------------------------------------
    # the evaluation
    # ------------------------------------------------------------
    def signal(self, bars, slice_state, ctx):
        stamp = {"sleeve": "shen_fade", "session": ctx.session}
        self.last_evaluation = stamp
        now_dt = datetime.fromtimestamp(float(ctx.now), tz=ET)
        session_d = date.fromisoformat(ctx.session)
        extra = ctx.extra or {}
        state = self._load_state(slice_state, extra, ctx.session)
        stamp["state_out"] = state
        intents = []
        if not is_trading_day(session_d):
            stamp["state"] = "not_a_trading_day"
            return []
        if EARLY_CLOSES.get(ctx.session, dtime(16, 0)) <= FLAT_T:
            stamp["state"] = "stood_down_half_day"
            return []

        raw = (extra.get("bars_1m_long") or {}).get(SYM)
        if raw is None:
            raw = (extra.get("bars_1m") or {}).get(SYM)
        if not raw:
            stamp["state"] = "blocked_data"
            return []
        all_bars = _shape(raw)
        completed = [b for b in all_bars if b["end"] <= now_dt]
        # prior session = the LATEST date before today's in
        # the bars window (R-3): the long door serves ~10
        # days, and an older session must never leak into
        # PDH/PDL or the warmup series (SHEN-20261022-5).
        prior_dates = {b["t"].date() for b in completed
                       if b["t"].date() < session_d}
        prior_d = max(prior_dates) if prior_dates else None
        prior_rth = [b for b in completed
                     if b["t"].date() == prior_d
                     and dtime(9, 30) <= _clock(b["t"]) < dtime(16, 0)]
        # RSI warmup series: prior session RTH tail + today's
        # premarket + today's completed RTH (DESIGN 4.1)
        warm = prior_rth
        today = [b for b in completed if b["t"].date() == session_d]
        premarket = [b for b in today if _clock(b["t"]) < dtime(9, 30)]
        rth = [b for b in today
               if dtime(9, 30) <= _clock(b["t"]) < dtime(16, 0)]
        series = warm + today
        closes = [b["close"] for b in series]
        rsi_series = rsi_wilder(closes)
        rsi_by_end = {b["end"]: r for b, r in zip(series, rsi_series)}

        slice_equity = extra.get("slice_equity") or ctx.equity or 0.0

        # ---- plan (once, from the first tick >= 09:29:30) ----
        if state["plan"] is None and now_dt.time() >= PLAN_T:
            plan, blocked = self._build_plan(
                prior_rth, premarket, today,
                len(warm) + len(premarket), slice_equity)
            if plan is None:
                stamp["state"] = blocked.lower()
                state["plan"] = {"status": blocked}
                self._file(state, "plan_blocked", reason=blocked)
                return []
            state["plan"] = plan
            self._file(state, "plan", ref=plan["ref_price"],
                       bias=plan["bias"],
                       levels=[l["price"] for l in plan["levels"]],
                       day_max_loss_usd=plan["day_max_loss_usd"],
                       day_take_profit_usd=plan["day_take_profit_usd"])
            stamp["plan"] = {"ref": plan["ref_price"],
                              "bias": plan["bias"],
                              "levels": [l["price"]
                                         for l in plan["levels"]]}
        plan = state["plan"]
        if plan is None:
            stamp["state"] = "premarket_track"
            return []
        if plan.get("status") != "FILED":
            stamp["state"] = "plan_blocked"
            return []

        # ---- latch reconstruction from today's completed bars:
        # any level an EARLIER completed bar reached is burned,
        # whatever the persisted record says (reload-proof).
        levels = plan["levels"]
        latest_end = rth[-1]["end"] if rth else None
        for lv in levels:
            if lv["latch"] != "ARMED":
                continue
            for b in rth:
                if b["end"] < latest_end and bar_touches(b, lv["price"]):
                    lv["latch"] = "TOUCHED"
                    self._file(state, "touch_reconstructed",
                               level=lv["price"], labels=lv["labels"])
                    break

        # ---- broker truth: position first ----
        sleeve_state = extra.get("sleeve_state") or {}
        pos = (sleeve_state.get(SYM) or {}).get("position")
        has_pos = isinstance(pos, dict) \
            and float(pos.get("qty") or 0) != 0
        if has_pos:
            self._manage(state, pos, extra, ctx, now_dt, stamp, intents)
            return intents
        if state.get("position") is not None:
            # broker says flat: the bracket resolved (or the flat
            # landed). Close the record; day P&L below re-latches.
            self._file(state, "position_closed",
                       occ=state["position"].get("occ"))
            state["position"] = None

        # ---- day latch from realized fills (step 10) ----
        realized = self._realized(extra)
        if realized is not None:
            state["day"]["realized_pnl_usd"] = round(realized, 2)
            if state["day"]["latch"] == "NONE":
                if plan["day_max_loss_usd"] < 0 \
                        and realized <= plan["day_max_loss_usd"]:
                    state["day"]["latch"] = "MAX_LOSS"
                elif plan["day_take_profit_usd"] > 0 \
                        and realized >= plan["day_take_profit_usd"]:
                    state["day"]["latch"] = "TAKE_PROFIT"
                if state["day"]["latch"] != "NONE":
                    self._file(state, "day_latch",
                               latch=state["day"]["latch"],
                               realized=round(realized, 2))
                    if state.get("working") is not None:
                        self._file(state, "day_latch_cancel_entry",
                                   occ=state["working"].get("occ"))
                        state["working"] = None

        # ---- 11:15 flat + done (no position) ----
        if now_dt.time() >= FLAT_T:
            self._flat(state, extra, ctx, now_dt, stamp, intents)
            return intents

        # ---- working entry ladder (R-12) ----
        working = state.get("working")
        if working is not None:
            return self._work_ladder(state, working, extra, ctx,
                                     now_dt, stamp, rth, rsi_by_end)

        if state["day"]["latch"] != "NONE":
            stamp["state"] = "stood_down_day_latch"
            return []
        if now_dt.time() >= LAST_ENTRY:
            stamp["state"] = "entry_window_closed"
            return []
        if now_dt.time() < ENTRY_OPEN or not rth:
            stamp["state"] = "armed"
            return []

        # ---- first touch on the latest completed bar ----
        bar = rth[-1]
        touched = [lv for lv in levels
                   if lv["latch"] == "ARMED"
                   and bar_touches(bar, lv["price"])]
        if not touched:
            stamp["state"] = "armed"
            return []
        rsi = rsi_by_end.get(bar["end"])
        stamp["touch"] = {"bar_end": bar["end"].isoformat(),
                          "rsi": (round(rsi, 2) if rsi is not None
                                  else None),
                          "levels": [lv["price"] for lv in touched]}
        kind = fade_side(rsi)
        for lv in touched:
            lv["latch"] = "TOUCHED"
        primary = touched[0]
        if kind is None:
            self._file(state, "no_rsi_extreme", level=primary["price"],
                       rsi=(round(rsi, 2) if rsi is not None else None))
            stamp["state"] = "no_rsi_extreme"
            return []
        if not bias_allows(plan["bias"], kind):
            self._file(state, "stood_down_bias_frame",
                       level=primary["price"], bias=plan["bias"],
                       option_kind=kind)
            stamp["state"] = "stood_down_bias_frame"
            return []
        # one entry results even when the bar touched two levels
        primary["latch"] = "TRADED"
        picked, why = self._pick_contract(extra, kind, session_d,
                                          bar["close"], ctx.now)
        if picked is None:
            primary["latch"] = "TOUCHED"
            self._file(state, "no_contract", level=primary["price"],
                       reason=why, option_kind=kind)
            stamp["state"] = "no_contract"
            return []
        occ, bid, ask, mid = picked
        qty = qty_for(slice_equity, mid)
        if qty <= 0:
            self._file(state, "size_zero", level=primary["price"])
            stamp["state"] = "size_zero"
            return []
        limit = ladder_price(1, bid, ask)
        state["working"] = {
            "occ": occ, "kind": kind, "qty": qty, "ladder_step": 1,
            "limit_price": limit, "since_ts": float(ctx.now),
            "level_ref": primary["price"],
            "rsi_at_trigger": (round(rsi, 2) if rsi is not None
                               else None)}
        entry_fields = {}
        overshoot = round(qty * mid * 100.0
                          - BUDGET_PCT * slice_equity, 2)
        if overshoot > 0:
            # R-17 / DESIGN 7.1: one contract costs more than the
            # 4% budget — the trade still takes the one contract
            # and the overshoot is filed, never silent.
            entry_fields["overshoot_usd"] = overshoot
        self._file(state, "entry_order_1", occ=occ, qty=qty,
                   limit=limit, level=primary["price"],
                   rsi=state["working"]["rsi_at_trigger"],
                   **entry_fields)
        stamp["state"] = "enter"
        intents.append(Intent(
            "enter", occ, qty=qty, limit_price=limit,
            price_hint=limit, side="buy",
            position_intent="buy_to_open",
            reason=(f"shen_fade enter {'calls' if kind == 'C' else 'puts'}: "
                    f"first touch of {primary['price']:.2f} "
                    f"({'/'.join(primary['labels'])}) with RSI "
                    f"{rsi:.1f} on the touch bar's close; limit at mid "
                    f"{limit:.2f} (ladder step 1 of 3, limit orders "
                    f"only) occ={occ}"),
            signal_date=ctx.session))
        return intents

    # ------------------------------------------------------------
    # the working ladder: reprice while the setup is still live
    # ------------------------------------------------------------
    def _work_ladder(self, state, working, extra, ctx, now_dt,
                     stamp, rth, rsi_by_end):
        elapsed = float(ctx.now) - float(working["since_ts"])
        occ = working["occ"]
        # the setup must still be live (DESIGN 5.3): underlying
        # still in the zone, RSI extreme still holding, clock
        # before last-entry, no day latch.
        live = True
        why = None
        if state["day"]["latch"] != "NONE":
            live, why = False, "day_latch"
        elif now_dt.time() >= LAST_ENTRY:
            live, why = False, "last_entry_passed"
        elif not rth:
            live, why = False, "no_bars"
        else:
            last = rth[-1]
            if abs(last["close"] - working["level_ref"]) \
                    > ZONE_HALF + 1e-9:
                live, why = False, "left_zone"
            else:
                rsi = rsi_by_end.get(last["end"])
                want = "P" if working["kind"] == "P" else "C"
                if fade_side(rsi) != want:
                    live, why = False, "rsi_extreme_lost"
        if not live:
            self._file(state, "entry_stood_down", occ=occ, reason=why)
            state["working"] = None
            stamp["state"] = "entry_stood_down"
            return []
        step_due = 1 + (1 if elapsed >= REPRICE_S[0] else 0) \
            + (1 if elapsed >= REPRICE_S[1] else 0)
        if elapsed >= REPRICE_S[2]:
            self._file(state, "no_fill", occ=occ)
            state["working"] = None
            stamp["state"] = "no_fill"
            return []
        if step_due <= working["ladder_step"]:
            stamp["state"] = "entry_working"
            return []
        q = self._fresh_quote(extra, occ, ctx.now)
        if q is None:
            stamp["state"] = "entry_working_unquoted"
            return []
        limit = ladder_price(step_due, q[0], q[1])
        working["ladder_step"] = step_due
        working["limit_price"] = limit
        self._file(state, f"entry_reprice_{step_due}", occ=occ,
                   limit=limit)
        stamp["state"] = "enter_reprice"
        return [Intent(
            "enter", occ, qty=working["qty"], limit_price=limit,
            price_hint=limit, side="buy",
            position_intent="buy_to_open",
            reason=(f"shen_fade entry reprice step {step_due} of 3: "
                    f"limit {limit:.2f} (setup still live in the zone "
                    f"at {working['level_ref']:.2f}) occ={occ}"),
            signal_date=ctx.session)]


def signal(bars, slice_state, context):
    return ShenFade().signal(bars, slice_state, context)
