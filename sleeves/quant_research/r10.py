"""Shared plumbing for the quant_research R10 rows (quant-research-backup@d170596b research-archives/
2026-10-09-ten-strategy-repair-review-r10): the funded core account several playbooks hold (index donors displaced
by episode stock positions and restored at the episode's exit), episode bookkeeping, the registry files that feed
caller-supplied kernel inputs, and the support counts the playbooks' admission gates read."""
import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from ... import calendar as cal
from . import common as C

ET = ZoneInfo("America/New_York")
REPO, COMMIT = "quant-research-backup", "d170596b4d3f24712da933683ceb6d9ee95d6937"
R10 = "research-archives/2026-10-09-ten-strategy-repair-review-r10/strategies/"


def source(lane, path, blob_sha, line_end=None, playbook=True):
    out = {"repo": REPO, "ref": "main", "commit": COMMIT, "path": R10 + lane + "/" + path, "blob_sha": blob_sha}
    if line_end:
        out.update(line_start=1, line_end=line_end)
    if playbook:
        out["playbook"] = R10 + lane + "/PRACTICAL_PLAYBOOK.md"
    return out


def hm(now):
    return datetime.fromtimestamp(float(now), tz=ET).strftime("%H:%M")


def read_registry(root, name):
    """a lane's registry document in <root>/cache/<name> ({} when absent)."""
    if not root:
        return {}
    try:
        return json.load(open(os.path.join(root, "cache", name)))
    except (OSError, ValueError):
        return {}


def sessions_since(a, b):
    """completed sessions after `a` through `b` (0 when b <= a)."""
    if not a or b <= a:
        return 0
    return len(C.sessions_between(a, b)) - 1


def support(history, keys=("episodes",)):
    """support counts over matured episode records [{issuer, group, exit_session, ...}]."""
    done = [h for h in history or [] if h.get("label") is not None]
    months = {str(h.get("exit_session", ""))[:7] for h in done if h.get("exit_session")}
    return {"episodes": len(done), "issuers": len({h.get("issuer") for h in done}),
            "groups": len({h.get("group") for h in done}), "months": len(months)}


class CoreBook:
    """the funded core: index shares bought once at the stated weights, displaced by each admitted episode
    (donor sale) and restored at its exit (donor restoration); episodes hold their own stock shares."""

    def __init__(self, st, weights):
        self.st, self.weights = st, weights
        st.setdefault("core", {})
        st.setdefault("episodes", {})

    def seed(self, view):
        """the core's initial shares at the live quotes (None until every core quote is in)."""
        if self.st["core"]:
            return True
        tgt = C.target_shares(view, self.weights)
        if tgt is None:
            return False
        self.st["core"] = {s: float(q) for s, q in tgt.items()}
        return True

    def displace(self, view, donor_weights):
        """sell donor index shares worth donor_weights x NAV; returns the shares taken (restored at exit)."""
        nav = C.nav(view)
        taken = {}
        for s, w in donor_weights.items():
            px = ((view.quotes or {}).get(s) or {}).get("bid")
            if not px:
                return None
            q = min(self.st["core"].get(s, 0.0), w * nav / float(px))
            taken[s] = q
        for s, q in taken.items():
            self.st["core"][s] = self.st["core"].get(s, 0.0) - q
        return taken

    def restore(self, taken):
        for s, q in (taken or {}).items():
            self.st["core"][s] = self.st["core"].get(s, 0.0) + float(q)

    def targets(self):
        out = {s: max(0.0, float(q)) for s, q in self.st["core"].items()}
        for ep in self.st["episodes"].values():
            if ep.get("status") in ("entering", "open"):
                out[ep["symbol"]] = out.get(ep["symbol"], 0.0) + float(ep["qty"])
        return out

    def rebalance(self, view, key, reason):
        out, _ = C.rebalance(view, self.targets(), key, reason)
        return out


def in_session(now, day):
    return cal.is_rth(now) and C.is_session(day)
