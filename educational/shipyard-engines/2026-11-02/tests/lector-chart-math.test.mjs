import test from 'node:test';
import assert from 'node:assert/strict';
import { analyzeElliottWave, explainChart, buildPatternHistory } from '../research/lector-chart-math/engine.mjs';

function fixtureBars(count=140, {missingVolumeAt=-1, wavy=false}={}) {
  const rows=[];
  const origin=Date.parse('2024-01-02T14:30:00Z');
  for (let i=0;i<count;i++) {
    const close=100+(wavy?Math.sin(i*Math.PI/4)*2:i);
    const open=close;
    const high=Math.max(open,close)+1;
    const low=Math.min(open,close)-1;
    rows.push([new Date(origin+i*300_000).toISOString(),open,high,low,close,i===missingVolumeAt?null:1000+(i%20)*10]);
  }
  return rows;
}
function chart(bars) {
  const last=bars.at(-1)[0];
  const observed=new Date(Date.parse(last)+300_000).toISOString();
  return {symbol:'SYN',interval:'5m',source:'caller-fixture',adjustment:'raw',bars,
    observed_at:observed,received_at:observed,last_completed_at:observed};
}
function nowAfter(input) { return new Date(Date.parse(input.observed_at)+60_000).toISOString(); }
function emaSmaSeed(values, period) {
  const result=Array(values.length).fill(null), alpha=2/(period+1);
  if(values.length<period)return result;
  let value=values.slice(0,period).reduce((a,b)=>a+b,0)/period;
  result[period-1]=value;
  for(let i=period;i<values.length;i++){value=alpha*values[i]+(1-alpha)*value;result[i]=value;}
  return result;
}

test('chart subset gives known-answer SMA, RSI, seeded EMA/MACD and causal pivot clocks', () => {
  const bars=fixtureBars(140,{wavy:true});
  // Use a monotone series for exact indicator boundaries and a wavy one for pivots.
  const monotone=chart(fixtureBars(140));
  const result=explainChart(monotone, nowAfter(monotone));
  const closes=monotone.bars.map(row=>row[4]);
  assert.equal(result.metrics.sma10, closes.slice(-10).reduce((a,b)=>a+b,0)/10);
  assert.equal(result.metrics.rsi14, 100);
  const fast=emaSmaSeed(closes,12), slow=emaSmaSeed(closes,26);
  const line=closes.map((_,i)=>fast[i]===null||slow[i]===null?null:fast[i]-slow[i]);
  const firstMacd=line.findIndex(x=>x!==null);
  const signal=emaSmaSeed(line.slice(firstMacd),9);
  assert.equal(firstMacd,25);
  assert.equal(result.indicators.macd.at(-1),line.at(-1));
  assert.equal(result.indicators.macd_signal.at(-1),signal.at(-1));
  assert.ok(result.pivots.every(p=>p.confirmation_bar_at<=monotone.last_completed_at));
  assert.equal(result.elliott.input_bar_count,140);
  assert.notEqual(result.elliott.status,'unavailable');
  const wavyChart=chart(bars);
  const wavyResult=explainChart(wavyChart,nowAfter(wavyChart));
  assert.ok(wavyResult.pivots.length>0,'wavy synthetic bars produce confirmed pivots');
  assert.ok(wavyResult.pivots.every(p=>p.confirmation_index<wavyChart.bars.length));
  const waves=analyzeElliottWave(wavyChart,nowAfter(wavyChart));
  assert.equal(waves.input_bar_count,140);
  assert.notEqual(waves.status,'unavailable');
  for(const count of [...waves.counts,...(waves.preferred?[waves.preferred]:[]),...(waves.alternate?[waves.alternate]:[])]) {
    assert.ok(count.pivots.every(p=>p.confirmed_at<=monotone.last_completed_at));
  }
});

test('missing volume stays unknown and pattern analog outcomes do not overlap', () => {
  const bars=fixtureBars(360,{missingVolumeAt:359,wavy:true});
  const chartBars=bars.slice(0,260);
  chartBars[259]=[...chartBars[259]]; chartBars[259][5]=null;
  const input=chart(chartBars);
  const result=explainChart(input,nowAfter(input));
  assert.equal(result.metrics.relative_volume,null);
  assert.equal(result.extended_status,'available');
  const history=buildPatternHistory({symbol:'SYN',interval:'5m',source:'caller-fixture',adjustment:'raw',bars});
  assert.equal(history.orders,false);
  assert.equal(history.history_bars,360);
  assert.ok(history.horizons.some(h=>h.matches.length>0),'repeated synthetic cycle yields known-neighbor matches');
  for(const horizon of history.horizons) {
    const indexes=horizon.matches.map(match=>bars.findIndex(row=>row[0]===match.origin));
    assert.equal(indexes.length,horizon.matches.length);
    assert.ok(horizon.matches.every(match=>match.distance<=0.65));
    for(let i=0;i<indexes.length;i++)for(let j=i+1;j<indexes.length;j++)
      assert.ok(Math.abs(indexes[i]-indexes[j])>horizon.bars,'selected outcomes are non-overlapping');
  }
  const short=buildPatternHistory({bars:bars.slice(0,109)});
  assert.equal(short.reason,'history_shorter_than_110_completed_bars');
});

test('chart and Elliott adapters reject invalid completion clocks and malformed OHLC', () => {
  const input=chart(fixtureBars(80));
  const stale=explainChart(input,'2024-01-02T14:30:00Z');
  assert.equal(stale.reason,'invalid_completion_or_receipt_clock');
  assert.equal(analyzeElliottWave(input,'2024-01-02T14:30:00Z').reason,'invalid_completion_or_receipt_clock');
  const broken=chart(fixtureBars(80));
  broken.bars[10]=[...broken.bars[10]];
  broken.bars[10][2]=broken.bars[10][3]-1;
  assert.equal(explainChart(broken,nowAfter(broken)).reason,'invalid_bar');
  assert.equal(analyzeElliottWave(broken,nowAfter(broken)).reason,'invalid_bar');
  const unordered=fixtureBars(120);
  unordered[61]=unordered[60];
  assert.equal(buildPatternHistory({bars:unordered}).reason,'invalid_or_unordered_bars');
});
