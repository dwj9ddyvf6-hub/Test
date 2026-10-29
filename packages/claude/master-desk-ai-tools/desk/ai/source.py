"""Where the desk AI's tools read from: the host's own files first (the edition the terminal job wrote, the Look up
shards, the books), then, only if allowed, the public site's copy of the same allow-listed edition. Every answer names
which one it used. Read-only: nothing here writes desk state.
"""
import json
import os
import urllib.request

SITE = os.environ.get("DESK_AI_SITE", "https://dwj9ddyvf6-hub.github.io/")


def _root():
    return os.environ.get("DESK_ROOT") or os.getcwd()


def ai_dir(root=None):
    return os.environ.get("DESK_AI_DIR") or os.path.join(root or _root(), "state", "ai")


class Source:
    def __init__(self, root=None, offline=None, edition=None, site=SITE):
        self.root = root or _root()
        self.offline = (os.environ.get("DESK_AI_OFFLINE") == "1") if offline is None else offline
        self.site = site
        self._ed = edition            # an injected edition (frozen replay, tests)
        self._cache = {}

    def _local(self, *parts):
        p = os.path.join(self.root, *parts)
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                return json.load(f), "host:" + "/".join(parts)
        return None, None

    def _remote(self, name):
        if self.offline:
            return None, None
        if name in self._cache:
            return self._cache[name], "site:" + name
        try:
            with urllib.request.urlopen(self.site + name, timeout=20) as r:
                doc = json.loads(r.read().decode("utf-8"))
        except (OSError, ValueError):
            return None, None
        self._cache[name] = doc
        return doc, "site:" + name

    def edition(self):
        """(edition, where, error)"""
        if self._ed is not None:
            return self._ed, "frozen:edition", None
        doc, where = self._local("state", "terminal", "edition.json")
        if doc is None:
            doc, where = self._remote("edition.json")
        if doc is None:
            return None, None, "no local edition and the site was not reachable" + (" (offline)" if self.offline else "")
        self._ed = doc
        return doc, where, None

    def read(self, sym):
        """a roster name's latest read (the Look up shard), or (None, None)"""
        from desk.terminal.reads import shard
        name = f"reads-{shard(sym)}.json"
        doc, where = self._local("cache", "terminal", "reads", name)
        if doc is None:
            doc, where = self._remote(name)
        if not doc or sym not in doc:
            return None, None
        return doc[sym], where

    def books(self):
        """the desk's books (host only, never fetched from anywhere else)"""
        return self._local("state", "books.json")
