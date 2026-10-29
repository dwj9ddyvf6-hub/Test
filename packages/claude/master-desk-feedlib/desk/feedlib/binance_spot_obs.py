"""One Binance spot observation per symbol per pass for the Ausar spot books (desk/sleeves/families/absorption.py and
ausar_spot_recipes.py).

Each book's capture reads, in its source's order, the exchange metadata, then the last trade, then the book ticker. Read
book by book, that was three requests a book a pass one after another: 15 requests and 11-13 s of every pass on
2026-10-17. The five books trade three symbols (ENJUSDT: iu_body and the ENJ absorption book; LINKUSDT: ai_volume and
the LINK absorption book; ADAUSDT: tomazetti_rsi2), so the pass's first capture observes the symbols of every due spot
book (the engine sets `feeds.due`) once, the symbols in parallel and each symbol's three reads in the source's order
(the quote after the last trade, which its age check needs), and the pass's later captures on a symbol read the same
observation, as every desk sleeve reads one quote a pass. A caller without a due list (a parity harness driving one
book) reads only its own symbol. A failed read is kept as its exception, so each capture records the same acquisition
error it did reading alone."""
from concurrent.futures import ThreadPoolExecutor

FAMILIES = ("absorption", "ausar_spot_recipes")


def _one(hub, symbol, info_fn):
    out = {}
    try:
        out["info"] = info_fn(symbol)
    except Exception as e:
        out["info_error"] = e
    try:
        out["last_trade"] = hub.binance.last_trade(symbol)
    except Exception as e:
        out["last_trade_error"] = e
    try:
        out["quote"] = hub.quotes("binance", [symbol], max_age=0).get(symbol)
    except Exception as e:
        out["quote"], out["quote_error"] = None, e
    return out


def wanted(feeds, symbol):
    """`symbol`, then the symbols of the pass's other due spot books."""
    out = [symbol]
    for s in getattr(feeds, "due", None) or ():
        cfg = getattr(s, "CONFIG", None)
        if cfg is not None and cfg.family in FAMILIES:
            out.extend(cfg.universe)
    return list(dict.fromkeys(out))


def observe(feeds, symbol, now, info_fn):
    """the pass's observation of `symbol`: {"info" | "info_error", "last_trade" | "last_trade_error", "quote"}."""
    memo = getattr(feeds, "_binance_spot_obs", None)
    if memo is None or memo["now"] != now:
        memo = {"now": now, "obs": {}}
        feeds._binance_spot_obs = memo
    obs = memo["obs"]
    if symbol not in obs:
        todo = [s for s in wanted(feeds, symbol) if s not in obs]
        with ThreadPoolExecutor(len(todo)) as pool:
            for s, r in zip(todo, pool.map(lambda s: _one(feeds.hub, s, info_fn), todo)):
                obs[s] = r
    return obs[symbol]
