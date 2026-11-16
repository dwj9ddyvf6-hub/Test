"""Aster Tensor G4 marker variation — aster_tensor_g4_varmk.

CONV57-G4-VARIATION-20261116 (2026-11-16, desk total audit):
registered live beside the G4 parents under the GUTTING AS
VARIATION rule, exactly per pass2/CONV57-G4-VARIATION-PROPOSAL.md
(Form C). The parents are never edited: desk3/aster_batch14.py is
byte-untouched and this module is a sleeve-layer consumer of the
Tensor bundle's own outputs (the tensor_analysis weekly records:
features + rep_g markers/votes). The Tensor ENGINE is untouched;
nothing here writes to it.

Definition (the proposal's, verbatim in substance): a week
qualifies when native_close <= 10 AND depth60 >= 70 AND
ret60 >= 0 AND vol20 >= 0.09 AND dv20 >= $2M AND the marker
element is satisfied in either of its two forms: the row carries
the buy-green marker (the recorded parent's own state), OR the
row carries no buy marker and prints the adjacency signature
bullishVotes >= 6 AND bearishVotes <= 1 (the engine's observed
buy-cyan vote signature, 8 of 8 cyan rows on the held stream).
The recorded parent's COOL gate (atr_ratio <= 1) does NOT apply
to this variation. Entry is the first session after the signal
week; the 52-week (260-session) scheduled exit, ticket and slots
are the chassis parent's (aster_tensor_g4_cash_all_25: cash mode,
$400 ticket, 25 slots, $10,000 standard slice).

Named divergences, printed not smoothed:
- The live batch14 G4 parents were gate-cured on 2026-11-12
  (buy-green marker removed there, G4 cool cap 1.0 -> 1.1 -> 1.5).
  This variation is registered against the RECORDED parent form,
  as the proposal specifies; it neither edits nor restores any
  parent gate. Against the live cash_all parent its gate is a
  marker-conditioned subset, which is exactly the hypothesis its
  falsifier grades.
- Replay recount at registration: the proposal prints 2
  qualifiers of 428 (SKYQ 2026-09-11, CRML 2026-10-30). The
  proposal's per-conjunct counts reproduce exactly on the held
  stream (marker 0, close 101, depth 358, ret60 94, vol 349,
  dv 426, COOL 66, core pool 13), but the core pool's composition
  differs by one row (proposal SKYQ 4 / SATL 5 / CRML 4; held
  stream SKYQ 3 / SATL 6 / CRML 4) and Form C as defined yields
  3 of 428 on the held stream: the printed two plus SATL, week
  ending 2026-10-02 (close 5.73, ret60 +24.3, bullishVotes 7,
  bearishVotes 0, atr_ratio 1.394, no marker). The definition is
  registered unchanged; the count is corrected on the record.

Falsifier (registered in config/conversion_variations_20261115.json,
CONV-57 entry): the existence check leads — zero qualifiers over
a full quarter of forward weekly bundles returns the variation
to the desk as an open anatomy row; behind it the uniform
variation falsifier (retire if mean fwd5 excess vs QQQ < 0 over
the first 20 resolved forward fires).
"""
from __future__ import annotations
from datetime import datetime, timezone, date

SLEEVE_ID = "aster_tensor_g4_varmk"
TICKET = 400.0   # chassis parent aster_tensor_g4_cash_all_25
SLOTS = 25       # chassis parent aster_tensor_g4_cash_all_25
HOLD_SESSIONS = 260  # the G4 family's 52-week scheduled exit

INPUTS = ("tensor", "bars", "positions")
PRODUCERS = ({"name": "tensor_bundle", "outputs": ("tensor",),
              "freshness_sla_s": 86400},
             {"name": "bars", "outputs": ("bars",),
              "freshness_sla_s": 900},
             {"name": "broker_readback", "outputs": ("positions",),
              "freshness_sla_s": 900})


def qualifies(row):
    """Form C gate on a stream-shaped row: keys native_close,
    depth60, ret60, vol20, dv20 (or adv_usd), primaryMarkers (or
    markers), bullishVotes, bearishVotes. Fail-closed on any
    missing field, exactly as the parents fail closed."""
    if not isinstance(row, dict):
        return False
    try:
        if float(row["native_close"]) > 10:
            return False
        if float(row["depth60"]) < 70:
            return False
        if float(row["ret60"]) < 0:
            return False
        if float(row["vol20"]) < 0.09:
            return False
        dv = row.get("dv20", row.get("adv_usd"))
        if dv is None or float(dv) < 2_000_000:
            return False
    except (KeyError, TypeError, ValueError):
        return False
    markers = row.get("primaryMarkers") or row.get("markers") or []
    if "buy-green" in markers:
        return True
    if any(str(m).startswith("buy-") for m in markers):
        return False  # adjacency is defined on no-buy-marker rows
    bv = row.get("bullishVotes")
    bear = row.get("bearishVotes")
    if bv is None or bear is None:
        return False
    try:
        return float(bv) >= 6 and float(bear) <= 1
    except (TypeError, ValueError):
        return False


def _analysis_row(sym, record):
    """Normalize one bundle tensor_analysis record to the stream
    shape qualifies() reads. Returns None when the record lacks
    the feature block (fail closed, the parents' own shape)."""
    if not isinstance(record, dict):
        return None
    feats = record.get("features") or {}
    last = (record.get("rep_g") or {}).get("last") or {}
    row = {"symbol": sym,
           "native_close": feats.get("native_close"),
           "depth60": feats.get("depth60"),
           "ret60": feats.get("ret60"),
           "vol20": feats.get("vol20"),
           "dv20": feats.get("dv20"),
           "atr_ratio": feats.get("atr_ratio"),
           "primaryMarkers": list(last.get("primaryMarkers") or []),
           "bullishVotes": last.get("bullishVotes"),
           "bearishVotes": last.get("bearishVotes"),
           "signal_end": record.get("signal_end")}
    if row["native_close"] is None:
        return None
    return row


def _now(view, ctx):
    n = view.get("now") or (ctx or {}).get("now") \
        or "2026-10-24T15:00:00"
    if isinstance(n, datetime):
        return n
    try:
        return datetime.fromisoformat(str(n).replace("Z", "+00:00"))
    except Exception:
        return datetime(2026, 10, 24, tzinfo=timezone.utc)


def _sess(view, ctx):
    s = (ctx or {}).get("session") if isinstance(ctx, dict) else None
    return str(s or _now(view, ctx).date().isoformat())[:10]


def _bars(view, sym):
    m = view.get("bars") or {}
    for k in (f"{sym}|1Day", f"{sym}|1D", sym):
        if m.get(k):
            return m[k]
    return []


def _opened_sessions(p, bars):
    # The batch14 parents' derivation, carried verbatim in shape:
    # sessions held = distinct bar dates after the opened date.
    od = str(p.get("opened_at") or p.get("entry_date") or "")[:10]
    if len(od) != 10 or od[4] != "-" or od[7] != "-":
        return 0
    days = set()
    for b in bars or []:
        if not isinstance(b, dict):
            continue
        t = b.get("t") or b.get("date") or b.get("timestamp")
        d = None
        if isinstance(t, (int, float)) and t > 1e11:
            d = datetime.fromtimestamp(
                t / 1000, tz=timezone.utc).date().isoformat()
        elif isinstance(t, str) and len(t) >= 10 \
                and t[4] == "-" and t[7] == "-":
            d = t[:10]
        if d and d > od:
            days.add(d)
    return len(days)


def _age(p, bars=None):
    for k in ("sessions_held", "age_sessions", "held_sessions"):
        if p.get(k) is not None:
            return int(p[k])
    if p.get("weeks_held") is not None:
        return int(p["weeks_held"]) * 5
    return _opened_sessions(p, bars)


def evaluate(sleeve_id, view, ctx=None):
    view = view or {}
    ctx = ctx or {}
    now = _now(view, ctx)
    sess = _sess(view, ctx)
    stamp = now.strftime("%Y%m%dT%H%M%S")
    positions = [p for p in (view.get("positions") or [])
                 if float(p.get("qty") or 0) != 0]
    out = []
    n = 0

    def intent(kind, sym, side, qty, reason, price):
        nonlocal n
        n += 1
        return {"intent_id": f"{sleeve_id}-{stamp}-{n}",
                "kind": kind, "symbol": sym, "side": side,
                "qty": qty, "order_type": "market",
                "limit_price": None, "stop_price": None,
                "reason": reason, "time_in_force": "day",
                "position_intent": "buy_to_open" if kind == "entry"
                else "sell_to_close",
                "price_hint": float(price) if price else None}

    # Designed exit ONLY: the G4 52-week scheduled deadline.
    for p in positions:
        sym = p["symbol"]
        bars = _bars(view, sym)
        price = float(bars[-1]["c"]) if bars \
            else float(p.get("avg_price") or 0)
        due = _age(p, bars) >= HOLD_SESSIONS
        ea = p.get("exit_at") or p.get("exit_deadline")
        if ea and sess >= str(ea)[:10]:
            due = True
        if due:
            out.append(intent(
                "exit", sym, "sell", abs(float(p["qty"])),
                f"{sleeve_id} exit: week52_deadline "
                f"sessions_held={_age(p, bars)}", price))
    if out:
        return out

    held = {p["symbol"] for p in positions}
    if len(held) >= SLOTS:
        return []

    bundle = view.get("tensor")
    if not isinstance(bundle, dict):
        return []
    analysis = bundle.get("tensor_analysis")
    if not isinstance(analysis, dict) or not analysis:
        return []  # no weekly bundle rows served: fail closed

    for sym in sorted(analysis):
        if sym in held:
            continue
        row = _analysis_row(sym, analysis[sym])
        if row is None or not qualifies(row):
            continue
        send = str(row.get("signal_end") or "")[:10]
        if not send:
            continue
        # Entry the first session AFTER the signal week (the
        # recorded cash-mode policy): the session must be
        # strictly later than the signal week's end date.
        try:
            if date.fromisoformat(sess) <= date.fromisoformat(send):
                continue
        except Exception:
            continue
        price = float(row["native_close"])
        # The parents' execution-price revalidation, carried:
        # size off the latest close when a current bar exists and
        # refuse when it has crossed the family's $10 cap.
        fb = _bars(view, sym)
        eprice = price
        if fb:
            cur = float(fb[-1]["c"])
            if cur and cur > 0:
                if cur > 10:
                    continue
                eprice = cur
        qty = int(TICKET // eprice)
        if qty < 1:
            continue
        out.append(intent(
            "entry", sym, "buy", qty,
            f"{sleeve_id} entry: tensor_g4_varmk form=C "
            f"ticket={TICKET:.0f} price={eprice:.2f} "
            f"signal_end={send}", eprice))
        return out
    return out
