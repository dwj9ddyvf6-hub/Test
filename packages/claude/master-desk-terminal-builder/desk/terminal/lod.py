"""ChartsLector's low-of-day entry on a listed card, in the regular session (P2): his rule on the session's running
low, read from the desk's cached hourly bars (the terminal requests nothing), with the ATR14 of the last completed
session (Wilder's, SMA-seeded: read/clx.py):

  zone   from the low of day to the low + 0.65 ATR (his entry zone)
  stop   the low - 0.1 ATR (his stop)
  state  blue: the price in the zone with the stop under 1 ATR and at most 4% of the price away; orange: in the zone
         with the stop more than 4% away (his orange line); red: above the zone, or the stop 1 ATR or more away

Only its levels (in the card's dollars) and the state's word are published; outside the regular session there is
none, and a name the caches hold no hour bars of today for, or whose newest hour began two hours ago or more, has
none. It is his rule, so the page credits him: context, voting nothing. The hour bars are the hub's (on Alpaca's clock
grid the one holding the open includes its last half hour of pre-market; Yahoo's start at the open).

lod(hourly, daily, now) -> {low, zone_low, zone_high, stop, state} or None"""
from .. import calendar as cal
from .read import clx

ZONE_ATR, STOP_ATR, ORANGE_PCT = 0.65, 0.1, 4.0
KEYS = {"low", "zone_low", "zone_high", "stop", "state"}      # the edition's setups[].lod
HOURS = 12                      # the hour bars a card reads: a whole session's, pre-market included
STALE_S = 7200                  # the newest hour must have begun within two hours of now


def _price(v):
    return round(v, 2) if v >= 1 else round(v, 4)


def lod(hourly, daily, now):
    """the card's low-of-day entry now (module docstring), or None outside the session or without today's bars"""
    d = cal._as_date(now)
    if not cal.is_trading_day(d):
        return None
    o, c = cal.session_open(d), cal.session_close(d)
    if not o <= now < c:
        return None
    today = [b for b in hourly or () if o - 1800 <= float(b["t"]) < now and b.get("l") is not None
             and b.get("c") is not None]
    prior = [b for b in daily or () if b.get("c") is not None and cal._as_date(float(b["t"])) < d]
    if not today or len(prior) < 15 or now - float(today[-1]["t"]) >= STALE_S:
        return None
    h, lo, cl = ([float(b[k]) for b in prior] for k in ("h", "l", "c"))
    atr = clx.ema_r(clx.true_range(h, lo, cl), 14, 1.0 / 14.0)[-1]
    if atr != atr or atr <= 0:
        return None
    low, price = min(float(b["l"]) for b in today), float(today[-1]["c"])
    risk = price - (low - STOP_ATR * atr)
    ok = price <= low + ZONE_ATR * atr and 0 < risk < atr
    state = "red" if not ok else "orange" if risk * 100.0 / price > ORANGE_PCT else "blue"
    return {"low": _price(low), "zone_low": _price(low), "zone_high": _price(low + ZONE_ATR * atr),
            "stop": _price(low - STOP_ATR * atr), "state": state}
