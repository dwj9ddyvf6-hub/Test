# Backup Sync (sync_backup.py) Algorithm

Created by GrokBot.

Algorithm derived from the code on 2026-10-29 (source: dwj9ddyvf6-hub/quant-research-backup, main, backup/sync_backup.py).

## What it is
The strictly-additive backup sync for the GrokBot box: an incremental backup of the research folders to the private quant-research-backup repo, rebuilt after the 2026-10-05 inbox wipes so the sync class that caused them cannot recur.

## Rules implemented in the code
- Additive only: the pushed commit may only add or modify files. Any deletion versus its parent undoes the commit and refuses the push (the _additive_push guard).
- Fetch and re-align first: before committing, the local main is re-aligned to the freshly fetched origin/main, so files another party pushed meanwhile are in the index and are not committed as deletions.
- Staged-deletion guard: if any deletions are still staged at commit time, the sync refuses to commit or push, and a protected-path guard ensures nothing under grokbot-inbox/ is staged by the sync.
- Change safety: a source file that changes while it is being scanned or staged aborts the sync before commit rather than backing up a torn copy.
- Exclusions: caches and environments that can be recreated, nested .git directories, credential and secret-pattern files, purged images, and rebuildable cache files are skipped; large files are split into parts and reassembled on restore.

## Files in this package
- packages/grokbot/backup-sync/backup/sync_backup.py
- docs/BACKUP-SYNC-ALGORITHM.md (this file)

## Sanitization note
This copy was sanitized at 42 point(s) to pass the public-repo privacy gate; the private original in the source repo named in this doc is the verbatim source.
Sanitized files in this package:
- packages/grokbot/backup-sync/backup/sync_backup.py: 42 occurrence(s) replaced
