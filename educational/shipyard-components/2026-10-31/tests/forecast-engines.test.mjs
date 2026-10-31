import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { evaluateForecastEngine, listForecastEngines } from '../dist/forecast-engines.mjs';
import { SILICON_FORECAST_SOURCE } from '../dist/forecast-engine-catalog.mjs';

const golden = JSON.parse(await readFile(new URL('./fixtures/forecast-engine-golden.json', import.meta.url), 'utf8'));

function close(actual, expected, path) {
  assert.equal(typeof actual, 'number', `${path} should be numeric`);
  assert.ok(Math.abs(actual - expected) <= 1e-12 * Math.max(1, Math.abs(expected)),
    `${path}: expected ${expected}, got ${actual}`);
}

test('catalog contains 30 engines pinned to the golden source commit', () => {
  const catalog = listForecastEngines();
  assert.equal(catalog.length, 30);
  assert.equal(new Set(catalog.map(engine => engine.engine_id)).size, 30);
  assert.equal(golden.engines.length, 30);
  assert.deepEqual(SILICON_FORECAST_SOURCE, golden.source);
});

test('all 30 browser scorer ports match canonical Python golden outputs', () => {
  for (const fixture of golden.engines) {
    const result = evaluateForecastEngine(fixture.engine_id, fixture.features);
    assert.equal(result.status, 'research_only_score', fixture.engine_id);
    assert.equal(result.decision_eligible, false, fixture.engine_id);
    close(result.forecast_value, fixture.expected.value, `${fixture.engine_id}.value`);
    close(result.model_score, fixture.expected.model_score, `${fixture.engine_id}.model_score`);
    assert.deepEqual(Object.keys(result.drivers).sort(), Object.keys(fixture.expected.drivers).sort());
    for (const [name, value] of Object.entries(fixture.expected.drivers)) {
      close(result.drivers[name], value, `${fixture.engine_id}.drivers.${name}`);
    }
  }
});

test('invalid feature contracts fail closed', () => {
  const fixture = golden.engines[0];
  const required = fixture.features;
  const missing = { ...required };
  delete missing[Object.keys(missing)[0]];
  assert.equal(evaluateForecastEngine(fixture.engine_id, missing).status, 'abstained');
  assert.equal(evaluateForecastEngine(fixture.engine_id, { ...required, unexpected: 1 }).status, 'abstained');
  assert.equal(evaluateForecastEngine(fixture.engine_id, { ...required, ret_21d_z: true }).status, 'abstained');
  assert.equal(evaluateForecastEngine(fixture.engine_id, { ...required, ret_21d_z: Number.NaN }).status, 'abstained');
  assert.equal(evaluateForecastEngine(fixture.engine_id, { ...required, ret_21d_z: 1e19 }).status, 'abstained');
  assert.equal(evaluateForecastEngine(fixture.engine_id, { ...required, trend_efficiency: 1.01 }).status, 'abstained');
  assert.equal(evaluateForecastEngine('UNKNOWN', required).status, 'abstained');
  assert.equal(evaluateForecastEngine(fixture.engine_id, null).status, 'abstained');
  assert.equal(evaluateForecastEngine(fixture.engine_id, Object.create(required)).status, 'abstained');
  const accessorValues = { ...required };
  Object.defineProperty(accessorValues, 'ret_21d_z', { get() { throw new Error('getter invoked'); } });
  assert.equal(evaluateForecastEngine(fixture.engine_id, accessorValues).status, 'abstained');
  assert.equal(evaluateForecastEngine(fixture.engine_id, Object.assign(Object.create(null), required)).status, 'research_only_score');
  const symbolValues = { ...required };
  symbolValues[Symbol('extra')] = 1;
  assert.equal(evaluateForecastEngine(fixture.engine_id, symbolValues).status, 'abstained');
  assert.equal(evaluateForecastEngine(fixture.engine_id, new Proxy(required, { getPrototypeOf() { throw new Error('trap'); } })).status, 'abstained');
});

test('catalog metadata is deeply immutable', () => {
  const catalog = listForecastEngines();
  assert.ok(Object.isFrozen(catalog));
  assert.ok(Object.isFrozen(catalog[0]));
  assert.ok(Object.isFrozen(catalog[0].inputs));
  assert.ok(Object.isFrozen(catalog[0].inputs[0]));
  assert.throws(() => { catalog[0].inputs[0].name = 'tampered'; });
  assert.equal(listForecastEngines()[0].inputs[0].name, 'ret_21d_z');
});

test('score outputs retain source provenance and closed decision eligibility', () => {
  for (const fixture of golden.engines) {
    const result = evaluateForecastEngine(fixture.engine_id, fixture.features);
    assert.deepEqual(result.source, golden.source);
    assert.equal(result.input_provenance, 'manual_unverified');
    assert.equal(result.calibrated_probability, null);
    assert.equal(result.decision_eligible, false);
    assert.equal(result.eligibility_blockers.length, 2);
  }
});

const expanded = JSON.parse(await readFile(new URL('./fixtures/forecast-engine-expanded-golden.json',import.meta.url),'utf8'));
test('all30 scorer ports match differentiated pinned Python vectors, not fitted market forecasts',()=>{
 assert.deepEqual(expanded.source,SILICON_FORECAST_SOURCE);assert.equal(new Set(expanded.vectors.map(x=>x.engine_id)).size,30);
 for(const vector of expanded.vectors){const r=evaluateForecastEngine(vector.engine_id,vector.features),name=`${vector.engine_id}/${vector.case}`;assert.equal(r.status,'research_only_score',name);close(r.forecast_value,vector.expected.value,name+'.value');close(r.model_score,vector.expected.model_score,name+'.score');assert.deepEqual(Object.keys(r.drivers).sort(),Object.keys(vector.expected.drivers).sort());for(const [k,v] of Object.entries(vector.expected.drivers))close(r.drivers[k],v,name+'.'+k);assert.equal(r.decision_eligible,false);assert.equal(r.input_provenance,'manual_unverified');}
});
test('FE08 distinct weights, independent baseline and clipping preserve variance units',()=>{
 const zero={log_rv_1:0,log_rv_5:0,log_rv_22:0,log_rv_baseline:0};for(const [name,weight] of [['log_rv_1',0.5],['log_rv_5',0.3],['log_rv_22',0.2]]){const r=evaluateForecastEngine('FE08',{...zero,[name]:1});close(r.model_score,weight,name);close(r.forecast_value,Math.exp(weight),name+'.variance');}
 const original=evaluateForecastEngine('FE08',{log_rv_1:-8,log_rv_5:-6,log_rv_22:-4,log_rv_baseline:-7}),changed=evaluateForecastEngine('FE08',{log_rv_1:-8,log_rv_5:-6,log_rv_22:-4,log_rv_baseline:-3});close(original.forecast_value,changed.forecast_value,'baseline cannot alter forecast');close(original.model_score-changed.model_score,4,'baseline contrast');assert.notEqual(original.forecast_value,Math.sqrt(original.forecast_value));
 const tiny=evaluateForecastEngine('FE08',{log_rv_1:-100,log_rv_5:-100,log_rv_22:-100,log_rv_baseline:0});assert(tiny.forecast_value>0);assert(Math.abs(tiny.forecast_value/Math.exp(-40)-1)<1e-12);
 const huge=evaluateForecastEngine('FE08',{log_rv_1:100,log_rv_5:100,log_rv_22:100,log_rv_baseline:0});assert(Math.abs(huge.forecast_value/Math.exp(10)-1)<1e-12);
});
test('every registered engine rejects each missing or nonfinite feature and respects declared bounds',()=>{
 for(const engine of listForecastEngines()){const fixture=golden.engines.find(x=>x.engine_id===engine.engine_id);for(const input of engine.inputs){const missing={...fixture.features};delete missing[input.name];assert.equal(evaluateForecastEngine(engine.engine_id,missing).status,'abstained');for(const v of [null,true,'1',NaN,Infinity,-Infinity,1e19])assert.equal(evaluateForecastEngine(engine.engine_id,{...fixture.features,[input.name]:v}).status,'abstained',engine.engine_id+'/'+input.name+'/'+v);if(input.value_range){const [lo,hi]=input.value_range,epsilon=Math.max(1e-7,(hi-lo)*1e-7);for(const v of [lo,hi])assert.equal(evaluateForecastEngine(engine.engine_id,{...fixture.features,[input.name]:v}).status,'research_only_score');for(const v of [lo-epsilon,hi+epsilon])assert.equal(evaluateForecastEngine(engine.engine_id,{...fixture.features,[input.name]:v}).status,'abstained');}}}
});
