#!/usr/bin/env python3
"""Content-addressed fragment registry for prompt context (A-14).

Sits on top of fragment_lint.py's pin-or-float references: large reusable
context (research corpora, teardown bundles, chart packs) is stored once,
addressed by its SHA-256, and cited by hash across many runs instead of
being copy-pasted. Objects live under fragment_store/objects/<sha256>;
index.json maps hash -> {names, size, stored_at}. A citation renders in
fragment_lint syntax: {{fragment:<name>@<hashprefix>}}.

Usage:
  fragment_registry.py selftest
  fragment_registry.py put <file> [--name NAME] [--registry DIR]
  fragment_registry.py cite <name> [--registry DIR]
  fragment_registry.py get <hashprefix> [--registry DIR]
  fragment_registry.py list [--registry DIR]
  fragment_registry.py verify [--registry DIR]
"""
import hashlib, json, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_REGISTRY = os.path.join(HERE, "fragment_store")

def _paths(registry):
    return os.path.join(registry, "objects"), os.path.join(registry, "index.json")

def _load_index(registry):
    _objs, idx = _paths(registry)
    if os.path.isfile(idx):
        return json.load(open(idx, encoding="utf-8"))
    return {}

def _save_index(registry, index):
    objs, idx = _paths(registry)
    os.makedirs(objs, exist_ok=True)
    tmp = idx + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=1, sort_keys=True)
    os.replace(tmp, idx)

def put_bytes(data: bytes, name: str, registry=DEFAULT_REGISTRY):
    h = hashlib.sha256(data).hexdigest()
    objs, _idx = _paths(registry)
    os.makedirs(objs, exist_ok=True)
    dest = os.path.join(objs, h)
    if not os.path.isfile(dest):
        tmp = dest + ".tmp"
        with open(tmp, "wb") as f:
            f.write(data)
        os.replace(tmp, dest)
    index = _load_index(registry)
    rec = index.get(h, {"names": [], "size": len(data), "stored_at": time.time()})
    if name not in rec["names"]:
        rec["names"].append(name)
    index[h] = rec
    _save_index(registry, index)
    return h

def put_file(path, name=None, registry=DEFAULT_REGISTRY):
    with open(path, "rb") as f:
        data = f.read()
    return put_bytes(data, name or os.path.basename(path), registry)

def resolve(prefix, registry=DEFAULT_REGISTRY):
    index = _load_index(registry)
    matches = [h for h in index if h.startswith(prefix)]
    if len(matches) != 1:
        raise KeyError(f"hash prefix {prefix!r} matches {len(matches)} objects")
    return matches[0]

def get_bytes(hash_or_prefix, registry=DEFAULT_REGISTRY):
    h = resolve(hash_or_prefix, registry) if len(hash_or_prefix) < 64 else hash_or_prefix
    objs, _idx = _paths(registry)
    with open(os.path.join(objs, h), "rb") as f:
        return f.read()

def cite(name, registry=DEFAULT_REGISTRY):
    index = _load_index(registry)
    for h, rec in index.items():
        if name in rec["names"]:
            return "{{fragment:%s@%s}}" % (name, h[:16])
    raise KeyError(f"no fragment named {name!r}")

def verify(registry=DEFAULT_REGISTRY):
    objs, _idx = _paths(registry)
    bad = []
    for h, rec in _load_index(registry).items():
        p = os.path.join(objs, h)
        if not os.path.isfile(p):
            bad.append((h, "missing object"))
            continue
        actual = hashlib.sha256(open(p, "rb").read()).hexdigest()
        if actual != h:
            bad.append((h, "hash mismatch"))
    return bad

def selftest():
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        reg = os.path.join(td, "reg")
        h1 = put_bytes(b"large reusable context pack", "pack", registry=reg)
        h2 = put_bytes(b"large reusable context pack", "pack-copy", registry=reg)
        assert h1 == h2, "identical content must share one address"
        assert get_bytes(h1[:12], registry=reg) == b"large reusable context pack"
        c = cite("pack", registry=reg)
        assert c.startswith("{{fragment:pack@") and h1[:16] in c, c
        assert verify(registry=reg) == []
        objs, _i = _paths(reg)
        with open(os.path.join(objs, h1), "ab") as f:
            f.write(b"tamper")
        assert verify(registry=reg), "tampered object must fail verify"
        print("SELFTEST PASS fragment_registry: dedup by hash, prefix get, fragment_lint citation, tamper detected by verify")
    return 0

if __name__ == "__main__":
    args = sys.argv[1:]
    reg = DEFAULT_REGISTRY
    if "--registry" in args:
        i = args.index("--registry"); reg = args[i + 1]; del args[i:i + 2]
    if args and args[0] == "selftest":
        raise SystemExit(selftest())
    if args and args[0] == "put":
        name = None
        if "--name" in args:
            i = args.index("--name"); name = args[i + 1]; del args[i:i + 2]
        print(put_file(args[1], name=name, registry=reg))
    elif args and args[0] == "cite":
        print(cite(args[1], registry=reg))
    elif args and args[0] == "get":
        sys.stdout.buffer.write(get_bytes(args[1], registry=reg))
    elif args and args[0] == "list":
        print(json.dumps(_load_index(reg), indent=1, sort_keys=True))
    elif args and args[0] == "verify":
        bad = verify(registry=reg)
        print("OK" if not bad else f"BAD: {bad}")
        raise SystemExit(1 if bad else 0)
    else:
        print(__doc__); raise SystemExit(2)
