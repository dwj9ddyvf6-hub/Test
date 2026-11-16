#!/usr/bin/env python3
"""Typed supersession, derived-fact review, forgetting contracts, and the
corpus junk audit for the tooling memory store. Disciplines 4, 5, and 17
(its first user), built 2026-11-03.

Facts are store notes whose frontmatter carries an `id`. The edge layer:

  edge        updates | extends | derives, recorded on the newer fact
              against `supersedes: <id>` by apply_edge, never left to
              author habit. updates retires the target; derives marks the
              new fact inferred with review pending.
  bi-temporal valid_from / valid_until / learned_on are separate fields:
              when a fact stopped being true and when memory learned it
              are different facts.
  review      derived (inferred) facts wait in review_queue, ranked by
              support count; approve clears the flag, decline forgets
              the fact (decline-as-forget, discipline 4).
  corrections are two-phase (discipline 5): propose_correction writes a
              status=proposed successor and the predecessor stays current
              until apply_correction; memory_search_local excludes
              proposed and superseded notes from recall.
  forgetting  forget_by_id returns a per-ID result (a success response
              does not prove every ID changed), cleans derived copies
              (the search index, when its path is given), and writes an
              erasure receipt plus a projection tombstone. Semantic
              forget is dry-run first and the delete is bound to the
              previewed IDs.
  audit       audit_corpus classifies every note clean / duplicate /
              feedback-loop / malformed and reports the junk rate; junk
              skeletons are recorded in the near-miss ledger (discipline
              17's named first user) when a ledger path is given. The
              ledger stays diagnostics-only; the audit never deletes.

Multi-file transactions stage in a temp copy of the store, run
memory_store_check on the staged copy, and commit only on a clean check:
memory_write.write_note stays the single-note write path; this module is
the transaction path for changes that are only valid together (an edge
and the retirement it causes). Platform MEMORY.md is runtime-managed and
outside this store, as with every tool here.

CLI: memory_edges.py summary [store] | selftest
"""
import hashlib, json, os, re, shutil, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import memory_store_check
from dedup_ids import deterministic_id
from near_misses import NearMissLedger

EDGES = ("updates", "extends", "derives")
TOK = re.compile(r"[a-z0-9]+")
NEAR_DUP_JACCARD = 0.8  # the audit's stated near-duplicate bar (token Jaccard)

def _fm_parse(text):
    fm, order = {}, []
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            for line in text[3:end].splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    fm[k.strip().lower()] = v.strip()
                    order.append(k.strip().lower())
    return fm, order

def _render(fm, order, body):
    keys = [k for k in order if k in fm] + [k for k in fm if k not in order]
    lines = "\n".join(f"{k}: {fm[k]}" for k in keys)
    return f"---\n{lines}\n---\n{body}"

def _body_of(text):
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            return text[end + 4:]
    return text

def load_facts(store):
    """{id: {rel, fm, order, body, text}} for notes carrying an id."""
    facts = {}
    if not os.path.isdir(store):
        return facts
    for dirpath, _, files in os.walk(store):
        for fn in sorted(files):
            if not fn.endswith(".md"):
                continue
            p = os.path.join(dirpath, fn)
            text = open(p, encoding="utf-8").read()
            fm, order = _fm_parse(text)
            if fm.get("id"):
                facts[fm["id"]] = {"rel": os.path.relpath(p, store), "fm": fm,
                                   "order": order, "body": _body_of(text), "text": text}
    return facts

def _transact(store, changes):
    """changes: {rel: new_text or None(delete)}. Stage, check, commit."""
    with tempfile.TemporaryDirectory() as td:
        staged = os.path.join(td, "store")
        shutil.copytree(store, staged)
        for rel, new in changes.items():
            dest = os.path.join(staged, rel)
            if new is None:
                os.remove(dest)
            else:
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                with open(dest, "w", encoding="utf-8") as f:
                    f.write(new)
        errors, _ = memory_store_check.check_store(staged)
        if errors:
            raise ValueError(f"transaction blocked by memory_store_check: {errors}")
    for rel, new in changes.items():
        dest = os.path.join(store, rel)
        if new is None:
            os.remove(dest)
        else:
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "w", encoding="utf-8") as f:
                f.write(new)

def _set(fact, **kw):
    fm = dict(fact["fm"])
    for k, v in kw.items():
        fm[k] = str(v)
    return _render(fm, fact["order"], fact["body"])

def apply_edge(store, new_id, target_id, edge, today):
    if edge not in EDGES:
        raise ValueError(f"edge must be one of {EDGES}, got {edge!r}")
    facts = load_facts(store)
    if new_id not in facts:
        raise ValueError(f"new fact {new_id!r} not in store")
    if target_id not in facts:
        raise ValueError(f"target fact {target_id!r} not in store")
    new, tgt = facts[new_id], facts[target_id]
    changes = {}
    kw = {"edge": edge, "supersedes": target_id, "learned_on": new["fm"].get("learned_on", today)}
    if edge == "updates":
        if tgt["fm"].get("status") == "superseded":
            raise ValueError(f"target {target_id!r} is already superseded")
        kw["status"] = "current"
        kw.setdefault("valid_from", new["fm"].get("valid_from", today))
        changes[tgt["rel"]] = _set(tgt, status="superseded",
                                   valid_until=tgt["fm"].get("valid_until", today))
    elif edge == "derives":
        kw["inferred"] = "true"
        kw["review"] = new["fm"].get("review", "pending")
    changes[new["rel"]] = _set(new, **kw)
    _transact(store, changes)
    return {"new": new_id, "target": target_id, "edge": edge}

def _support_counts(store, facts):
    counts = {fid: 0 for fid in facts}
    texts = []
    if os.path.isdir(store):
        for dirpath, _, files in os.walk(store):
            for fn in sorted(files):
                if fn.endswith(".md"):
                    texts.append(open(os.path.join(dirpath, fn), encoding="utf-8").read())
    for fid in counts:
        for f in facts.values():
            if f["fm"].get("supersedes") == fid or fid in f["fm"].get("links", ""):
                counts[fid] += 1
        counts[fid] += sum(1 for t in texts if fid in t) - 1  # minus its own file
    return counts

def review_queue(store):
    facts = load_facts(store)
    support = _support_counts(store, facts)
    pending = [{"id": fid, "support": support[fid], "rel": f["rel"]}
               for fid, f in facts.items() if f["fm"].get("review") == "pending"]
    pending.sort(key=lambda r: (-r["support"], r["id"]))
    return pending

def apply_review(store, fact_id, decision, today):
    if decision not in ("approve", "decline"):
        raise ValueError(f"decision must be approve or decline, got {decision!r}")
    facts = load_facts(store)
    if fact_id not in facts:
        raise ValueError(f"fact {fact_id!r} not in store")
    if decision == "decline":
        return {"id": fact_id, "decision": "decline",
                "forget": forget_by_id(store, [fact_id], today)}
    _transact(store, {facts[fact_id]["rel"]: _set(facts[fact_id], review="approved")})
    return {"id": fact_id, "decision": "approve"}

def propose_correction(store, target_id, new_rel, new_body, today):
    facts = load_facts(store)
    if target_id not in facts:
        raise ValueError(f"target fact {target_id!r} not in store")
    new_id = deterministic_id(["correction", target_id, new_body, today])[:16]
    fm = {"id": new_id, "status": "proposed", "edge": "updates",
          "supersedes": target_id, "learned_on": today}
    text = _render(fm, list(fm), new_body if new_body.endswith("\n") else new_body + "\n")
    _transact(store, {new_rel: text})
    return new_id

def apply_correction(store, successor_id, today):
    facts = load_facts(store)
    if successor_id not in facts:
        raise ValueError(f"successor {successor_id!r} not in store")
    suc = facts[successor_id]
    if suc["fm"].get("status") != "proposed":
        raise ValueError(f"successor {successor_id!r} is not proposed (status={suc['fm'].get('status')!r})")
    target_id = suc["fm"].get("supersedes")
    if target_id not in facts:
        raise ValueError(f"correction target {target_id!r} not in store")
    tgt = facts[target_id]
    _transact(store, {
        suc["rel"]: _set(suc, status="current", valid_from=today),
        tgt["rel"]: _set(tgt, status="superseded", valid_until=tgt["fm"].get("valid_until", today)),
    })
    return {"applied": successor_id, "superseded": target_id}

def _tombstones(store):
    p = os.path.join(store, "erasure", "tombstones.jsonl")
    out = set()
    if os.path.isfile(p):
        for line in open(p, encoding="utf-8"):
            try:
                out.add(json.loads(line)["id"])
            except Exception:
                continue
    return out

def forget_by_id(store, ids, today, index_path=None):
    facts = load_facts(store)
    gone = _tombstones(store)
    results, changes = {}, {}
    for fid in ids:
        if fid in facts:
            changes[facts[fid]["rel"]] = None
            results[fid] = "forgotten"
        elif fid in gone:
            results[fid] = "already_forgotten"
        else:
            results[fid] = "not_found"
    if changes:
        _transact(store, changes)
        forgotten = [fid for fid, r in results.items() if r == "forgotten"]
        rels = {facts[fid]["rel"] for fid in forgotten}
        index_cleaned = []
        if index_path and os.path.isfile(index_path):
            idx = json.load(open(index_path, encoding="utf-8"))
            kept = {k: v for k, v in idx.items() if k not in rels and v not in rels}
            index_cleaned = sorted(set(idx) - set(kept))
            with open(index_path, "w", encoding="utf-8") as f:
                json.dump(kept, f, indent=1, sort_keys=True)
        edir = os.path.join(store, "erasure")
        os.makedirs(edir, exist_ok=True)
        receipt = {"date": today, "results": {k: results[k] for k in forgotten},
                   "index_cleaned": index_cleaned}
        rp = os.path.join(edir, f"erasure-{today}-{deterministic_id([today] + forgotten)[:8]}.json")
        with open(rp, "w", encoding="utf-8") as f:
            json.dump(receipt, f, indent=1)
        with open(os.path.join(edir, "tombstones.jsonl"), "a", encoding="utf-8") as f:
            for fid in forgotten:
                f.write(json.dumps({"id": fid, "date": today, "receipt": os.path.basename(rp)}) + "\n")
        results["_receipt"] = rp
    return results

def semantic_forget_preview(store, query):
    """Dry run (mandatory): the IDs a semantic forget WOULD delete."""
    import memory_search_local
    facts = load_facts(store)
    hits = memory_search_local.search(store, query)
    return sorted({f["fm"]["id"] for h in hits
                   for f in [facts.get(h["rel"] and _fact_by_rel(facts, h["rel"]))] if f})

def _fact_by_rel(facts, rel):
    for f in facts.values():
        if f["rel"] == rel:
            return f
    return None

def forget_semantic_commit(store, preview_ids, today, index_path=None):
    """Delete exactly the previewed IDs; the match is never re-run."""
    return forget_by_id(store, list(preview_ids), today, index_path=index_path)

def audit_corpus(store, near_miss_path=None):
    notes = {}
    if os.path.isdir(store):
        for dirpath, _, files in os.walk(store):
            for fn in sorted(files):
                if fn.endswith(".md") and fn != "MEMORY.md":
                    p = os.path.join(dirpath, fn)
                    notes[os.path.relpath(p, store)] = open(p, encoding="utf-8").read()
    malformed = {rel for rel, t in notes.items()
                 if t.startswith("---") and "\n---" not in t[3:]}
    parent = {rel: rel for rel in notes}
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra
    rels = sorted(notes)
    hashes = {rel: hashlib.sha256(notes[rel].encode()).hexdigest() for rel in rels}
    toks = {rel: set(TOK.findall(notes[rel].lower())) for rel in rels}
    for i, a in enumerate(rels):
        for b in rels[i + 1:]:
            if hashes[a] == hashes[b]:
                union(a, b)
            elif toks[a] and toks[b] and len(toks[a] & toks[b]) / len(toks[a] | toks[b]) >= NEAR_DUP_JACCARD:
                union(a, b)
    clusters = {}
    for rel in rels:
        clusters.setdefault(find(rel), []).append(rel)
    cls = {rel: "clean" for rel in rels}
    for rel in malformed:
        cls[rel] = "malformed"
    loop_clusters = []
    for members in clusters.values():
        if len(members) < 2:
            continue
        kind = "feedback_loop" if len(members) >= 3 else "duplicate"
        if kind == "feedback_loop":
            loop_clusters.append(sorted(members))
        for rel in sorted(members)[1:]:
            if cls[rel] == "clean":
                cls[rel] = kind
    counts = {"clean": 0, "duplicate": 0, "feedback_loop": 0, "malformed": 0}
    for v in cls.values():
        counts[v] += 1
    total = len(rels)
    junk = total - counts["clean"]
    if near_miss_path:
        led = NearMissLedger(near_miss_path).load()
        for rel in rels:
            if cls[rel] != "clean":
                led.record(f"memory-corpus:{rel}", "other", notes[rel])
    return {"total": total, "counts": counts,
            "junk_rate": round(junk / total, 4) if total else 0.0,
            "feedback_loop_clusters": loop_clusters,
            "classification": cls}

def corpus_summary(store, near_miss_path=None):
    facts = load_facts(store)
    audit = audit_corpus(store, near_miss_path=near_miss_path)
    return {"facts": len(facts), "pending_review": len(review_queue(store)),
            "notes": audit["total"], "junk_rate": audit["junk_rate"],
            "junk_counts": audit["counts"]}

def selftest():
    with tempfile.TemporaryDirectory() as td:
        store = os.path.join(td, "store"); os.makedirs(store)
        open(os.path.join(store, "MEMORY.md"), "w").write("# index\n")
        json.dump({"schema_version": 1}, open(os.path.join(store, "schema_version.json"), "w"))
        def w(rel, fid, body, extra=""):
            open(os.path.join(store, rel), "w").write(f"---\nid: {fid}\n{extra}---\n{body}\n")
        w("a.md", "fact-a", "The fee walk pages by date.")
        w("b.md", "fact-b", "The fee walk pages by token until exhausted.")
        r = apply_edge(store, "fact-b", "fact-a", "updates", "2026-11-03")
        facts = load_facts(store)
        assert facts["fact-a"]["fm"]["status"] == "superseded" and facts["fact-a"]["fm"]["valid_until"] == "2026-11-03", facts["fact-a"]
        assert facts["fact-b"]["fm"]["edge"] == "updates" and facts["fact-b"]["fm"]["valid_from"] == "2026-11-03"
        try:
            apply_edge(store, "fact-b", "fact-a", "updates", "2026-11-03"); raise SystemExit("double supersession must fail")
        except ValueError:
            pass
        w("c.md", "fact-c", "Inferred: the desk probably prefers token paging.")
        apply_edge(store, "fact-c", "fact-b", "derives", "2026-11-03")
        q = review_queue(store)
        assert [x["id"] for x in q] == ["fact-c"], q
        out = apply_review(store, "fact-c", "approve", "2026-11-03")
        assert load_facts(store)["fact-c"]["fm"]["review"] == "approved"
        sid = propose_correction(store, "fact-b", "b2.md", "The fee walk pages by token; CFEE is never added.", "2026-11-03")
        facts = load_facts(store)
        assert facts[sid]["fm"]["status"] == "proposed" and facts["fact-b"]["fm"].get("status") != "superseded"
        apply_correction(store, sid, "2026-11-03")
        facts = load_facts(store)
        assert facts[sid]["fm"]["status"] == "current" and facts["fact-b"]["fm"]["status"] == "superseded"
        idx = os.path.join(td, "index.json")
        json.dump({"b2.md": "x", "a.md": "y", "keep.md": "z"}, open(idx, "w"))
        res = forget_by_id(store, [sid, "fact-zzz"], "2026-11-03", index_path=idx)
        assert res[sid] == "forgotten" and res["fact-zzz"] == "not_found", res
        assert not os.path.exists(os.path.join(store, "b2.md"))
        assert json.load(open(idx)) == {"a.md": "y", "keep.md": "z"}, "derived index copy must be cleaned"
        res2 = forget_by_id(store, [sid], "2026-11-03")
        assert res2[sid] == "already_forgotten", res2
        for i in range(3):
            w(f"loop{i}.md", f"loop-{i}", "The agent notes the gate is green and the gate is green today.")
        nmp = os.path.join(td, "nm.jsonl")
        audit = audit_corpus(store, near_miss_path=nmp)
        assert audit["counts"]["feedback_loop"] == 2, audit
        assert audit["junk_rate"] > 0
        led = NearMissLedger(nmp).load()
        assert led.report()["count"] >= 2, "junk skeletons must land in the near-miss ledger"
        print("SELFTEST PASS memory_edges: typed updates edge retires with bi-temporal stamps, double supersession refused, derives waits in review queue, approve clears, two-phase correction applies atomically, forget returns per-ID results + cleans the index + tombstones, feedback-loop cluster classified and recorded as near misses")
    return 0

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "selftest":
        raise SystemExit(selftest())
    if len(sys.argv) > 1 and sys.argv[1] == "summary":
        store = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "memory_store")
        print(json.dumps(corpus_summary(store), indent=1))
    else:
        print(__doc__)
