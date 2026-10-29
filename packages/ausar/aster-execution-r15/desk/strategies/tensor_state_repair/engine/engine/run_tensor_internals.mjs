import fs from 'node:fs';
import {fileURLToPath} from 'node:url';
import {runTensorResearch} from './run_tensor.mjs';
import {stochasticRsi,macdSeries,wilderAtr,redDragonMcdx,utBotSeries,slope,onBalanceVolume} from './instrumented-v690/lib/anna-internals.mjs';

export function runTensorInternals(request) {
  const native=runTensorResearch(request);
  const bars=request.bars;
  const close=bars.map(b=>b.close),high=bars.map(b=>b.high),low=bars.map(b=>b.low),volume=bars.map(b=>b.volume);
  const macd=macdSeries(close,12,26,9),stoch=stochasticRsi(close,14,14,3,3);
  const mcdx=redDragonMcdx(high,low,close,volume,100,5),ut=utBotSeries(high,low,close,10,1),obv=onBalanceVolume(close,volume);
  return {...native,internalsProvenance:'Native private helper formulas exposed by instrumented source derivative; frozen-v690 source remains byte-identical.',
    internalArrays:{
      timestamp:bars.map(b=>b.timestamp),
      macdLine:macd.macd,macdSignal:macd.signal,macdHistogram:macd.histogram,
      stochRsiUnderlyingRsi14:stoch.rsi,stochRsiRaw14:stoch.raw,stochK:stoch.k,stochD:stoch.d,
      wilderAtr10:ut.atr,wilderAtr14:wilderAtr(high,low,close,14),wilderAtr20:wilderAtr(high,low,close,20),
      mcdxProfitSma5:mcdx.averageProfit,mcdxLockedSma5:mcdx.averageLocked,mcdxRockSma5:mcdx.averageRock,
      obvSlope5:obv.map((_,i)=>slope(obv,i,5)),obvSlope10:obv.map((_,i)=>slope(obv,i,10)),priceSlope10:close.map((_,i)=>slope(close,i,10)),
    },
    internalClockScope:'Each array uses only its input prefix; open-bar values remain tentative and must not be financial decision inputs.'};
}
if (process.argv[1] && fileURLToPath(import.meta.url)===process.argv[1]) {
  const x=JSON.parse(process.argv[2]?fs.readFileSync(process.argv[2],'utf8'):fs.readFileSync(0,'utf8'));
  const result=JSON.stringify(runTensorInternals(x))+'\n';
  if(process.argv[3])fs.writeFileSync(process.argv[3],result);else process.stdout.write(result);
}
