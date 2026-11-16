# LOCAL VARIANT (adopted 2026-11-10, IBMA-D05, FIX-ALL Lane D): deliberate
# divergence from InfinityBlade canon 3.3.0 tools/priced_initiative_score.py.
# Canon delegates to skills/agent-enhancement-systems/bin/proactive.py
# (absent at ~/workspace/skills/), makes --lambda required, validates
# windows, and charges MUST-NOT 5/fire (1 + 4 penalty); this self-contained
# local scorer charges MUST-NOT 4/fire and defaults --lambda to 1.0.
# Do not cite as canon-current. Comparison: research_notes/fix-all-20261110/D-COMPARISONS.md
"""Starter for discipline 1: score a proactive lane against a logged timeline.

Input: a JSON file with windows: [{"label": "MUST"|"MAY"|"MUST-NOT"|"OTHER",
"fires": int}]. Benefit: MUST 4, MAY 2, credited once per window. Cost: 4 per
fire on a MUST-NOT window, 1 per fire on any other fired window, charged per
fire. Prints benefit minus lambda times cost for lambda in {0.25,0.5,1,2,4}
and the deploy verdict at the lambda the caller names with --lambda.
A lane that cannot state its lambda has not priced its interruption.
"""
import argparse, json
BENEFIT = {"MUST": 4, "MAY": 2}
ap = argparse.ArgumentParser(); ap.add_argument("timeline"); ap.add_argument("--lambda", dest="lam", type=float, default=1.0)
a = ap.parse_args()
windows = json.load(open(a.timeline, encoding="utf-8"))["windows"]
benefit = sum(BENEFIT.get(w["label"], 0) for w in windows if w.get("fires", 0) > 0)
cost = sum((4 if w["label"] == "MUST-NOT" else 1) * w.get("fires", 0) for w in windows if w.get("fires", 0) > 0)
for lam in (0.25, 0.5, 1, 2, 4):
    print(f"lambda={lam}: benefit={benefit} cost={cost} net={benefit - lam*cost}")
net = benefit - a.lam * cost
print(f"verdict at lambda={a.lam}: {'DEPLOY' if net > 0 else 'SILENCE'} (net {net})")
