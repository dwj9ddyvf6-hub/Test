"""Data lanes of the Morgue Engine: point-in-time stores that accrue one file a session (REA work package 5).

  chain_archive   L2  the daily option chain (open interest, volume, IV, gamma per contract) of SPY, QQQ, IWM
  finra_shortvol  B52 FINRA's per-name daily short-sale volume, the history DEEP studies need
  sec_facts       L1  SEC companyfacts as (concept, period end, filed date) facts, read as of a decision date

Each lane writes under state/morgue/ with an atomic replace, never overwrites a stored day, and rotates by age. Reads go
through the desk's data layer (desk/data/http.py: one User-Agent, the per-host pace, the refusal breaker) by way of
desk/morgue/fetch.py, and every function that reads takes a `getter` so a test serves fixtures and no network is touched."""
