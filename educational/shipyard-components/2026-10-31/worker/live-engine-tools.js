const SHIPYARD_LIVE_BUILD = __SHIPYARD_LIVE_BUILD__;
function shipyardLectorScanArguments(a) {
  if (!a || typeof a !== 'object' || Array.isArray(a) || Object.keys(a).some(k=>!['symbol','section','offset','limit','snapshot_hash'].includes(k))) return false;
  if (typeof a.symbol !== 'string' || !/^[A-Za-z][A-Za-z0-9.-]{0,9}$/.test(a.symbol)) return false;
  if (a.section !== undefined && !['summary','factors'].includes(a.section)) return false;
  if (a.offset !== undefined && (!Number.isInteger(a.offset)||a.offset<0||a.offset>1000)) return false;
  if (a.limit !== undefined && (!Number.isInteger(a.limit)||a.limit<1||a.limit>20)) return false;
  if ((a.offset!==undefined || a.limit!==undefined) && a.section!=='factors') return false;
  if (a.snapshot_hash!==undefined && (typeof a.snapshot_hash!=='string'||!/^[a-f0-9]{64}$/.test(a.snapshot_hash))) return false;
  return !a.offset || Boolean(a.snapshot_hash);
}
async function shipyardLectorChart(request,symbol,env,now) {
  const target=new URL('/api/alpaca/bars',request.url);target.searchParams.set('symbol',symbol);target.searchParams.set('days','370');target.searchParams.set('adjustment','split');
  const response=await alpacaRoute(new Request(target,{headers:{'cf-connecting-ip':request.headers.get('cf-connecting-ip') || 'mcp'},signal:request.signal}),env);
  const data=await response.json();
  if (!response.ok && ['invalid_daily_history','invalid_daily_history_schema'].includes(data.error)) throw Error('invalid_daily_history');
  if (!response.ok || data.status!=='connected' || data.complete_response!==true || !data.session_calendar) throw Error('daily_history_or_calendar_unavailable');
  if(data.feed!=='iex' || data.adjustment!=='split' || !Array.isArray(data.bars) || data.bars.length>500 || data.bars.some((b,i)=>
    !shipyardProviderInstant(b.at) || Date.parse(b.at)<Date.parse(data.request_window?.start) || Date.parse(b.at)>Date.parse(data.request_window?.end) || Date.parse(b.at)>now ||
    (i>0 && (b.at<=data.bars[i-1].at || newYorkDate(new Date(b.at))<=newYorkDate(new Date(data.bars[i-1].at)))))) throw Error('invalid_daily_history');
  const today=data.session_calendar.date;
  const rows=data.bars.filter(b=>newYorkDate(new Date(b.at))<today || (newYorkDate(new Date(b.at))===today && data.session_calendar.status==='open' && Date.parse(data.session_calendar.core_end)<=now));
  if (rows.length<20) throw Error('insufficient_completed_daily_history');
  const lastDay=newYorkDate(new Date(rows.at(-1).at));
  // Verify the latest expected completed session, not merely an arbitrary old
  // bar within the original engine's four-day freshness allowance.
  let expected=null;
  for(let back=0;back<8;back++) {
    const day=new Date(Date.parse(today+'T12:00:00Z')-back*86400000).toISOString().slice(0,10);
    const session=back===0?data.session_calendar:await alpacaIexSessionCalendar(day,env.ALPACA_API_KEY_ID,env.ALPACA_API_SECRET_KEY);
    if(!session) throw Error('completed_session_calendar_unavailable');
    if(session.status==='open' && Date.parse(session.core_end)<=now) {expected=day;break;}
  }
  if(!expected || lastDay!==expected) throw Error('latest_completed_session_missing');
  const completed=lastDay===today?data.session_calendar:await alpacaIexSessionCalendar(lastDay,env.ALPACA_API_KEY_ID,env.ALPACA_API_SECRET_KEY);
  if (!completed || completed.status!=='open' || Date.parse(completed.core_end)>now) throw Error('completed_session_calendar_unavailable');
  const capturedBars=rows.slice(-260).map(b=>[b.at,b.open,b.high,b.low,b.close,b.volume]);
  // Apply the same adapter in runLector as a defensive, idempotent boundary.
  // The original source receipt is authoritative for this classification;
  // cache-served timestamps are deliberately not consulted.
  const clocked=SHIPYARD_LIVE_RESEARCH.prepareDailyVolumeChart({interval:'1d',received_at:data.received_at,bars:capturedBars},Date.now());
  const bars=clocked.bars, dailyVolumeInterval=clocked.source_capture.daily_volume_interval;
  return {symbol,interval:'1d',source:'Alpaca Market Data',feed:data.feed,adjustment:data.adjustment,
    observed_at:data.received_at,last_completed_at:completed.core_end,received_at:data.received_at,bars,
    source_capture:{expected_latest_completed_session:expected,latest_session_present:true,session_completion_basis:'OHLC price bar selected at official regular-session close; this does not establish daily-volume interval closure, provider finalization or historical availability',price_clock:{status:'rth_close_observed',close_at:completed.core_end,basis:'official IEX regular-session calendar; price-bar selection boundary only, not provider finality or revision protection'},daily_volume_interval:dailyVolumeInterval,provider_revisions_possible:true,provider_finality:'unknown',received_at:data.received_at,cache_observation:{cache_hit:data.cache_hit===true,served_at:data.served_at||data.received_at,basis:'served_at records when this API response was served; volume interval classification uses original received_at only'},provider_bar_start:rows.at(-1).at,completed_session:completed,excluded_unfinished_daily_rows:data.bars.length-rows.length,requested_days:370}};
}
async function shipyardLectorScan(request,args,env) {
  const symbol=args.symbol.toUpperCase(),start=Date.now();
  const base={schema:'SHIPYARD_LECTOR_SCAN_V1',symbol,producer:'original desk-read-16 chart-only computation',implementation:SHIPYARD_LIVE_BUILD,
    restrictions:{research_only:true,decision_eligible:false,order_submission_enabled:false,account_data_returned:false,continuous_stream:false,stored_output_retimestamped:false,
      note:'Fresh on-demand calculation over completed daily bars, not an intraday quote signal. No position/strategy, news, fundamentals, options or breadth context is supplied; missing factors remain unknown. Source rights and trade admission are not established by calculation.'}};
  try {
    const names=symbol==='SPY'?['SPY']:[symbol,'SPY'];
    const charts=[];for(const s of names) charts.push(await shipyardLectorChart(request,s,env,start));
    if (request.signal.aborted) return json({...base,status:'cancelled'},408);
    const now=new Date().toISOString(),computed=SHIPYARD_LIVE_RESEARCH.runLector({now,primary:charts[0],...(charts[1]?{benchmark:charts[1]}:{})});
    const hash=await SHIPYARD_RESEARCH_LOGIC_HASH(shipyardCanonicalJson({charts:charts.map(c=>({symbol:c.symbol,source:c.source,feed:c.feed,adjustment:c.adjustment,bars:c.bars,last_completed_at:c.last_completed_at,daily_volume_interval:(()=>{const x=c.source_capture?.daily_volume_interval;return x?{status:x.status,timezone:x.timezone,bar_date:x.bar_date,capture_date:x.capture_date,current_bar_volume_withheld:x.current_bar_volume_withheld,withheld_reason:x.withheld_reason,provider_finality:x.provider_finality,provider_revisions_possible:x.provider_revisions_possible,basis:x.basis}:null;})()})),read:computed.read,build:SHIPYARD_LIVE_BUILD}));
    if (args.snapshot_hash && args.snapshot_hash!==hash) return json({...base,status:'snapshot_changed',message:'Input content, original-engine assessment or build changed; restart at offset zero.'},409);
    const read=computed.read,section=args.section || 'summary';
    const out={...base,status:'available',computed_at:now,source_as_of:computed.last_completed_at,snapshot_sha256:hash,source_commit:computed.source_commit,source_vintage:computed.source_vintage,volume_clock_adapter:computed.volume_clock_adapter,
      input_captures:charts.map(({bars,...c})=>({...c,bar_count:bars.length})),section,
      scope:{timeframe:'completed daily',requested_symbols:names,context:'chart-only',source_feed:'iex',adjustment:'split',historical_observation_availability:'unknown; actual present receipt preserved'}};
    if(section==='factors') {const offset=args.offset||0,limit=args.limit||20;out.rows=read.factor_checks.slice(offset,offset+limit);out.pagination={offset,limit,total:read.factor_checks.length,next_offset:offset+limit<read.factor_checks.length?offset+limit:null};}
    else out.assessment={method:read.method,call:read.call,direction_resolution:read.direction_resolution,score:read.score,salient:read.salient,conflicts:read.conflicts,changes_mind:read.changes_mind,factor_review:read.factor_review,scope:read.scope};
    return researchResponse(out);
  } catch(error) {return json({...base,status:'unavailable',error:['daily_history_or_calendar_unavailable','insufficient_completed_daily_history','completed_session_calendar_unavailable','latest_completed_session_missing','invalid_daily_history'].includes(error?.message)?error.message:'lector_computation_unavailable',computed_at:new Date().toISOString()},503);}
}
