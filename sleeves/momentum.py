"""Momentum — lean-desk port.

EXTRACTED from the old desk's momentum_sleeve.py. compute_rank and
new_buy_gates ported verbatim in behavior (the desk-halt leg is core
Risk's job now and is dropped here — named in ports/momentum.md);
plumbing is core-owned.

Strategy (old module): rank the universe by 126-session return on last
COMPLETED bars; eligibility = price >= $5, 20d avg dollar volume >=
$1M, SOXL skipped; take the top tenth (capped at 10 positions) when at
least 10 names are eligible. Review every 63 sessions. Sleeve cap 30%
of equity. Circuit breaker: close a position down 40% from entry.
New-buy gates (old, verbatim): Friday after 14:00 ET, last 5 December
weekdays, FOMC blackout (prior session + both days), VIX unavailable/
stale (>4 calendar days) fail-closed, VIX > 32, VIX +25% day spike,
SPY -8%/20d with VIX rising.

Inputs via context.extra:
  "sleeve_state": {SYM: {"position": {...} | None}}
  "vix": (close, prev_close, asof_iso, source) — absent = vix_unknown
  "review_due": bool — the 63-session review is due (core-persisted
    scheduling in core.bars_universe; M-MO1 cure 2026-10-18). At a due
    review, held names outside the current top set are sold (the old
    mode_rank sell set); absent/False = hold between reviews.
  "universe": optional override (default: bars keys)
Bars: daily dicts {"t","o","h","l","c","v"} ascending; the last bar is
treated as completed iff its date < context.session (old last_completed).
"""
from datetime import date, datetime, timedelta, timezone

from core.sleeve import BaseSleeve, Intent, SleeveConfig

LOOKBACK = 126
REVIEW_EVERY = 63
TOP_FRAC = 0.10
MAX_POSITIONS = 10

def _frac_qty(dollars, per_unit):
    """WS4-FRACTIONAL-20261114 (owner ruling 2026-11-14 17:08 ET:
    "It needs to buy stuff of any price"). Express a positive
    dollar budget as a fractional quantity, rounded DOWN to the
    door's 6dp precision, never up past the budget. Returns 0.0
    only when the budget itself is not positive or the unit
    price / per-share risk is not positive — the budget deciding,
    never the share price. Reconciliation with OBS-1 (2026-10-23,
    standing): the forced 1-share floor stays forbidden;
    whole-share rounding was the defect."""
    if dollars <= 0 or per_unit <= 0:
        return 0.0
    import math as _m
    return _m.floor((dollars / per_unit) * 1_000_000) / 1_000_000

SLEEVE_CAP = 0.30
MIN_PRICE = 5.0
MIN_DOLLAR_VOL = 1_000_000
SKIP_SYMBOLS = {"SOXL"}
BREAKER_DROP = 0.40
VIX_HIGH = 32.0
VIX_SPIKE = 0.25
SPY_DROP = -0.08
FOMC_2026 = [("2026-01-27", "2026-01-28"), ("2026-03-17", "2026-03-18"),
             ("2026-04-28", "2026-04-29"), ("2026-06-16", "2026-06-17"),
             ("2026-07-28", "2026-07-29"), ("2026-09-15", "2026-09-16"),
             ("2026-10-27", "2026-10-28"), ("2026-12-08", "2026-12-09")]

CONFIG = SleeveConfig(
    sleeve_id="momentum", cadence_s=300, universe=(),
    state_schema={"position": "dict|None",
                  "meta.last_review_spy_date": "str|None"}, risk_pct=None)


def _dates(bars):
    return [datetime.fromtimestamp(float(b["t"]) + 4 * 3600,
                                   tz=timezone.utc).date().isoformat()
            for b in bars]


def last_completed(bars, today):
    """Bars strictly before today's session (old last_completed shape)."""
    ds = _dates(bars)
    return [b for b, d in zip(bars, ds) if d < today]


def compute_rank(bars_by_sym, today):
    """Verbatim port of the old compute_rank (corrupt-bar guards incl.)."""
    comp = {}
    for sym, bars in bars_by_sym.items():
        cb = last_completed(bars, today)
        if len(cb) >= LOOKBACK + 1:
            comp[sym] = cb
    spy_all = sorted(set(_dates(last_completed(bars_by_sym["SPY"], today)))) \
        if "SPY" in bars_by_sym else []
    eligible = []
    for sym, cb in comp.items():
        if sym in SKIP_SYMBOLS:
            continue
        c = cb[-1].get("c")
        if not isinstance(c, (int, float)) or isinstance(c, bool):
            continue
        if c < MIN_PRICE:
            continue
        dv20 = sum(b["c"] * b["v"] for b in cb[-20:]
                   if isinstance(b.get("c"), (int, float))
                   and isinstance(b.get("v"), (int, float))) / 20.0
        if dv20 < MIN_DOLLAR_VOL:
            continue
        dc = cb[-LOOKBACK - 1].get("c")
        if not dc:
            continue
        eligible.append({"symbol": sym, "ret126": c / dc - 1, "price": c,
                         "dollar_vol_20d": dv20, "bars": len(cb)})
    eligible.sort(key=lambda r: r["ret126"], reverse=True)
    k = max(1, int(len(eligible) * TOP_FRAC))
    k = min(k, MAX_POSITIONS)
    top = eligible[:k] if len(eligible) >= 10 else []
    flagged = set()
    scored = []
    for sym, cb in comp.items():
        if len(cb) >= 252 + 21 + 1:
            n22, d274 = cb[-22].get("c"), cb[-274].get("c")
            if not n22 or not d274:
                continue
            scored.append((sym, n22 / d274 - 1))
    if scored:
        scored.sort(key=lambda t: t[1], reverse=True)
        kf = max(1, int(len(scored) * 0.20))
        flagged = {s for s, _ in scored[:kf]}
    for r in eligible:
        r["overlap_252_21_flag"] = r["symbol"] in flagged
    return {"eligible": eligible, "top": [t["symbol"] for t in top],
            "top_detail": top, "n_eligible": len(eligible),
            "spy_sessions": spy_all,
            "session_idx": (spy_all.index(spy_all[-1]) if spy_all else None)}


def new_buy_gates(now_date, now_hm, vix, spy_bars, today):
    """Old new_buy_gates minus the risk_gate desk-halt leg (core Risk).
    now_date: date; now_hm: (hour, minute) ET; vix: tuple or None."""
    blocks = []
    if now_date.weekday() == 4 and now_hm[0] >= 14:
        blocks.append(("friday_pm", "Friday after 14:00 ET"))
    dec_weekdays = []
    d = date(now_date.year, 12, 1)
    while d.month == 12:
        if d.weekday() < 5:
            dec_weekdays.append(d.isoformat())
        d += timedelta(days=1)
    if today in dec_weekdays[-5:]:
        blocks.append(("year_end", "last 5 sessions of the year"))
    for d1s, d2s in FOMC_2026:
        d1 = date.fromisoformat(d1s)
        prev = d1 - timedelta(days=1)
        while prev.weekday() >= 5:
            prev -= timedelta(days=1)
        if today in (prev.isoformat(), d1s, d2s):
            blocks.append(("fomc", "FOMC blackout %s/%s/%s"
                           % (prev.isoformat(), d1s, d2s)))
            break
    if not vix:
        blocks.append(("vix_unknown", "VIX unavailable; buys wait"))
        return blocks
    vclose, vprev, vasof, vsrc = vix
    if vclose is None:
        blocks.append(("vix_unknown", "VIX unavailable (%s); buys wait" % vsrc))
    else:
        stale = False
        try:
            asof = date.fromisoformat(str(vasof)[:10])
            if (now_date - asof).days > 4:
                stale = True
        except (TypeError, ValueError):
            stale = True
        if stale:
            blocks.append(("vix_stale", "VIX as-of %s is stale (%s); buys wait"
                           % (vasof, vsrc)))
        if vclose > VIX_HIGH:
            blocks.append(("vix_high", "VIX %.1f > %.1f" % (vclose, VIX_HIGH)))
        if vprev and (vclose / vprev - 1) > VIX_SPIKE:
            blocks.append(("vix_spike", "VIX +%0.0f%% on the day"
                           % ((vclose / vprev - 1) * 100)))
        sc = last_completed(spy_bars or [], today)
        if len(sc) >= 21:
            try:
                c1, c21 = float(sc[-1]["c"]), float(sc[-21]["c"])
                if not (c1 > 0 and c21 > 0):
                    raise ValueError("non-positive SPY close")
                r20 = c1 / c21 - 1
            except (TypeError, ValueError, KeyError):
                r20 = None
            if r20 is not None and r20 <= SPY_DROP and vprev and vclose > vprev:
                blocks.append(("spy_drop_vix_up",
                               "SPY %.1f%%/20d and VIX rising" % (r20 * 100)))
    return blocks


def enhance_enabled(extra):
    """ENH momentum (IMPROVE-momentum): every-pass top-set sell-test
    switch, ctx.extra['momentum_enhance']['enabled'], default ON;
    OFF restores the pre-change rule exactly (rotation exits only
    when review_due is supplied)."""
    ov = (extra or {}).get("momentum_enhance")
    if isinstance(ov, dict) and "enabled" in ov:
        return bool(ov["enabled"])
    if isinstance(ov, bool):
        return ov
    return True


def cost_bps(price):
    """Verbatim old cost_bps tiers (paper calibration reference)."""
    if price >= 20:
        return 0.0010
    if price >= 5:
        return 0.0025
    return 0.0050


class Momentum(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        extra = context.extra or {}
        state = extra.get("sleeve_state") or {}
        equity = float(context.equity or 0.0)
        today = context.session
        now_et = datetime.fromtimestamp(float(context.now),
                                        tz=timezone.utc)
        # ET wall time via the desk's fixed convention is core-injected
        # as extra["now_et"] when available; fall back to session date.
        now_date = date.fromisoformat(today)
        now_hm = tuple(extra.get("now_hm") or (16, 0))
        intents = []
        # circuit breaker exits first (old: close if down 40% from entry)
        held = {}
        for sym, st in state.items():
            p = (st or {}).get("position")
            if p:
                held[sym] = p
        for sym, p in held.items():
            bl = bars.get(sym) or []
            if not bl:
                continue
            last_px = float(bl[-1]["c"])
            entry_px = float(p.get("entry_px") or last_px)
            qty = float(p.get("qty") or 0)  # WS4: actual held qty
            if qty > 0 and entry_px > 0 and last_px <= entry_px * (1 - BREAKER_DROP):
                intents.append(Intent(
                    "exit", sym, qty=qty, price_hint=round(last_px, 2),
                    reason="momentum breaker: %.2f <= entry %.2f x %.2f"
                           % (last_px, entry_px, 1 - BREAKER_DROP)))
        # 63-session review rotation exits (M-MO1 cure 2026-10-18;
        # ports/momentum.md named this sell set unported because core
        # never supplied extra["review_due"] — core.bars_universe now
        # supplies it from the persisted last_review_spy_date stamp).
        # The old mode_rank sell set: at a due review, target is the
        # current top set and every held name outside it is sold.
        # Like the breaker, these are exits: the new-buy gates below
        # block buys only, never sells (old mode_fill law). Fail
        # closed on an empty top (compute_rank's >= 10-eligible
        # condition): no ranking, no rotation — never a liquidation
        # off an empty set. Names already breaker-exiting are not
        # re-staged.
        rank = None
        enh_on = enhance_enabled(extra)
        self._paired = []
        self.last_evaluation = {"sleeve": "momentum",
                                "enhance_switch": enh_on,
                                "paired": self._paired}
        # ENH: the existing top-set sell test runs on every rank pass,
        # not only when review_due is supplied (same fail-closed rule:
        # an empty top set sells nothing). Control = review-only.
        if extra.get("review_due") or (enh_on and held):
            rank = compute_rank(bars, today)
            top_set = set(rank["top"])
            if top_set:
                exited = {i.symbol for i in intents}
                for sym, p in held.items():
                    if sym in top_set or sym in exited:
                        continue
                    self._paired.append({
                        "symbol": sym, "review_due": bool(extra.get("review_due")),
                        "control": "exit" if extra.get("review_due") else "hold",
                        "treatment": "exit", "switch_on": enh_on})
                    bl = bars.get(sym) or []
                    if not bl:
                        continue
                    qty = int(float(p.get("qty") or 0))
                    if qty <= 0:
                        continue
                    last_px = float(bl[-1]["c"])
                    intents.append(Intent(
                        "exit", sym, qty=qty,
                        price_hint=round(last_px, 2),
                        reason="momentum review: held not in top set "
                               "at %s (top=%s)"
                               % (("%d-session review" % REVIEW_EVERY)
                                  if extra.get("review_due")
                                  else "every-pass top-set test (ENH)",
                                  ",".join(rank["top"]))))
        if equity <= 0:
            return intents
        blocks = new_buy_gates(now_date, now_hm, extra.get("vix"),
                               bars.get("SPY"), today)
        if blocks:
            return intents
        if rank is None:
            rank = compute_rank(bars, today)
        room = MAX_POSITIONS - len(held)
        if room <= 0:
            return intents
        # Sleeve cap is on TOTAL notional (old BC13N-1 fix,
        # momentum_sleeve.py:1381-1399): subtract the held book's
        # notional before sizing, split the remaining budget over the
        # new names actually targeted, and size on the all-in cost per
        # share (old 2026-10-08 fee-reserve fix). (Repair 2026-10-15
        # P3: the port sized every pass at a fresh cap/10 per name
        # regardless of the existing book, so the stated 30% cap could
        # be stacked past on any pass with room.)
        book_notional = 0.0
        for sym, p in held.items():
            try:
                ref = float(p.get("entry_px") or p.get("ref_px") or 0)
                if ref <= 0:
                    bl = bars.get(sym) or []
                    ref = float(bl[-1]["c"]) if bl else 0.0
                book_notional += int(float(p.get("qty") or 0)) * ref
            except (TypeError, ValueError):
                continue
        budget = max(0.0, SLEEVE_CAP * equity - book_notional)
        if budget <= 0:
            return intents
        targets = [r for r in rank["top_detail"]
                   if r["symbol"] not in held][:room]
        if not targets:
            return intents
        per_name = budget / max(1, len(targets))
        for row in targets:
            if room <= 0:
                break
            sym = row["symbol"]
            all_in = row["price"] * (1.0 + cost_bps(row["price"]))
            qty = _frac_qty(per_name, all_in) if all_in > 0 else 0
            if qty <= 0:
                # OBS-1 as reconciled by WS4-FRACTIONAL-20261114:
                # no forced floor; a zero per-name budget takes no
                # position, price alone no longer zeroes the qty.
                continue
            intents.append(Intent(
                "enter", sym, qty=qty, price_hint=round(row["price"], 2),
                reason="momentum top-decile: ret126=%.4f dv20=%.0f cost_bps=%.4f"
                       % (row["ret126"], row["dollar_vol_20d"],
                          cost_bps(row["price"]))))
            room -= 1
        return intents


def signal(bars, slice_state, context):
    return Momentum().signal(bars, slice_state, context)
