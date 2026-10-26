"""Entry gates. Pure functions: numbers in, decision out. No I/O, no clock reads.
fear_day   : Galath doctrine (2026-10-12): buy only when QQQ < prior close AND stock <= its prior close AND stock <= 1.02 x fire close, decided
             inside the afternoon window (close-40 .. close-10 min) of a session D+1..D+5; nothing by D+5 -> skip (never a green-day buy).
qqq_red_1h : Main 1H lane: QQQ < prior close AND stock <= prior close at entry time (else wait until the 30-min deadline).
midna_block: Midna lanes keep her own buyBlockReason (green.ts): block when QQQ red AND VIX up AND name red; unknown input -> block (fail closed).
Every unknown price -> wait/block, never a false trigger."""
import math
def _red(px, prior): return px is not None and prior is not None and px < prior
def fear_day(*, day, window, now, w_open, w_cut, qqq_px, qqq_prior, px, prior, fire_close, mult=1.02):
    """-> (result, why). result in: not_in_window | early | missed | wait | skip | trigger"""
    if day not in window: return "not_in_window", f"{day} outside {window[0]}..{window[-1]}"
    last = day == window[-1]
    if now >= w_cut: return ("skip" if last else "missed"), "past the afternoon decision cutoff"
    if now < w_open: return "early", "before the afternoon decision window"
    cap = fire_close * mult if fire_close else None
    qred = _red(qqq_px, qqq_prior); sred = px is not None and prior is not None and px <= prior; nc = px is not None and cap is not None and px <= cap
    why = f"QQQ {qqq_px} vs {qqq_prior} red={qred}; stock {px} vs prior {prior} red={sred}; cap {cap and round(cap, 4)} ok={nc}"
    if qred and sred and nc: return "trigger", why
    return ("skip" if last else "wait"), why
def qqq_red_1h(*, qqq_px, qqq_prior, px, prior):
    ok = _red(qqq_px, qqq_prior) and px is not None and prior is not None and px <= prior
    return ("trigger" if ok else "wait"), f"QQQ {qqq_px}/{qqq_prior} stock {px}/{prior}"
def midna_block(*, qqq_px, qqq_prior, vix_px, vix_prior, px, prior):
    """-> (blocked, why). Midna green.ts buyBlockReason; any missing input = blocked."""
    if None in (qqq_px, qqq_prior, vix_px, vix_prior, px, prior): return True, "input unknown (fail closed)"
    b = qqq_px < qqq_prior and vix_px > vix_prior and px < prior
    return b, ("QQQ red + VIX up + name red" if b else "not blocked")
def capped_limit(*, ref, buffer_pct, fire_close, band_pct, no_chase_max=None):
    """marketable DAY limit = ref x (1 + buffer), capped by fire_close x (1 + band) and, for fear-day entries, by the 1.02x no-chase cap.
    Never above the doctrine cap. -> limit or None (no reference)."""
    if not ref: return None
    lim = ref * (1 + buffer_pct / 100.0); caps = [c for c in (fire_close * (1 + band_pct / 100.0) if fire_close and band_pct else None, no_chase_max) if c]
    for c in caps: lim = min(lim, c)
    dp = 2 if lim >= 1 else 4; r = round(lim, dp)
    if caps and r > min(caps) + 1e-12: r = math.floor(min(caps) * 10 ** dp + 1e-9) / 10 ** dp   # L-28: rounding never lifts a limit above its cap
    return r
def size(*, position_usd, ref, avail, dv20, cap_pct_dv20, min_fraction, global_slot_usd, lane_used_usd, budget_usd, one_share_max_usd=None):
    """paper-desk 1.8.2 sizing (desk.py enter(), lines ~1276-1296): dv20 cap, free-cash check, whole shares, one-share rule, lane dollar budget
    (shrink to the remaining budget if >= min_fraction of the position). -> (qty, why_or_None, blocked_retryable_or_None)"""
    if not ref or ref <= 0: return 0, "no reference price", None
    slot = position_usd; cap = None
    if cap_pct_dv20:
        if dv20 is None: return 0, "illiquid/unknown: dv20 unavailable", None
        cap = dv20 * cap_pct_dv20 / 100.0; slot = min(slot, cap)
    if avail < min_fraction * min(slot, global_slot_usd): return 0, f"insufficient cash ({avail:,.0f})", "insufficient_cash"
    slot0 = slot; slot = min(slot, avail); qty = int(slot // ref)
    if qty < 1 and one_share_max_usd and ref <= one_share_max_usd and ref <= avail and (cap is None or ref <= cap): qty = 1
    if qty < 1 and avail < slot0 and ref <= slot0: return 0, f"insufficient cash for one share at {ref:.2f}", "insufficient_cash"
    if qty < 1: return 0, f"price {ref:.2f} above slot ${slot:,.0f} (whole shares)", None
    if budget_usd is not None and lane_used_usd + qty * ref > budget_usd + 1e-6:
        room = budget_usd - lane_used_usd
        if room >= min_fraction * slot and int(room // ref) >= 1: qty = int(room // ref)
        else: return 0, f"lane budget ${lane_used_usd:,.0f} + ${qty * ref:,.0f} > ${budget_usd:,.0f}", "lane_budget"
    return qty, None, None
