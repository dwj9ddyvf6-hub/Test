"""Polymarket public market data for the span harvest sleeve (desk/sleeves/families/prediction_markets.py).

  events ..... Gamma (gamma-api.polymarket.com/events/keyset?tag_slug=<sport>&closed=false&start_time_min/max, every
               page; active events only): two-way moneyline match events — tennis, MLB, UFC (the research corpus's
               "mma"), boxing, NPB — with the scheduled gameStartTime, both outcomes, their CLOB token ids and Gamma's
               outcome prices. The offset /events (active=true&closed=false&limit=200) answered at most 100 events
               and carried every season-long market of the tag: on 2026-10-17 the four sports' sweep was 12.0 MB for
               19 in-window matches, by start time 1.0 MB for the same 19 (identical records)
  trades ..... data-api.polymarket.com/v2/trades?condition=<conditionId>: the public trade prints (price, size,
               token_id, timestamp), newest first, paged by cursor. Data API v1 (/trades?market=, paged by offset)
               retires 2026-10-24 (docs.polymarket.com/migrate/data-api-v1-to-v2); on 2026-10-17 a live market's
               v1 and v2 rows were identical (17 of 17 by tx, token, time, price, size, side), and v1 was edge-cached
               for up to 300 s. v2 is cached too: CloudFront (behind Cloudflare) keeps each URL up to 300 s
               (x-cache: Hit, age), so a URL asked again within 5 minutes can miss the newest prints.
               trades_many: up to 20 markets a request (condition=<id>,<id>...), each market's rows exactly its own
               trades() read's (23 in-play markets on 2026-10-17: 23 requests / 1,282.5 KB -> 11 / 273.2 KB)
  book ....... clob.polymarket.com/book?token_id=<token>: best bid / ask (the simulated venue's live quote)
  market ..... gamma-api.polymarket.com/markets/<id>: closed + outcomePrices (the resolution, 1 / 0)
  corpus ..... the TimePortal public research release the source replays (timeportal.pro/polymarket/odds_data/
               clean_tapes.json + game_time_by_sport.json), cached 7 days

Every reader goes through the desk's data/http.get (per-host pacing, retries) and fails soft (None / [])."""
import json
import os
import time
from datetime import datetime, timezone

from ..data.http import get
from ..util import read_json, write_json_atomic

GAMMA = "https://gamma-api.polymarket.com"
CLOB = "https://clob.polymarket.com"
DATA = "https://data-api.polymarket.com"
TP_TAPES = "https://timeportal.pro/polymarket/odds_data/clean_tapes.json"
TP_CLOCK = "https://timeportal.pro/polymarket/odds_data/game_time_by_sport.json"
SPORT_TAGS = {"tennis": "tennis", "mlb": "mlb", "ufc": "mma", "boxing": "boxing", "npb": "npb"}
CORPUS_TTL_S = 7 * 86400
EVENTS_PAGE = 100                 # /events/keyset's largest page
EVENTS_PAGES = 30                 # a guard far above any tag (tennis: 286 events in 3 pages)
EVENTS_MARGIN_S = 24 * 3600       # the start-time filter reads the event's startTime; the window keeps the match's
                                  # (its moneyline's gameStartTime: equal in 143 of 143 match events, 2026-10-17)
DISCOVERY = {}                    # tag -> the last read: {"at", "ok", "events", "complete"} or its error
TRADE_PAGE = 500
TRADE_PAGES = 10
TRADE_BATCH = 20                  # condition ids a /v2/trades request takes (the API's cap: 20 distinct values)
BATCH_FIRST = 25                  # a batch's first page: a quiet batch's new prints fit (a page carries older ones too)
BATCH_PAGE = 1000                 # the API's largest page (a cursor keeps its first page's size)
BATCH_PAGES = 10
BATCH_SPREAD_S = 600
BATCH_THREADS = 8


def _ts(text):
    """Gamma's '2026-10-17 09:00:00+00' / ISO -> epoch seconds (None when unreadable)."""
    if not text:
        return None
    s = str(text).strip().replace(" ", "T")
    if s.endswith("+00"):
        s += ":00"
    s = s.replace("Z", "+00:00")
    try:
        d = datetime.fromisoformat(s)
    except ValueError:
        return None
    return (d if d.tzinfo else d.replace(tzinfo=timezone.utc)).timestamp()


def _list(v):
    if isinstance(v, list):
        return v
    try:
        out = json.loads(v or "[]")
        return out if isinstance(out, list) else []
    except (TypeError, ValueError):
        return []


def match_event(e, sport):
    """a Gamma event -> the match record (None unless it is a two-way moneyline match)."""
    ml = [m for m in (e.get("markets") or []) if m.get("sportsMarketType") == "moneyline"]
    if len(ml) != 1:
        return None
    m = ml[0]
    outcomes, tokens = _list(m.get("outcomes")), _list(m.get("clobTokenIds"))
    if len(outcomes) != 2 or len(tokens) != 2:
        return None
    start = _ts(m.get("gameStartTime")) or _ts(e.get("startTime"))
    if start is None:
        return None
    prices = []
    for p in _list(m.get("outcomePrices")):
        try:
            prices.append(float(p))
        except (TypeError, ValueError):
            prices.append(None)
    return {"event_id": str(e.get("id")), "title": str(e.get("title") or m.get("question") or ""), "sport": sport,
            "start_ts": start, "market_id": str(m.get("id")), "condition_id": str(m.get("conditionId") or ""),
            "outcomes": [str(o) for o in outcomes], "tokens": [str(t) for t in tokens],
            "prices": prices if len(prices) == 2 else [None, None], "closed": bool(m.get("closed"))}


def _iso(ts):
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def tag_events(tag, now, fetch=get, lookback_s=12 * 3600, ahead_s=24 * 3600):
    """(active open events of a Gamma tag whose start lies within [now - lookback, now + ahead] widened by
    EVENTS_MARGIN_S, complete): /events/keyset by start time, every page (a page is full until the last; the offset
    /events stops at 100 events: tennis showed 40 of 226 in-window matches). complete is False when the page guard
    stopped it; a failed page raises (no partial list)."""
    params = {"tag_slug": tag, "closed": "false", "limit": EVENTS_PAGE,
              "start_time_min": _iso(now - lookback_s - EVENTS_MARGIN_S),
              "start_time_max": _iso(now + ahead_s + EVENTS_MARGIN_S)}
    out, cursor = [], None
    for _ in range(EVENTS_PAGES):
        doc = fetch(GAMMA + "/events/keyset", dict(params, after_cursor=cursor) if cursor else params) or {}
        out += [e for e in doc.get("events") or [] if e.get("active")]     # the offset query's active=true
        cursor = doc.get("next_cursor")
        if not cursor:
            return out, True
    return out, False


def match_events(now, fetch=get, lookback_s=12 * 3600, ahead_s=24 * 3600, tags=None):
    """open two-way moneyline matches starting in [now - lookback, now + ahead], for the Gamma tags given
    ({tag: sport}; default every tag in SPORT_TAGS). A tag whose read failed is skipped this round; each tag's
    events, pages and completeness are in DISCOVERY."""
    out = {}
    for tag, sport in (SPORT_TAGS if tags is None else tags).items():
        try:
            evs, complete = tag_events(tag, now, fetch=fetch, lookback_s=lookback_s, ahead_s=ahead_s)
        except Exception as e:
            DISCOVERY[tag] = {"at": now, "ok": False, "error": f"{type(e).__name__}: {str(e)[:120]}"}
            continue
        DISCOVERY[tag] = {"at": now, "ok": True, "events": len(evs), "complete": complete}
        for e in evs:
            r = match_event(e, sport)
            if r and now - lookback_s <= r["start_ts"] <= now + ahead_s:
                out[r["event_id"]] = r
    return out


def trades(condition_id, since_ts, fetch=get):
    """the market's public trade prints at or after since_ts, oldest first: [{ts, asset, price, size, tx}].
    Data API v2: {data, pagination: {next_cursor}}, snake_case rows (token_id, transaction_hash); a v1 list of
    camelCase rows (asset, transactionHash) is still read the same way."""
    rows, seen, cursor = [], set(), None
    for page in range(TRADE_PAGES):
        params = {"condition": condition_id, "limit": TRADE_PAGE} if cursor is None else \
            {"condition": condition_id, "cursor": cursor}
        try:
            doc = fetch(DATA + "/v2/trades", params)
        except Exception:
            break
        got = doc.get("data") if isinstance(doc, dict) else doc
        if not got:
            break
        stop = False
        for r in got:
            try:
                ts, px = float(r["timestamp"]), float(r["price"])
            except (KeyError, TypeError, ValueError):
                continue
            if ts < since_ts:
                stop = True
                continue
            tx = r.get("transaction_hash", r.get("transactionHash"))
            asset = r.get("token_id", r.get("asset"))
            key = (tx, str(asset), ts, px, r.get("size"), r.get("side"))
            if key in seen:
                continue
            seen.add(key)
            rows.append({"ts": ts, "asset": str(asset), "price": px, "size": float(r.get("size") or 0.0), "tx": tx})
        cursor = (doc.get("pagination") or {}).get("next_cursor") if isinstance(doc, dict) else None
        if stop or not cursor:
            break
    rows.sort(key=lambda r: (r["ts"], r["tx"] or "", r["price"]))
    return rows


def _batches(since):
    """condition ids grouped for batched reads: newest `since` first, at most TRADE_BATCH a batch, and a batch's sinces
    within BATCH_SPREAD_S of its newest (a quiet market's old since would page an active one's prints back to it)."""
    out, cur = [], []
    for c in sorted(since, key=lambda c: (-since[c], c)):
        if cur and (len(cur) >= TRADE_BATCH or since[cur[0]] - since[c] > BATCH_SPREAD_S):
            out.append(cur)
            cur = []
        cur.append(c)
    return out + ([cur] if cur else [])


def _read_batch(batch, since, fetch):
    """one batch of trades_many: {condition_id: rows}."""
    ids = {c.lower(): c for c in batch}
    floor = since[batch[-1]]
    got, seen = {c: [] for c in batch}, {c: set() for c in batch}
    cursor, oldest, complete, limit, restarted, stray = None, None, False, BATCH_FIRST, False, False
    for _ in range(BATCH_PAGES):
        params = {"condition": ",".join(batch), "limit": limit} if cursor is None else \
            {"condition": ",".join(batch), "cursor": cursor}
        try:
            doc = fetch(DATA + "/v2/trades", params)
        except Exception:
            complete = None                              # failed: what was read stands, nothing is read alone
            break
        rows = doc.get("data") if isinstance(doc, dict) else doc
        if not rows:
            complete = True
            break
        newest = None
        for r in rows:
            try:
                ts, px = float(r["timestamp"]), float(r["price"])
            except (KeyError, TypeError, ValueError):
                continue
            newest = ts if newest is None else max(newest, ts)
            oldest = ts if oldest is None else min(oldest, ts)
            if ts < floor:
                complete = True
                continue
            c = ids.get(str(r.get("condition_id", r.get("conditionId")) or "").lower())
            if c is None:                                # a print no member's id names: every market is read alone
                stray = True
                continue
            if ts < since[c]:
                continue
            tx = r.get("transaction_hash", r.get("transactionHash"))
            asset = r.get("token_id", r.get("asset"))
            key = (tx, str(asset), ts, px, r.get("size"), r.get("side"))
            if key in seen[c]:
                continue
            seen[c].add(key)
            got[c].append({"ts": ts, "asset": str(asset), "price": px, "size": float(r.get("size") or 0.0), "tx": tx})
        cursor = (doc.get("pagination") or {}).get("next_cursor") if isinstance(doc, dict) else None
        if complete or not cursor:
            complete = True
            break
        if not restarted and newest is not None:
            # the small first page did not reach back: read again from the newest, the page sized by the prints a
            # second this one held over the time still to cover. Only the new read's prints count: each URL is
            # cached apart (CloudFront, up to 300 s), and two snapshots could leave a gap below the newest print
            est = len(rows) * (newest - floor) / max(newest - oldest, 1.0)
            limit = min(BATCH_PAGE, max(4 * BATCH_FIRST, int(1.25 * est) + BATCH_FIRST))
            cursor, restarted, oldest = None, True, None
            got, seen = {c: [] for c in batch}, {c: set() for c in batch}
    out = {}
    for c in batch:
        short = complete is False and (oldest is None or since[c] <= oldest)
        if short or stray or len(got[c]) > TRADE_PAGE * TRADE_PAGES:
            out[c] = trades(c, since[c], fetch=fetch)
        else:
            out[c] = sorted(got[c], key=lambda r: (r["ts"], r["tx"] or "", r["price"]))
    return out


def trades_many(since_by_condition, fetch=get):
    """trades(condition_id, since) for many markets, TRADE_BATCH condition ids a request: {condition_id: rows}, each
    market's rows exactly those trades(condition_id, since) returns. A batch's feed is newest first across its
    markets (keyset by block time), so it is read until a print older than the batch's oldest since (or the feed's
    end): every market's window is then complete. The first page is small; when it does not reach back that far
    the batch is read again from the newest in pages sized by that page's prints per second (a re-read print is
    deduplicated like any other). A market the page budget did not reach back to, or one with more prints in its
    window than trades() pages (TRADE_PAGES x TRADE_PAGE: it keeps the newest), is read alone by trades(), and so is
    every market of a batch whose feed held a print no member's condition id names (rows are split by that field); a
    failed read leaves the prints read so far, as trades() does. Batches are read side by side."""
    since = {str(c): float(s) for c, s in since_by_condition.items() if c}
    batches = _batches(since)
    if len(batches) > 1:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=min(BATCH_THREADS, len(batches))) as pool:
            parts = list(pool.map(lambda b: _read_batch(b, since, fetch), batches))
    else:
        parts = [_read_batch(b, since, fetch) for b in batches]
    out = {}
    for part in parts:
        out.update(part)
    return out


def book(token, fetch=get):
    """best bid / ask of a token's CLOB book (None when a side is empty or the read fails)."""
    try:
        b = fetch(CLOB + "/book", {"token_id": token})
    except Exception:
        return None
    try:
        bids = [float(x["price"]) for x in (b or {}).get("bids") or []]
        asks = [float(x["price"]) for x in (b or {}).get("asks") or []]
    except (KeyError, TypeError, ValueError):
        return None
    if not bids or not asks:
        return None
    return {"bid": max(bids), "ask": min(asks)}


def resolution(market_id, fetch=get):
    """{"closed", "prices"} of a Gamma market (prices "1" / "0" once resolved)."""
    try:
        m = fetch(GAMMA + "/markets/" + str(market_id))
    except Exception:
        return None
    if not m:
        return None
    prices = []
    for p in _list(m.get("outcomePrices")):
        try:
            prices.append(float(p))
        except (TypeError, ValueError):
            prices.append(None)
    return {"closed": bool(m.get("closed")), "prices": prices,
            "resolved": str(m.get("umaResolutionStatus") or "").lower() == "resolved"}


def corpus(d, now, fetch=get):
    """(tapes_path, clock_path) of the cached TimePortal release (refetched weekly; the stale copy beats none)."""
    os.makedirs(d, exist_ok=True)
    out = []
    for url, name in ((TP_TAPES, "clean_tapes.json"), (TP_CLOCK, "game_time_by_sport.json")):
        path = os.path.join(d, name)
        fresh = os.path.exists(path) and now - os.path.getmtime(path) < CORPUS_TTL_S
        if not fresh:
            try:
                doc = fetch(url, None, timeout=90)
                if isinstance(doc, dict) and doc:
                    write_json_atomic(path, doc)
            except Exception:
                pass
        out.append(path if os.path.exists(path) else None)
    return tuple(out)


def load_state(path):
    return read_json(path, None) or {"matches": {}, "events_at": 0}


def save_state(path, doc):
    try:
        write_json_atomic(path, doc)
    except OSError:
        pass


def now_ts():
    return time.time()
