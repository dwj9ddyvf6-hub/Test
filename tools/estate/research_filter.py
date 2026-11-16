#!/usr/bin/env python3
"""Scored research filter (adoption item A-27, source: assafelovic/gpt-researcher).

The research workflow's filter step produces a FILE: every retrieved chunk
carries a 0 to 3 usefulness score against its sub-question, chunks scoring
under 1 drop, and the kept and dropped sets are both written out so the
filter is auditable, never silent.

Rubric (score against the chunk's sub-question):
  3 = directly answers the sub-question with usable evidence
  2 = materially supports an answer (partial evidence or key context)
  1 = marginally relevant (background, a pointer, a weak corroboration)
  0 = not useful for the sub-question (off-topic, duplicate, or empty)

Usage: research_filter.py <chunks.json> <out.json>
Input: [{"id":..., "sub_question":..., "text":..., "score":0..3}, ...]
Output file: {"kept": [...], "dropped": [...], "threshold": 1}
"""
import json, sys

THRESHOLD = 1

def filter_chunks(chunks):
    kept, dropped = [], []
    for c in chunks:
        s = c.get("score")
        if not isinstance(s, (int, float)) or not (0 <= s <= 3):
            raise ValueError(f"chunk {c.get('id')!r} has no valid 0..3 score: {s!r}")
        (kept if s >= THRESHOLD else dropped).append(c)
    return {"kept": kept, "dropped": dropped, "threshold": THRESHOLD}

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__); sys.exit(2)
    with open(sys.argv[1], encoding="utf-8") as f:
        chunks = json.load(f)
    result = filter_chunks(chunks)
    with open(sys.argv[2], "w", encoding="utf-8") as f:
        json.dump(result, f, indent=1)
    print(f"kept {len(result['kept'])}, dropped {len(result['dropped'])} (threshold {THRESHOLD})")
