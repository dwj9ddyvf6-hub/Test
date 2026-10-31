// This adapter is appended after the hash-pinned original scorer. It changes
// only the evidence eligibility of volume-dependent factors when any supplied
// volume observation is absent; it does not alter indicator formulas, weights,
// thresholds, price-only factors, or the original scorer implementation.
function deskDailyVolumeClockAbstention(row,factors){
  if(row?.on_demand!==true||row?.chart?.interval!=='1d'||!Array.isArray(factors))return factors;
  const bars=row.chart.bars||[],hasMissingVolume=bars.some(bar=>!Array.isArray(bar)||bar[5]===null||bar[5]===undefined||!Number.isFinite(bar[5])||bar[5]<0);
  if(!hasMissingVolume)return factors;
  const clock=row.chart?.source_capture?.daily_volume_interval||{},clockStatus=clock.status||'unknown';
  const captureDate=clock.capture_date||'unknown capture date',barDate=clock.bar_date||'unknown bar date';
  const reason=clockStatus==='open_at_capture'
    ?`The latest daily bar is retained for its OHLC, but its New York-date volume interval was still open at the original source receipt (capture date ${captureDate}; bar date ${barDate}).`
    :clockStatus==='closed_as_observed'
      ?`The latest daily bar is retained for its OHLC, but the supplied daily volume history contains a missing observation (capture date ${captureDate}; bar date ${barDate}).`
      :`The latest daily bar is retained for its OHLC, but capture evidence does not verify closure of its New York-date volume interval (capture date ${captureDate}; bar date ${barDate}).`;
  const caveat=` ${reason} This is an interval-completeness abstention, not a provider-finality claim: finality is unknown and later provider revisions remain possible.`;
  const extraVolumeIds=new Set([
    'dollar_volume','effort_result','gap_taxonomy','high_tight_flag','bump_run_reversal',
    'climax_top','climax_run','selling_climax','volume_dry_up','power_earnings_gap',
    'anchored_vwap_gap','ytd_anchored_vwap','vwap_stdev_bands'
  ]);
  return factors.map(f=>{
    if(!f||typeof f!=='object')return f;
    const directVolume=f.category==='Volume'||(f.category==='Additional volume gauges'&&f.id!=='market_profile_tpo')||extraVolumeIds.has(f.id);
    if(directVolume)return {...f,status:'not_supplied',value:null,material:false,detail:caveat.trim()};
    // A price-only breakout remains readable, but never lets a missing current
    // volume value masquerade as a below-threshold confirmation.
    if(f.id==='breakout_quality'&&f.value&&typeof f.value==='object'){
      const detail=String(f.detail||'').replace(/;\s*volume (?:confirms|is below 1\.5×);?/i,'');
      return {...f,value:{...f.value,relative_volume:null},detail:`${detail}${detail?'.':''} Current-bar volume confirmation is unavailable.${caveat}`};
    }
    return f;
  });
}
