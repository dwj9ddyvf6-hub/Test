#!/usr/bin/env python3
"""Local memory search over the tooling memory store, with the two ranking
pieces adopted 2026-11-03:

A-5 (mem0): one-pass fusion of semantic similarity, keyword match, and entity
matching at a generous top-N budget, no agentic loop. Locally the semantic
component is a lexical proxy (body token overlap; no embedding service is a
workspace surface, and the score components are reported per hit so the proxy
is never dressed as an embedding). The new piece is the entity-match boost:
entities (capitalised phrases, backticked tokens, [[links]], frontmatter
entities:) that recur across the store and match the query add a fixed boost
per matched entity.

A-4 (memoket-kite): thread-following recall. After ranking, the search walks
the linked-ids chain (frontmatter links: and [[...]] references) from the top
hits, breadth-first to depth 3, and appends chained notes the ranking missed,
each marked via=thread with its depth. A fact reachable only through the
chain is recalled, not lost because its own text matched nothing.

Honest recall tiers (discipline 5, added 2026-11-03): recall() wraps
search() and reports what it actually found. supported: the best ranked
score meets SUPPORTED_MIN, a real match. closest-only: below the bar;
at most PREVIEW_MAX previews of PREVIEW_CHARS, labelled and never
claimed relevant. not present: no ranked hit at all. Confidence is the
best score normalised; above CONF_DIRECT the recall returns directly,
below CONF_DEEP it spends exactly one deeper exploration round (double
top_n). Admission is enforced here, at the recall boundary: notes with
frontmatter status proposed or superseded are excluded from every
result, and unapproved inferred notes are flagged inferred on the hit.

CLI: memory_search_local.py '<query>' [store_root] [top_n]
     memory_search_local.py recall '<query>' [store_root]
     memory_search_local.py selftest
"""
import os, re, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import context_inject

ENTITY_BOOST = 0.5      # per query-matched entity (A-5)
RECURRENCE_BOOST = 0.1  # per extra store note sharing a matched entity
KEYWORD_W = 1.0         # title / frontmatter token match
SEMANTIC_W = 0.6        # body token overlap (lexical proxy, reported as such)
THREAD_DEPTH = 3
DEFAULT_TOP_N = 20      # generous top-N budget, one pass, no agentic loop

TOK = re.compile(r"[a-z0-9]+")
LINK = re.compile(r"\[\[([^\]]+)\]\]")

def _tokens(text):
    return TOK.findall((text or "").lower())

def _frontmatter(text):
    fm = {}
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            for line in text[3:end].splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    fm[k.strip().lower()] = v.strip()
    return fm

def _entities(name, fm, text):
    ents = set()
    for raw in fm.get("entities", "").strip("[]").split(","):
        if raw.strip():
            ents.add(raw.strip().lower())
    ents.update(m.group(1).strip().lower() for m in LINK.finditer(text))
    ents.update(t.lower() for t in re.findall(r"`([^`]{2,40})`", text))
    ents.update(p.lower() for p in re.findall(r"\b([A-Z][a-z]+(?: [A-Z][a-z]+)+)\b", text))
    return ents

def _links(fm, text):
    out = []
    for raw in fm.get("links", "").strip("[]").split(","):
        if raw.strip():
            out.append(raw.strip())
    out.extend(m.group(1).strip() for m in LINK.finditer(text))
    return out

def load_store(root):
    notes = {}
    for dirpath, _, files in os.walk(root):
        for fn in sorted(files):
            if not fn.endswith(".md"):
                continue
            p = os.path.join(dirpath, fn)
            rel = os.path.relpath(p, root)
            text = open(p, encoding="utf-8").read()
            fm = _frontmatter(text)
            notes[rel] = {"rel": rel, "name": fn[:-3], "text": text, "fm": fm,
                          "entities": _entities(fn, fm, text), "links": _links(fm, text)}
    by_name = {}
    for n in notes.values():
        by_name[n["name"]] = n["rel"]
        by_name[n["rel"]] = n["rel"]
        if n["fm"].get("id"):
            by_name[n["fm"]["id"]] = n["rel"]
    return notes, by_name

def search(root, query, top_n=DEFAULT_TOP_N):
    notes, by_name = load_store(root)
    q_tokens = set(_tokens(query))
    q_ents = {e for e in _entities("", {}, query)}
    # entity recurrence across the store (A-5: recurrence is the boost signal)
    recurrence = {}
    for n in notes.values():
        for e in n["entities"]:
            recurrence[e] = recurrence.get(e, 0) + 1
    scored = []
    for n in notes.values():
        if n["fm"].get("status") in ("proposed", "superseded"):
            continue  # admission: unapplied successors and retired facts never surface
        title_tokens = set(_tokens(n["name"] + " " + " ".join(n["fm"].values())))
        body_tokens = set(_tokens(n["text"]))
        keyword = len(q_tokens & title_tokens)
        semantic = len(q_tokens & body_tokens) / max(len(q_tokens), 1)
        matched_ents = {e for e in n["entities"] if e in q_ents or e in query.lower()}
        entity_score = sum(ENTITY_BOOST + RECURRENCE_BOOST * (recurrence[e] - 1) for e in matched_ents)
        score = KEYWORD_W * keyword + SEMANTIC_W * semantic + entity_score
        if score > 0:
            scored.append({"rel": n["rel"], "score": round(score, 3), "via": "ranked",
                           "inferred": n["fm"].get("inferred") == "true" and n["fm"].get("review") != "approved",
                           "components": {"keyword": keyword, "semantic_proxy": round(semantic, 3),
                                          "entity": round(entity_score, 3)},
                           "matched_entities": sorted(matched_ents)})
    scored.sort(key=lambda r: (-r["score"], r["rel"]))
    hits = scored[:top_n]
    seen = {h["rel"] for h in hits}
    # A-4: follow the linked-ids chain from the ranked hits
    frontier = [(h["rel"], 0) for h in hits]
    visited = set(seen)
    while frontier:
        rel, depth = frontier.pop(0)
        if depth >= THREAD_DEPTH:
            continue
        for link in notes[rel]["links"]:
            target = by_name.get(link) or by_name.get(link + ".md")
            if target and target not in visited and notes[target]["fm"].get("status") not in ("proposed", "superseded"):
                visited.add(target)
                hits.append({"rel": target, "score": 0.0, "via": "thread", "thread_depth": depth + 1,
                             "inferred": notes[target]["fm"].get("inferred") == "true" and notes[target]["fm"].get("review") != "approved",
                             "components": {"keyword": 0, "semantic_proxy": 0.0, "entity": 0.0},
                             "matched_entities": []})
                frontier.append((target, depth + 1))
    return hits

SUPPORTED_MIN = 2.0   # the stated supported bar for the best ranked score
CONF_DIRECT = 0.8     # confidence above this returns directly
CONF_DEEP = 0.5       # confidence below this spends one deeper round
PREVIEW_MAX = 3       # closest-only previews: at most 3
PREVIEW_CHARS = 240   # ... of at most 240 characters

def recall(root, query, top_n=DEFAULT_TOP_N):
    """Tiered recall (discipline 5). A failed lookup proves the lookup
    failed, not that the fact does not exist: the tier says which."""
    notes, _ = load_store(root)
    store_state = "empty" if not notes else "ready"
    hits = search(root, query, top_n)
    ranked = [h for h in hits if h["via"] == "ranked"]
    if not ranked:
        return {"tier": "not present", "confidence": 0.0, "hits": [], "previews": [],
                "exploration_rounds": 0, "store_state": store_state}
    best = ranked[0]["score"]
    confidence = round(min(1.0, best / 4.0), 3)
    if best >= SUPPORTED_MIN:
        return {"tier": "supported", "confidence": confidence, "hits": hits, "previews": [],
                "exploration_rounds": 0, "store_state": store_state}
    rounds = 0
    if confidence < CONF_DEEP:
        rounds = 1  # exactly one deeper exploration round, bounded
        hits = search(root, query, top_n * 2)
        ranked = [h for h in hits if h["via"] == "ranked"]
    previews = [{"rel": h["rel"], "preview": notes[h["rel"]]["text"][:PREVIEW_CHARS],
                 "note": "related only; not claimed relevant"} for h in ranked[:PREVIEW_MAX]]
    return {"tier": "closest-only", "confidence": confidence, "hits": [], "previews": previews,
            "exploration_rounds": rounds, "store_state": store_state}

def injection_for(root, query, budget_chars=8000, top_n=DEFAULT_TOP_N):
    hits = search(root, query, top_n)
    notes, _ = load_store(root)
    items = [(h["rel"], notes[h["rel"]]["text"][:2000]) for h in hits]
    return context_inject.build_injection(items, budget_chars), hits

def selftest():
    with tempfile.TemporaryDirectory() as td:
        def w(name, text):
            open(os.path.join(td, name), "w").write(text)
        w("MEMORY.md", "# index\n")
        w("alpha.md", "---\nentities: fee-walk\nlinks: [beta]\n---\nThe fee walk uses the generic endpoint for fees.\n")
        w("beta.md", "---\nlinks: [gamma]\n---\nA note about scheduling unrelated words.\n")
        w("gamma.md", "The cash halt residue is explained in this chained note.\n")
        w("delta.md", "---\nentities: fee-walk\n---\nAnother fees note mentioning the endpoint briefly.\n")
        hits = search(td, "fee-walk fees endpoint")
        rels = [h["rel"] for h in hits]
        assert "gamma.md" in rels, f"thread-following must recall the chained note: {rels}"
        g = hits[rels.index("gamma.md")]
        assert g["via"] == "thread" and g["thread_depth"] == 2, g
        ranked = [h for h in hits if h["via"] == "ranked"]
        assert ranked[0]["components"]["entity"] > 0, f"entity boost must fire: {ranked}"
        inj, _ = injection_for(td, "fee-walk fees endpoint", budget_chars=300)
        assert "INJECTION OMISSIONS" in inj["text"]
        # Tiered recall: a held-out probe set with known answers; the tier
        # returned must match the known answer on every probe (discipline
        # 5's calibration measurement, run against this fixture store).
        probes = [("fee-walk fees endpoint", "supported"),
                  ("scheduling", "closest-only"),
                  ("zxqw platypus", "not present")]
        for q, want in probes:
            got = recall(td, q)
            assert got["tier"] == want, f"probe {q!r}: tier {got['tier']!r} != known {want!r}"
            if want == "closest-only":
                assert got["hits"] == [] and 1 <= len(got["previews"]) <= PREVIEW_MAX
                assert all(len(p["preview"]) <= PREVIEW_CHARS for p in got["previews"])
                assert got["exploration_rounds"] == 1, "low confidence must spend exactly one deeper round"
        # Admission at the recall boundary: proposed and superseded notes
        # never surface; an unapproved inferred note is flagged.
        w("old.md", "---\nstatus: superseded\n---\nThe zzold token lives here.\n")
        w("prop.md", "---\nstatus: proposed\n---\nThe zzprop token lives here.\n")
        w("inf.md", "---\ninferred: true\nentities: fee-walk\n---\nAn inferred fees note about the endpoint.\n")
        assert search(td, "zzold") == [] and search(td, "zzprop") == []
        inf_hits = [h for h in search(td, "fee-walk fees endpoint") if h["rel"] == "inf.md"]
        assert inf_hits and inf_hits[0]["inferred"] is True, inf_hits
        print("SELFTEST PASS memory_search_local: chained note recalled via thread at depth 2 though its text matched nothing, entity-match boost present in ranked components, injection names omissions, tier probes 3/3 match known answers, proposed/superseded excluded, inferred flagged")
    return 0

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "selftest":
        raise SystemExit(selftest())
    if len(sys.argv) > 2 and sys.argv[1] == "recall":
        root = sys.argv[3] if len(sys.argv) > 3 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "memory_store")
        import json
        print(json.dumps(recall(root, sys.argv[2]), indent=1))
    elif len(sys.argv) > 1:
        root = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "memory_store")
        import json
        print(json.dumps(search(root, sys.argv[1], int(sys.argv[3]) if len(sys.argv) > 3 else DEFAULT_TOP_N), indent=1))
    else:
        print(__doc__)
