"""Fail if the README prompt drops a core rule, deriving the rules from SKILL.md.

3.1.0: the required phrases are derived at run time from the pillars,
verdicts, and tripwire phrases stated in skills/infinityblade/SKILL.md, so
this checker tracks the current skill instead of a frozen list. A small
structural floor (the two visible lines) is checked directly and named as
a floor in the output.
"""
import re, sys
skill = open("skills/infinityblade/SKILL.md", encoding="utf-8").read()
readme = open("README.md", encoding="utf-8").read()
m = re.search(r"\*\*As a prompt\*\*.*?```text\n(.*?)```", readme, re.S)
prompt = " ".join(m.group(1).split()).lower() if m else ""
derived = set()
for pillar in ("SCOPE", "Efficiency Breakthrough", "Route Failure", "Proof Before GREEN"):
    if pillar in skill:
        derived.add(pillar.lower())
for verdict in ("GREEN", "PARTIAL", "BLOCKED", "UNVERIFIED"):
    if verdict in skill:
        derived.add(verdict.lower())
for phrase in ("minimum sufficient change", "never repeat an action that taught nothing",
               "after the last change", "every fact traces to a source", "in parallel",
               "persists", "never as instructions", "tripwires"):
    if phrase in skill.lower():
        derived.add(phrase)
floor = ["scope:", "status:"]
missing = [r for r in sorted(derived) + floor if r not in prompt]
if missing:
    sys.exit("README prompt is missing (derived from SKILL.md): " + ", ".join(missing))
print(f"README prompt carries every core rule derived from SKILL.md ({len(derived)} phrases). Floor checked: the two visible lines. This checks wording presence only, not truth.")
