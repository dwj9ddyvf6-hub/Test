import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { pathToFileURL } from 'node:url';
const raw=await readFile(new URL('../worker/psychology.js',import.meta.url),'utf8');
const source=raw+'\nexport { shipyardPsychologyScoreHeadline, shipyardPsychologyIsoMillis, shipyardPsychologyDerive };';
const mod=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
test('psychology bridge exposes transparent lexicon calculation, strict clocks, and content-free derived output',async()=>{
 assert.equal(mod.shipyardPsychologyScoreHeadline('Strong growth, but not bullish.').sentiment,1/3);
 assert.equal(mod.shipyardPsychologyIsoMillis('2026-02-30T00:00:00Z'),null);
 const computed='2026-10-30T12:00:00.000Z',created='2026-10-30T11:59:00.000Z';
 const news={schema:'SHIPYARD_ALPACA_NEWS_V1',status:'connected',retrieved_at:computed,served_at:computed,articles:[{id:1,headline:'Strong growth headline',summary:'private payload',content:'must not leak',author:'private',source:'Synthetic',url:'https://example.test',created_at:created,updated_at:created,symbols:['SPY']}]};
 const result=await mod.shipyardPsychologyDerive(news,{firstSeenAt:computed,computedAt:computed});assert.equal(result.status,'available_advisory');assert.equal(result.authority.order_submission_enabled,false);assert.equal(result.quality.raw_text_in_output,false);assert.equal(JSON.stringify(result).includes('must not leak'),false);assert.equal(JSON.stringify(result).includes('private payload'),false);
});
