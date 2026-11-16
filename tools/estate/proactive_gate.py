#!/usr/bin/env python3
"""PRISM closed-form proactive gate. Round-5 item 3 (discipline 1).
tau(p_need) = C_FA / (C_FA + p_need * C_FN); fire iff p_accept >= tau.
Fail-closed on missing/out-of-range inputs. Costs/margin live in per-lane
config read by the gate, never in the generator prompt. Slow mode only
within margin of boundary, charged to same ledger entry. Coded rate caps
(item 6, YETI m/k): min_interval + max_fires_per_window enforced here.
"""
import sys
def tau(c_fa, c_fn, p_need):
    for name,v in [("C_FA",c_fa),("C_FN",c_fn),("p_need",p_need)]:
        if v is None or not isinstance(v,(int,float)): raise ValueError(f"missing {name}: fail closed")
    if c_fa<0 or c_fn<0 or not (0.0<=p_need<=1.0): raise ValueError("out of range: fail closed")
    denom=c_fa+p_need*c_fn
    if denom==0: return 1.0
    return c_fa/denom
def decide(lane_cfg: dict, p_accept, p_need):
    if p_accept is None or not (0.0<=p_accept<=1.0): raise ValueError("p_accept missing/out of range: fail closed")
    t=tau(lane_cfg.get("C_FA"), lane_cfg.get("C_FN"), p_need)
    margin=lane_cfg.get("margin",0.0)
    if p_accept>=t: mode="fire"
    elif p_accept>=t-margin: mode="slow"
    else: mode="silent"
    return {"tau":t,"verdict":mode,"lane":lane_cfg.get("lane","?"),
            "rate_caps":{"min_interval":lane_cfg.get("min_interval"),"max_fires_per_window":lane_cfg.get("max_fires_per_window")}}
def check_rate(history_ts, now, min_interval, max_per_window, window_s=3600):
    if min_interval is None or max_per_window is None: raise ValueError("rate caps unconfigured: fail closed")
    recent=[t for t in history_ts if now-t<window_s]
    if recent and now-max(recent)<min_interval: return False
    return len(recent)<max_per_window
def selftest():
    assert abs(tau(1,1,1)-0.5)<1e-9, "equal costs p_need=1 gives 0.5"
    assert tau(1,1,0)==1.0, "p_need=0 forces silence (tau=1, p_accept<1 normally)"
    assert decide({"C_FA":1,"C_FN":9,"lane":"x"},0.9,1.0)["verdict"]=="fire", "certain need lowers bar"
    assert decide({"C_FA":9,"C_FN":1,"lane":"x"},0.1,0.1)["verdict"]=="silent"
    assert decide({"C_FA":1,"C_FN":1,"margin":0.2,"lane":"x"},0.35,1.0)["verdict"]=="slow"
    for bad in [lambda: tau(None,1,0.5), lambda: tau(1,1,1.5), lambda: decide({},0.5,0.5)]:
        try: bad(); raise SystemExit("fail-closed broken")
        except ValueError: pass
    assert check_rate([1000],1005,60,5) is False and check_rate([1000],2000,60,5) is True
    print("SELFTEST PASS proactive_gate: tau regimes (0.5 equal/p1, 1.0 at p_need=0, certain-need fires), slow within margin, fail-closed on missing/range, rate caps enforced")
    return 0
if __name__=="__main__":
    raise SystemExit(selftest() if len(sys.argv)>1 and sys.argv[1]=="selftest" else print(__doc__))
