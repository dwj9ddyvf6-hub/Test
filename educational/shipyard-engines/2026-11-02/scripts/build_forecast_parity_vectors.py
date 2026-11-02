#!/usr/bin/env python3
"""Synthetic conformance vectors, not market inputs or predictive evidence."""
import hashlib, importlib.util, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'tests/fixtures/canonical-forecast-scorers.py'
EXPECTED='d3ac0ae48893fd1175277617d2fe0707e4866f15'
# Compare canonical Git text bytes on Windows as well as POSIX; checkout
# autocrlf must not look like a change to the pinned scorer fixture.
b=SOURCE.read_bytes().replace(b'\r\n',b'\n')
if hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()!=EXPECTED:
    raise SystemExit('Pinned canonical scorer bytes changed')
text=(ROOT/'dist/forecast-engine-catalog.mjs').read_text()
prefix='export const FORECAST_ENGINE_CATALOG = Object.freeze('
catalog=json.loads(text[text.index(prefix)+len(prefix):text.rindex(');')])
golden=json.loads((ROOT/'tests/fixtures/forecast-engine-golden.json').read_text())
if golden['source']['commit']!='f88c874656857841ba1d52c988b8210095949608':
    raise SystemExit('Source pin changed; re-review canonical fixture')
spec=importlib.util.spec_from_file_location('forecast_canonical_pinned',SOURCE)
module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
vectors=[]
for engine in catalog:
    inputs=engine['inputs']
    base={i['name']:(sum(i['value_range'])/2 if i.get('value_range') else 0.0) for i in inputs}
    cases=[('midpoint',base)]
    for i in inputs:
        low,high=i.get('value_range') or (-3.0,3.0)
        for label,value in [('low',low),('high',high)]:
            cases.append((i['name']+'_'+label,{**base,i['name']:value}))
    for label,sign in [('mixed_positive',1),('mixed_negative',-1)]:
        features={}
        for j,i in enumerate(inputs):
            bounds=i.get('value_range')
            features[i['name']]=(bounds[0]+(bounds[1]-bounds[0])*(0.2 if (j+(sign<0))%2 else 0.8)) if bounds else sign*((-1)**j)*(j+1)*0.73
        cases.append((label,features))
    if engine['engine_id']=='FE08':
        for name in base:cases.append(('basis_'+name,{**{k:0.0 for k in base},name:1.0}))
        cases += [('forecast_low_clip',dict(log_rv_1=-100,log_rv_5=-100,log_rv_22=-100,log_rv_baseline=0)),('forecast_high_clip',dict(log_rv_1=100,log_rv_5=100,log_rv_22=100,log_rv_baseline=0)),('baseline_low_clip',dict(log_rv_1=-8,log_rv_5=-6,log_rv_22=-4,log_rv_baseline=-100)),('baseline_high_clip',dict(log_rv_1=-8,log_rv_5=-6,log_rv_22=-4,log_rv_baseline=100))]
    for case,features in cases:
        signal=module.score(engine['formula'],features)
        vectors.append({'engine_id':engine['engine_id'],'case':case,'features':features,'expected':{'value':signal.value,'model_score':signal.model_score,'drivers':dict(signal.drivers)}})
result={'source':golden['source'],'canonical_scorer_git_blob_sha':EXPECTED,'canonical_scorer_sha256':hashlib.sha256(b).hexdigest(),'purpose':'Synthetic algebra and contract conformance only; no live-feature, calibration or financial-edge claim.','vectors':vectors}
output=ROOT/'tests/fixtures/forecast-engine-expanded-golden.json'
encoded=json.dumps(result,indent=2,allow_nan=False)+'\n'
if '--check' in sys.argv:
    if output.read_text()!=encoded:raise SystemExit('Expanded fixture differs from pinned canonical scorer output')
else:output.write_text(encoded)
print(json.dumps({'engines':len(catalog),'vectors':len(vectors),'canonical_git_blob':EXPECTED}))
