#!/usr/bin/env python3
"""Skill token cost budgets. Round-5 item 29 (openai/plugins plugin-eval).
Three banded costs (tokens): trigger 48/92/150, invoke 220/480/900,
deferred 180/520/1200. Explicit-only skills excluded from implicit cost and
reported separately. Static estimate ~ chars/4; heavy implicit band fails
review until explicit-only or split.
"""
import sys
BANDS={"trigger":(48,92,150),"invoke":(220,480,900),"deferred":(180,520,1200)}
def band(kind, tokens):
    lo,mid,hi=BANDS[kind]
    return "light" if tokens<=lo else "standard" if tokens<=mid else "heavy" if tokens<=hi else "over"
def estimate(skill_text, description, explicit_only=False):
    trig=len(description)//4; inv=len(skill_text)//4
    rep={"trigger_tokens":trig,"trigger_band":band("trigger",trig),
         "invoke_tokens":inv,"invoke_band":band("invoke",inv),"explicit_only":explicit_only}
    rep["fails_review"]= (not explicit_only) and rep["invoke_band"] in ("heavy","over")
    return rep
def selftest():
    r=estimate("x"*400,"d"*100); assert r["trigger_band"]=="light" and not r["fails_review"], r
    r=estimate("x"*4000,"d"*100); assert r["fails_review"], "heavy implicit must fail review"
    r=estimate("x"*4000,"d"*100,explicit_only=True); assert not r["fails_review"], "explicit-only reported separately"
    print("SELFTEST PASS skill_cost: light passes, heavy implicit fails review, explicit-only excluded from implicit failure")
    return 0
if __name__=="__main__":
    raise SystemExit(selftest() if len(sys.argv)>1 and sys.argv[1]=="selftest" else print(__doc__))
