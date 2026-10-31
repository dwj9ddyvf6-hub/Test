import {explainChart,buildDeskRead} from './engine.mjs';
export const SOURCE_COMMIT='bfdc165d9d89908bcbc327444ca4628d90e04d8c';
export const SOURCE_VINTAGE='source-sha256:85015f375a99801393edd7ec7fdf3e91385ed5029a2160cada5f4b700146e385';
export const VOLUME_CLOCK_ADAPTER='ny-day-volume-interval-1';
function newYorkDate(value){
 const ms=typeof value==='number'?value:Date.parse(value||'');if(!Number.isFinite(ms))return null;
 const parts=new Intl.DateTimeFormat('en-US',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(new Date(ms));
 const date=Object.fromEntries(parts.map(part=>[part.type,part.value]));return `${date.year}-${date.month}-${date.day}`;
}
export function classifyDailyVolumeInterval(barAt,receivedAt,now=Date.now()){
 const barDate=newYorkDate(barAt),captureDate=newYorkDate(receivedAt),receivedMs=Date.parse(receivedAt||''),validReceipt=Number.isFinite(receivedMs)&&Number.isFinite(now)&&receivedMs<=now;
 const status=barDate&&captureDate&&validReceipt?(captureDate>barDate?'closed_as_observed':'open_at_capture'):'unknown';
 return {status,timezone:'America/New_York',bar_date:barDate,capture_date:captureDate,received_at:typeof receivedAt==='string'?receivedAt:null,
  provider_finality:'unknown',provider_revisions_possible:true,
  basis:'Interval closure is inferred only when the original source receipt is on a later New York civil date than the daily bar date; this is not provider finality.'};
}
export function prepareDailyVolumeChart(chart,now=Date.now()){
 if(!chart||chart.interval!=='1d'||!Array.isArray(chart.bars)||!chart.bars.length)return chart;
 const last=chart.bars.at(-1),clock=classifyDailyVolumeInterval(last?.[0],chart.received_at,now),sourceMissing=last?.[5]===null||last?.[5]===undefined,
  volumeWithheld=clock.status!=='closed_as_observed'||sourceMissing,
  reason=clock.status!=='closed_as_observed'?'interval_not_observed_closed':sourceMissing?'source_volume_missing':null,
  dailyVolumeInterval={...clock,current_bar_volume_withheld:volumeWithheld,withheld_reason:reason};
 const bars=chart.bars.map((bar,index)=>index===chart.bars.length-1&&volumeWithheld?[...bar.slice(0,5),null]:bar);
 return {...chart,bars,source_capture:{...(chart.source_capture||{}),daily_volume_interval:dailyVolumeInterval}};
}
function validate(c,now){
 if(!c || !/^[A-Z][A-Z0-9.\-]{0,14}$/.test(c.symbol||''))throw Error('invalid symbol');
 if(c.interval!=='1d')throw Error('only daily interval supported');
 if(typeof c.source!=='string'||!c.source.trim()||typeof c.adjustment!=='string'||!c.adjustment.trim()||!['iex','sip'].includes(c.feed))throw Error('source, feed and adjustment required');
 for(const k of ['observed_at','received_at','last_completed_at'])if(!Number.isFinite(Date.parse(c[k]))||Date.parse(c[k])>now)throw Error('invalid '+k);
 if(Date.parse(c.last_completed_at)>Date.parse(c.observed_at)||Date.parse(c.observed_at)>Date.parse(c.received_at))throw Error('inconsistent observation/receipt clocks');
 const t=explainChart(c,now);if(t.status==='unavailable')throw Error(t.reason||'invalid chart');return t;
}
export function prepareInput(input){
 const now=Date.parse(input?.now);if(!Number.isFinite(now))throw Error('explicit now required');
 const primary=prepareDailyVolumeChart(input.primary,now),benchmark=input.benchmark?prepareDailyVolumeChart(input.benchmark,now):null;
 const technicals=validate(primary,now);
 if(benchmark){validate(benchmark,now);if(benchmark.symbol!=='SPY'||benchmark.source!==primary.source||benchmark.feed!==primary.feed||benchmark.adjustment!==primary.adjustment)throw Error('SPY must match source/feed/adjustment');}
 // Neutral is absence of an external strategy direction, not a directional forecast.
 // Original deskResolveDirection derives the on-demand assessment from original factors.
 const row={id:'research-'+primary.symbol+'-1d',symbol:primary.symbol,direction:'neutral',horizon:'daily',stage:'on_demand',on_demand:true,origin:'on_demand',chart:primary,technicals,evidence:[],families:[],books:[],ranker:null};
 const snapshot={terminal:{setup_observation:{charts:{series:[primary,...benchmark?[benchmark]:[]]}}}};
 return {row,snapshot,packet:null,now};
}
export function runLector(input){
 const p=prepareInput(input),read=buildDeskRead(p.row,p.snapshot,p.packet,p.now);
 return {schema:'SHIPYARD_LECTOR_ON_DEMAND_RESEARCH_V1',source_commit:SOURCE_COMMIT,source_vintage:SOURCE_VINTAGE,volume_clock_adapter:VOLUME_CLOCK_ADAPTER,computed_at:input.now,primary:input.primary.symbol,feed:input.primary.feed,adjustment:input.primary.adjustment,last_completed_at:input.primary.last_completed_at,received_at:input.primary.received_at,scope:'chart-only; no account, strategy, news, fundamentals, options or breadth context supplied',decision_eligible:false,primary_input:p.row.chart,benchmark_input:p.snapshot.terminal.setup_observation.charts.series[1]||null,technicals:p.row.technicals,read};
}
