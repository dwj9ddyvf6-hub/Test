"""Concatenate pinned, pure original functions; no minification or logic rewrites."""
from pathlib import Path
import json,hashlib
p=Path(__file__).parent
for entry in json.loads((p/'SOURCE_MANIFEST.json').read_text(encoding='utf-8'))['files']:
    source_bytes=(p/entry['path']).read_bytes().replace(b'\r\n',b'\n')
    assert hashlib.sha256(source_bytes).hexdigest()==entry['sha256'], 'Original source changed: '+entry['path']
files=['worker/elliott-wave.js','worker/technicals.js','worker/setup-factor-checks.js','worker/pattern-history.js','dist/setup-plan.js','worker/setup-clock-helpers.extracted.js','worker/desk-read.js']
s='import {tensorV698Frame} from "./worker/tensor-v698/index.mjs";\n'
for f in files:
 t=(p/f).read_text(encoding='utf-8')
 if f=='worker/desk-read.js':t=t.replace('__DESK_GESTALT_REGISTRY__',(p/'worker/gestalt-registry.json').read_text(encoding='utf-8'))
 s+='\n// Original: '+f+'\n'+t+'\n'
# Keep the original score engine hash-pinned. Inject the live source-clock
# adapter immediately before direction resolution so abstentions cannot vote.
hook='  const directionResolution=deskResolveDirection(row,factorChecks,{readFresh,held,pending})'
if s.count(hook)!=1: raise RuntimeError('Lector volume-clock adapter hook not unique')
s=s.replace(hook,'  factorChecks=deskDailyVolumeClockAbstention(row,factorChecks);\n'+hook,1)
s+='\n// Isolated source-clock adapter; original scorer sources remain unchanged.\n'+(p/'volume-clock-adapter.js').read_text(encoding='utf-8')+'\n'
s+='\nexport {explainChart,buildDeskRead,setupFactorChecks,DESK_READ_METHOD};\n'
(p/'engine.mjs').write_text(s,encoding='utf-8',newline='\n')
