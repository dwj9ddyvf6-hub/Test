# Vintage archive store schema (CB-20 Lag Detector)

One directory per capture date (America/New_York), named
YYYY-MM-DD. A capture never overwrites an earlier date's directory.
Re-running the capture on the same date refreshes that date's
directory only, and the manifest records rerun_same_date true.

Each capture directory holds:

- manifest.json: capture timestamps (ET and UTC), and per file:
  kind, source route, as-of period the file describes, row count,
  byte size, sha256. The manifest is the read-back proof: a file
  counts as archived only when its recomputed sha256 matches the
  manifest.
- finra_ats_weekly_YYYY-MM-DD.json: the FINRA ATS weekly file for
  the latest published week as of the capture, all rows exactly as
  the public API served them (weekStartDate in the filename is the
  as-of week the file describes, not the capture date).
- finra_ats_weekly_YYYY-MM-DD.json.gz: in a full capture (--full),
  every other weekly file the route currently publishes, one
  gzipped file per week, same as-published rule. Route range as
  discovered 2026-11-15: first published week 2021-12-06, latest
  2026-10-19. The manifest's full_archive section lists every
  week with its row count and hash.
- short_interest_pit_snapshot.jsonl: byte copy of the held morgue
  PIT short-interest file as it stands at capture time. Named gap:
  no public no-credential live short-interest route exists on this
  estate (the FINRA API equity shortInterest dataset answers 401
  without FINRA API credentials, probed 2026-11-15), so the SI
  vintage series accrues as snapshots of the held file until a
  live route lands.

Writer: keepgoing2/wave7/w7c_vintage_capture.py, run daily by cron
w7-vintage-capture-daily. Readers must treat every directory as
immutable once a later capture date exists.
