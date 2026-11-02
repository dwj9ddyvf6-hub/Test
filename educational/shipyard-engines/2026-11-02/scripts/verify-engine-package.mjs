import { createHash } from 'node:crypto';
import { readFile, readdir, lstat } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const EXPECTED_PATHS = [
  'ENGINE-CATALOG.json',
  'LICENSE-INVENTORY.md',
  'README.md',
  'SOURCE-MANIFEST.json',
  'components/bullflow-activity.mjs',
  'components/confluence.mjs',
  'components/daily-change-alerts.mjs',
  'components/finviz-filter.mjs',
  'components/portfolio.mjs',
  'components/shared/csv.mjs',
  'components/shared/input-validation.mjs',
  'components/static-gex.mjs',
  'components/stockrover-factors.mjs',
  'components/strategy-sma.mjs',
  'dist/forecast-engine-catalog.mjs',
  'dist/forecast-engines.mjs',
  'package.json',
  'python/rre/__init__.py',
  'python/rre/raschke_core.py',
  'python/rre/raschke_engine.py',
  'python/saty/saty_reference.py',
  'python/saty/saty_system/__init__.py',
  'python/saty/saty_system/models.py',
  'python/saty/saty_system/routing.py',
  'python/saty/saty_system/strategies.py',
  'python/saty/saty_system/structure.py',
  'research/chartslector/adapter.mjs',
  'research/lector-chart-math/engine.mjs',
  'scripts/build_forecast_parity_vectors.py',
  'scripts/verify-engine-package.mjs',
  'tests/chartslector-synthetic.test.mjs',
  'tests/fixtures/canonical-forecast-scorers.py',
  'tests/fixtures/forecast-engine-expanded-golden.json',
  'tests/fixtures/forecast-engine-golden.json',
  'tests/forecast-engines.test.mjs',
  'tests/lector-chart-math.test.mjs',
  'tests/math-labs.test.mjs',
  'tests/test_rre_kernels.py',
  'tests/test_saty_kernels.py'
].sort();

function sha256(bytes) { return createHash('sha256').update(bytes).digest('hex'); }
function fail(message) { throw new Error(message); }

async function walk(dir, prefix='') {
  const files=[];
  for (const entry of await readdir(dir, {withFileTypes:true})) {
    const rel=prefix ? `${prefix}/${entry.name}` : entry.name;
    const absolute=path.join(dir, entry.name);
    const stat=await lstat(absolute);
    if (entry.isSymbolicLink() || stat.isSymbolicLink()) fail(`symlink rejected: ${rel}`);
    if (entry.isDirectory()) files.push(...await walk(absolute, rel));
    else if (entry.isFile() && stat.isFile()) files.push(rel);
    else fail(`non-regular package entry rejected: ${rel}`);
  }
  return files;
}

const actual=(await walk(ROOT)).sort();
if (JSON.stringify(actual)!==JSON.stringify(EXPECTED_PATHS)) {
  const missing=EXPECTED_PATHS.filter(x=>!actual.includes(x));
  const extra=actual.filter(x=>!EXPECTED_PATHS.includes(x));
  fail(`exact path set mismatch; missing=${JSON.stringify(missing)} extra=${JSON.stringify(extra)}`);
}

const expectedDirs=new Set();
for (const item of EXPECTED_PATHS) {
  let current=path.posix.dirname(item);
  while (current!=='.') { expectedDirs.add(current); current=path.posix.dirname(current); }
}
async function collectDirs(dir, prefix='') {
  const out=[];
  for (const entry of await readdir(dir,{withFileTypes:true})) {
    if (!entry.isDirectory()) continue;
    const rel=prefix?`${prefix}/${entry.name}`:entry.name;
    out.push(rel,...await collectDirs(path.join(dir,entry.name),rel));
  }
  return out;
}
const dirs=(await collectDirs(ROOT)).sort();
if (JSON.stringify(dirs)!==JSON.stringify([...expectedDirs].sort())) fail('unexpected empty or missing directory');

const manifest=JSON.parse(await readFile(path.join(ROOT,'SOURCE-MANIFEST.json'),'utf8'));
if (manifest.schema!=='SHIPYARD_ENGINE_ONLY_SOURCE_MANIFEST_V1' || manifest.files.length!==39) fail('source manifest schema/count mismatch');
const manifestPaths=manifest.files.map(x=>x.path).sort();
if (JSON.stringify(manifestPaths)!==JSON.stringify(EXPECTED_PATHS)) fail('manifest paths do not match exact allowlist');
if (manifest.self_hash_policy?.public_representation_sha256!==null || manifest.self_hash_policy?.external_private_inventory!==true) fail('self-hash policy must point to external private control inventory');
for (const entry of manifest.files) {
  const p=entry.path;
  const raw=await readFile(path.join(ROOT,p));
  const stat=await lstat(path.join(ROOT,p));
  if ((stat.mode&0o777)!==0o644) fail(`mode must be 0644: ${p}`);
  if (p==='SOURCE-MANIFEST.json') {
    if (entry.representation_sha256!==null) fail('public source manifest must not self-hash');
    continue;
  }
  if (!/^[0-9a-f]{64}$/.test(entry.representation_sha256||'')) fail(`invalid representation digest: ${p}`);
  if (sha256(raw)!==entry.representation_sha256) fail(`representation digest mismatch: ${p}`);
  if (entry.source_sha256!==null && !/^[0-9a-f]{64}$/.test(entry.source_sha256||'')) fail(`invalid source digest: ${p}`);
}

const pkg=JSON.parse(await readFile(path.join(ROOT,'package.json'),'utf8'));
if (pkg.private!==true || Object.keys(pkg.dependencies||{}).length || Object.keys(pkg.devDependencies||{}).length) fail('package must remain private and dependency-free');
if (pkg.scripts?.test!=='npm run verify && npm run test:js && npm run test:python && npm run test:parity') fail('unexpected test command closure');

const golden=JSON.parse(await readFile(path.join(ROOT,'tests/fixtures/forecast-engine-golden.json'),'utf8'));
const expanded=JSON.parse(await readFile(path.join(ROOT,'tests/fixtures/forecast-engine-expanded-golden.json'),'utf8'));
if (golden.engines?.length!==30 || expanded.vectors?.length!==344) fail('synthetic scorer fixture counts changed');
if (golden.source?.repository!=='__UPSTREAM_REPOSITORY_URL__' || expanded.source?.repository!=='__UPSTREAM_REPOSITORY_URL__') fail('forecast source metadata must remain redacted');
const catalog=await readFile(path.join(ROOT,'dist/forecast-engine-catalog.mjs'),'utf8');
const chartAdapter=await readFile(path.join(ROOT,'research/chartslector/adapter.mjs'),'utf8');
if (!catalog.includes('"repository": "__UPSTREAM_REPOSITORY_URL__"')) fail('forecast catalog redaction placeholder missing');
if (!chartAdapter.includes("repository:'__ARCHIVE_REPOSITORY__'") || !chartAdapter.includes("prefix:'__OWNER_SUPPLIED_ARCHIVE_SUBTREE__'")) fail('ChartsLector metadata-redaction placeholders missing');

// Conservative tripwires for machine-local paths and credential-shaped literals.
// They are a review aid, not a semantic privacy decision; any match is rejected for manual inspection.
const forbiddenPaths=['/workspace'+'/scratch/','/workspace'+'/shared/','/home'+'/agent/','/Us'+'ers/'];
const credentialPatterns=[/-----BEGIN(?: RSA| EC| OPENSSH)? PRIVATE KEY-----/,/\bAKIA[0-9A-Z]{16}\b/,/\bgh[pousr]_[A-Za-z0-9]{20,}\b/,/\bsk-[A-Za-z0-9_-]{20,}\b/];
for (const p of EXPECTED_PATHS) {
  if (p==='scripts/verify-engine-package.mjs') continue; // It necessarily contains the tripwire patterns below.
  const body=(await readFile(path.join(ROOT,p))).toString('utf8');
  if (forbiddenPaths.some(marker=>body.includes(marker))) fail(`machine-local path tripwire: ${p}`);
  if (credentialPatterns.some(pattern=>pattern.test(body))) fail(`credential-shaped literal tripwire: ${p}`);
  if (/\bfetch\s*\(|XMLHttpRequest|axios\s*\(|https?\.request\s*\(/.test(body)) fail(`network-acquisition tripwire: ${p}`);
}

console.log(JSON.stringify({status:'ok',files:actual.length,sha256_self:'externally controlled',scope:'exact offline engine-only candidate'}));
