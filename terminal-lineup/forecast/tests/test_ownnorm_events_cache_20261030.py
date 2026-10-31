"""Regression blocker for the Own-Norm Depth events checkpoint
cache (cure G17 remainder, 2026-10-30).

Fail direction: on the pre-cure refresh_ownnormdepth.py,
collect_events takes no checkpoint_path and none of the cache
helpers exist, so a killed multi-hour era pass lost every event
it had collected (the 2026-10-30 fit died exactly that way).
These tests pin: a checkpointed pass returns the identical event
sequence as an uninterrupted pass, a second pass reuses stored
symbols without touching the panel again, and a torn final line
is tolerated.
"""
import importlib.util
import os
import sys

SITE = os.path.expanduser("~/workspace/terminal-lineup/site")
sys.path.insert(0, SITE)
sys.path.insert(0, os.path.expanduser("~/workspace/terminal-lineup"))


def _load():
    spec = importlib.util.spec_from_file_location(
        "refresh_ownnormdepth_cache_test",
        os.path.join(SITE, "refresh_ownnormdepth.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _rows(base, days=900):
    rows = []
    price = base
    for i in range(days):
        price *= 1.001 if i % 3 else 0.999
        rows.append([f"20{16 + i // 250}-{(i % 250) // 28 + 1:02d}-"
                     f"{i % 28 + 1:02d}",
                     price * 0.999, price * 1.01, price * 0.99,
                     price, 1000000])
    # strictly increasing unique dates are required by the engine;
    # rebuild them properly from a real calendar
    from datetime import date, timedelta
    out = []
    d = date(2016, 1, 4)
    price = base
    while len(out) < days:
        if d.weekday() < 5:
            price *= 1.001 if len(out) % 3 else 0.999
            out.append([d.isoformat(), price * 0.999, price * 1.01,
                        price * 0.99, price, 1000000])
        d += timedelta(days=1)
    return out


def test_checkpoint_roundtrip_identical_and_reused(tmp_path):
    mod = _load()
    spy = _rows(500.0)
    panel = {"SPY": spy, "AAA": _rows(50.0), "BBB": _rows(80.0)}
    ckpt = str(tmp_path / "fit.jsonl")
    ev1, fear1 = mod.collect_events(
        panel, spy, "2016-01-01", "2022-12-31", set(),
        checkpoint_path=ckpt)
    assert os.path.exists(ckpt)
    # Second pass over a panel that raises if a stored symbol is
    # parsed again: reuse must serve AAA and BBB from the file.
    class Exploding(dict):
        def __getitem__(self, key):
            if key in ("AAA", "BBB"):
                raise AssertionError(f"{key} reparsed despite cache")
            return super().__getitem__(key)
    panel2 = Exploding(panel)
    ev2, fear2 = mod.collect_events(
        panel2, spy, "2016-01-01", "2022-12-31", set(),
        checkpoint_path=ckpt)
    assert ev1 == ev2
    assert fear1 == fear2
    # Uncached pass over the same panel agrees exactly.
    ev3, fear3 = mod.collect_events(
        panel, spy, "2016-01-01", "2022-12-31", set())
    assert ev1 == ev3
    assert fear1 == fear3


def test_torn_final_line_tolerated(tmp_path):
    mod = _load()
    ckpt = str(tmp_path / "fit.jsonl")
    with open(ckpt, "w", encoding="utf-8") as fh:
        fh.write('{"symbol": "AAA", "events": [[50.0, 1.5]], '
                 '"fear_events": []}\n')
        fh.write('{"symbol": "BBB", "events": [[1.0,')  # torn
    done = mod._read_events_checkpoint(ckpt)
    assert done == {"AAA": ([(50.0, 1.5)], [])}
