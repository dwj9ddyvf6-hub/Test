Algorithm derived from the sleeve code on 2026-10-29 (no author spec on file).

# 1dc: Algorithm

## What it trades
Long-only equity entries driven by Lazarus fires. This sleeve is a thin
wrapper (module adapters3/laz_1dc.py in the desk) whose evaluate(view, ctx)
delegates to the shared engine desk3/lazarus.py with SLEEVE_ID "1dc".
It implements no strategy math of its own; all rules below are the engine
rules for this sleeve id.

## Data inputs
Config inputs: lazarus_fires, bars, positions. The engine reads fires from
view["lazarus_fires"] (or view["extra"]["lazarus_fires"] / view["tensor_fires"]),
bars from view["bars"], and open positions from view["positions"]. Fires are
records with sleeve_id, symbol, fired_at, price, and optional target_price,
family/color, cap_tier, signal_tier, qqq_red and stock_red fields. The desk
tracker source is unreachable from the desk host, so ingested fires in the
snapshot are the only fire source. Fail-closed: no fresh matching fire means
no entry, and missing QQQ-red data for a QQQ-down sleeve means no entry.

## Entry rules
- Fire sleeve_id must match this sleeve (when present), symbol not already
  held, side buy/long when present, fired_at parsed and age within the limit.
- Maximum fire age: 2880 minutes (48 hours).
- QQQ-down gate: this sleeve requires QQQ red (fire qqq_red/qqq_down when
  carried, otherwise computed from QQQ bars: last close below prior close).
- Family filter: cyan (enforced when the fire carries a family/color). Timeframe tag in the spec: 1D.
- Horizon is taken from the fire when the spec horizon_from_fire flag applies.
- Entries stop when open positions reach the slot count.
- Sizing: equal slots, capital divided by slots (see below). With the
  fresh-price enhancement on by default, size, stop anchor and price hint use
  the freshest completed bar close in the same snapshot instead of the
  possibly stale fire print; the fire print is the fallback when no bars exist.

## Exit rules
Exits are evaluated before entries, in this order:
- No percent stop in this spec (stop_pct is None).
- Target price: exit in full when current price reaches the fire target_price stored in sleeve state, when one was recorded.
- No partial or percent target in this spec.
- Horizon: 21 sessions.
- Time exit when sessions held reaches the horizon.

## Sizing, session and cadence
- Slots: 68. Sleeve capital: $12,500 (per-slot $183.82).
- Cadence: 300 seconds. Session: rth. Flat by close: no.
- Config slice in desk config/sleeves.json matches the engine spec above.

## Ambiguity note
Per-fire family, tier and cap filters are enforced only when the fire record
carries the field; a fire without the field is not rejected on that filter.
That is the engine behaviour as coded, not an added rule.
