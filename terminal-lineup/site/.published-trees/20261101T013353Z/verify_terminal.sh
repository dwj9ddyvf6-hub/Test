#!/bin/sh
# Post-refresh verification step for the terminal: provenance coverage,
# then rebuild the content-addressed asset manifest and run the
# served-bytes smoke check against it. Fails loudly (nonzero exit) on
# any gap. Run after any batch of refresh scripts, before calling the
# tree current.
set -e
cd "$(dirname "$0")"
python3 ../forecast/verify_grade_rows.py
python3 stamp_provenance.py
python3 smoke_check.py --write-manifest
python3 smoke_check.py --serve
