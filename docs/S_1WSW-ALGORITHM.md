Algorithm derived from the sleeve code on 2026-10-29 (no author spec on file).

# s_1wsw: Algorithm

## What it trades
A thin wrapper sleeve. The file adapters3/laz_s_1wsw.py is the
per-sleeve core: evaluate() delegates to the shared engine
desk3/lazarus.py evaluate(SLEEVE_ID, view, ctx), with INPUTS taken
from that engine. It is a long-only equity Lazarus fire-consumer
sleeve: signal generation stays upstream in the fire producer and
this engine consumes only ingested fires via the snapshot.
Fail-closed: no fresh matching fire means no entry; missing
QQQ-red data for a QQQ-down sleeve means no entry. The sleeve runs
on the shared engine desk3/lazarus.py.

## Spec (from SPECS in desk3/lazarus.py)
slots=1, capital=1000.0, cadence_s=3600, session="rth",
max_age_min=11520 (60*24*8), qqq_down=True, stop_pct=0.15,
horizon_sessions=126, family="swing", tf="1W".
- Inputs: lazarus_fires, bars, positions.
- Fires are read from view["lazarus_fires"], view["extra"]
  ["lazarus_fires"], view["tensor_fires"], or view["extra"]
  ["fires"] (the first list found).

## Entry rules
- Exits are evaluated first; if any exit intent is emitted, no
  entry is evaluated in the same call.
- A fire is skipped if its sleeve_id differs, its symbol is
  already held, its side is not buy/long, it has no parseable
  fired_at/ts, or its age is below 0 or above the spec
  max_age_min. Entries stop once the spec slots are filled.
- Family, signal-tier and cap-tier filters are enforced only
  when the fire carries that field: a carried family/color must
  contain the spec family, a carried signal_tier/tier must equal
  the spec signal_tier, and a carried cap_tier must be in the
  spec cap tier(s).
- QQQ-down gate: the fire qqq_red/qqq_down value, or (when
  absent) QQQ red derived from QQQ bars (last close below the
  prior close, or below its open on a single bar), must be
  True; missing data fails closed.
- Price: the fire price, falling back to the latest bar close.
  Execution-price revalidation (ENH-LAZ-REPRICE-20261024, switch
  default ON; OFF restores the fire-price rule exactly): when a
  fresh bar close exists and differs, sizing, stop and price_hint
  use the fresh close, and the fire-price decision is recorded as
  the paired shadow control on the entry intent.
- Bound guard (ENH19-LAZ-BOUND-20261024, switch default ON; OFF
  restores the pre-change rule): refuse an entry whose fresh
  price is at or above the fire target_price, or at/above the
  spec max_price where one is set (above it where the spec marks
  the cap inclusive).
- Sizing: per_slot = capital / slots; qty = int(per_slot //
  execution price); qty < 1 emits nothing. Orders are market,
  day, buy, with stop_price = round(price * (1 - stop_pct), 4)
  when the spec sets a stop, otherwise None, and price_hint set
  to the execution price. The entry records horizon_sessions
  (the fire's own horizon when carried, otherwise the spec
  horizon), target_price and entry_at in the sleeve state file.

## Exit rules
- Stop (only where the spec sets stop_pct): a position whose
  current price is at or below avg_price * (1 - stop_pct) is
  sold in full, reason <sleeve>_stop15.
- Target: otherwise, a position whose current price reaches
  the target_price stored at entry is sold in full.
- Time: otherwise, a position held for at least the stored
  horizon_sessions (or the spec horizon when no stored value
  exists) is sold in full. Sessions held are counted from
  session_dates when supplied, else from SPY bar dates, else
  business days.
- No partial or target_pct exit applies to this sleeve (its
  spec sets neither partial_pct nor target_pct). Exits are
  market, day, sell, in full.

## Data inputs
Declared inputs: lazarus_fires, bars, positions.
