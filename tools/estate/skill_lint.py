#!/usr/bin/env python3
"""Skill lint. Round-5 item 28 (anthropics quick_validate.py, corrected:
six allowed properties, not two). Kebab-case name max 64, description max
1024 and no angle brackets, compatibility max 500. Stdlib-only frontmatter
parse (simple key: value subset; PyYAML used if available).

Local amendment (dated ruling, loose-ends DECISIONS-20261103 Q7, executed
2026-11-03): `version` is a seventh allowed property. The canon 3.1.0
library skills carry version frontmatter; the unamended lint rejected the
canonical InfinityBlade SKILL.md itself. This is a named local divergence
from the round-5 six-property floor, not a silent widening: any other
unlisted property still fails.
"""
import re, sys, tempfile, os
ALLOWED={"name","description","license","allowed-tools","metadata","compatibility","version"}
def parse_fm(text):
    if not text.startswith("---"): return None
    end=text.find("\n---",3)
    if end<0: return None
    fm={}
    for line in text[3:end].splitlines():
        if ":" in line and not line.startswith(" "):
            k,v=line.split(":",1); fm[k.strip()]=v.strip().strip("'\"")
    return fm
def lint_text(text):
    fm=parse_fm(text)
    if fm is None: return ["no frontmatter"]
    errs=[]
    for k in fm:
        if k not in ALLOWED: errs.append(f"property not allowed: {k}")
    name=fm.get("name","")
    if not re.fullmatch(r"[a-z0-9-]{1,64}",name or ""): errs.append("name must be kebab-case max 64")
    desc=fm.get("description","")
    if len(desc)>1024: errs.append("description > 1024 chars")
    if "<" in desc or ">" in desc: errs.append("description contains angle brackets")
    if len(fm.get("compatibility",""))>500: errs.append("compatibility > 500 chars")
    return errs
def selftest():
    good="---\nname: my-skill\ndescription: Does a thing when asked.\n---\nbody\n"
    assert lint_text(good)==[], lint_text(good)
    versioned="---\nname: infinityblade\ndescription: Canon skill carrying a version.\nversion: 3.1.0\n---\nbody\n"
    assert lint_text(versioned)==[], f"Q7 amendment: version must be allowed: {lint_text(versioned)}"
    assert any("not allowed" in e for e in lint_text("---\nname: ok-name\ndescription: fine\nbogus: 1\n---\n")), "unlisted property must still fail"
    assert lint_text("---\nname: Bad_Name\ndescription: x <y>\nextra: 1\n---\n")
    assert any("angle" in e for e in lint_text("---\nname: ok-name\ndescription: has <tag>\n---\n"))
    print("SELFTEST PASS skill_lint: valid skill passes, bad name/extra property/angle brackets each fail")
    return 0
if __name__=="__main__":
    if len(sys.argv)>1 and sys.argv[1]=="selftest": raise SystemExit(selftest())
    errs=lint_text(open(sys.argv[1],encoding="utf-8").read()); print(errs); raise SystemExit(1 if errs else 0)
