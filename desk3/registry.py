"""Producer registry contract (V3-SCOPE §7.3). Every sleeve declares its
inputs; the warm registers what it produced; at cycle start each sleeve's
fed state is computed. An unproduced or stale declared input => UNFED:
excluded from dispatch and surfaced, never a silent abstention."""
from __future__ import annotations


class Registry:
    def __init__(self):
        self.producers = {}   # name -> {outputs, freshness_sla_s}
        self.sleeves = {}     # sleeve_id -> {inputs}
        self._key_owner = {}  # output key -> producer name
        self._produced = {}   # output key -> ts

    def register_producer(self, name, outputs, freshness_sla_s):
        self.producers[name] = {"outputs": tuple(outputs),
                                 "freshness_sla_s": float(freshness_sla_s)}
        for key in outputs:
            self._key_owner[key] = name

    def register_sleeve(self, sleeve_id, inputs):
        self.sleeves[sleeve_id] = {"inputs": tuple(inputs)}

    def mark_produced(self, producer_name, ts):
        spec = self.producers[producer_name]
        for key in spec["outputs"]:
            self._produced[key] = float(ts)

    def mark_produced_keys(self, producer_name, keys, ts):
        """CURE3-1: mark ONLY the output keys the producer actually
        returned this cycle. A producer that fails (returns {}) must
        not mark its keys produced — that was the empty-bars FED bug."""
        spec = self.producers[producer_name]
        for key in spec["outputs"]:
            if key in keys:
                self._produced[key] = float(ts)

    def fed_states(self, now):
        states = {}
        for sid, spec in self.sleeves.items():
            missing, stale = [], []
            for key in spec["inputs"]:
                if key not in self._produced:
                    missing.append(key)
                    continue
                owner = self._key_owner.get(key)
                sla = (self.producers[owner]["freshness_sla_s"]
                       if owner else float("inf"))
                if now - self._produced[key] > sla:
                    stale.append(key)
            bad = missing + stale
            states[sid] = {"state": "UNFED" if bad else "FED",
                           "missing": missing, "stale": stale}
        return states
