# Forward lab accounts (Tensor scan)

$20,000 accounts, each buying Tensor Cyan or Green fires that pass its frozen filter, and holding each for its rule's horizon.

| | |
|---|---|
| **Family** | Midna |
| **Source** | Midna's TypeScript desk (equity books), ported line for line to the master desk |
| **Asset** | US equities |
| **Timeframe** | 1d · 1w |
| **Universe** | Midna's daily panel |
| **Style** | Tensor signal + filters |
| **Status** | 5 waiting |

## Entry

- Rules: weekly Cyan with dollar-volume, breadth or VIX limits; daily Green $10-20 with dispersion and gap-age limits; weekly Green with skew, SMH-SPY and no FOMC in 5 sessions.
- Up to 6 hits per account, best score first; entry from 10:00 ET on the session after the signal.

## Exit

- Sells once the hold (21, 126 or 252 sessions) is reached.

## Sizing

- qty = floor((20,000 / 6) / (price × (1 + cost))), capped by cash.

## Data

- Midna's daily panel, the Tensor engine and the frozen v4 GBM.

## Variants

| Account (row) | Rule | Hold |
|---|---|---|
| w-cyan-breadth (`midna_w_cyan_quiet_tape`; Lazarus lane `midna_w_cyan_breadth`) | dv ≤ 6.92, slow state 2, breadth ≥ 0.037 | 126 |
| w-cyan-vix (`midna_w_cyan_mid_vix`) | dv ≤ 7.36, 126d ≥ 44.1%, VIX 13.71-26.38 | 252 |
| d-green-band (`midna_d_green_band`) | $10-20, dispersion 0.021-0.029, gap age 32-252 | 21 |
| w-green-smh (`midna_w_green_calm_smh`) | skew -0.68..0.472, SMH-SPY -0.049..0.097, no FOMC | 126 |

Rows: 5 on the master desk, 4 on Midna's desk (ids in `docs/CATALOG.json`).

## Code

- **Midna v3**: `desk3/lazarus_midna.py`. Fire consumer for d_green_band, w_cyan_vix, w_green_smh, w_cyan_breadth; the rules run upstream
- **Master desk**: `sleeves/midna/forward.py`, `sleeves/midna/forward_scan.py`, `sleeves/midna/lanes.py`
- **Rule lines**: [docs/verify/midna.md](../../docs/verify/midna.md)

## Notes

- The lab's other two accounts, gbm-1d-cyan (`midna_d_cyan_gbm`) and w-cyan-adx (`midna_w_cyan_high_adx`), run the same rules as Femto's Daily Cyan GBM and weekly Cyan momentum ADX and are carded there.
- The master desk drops Midna's desk-wide red-day buy gate (QQQ red, VIX up and the name red) and her desk halt.
