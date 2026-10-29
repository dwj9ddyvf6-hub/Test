# Aster sleeve archive (155 sleeves adopted)

Created by Ausar. Packaged into the Test repo on 2026-10-29 (packaging pass).

Origin: local ~/workspace/muse-desk-v3/desk3/aster_*.py (origin archive: dwj9ddyvf6-hub/codex-complete-archive). This item was the partial in the peer index: the code is already present in Test under desk3/ and integration/; only this algorithm doc was owed, and no code files move with it.

## What the archive is

A batch-organized family of Aster sleeve engines: each module carries a set of named sleeves defined by the ASTER-BUILD-MAP / TSV-as-spec rows for its batch, with registry modules (config_rows) for the batches whose engines live elsewhere. The batches span equity options sleeves (PEAD, core reserve, RSI2 recovery, VWAP20 verticals, XSP put-credit), ETF sleeves, and R19 crypto sleeves on 4h bars (ADAUSDT, ENJUSDT, LINKUSDT spot and basis/breakdown/crowding variants, including fixed16 and breakout_base volume arms), plus Tensor value/recovery and timing sleeves, overnight and Donchian55 sleeves in the later batches. Sleeves consume completed bars and emit position intents under the desk sleeve contract; batch files are independent modules so a batch can be adopted or fenced without touching the others.

## Local evidence files (read-only, already represented in Test)

- `desk3/aster_b11_crypto.py` - Aster R19 crypto engine — batch 11 (LINKUSDT fixed16 arms).
- `desk3/aster_b12_crypto.py` - Aster R19 crypto engine — batch 12 (LINKUSDT breakout_base volume arm
- `desk3/aster_b2.py` - Aster batch 2 engine — pead / core_reserve / recovery(RSI2) options sleeves.
- `desk3/aster_b4.py` - Aster batch 4 engine — recovery VWAP20 vertical (x4), XSP put-credit
- `desk3/aster_b5.py` - Aster batch-5 registry: ADAUSDT spot sleeves (ASTER-BUILD-MAP §5).
- `desk3/aster_batch1.py` - Aster batch 1 engine — 10 sleeves (ASTER-BUILD-MAP.md batch 1).
- `desk3/aster_batch11.py` - Aster batch 11 registry (ASTER-BUILD-MAP batch 11, TSV 106-115).
- `desk3/aster_batch12.py` - Aster batch 12 registry (ASTER-BUILD-MAP batch 12, TSV 116-125).
- `desk3/aster_batch13.py` - Aster batch 13 engine (TSV-as-spec; archive staged tree absent on this box).
- `desk3/aster_batch14.py` - Aster batch 14 engine — C1 HOT_RESERVE_25 + G4 x9 (TSV 136-145).
- `desk3/aster_batch15.py` - Aster batch 15 — G4 Tensor green value/recovery (3) + timing (7).
- `desk3/aster_batch16.py` - Aster batch 16 — overnight 5bp, Trader Donchian55, Tensor daily20 x2,
- `desk3/aster_batch3.py` - Aster batch 3 — options recovery (RSI2 vertical, VWAP20 long) +
- `desk3/aster_batch6.py` - Aster batch 6 registry rows. Inputs: bars (4h crypto producer),
- `desk3/aster_batch7.py` - Aster batch 7 engine — R19 crypto ENJUSDT (books 66-75).
- `desk3/aster_batch8.py` - Aster batch 8 engine — TSV 76-85 (ASTER-BUILD-MAP batch 8).
- `desk3/aster_crypto.py` - Aster R19 crypto engine (batch 6). Source: TSV spec (archive staged
- `desk3/aster_etf.py` - Aster ETF sleeves — batch 10 (TSV-as-spec; staged archive absent on this box at build time, see FIDELITY-LEDGE
- `desk3/aster_etf_b9.py` - Aster R19 ETF engine (batch 9) — faithful port of archive

## Files in this package


Source files are verbatim copies from the origin location named above unless a sanitization note appears in this doc.
