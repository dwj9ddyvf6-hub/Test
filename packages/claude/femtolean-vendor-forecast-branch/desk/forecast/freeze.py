"""Frozen thresholds and weights, pinned by content (as desk/analysis/frozen.py pins the engine spec).

A threshold is learned on discovery data only (learn_rank_rule: the sign of the discovery IC and the decile cuts of the
discovery values), written as canonical JSON (sorted keys, no whitespace) and pinned by its sha256. load() refuses a
file whose bytes differ from the pin, so a forecaster never runs on a moved threshold. The pins of the artifacts that
ship with the package are in PINS; a run's own artifacts go under state/forecast/frozen/<name>.json."""
import hashlib
import json
import os

import numpy as np

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frozen")

# the avoid arm's discovery thresholds (xcheck/avoid/build.py on DEEP 2016-22: the 95th percentile of stretch,
# the 80th percentile of idio among r5 < 0), exactly as its run.log printed them
PINS = {"avoid-deep-1": "23875c150dfe96435f6ab83061b9a608a91aad2be7559fac40f708824499349b"}


class FrozenError(RuntimeError):
    pass


def canonical(payload):
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=float).encode()


def sha256(payload):
    return hashlib.sha256(canonical(payload)).hexdigest()


def freeze(name, payload, root=HERE):
    """write <root>/<name>.json once; -> its sha256. An existing file with other bytes is refused (immutable)"""
    os.makedirs(root, exist_ok=True)
    path = os.path.join(root, name + ".json")
    raw = canonical(payload)
    if os.path.exists(path):
        with open(path, "rb") as f:
            if f.read() != raw:
                raise FrozenError(f"{name} is frozen with other content")
        return hashlib.sha256(raw).hexdigest()
    tmp = path + ".tmp"
    with open(tmp, "wb") as f:
        f.write(raw)
    os.replace(tmp, path)
    return hashlib.sha256(raw).hexdigest()


def load(name, pin=None, root=HERE):
    """the payload when <root>/<name>.json hashes to its pin (PINS[name] by default); FrozenError otherwise"""
    pin = pin or PINS.get(name)
    if not pin:
        raise FrozenError(f"no sha256 pin for {name}")
    path = os.path.join(root, name + ".json")
    try:
        with open(path, "rb") as f:
            raw = f.read()
    except OSError as e:
        raise FrozenError(f"{name} unreadable: {e}")
    got = hashlib.sha256(raw).hexdigest()
    if got != pin:
        raise FrozenError(f"{name} sha256 {got} is not the pinned {pin}")
    return json.loads(raw)


def learn_rank_rule(x_disc, ic_disc):
    """the rule learned on discovery: the sign of the discovery IC and the discovery deciles of x (9 cuts)"""
    x = np.asarray(x_disc, float)
    x = x[np.isfinite(x)]
    cuts = [float(v) for v in np.quantile(x, np.arange(1, 10) / 10)] if len(x) else []
    return {"sign": 1 if ic_disc >= 0 else -1, "deciles": cuts, "n": int(len(x))}
