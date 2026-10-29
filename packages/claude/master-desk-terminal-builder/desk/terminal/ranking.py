"""The board's ranking, drawn (edition `ranked`; GrokBot's Opportunity Ranker, drawn by the page): the top RANKED of the
board's eligible reads in exactly the board's own order (board.select: rank_key, with the engine's tie-break), each with
the kinds of evidence its number is made of.

  ranked[]  {rank, symbol, take, form, evidence, parts: [{key, label, value}], r, delta, listed}
            evidence  the number the board ranks by: the read's E (read/call.evidence, the sum of the kinds'
                      saturated votes) to a tenth, as every card shows it
            parts     each kind's vote (read/call.family_votes, kept in the read's record as "kinds") to a tenth, by
                      the largest remainder, so the parts sum to evidence exactly; strongest first, zeros left out
            r         the plan's reward to risk; listed: on the board
            delta     evidence against the last edition of the session before (an edition within one session reads
                      the same bars: against the previous edition the change would read zero all day); None when
                      the name was not ranked then
Parts are empty for a read whose record predates its kinds (one session after this lands)."""
RANKED = 20
LABEL = {"trend": "Trend", "levels": "Support and resistance", "momentum": "Momentum", "divergence": "Divergence",
         "volume": "Volume", "volatility": "Volatility", "session": "Candles and gaps", "pattern": "Chart patterns",
         "wyckoff": "Wyckoff", "waves": "Elliott waves", "desk": "The desk's strategies"}


def _tenths(t):
    """ten-thousandths to the nearest tenth, halves away from zero (integers: exact)"""
    return (1 if t >= 0 else -1) * ((abs(t) + 500) // 1000)


def parts(kinds, evidence=None):
    """[{key, label, value}]: each kind's vote to a tenth, by the largest remainder so that the parts sum exactly to
    evidence (to a tenth; the kinds' own sum when None), in integers on the record's four decimals; strongest first,
    a kind that rounds to zero left out"""
    items = [(k, int(round(float(v) * 10000))) for k, v in sorted((kinds or {}).items()) if v]
    if not items:
        return []
    target = int(round(float(evidence) * 10)) if evidence is not None else _tenths(sum(t for _, t in items))
    base = [_tenths(t) for _, t in items]
    diff = target - sum(base)
    step = 1 if diff > 0 else -1
    order = sorted(range(len(items)), key=lambda j: step * (items[j][1] - 1000 * base[j]), reverse=True)
    for k in range(abs(diff)):
        base[order[k % len(order)]] += step
    out = [{"key": k, "label": LABEL.get(k, k[:1].upper() + k[1:]), "value": b / 10.0}
           for (k, _), b in zip(items, base) if b]
    return sorted(out, key=lambda p: (-abs(p["value"]), p["key"]))


def rows(ranked, records, listed, before):
    """the edition's ranked list (the module docstring) and {symbol: evidence} for the next session's delta"""
    out, now = [], {}
    for i, p in enumerate(ranked):
        sym = p["symbol"]
        e = round(float(p.get("evidence") or 0.0), 1)
        now[sym] = e
        if i >= RANKED:
            continue
        b = (before or {}).get(sym)
        out.append({"rank": i + 1, "symbol": sym, "take": p["gut"]["word"], "form": p["form"], "evidence": e,
                    "parts": parts((records.get(sym) or {}).get("kinds"), e), "r": (p.get("plan") or {}).get("r"),
                    "delta": None if b is None else round(e - b, 1), "listed": sym in listed})
    return out, now


def before_of(old, session):
    """{symbol: evidence} of the last edition of the session before `session`, from board.json's memory"""
    old = old or {}
    return dict((old.get("before") if old.get("as_of") == session else old.get("evidence")) or {})


def history(old, session, now):
    """board.json's ranking memory for the next edition: {"as_of", "evidence", "before"}"""
    return {"as_of": session, "evidence": now, "before": before_of(old, session)}
