# proof/: what lives here

Install proof records: one JSON receipt per installed sleeve under proof/install/.

Exact file count, byte total and captured revision: [the generated repository index](../INDEX.md). The matching entries in [INDEX.json](../INDEX.json) retain every path and blob hash.

Everything here lives under proof/install/ (22 JSON receipts, one per installed sleeve). There are no files at the top of proof/ itself besides this entry doc.

## Where its index lives

- Every file in this area is listed, with size and blob sha, in the root INDEX.json (search it by the path prefix `proof/`).
- The prose map is the root INDEX.md; the mandatory first read is the root START-HERE.md; routing by topic is the root ROADMAP.md.
