"""ENH2 (Edge pass batch 16) adapter helpers.

Decision-changing post-filters for the free_opt family adapters.
Vendor/strategy files stay byte-identical (fidelity pins); the
change point is the v3 adapter, where the emitted intent dicts and
the raw served extra are both visible. Each filter is switched by
extra["<sleeve>_enh2"]["enabled"] (default ON; OFF restores the
pre-change rule exactly — the filter is skipped entirely). The
pre-change rule is the shadow control: paired records are appended
to extra["enh2_paired"] for every entry the filter judges; the
control itself never emits.
"""
import re
from datetime import date

_OCC = re.compile(r"^[A-Z]{1,6}(\d{6})([CP])\d{8}$")


def enh2_on(extra, sleeve):
    ov = (extra or {}).get(sleeve + "_enh2")
    if isinstance(ov, dict) and "enabled" in ov:
        return bool(ov["enabled"])
    if isinstance(ov, bool):
        return ov
    return True


def occ_expiry(symbol):
    m = _OCC.match(str(symbol or ""))
    if not m:
        return None
    d = m.group(1)
    return "20%s-%s-%s" % (d[:2], d[2:4], d[4:6])


def occ_right(symbol):
    m = _OCC.match(str(symbol or ""))
    return m.group(2) if m else None


def _paired(extra, record):
    try:
        (extra or {}).setdefault("enh2_paired", []).append(record)
    except Exception:
        pass


def filter_package_expiry_coherence(intents, extra, sleeve):
    """Refuse entry packages whose legs expire on different dates
    (or carry an unparseable expiry). Exits are never filtered."""
    if not enh2_on(extra, sleeve):
        return intents
    entries = [i for i in intents if i.get("kind") == "entry"]
    if len(entries) < 2:
        return intents
    expiries = [occ_expiry(i.get("symbol")) for i in entries]
    bad = any(e is None for e in expiries) or len(set(expiries)) > 1
    _paired(extra, {"sleeve": sleeve, "gate": "leg_expiry_coherence",
                    "expiries": expiries, "control": "enter",
                    "treatment": "refuse_mismatched_expiry" if bad else "enter",
                    "switch_on": True})
    if bad:
        return [i for i in intents if i.get("kind") != "entry"]
    return intents


def filter_min_days_to_expiry(intents, extra, sleeve, session_iso,
                                min_days):
    """Refuse entries whose OCC expiry is < min_days after the
    session date (or unparseable). Exits are never filtered."""
    if not enh2_on(extra, sleeve):
        return intents
    try:
        sess = date.fromisoformat(str(session_iso)[:10])
    except (TypeError, ValueError):
        return intents
    out, dropped = [], False
    for i in intents:
        if i.get("kind") == "entry":
            exp = occ_expiry(i.get("symbol"))
            days = None
            if exp:
                try:
                    days = (date.fromisoformat(exp) - sess).days
                except ValueError:
                    days = None
            bad = days is None or days < min_days
            _paired(extra, {"sleeve": sleeve, "gate": "min_days_to_expiry",
                            "symbol": i.get("symbol"), "expiry": exp,
                            "days": days, "control": "enter",
                            "treatment": "refuse_short_life" if bad else "enter",
                            "switch_on": True})
            if bad:
                dropped = True
                continue
        out.append(i)
    return out


def filter_wheel_zero_life_put(intents, extra, sleeve, session_iso):
    """Refuse sell_to_open put entries expiring on/before the
    session date. Covered-call entries and exits are untouched."""
    if not enh2_on(extra, sleeve):
        return intents
    sess = str(session_iso)[:10]
    out = []
    for i in intents:
        if i.get("kind") == "entry" \
                and i.get("position_intent") == "sell_to_open" \
                and occ_right(i.get("symbol")) == "P":
            exp = occ_expiry(i.get("symbol"))
            bad = exp is None or exp <= sess
            _paired(extra, {"sleeve": sleeve, "gate": "zero_life_put",
                            "symbol": i.get("symbol"), "expiry": exp,
                            "control": "enter",
                            "treatment": "refuse_zero_life" if bad else "enter",
                            "switch_on": True})
            if bad:
                continue
        out.append(i)
    return out


def filter_parity_max_dte(intents, extra, sleeve, session_iso, max_dte=60):
    """Refuse parity box entries whose expiry is > max_dte days out:
    the box edge is locked only at expiry, so a long-dated box locks
    the slice capital for the same per-share edge. Legs are grouped
    by package_id; exits are never filtered."""
    if not enh2_on(extra, sleeve):
        return intents
    try:
        sess = date.fromisoformat(str(session_iso)[:10])
    except (TypeError, ValueError):
        return intents
    bad_pkgs = set()
    for i in intents:
        if i.get("kind") != "entry":
            continue
        pkg = i.get("package_id") or ""
        exp = None
        parts = pkg.split("-")
        # package_id: spy-box-<expiry>-<k1>-<k2>-<direction>
        if len(parts) >= 5:
            exp = "-".join(parts[2:5])
        if exp is None:
            exp = occ_expiry(i.get("symbol"))
        days = None
        if exp:
            try:
                days = (date.fromisoformat(exp) - sess).days
            except ValueError:
                days = None
        bad = days is not None and days > max_dte
        _paired(extra, {"sleeve": sleeve, "gate": "max_dte",
                        "package_id": pkg, "expiry": exp, "dte": days,
                        "control": "enter",
                        "treatment": "refuse_long_dated" if bad else "enter",
                        "switch_on": True})
        if bad:
            bad_pkgs.add(pkg)
    if not bad_pkgs:
        return intents
    return [i for i in intents
            if not (i.get("kind") == "entry"
                    and (i.get("package_id") or "") in bad_pkgs)]
