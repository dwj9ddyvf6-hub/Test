#!/usr/bin/env python3
"""AgentShield-style self-configuration scan, native subset (A-7).

Scans the harness's own configuration surface as the attack surface:
local skills, connector docs, and hook/tool scripts. Score comes ONLY
from findings, never from decorations (no points for headers, badges,
or boilerplate). Secrets are never discounted by location; other
findings may carry a location weight. A baseline fingerprint hashes
rule id + normalized evidence (whitespace collapsed, volatile numbers
and line numbers stripped), never the line number, so a pure line
shift does not create a new finding (the source's designed-out defect).

Usage:
  self_config_scan.py selftest
  self_config_scan.py scan <path...> [--baseline FILE] [--write-baseline FILE]
Exit: 0 no unbaselined findings, 1 findings present, 2 infra failure.
"""
import hashlib, json, os, re, sys

RULES = [
    ("hardcoded-secret", 25, re.compile(
        r"(?i)(api[_-]?key|secret|token|password|passwd)\s*[:=]\s*['\"][A-Za-z0-9_\-./+]{16,}['\"]")),
    ("private-key-block", 25, re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("world-writable-chmod", 10, re.compile(r"chmod\s+(?:-R\s+)?777|0o777")),
    ("unsafe-eval-exec", 10, re.compile(r"\b(?:eval|exec)\s*\(\s*(?!['\"])")),
    ("shell-true-on-input", 10, re.compile(r"shell\s*=\s*True")),
]
LOCATION_WEIGHT = {"skills": 1.0, "custom-skills": 1.0, "connectors": 1.0, "tools": 0.8}

def _location(path):
    parts = path.replace("\\", "/").split("/")
    for p in parts:
        if p in LOCATION_WEIGHT:
            return p
    return "other"

def normalize_evidence(text):
    t = re.sub(r"\d+", "N", text.strip())
    t = re.sub(r"\s+", " ", t)
    return t[:160]

def fingerprint(rule_id, evidence):
    return hashlib.sha256(f"{rule_id}|{normalize_evidence(evidence)}".encode()).hexdigest()[:32]

def scan_file(path):
    findings = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f, 1):
            for rule_id, weight, rx in RULES:
                m = rx.search(line)
                if m:
                    secret = rule_id in ("hardcoded-secret", "private-key-block")
                    w = weight if secret else weight * LOCATION_WEIGHT.get(_location(path), 1.0)
                    findings.append({
                        "rule": rule_id, "path": path, "line": i,
                        "weight": w, "secret": secret,
                        "evidence": line.strip()[:160],
                        "fingerprint": fingerprint(rule_id, line),
                    })
    return findings

def scan_paths(paths):
    findings, scanned = [], 0
    for p in paths:
        files = []
        if os.path.isfile(p):
            files = [p]
        elif os.path.isdir(p):
            for root, _dirs, names in os.walk(p):
                files += [os.path.join(root, n) for n in names
                          if n.endswith((".md", ".py", ".sh", ".yaml", ".yml", ".json"))]
        else:
            raise OSError(f"path not found: {p}")
        for fp in files:
            scanned += 1
            findings += scan_file(fp)
    score = max(0.0, 100.0 - sum(f["weight"] for f in findings))
    return {"scanned_files": scanned, "findings": findings, "score": round(score, 1)}

def selftest():
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        bad = os.path.join(td, "bad.py")
        clean = os.path.join(td, "clean.py")
        with open(bad, "w") as f:
            f.write("x = 1\n")
            f.write('api_key = "ABCDEFGHIJKLMNOP1234"\n')
            f.write("os.chmod(p, 0o777)\n")
        with open(clean, "w") as f:
            f.write('greeting = "hello world, this is a long friendly string"\n')
        r = scan_paths([td])
        rules = {f["rule"] for f in r["findings"]}
        assert "hardcoded-secret" in rules and "world-writable-chmod" in rules, r
        assert r["score"] < 100, r
        assert all(f["path"] != clean for f in r["findings"]), "clean file must have no findings"
        fp1 = fingerprint("hardcoded-secret", 'api_key = "ABCDEFGHIJKLMNOP1234"')
        with open(bad) as f:
            lines = f.readlines()
        shifted = "\n\n\n" + "".join(lines)
        st = os.path.join(td, "shifted.py")
        with open(st, "w") as f:
            f.write(shifted)
        fps = {f["fingerprint"] for f in scan_file(st) if f["rule"] == "hardcoded-secret"}
        assert fp1 in fps, "line shift must not change the fingerprint"
        print("SELFTEST PASS self_config_scan: secret + chmod findings scored from findings only, clean file clean, fingerprint invariant under line shift")
    return 0

if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "selftest":
        raise SystemExit(selftest())
    if args and args[0] == "scan":
        rest = args[1:]
        baseline_path = write_baseline = None
        paths = []
        i = 0
        while i < len(rest):
            if rest[i] == "--baseline":
                baseline_path = rest[i + 1]; i += 2
            elif rest[i] == "--write-baseline":
                write_baseline = rest[i + 1]; i += 2
            else:
                paths.append(rest[i]); i += 1
        try:
            result = scan_paths(paths)
        except OSError as e:
            print(f"INFRA_FAILURE: {e}")
            raise SystemExit(2)
        known = set()
        if baseline_path and os.path.isfile(baseline_path):
            known = set(json.load(open(baseline_path)))
        if write_baseline:
            json.dump(sorted({f["fingerprint"] for f in result["findings"]}),
                      open(write_baseline, "w"), indent=1)
        fresh = [f for f in result["findings"] if f["fingerprint"] not in known]
        print(json.dumps({"scanned_files": result["scanned_files"], "score": result["score"],
                          "findings": len(result["findings"]), "unbaselined": len(fresh),
                          "fresh": fresh}, indent=1))
        raise SystemExit(1 if fresh else 0)
    print(__doc__)
    raise SystemExit(2)
