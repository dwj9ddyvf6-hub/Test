"""Record, ledger and AI-tool extensions (REA work package WP4), pure functions with no I/O beyond the append-only decay
log. New files only: nothing here edits the scorer, the ledger or a sleeve.

  stats.py        shared per-date Spearman IC and the plain t over dates
  noise_floor.py  C197  the permutation (shuffled-ghost) noise floor of a forecaster's IC t
  rolling.py      C198  the rolling-start gate and the factor-disguise check
  bench.py        V-vibe-3  alive / reversed / dead / untested buckets from a per-date IC series
  decay.py        V-vibe-2  the decay state machine and its append-only state log
  fan.py          V-tradingkit-1  the stationary-bootstrap uncertainty fan of closed-call R
  tracks.py       V-alertsify-5  overnight-versus-day split and the level track record
  trials.py       V-tradingkit-2  best-of-N label discipline: a rate prints only with its trial count
  audit.py        V-tv-2  tolerance compare of desk RSI / MACD against hand-captured chart values

Every function answers status ok or no_data with a reason; a small sample never yields a number."""
