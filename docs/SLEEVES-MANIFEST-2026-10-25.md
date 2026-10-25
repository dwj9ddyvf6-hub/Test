# Sleeves Manifest — Week of Oct 19–25, 2026

Target repo: dwj9ddyvf6-hub/Test (branch main)
Week: 2026-10-19/2026-10-25
muse-desk-v3 head: 6c503bf3444f39dcc743568e21fc74a2caac5621
Total sleeves: 313
By book: {"aster": 155, "femto": 1, "lazarus": 75, "main": 82}
Adapters: 292

## Layout in this repo
- Per-sleeve strategy files: `sleeves/…` (aster under `sleeves/aster/`, lazarus under `sleeves/lazarus/`, femto under `sleeves/femto/`)
- Per-sleeve v3 adapter/wrapper files: `integration/<id>_adapter.py`
- Shared engines (saved once, imported by the adapters): `desk3/…`
- v3 roster config: `docs/v3-sleeves-config-2026-10-25.json`
- This manifest: `docs/SLEEVES-MANIFEST-2026-10-25.json` (+ this .md)

## Notes
- bb_rsi_divergence: the original v2.2 file stays at `sleeves/bb_rsi_divergence.py`; the desk expanded version is saved as `sleeves/bb_rsi_divergence_expanded.py` (never overwrite an origin file under the same name).
- trullas_divergence strategy was already saved at `sleeves/trullas_divergence.py` (identical blob, skipped). Its manifest adapter path `integration/trullas_divergence_adapter.py` already holds the adapters/ plumbing version from the earlier save with a different blob, so the adapters3 wrapper was NOT overwritten over it (never-overwrite rule); see the save report.

## Chunk commits
- 9267eeb5000565e58101dec5097d2dc3b762ddf3
- 57b7735e22f0df943f54b6e6547f05897368524e
- 868ac38ae3e86ad08cf205b0053f3018edf556dc
- e9be66b39810cfd9664b4fc9b7262bf98b24d331
- a0cb7113b5b09faafc172ca756ca1270fd770416
- c7fc028878143d89cc990b80b8bf99246c08ddd4

Full machine-readable manifest: `docs/SLEEVES-MANIFEST-2026-10-25.json`.
