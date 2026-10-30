# Release 0.4.1 — operational audit corrections

All 70 offline engineering tests pass, including new regressions for each independently reported 0.4.0 defect.

Health selects the latest eligible observation revision using snapshot-equivalent keys, ordering and availability clocks before testing value, access and freshness. A latest null/withdrawn revision invalidates the earlier usable value; a future revision does not affect prior health cutoffs.

Receipt import rejects event/completion or publication timestamps later than the supplied upstream capture, even when local import is later. Invalid batches add no observations. The supplied real Wikimedia receipt remains valid.

SQLite backups create new destination files with O_CREAT|O_EXCL and mode 0600. Existing destination bytes and permissions remain unchanged. No host/global security settings are modified.
