"""SPAN HARVEST UNIFIED (span-harvest-unified @649e71f1 span_harvest_unified.py v1.2.0, vendored byte-exact as
desk/vendor/span_harvest/span_harvest_unified.py) forward-tested on live Polymarket match tapes, on the labelled
simulated venue sim:polymarket (live CLOB quotes).

The source's two layers decide everything:
  PZOE  select_profile(): from OLDER matches only — the first hierarchy group (sport + cohort + opening bucket,
        sport + cohort, cohort + bucket, sport, cohort, all) with >= 30 priors — a frozen profile (14) whose replay
        clears >= 5 resolved fills, 85% coverage and positive family-wise / cluster lower bounds with and without
        the best trade; otherwise NO_TRADE (the study: on its own release no profile clears — the gate is the edge).
  APZI  simulate_profile(): rung 1 rests at 55% of the opening price through relative clock 0.25, then 38%
        (first-crossing fill); rungs 2-3 need a 1.5c bounce off the 8-minute low, a non-negative 6-minute slope, no
        falling knife / toxic print, price 15-85c, before clock 0.80; inventory A 34% harvest at
        ceil(max(2.15 x avg, avg + 18c)), B 33% target max(72c, avg + tick) or a 38% giveback with the slope <= 0.002,
        C 33% rides or transfers to B when the state score <= 0.28; salvage <= 8c falling; flatten at 240 min;
        settlement 1 / 0; an unknown end stays unresolved.

The sleeve replays the source's state machine on each live match's tape-so-far every pass (the state machine is
causal: its decisions on a prefix are exactly the full replay's up to that print) and carries out the new ones.

Named divergences (inputs the source read from TimePortal, which stopped publishing — its list.json was last
generated 2026-10-06 — and plumbing of a replay engine turned into a live sleeve):
  1. candidates: Polymarket two-way moneyline matches (Gamma: MLB, UFC = the corpus's "mma", boxing, NPB; no tennis,
     the owner's call on 2026-10-17: SPORTS_OFF) starting within the next 24 h; the tracked side is the market underdog — the lower Gamma price at the last read
     before the start, else the lower first post-start print (the source tracked TimePortal's astrological pick);
     the cohort is "cohort unavailable", TimePortal's own label when it had no cohort, so the source's hierarchy
     falls back by itself.
  2. tape: the tracked token's public trade prints (data-api) at or after Gamma's scheduled start, unfiltered like
     the release's p array (the source: TimePortal's recorder prints and its verified real starts); the end is the
     first run of 3 prints >= 99.9c (won: the $1 settlement event there) or <= 0.1c, the result Gamma's resolution.
  3. priors: TimePortal's public release (clean_tapes.json, game_time_by_sport.json for the sport clocks) plus the
     sleeve's own completed tapes, each a prior once resolved (the replay counted every earlier-starting match,
     including ones still in play at the decision — a hindsight live trading cannot have).
  4. execution: entries rest as limits at the state machine's fill price for 10 minutes; exits and the settlement
     sell at the live bid (a limit at 0.1c); a lost settlement books at 0.1c (the simulated venue needs a positive
     quote); stake 1% of the sleeve's capital per match (the source's $1 unit) in whole shares, the inventory's
     last sale closing whatever is held; no fees (Polymarket's sports
     moneylines; the source's default fee_per_share 0).
  5. cadence: a pass every 60 s; Gamma refreshed every 10 minutes, resolutions read every 10 minutes after the
     first hour.

Not ported: nothing gates this sleeve but the source's own PZOE gate. The engine marks open positions between fills
at the mid of the token's CLOB book (the hub's "polymarket" quote source); a resolved market's empty book leaves
the last mark until the settlement closes the position."""
import json
import math
import os
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor

from ...contract import Intent, OrderSpec, Sleeve, SleeveConfig
from ...feedlib import polymarket as PM
from ...vendor.span_harvest import span_harvest_unified as SH
from ...venues.sim import SimVenue

SLEEVE_ID = "span_harvest_unified"
SOURCE = {"repo": "span-harvest-unified", "ref": "main", "commit": "649e71f1473130b5df78b9bc9b34cfc7287a3d59",
          "path": "span_harvest_unified.py", "blob_sha": "6ab429a494c58d68092c51418480337ee875c26b"}
VENUE = "sim:polymarket"
CAPITAL = 100_000.0
STAKE_PCT = 0.01
PROFILES = SH.profile_library()
PROFILE_BY_ID = {p.profile_id: p for p in PROFILES}
GATE = SH.Gate()
COHORT = "cohort unavailable"
EVENTS_REFRESH_S = 600
RESOLVE_AFTER_S = 3600
RESOLVE_EVERY_S = 600
STALE_AFTER_S = 3 * 86400
PREGAME_MAX_AGE_S = 2 * 3600
END_RUN = 3
WON_PX, LOST_PX = 0.999, 0.001
SETTLE_LOST_PX = 0.001
EXIT_LIMIT = 0.001
ENTRY_WINDOW_S = 600
EXIT_WINDOW_S = 3600
QUOTE_TTL_S = 15
MAX_LIVE = 400                    # a runaway-state guard, far above the live match count
SPORTS_OFF = {"tennis"}           # the owner, 2026-10-17: no tennis matches. Discovery skips them, a pending one
                                  # is dropped, and an unheld one is never entered; a held one runs its exits

_TRADE_CACHE = {}
_FEATURE_CACHE = {}
_CORPUS = {"key": None, "tapes": [], "clock": None}
_SETTLED = {}
_QUOTES = {}


# -- the live tape in the release's record layout ----------------------------------------------------------------------
def end_index(prices):
    """the first run of END_RUN prints all >= 99.9c (won) or all <= 0.1c (lost): (index, 'won'|'lost') or None."""
    for i in range(len(prices) - END_RUN + 1):
        run = prices[i:i + END_RUN]
        if all(p >= WON_PX for p in run):
            return i, "won"
        if all(p <= LOST_PX for p in run):
            return i, "lost"
    return None


def live_record(m):
    """the match so far as a clean_tapes record (Tape.from_record parses it, exactly as the source's loader)."""
    prints = m.get("prints") or []
    if not prints:
        return None
    t = [float(ts) for ts, _ in prints]
    p = [float(px) for _, px in prints]
    rec = {"id": m["event_id"], "sport": m["sport"], "favcohort_tracked": COHORT, "open": p[0], "p": p, "t": t,
           "start_ts": float(m["start_ts"]), "result": m.get("result"), "end_recorded": bool(m.get("result")),
           "settlement_i": None}
    if m.get("result") == "won":
        end = end_index(p)
        i = end[0] if end and end[1] == "won" else len(p)
        rec["p"] = p[:i] + [1.0]
        rec["t"] = t[:i] + [t[i] if i < len(t) else max(t[-1], float(m.get("resolved_at") or t[-1]))]
        rec["settlement_i"] = i
    return rec


def tape_of(m):
    rec = live_record(m)
    return SH.Tape.from_record(rec) if rec else None


def corpus_tapes(tp_path, own_records):
    """the source's own loader on the release + the sleeve's completed tapes, chronological."""
    tapes = []
    if tp_path and os.path.exists(tp_path):
        _payload, tapes, _rejected = SH.load_tapes(tp_path)
    for rec in own_records or []:
        t = SH.Tape.from_record(rec)
        if t is not None and t.last_tradable_i >= 0:
            tapes.append(t)
    tapes.sort(key=lambda tape: (tape.start_ts, tape.match_id))
    return tapes


def priors_for(tape, corpus):
    """older matches only (the replay's ordered[:index]: start before this one, ties broken by match id)."""
    key = (tape.start_ts, tape.match_id)
    return [t for t in corpus if (t.start_ts, t.match_id) < key]


def select(tape, corpus, clock):
    """PZOE for one live match: (profile or None, selection record)."""
    return SH.select_profile(tape, priors_for(tape, corpus), clock, PROFILES, GATE,
                             trade_cache=_TRADE_CACHE, feature_cache=_FEATURE_CACHE)


def shares_of(x):
    """whole shares, rounded down (the desk's simulated venues sell whole units)."""
    return float(math.floor(float(x) + 1e-9))


def actions(tape, profile, clock):
    """the state machine's fills / exits on the tape so far: [(key, kind, row)] in print order."""
    tr = SH.simulate_profile(tape, profile, clock)
    out = [(f"e:{r['i']}:R{r['rung']}", "enter", r) for r in tr.entries]
    out += [(f"x:{r['i']}:{r['sleeve']}:{r['reason']}", "exit", r) for r in tr.exits if r["shares"] > SH.EPS]
    out.sort(key=lambda a: (a[2]["i"], 0 if a[1] == "enter" else 1, a[0]))
    return tr, out


# -- the sleeve ---------------------------------------------------------------------------------------------------------
class SpanHarvest(Sleeve):
    def __init__(self):
        self.CONFIG = SleeveConfig(
            sleeve_id=SLEEVE_ID, family="prediction_markets", cadence_s=60, schedule="always", universe=(),
            capital=CAPITAL, needs={"feeds": ["pm_span"]}, venue_pref=VENUE, source=SOURCE,
            params={"stake_pct": STAKE_PCT, "profiles": [p.profile_id for p in PROFILES], "gate": "SH.Gate()",
                    "cohort": COHORT})
        self.engine = None
        self._st = None

    def bind(self, engine):
        self.engine = engine
        if VENUE not in engine.venues:
            engine.venues[VENUE] = SimVenue(VENUE, self.quote, orders=engine.sim_orders.setdefault("polymarket", {}),
                                            fee_bps=0.0, clock=engine.clock, max_quote_age_s=120)

    def quote(self, token):
        """the simulated venue's quote: the live CLOB book, the settlement price once the market resolved."""
        now = self.engine.clock() if self.engine is not None else time.time()
        if token in _SETTLED:
            px = _SETTLED[token]
            return {"bid": px, "ask": px, "t": now}
        hit = _QUOTES.get(token)
        if hit and now - hit[0] < QUOTE_TTL_S:
            return hit[1]
        b = PM.book(token)
        q = {"bid": b["bid"], "ask": b["ask"], "t": now} if b else None
        _QUOTES[token] = (now, q)
        return q

    def signal(self, view):
        feed = (view.extra or {}).get("pm_span") or {}
        st = {"matches": dict((view.state or {}).get("matches") or {})}
        self._st = st
        clock, corpus = feed.get("clock"), feed.get("corpus") or []
        out = []
        if clock is None:
            return out
        stake = CAPITAL * STAKE_PCT
        for eid, m in sorted((feed.get("matches") or {}).items()):
            if not m.get("token") or not m.get("prints"):
                continue
            off = m.get("sport") in SPORTS_OFF               # a sport the owner took off: exits of a held one only
            if off and m["token"] not in (view.positions or {}):
                continue
            tape = tape_of(m)
            if tape is None:
                continue
            ms = dict(st["matches"].get(eid) or {})
            if "profile" not in ms:
                profile, sel = select(tape, corpus, clock)
                ms.update(profile=profile.profile_id if profile else None, reason=sel["reason"],
                          group=list(sel.get("group") or []), group_matches=sel.get("group_matches"),
                          token=m["token"], side=m.get("side_name"), done=[])
                out.append(Intent("signal", m["token"], asset="spot", venue=VENUE,
                                  reason=(f"{SLEEVE_ID} {m.get('title', eid)}: tracked {m.get('side_name')} open "
                                          f"{tape.opening:.3f}; {sel['reason']}"
                                          + (f" -> {profile.profile_id}" if profile else ""))[:300],
                                  meta={"event": eid, "group": ms["group"], "group_matches": ms["group_matches"],
                                        "profile": ms["profile"]},
                                  signal_key=f"sh:{eid}:selection"))
            st["matches"][eid] = ms
            if not ms["profile"]:
                continue
            tr, acts = actions(tape, PROFILE_BY_ID[ms["profile"]], clock)
            done = set(ms.get("done") or [])
            left = 0.0                                     # the state machine's inventory after each action
            for key, kind, row in acts:
                left += row["capital"] / max(SH.TICK, row["price"]) if kind == "enter" else -row["shares"]
                if key in done:
                    continue
                done.add(key)
                if kind == "enter" and off:
                    continue
                if kind == "enter":
                    qty = shares_of(row["capital"] / max(SH.TICK, row["price"]) * stake)
                    out.append(Intent("enter", m["token"], asset="spot", venue=VENUE, qty=qty,
                                      order=OrderSpec(type="limit", limit_price=round(float(row["price"]), 4),
                                                      window_s=ENTRY_WINDOW_S),
                                      signal_key=f"sh:{eid}:{key}", price_hint=float(row["price"]),
                                      reason=f"{SLEEVE_ID} {ms['profile']} rung {row['rung']} at "
                                             f"{row['price']:.4f} (limit {row['limit']:.4f})"[:300],
                                      meta={"position_meta": {"event": eid, "profile": ms["profile"],
                                                              "rung": row["rung"]}}))
                else:                                      # the last sale of the inventory closes what is held
                    qty = None if left <= SH.EPS * 1e3 else shares_of(row["shares"] * stake)
                    out.append(Intent("exit", m["token"], asset="spot", venue=VENUE, qty=qty,
                                      order=OrderSpec(type="limit", limit_price=EXIT_LIMIT, window_s=EXIT_WINDOW_S),
                                      signal_key=f"sh:{eid}:{key}", price_hint=float(row["price"]),
                                      reason=f"{SLEEVE_ID} {row['reason']} sleeve {row['sleeve']} at "
                                             f"{row['price']:.4f}"[:300]))
            ms["done"] = sorted(done)
            ms["status"] = tr.status
        for eid in list(st["matches"]):
            if eid not in (feed.get("matches") or {}):
                st["matches"].pop(eid)
        return out

    def update_state(self, view, intents):
        return self._st if self._st is not None else dict(view.state or {})


# -- the producer: Gamma + trades + resolutions, persisted under <root>/cache/span_harvest ------------------------------
def _dir(feeds):
    root = os.path.dirname(feeds.hub.cache.root) if getattr(feeds, "hub", None) is not None else "cache"
    d = os.path.join(root, "span_harvest")
    os.makedirs(d, exist_ok=True)
    return d


def trade_since(m):
    """the oldest print track() reads for an in-play match this pass (None: it reads none): from the start until the
    tracked side is known, then from the last print."""
    if m.get("token"):
        return float(m.get("last_ts") or m["start_ts"])
    return None if m.get("no_underdog") else float(m["start_ts"])


def track(m, now, fetch=PM.get, trades=None):
    """advance one match: the tracked side at the start, new prints, the end and the resolution. trades(condition,
    since): the prints read (default PM.trades; the producer serves them from its batched read)."""
    if trades is None:
        def trades(cid, since):
            return PM.trades(cid, since, fetch=fetch)
    if now < m["start_ts"] or m.get("finished"):
        return m
    if not m.get("token") and not m.get("no_underdog"):
        pre = m.get("pregame") or {}
        prices = pre.get("prices") or []
        side = None
        if len(prices) == 2 and None not in prices and m["start_ts"] - float(pre.get("at") or 0) <= PREGAME_MAX_AGE_S \
                and prices[0] != prices[1]:
            side = 0 if prices[0] < prices[1] else 1
        else:
            first = {}
            for r in trades(m["condition_id"], m["start_ts"]):
                first.setdefault(r["asset"], r["price"])
            a, b = first.get(m["tokens"][0]), first.get(m["tokens"][1])
            if a is not None and b is not None and a != b:
                side = 0 if a < b else 1
        if side is None:
            if now - m["start_ts"] > 1800:
                m["no_underdog"] = True
            return m
        m.update(token=m["tokens"][side], side=side, side_name=m["outcomes"][side], prints=[], last_ts=m["start_ts"])
    if m.get("token"):
        new = [r for r in trades(m["condition_id"], float(m.get("last_ts") or m["start_ts"]))
               if r["asset"] == m["token"] and r["ts"] >= m["start_ts"]]
        seen = set(tuple(x) for x in m.get("seen") or [])
        for r in new:
            k = (r["tx"], r["ts"], r["price"], r["size"])
            if k in seen:
                continue
            seen.add(k)
            m["prints"].append([r["ts"], r["price"]])
        m["prints"].sort(key=lambda x: x[0])
        if new:
            m["last_ts"] = max(r["ts"] for r in new)
        m["seen"] = [list(k) for k in seen if k[1] >= float(m.get("last_ts") or 0) - 60]
    if now - m["start_ts"] >= RESOLVE_AFTER_S and now - float(m.get("res_at") or 0) >= RESOLVE_EVERY_S:
        m["res_at"] = now
        res = PM.resolution(m["market_id"], fetch=fetch)
        if res and res["closed"] and len(res["prices"]) == 2 and m.get("side") is not None:
            px = res["prices"][m["side"]]
            if px is not None and px >= WON_PX:
                m["result"] = "won"
            elif px is not None and px <= LOST_PX:
                m["result"] = "lost"
            if m.get("result"):
                m["finished"], m["resolved_at"] = True, now
                _SETTLED[m["token"]] = 1.0 if m["result"] == "won" else SETTLE_LOST_PX
    if not m.get("finished") and now - m["start_ts"] > STALE_AFTER_S:
        m["finished"], m["unresolved"] = True, True
    return m


_LIVE = {}
_OWN = {}                  # live.json path -> {"recs": the completed tapes (the last COMPLETED_KEEP), "lines": the file's}
_SAVED = {}                # live.json path -> the document as last written (a step that changed nothing writes nothing)
COMPLETED_KEEP = 2000      # the priors the sleeve keeps: its last completed tapes
COMPLETED_SLACK = 400      # completed.jsonl is rewritten to the last COMPLETED_KEEP once it holds this many more


def _write_completed(path, recs):
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), prefix=".tmp_")
    try:
        with os.fdopen(fd, "w") as f:
            f.writelines(json.dumps(r, sort_keys=True) + "\n" for r in recs)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def _load_completed(d, doc):
    """the completed tapes: completed.jsonl, one a line, each appended once as its match finishes (a live.json of
    the earlier layout carried them in doc["completed"], rewritten with the matches at every step: they move over
    once). A line torn by a crash mid-append is dropped and the file rewritten whole, so the next append is clean."""
    path = os.path.join(d, "completed.jsonl")
    old = doc.pop("completed", None)
    if not os.path.exists(path):
        recs = list(old or [])[-COMPLETED_KEEP:]
        _write_completed(path, recs)
        return {"recs": recs, "lines": len(recs)}
    with open(path, "rb") as f:
        raw = f.read()
    recs, torn = [], bool(raw) and not raw.endswith(b"\n")
    for line in raw.decode("utf-8", "replace").splitlines():
        try:
            recs.append(json.loads(line))
        except ValueError:
            torn = True
    if torn:
        _write_completed(path, recs)
    return {"recs": recs[-COMPLETED_KEEP:], "lines": len(recs)}


def produce(d, now, fetch=PM.get):
    """one producer step (memoised per pass by the feed layer): the live state + the corpus for the sleeve."""
    path = os.path.join(d, "live.json")
    doc = _LIVE.get(path)
    if doc is None:
        doc = _LIVE[path] = PM.load_state(path)
    if path not in _OWN:
        _OWN[path] = _load_completed(d, doc)
    ms = doc.setdefault("matches", {})
    if now - float(doc.get("events_at") or 0) >= EVENTS_REFRESH_S:
        doc["events_at"] = now
        for eid, m in list(ms.items()):                   # a pending match of a sport now off can hold nothing
            if m.get("sport") in SPORTS_OFF and not m.get("finished") and now < m["start_ts"]:
                ms.pop(eid)
        tags = {t: sp for t, sp in PM.SPORT_TAGS.items() if sp not in SPORTS_OFF}
        for eid, r in PM.match_events(now, fetch=fetch, tags=tags).items():
            cur = ms.get(eid)
            if cur is None:
                if sum(1 for x in ms.values() if not x.get("finished")) >= MAX_LIVE:
                    continue
                cur = ms[eid] = dict(r)
            if now < cur["start_ts"]:
                cur["pregame"] = {"prices": r["prices"], "at": now}
    stored = _OWN[path]
    own = list(stored["recs"])
    ids = {r.get("id") for r in own}
    was = {eid: bool(m.get("finished")) for eid, m in ms.items()}
    live = [m for m in ms.values() if not m.get("finished") and now >= m["start_ts"]]
    if live:
        # every in-play match's prints in batched reads (PM.trades_many: 20 markets a request, each market's rows
        # exactly what its own read returns); a read from further back than the batch went is made alone
        want = {}
        for m in live:
            s = trade_since(m) if m.get("condition_id") else None
            if s is not None:
                want[m["condition_id"]] = min(s, want.get(m["condition_id"], s))
        got = PM.trades_many(want, fetch=fetch) if want else {}

        def trades(cid, since):
            if cid not in got or since < want[cid]:
                return PM.trades(cid, since, fetch=fetch)
            return [r for r in got[cid] if r["ts"] >= since]
        with ThreadPoolExecutor(max_workers=min(8, len(live))) as pool:   # the resolution reads run side by side
            list(pool.map(lambda m: track(m, now, fetch=fetch, trades=trades), live))
    for eid, m in list(ms.items()):
        if m.get("finished") and not was[eid] and m.get("token") and m.get("result"):
            rec = live_record(m)
            if rec and rec["id"] not in ids:          # once, even if a crash re-finished it after the append
                own.append(rec)
                ids.add(rec["id"])
        if m.get("finished") and m.get("token") and m.get("result"):
            _SETTLED[m["token"]] = 1.0 if m["result"] == "won" else SETTLE_LOST_PX
        if m.get("finished") and now - float(m.get("resolved_at") or m["start_ts"]) > STALE_AFTER_S:
            ms.pop(eid)
    new = own[len(stored["recs"]):]
    done = os.path.join(d, "completed.jsonl")
    if new:
        with open(done, "a") as f:
            f.writelines(json.dumps(r, sort_keys=True) + "\n" for r in new)
            f.flush()
            os.fsync(f.fileno())
        stored["lines"] += len(new)
    kept = own[-COMPLETED_KEEP:]
    if stored["lines"] > COMPLETED_KEEP + COMPLETED_SLACK:
        _write_completed(done, kept)
        stored["lines"] = len(kept)
    stored["recs"] = kept
    body = json.dumps(doc, sort_keys=True, default=str)
    if _SAVED.get(path) != body:
        PM.save_state(path, doc)
        _SAVED[path] = body
    tp_path, clock_path = PM.corpus(d, now, fetch=fetch)
    key = (tp_path and os.path.getmtime(tp_path), clock_path and os.path.getmtime(clock_path), len(own),
           own[-1]["id"] if own else None)
    if _CORPUS["key"] != key:
        tapes = corpus_tapes(tp_path, own)
        _CORPUS.update(key=key, tapes=tapes,
                       clock=SH.load_clock_reference(clock_path, tapes) if clock_path else None)
    return {"matches": {k: v for k, v in ms.items() if v.get("token")}, "corpus": _CORPUS["tapes"],
            "clock": _CORPUS["clock"], "n_live": sum(1 for v in ms.values() if not v.get("finished")),
            "n_completed": len(own)}


def _feed_span(feeds, sleeve, now, arg):
    return produce(_dir(feeds), now)


FEEDS = {"pm_span": _feed_span}


def sleeves():
    return [SpanHarvest()]
