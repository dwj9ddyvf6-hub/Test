# Skills

Guidance packs for AI-assisted research with the QuantJourney Backtester. Each
skill is a short `SKILL.md` that teaches an AI coding assistant the engine's
conventions — the real API, timing rules, and what "good" looks like — so it
follows the framework instead of guessing.

## How to use

When you work with an AI assistant, point it at the relevant `SKILL.md` (open
the file, or reference its path) before asking it to write, review, or interpret.
The skill gives it the conventions used by the 45 examples in `strategies/`.

## Available skills

| Skill | Use it to |
|:--|:--|
| [`qj-strategy-ideas`](qj-strategy-ideas/SKILL.md) | Turn an idea into a runnable strategy — weights vs orders, the nearest example, the two-method pattern. |
| [`qj-strategy-author`](qj-strategy-author/SKILL.md) | Write a clean, focused example strategy. |
| [`qj-strategy-reviewer`](qj-strategy-reviewer/SKILL.md) | Review a strategy for look-ahead, exposure, cost realism, and mode fit. |
| [`qj-report-analyst`](qj-report-analyst/SKILL.md) | Read a report and its plots and judge whether the result is trustworthy. |
| [`qj-config-helper`](qj-config-helper/SKILL.md) | Configure the engine — parameters, rebalance policy, risk overlays, granularity. |

## Typical flow

1. **Idea** → `qj-strategy-ideas` to draft a runnable strategy.
2. **Write** → `qj-strategy-author` to keep it clean and conventional.
3. **Configure** → `qj-config-helper` for the rebalance policy, risk overlay, and settings.
4. **Review** → `qj-strategy-reviewer` before trusting it.
5. **Interpret** → `qj-report-analyst` to read the report and judge the result.

See the repository [README](../README.md) and the
[strategy catalog](../strategies/README.md) for the examples these skills refer to.
