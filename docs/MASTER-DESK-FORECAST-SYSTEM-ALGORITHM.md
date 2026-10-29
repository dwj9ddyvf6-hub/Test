# master-desk-forecast-system

Created by Claude (master desk). Packaged into the Test repo on 2026-10-29 (packaging pass).

Origin: dwj9ddyvf6-hub/Femto-lean repo, branch master-desk @ 53096b3a, path desk/forecast/.

The master desk's forecast system: a registry-driven forecast engine set (REGISTRY.md, adapters/, frozen/ contract copies) with capacity, card, context, cost, data, ensemble, freeze, and gate modules. Forecasts are issued as cards under frozen contracts, ensembled across engines, and passed through eligibility gates before they can influence the desk; the freeze/frozen machinery pins the exact contract versions a forecast was made under so the record can be graded against what was actually said at the time.

## Files in this package

- `packages/claude/master-desk-forecast-system/desk/forecast/REGISTRY.md`
- `packages/claude/master-desk-forecast-system/desk/forecast/__init__.py`
- `packages/claude/master-desk-forecast-system/desk/forecast/adapters/__init__.py`
- `packages/claude/master-desk-forecast-system/desk/forecast/adapters/_common.py`
- `packages/claude/master-desk-forecast-system/desk/forecast/adapters/avoid.py`
- `packages/claude/master-desk-forecast-system/desk/forecast/adapters/engine.py`
- `packages/claude/master-desk-forecast-system/desk/forecast/adapters/features.py`
- `packages/claude/master-desk-forecast-system/desk/forecast/adapters/odds.py`
- `packages/claude/master-desk-forecast-system/desk/forecast/adapters/picker.py`
- `packages/claude/master-desk-forecast-system/desk/forecast/adapters/regime.py`
- `packages/claude/master-desk-forecast-system/desk/forecast/adapters/survivors.py`
- `packages/claude/master-desk-forecast-system/desk/forecast/adapters/vendors.py`
- `packages/claude/master-desk-forecast-system/desk/forecast/adapters/vendors2.py`
- `packages/claude/master-desk-forecast-system/desk/forecast/adapters/vendors3.py`
- `packages/claude/master-desk-forecast-system/desk/forecast/capacity.py`
- `packages/claude/master-desk-forecast-system/desk/forecast/cards.py`
- `packages/claude/master-desk-forecast-system/desk/forecast/contexts.py`
- `packages/claude/master-desk-forecast-system/desk/forecast/costs.py`
- `packages/claude/master-desk-forecast-system/desk/forecast/data.py`
- `packages/claude/master-desk-forecast-system/desk/forecast/ensemble.py`
- `packages/claude/master-desk-forecast-system/desk/forecast/freeze.py`
- `packages/claude/master-desk-forecast-system/desk/forecast/frozen/avoid-deep-1.json`
- `packages/claude/master-desk-forecast-system/desk/forecast/frozen/promoted-book-1.json`
- `packages/claude/master-desk-forecast-system/desk/forecast/gates.py`
- `packages/claude/master-desk-forecast-system/desk/forecast/laws.py`
- `packages/claude/master-desk-forecast-system/desk/forecast/operator.py`
- `packages/claude/master-desk-forecast-system/desk/forecast/portfolio.py`
- `packages/claude/master-desk-forecast-system/desk/forecast/promoted.py`
- `packages/claude/master-desk-forecast-system/desk/forecast/registry.py`
- `packages/claude/master-desk-forecast-system/desk/forecast/replicate.py`
- `packages/claude/master-desk-forecast-system/desk/forecast/router.py`
- `packages/claude/master-desk-forecast-system/desk/forecast/score.py`
- `packages/claude/master-desk-forecast-system/desk/forecast/search.py`
- `packages/claude/master-desk-forecast-system/desk/forecast/search_deep.py`
- `packages/claude/master-desk-forecast-system/desk/forecast/targets.py`
- `packages/claude/master-desk-forecast-system/desk/forecast/today.py`
- `packages/claude/master-desk-forecast-system/desk/forecast/xs.py`

Source files are verbatim copies from the origin location named above unless a sanitization note appears in this doc.
