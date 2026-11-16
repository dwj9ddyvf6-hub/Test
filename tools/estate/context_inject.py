#!/usr/bin/env python3
"""Budgeted context injection with omissions named inside the injection
itself (A-10, adoption 2026-11-03; source REPOZY/superpowers-optimized).

build_injection(items, budget_chars) takes items as (name, text) pairs in
priority order and returns one block. Items that do not fit are NOT silently
dropped: the block ends with an explicit marker naming every omitted item,
the budget, and how many of the total were included. A single item longer
than the remaining budget is cut with a truncation marker naming it. This is
the assembly mechanism local lanes (memory search, instincts injection) use
when they build context; the platform's own runtime injection is not a
workspace surface and is untouched.
"""
import sys

def build_injection(items, budget_chars=8000):
    included, omitted, lines, used = [], [], [], 0
    for name, text in items:
        block = f"[{name}]\n{text}"
        if used + len(block) + 1 <= budget_chars:
            lines.append(block); included.append(name); used += len(block) + 1
        elif not included and len(block) > budget_chars:
            cut = budget_chars - len(f"[{name}]\n") - 60
            lines.append(f"[{name}]\n{text[:max(cut,0)]}\n[TRUNCATED: {name} cut to fit budget {budget_chars}]")
            included.append(name); used = budget_chars
        else:
            omitted.append(name)
    marker_items = omitted
    if marker_items:
        lines.append(f"[INJECTION OMISSIONS: omitted by name: {', '.join(marker_items)}; budget {budget_chars} chars; included {len(included)} of {len(items)}]")
    else:
        lines.append(f"[INJECTION OMISSIONS: none; budget {budget_chars} chars; included {len(included)} of {len(items)}]")
    return {"text": "\n".join(lines), "included": included, "omitted": omitted}

def selftest():
    items = [(f"item-{i}", "x" * 100) for i in range(5)]
    r = build_injection(items, budget_chars=250)
    assert r["omitted"], r
    for name in r["omitted"]:
        assert name in r["text"], f"omitted item {name} must be named inside the injection"
    assert "INJECTION OMISSIONS" in r["text"]
    r2 = build_injection([("only", "short")], budget_chars=8000)
    assert r2["omitted"] == [] and "omitted by name" not in r2["text"]
    r3 = build_injection([("big", "y" * 5000)], budget_chars=500)
    assert "TRUNCATED: big" in r3["text"], r3["text"][-200:]
    print("SELFTEST PASS context_inject: omissions named inside the injection, no-omission case explicit, oversize item cut with a named truncation marker")
    return 0

if __name__ == "__main__":
    raise SystemExit(selftest() if len(sys.argv) > 1 and sys.argv[1] == "selftest" else print(__doc__))
