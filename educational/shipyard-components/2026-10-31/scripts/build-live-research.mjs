import {build} from 'esbuild';
import {execFileSync} from 'node:child_process';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import path from 'node:path';
execFileSync(process.env.SHIPYARD_PYTHON || process.env.PYTHON || (process.platform === 'win32' ? 'python' : 'python3'),['research/live-lector/build_bundle.py']);
const root='research/live-aperture';
const canonicalSourceBytes = (path) => Buffer.from(readFileSync(path).toString('utf8').replace(/\r\n/g,'\n'));
for(const f of JSON.parse(readFileSync(root+'/SOURCE_MANIFEST.json','utf8')).files) {
 if(createHash('sha256').update(canonicalSourceBytes(root+'/'+f.path)).digest('hex')!==f.sha256)throw Error('Original Aperture source changed: '+f.path);
}
if(JSON.parse(readFileSync('node_modules/@noble/hashes/package.json','utf8')).version!=='2.4.0')throw Error('Unexpected SHA256 dependency version');
const result=await build({stdin:{contents:`export {runLector,prepareDailyVolumeChart,classifyDailyVolumeInterval,VOLUME_CLOCK_ADAPTER} from './research/live-lector/run.mjs';
export {buildLiveDiscoveryView} from './research/live-aperture/lib/live-scan-engine.ts';
export {APERTURE_EQUITY_SYMBOLS} from './research/live-aperture/lib/aperture-universe.ts';
export {isScannerEligible,classifyRunnerFreshness} from './research/live-aperture/services/aperture-runner/src/coverage.ts';`,resolveDir:process.cwd(),sourcefile:'live-research-entry.mjs'},bundle:true,write:false,format:'iife',globalName:'SHIPYARD_LIVE_RESEARCH',platform:'browser',target:'es2022',alias:{'node:crypto':path.resolve(root,'crypto-shim.mjs')},logLevel:'silent'});
process.stdout.write(result.outputFiles[0].text);
