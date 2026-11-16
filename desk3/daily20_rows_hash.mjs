// tensor_daily20 anchor-hash packing (TENSOR-DAILY20-PHASE2-20261031):
// reads rows JSON (array of row dicts) from argv[2] and prints
// {rows, csvSha256, packedSha256} using the archive exporter's exact
// encodeRows and Node zlib gzip level 4 (mtime 0) — the receipt
// convention proven in Phase 1 (Python gzip emits a different
// deflate stream; packing must be Node zlib).
import fs from 'node:fs';
import { gzipSync } from 'node:zlib';
import { createHash } from 'node:crypto';
import { encodeRows } from '/home/hatch/workspace/.scratch-ausar-archive/handoff-20261024/source/strategies/tensor_state_repair/engine/scripts/replay_native_features.mjs';
const sha = b => createHash('sha256').update(b).digest('hex');
const rows = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const encoded = encodeRows(rows);
const packed = gzipSync(encoded, { level: 4 });
console.log(JSON.stringify({ rows: rows.length, csvSha256: sha(encoded), packedSha256: sha(packed) }));
