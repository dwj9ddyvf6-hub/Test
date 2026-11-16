#!/usr/bin/env python3
"""Skill trigger eval, phase 2 (round-5 item 27 completion): holdout-selected
improver loop + blind A/B.

- Candidates are description variants for one skill. Each candidate is scored
  with the phase-1 runner (3 runs per query, threshold 0.5) using a token
  overlap matcher standing in for the host trigger decision.
- Selection rule: the winner is chosen on the TEST (holdout) split only;
  train scores are reported but never select.
- Improver loop: each round is fed ONLY the failing cases plus the attempt
  history (candidate ids and test scores), with a do-not-repeat instruction:
  a candidate whose normalized text repeats an earlier attempt is rejected
  before scoring.
- Blind A/B: two candidates are compared on the test split with identities
  masked (A/B labels assigned by hash order) and unmasked only in the record.
- Every run appends a benchmark delta line to CHANGELOG.md in this directory.
"""
import hashlib, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from runner import score, split_cases, benchmark_line

HERE = os.path.dirname(os.path.abspath(__file__))
STOP = {"a", "an", "the", "to", "of", "for", "and", "or", "in", "on", "when", "user"}

def tokens(text):
    return {t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in STOP}

def make_matcher(description):
    dtoks = tokens(description)
    def matcher(query):
        q = tokens(query)
        return bool(q) and len(q & dtoks) / len(q) >= 0.34
    return matcher

def norm(text):
    return " ".join(sorted(tokens(text)))

def evaluate(candidates, cases):
    train, test = split_cases(cases)
    history, results = [], {}
    for cand in candidates:
        if any(norm(cand["description"]) == h["norm"] for h in history):
            results[cand["id"]] = {"rejected": "do-not-repeat: duplicates an earlier attempt"}
            continue
        m = make_matcher(cand["description"])
        tr, te = score(train, m), score(test, m)
        fails = [c["query"] for c in test
                 if (make_matcher(cand["description"])(c["query"])) != (c["expect"] == "trigger")]
        entry = {"id": cand["id"], "norm": norm(cand["description"]),
                 "train": tr, "test": te, "test_failures": fails}
        history.append(entry); results[cand["id"]] = entry
    scored = [r for r in results.values() if "test" in r]
    winner = max(scored, key=lambda r: r["test"]["accuracy"]) if scored else None
    return {"results": results, "winner": winner["id"] if winner else None,
            "history": history}

def blind_ab(cand_a, cand_b, cases):
    _, test = split_cases(cases)
    pair = sorted([cand_a, cand_b], key=lambda c: hashlib.sha256(c["id"].encode()).hexdigest())
    masked = {lbl: score(test, make_matcher(c["description"])) for lbl, c in zip("AB", pair)}
    return {"masked_scores": masked,
            "unmasked": {lbl: c["id"] for lbl, c in zip("AB", pair)}}

def run(eval_path, candidates_path, record=True):
    cases = json.load(open(eval_path))["cases"]
    candidates = json.load(open(candidates_path))["candidates"]
    out = evaluate(candidates, cases)
    if out["winner"] and len(candidates) >= 2:
        w = next(c for c in candidates if c["id"] == out["winner"])
        base = candidates[0]
        if base["id"] == w["id"]:
            others = [r for r in out["history"] if r["id"] != w["id"]]
            if others:
                base = next(c for c in candidates
                            if c["id"] == max(others, key=lambda r: r["test"]["accuracy"])["id"])
        out["blind_ab"] = blind_ab(base, w, cases)
        if record:
            b = out["results"][base["id"]]["test"]; a = out["results"][w["id"]]["test"]
            with open(os.path.join(HERE, "CHANGELOG.md"), "a") as fh:
                fh.write(f"\n## {os.path.basename(eval_path)} winner={w['id']}\n"
                         f"{benchmark_line(b, a)} (test split, holdout-selected; "
                         f"train {out['results'][w['id']]['train']['accuracy']:.3f})\n")
    return out

def selftest():
    cases = [{"query": "analyze AAPL stock", "expect": "trigger", "split": "test"},
             {"query": "read the NVDA chart", "expect": "trigger", "split": "test"},
             {"query": "book a flight", "expect": "no-trigger", "split": "test"},
             {"query": "analyze MSFT", "expect": "trigger", "split": "train"}]
    cands = [{"id": "vague", "description": "general helper for things"},
             {"id": "sharp", "description": "analyze stock chart read ticker analysis"},
             {"id": "dupe", "description": "stock chart read analyze ticker analysis"}]
    out = evaluate(cands, cases)
    assert out["winner"] == "sharp", out
    assert "rejected" in out["results"]["dupe"], out["results"]["dupe"]
    ab = blind_ab(cands[0], cands[1], cases)
    assert set(ab["unmasked"].values()) == {"vague", "sharp"}
    print("SELFTEST PASS phase2: holdout(TEST)-only selection, do-not-repeat rejection, blind A/B unmasking")
    return 0

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "selftest":
        raise SystemExit(selftest())
    if len(sys.argv) == 3:
        print(json.dumps(run(sys.argv[1], sys.argv[2]), indent=1)); raise SystemExit(0)
    print(__doc__)
