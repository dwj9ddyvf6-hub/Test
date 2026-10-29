"""QQQ put ladder — lean-desk port (Wave D, Decision #119 family).

master-desk: the Aurelia source desk's QQQ put ladder restored on the engine (Agentic-Trading-Desk aurelia-paper-desk
@1720157f768e): its rules are desk/put_ladder.py, vendored byte-exact (desk/vendor/aurelia/put_ladder.py) and called
unchanged; its inputs and sends are desk/ladder_broker.py sync(). The public campaign, as the source ran it:

  layers ... three QQQ puts sold about 45 days out at delta 0.05-0.08, a new layer at most once per ISO week; a layer
             is a short QQQ put in this sleeve's book (or one being sold), with the record its sale stored (id,
             session opened, entry credit = the bid sold at, entry spot, entry delta, rolled_on).
  decide ... the source's decide(), unchanged: the open layers oldest expiration first — <= 5 DTE bought back; <= 21
             DTE managed: rolled UP in the same expiration (to the band put above it whose bid beats this put's ask)
             only when the posture is normal, the put is not challenged, QQQ is above the layer's entry spot and the
             put's ask is <= half its entry credit; a challenged put (|delta| >= 0.20 or spot <= strike x 1.03) is
             rolled OUT and down (the 38-52 DTE band put at or below its strike) unless the posture is stand-down,
             else bought back. A new layer: the band put nearest 45 DTE, then delta 0.05, then the tightest
             spread, then the lowest strike; bid >= 0.05, ask > bid, (ask - bid) <= max(0.10, 25% of mid), strike
             below spot, not in an expiration a layer already holds — blocked, in order, by a posture other than
             normal, an unknown or down QQQ week (last close below the close five sessions earlier), a challenged
             put, 12 contracts open, a layer already sold this ISO week, no band put, unknown or insufficient options
             buying power (cash required = (strike - bid) x 100 x 3), or an open put without a quote.
  sends .... buy-backs first, then the rolls and the new layer in decide()'s order; each roll's buy-back before its
             new sale, the new sale only while the options buying power after the buy-back covers it. Day limits:
             sales at the bid, buy-backs at the ask (to the cent, as the source rounded them).
  inputs ... the QQQ puts of the desk's indicative chain with a delta (abs) — 38-52 DTE, plus 0-25 DTE while a
             layer is open; spot = the live QQQ quote; the five-session change on QQQ's completed daily closes;
             posture = the brain's tape posture (brain/judgment.py: VIX >= 40 or a Nasdaq day <= -8% stand down,
             VIX >= 25 or a day <= -5% cautious) on the Aurelia feed's tape, "unknown" without it; options buying
             power = the book's cash less the strike value of its short puts and the cash its working sales secure.
  timing ... a pass every 15 minutes of the regular session until 15 minutes before the close (moc_window).

Gone under the cutover doctrine: the desk kill switch (desk_state/KILL_SWITCH halted every send) and the Femto
fences of the old desk's copy (no chain fetch, a sim book, buying power as a fed input, no broker call ever).
Named divergences: the ladder trades its own book ($1,000,000, so the campaign's own 12-contract cap binds; the
source shared the Aurelia paper account's options buying power); options buying power is that book's cash less
the strike cash of its short puts and its working sales (the source read the account's options_buying_power);
spot is the live QQQ quote (the source read the Aurelia plan's price, the last finished close); the five-session
change is on the desk's completed daily closes (the source's 12-hour Yahoo cache); every held layer is quoted (the
source fetched 38-52 and 0-25 DTE only, so a layer 26-37 DTE out had no quote and held new layers back as
"quote_missing"); a roll's new put is sold when the buying power after the buy-back (its strike cash released, its
ask paid) covers it (the source re-read the account right after sending the buy-back, filled or not); a layer is a
fill in the book: a sale that never fills leaves no layer, a buy-back that never fills leaves the layer to be
managed again (the source recorded a layer when the broker accepted the order and never reconciled fills); a roll
whose new sale is skipped leaves no layer (the source wrote the skipped sale into its state as a new working layer
and stamped the week); two layers that land in one contract are one position; the week is stamped when the new
layer's sale is sent (a broker reject still trades the virtual book); posture without the Aurelia feed is
"unknown" (the source then had no fresh plan); the stand-down notices the operator gave the brain have no channel
here (the tape posture is kept); Aurelia's equity ticket, which decide() reads and ignores, is passed as not
pending; the chain and quotes are the desk's (its cache, refreshed every 5 minutes, not reused for 15); an empty
chain after a failed fetch is not labelled data_unavailable (the source never cleared its first quote error; no
order differs: an empty chain trades nothing).

Inputs via context.extra:
  "chain"          {"QQQ": put rows 0-52 DTE {"symbol","expiration","strike","type","bid","ask","delta"}}
  "legs"           the sleeve's option positions {OCC: {"qty","avg","opened_at","meta"}} (meta = position_meta)
  "pending"        its working option orders [{"action","occ","side","qty","limit","key","meta"}]
  "quotes"         {"QQQ": {"bid","ask","last"}} — the spot
  "cash"           the book's cash
  "aurelia"        the Aurelia feed (its tape: "as_of", "vix", "ndx_day") | {"error"}
  "meta"           {"week_opened": "YYYY-Www"}
  "session_close"  epoch of today's close (the day orders' end)
  "sleeve_state"
Bars: QQQ completed daily bars (the five-session change; the spot when no quote)."""
from datetime import date, datetime
from zoneinfo import ZoneInfo

from .compat import BaseSleeve, Intent, SleeveConfig
from ...vendor.aurelia import judgment as AJ
from ...vendor.aurelia import put_ladder as PL

ET = ZoneInfo("America/New_York")
UNDERLYING = PL.UNDERLYING
FAR_DTE = (38, PL.DTE_HI)          # ladder_broker._fetch_quotes: the band window
NEAR_DTE = (0, 25)                 # ... and the managed layers' window while a layer is open
CONFIG = SleeveConfig(
    sleeve_id="qqq_put_ladder", cadence_s=900, universe=(UNDERLYING,),
    state_schema={"week_opened": "str|None"}, risk_pct=None)


def is_ladder_put(occ):
    p = PL.parse_occ(occ or "")
    return bool(p) and p["root"] == UNDERLYING and p["cp"] == "P"


def layers_of(legs, pending):
    """the ladder's layers: each short QQQ put held or being sold (qty = held + working sale), with the layer record
    its sale stored; "closing" while a buy-back works on it. In the order the layers opened (the source's list)."""
    rows = {}
    closing = {o.get("occ") for o in pending or [] if o.get("action") == "exit"}
    for occ, p in (legs or {}).items():
        q = float(p.get("qty") or 0.0)
        if q < 0 and is_ladder_put(occ):
            rows[occ] = {"held": -q, "working": 0.0, "meta": dict((p.get("meta") or {}).get("layer") or {})}
    for o in pending or []:
        occ = o.get("occ") or ""
        if o.get("action") != "enter" or o.get("side") != "sell" or not is_ladder_put(occ):
            continue
        r = rows.setdefault(occ, {"held": 0.0, "working": 0.0, "meta": {}})
        r["working"] += float(o.get("qty") or 0.0)
        if not r["meta"]:
            r["meta"] = dict((o.get("meta") or {}).get("layer") or {})
    out = []
    for occ, r in rows.items():
        p, m = PL.parse_occ(occ), r["meta"]
        layer = {"id": m.get("id") or "%s:%s" % (p["expiration"], p["strike"]), "opened": m.get("opened"),
                 "expiration": p["expiration"], "strike": p["strike"], "symbol": occ,
                 "qty": int(round(r["held"] + r["working"])), "entry_credit": m.get("entry_credit"),
                 "entry_spot": m.get("entry_spot"), "entry_delta": m.get("entry_delta"),
                 "status": "closing" if occ in closing else "open"}
        if m.get("rolled_on"):
            layer["rolled_on"] = m["rolled_on"]
        if layer["qty"] > 0:
            out.append(layer)
    out.sort(key=lambda l: (str(l.get("opened") or ""), l["id"]))
    return out


def chain_quotes(rows, today, layers):
    """ladder_broker._quotes_from on the desk's chain: QQQ puts with a delta (abs; bid/ask 0 when absent), 38-52 DTE,
    then 0-25 DTE while a layer is open, then any held layer's own contract outside both windows."""
    any_open = any(l.get("status") in ("working", "open") for l in layers)
    held = {l["symbol"] for l in layers}
    far, near, other = [], [], []
    for r in rows or []:
        sym = r.get("symbol") or ""
        p = PL.parse_occ(sym)
        if not p or p["cp"] != "P" or p["root"] != UNDERLYING or r.get("delta") is None:
            continue
        q = {"symbol": sym, "expiration": p["expiration"], "strike": p["strike"], "delta": abs(float(r["delta"])),
             "bid": float(r.get("bid") or 0), "ask": float(r.get("ask") or 0)}
        life = PL.dte(p["expiration"], today)
        if FAR_DTE[0] <= life <= FAR_DTE[1]:
            far.append(q)
        elif any_open and NEAR_DTE[0] <= life <= NEAR_DTE[1]:
            near.append(q)
        elif sym in held:
            other.append(q)
    return far + near + other


def completed_closes(bars, session):
    """QQQ's daily closes of the sessions before today's (a running session's bar is not a close)."""
    return [float(b["c"]) for b in (bars or {}).get(UNDERLYING) or []
            if datetime.fromtimestamp(float(b["t"]), tz=ET).date().isoformat() < session]


def spot_of(quotes, bars):
    q = (quotes or {}).get(UNDERLYING) or {}
    try:
        bid, ask, last = q.get("bid"), q.get("ask"), q.get("last")
        if bid and ask and float(ask) >= float(bid) > 0:
            return (float(bid) + float(ask)) / 2
        if last and float(last) > 0:
            return float(last)
    except (TypeError, ValueError):
        pass
    bl = (bars or {}).get(UNDERLYING) or []
    return float(bl[-1]["c"]) if bl else None


def buying_power(cash, legs, pending):
    """options buying power of a cash-secured book: cash less the strike value of every short put it holds and the
    cash each working put sale will secure ((strike - limit) x 100 x qty)."""
    if cash is None:
        return None
    bp = float(cash)
    for occ, p in (legs or {}).items():
        q, k = float(p.get("qty") or 0.0), PL.parse_occ(occ)
        if q < 0 and k and k["cp"] == "P":
            bp -= k["strike"] * 100.0 * -q
    for o in pending or []:
        k = PL.parse_occ(o.get("occ") or "")
        if o.get("action") == "enter" and o.get("side") == "sell" and k and k["cp"] == "P":
            bp -= max(0.0, k["strike"] - float(o.get("limit") or 0.0)) * 100.0 * float(o.get("qty") or 0.0)
    return bp


def posture_of(tape):
    """plan["brain"]["level"]: the brain's posture on the tape (no stand-down notices); "unknown" without the feed."""
    if not isinstance(tape, dict) or tape.get("error") or not tape.get("as_of"):
        return "unknown"
    return AJ.posture({"vix": tape.get("vix"), "ndx_day": tape.get("ndx_day")}, [], [])["level"]


def sends(decision, bp):
    """sync()'s send loop: buy-backs first (then decide()'s order); per action its buy-back, then its sale. A roll's
    new put is sold only while the buying power after the buy-backs covers its cash requirement. Returns the
    ordered log [("close" | "open" | "skip", action, leg)]."""
    ordered = sorted(decision["actions"], key=lambda a: a["kind"] != "buy_close")
    log, avail = [], bp
    for a in ordered:
        close, opn = a.get("close"), a.get("open")
        if close:
            log.append(("close", a, close))
            if avail is not None:
                k = PL.parse_occ(close["symbol"])["strike"]
                avail += (k - float(close["limit"])) * 100.0 * int(close["qty"])
        if opn:
            need = PL.cash_required(opn["strike"], opn["bid"], opn["qty"])
            if a["kind"] != "sell_open" and (avail is None or avail < need):
                log.append(("skip", a, opn))
                continue
            log.append(("open", a, opn))
            if avail is not None:
                avail -= need
    return log


def decide(bars, context):
    """one pass of ladder_broker.sync() on this sleeve's book: the decision and the sends."""
    extra = context.extra or {}
    today = date.fromisoformat(context.session)
    legs, pending = extra.get("legs") or {}, extra.get("pending") or []
    layers = layers_of(legs, pending)
    rows = (extra.get("chain") or {}).get(UNDERLYING)
    quotes = chain_quotes(rows, today, layers)
    closes = completed_closes(bars, context.session)
    spot = spot_of(extra.get("quotes"), bars)
    posture = posture_of(extra.get("aurelia"))
    fell = PL.price_fell(closes)
    bp = buying_power(extra.get("cash"), legs, pending)
    week = (extra.get("meta") or {}).get("week_opened")
    if spot is None:
        decision = {"actions": [], "add_block": "data_unavailable", "candidate": None}
    else:
        decision = PL.decide(layers, quotes, today, spot, posture=posture, fell=fell, buying_power=bp,
                             equity_pending=False, week_opened=week)
    if rows is None:                                   # no chain this pass (the source: a quote error, no quotes)
        decision["add_block"] = "data_unavailable"
        decision["actions"] = [a for a in decision["actions"] if a["kind"] == "buy_close"]
    log = sends(decision, bp)
    by_id = {l["id"]: l for l in layers}
    end = extra.get("session_close")
    intents, stamp = [], None
    for leg_name, a, leg in log:
        if leg_name == "skip":
            continue
        order = {"type": "limit", "limit_price": float(leg["limit"])}
        if end:
            order["not_after"] = float(end)
        lid = a.get("layer_id") or "new"
        key = "ladder:%s:%s:%s:%s" % (today.isoformat(), a["kind"], lid, leg["symbol"])
        if leg_name == "close":
            intents.append(Intent(
                "exit", UNDERLYING, qty_hint=int(leg["qty"]),
                legs=({"symbol": leg["symbol"], "side": "buy", "ratio": 1, "position_intent": "buy_to_close"},),
                order=order, signal_key=key + ":btc",
                reason="qqq_put_ladder %s: buy_to_close %s x%d @%.2f layer=%s: %s"
                       % (a["kind"], leg["symbol"], int(leg["qty"]), float(leg["limit"]), lid, a["reason"])))
            continue
        if a["kind"] == "sell_open":
            rec = {"id": "%s:%s" % (leg["expiration"], leg["strike"]), "opened": today.isoformat()}
            stamp = PL.iso_week(today)
        else:
            old = by_id.get(a.get("layer_id")) or {}
            rec = {"id": old.get("id") or a.get("layer_id"), "opened": old.get("opened"), "rolled_on": today.isoformat()}
        rec.update(entry_credit=leg["bid"], entry_spot=spot, entry_delta=leg["delta"], qty=int(leg["qty"]))
        intents.append(Intent(
            "enter", UNDERLYING, qty_hint=int(leg["qty"]), asset="option",
            legs=({"symbol": leg["symbol"], "side": "sell", "ratio": 1, "position_intent": "sell_to_open"},),
            order=order, signal_key=key + ":sto", position_meta={"layer": rec},
            reason="qqq_put_ladder %s: sell_to_open %s x%d @%.2f delta %.3f dte %s cash_required %.2f layer=%s "
                   "(spot %.2f, posture %s): %s"
                   % (a["kind"], leg["symbol"], int(leg["qty"]), float(leg["limit"]), float(leg["delta"]),
                      leg.get("dte"), float(leg.get("cash_required") or 0.0), rec["id"], spot, posture, a["reason"])))
    return {"decision": decision, "intents": intents, "week_stamp": stamp, "layers": layers, "spot": spot,
            "posture": posture, "fell": fell, "buying_power": bp, "log": log,
            "skipped": [(a, leg) for kind, a, leg in log if kind == "skip"], "quotes": len(quotes)}


def _pass(bars, context):
    extra = context.extra
    memo = extra.get("_ladder_pass") if isinstance(extra, dict) else None
    if memo is None or memo[0] is not context:           # one decision per pass's context (identity, not id())
        memo = (context, decide(bars, context))
        if isinstance(extra, dict):
            extra["_ladder_pass"] = memo
    return memo[1]


class QqqPutLadder(BaseSleeve):
    CONFIG = CONFIG

    def signal(self, bars, slice_state, context):
        if not (context.extra or {}).get("chain") and not (context.extra or {}).get("legs"):
            return []                                    # nothing quoted and nothing held: no decision to make
        return list(_pass(bars, context)["intents"])


def signal(bars, slice_state, context):
    return QqqPutLadder().signal(bars, slice_state, context)


def next_meta(bars, slice_state, context, intents=()):
    """meta.week_opened: the ISO week of the last new layer sold (stamped when the sale is sent)."""
    meta = dict((context.extra or {}).get("meta") or {})
    extra = context.extra or {}
    if extra.get("chain") or extra.get("legs"):
        stamp = _pass(bars, context)["week_stamp"]
        if stamp:
            meta["week_opened"] = stamp
    return meta


def monitor(mod, bars, context):
    """one record per ladder state: the add block, the candidate, the layers, the posture."""
    extra = context.extra or {}
    if not extra.get("chain") and not extra.get("legs"):
        return []
    p = _pass(bars, context)
    d = p["decision"]
    cand = (d.get("candidate") or {}).get("symbol")
    acts = ", ".join("%s %s" % (a["kind"], a.get("layer_id") or "new") for a in d["actions"]) or "none"
    return [(UNDERLYING, "qqq_put_ladder: block %s, candidate %s, actions %s; %d layers, posture %s, week fell %s"
             % (d.get("add_block"), cand, acts, len([l for l in p["layers"] if l["status"] == "open"]), p["posture"],
                p["fell"]),
             {"add_block": d.get("add_block"), "candidate": cand, "buying_power": p["buying_power"],
              "spot": p["spot"]})]
