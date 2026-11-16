#!/usr/bin/env python3
"""Recursive diagnostic redactor. Round-5 item 43 (ChatGPTBox redact.mjs +
Supermemory plugin redact.js, as specified in SYNTHESIS item 43 before its
truncation). Key-substring classes + prompt/question/query/selection key
classes. Markers: REDACTED / REDACTED_CIRCULAR_REFERENCE / REDACTED_TOO_DEEP.
Capture-delta rule: redaction applies at capture time, before storage.
"""
import sys
SENSITIVE_SUBSTRINGS=("password","secret","token","api_key","apikey","credential","private_key","authorization","cookie","session")
CONTENT_KEYS={"prompt","question","query","selection"}
MAX_DEPTH=8
def _key_sensitive(k):
    lk=str(k).lower()
    return any(s in lk for s in SENSITIVE_SUBSTRINGS) or lk in CONTENT_KEYS
def redact(obj, _depth=0, _seen=None):
    if _seen is None: _seen=set()
    if id(obj) in _seen and isinstance(obj,(dict,list)): return "REDACTED_CIRCULAR_REFERENCE"
    if _depth>MAX_DEPTH: return "REDACTED_TOO_DEEP"
    if isinstance(obj,dict):
        _seen.add(id(obj))
        return {k:("REDACTED" if _key_sensitive(k) else redact(v,_depth+1,_seen)) for k,v in obj.items()}
    if isinstance(obj,list):
        _seen.add(id(obj)); return [redact(v,_depth+1,_seen) for v in obj]
    return obj
def selftest():
    d={"user":"sam","api_key":"abc","nested":{"user_password":"x","note":"keep"},"prompt":"full text"}
    r=redact(d); assert r["api_key"]=="REDACTED" and r["nested"]["user_password"]=="REDACTED" and r["nested"]["note"]=="keep" and r["prompt"]=="REDACTED" and r["user"]=="sam", r
    cyc={}; cyc["self"]=cyc; assert redact(cyc)["self"]=="REDACTED_CIRCULAR_REFERENCE"
    deep=cur={}; 
    for i in range(12): cur["n"]={}; cur=cur["n"]
    out=redact(deep); s=str(out); assert "REDACTED_TOO_DEEP" in s
    print("SELFTEST PASS redact: key-substring + content-key classes redacted, innocuous values kept, circular and too-deep markers emitted")
    return 0
if __name__=="__main__":
    raise SystemExit(selftest() if len(sys.argv)>1 and sys.argv[1]=="selftest" else print(__doc__))
