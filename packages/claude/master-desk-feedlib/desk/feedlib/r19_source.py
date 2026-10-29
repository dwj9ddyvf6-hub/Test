"""The R19 source acquisition layer, run as-is: the vendored backend/r19_data.py Collector (its sqlite market cache,
asset census, corporate actions, raw SIP daily bars, IEX latest quotes), backend/r19_intraday_data.py (IEX
regular-session 30/10-minute bars, 09:30-anchored hours, observed split transforms) and the decision modules.
Only their I/O is bound to this desk:

  * the authenticated GET (r19_data.alpaca_get, which read a private credentials file) -> the desk's Alpaca client
    (`getter`), the same four endpoints (paper /v2/assets, data /v2/stocks/bars, /v1/corporate-actions,
    /v2/stocks/quotes/latest); the receipt hash is over the parsed body (the source hashed the raw bytes);
  * exchange_calendars' XNYS (backend/providers._nyse, a library the desk does not carry) -> `DeskXNYS`, the desk's
    rule calendar plus the exchange's ad-hoc closures and special closes (identical to XNYS 2000-2040 on
    every call made: tools/parity/r19_calendar.py), exposing the subset of the exchange_calendars API r19_data
    calls (date_to_session, is_session, session_open/close, previous/next_session, sessions_in_range);
  * backend/http_transport (an httpx transport the injected getter never reaches) -> a refusing stub.
vendored() also loads backend/r19_cli.py (the worker; only its bounded_snapshot, the per-book decision view, is
called — never its loop, install or funding commands).
The shims are package-scoped (desk.vendor.ausar_r19.providers / .http_transport); vendored bytes are untouched."""
import hashlib
import json
import os
import sys
import types
from datetime import date, datetime, timedelta, timezone

from .. import calendar as dcal

UTC = timezone.utc
PKG = "desk.vendor.ausar_r19"
DATA = "https://data.alpaca.markets"
# XNYS closures that are not rule holidays (exchange_calendars XNYS adhoc_holidays from its 2000 start)
ADHOC_CLOSED = {date(2001, 9, 11), date(2001, 9, 12), date(2001, 9, 13), date(2001, 9, 14), date(2004, 6, 11),
                date(2007, 1, 2), date(2012, 10, 29), date(2012, 10, 30), date(2018, 12, 5), date(2025, 1, 9)}
# exchange_calendars XNYS closes the desk's early-close rule does not derive (tools/parity/r19_calendar.py)
EARLY_EXTRA = {date(2002, 7, 5), date(2003, 12, 26)}      # 13:00 ET special closes
NOT_EARLY = {date(2002, 7, 3)}                            # a full session


def _date(x):
    if isinstance(x, datetime):
        return x.date() if x.tzinfo is None else x.astimezone(dcal.ET).date()
    if isinstance(x, date):
        return x
    return date.fromisoformat(str(x)[:10])


def is_session(d):
    d = _date(d)
    if d in ADHOC_CLOSED:
        return False
    if d.year < 2022 and d.month == 6 and d in dcal.holidays(d.year) and abs(d.day - 19) <= 1:
        return d.weekday() < 5                     # Juneteenth became an NYSE holiday in 2022
    return dcal.is_trading_day(d)


class DeskXNYS:
    """the exchange_calendars XNYS calls r19_data makes, on the desk's NYSE rules."""

    @staticmethod
    def _ts(d):
        import pandas as pd
        return pd.Timestamp(_date(d))

    def is_session(self, x):
        return is_session(x)

    def date_to_session(self, x, direction="none"):
        d = _date(x)
        if is_session(d):
            return self._ts(d)
        if direction not in ("previous", "next"):
            raise ValueError(f"{d} is not a session")
        step = -1 if direction == "previous" else 1
        while not is_session(d):
            d += timedelta(days=step)
        return self._ts(d)

    def session_open(self, x):
        import pandas as pd
        return pd.Timestamp(dcal.session_open(_date(x)), unit="s", tz="UTC")

    def session_close(self, x):
        import pandas as pd
        d = _date(x)
        if d in EARLY_EXTRA or d in NOT_EARLY:
            hm = (13, 0) if d in EARLY_EXTRA else (16, 0)
            return pd.Timestamp(datetime(d.year, d.month, d.day, *hm, tzinfo=dcal.ET).timestamp(), unit="s", tz="UTC")
        return pd.Timestamp(dcal.session_close(d), unit="s", tz="UTC")

    def previous_session(self, x):
        d = _date(x) - timedelta(days=1)
        while not is_session(d):
            d -= timedelta(days=1)
        return self._ts(d)

    def next_session(self, x):
        d = _date(x) + timedelta(days=1)
        while not is_session(d):
            d += timedelta(days=1)
        return self._ts(d)

    def sessions_in_range(self, a, b):
        d, end, out = _date(a), _date(b), []
        while d <= end:
            if is_session(d):
                out.append(self._ts(d))
            d += timedelta(days=1)
        return out


def install_shims():
    """bind the two absent source modules inside the vendored package (idempotent)."""
    prov = PKG + ".providers"
    if prov not in sys.modules:
        m = types.ModuleType(prov)
        m.__doc__ = "desk shim for backend/providers: only _nyse() (XNYS) is read by r19_data"
        m._nyse = DeskXNYS
        sys.modules[prov] = m
    http = PKG + ".http_transport"
    if http not in sys.modules:
        m = types.ModuleType(http)
        m.__doc__ = "desk shim for backend/http_transport: the injected desk getter is the only transport"

        def bounded_http(*a, **k):
            raise RuntimeError("the R19 collector reads through the desk's Alpaca getter only")
        m.bounded_http = bounded_http
        sys.modules[http] = m


def vendored():
    install_shims()
    import importlib
    return {n: importlib.import_module(PKG + "." + n) for n in
            ("r19_core", "r19_data", "r19_tensor", "r19_timing", "r19_intraday_data", "r19_cli")}


_CLOCK = [None]


class _DeskClock(datetime):
    """datetime as the vendored modules see it: now() reads the bound desk clock."""
    @classmethod
    def now(cls, tz=None):
        import time
        t = (_CLOCK[0] or time.time)()
        return datetime.fromtimestamp(t, tz) if tz is not None else datetime.fromtimestamp(t)


def bind_clock(clock):
    """the vendored collector / ledger / worker read the wall clock through datetime.now(UTC): bind them to the
    desk's clock (the wall clock when live; a test or replay clock otherwise). Their bytes are untouched."""
    m = vendored()
    _CLOCK[0] = clock
    for n in ("r19_data", "r19_core", "r19_cli"):
        m[n].datetime = _DeskClock
    return m


def vendored_settlement():
    install_shims()
    import importlib
    return importlib.import_module(PKG + ".settlement_calendar")


def alpaca_getter(client, clock):
    """r19_data's getter contract: (service, path, params) -> (value, receipt), GET only."""
    def get(service, path, params=None):
        if service not in ("paper", "data") or not path.startswith("/") or "?" in path or "://" in path:
            raise RuntimeError("Only explicit allowed GET host/path")
        params = dict(params or {})
        host = DATA if service == "data" else getattr(client, "host", None)
        value = client._get(path, params, host=host)
        if value is None:
            raise RuntimeError(f"Alpaca {service} {path}: HTTP 404")
        body = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
        return value, {"service": service, "path": path, "parameters": params,
                       "received_at": datetime.fromtimestamp(clock(), tz=UTC).isoformat(),
                       "source_sha256": hashlib.sha256(body).hexdigest(), "method": "GET"}
    return get


_COLLECTORS = {}


def collector(directory, client, clock):
    """one source Collector per process and directory (the source's own sqlite market cache, and the Tensor
    engine-prefix cache beside it)."""
    key = (directory, id(client))
    if key not in _COLLECTORS:
        m = vendored()
        os.makedirs(directory, exist_ok=True)
        _COLLECTORS[key] = m["r19_data"].Collector(directory, getter=alpaca_getter(client, clock))
    return _COLLECTORS[key]
