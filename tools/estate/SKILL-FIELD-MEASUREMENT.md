# Skill field measurement: the 30-day rule for every learned skill (T-235)

Standing rule, stated once for all skills (the pattern previously lived
only inside individual skill.yaml files). Every learned skill is a
measured claim about future performance, not just a document. Its
`skill.yaml` must carry, under `skill_improvement`:

- `evidence_handles`: a non-empty list naming the episodes that created
  or last changed the skill, so the claim can be traced to its evidence.
- `measurement.success_criterion`: a proxy success criterion stated as
  an observable outcome over the 30 days after install
  (`measurement.window_days: 30`).
- `review_after`: the date the field measurement is reviewed; arriving
  at that date with no review is an open item, not a pass.
- `rationale`: a paragraph naming what was checked, what was changed,
  and what was considered and not proposed, so a later reader can tell
  a measured decision from a guess.

Consolidation is reviewed before any new skill is added, and merging is
rejected when it would trade specific methods for a vaguer general one.

Mechanical check: `skill_field_check.py` validates one skill.yaml (or a
whole skills root) against this rule and names every missing or overdue
field. It reads only; it never edits a skill.
