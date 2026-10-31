import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {buildLiveDiscoveryView as original} from '../research/live-aperture/lib/live-scan-engine.ts';
import vm from 'node:vm';
import {execFileSync} from 'node:child_process';
const code=execFileSync('node',['scripts/build-live-research.mjs'],{encoding:'utf8',maxBuffer:5000000});
const ctx={TextEncoder,Uint8Array,Uint32Array,DataView,ArrayBuffer,Date,Intl};vm.createContext(ctx);vm.runInContext(code,ctx);
const bundled=input=>JSON.parse(JSON.stringify(ctx.SHIPYARD_LIVE_RESEARCH.buildLiveDiscoveryView(input)));
import {prepareInput} from '../research/live-aperture/research-adapter.mjs';
const root=new URL('../research/live-aperture/',import.meta.url);
const fixture=JSON.parse(await readFile(new URL('synthetic-fixture.json',root)));
const input=prepareInput(fixture);
const expected=original(input), actual=bundled(input);
assert.deepEqual(actual,expected,'Full original/bundled engine output must match');
assert.equal(createHash('sha256').update(JSON.stringify(actual)).digest('hex'),'94f0c4195451783459c33e5aa1778f7144af9029087a6a5ca3b84e632135d8a1');
let count=1;
for(const freshness of ['LIVE','BASELINE','LAGGING','STALE','CLOSED','WARMING','OFFLINE']) {
  for(const session of ['REGULAR','PREMARKET','AFTERHOURS','CLOSED']) {
    const variant=structuredClone(input); variant.freshness=freshness;variant.session=session;
    assert.deepEqual(bundled(variant),original(variant));count++;
  }
}
for(const mode of ['missing-benchmark','missing-current','insufficient-daily','unicode']) {
  const variant=structuredClone(input);
  if(mode==='missing-benchmark') variant.symbols=variant.symbols.slice(0,1);
  if(mode==='missing-current') variant.symbols[1].intraday.pop();
  if(mode==='insufficient-daily') variant.symbols[0].daily=variant.symbols[0].daily.slice(0,79);
  if(mode==='unicode') variant.symbols[0].company='Unicode 测试 🚀 é';
  assert.deepEqual(bundled(variant),original(variant));count++;
}
const bundle=code;
assert.ok(!/from\s+["']node:|require\(|\bfetch\(|WebSocket/.test(bundle));
console.log(`PASS: ${count} full-output original/browser parity cases; frozen golden SHA; no Node imports/network references`);
