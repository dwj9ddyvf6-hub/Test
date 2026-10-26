"""The recorders that trade (family "monitor"): the owner's ruling D32 (2026-10-26, "Convert where rules exist")
turned each recorder whose source defines complete entry, exit and size rules on bars of 1H or longer into a funded
paper book copying them (the owner, 03:55 UTC: "Anything that's not a trading strategy, or requires 5m bars,
disable"). Their books (desk/sleeves/monitor/printer_books.py, midna_books.py) take the place of the monitors they
were, and each reads the producer its monitor read:

  mon_galath_tensor2washoutreclaimtransition       the Tensor 2 replica's signal on the 1h frame (job mon_galath_tensor,
                                                   desk/sleeves/monitor/galath_tensor_mon.py)
  mon_galath_annaphdlocationoverriddenprintergrid  the gospel PhD replay's printer on daily bars (job mon_galath_phd,
                                                   desk/sleeves/monitor/galath_phd_mon.py)
  mon_midna_weekly_8_20_50_pullback                the weekly 8/20/50 pullback's primary book (daily bars)
  mon_midna_tsmom_forms                            the TSMOM study's ETF 12-1 book (daily bars)

mon_midna_3tf_vwap_pullback stays "disabled" in the manifest: a complete strategy, but on 15-minute bars (its monitor
spec is kept in desk/sleeves/monitor/midna_mon.py; the registry does not load it). Every other recorder — the rows
that only measured or rendered, the partial ones and the minute-chart Tensor rows — was removed from the desk with
its code, producers and tests (the owner, 2026-10-26: "anything that is not an actual trading sleeve/strategy can
just be removed altogether. And any tensor strategy that requires 1m or 5m bars");
docs/research/2026-10-26-recorders/CONVERT.md names each with its source lines. A group's jobs are scheduled only while
one of its rows runs (desk/registry.py serving).

Groups (each module's docstring names its source pins, data, removed gates and named divergences):
  desk/sleeves/monitor/galath_tensor_mon.py   the Galath Tensor watch desk on the 1h frame (executed; job
                                              mon_galath_tensor): the Tensor 2 replica's row
  desk/sleeves/monitor/galath_phd_mon.py      the Galath gospel PhD replay printer (executed; job mon_galath_phd)
  desk/sleeves/monitor/midna_mon.py           midna's VWAP pullback (disabled), weekly pullback and TSMOM forms"""
import importlib

from ... import registry
from ..monitor.base import Monitor

GROUPS = ["desk.sleeves.monitor.galath_tensor_mon", "desk.sleeves.monitor.galath_phd_mon",
          "desk.sleeves.monitor.midna_mon"]


def specs():
    out = []
    for g in GROUPS:
        out += list(importlib.import_module(g).SPECS)
    return out


def _jobs():
    """the groups' jobs, each kept only while one of its group's rows runs."""
    out = {}
    for g in GROUPS:
        mod = importlib.import_module(g)
        for name, spec in registry.serving(getattr(mod, "JOBS", {}), [s.sleeve_id for s in mod.SPECS]).items():
            if name in out:
                raise ValueError("duplicate monitor job %s" % name)
            out[name] = spec
    return out


JOBS = _jobs()


def converted():
    """{sleeve_id: book factory} of the rows that trade (D32); each book takes its monitor's place."""
    from ..monitor import midna_books, printer_books
    return dict(printer_books.BOOKS, **midna_books.BOOKS)


CONVERTED = tuple(converted())


def sleeves():
    books = converted()
    return [books[s.sleeve_id]() if s.sleeve_id in books else Monitor(s) for s in specs()]
