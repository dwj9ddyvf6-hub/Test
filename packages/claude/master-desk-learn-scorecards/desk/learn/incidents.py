"""What health raised to the owner: state/incidents.json, kept by the record push (desk/jobs.py state_sync).

Each push that lands pings DESK_PING_URL, a dead-man's switch such as a healthchecks.io check. observe() turns each
health check into the push's signal. Every row that is not OK is an incident, fingerprinted by its check name: seen
again, the same incident; `streak` counts the checks in a row it has been seen, `healthy` the checks in a row its row
has been OK or gone, and HEALTHY_CHECKS of those resolve it (the newest KEEP_RESOLVED resolved ones are kept).
<url>/fail, with summary() as the body, is sent while any row is CRIT or any non-baseline incident's row is WARN with a
streak of WARN_CHECKS or more; otherwise the success ping. So another WARN appearing or clearing never resets one's
persistence. The WARN rows of a host's first check (no incidents file yet) are its baseline: the 3 stale job failures
the KS-5-A carried from the old container would otherwise page an hour after the deploy. A baseline incident never
pages at WARN, resolves as usual, and comes back as a new incident that pages; a CRIT always pages."""
import hashlib
import os

from ..util import iso, read_json, write_json_atomic

WARN_CHECKS = 3              # a non-baseline WARN incident seen this many checks in a row pages
HEALTHY_CHECKS = 3           # an incident resolves after this many checks in a row with its row OK or gone
KEEP_RESOLVED = 100
BODY_MAX = 1000              # characters of the /fail body (healthchecks.io keeps up to 100 kB)


def fingerprint(check):
    return hashlib.sha256(str(check).encode()).hexdigest()[:16]


def _names(xs, room):
    s = ", ".join(xs)
    if len(s) <= room:
        return s
    return s[:room].rsplit(", ", 1)[0] + ", ... (%d in all)" % len(xs)


def summary(hl, doc):
    """the /fail body: the level, the paging incidents first, then the other rows that are not OK, the last pass, the
    open incidents; plain text, at most BODY_MAX characters"""
    rows = {c["check"]: c for c in hl.get("checks") or []}
    opened = {i["check"]: i for i in doc.get("open") or []}
    paging = list(doc.get("paging") or [])

    def tag(name):
        i, lv = opened.get(name) or {}, rows[name]["level"]
        if lv == "CRIT":
            return "%s (CRIT)" % name
        if i.get("baseline"):
            return "%s (WARN, baseline)" % name
        n = int(i.get("streak") or 1)
        return "%s (WARN, %d check%s)" % (name, n, "" if n == 1 else "s")
    others = sorted(k for k, c in rows.items() if c["level"] != "OK" and k not in paging)
    out = ["master-desk %s at %s: %d paging" % (hl.get("level"), iso(float(hl.get("at") or 0)), len(paging))]
    if paging:
        out.append("paging: " + _names([tag(k) for k in paging], 450))
    if others:
        out.append("not paging: " + _names([tag(k) for k in others], 250))
    hb = (rows.get("heartbeat") or {}).get("detail") or {}
    if hb.get("age_s") is not None:
        out.append("last pass %.0f s ago (pass %s)" % (float(hb["age_s"]), hb.get("passes")))
    if doc.get("open"):
        base = sum(1 for i in doc["open"] if i.get("baseline"))
        out.append("open incidents: %d (%d baseline), the oldest since %s" % (len(doc["open"]), base,
                                                                             doc["open"][0]["opened_iso"]))
    return "\n".join(out)[:BODY_MAX - 1] + "\n"


def observe(root, hl, now=None):
    """one health check (desk/learn/health.check's report) -> {"fail": the /fail signal, "body": its text or None,
    "paging": the check names it pages for, "open": open incidents}; state/incidents.json updated"""
    now = float(hl.get("at") if now is None else now)
    path = os.path.join(root, "state", "incidents.json")
    first = not os.path.exists(path)             # this host's first check: its WARN rows are the baseline
    doc = read_json(path, {}) or {}
    level = {c["check"]: c["level"] for c in hl.get("checks") or []}
    opened = {i["check"]: i for i in doc.get("open") or []}
    resolved = list(doc.get("resolved") or [])
    for name, lv in sorted(level.items()):
        if lv == "OK":
            continue
        i = opened.get(name)
        if i is None:
            i = opened[name] = {"fingerprint": fingerprint(name), "check": name, "baseline": first and lv == "WARN",
                                "opened": now, "opened_iso": iso(now), "worst": lv}
        i.update(level=lv, last=now, seen=int(i.get("seen") or 0) + 1, streak=int(i.get("streak") or 0) + 1,
                 healthy=0, worst="CRIT" if "CRIT" in (lv, i.get("worst")) else "WARN")
    for name, i in list(opened.items()):
        if level.get(name, "OK") != "OK":
            continue
        i["streak"], i["healthy"] = 0, int(i.get("healthy") or 0) + 1
        if i["healthy"] >= HEALTHY_CHECKS:
            resolved.append(dict(opened.pop(name), resolved=now, resolved_iso=iso(now)))
    crit = sorted(k for k in opened if level.get(k) == "CRIT")
    held = sorted((k for k, i in opened.items() if level.get(k) == "WARN" and not i.get("baseline")
                   and i["streak"] >= WARN_CHECKS), key=lambda k: (-opened[k]["streak"], k))
    paging = crit + held
    doc = {"at": now, "checks": int(doc.get("checks") or 0) + 1, "level": hl.get("level"),
           "signal": "fail" if paging else "success", "paging": paging,
           "open": sorted(opened.values(), key=lambda i: (i["opened"], i["check"])),
           "resolved": resolved[-KEEP_RESOLVED:]}
    write_json_atomic(path, doc)
    return {"fail": bool(paging), "body": summary(hl, doc) if paging else None, "paging": paging,
            "open": len(doc["open"])}
