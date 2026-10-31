// Provider-origin, read-only inputs for exact research engines. No browser upload,
// strategy substitution, order/account path, WebSocket or persistent state.
const SHIPYARD_INTRADAY_INTERVALS = { '1Min': 60000, '5Min': 300000, '10Min': 600000 };
function shipyardStrictInstant(v) {
  return typeof v === 'string' && /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,3})?Z$/.test(v)
    && Number.isFinite(Date.parse(v)) && new Date(Date.parse(v)).toISOString().slice(0,10) === v.slice(0,10);
}
function shipyardProviderInstant(v) {
  return typeof v === 'string' && /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,9})?Z$/.test(v)
    && Number.isFinite(Date.parse(v)) && new Date(Date.parse(v)).toISOString().slice(0,10) === v.slice(0,10);
}
function shipyardIntradayArguments(args) {
  if (!args || typeof args !== 'object' || Array.isArray(args)) return false;
  if (Object.keys(args).some(k => !['symbol','timeframe','start','end','feed','adjustment','page_token','limit'].includes(k))) return false;
  if (!/^[A-Za-z0-9][A-Za-z0-9.-]{0,9}$/.test(args.symbol || '') || typeof args.symbol !== 'string') return false;
  if (typeof args.timeframe !== 'string' || !Object.hasOwn(SHIPYARD_INTRADAY_INTERVALS,args.timeframe)) return false;
  if (!shipyardStrictInstant(args.start) || !shipyardStrictInstant(args.end)) return false;
  const span = Date.parse(args.end)-Date.parse(args.start);
  if (!(span > 0 && span <= 370*86400000)) return false;
  if (args.adjustment !== undefined && !['raw','all'].includes(args.adjustment)) return false;
  if (args.feed !== undefined && !['sip','iex'].includes(args.feed)) return false;
  if (args.limit !== undefined && (!Number.isInteger(args.limit) || args.limit < 1 || args.limit > 100)) return false;
  if (args.page_token !== undefined && (typeof args.page_token !== 'string' || !/^[\x21-\x7e]{1,2048}$/.test(args.page_token))) return false;
  return true;
}
async function shipyardIntradayBars(request, args, env) {
  if (!shipyardIntradayArguments(args)) return json({schema:'SHIPYARD_INTRADAY_BARS_V1',status:'invalid',error:'invalid_arguments'},400);
  const now = Date.now(), receivedAt = () => new Date().toISOString();
  const base = { schema:'SHIPYARD_INTRADAY_BARS_V1', symbol:args.symbol.toUpperCase(), timeframe:args.timeframe,
    requested_window:{start:args.start,end:args.end,end_exclusive:true}, feed:args.feed || 'iex', adjustment:args.adjustment || 'raw',
    restrictions:{research_only:true,continuous_stream:false,engine_executed:false,decision_eligible:false,account_data_returned:false,order_submission_enabled:false},
    source:'Alpaca Market Data', transport:'on-demand REST; independent of browser',
    availability_contract:'Provider timestamps are bar starts, not receipt times. Historical available_at is unknown; do not invent pre-decision observations. Adjustment is explicit: raw is unadjusted; all uses provider corporate-action adjustments and may revise historical values.',
  };
  if (Date.parse(args.end) > now) return json({...base,status:'invalid',error:'end_must_not_be_in_the_future'},400);
  if (!alpacaRateAllowed(request,now)) return json({...base,status:'unavailable',error:'rate_limited',retry_after_seconds:60},429);
  const key = env?.ALPACA_API_KEY_ID, secret = env?.ALPACA_API_SECRET_KEY;
  if (typeof key !== 'string'||!key||typeof secret !== 'string'||!secret) return json({...base,status:'unavailable',error:'market_data_credentials_unavailable'},503);
  if (request.signal.aborted) return json({...base,status:'cancelled'},408);
  const query = new URLSearchParams({timeframe:args.timeframe,start:args.start,end:new Date(Date.parse(args.end)-1).toISOString(),feed:base.feed,adjustment:args.adjustment || 'raw',sort:'asc',limit:String(args.limit || 100)});
  if (args.page_token) query.set('page_token',args.page_token);
  const result = await alpacaJson(`https://data.alpaca.markets/v2/stocks/${encodeURIComponent(base.symbol)}/bars?${query}`,key,secret);
  const retrievedAt=receivedAt();
  if (request.signal.aborted) return json({...base,status:'cancelled'},408);
  if (!result.ok) return json({...base,status:'unavailable',retrieved_at:retrievedAt,error:result.status===401?'market_data_authentication_failed':result.status===403?'requested_feed_not_entitled':result.status===429?'provider_rate_limited':'intraday_bars_unavailable',feed_fallback:false},503);
  const payload=result.value;
  if ((payload?.symbol !== undefined && payload.symbol !== base.symbol) || !Array.isArray(payload?.bars) || payload.bars.length>(args.limit || 100)) return json({...base,status:'invalid',error:'provider_schema_invalid',retrieved_at:retrievedAt},502);
  const next=payload.next_page_token;
  if (next!==null && next!==undefined && (typeof next!=='string'||!/^[\x21-\x7e]{1,2048}$/.test(next))) return json({...base,status:'invalid',error:'provider_pagination_invalid',retrieved_at:retrievedAt},502);
  if (next && next === args.page_token) return json({...base,status:'invalid',error:'provider_pagination_did_not_advance',retrieved_at:retrievedAt},502);
  const duration=SHIPYARD_INTRADAY_INTERVALS[args.timeframe], rows=[], seen=new Set(); let previous=-Infinity, incomplete=0;
  for (const b of payload.bars) {
    const providerTime = shipyardProviderInstant(b?.t);
    const at=providerTime ? timestamp(b.t) : null, t=Date.parse(at), end=t+duration;
    const values=['o','h','l','c','v'].map(k=>finite(b?.[k]));
    if (!at || t<previous || seen.has(t) || t<Date.parse(args.start) || t>=Date.parse(args.end) || values.some(v=>v===null)
        || values.slice(0,4).some(v=>v<=0) || b.v<0 || b.l>Math.min(b.o,b.c) || b.h<Math.max(b.o,b.c) || b.h<b.l
        || (b.n!==undefined && (!Number.isSafeInteger(b.n)||b.n<0)) || (b.vw!==undefined && (finite(b.vw)===null||b.vw<=0))) {
      return json({...base,status:'invalid',error:'provider_bar_invalid',retrieved_at:retrievedAt},502);
    }
    previous=t;seen.add(t);
    // Preserve missing bars; never manufacture flat candles. Intraday provider
    // bars can be revised after close, so closure is not finality.
    if (end>now-1000 || end>Date.parse(args.end)) {incomplete++;continue;}
    rows.push({t:at,o:b.o,h:b.h,l:b.l,c:b.c,v:b.v,...(b.n!==undefined?{n:b.n}:{}),...(b.vw!==undefined?{vw:b.vw}:{}),bar_end:new Date(end).toISOString()});
  }
  return researchResponse({...base,status:'available',retrieved_at:retrievedAt,bars:rows,
    quality:{provider_rows:payload.bars.length,returned_rows:rows.length,unfinished_or_window_straddling_excluded:incomplete,missing_intervals_filled:false,regular_session_filtered:false,provider_revisions_possible:true,historical_availability_known:false},
    clocks:{latest_returned_bar_end:rows.at(-1)?.bar_end || null,latest_returned_bar_age_seconds:rows.length?(Date.parse(retrievedAt)-Date.parse(rows.at(-1).bar_end))/1000:null,live_freshness_asserted:false},
    pagination:{next_page_token:next || null,limit:args.limit || 100,request_identity:{symbol:base.symbol,timeframe:args.timeframe,start:args.start,end:args.end,feed:base.feed,adjustment:args.adjustment || 'raw'},
      note:'Keep start/end/feed/timeframe/adjustment and all request fields unchanged on continuation. Tokens are provider cursors, not cryptographic identity locks; compare the returned request_identity. Provider revisions may occur across pages; this is not an atomic historical snapshot. Fetch the exchange calendar separately and resample using the exact engine contract; all sessions are returned.'}});
}
