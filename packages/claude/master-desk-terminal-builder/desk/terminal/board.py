"""The board: the session's best setups from the desk's reads, how long each stays, why each leaves, and the watching
list (docs/research/2026-10-18-terminal/SETUPS_V2.md).

  Pool       every roster name's read (state/terminal/reads.json, once a session) and every name a desk strategy
             signalled to buy, read fresh with the strategies counted as evidence
  Eligible   liquid (a close of 5 or more, a 20-session median dollar volume of 20 million or more), a plan to buy now,
             on a pullback or on a breakout (a turn waits for its trigger in Look up), and a take other than Against
  Rank       the desk's take, the form (a buy here first), the evidence, reward to risk, the ticker. Conviction is the
             card's grade, not its rank: a grade the board sorts on first reads the same on every card it lists (all
             27 listed calls read High to 2026-10-23, batch bs1 item 8)
  Board      at most five. A listed name holds its place while its call is live and it ranks within the top ten; new
             names fill the rest in rank order. Each departure states why and, when the call has closed, its result.
             A buy that ran away leaves: a waiting buy or pullback whose last close is 5% or more over its buy range's
             top (or the close it was listed on, when that sat higher: a pullback's), or one risk unit past it
             (ran_away); its call keeps resolving by the record's rules, which fill only at the cap or under
  Spikes     a name up 25% or more in its last ten sessions is not listed as a new buy (SPIKE_PCT; the research
             ledger's grade-A theme T02: short-term strength fades in small caps, ROC(10) lags equally volatile
             names). On watching its line says to wait for a pullback
  Watching   up to six plans of Solid conviction or more, take not Against, liquid and not on the board: first the
             pullbacks inside a long uptrend (the read's averages: over a rising 200-day, the 50-day over it) whose
             buy zone's top sits within 1.5 ATR under the close, the research ledger's grade-A buy side (theme T04:
             dips and quiet pauses inside long uptrends; small, and chiefly nano); then the breakouts whose trigger
             sits within 1.5 ATR over the close, the shape the research calls a trap in small caps and nothing in
             liquid names (T02), kept at one row or more while any qualifies. One line each"""
MAX_BOARD, KEEP_WITHIN, MAX_WATCH = 5, 10, 6
RAN_PCT = 5.0                   # a waiting buy this far over the top of its buy range has run away from it
NEXT_N = 20                     # beneath the board: the next twenty setups in rank order (owner, 2026-10-26)
WATCH_MIN_R = 1.5               # watching: reward to risk from the top of the buy (trigger or zone top), owner 2026-10-26
SPIKE_PCT = 25.0                # up this much in ten sessions: a spike, not a new buy
RAN_AWAY = "Ran away from its buy range"
WATCH_ATR = 1.5
TAKE_SCORE = {"Strong": 3, "For": 2, "Leaning": 1, "Against": 0}
FORM_SCORE = {"now": 3, "pullback": 2, "breakout": 2, "turn": 0}


def eligible(pub):
    return bool(pub.get("liquid")) and pub["gut"]["word"] != "Against" and pub["form"] in ("now", "pullback",
                                                                                            "breakout")


def rank_key(pub, mom=None):
    """the board's order: the take, the form, the evidence, reward to risk, the ticker. mom ({symbol: the analysis
    engine's momentum rank}) breaks an exact tie of the first four before the ticker, a name without one last
    (PROGRAM2.md Addendum 2-19b's TILT, desk/terminal/engine.py): it moves nothing else"""
    key = (-TAKE_SCORE[pub["gut"]["word"]], -FORM_SCORE[pub["form"]], -(pub.get("evidence") or 0),
           -(pub["plan"].get("r") or 0))
    if mom is None:
        return key + (pub["symbol"],)
    m = mom.get(pub["symbol"])
    return key + (-(m if m is not None else -1), pub["symbol"])


def ran_away(plan, last_pct):
    """whether a waiting buy's last close, last_pct % from the close its plan is measured on, ran away from its buy
    range: 5% or more over the range's top, or one risk unit (top minus exit) past it. A pullback's range sits under
    the close it was listed on, so it is measured from that close"""
    hi, out = plan.get("zone_hi"), plan.get("out")
    if last_pct is None or hi is None or out is None or hi <= out:
        return False                                     # no risk to measure (prices.check holds such a card back)
    ref, risk = 1 + max(hi, 0.0) / 100, (hi - out) / 100
    return 1 + last_pct / 100 >= min(ref * (1 + RAN_PCT / 100), ref + risk)


def spiked(rec):
    """a spike: up SPIKE_PCT or more in the read's last ten sessions (its record's run10)"""
    return (rec or {}).get("run10") is not None and rec["run10"] >= SPIKE_PCT


def select(pool, prev_listed, live, called=(), session=None, ran=(), spikes=(), mom=None):
    """(listed, ranked, reasons): pool {symbol: public read}; prev_listed {symbol: listing with its "call" id}; live
    {call id: symbol} of the calls still waiting or open; called: the (symbol, read session) pairs that already have
    a call; session: the latest session the desk's prices hold, once the roster's read of it is complete, else None.
    A listed name stays while its own call lives and it ranks within KEEP_WITHIN (on a partial read no rank is
    trusted, so it stays while its call lives). New names fill the rest in rank order, only from reads of `session`,
    never a name with a live call or a read that already had one (the audit's F2, F3, F4 and F9), and never a spike
    (spikes: the names up SPIKE_PCT or more in ten sessions). ran: the listed names whose waiting buy ran away from
    its range (ran_away). reasons {symbol: why it left} for every previously listed name that did not stay. mom:
    the engine's momentum ranks, the tie-break (rank_key)"""
    def order(p):
        return rank_key(p, mom)
    ranked = sorted((p for p in pool.values() if eligible(p)), key=order)
    pos = {p["symbol"]: i + 1 for i, p in enumerate(ranked)}
    live_syms = set(live.values())
    keep, reasons = [], {}
    for sym, old in prev_listed.items():
        p = pool.get(sym)
        if old.get("call") not in live:
            reasons[sym] = "closed"
        elif sym in ran:
            reasons[sym] = RAN_AWAY
        elif p is None:
            reasons[sym] = "No read this session"
        elif p["form"] == "wait":
            reasons[sym] = "The desk's read now stands aside: no line to be wrong at"
        elif p["gut"]["word"] == "Against":
            reasons[sym] = "The desk's read turned against it"
        elif not p.get("liquid"):
            reasons[sym] = "Its trading fell under the board's liquidity bar"
        elif not eligible(p):
            reasons[sym] = "Its plan changed to a wait for a turn"
        elif session is not None and pos[sym] > KEEP_WITHIN:
            reasons[sym] = f"Fell out of the top {KEEP_WITHIN}"
        else:
            keep.append(p)
    listed = sorted(keep, key=order)[:MAX_BOARD]
    for p in ranked:
        if len(listed) >= MAX_BOARD or session is None:
            break
        sym = p["symbol"]
        if sym in {q["symbol"] for q in listed} or sym in prev_listed or sym in live_syms or \
                p.get("as_of") != session or (sym, p.get("as_of")) in called or sym in spikes:
            continue
        listed.append(p)
    for p in keep:
        if p not in listed:
            reasons[p["symbol"]] = "Made room for stronger setups"
    listed.sort(key=order)
    return listed, ranked, reasons


def long_uptrend(rec):
    """the read's averages in a long uptrend: its trend.stack for the long at 0.45 or more (price over a rising 200-day
    with the 50-day over it: read/call._uptrend), from the record's facts"""
    return any(k == "trend.stack" and side > 0 and st >= 0.45 for k, side, st in (rec or {}).get("facts") or ())


def watching(pool, records, listed_syms):
    """[{symbol, action, conviction, gut, line, by, ...}]: the next NEXT_N setups after the board, in the board's own rank
    order (owner, 2026-10-26: "top 5, then top 20 beneath that"): eligible reads of Solid conviction or more, not on the
    board, with room to their target (WATCH_MIN_R from the top of the buy), never a breakout after a spike"""
    cands = []
    for sym, p in pool.items():
        if sym in listed_syms or not eligible(p) or p["conviction"]["level"] < 2:
            continue
        rec = records.get(sym) or {}
        pp = p.get("plan") or {}
        top = pp.get("trigger") if pp.get("trigger") is not None else pp.get("zone_hi")
        if None in (top, pp.get("t1"), pp.get("out")) or top <= pp["out"] or \
                (pp["t1"] - top) / (top - pp["out"]) < WATCH_MIN_R:   # room to the target from the top of its buy
            continue
        if not rec.get("atr") or not rec.get("close"):
            continue
        if p["form"] == "breakout" and spiked(rec):          # after a spike the desk buys no breakout
            continue
        cands.append(p)
    cands.sort(key=rank_key)
    out = [(None, p) for p in cands[:NEXT_N]]
    rows = [{"symbol": p["symbol"], "action": p["action"], "conviction": p["conviction"]["word"],
             "gut": p["gut"]["word"], "line": p["plan"]["sentence"], "by": p["plan"]["by"],
             "close": round(float((records.get(p["symbol"]) or {}).get("close") or 0), 4) or None,
             "trigger": p["plan"].get("trigger"), "zone_hi": p["plan"].get("zone_hi"), "t1": p["plan"].get("t1"),
             "out": p["plan"].get("out")} for _, p in out]
    for row, (_, p) in zip(rows, out):
        if p["form"] in ("pullback", "now"):             # its buy range: both ends, for the row's words and ladder
            row.update(zone_lo=p["plan"].get("zone_lo"), mode=p["plan"].get("mode") or "level")
    for row in rows:                                     # a spiked pullback stays on watching, waiting for its range
        rec = records.get(row["symbol"])
        if spiked(rec):
            row["spike"] = round(rec["run10"])
    for row, (_, p) in zip(rows, out):                   # its read drawn: the bars its words name, its lines, averages
        row.update({k: p[k] for k in ("marks", "lines", "avgs") if p.get(k)})
    return rows
