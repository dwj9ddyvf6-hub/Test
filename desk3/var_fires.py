"""Variation fire-stream cloning (GOING-LIVE-VARIATIONS-20261115).

Fire-consumer engines (desk3/lazarus.py, desk3/lazarus_midna.py)
route fires by the fire's sleeve_id field: a fire addressed to a
parent sleeve is skipped by every other sleeve id. A variation
sleeve beside its parent (GUTTING AS VARIATION: the parent is never
edited into the variation) therefore cannot see its parent's fire
stream under its own id.

This helper builds the variation's view: a shallow copy of the
snapshot in which every fire addressed to the parent id, in every
container those engines read, is re-addressed to the variation id
(fire dicts are copied, never mutated in place, so the parent's own
evaluation of the same snapshot is unaffected). Bars, positions and
every other view key are shared by reference, exactly as the parent
sees them. Only the variation adapters call this; no existing
sleeve's view is ever rewritten.
"""
from __future__ import annotations

_FIRE_KEYS = ("lazarus_fires", "tensor_fires", "midna_fires", "fires")


def _clone_list(fires, parent_id, var_id):
    out = []
    for f in fires:
        if isinstance(f, dict) and f.get("sleeve_id") == parent_id:
            g = dict(f)
            g["sleeve_id"] = var_id
            out.append(g)
        else:
            out.append(f)
    return out


def _clone_tensor(t, parent_id, var_id):
    if isinstance(t, list):
        return _clone_list(t, parent_id, var_id)
    if isinstance(t, dict):
        t = dict(t)
        for k in ("fires", "midna_fires"):
            if isinstance(t.get(k), list):
                t[k] = _clone_list(t[k], parent_id, var_id)
        sv = t.get("sleeves")
        if isinstance(sv, dict):
            sv = dict(sv)
            for sid, v in list(sv.items()):
                if sid != parent_id:
                    continue
                if isinstance(v, list):
                    sv[var_id] = _clone_list(v, parent_id, var_id)
                elif isinstance(v, dict) and isinstance(v.get("fires"), list):
                    nv = dict(v)
                    nv["fires"] = _clone_list(v["fires"], parent_id, var_id)
                    sv[var_id] = nv
            t["sleeves"] = sv
        return t
    return t


def clone_view_for_parent(view, parent_id, var_id):
    """Return a shallow copy of view with the parent's fires
    re-addressed to var_id in every container the fire-consumer
    engines read. The input view is not mutated."""
    v = dict(view or {})
    for k in _FIRE_KEYS:
        if isinstance(v.get(k), list):
            v[k] = _clone_list(v[k], parent_id, var_id)
    for k in ("tensor", "tensor_bundle"):
        if k in v:
            v[k] = _clone_tensor(v[k], parent_id, var_id)
    ex = v.get("extra")
    if isinstance(ex, dict):
        ex = dict(ex)
        for k in _FIRE_KEYS:
            if isinstance(ex.get(k), list):
                ex[k] = _clone_list(ex[k], parent_id, var_id)
        for k in ("tensor", "tensor_bundle"):
            if k in ex:
                ex[k] = _clone_tensor(ex[k], parent_id, var_id)
        v["extra"] = ex
    return v
