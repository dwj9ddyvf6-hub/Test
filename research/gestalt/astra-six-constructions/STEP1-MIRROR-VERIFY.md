# Step 1: Mirror and Verify, Astra Six Constructions

SCOPE: Mirror 88 files from cos2-estate at a pinned head, verify against the package MANIFEST.json, reassemble and unpack the data archive, and cross-check byte identity against the master-desk copy. No package code was run. Typed spend $0.00.

## Sources

- Source repo: dwj9ddyvf6-hub/cos2-estate, branch research/six-constructions-20261115, head c2cba0d433823c56cdb3b9680f69c58365a35ab2
- Source subtree: research/brainstorm/six_constructions_2026-11-15/
- Mirror copy repo: dwj9ddyvf6-hub/master-desk, same branch, head 3bc102f26abc0bda30da0e547c4c25e626f09514
- Mirror home: ~/workspace/research_notes/astra-six-constructions-20261115/
- Fetch manifest: FETCH-MANIFEST.json in the mirror home
- Cross-check detail: CROSSCHECK.json in the mirror home

## 1. Mirror

Verdict: GREEN

- Files fetched and written byte-exact: 88 of 88
- Total fetched bytes: 9,455,986
- Layout: package files under six_constructions_2026-11-15/ in the mirror home, with six_constructions_2026-11-15.remote-readback.json beside it
- Per file evidence in FETCH-MANIFEST.json: repo path, local path, byte length, sha256 of fetched bytes, git blob sha computed as sha1 of "blob <len>" plus NUL plus bytes, tree-listed git blob sha, and fetch-returned git blob sha
- Computed git blob sha matched the tree-listed sha for 88 of 88 files
- Computed git blob sha matched the fetch-returned sha for 88 of 88 files
- No missing files

## 2. Verification against the package MANIFEST.json

Verdict: GREEN, with the counting accounting named below

- MANIFEST.json lists 86 payload files, in its field payload_file_count_excluding_manifest: 86
- Listed payload bytes: 9,396,730, matching the sum of the listed entries and the field payload_bytes_excluding_manifest
- Verified against fetched copies: 86 listed files checked, 86 matched on both byte size and sha256, 0 mismatches, 0 missing
- Extra files in the original mirrored package, before archive reassembly: none. The package held 87 files on disk: the 86 listed payload files plus MANIFEST.json itself, which the MANIFEST excludes from its own list by its self note
- Accounting for the 88 total: 86 MANIFEST-listed payload files, plus MANIFEST.json itself as package file 87, plus the sibling readback file as fetched file 88. The readback file itself states its scope as 87 package files per repository
- Conclusion on the 88 of 88 claim: confirmed under that accounting. All 88 fetched files are verified, by git blob sha in Step 1 and, for the 86 payload files, also by the MANIFEST sha256 and size list in this step. The MANIFEST list on its own covers 86 files, not 88

## 3. Data archive reassembly and unpack

Verdict: GREEN

- Manifest checked: six_constructions_2026-11-15/data_archive/manifest.json
- Parts verified: 4 of 4 parts matched their stated byte size and sha256
  - market-data.tar.gz.part-001: 2,097,152 bytes, sha256 12348c7787a3d7c3dab9e4dd7d980f09c7932948fb51436f63eb273e46337d1e
  - market-data.tar.gz.part-002: 2,097,152 bytes, sha256 c88b84e5652ecd7f09bc0a7eaaeb634186fe4879ba07cf1ed81e9b49ad75ba6b
  - market-data.tar.gz.part-003: 2,097,152 bytes, sha256 913a2d1d1a2be9b5dbf7d9ab9f1365b5171232277e16f942d58bddae4ed67d14
  - market-data.tar.gz.part-004: 1,095,519 bytes, sha256 6bcfccdb8baf7466f267453cb27c5e342ec315b15e676f92887fe5e3e0bb3555
- Reassembled file: six_constructions_2026-11-15/data_archive/market-data.tar.gz
- Reassembled size: 7,386,975 bytes, matching archive_bytes in data_archive/manifest.json
- Reassembled sha256: 3b7c7f70b68cad0ed3cd41e27e3c0178f71230be4943fa080802bb3d24563713, matching archive_sha256 in data_archive/manifest.json
- Unpacked locations: six_constructions_2026-11-15/data_archive/unpacked/ and, per the literal instruction wording, data_archive/unpacked/ in the mirror home, with identical contents
- Unpacked file count: 799 files
- Unpacked total size: 7,638,507 bytes
- Internal archive list check: data_archive/manifest.json lists 799 files inside the archive; 799 matched on byte size and sha256, 0 mismatches, 0 missing
- Archive contents summary, top level of the unpacked tree:
  - binance/: 634 files, 6,661,084 bytes
  - perp_history/: 165 files, 977,423 bytes

## 4. Cross-check against master-desk

Verdict: GREEN on content identity. One named divergence on repo path, recorded below, with no content divergence.

- Files compared byte for byte by sha256: 88
  - 86 MANIFEST-listed payload files
  - plus MANIFEST.json itself
  - plus the sibling readback file
- Files identical: 88 of 88
- Files divergent: 0
- Files missing in one repo subtree but present in the other: 0. Tree listings for both repos gave 88 blobs under their respective prefixes, with identical relative file sets and identical git blob shas by relative path
- Full per file hashes for both copies: CROSSCHECK.json in the mirror home

Named divergence, path only, not content:

- The brief described the master-desk copy as living at the same subtree paths as the source. That literal path claim is refuted by the tree listings.
- Source prefix in cos2-estate: research/brainstorm/six_constructions_2026-11-15/, with the readback at research/brainstorm/six_constructions_2026-11-15.remote-readback.json
- Actual prefix in master-desk: research/six-constructions/2026-11-15/, with the readback at research/six-constructions/2026-11-15.remote-readback.json
- Example: the readback file has git blob sha 8082391a0d05ea5ed8b8c41164941f3d2f109f03 in both repos, at the two different paths above
- The cross-check above was therefore run using the master-desk actual prefix, mapped by relative path. Content identity holds across that mapping

## Overall Step 1 verdict

GREEN on mirror, MANIFEST verification, archive verification, and cross-repo content identity, with one named open note carried forward: the two repos use different subtree prefixes, listed in Step 4, so any later step must use each repo's actual prefix and not assume identical repo paths.

STATUS: GREEN, evidence in FETCH-MANIFEST.json, CROSSCHECK.json, and this file in the mirror home, all read back from the final mirrored artifacts after the last fetch. No package code was run in this step.
