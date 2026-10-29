"""Publishing an edition: the static page and its data, pushed to the public site as one orphan commit.

The site (cache/terminal/site, a git repository of its own) is rebuilt from web/terminal and the edition on every run:
  - the CSS and JS get content-hashed names, because the Pages CDN ignores query strings; index.html refers to them;
  - the dashboards beside the edition (DASH_FILES from cache/terminal/dash, written by dash.py) and the roster's reads;
  - `.nojekyll` skips Pages' Jekyll build.
Before anything leaves the host, every file is scanned for secrets: token and key shapes, private keys, e-mail
addresses, and the value of every credential-like variable in this process's environment. A hit stops the publish.
The commit has no parent and is force-pushed to the site's main branch, so the public history is always one commit and
only changed blobs travel; local history is pruned. A refusal (no access to the repository) or a network failure is
recorded and retried at the next edition. Nothing here raises into the loop."""
import glob
import hashlib
import json
import logging
import os
import re
import shutil
import subprocess
import time
import urllib.request

REPO = "dwj9ddyvf6-hub/dwj9ddyvf6-hub.github.io"
SITE_URL = "https://dwj9ddyvf6-hub.github.io/"
WEB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "web", "terminal")
PAGE_FILES = ("index.html", "app.css", "app.js", "viz.css", "viz.js", "market.css", "market.js", "engine.css", "engine.js",
              "desk.css", "desk.js", "record.css", "record.js", "context.css", "context.js", "brief.css", "brief.js", "strip.css", "strip.js", "heur.css", "heur.js", "funnel.css", "funnel.js", "vendor.css", "vendor.js", "favicon.svg", "manifest.webmanifest")
# a tab's own files (market, engine, desk) load on its first open, named in index.html's data-css and data-js
HASHED = ("app.css", "app.js", "viz.css", "viz.js", "market.css", "market.js", "engine.css", "engine.js", "desk.css",
          "desk.js", "record.css", "record.js", "context.css", "context.js", "brief.css", "brief.js", "strip.css", "strip.js", "heur.css", "heur.js", "funnel.css", "funnel.js", "vendor.css", "vendor.js")
DASH_FILES = ("market.json", "charts.json", "heur-names.json")      # the dashboards beside the edition (dash.py), fetched lazily
DESK_FILES = ("deskview.json", "sleeves.json", "positions.json")   # the Desk tab's data (desk/terminal/deskview.py)
MORGUE_FILES = ("morgue-board.json", "morgue-map.json")   # the Morgue Engine's sidecars (desk/morgue/edition.py), fetched lazily
IDENT = ["-c", "user.name=Master Desk", "-c", "user.email=dwj9ddyvf6-hub@users.noreply.github.com"]
SECRET_SHAPES = [re.compile(p) for p in (
    r"gh[pousr]_[A-Za-z0-9]{20,}", r"github_pat_[A-Za-z0-9_]{20,}", r"AKIA[0-9A-Z]{16}",
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----", r"xox[abpr]-[A-Za-z0-9-]{10,}", r"\bsk-[A-Za-z0-9]{20,}",
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")]
CREDENTIAL_NAMES = re.compile(r"KEY|SECRET|TOKEN|PASS|PING|AUTH|CRED|COOKIE|SESSION", re.I)
STALE_LOCK_S = 600


def site_dir(root):
    return os.path.join(root, "cache", "terminal", "site")


def reads_dir(root):
    return os.path.join(root, "cache", "terminal", "reads")


def dash_dir(root):
    return os.path.join(root, "cache", "terminal", "dash")


def desk_dir(root):
    return os.path.join(root, "cache", "terminal", "desk")


def morgue_dir(root):
    return os.path.join(root, "cache", "terminal", "morgue")


def build_site(site, edition, web=WEB, extra=None, dash=None, engine=None, desk=None, morgue=None):
    """write the page (hashed asset names), the edition, the roster's reads (reads-*.json from `extra`, a directory),
    the dashboards (DASH_FILES from `dash`, a directory), the analysis engine's screen (engine.json from `engine`, a
    file the edition job validated: engine.save), the Desk tab's data (DESK_FILES from `desk`, a directory) and the Morgue
    Engine's sidecars (MORGUE_FILES from `morgue`, a directory) into site/ (its .git kept) -> the published file names"""
    os.makedirs(site, exist_ok=True)
    for name in os.listdir(site):
        if name != ".git":
            p = os.path.join(site, name)
            shutil.rmtree(p) if os.path.isdir(p) and not os.path.islink(p) else os.remove(p)
    renamed = {}
    for name in PAGE_FILES:
        src = os.path.join(web, name)
        data = open(src, "rb").read()
        out = name
        if name in HASHED:
            stem, ext = os.path.splitext(name)
            out = f"{stem}.{hashlib.sha256(data).hexdigest()[:10]}{ext}"
            renamed[name] = out
        if name == "index.html":
            continue
        with open(os.path.join(site, out), "wb") as f:
            f.write(data)
    html = open(os.path.join(web, "index.html"), encoding="utf-8").read()
    for a, b in renamed.items():
        html = re.sub(r'(["\'/])' + re.escape(a) + r'(["\'?#])', lambda m: m.group(1) + b + m.group(2), html)
    with open(os.path.join(site, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    with open(os.path.join(site, "edition.json"), "w", encoding="utf-8") as f:
        json.dump(edition, f, ensure_ascii=False, separators=(",", ":"))
    if extra and os.path.isdir(extra):
        for name in sorted(os.listdir(extra)):
            if re.fullmatch(r"reads-[A-Z0-9]+\.json|reads-index\.json", name):
                shutil.copyfile(os.path.join(extra, name), os.path.join(site, name))
    if dash and os.path.isdir(dash):
        for name in DASH_FILES:
            if os.path.isfile(os.path.join(dash, name)):
                shutil.copyfile(os.path.join(dash, name), os.path.join(site, name))
    if engine and os.path.isfile(engine):
        shutil.copyfile(engine, os.path.join(site, "engine.json"))
    if desk and os.path.isdir(desk):
        for name in DESK_FILES:
            if os.path.isfile(os.path.join(desk, name)):
                shutil.copyfile(os.path.join(desk, name), os.path.join(site, name))
    if morgue and os.path.isdir(morgue):
        for name in MORGUE_FILES:
            if os.path.isfile(os.path.join(morgue, name)):
                shutil.copyfile(os.path.join(morgue, name), os.path.join(site, name))
    open(os.path.join(site, ".nojekyll"), "w").close()
    return sorted(n for n in os.listdir(site) if n != ".git")


SIZE_WARN = 2 * 1024 * 1024          # a data file over this is logged: the page loads edition.json and its sidecars whole
log = logging.getLogger(__name__)


def warn_oversize(site, limit=SIZE_WARN):
    """log a warning for each .json file (edition.json and the sidecars) over `limit` bytes -> their names"""
    big = []
    for name in sorted(os.listdir(site)):
        p = os.path.join(site, name)
        if name.endswith(".json") and os.path.isfile(p) and os.path.getsize(p) > limit:
            big.append(name)
            log.warning("published data file %s is %.1f MB, over the %.0f MB watch line", name,
                        os.path.getsize(p) / 1048576, limit / 1048576)
    return big


def scan(site, env=None):
    """[(file, what)] for every secret-like string in the site's files"""
    env = os.environ if env is None else env
    values = [(k, v) for k, v in env.items() if CREDENTIAL_NAMES.search(k) and v and len(v) >= 12]
    hits = []
    for name in sorted(os.listdir(site)):
        p = os.path.join(site, name)
        if name == ".git" or not os.path.isfile(p):
            continue
        text = open(p, "rb").read().decode("utf-8", "replace")
        for pat in SECRET_SHAPES:
            if pat.search(text):
                hits.append((name, "pattern " + pat.pattern[:24]))
        for k, v in values:
            if v in text:
                hits.append((name, "the value of $" + k))
    return hits


def _git(site, args, timeout=120):
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    return subprocess.run(["git"] + IDENT + args, cwd=site, capture_output=True, text=True, timeout=timeout, env=env)


def _classify(err):
    e = (err or "").lower()
    if any(s in e for s in ("403", "permission", "not found", "authentication", "could not read username",
                            "denied", "terminal prompts disabled")):
        return "no_access"
    if any(s in e for s in ("could not resolve", "timed out", "connection", "network", "unable to access",
                            "tls", "ssl")):
        return "network"
    return "error"


def _clear_stale_locks(site, now):
    for p in glob.glob(os.path.join(site, ".git", "*.lock")) + glob.glob(os.path.join(site, ".git", "refs", "**",
                                                                                         "*.lock"), recursive=True):
        try:
            if now - os.path.getmtime(p) > STALE_LOCK_S:
                os.remove(p)
        except OSError:
            pass


def push(site, message, repo=REPO, now=None, url=None):
    """one orphan commit of the site, force-pushed to main -> {"status", "commit", "error"}"""
    now = time.time() if now is None else now
    url = url or f"https://github.com/{repo}.git"
    try:
        if not os.path.isdir(os.path.join(site, ".git")):
            r = _git(site, ["init", "-q"])
            if r.returncode:
                return {"status": "error", "error": "git init: " + r.stderr.strip()[:200]}
        _clear_stale_locks(site, now)
        remotes = _git(site, ["remote"]).stdout.split()
        _git(site, ["remote", "set-url" if "origin" in remotes else "add", "origin", url])
        for args in (["add", "-A"], ["write-tree"]):
            r = _git(site, args)
            if r.returncode:
                return {"status": "error", "error": f"git {args[0]}: " + r.stderr.strip()[:200]}
        tree = r.stdout.strip()
        r = _git(site, ["commit-tree", tree, "-m", message])
        if r.returncode:
            return {"status": "error", "error": "git commit-tree: " + r.stderr.strip()[:200]}
        commit = r.stdout.strip()
        r = _git(site, ["push", "--force", "--quiet", "origin", f"{commit}:refs/heads/main"], timeout=180)
        if r.returncode:
            err = (r.stderr or r.stdout).strip().replace(url, "<site repo>")[:300]
            return {"status": _classify(err), "commit": commit, "error": err}
        _git(site, ["update-ref", "refs/heads/main", commit])
        _git(site, ["symbolic-ref", "HEAD", "refs/heads/main"])
        _git(site, ["reflog", "expire", "--expire=now", "--all"])
        _git(site, ["gc", "--prune=now", "--quiet"], timeout=120)
        return {"status": "published", "commit": commit}
    except (OSError, subprocess.SubprocessError) as e:
        return {"status": "error", "error": f"{type(e).__name__}: {str(e)[:200]}"}


def live_seq(url=SITE_URL + "edition.json", timeout=10):
    """the seq the public site serves now (None when it cannot be read)"""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "master-desk-terminal/1", "Cache-Control": "no-cache"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read(200_000)).get("seq")
    except Exception:
        return None


def publish(root, edition, web=WEB, repo=REPO, env=None, now=None, url=None):
    """build the site, scan it, push it -> {"status", ...}; blocked on any scan hit"""
    from .engine import path as engine_path
    site = site_dir(root)
    try:
        files = build_site(site, edition, web, reads_dir(root), dash=dash_dir(root), engine=engine_path(root),
                           desk=desk_dir(root), morgue=morgue_dir(root))
    except OSError as e:
        return {"status": "error", "error": f"build: {type(e).__name__}: {str(e)[:200]}"}
    warn_oversize(site)
    hits = scan(site, env)
    if hits:
        return {"status": "blocked", "error": "secret scan: " + "; ".join(f"{f}: {w}" for f, w in hits)[:300],
                "files": files}
    out = push(site, f"Edition {edition.get('edition')} (seq {edition.get('seq')})", repo, now, url)
    out["files"] = files
    return out
