"""Universe loading — the one piece of femto-lean core/bars_universe.py
the Tensor producer needs in v2 (WIRING-SOURCE-MAP §2).

`load_universes` is ported verbatim from femto-lean master @15f3368
(core/bars_universe.py); the rest of that 2,115-line module serves
producers v2 does not port here. Tensor's trading universe is
`basket_41` from config/universes.json (Decision #38).
"""
import json
import pathlib

_ROOT = pathlib.Path(__file__).resolve().parent.parent


def load_universes(path=None):
    p = pathlib.Path(path) if path else _ROOT / "config" / "universes.json"
    data = json.loads(p.read_text())
    return {k: list(v) for k, v in data.items() if isinstance(v, list)}
