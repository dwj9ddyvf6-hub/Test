"""Point-in-time feature and condition functions of the Griffith / Ledge Tensor research programme, ported line for
line from agentic-trading-desk main @4c8c179c (tools/parity/tensor_features.py compares each with the source function
on randomized inputs). Pure functions over completed bars ({time, open, high, low, close, volume}, oldest first) and
the Tensor research-tape fields of each bar.

  tensor_htf_event_ledger.py          ema, feature_tape, outcomes-free structural features
  tensor_htf_advanced_features.py     rsi, technical_tape
  tensor_htf_conditional_discovery.py TARGETS, bucket, labels
  tensor_htf_weekly_color_discovery.py atoms
  tensor_htf_weekly_cyan_study.py     context, HYPOTHESES
  tensor_htf_weekly_cyan_discovery.py purge (84-day symbol spacing)
  tensor_htf_deep_mine.py             num, base_type, cycle_state
  tensor_atlas_phenotype_consolidation.py prospective_taxonomy
  tensor_market_scan.py               point_in_time_bundle, frozen_daily_green_g1, tail_features, get_path,
                                      condition, evaluate_specs
  tensor_htf_chart_factory.py         signal_ids, weekly (ISO-week aggregation)
  tensor_counterfactual_policy_lab.py true_range, atr
  tensor_higher_timeframe.py          admit_completed
  tensor_experimental_strategy.py     decision_from_prediction (as a field dict)"""
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from statistics import mean
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
FEATURE_VERSION = "tensor-market-features/1.2.0"
PHENOTYPE_TAXONOMY_VERSION = "tensor-phase2-point-in-time-taxonomy/1.0.0"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


# -- tensor_htf_chart_factory -----------------------------------------------------------------------------------------
def signal_ids(bar):
    values = list(bar.get("primaryMarkers") or [])
    if bar.get("dcbMarker"):
        values.append(f"dcb-{bar['dcbMarker']}")
    values.extend(item["id"] for item in (bar.get("enrichment") or {}).get("signals", []))
    return values


def weekly(daily, current_week=None):
    """ISO-week bars from daily bars, the current (forming) ISO week left out."""
    groups = defaultdict(list)
    for bar in daily:
        dt = datetime.fromtimestamp(bar["time"], timezone.utc)
        iso = dt.isocalendar()
        groups[(iso.year, iso.week)].append(bar)
    result = []
    current_week = current_week or datetime.now(timezone.utc).isocalendar()[:2]
    for key in sorted(groups):
        items = groups[key]
        if key == current_week:
            continue
        result.append({
            "time": items[0]["time"], "open": items[0]["open"],
            "high": max(item["high"] for item in items),
            "low": min(item["low"] for item in items),
            "close": items[-1]["close"],
            "volume": sum(item["volume"] for item in items),
        })
    return result


# -- tensor_htf_event_ledger ------------------------------------------------------------------------------------------
def ema(values, period):
    alpha = 2 / (period + 1); current = values[0]; result = []
    for value in values:
        current = alpha * value + (1 - alpha) * current
        result.append(current)
    return result


def feature_tape(tape, *, only_latest=False):
    closes = [float(row["close"]) for row in tape]; highs = [float(row["high"]) for row in tape]
    lows = [float(row["low"]) for row in tape]; volumes = [float(row.get("volume") or 0) for row in tape]
    emas = {period: ema(closes, period) for period in (21, 50, 200)}
    tr = [highs[0] - lows[0]] + [max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1]))
                                 for i in range(1, len(tape))]
    result = []
    annualizer = math.sqrt(252 if len(tape) > 300 else 52)
    indices = [(len(closes) - 1, closes[-1])] if only_latest and closes else enumerate(closes)
    for index, current in indices:
        prior20 = tape[max(0, index - 20):index]; window52 = tape[max(0, index - 51):index + 1]
        low52 = min(row["low"] for row in window52); high52 = max(row["high"] for row in window52)
        ema200 = emas[200][index]; slope200 = None if index < 20 else ema200 / emas[200][index - 20] - 1
        distance200 = current / ema200 - 1
        if index < 200: label = "EMA200 warming"
        elif distance200 >= 0 and slope200 > 0: label = "above rising EMA200"
        elif distance200 < 0 and slope200 < 0: label = "below falling EMA200"
        elif distance200 >= 0: label = "above flat/falling EMA200"
        else: label = "below flat/rising EMA200"
        recent20_high = max(highs[max(0, index - 19):index + 1]); recent20_low = min(lows[max(0, index - 19):index + 1])
        recent60_high = max(highs[max(0, index - 59):index + 1]); recent60_low = min(lows[max(0, index - 59):index + 1])
        prior52_high = max(highs[max(0, index - 52):index] or [current])
        prior52_low = min(lows[max(0, index - 52):index] or [current])
        tr20 = tr[max(0, index - 19):index + 1]; atr20 = sum(tr20) / len(tr20)
        returns = [closes[i] / closes[i - 1] - 1 for i in range(max(1, index - 19), index + 1)]
        dollars = sorted(closes[i] * volumes[i] for i in range(max(0, index - 19), index + 1))
        row = {
            "regime": label, "ema200Distance": distance200 if index >= 200 else None,
            "ema200Slope20": slope200 if index >= 200 else None,
            "pre20Return": current / closes[index - 20] - 1 if index >= 20 else None,
            "range52Location": (current - low52) / max(high52 - low52, 1e-9) if index >= 51 else None,
            "breakout20": bool(prior20 and current >= max(float(item["high"]) for item in prior20))
            if index >= 20 else None,
            "atr20Fraction": atr20 / current if current else None,
            "compression20To60": ((recent20_high - recent20_low) / current)
            / max((recent60_high - recent60_low) / current, 1e-9) if current else None,
            "realizedVol20": math.sqrt(sum(value * value for value in returns) / max(1, len(returns))) * annualizer,
            "medianDollarVolume20": dollars[(len(dollars) - 1) // 2],
            "overheadSupplyDistance52": max(0.0, prior52_high / current - 1) if current else None,
            "drawdown52": current / prior52_high - 1 if prior52_high else None,
            "rangeExpansion20": (recent20_high - recent20_low) / max(atr20, 1e-9),
            "supportDistance52": current / prior52_low - 1 if prior52_low else None,
        }
        for period in (21, 50, 200):
            row[f"ema{period}Distance"] = current / emas[period][index] - 1
            row[f"ema{period}Slope10"] = None if index < 10 else emas[period][index] / emas[period][index - 10] - 1
        result.append(row)
    return result


# -- tensor_htf_advanced_features -------------------------------------------------------------------------------------
def safe_div(a, b):
    return a / b if b else None


def rsi(values, period=14):
    result = [None] * len(values); gains = []; losses = []
    for i in range(1, len(values)):
        change = values[i] - values[i - 1]; gains.append(max(change, 0)); losses.append(max(-change, 0))
        if i >= period:
            g = mean(gains[i - period:i]); l = mean(losses[i - period:i])
            result[i] = 100.0 if l == 0 else 100 - 100 / (1 + g / l)
    return result


def _day(t):
    return datetime.fromtimestamp(int(t), timezone.utc).date().isoformat()


def technical_tape(tape, spy_by_date, *, only_latest=False):
    closes = [float(x["close"]) for x in tape]; highs = [float(x["high"]) for x in tape]
    lows = [float(x["low"]) for x in tape]; opens = [float(x["open"]) for x in tape]
    volumes = [float(x.get("volume") or 0) for x in tape]
    ema10, ema20, ema40 = ema(closes, 10), ema(closes, 20), ema(closes, 40); rsi14 = rsi(closes)
    tr = [highs[0] - lows[0]] + [max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1]))
                                 for i in range(1, len(tape))]
    plus_dm = [0.0] + [max(highs[i] - highs[i - 1], 0) if highs[i] - highs[i - 1] > lows[i - 1] - lows[i] else 0.0
                       for i in range(1, len(tape))]
    minus_dm = [0.0] + [max(lows[i - 1] - lows[i], 0) if lows[i - 1] - lows[i] > highs[i] - highs[i - 1] else 0.0
                        for i in range(1, len(tape))]
    obv = [0.0]
    adl = []; running_adl = 0.0
    for i in range(len(tape)):
        if i:
            obv.append(obv[-1] + (volumes[i] if closes[i] > closes[i - 1] else -volumes[i]
                                  if closes[i] < closes[i - 1] else 0))
        multiplier = ((closes[i] - lows[i]) - (highs[i] - closes[i])) / max(highs[i] - lows[i], 1e-12)
        running_adl += multiplier * volumes[i]; adl.append(running_adl)
    result = []
    indices = [(len(tape) - 1, tape[-1])] if only_latest and tape else enumerate(tape)
    for i, row in indices:
        stamp = _day(row["time"])

        def window(n, arr, i=i):
            return arr[max(0, i - n + 1):i + 1]
        atr14 = mean(window(14, tr)); atr_prior = mean(tr[max(0, i - 27):max(0, i - 13)]) if i >= 14 else None
        high14 = max(window(14, highs)); low14 = min(window(14, lows)); stoch = safe_div(closes[i] - low14, high14 - low14)
        dx = None
        if i >= 13:
            p = 100 * sum(window(14, plus_dm)) / max(sum(window(14, tr)), 1e-12)
            m = 100 * sum(window(14, minus_dm)) / max(sum(window(14, tr)), 1e-12)
            dx = 100 * abs(p - m) / max(p + m, 1e-12)
        mid = mean(window(20, closes)); variance = mean([(x - mid) ** 2 for x in window(20, closes)])
        sd = math.sqrt(variance); upper = mid + 2 * sd; lower = mid - 2 * sd

        def prior(n, i=i):
            return closes[i] / closes[i - n] - 1 if i >= n else None
        spy_now = spy_by_date.get(stamp); rs = {}
        for n in (4, 13, 26, 52):
            if i >= n and spy_now:
                prior_stamp = _day(tape[i - n]["time"]); spy_then = spy_by_date.get(prior_stamp)
                rs[str(n)] = (prior(n) - (spy_now / spy_then - 1)) if spy_then else None
            else:
                rs[str(n)] = None
        spy_returns = []; stock_returns = []
        for j in range(max(1, i - 25), i + 1):
            a = _day(tape[j - 1]["time"]); b = _day(tape[j]["time"])
            if spy_by_date.get(a) and spy_by_date.get(b):
                stock_returns.append(closes[j] / closes[j - 1] - 1); spy_returns.append(spy_by_date[b] / spy_by_date[a] - 1)
        beta = corr = None
        if len(stock_returns) >= 12:
            sm, pm = mean(stock_returns), mean(spy_returns)
            cov = mean([(a - sm) * (b - pm) for a, b in zip(stock_returns, spy_returns)])
            var = mean([(b - pm) ** 2 for b in spy_returns]); beta = safe_div(cov, var)
            denom = math.sqrt(mean([(a - sm) ** 2 for a in stock_returns]) * var); corr = safe_div(cov, denom)
        ranges = {n: (max(window(n, highs)) - min(window(n, lows))) / closes[i] for n in (4, 13, 26, 52)}
        prior_highs = {n: max(highs[max(0, i - n):i] or [highs[i]]) for n in (13, 26, 52)}
        up_volume = sum(volumes[j] for j in range(max(1, i - 12), i + 1) if closes[j] >= closes[j - 1])
        total_volume = sum(window(13, volumes))
        body = abs(closes[i] - opens[i]); full = max(highs[i] - lows[i], 1e-12)
        result.append({
            "rsi14": rsi14[i], "stoch14": stoch, "adxProxy14": dx, "atr14Fraction": atr14 / closes[i],
            "atrContracting": atr_prior is not None and atr14 < atr_prior,
            "bollingerPercentB": safe_div(closes[i] - lower, upper - lower), "bollingerBandwidth": safe_div(upper - lower, mid),
            "volume4To20": safe_div(mean(window(4, volumes)), mean(window(20, volumes))),
            "volumeDryup": mean(window(4, volumes)) < .7 * mean(window(20, volumes)),
            "upVolumeShare13": safe_div(up_volume, total_volume),
            "obvSlope13": safe_div(obv[i] - obv[max(0, i - 13)], abs(obv[max(0, i - 13)]) + mean(window(13, volumes))),
            "adlSlope13": safe_div(adl[i] - adl[max(0, i - 13)], abs(adl[max(0, i - 13)]) + mean(window(13, volumes))),
            "return4": prior(4), "return13": prior(13), "return26": prior(26), "return52": prior(52),
            "relativeStrength4": rs["4"], "relativeStrength13": rs["13"], "relativeStrength26": rs["26"],
            "relativeStrength52": rs["52"], "beta26": beta, "correlation26": corr,
            "range4Fraction": ranges[4], "range13Fraction": ranges[13], "range26Fraction": ranges[26],
            "range52Fraction": ranges[52], "range4To13": safe_div(ranges[4], ranges[13]),
            "range13To26": safe_div(ranges[13], ranges[26]),
            "breakout13": closes[i] >= prior_highs[13], "breakout26": closes[i] >= prior_highs[26],
            "breakout52": closes[i] >= prior_highs[52], "trendAligned": closes[i] > ema10[i] > ema20[i] > ema40[i],
            "closeLocation": safe_div(closes[i] - lows[i], full), "bodyFraction": body / full,
            "upperWickFraction": safe_div(highs[i] - max(opens[i], closes[i]), full),
            "lowerWickFraction": safe_div(min(opens[i], closes[i]) - lows[i], full),
            "gapFraction": safe_div(opens[i] - closes[i - 1], closes[i - 1]) if i else None,
        })
    return result


# -- tensor_htf_conditional_discovery ---------------------------------------------------------------------------------
TARGETS = ("buy-green", "buy-cyan", "sell-red", "sell-magenta", "dcb-buy", "consensus-buy", "consensus-sell",
           "participation-footprint", "extension-warning", "state-p", "state-d")


def bucket(features):
    regime = str(features.get("regime") or "unknown")
    vol = float(features.get("realizedVol20") or 0)
    dollar = float(features.get("medianDollarVolume20") or 0)
    compression = features.get("compression20To60")
    return {
        "trend": "RISING" if regime == "above rising EMA200" else "FALLING" if regime == "below falling EMA200"
        else "WARMING" if "warming" in regime else "MIXED",
        "volatility": "HIGH" if vol >= .6 else "MEDIUM" if vol >= .3 else "LOW",
        "liquidity": "HIGH" if dollar >= 100_000_000 else "MID" if dollar >= 20_000_000 else "LOW",
        "compression": "TIGHT" if compression is not None and compression <= .45 else "MODERATE"
        if compression is not None and compression <= .75 else "LOOSE",
        "breakout": "BREAKOUT" if features.get("breakout20") is True else "NO_BREAKOUT",
        "extension": "EXTENDED" if float(features.get("ema21Distance") or 0) >= .15 else "NOT_EXTENDED",
    }


def labels(signals, fresh, features):
    result = {f"SIGNAL:{signal}" for signal in fresh & set(TARGETS)}
    structural = bucket(features)
    primary = fresh & {"buy-green", "buy-cyan", "sell-red", "sell-magenta", "dcb-buy"}
    for signal in primary:
        result.add(f"{signal}|TREND:{structural['trend']}")
        result.add(f"{signal}|{structural['breakout']}|COMP:{structural['compression']}")
        result.add(f"{signal}|VOL:{structural['volatility']}|LIQ:{structural['liquidity']}")
        if "consensus-buy" in signals: result.add(f"{signal}|WITH:consensus-buy")
        if "consensus-sell" in signals: result.add(f"{signal}|WITH:consensus-sell")
        if "participation-footprint" in signals: result.add(f"{signal}|WITH:participation-footprint")
        if "extension-warning" in signals: result.add(f"{signal}|WITH:extension-warning")
        if "state-p" in signals: result.add(f"{signal}|WITH:state-p")
        margin = int(features.get("bullishVotes") or 0) - int(features.get("bearishVotes") or 0)
        if margin >= 4: result.add(f"{signal}|BULL_MARGIN_GE4")
        if features.get("fastState") == features.get("slowState") == "bullish": result.add(f"{signal}|FAST_SLOW_BULLISH")
        if structural["trend"] == "RISING" and structural["compression"] in {"TIGHT", "MODERATE"} \
                and structural["breakout"] == "BREAKOUT": result.add(f"{signal}|BASE_EXPANSION_RISING")
        if structural["trend"] == "FALLING": result.add(f"{signal}|DAMAGED_TREND")
    return result


# -- tensor_htf_weekly_color_discovery --------------------------------------------------------------------------------
def n(f, key):
    value = f.get(key); return float(value) if value is not None else None


def atoms(f, signals, classification):
    result = set()

    def add(name, condition):
        if condition:
            result.add(name)
    rsi_ = n(f, "rsi14"); stoch = n(f, "stoch14"); adx = n(f, "adxProxy14"); atr = n(f, "atr14Fraction")
    bb = n(f, "bollingerPercentB"); band = n(f, "bollingerBandwidth"); vol = n(f, "volume4To20")
    up = n(f, "upVolumeShare13"); obv = n(f, "obvSlope13"); adl = n(f, "adlSlope13"); ret13 = n(f, "return13")
    ret26 = n(f, "return26"); rs13 = n(f, "relativeStrength13"); rs26 = n(f, "relativeStrength26"); beta = n(f, "beta26")
    corr = n(f, "correlation26"); rvol = n(f, "rvol"); close_loc = n(f, "closeLocation"); body = n(f, "bodyFraction")
    comp = n(f, "compression20To60"); draw = n(f, "drawdown52"); ema21 = n(f, "ema21Distance")
    margin = int(f.get("bullishVotes") or 0) - int(f.get("bearishVotes") or 0)
    cycle = ((f.get("tensorContext") or {}).get("cycle") or {}); cycle_age = cycle.get("ageBars")
    slow_k = cycle.get("slowK"); ages = f.get("signalAges") or {}
    recent_sell = min((int(ages[x]) for x in ("sell-red", "sell-magenta", "consensus-sell") if ages.get(x) is not None),
                      default=None)
    for name, condition in (
        ("RSI_LT45", rsi_ is not None and rsi_ < 45), ("RSI_45_60", rsi_ is not None and 45 <= rsi_ < 60),
        ("RSI_60_72", rsi_ is not None and 60 <= rsi_ < 72), ("RSI_GE72", rsi_ is not None and rsi_ >= 72),
        ("STOCH_LT30", stoch is not None and stoch < .30), ("STOCH_30_70", stoch is not None and .30 <= stoch < .70),
        ("STOCH_GE70", stoch is not None and stoch >= .70),
        ("ADX_LT20", adx is not None and adx < 20), ("ADX_20_35", adx is not None and 20 <= adx < 35),
        ("ADX_GE35", adx is not None and adx >= 35),
        ("ATR_LT6PCT", atr is not None and atr < .06), ("ATR_6_12PCT", atr is not None and .06 <= atr < .12),
        ("ATR_GE12PCT", atr is not None and atr >= .12), ("ATR_CONTRACTING", f.get("atrContracting") is True),
        ("BB_BELOW_MID", bb is not None and bb < .5), ("BB_MID_TO_UPPER", bb is not None and .5 <= bb < 1),
        ("BB_ABOVE_UPPER", bb is not None and bb >= 1), ("BB_NARROW", band is not None and band < .25),
        ("BB_WIDE", band is not None and band >= .50),
        ("VOLUME_DRYUP", f.get("volumeDryup") is True), ("VOLUME_EXPANSION", vol is not None and vol >= 1.35),
        ("UP_VOLUME_GE60", up is not None and up >= .60), ("OBV_POSITIVE", obv is not None and obv > 0),
        ("ADL_POSITIVE", adl is not None and adl > 0), ("RVOL_GE120", rvol is not None and rvol >= 1.2),
        ("RET13_NEG", ret13 is not None and ret13 < 0), ("RET13_0_25", ret13 is not None and 0 <= ret13 < .25),
        ("RET13_25_60", ret13 is not None and .25 <= ret13 < .60), ("RET13_GE60", ret13 is not None and ret13 >= .60),
        ("RET26_POS", ret26 is not None and ret26 > 0),
        ("RS13_POS", rs13 is not None and rs13 > 0), ("RS13_GE20", rs13 is not None and rs13 >= .20),
        ("RS26_POS", rs26 is not None and rs26 > 0), ("BETA_GE150", beta is not None and beta >= 1.5),
        ("CORR_LT40", corr is not None and corr < .4),
        ("RANGE4_TO13_LT50", n(f, "range4To13") is not None and n(f, "range4To13") < .5),
        ("RANGE13_TO26_LT70", n(f, "range13To26") is not None and n(f, "range13To26") < .7),
        ("TREND_ALIGNED", f.get("trendAligned") is True),
        ("BREAKOUT13", f.get("breakout13") is True), ("BREAKOUT26", f.get("breakout26") is True),
        ("BREAKOUT52", f.get("breakout52") is True), ("CLOSE_HIGH", close_loc is not None and close_loc >= .75),
        ("BODY_GE50", body is not None and body >= .5),
        ("BASE_TIGHT", comp is not None and comp <= .45), ("BASE_MODERATE", comp is not None and .45 < comp <= .75),
        ("DRAWDOWN_GE30", draw is not None and draw <= -.30), ("EMA21_EXTENSION", ema21 is not None and ema21 >= .15),
        ("BULL_MARGIN_GE4", margin >= 4),
        ("SPY_BULL", f.get("spyRegime") == "above rising EMA200"),
        ("SPY_TRANSITION", f.get("spyRegime") != "above rising EMA200"),
        ("WITH_PARTICIPATION", "participation-footprint" in signals), ("WITH_CONSENSUS_BUY", "consensus-buy" in signals),
        ("WITH_BOUNCE", "dcb-buy" in signals), ("WITH_EXTENSION_WARNING", "extension-warning" in signals),
        ("FAST_BULL", f.get("fastState") == "bullish"), ("SLOW_BULL", f.get("slowState") == "bullish"),
        ("FAST_SLOW_BULL", f.get("fastState") == f.get("slowState") == "bullish"),
        ("ACTIVE_CALL_BULL", f.get("activeCall") == "bullish"),
        ("CALL_REVERSAL_BULL", f.get("activeCall") == "bullish" and f.get("callLifecycle") == "reversed"),
        ("CANDLE_BULL", f.get("candleRegime") == "bullish"),
        ("MACD_HIST_POS", n(f, "macdHistogram") is not None and n(f, "macdHistogram") > 0),
        ("CYCLE_BULL_STRONG", cycle.get("state") == "BULL_STRONG"), ("CYCLE_BULL_WEAK", cycle.get("state") == "BULL_WEAK"),
        ("CYCLE_MOMENTUM_ALIGNED", cycle.get("momentumAgreement") is True),
        ("CYCLE_MOMENTUM_DIVERGING", cycle.get("momentum") == "diverging"),
        ("CYCLE_AGE_LE3", cycle_age is not None and int(cycle_age) <= 3),
        ("CYCLE_AGE_4_10", cycle_age is not None and 4 <= int(cycle_age) <= 10),
        ("CYCLE_AGE_GT10", cycle_age is not None and int(cycle_age) > 10),
        ("CYCLE_STOCH_GE70", slow_k is not None and float(slow_k) >= 70),
        ("PRIOR_BOUNCE_1_8", ages.get("dcb-buy") is not None and 1 <= int(ages["dcb-buy"]) <= 8),
        ("PRIOR_GREEN_1_8", ages.get("buy-green") is not None and 1 <= int(ages["buy-green"]) <= 8),
        ("PRIOR_CYAN_1_8", ages.get("buy-cyan") is not None and 1 <= int(ages["buy-cyan"]) <= 8),
        ("PRIOR_SELL_1_8", recent_sell is not None and 1 <= recent_sell <= 8),
        ("NO_CYAN_26", ages.get("buy-cyan") is None or int(ages["buy-cyan"]) >= 26),
        ("NO_GREEN_26", ages.get("buy-green") is None or int(ages["buy-green"]) >= 26),
    ):
        add(name, condition)
    b = str(classification.get("risk_bucket") or "UNCLASSIFIED"); result.add(f"SIC:{b}")
    return result


# -- tensor_htf_weekly_cyan_study / discovery -------------------------------------------------------------------------
COST_CYAN = 0.01


def number(features, key):
    value = features.get(key)
    return float(value) if value is not None else None


def age(features, signal):
    value = (features.get("signalAges") or {}).get(signal)
    return int(value) if value is not None else None


def cyan_context(features, active):
    regime = str(features.get("regime") or "")
    compression = number(features, "compression20To60")
    drawdown = number(features, "drawdown52")
    pre20 = number(features, "pre20Return")
    ema21 = number(features, "ema21Distance")
    ema50 = number(features, "ema50Distance")
    overhead = number(features, "overheadSupplyDistance52")
    margin = int(features.get("bullishVotes") or 0) - int(features.get("bearishVotes") or 0)
    prior_cyan = age(features, "buy-cyan")
    prior_bounce = age(features, "dcb-buy")
    prior_sell = min((x for x in (age(features, "sell-red"), age(features, "sell-magenta"),
                                  age(features, "consensus-sell")) if x is not None), default=None)
    rising = regime == "above rising EMA200"
    warming = regime == "EMA200 warming" or "warming" in regime
    damaged = regime == "below falling EMA200"
    compressed = compression is not None and compression <= 0.75
    tight = compression is not None and compression <= 0.45
    near_high = drawdown is not None and drawdown >= -0.15
    deep = drawdown is not None and drawdown <= -0.30
    extended = (ema21 is not None and ema21 >= 0.15) or (pre20 is not None and pre20 >= 0.50)
    repaired = (not damaged and ema21 is not None and ema21 > 0 and ema50 is not None and ema50 > -0.03
                and pre20 is not None and pre20 > 0)
    first_in_26 = prior_cyan is None or prior_cyan >= 26
    return {
        "rising": rising, "warming": warming, "damaged": damaged, "compressed": compressed, "tight": tight,
        "breakout": features.get("breakout20") is True, "near_high": near_high, "deep_drawdown": deep,
        "extended": extended, "not_extended": not extended,
        "low_overhead": overhead is not None and overhead <= 0.15, "repaired": repaired,
        "participation": "participation-footprint" in active, "consensus_buy": "consensus-buy" in active,
        "fast_slow_bullish": features.get("fastState") == features.get("slowState") == "bullish",
        "bull_margin_ge4": margin >= 4, "first_cyan_26": first_in_26,
        "recent_bounce_8": prior_bounce is not None and 1 <= prior_bounce <= 8,
        "recent_sell_8": prior_sell is not None and 1 <= prior_sell <= 8,
        "bullish_candle": features.get("candleRegime") == "bullish",
        "call_reversal": features.get("callLifecycle") == "reversed" and features.get("activeCall") == "bullish",
    }


CYAN_HYPOTHESES = (
    ("CY01_RISING_COMPRESSED", lambda c: c["rising"] and c["compressed"]),
    ("CY02_RISING_BASE_BREAKOUT", lambda c: c["rising"] and c["compressed"] and c["breakout"]),
    ("CY03_RISING_FIRST_CYAN", lambda c: c["rising"] and c["first_cyan_26"]),
    ("CY04_RISING_PARTICIPATION", lambda c: c["rising"] and c["participation"]),
    ("CY05_RISING_CONSENSUS", lambda c: c["rising"] and c["consensus_buy"]),
    ("CY06_RISING_BULL_STACK", lambda c: c["rising"] and c["fast_slow_bullish"]),
    ("CY07_BASE_IGNITION", lambda c: c["compressed"] and c["breakout"] and c["low_overhead"] and c["not_extended"]),
    ("CY08_FIRST_BASE_IGNITION", lambda c: c["first_cyan_26"] and c["compressed"] and c["breakout"]
     and c["not_extended"]),
    ("CY09_REPAIR_REVERSAL", lambda c: c["repaired"] and c["call_reversal"]),
    ("CY10_REPAIR_PARTICIPATION", lambda c: c["repaired"] and c["participation"]),
    ("CY11_DEEP_REVERSAL", lambda c: c["deep_drawdown"] and c["repaired"]),
    ("CY12_BOUNCE_THEN_CYAN", lambda c: c["recent_bounce_8"] and c["repaired"]),
    ("CY13_SELL_TO_CYAN_REVERSAL", lambda c: c["recent_sell_8"] and c["repaired"]),
    ("CY14_LOW_OVERHEAD_FIRST", lambda c: c["first_cyan_26"] and c["low_overhead"] and c["not_extended"]),
    ("CY15_NEAR_HIGH_CONTINUATION", lambda c: c["rising"] and c["near_high"] and c["not_extended"]),
    ("CY16_TIGHT_BULLISH_CANDLE", lambda c: c["tight"] and c["bullish_candle"] and c["not_extended"]),
    ("CY17_DAMAGED_NEGATIVE_CONTROL", lambda c: c["damaged"]),
    ("CY18_EXTENDED_NEGATIVE_CONTROL", lambda c: c["extended"]),
)


def purge_ok(last_iso, stamp, days=84):
    """tensor_htf_weekly_cyan_discovery.purge: a symbol's next counted event is >= 84 days after its last."""
    if not last_iso:
        return True
    return datetime.fromisoformat(stamp).date().toordinal() - datetime.fromisoformat(last_iso).date().toordinal() >= days


# -- tensor_htf_deep_mine / tensor_atlas_phenotype_consolidation ------------------------------------------------------
def num(value):
    try:
        value = float(value); return value if math.isfinite(value) else None
    except (TypeError, ValueError):
        return None


def base_type(f):
    r13 = num(f.get("return13")); comp = num(f.get("compression20To60")); short = num(f.get("range4To13"))
    rsi_ = num(f.get("rsi14")); reg = str(f.get("regime") or "")
    if (rsi_ or 0) >= 75 or (r13 or 0) >= 1: return "VERTICAL_EXTENSION"
    if r13 is not None and r13 >= .50 and short is not None and short <= .65: return "HIGH_TIGHT_FLAG_OR_LEDGE"
    if comp is not None and comp <= .50 and short is not None and short <= .65: return "VOLATILITY_CONTRACTION"
    if f.get("breakout26"): return "BREAKOUT_26"
    if "below falling" in reg or "warming" in reg: return "RECOVERY_OR_EARLY_CYCLE"
    if r13 is not None and .15 <= r13 <= .60 and short is not None and short <= .75: return "CONTROLLED_REACCELERATION_LEDGE"
    return "OTHER_OR_MIXED"


def cycle_state(f):
    rsi_ = num(f.get("rsi14")) or 50; r13 = num(f.get("return13")) or 0; rs = num(f.get("relativeStrength13")) or 0
    comp = num(f.get("compression20To60")) or 1
    if rsi_ >= 75 or r13 >= 1: return "TERMINAL_OR_EXHAUSTION"
    if r13 >= .20 and rs >= .10 and comp <= .75: return "LEADER_REACCELERATION"
    if r13 >= 0 and rs >= 0: return "EARLY_MARKUP"
    if comp <= .55: return "ACCUMULATION_OR_COMPRESSION"
    if r13 < 0 and rs < 0: return "REPAIR_OR_DECLINE"
    return "TRANSITION"


def prospective_taxonomy(features, topology):
    cycle = str(topology.get("cycleState") or "STATE_UNKNOWN")
    momentum = str(topology.get("cycleMomentum") or "MOMENTUM_UNKNOWN")
    bulls = num(topology.get("bullishVotes"))
    bears = num(topology.get("bearishVotes"))
    if "STRONG" in cycle or momentum == "aligned" or (bulls is not None and bears is not None and bulls >= bears + 2):
        event_energy = "BULLISH_ALIGNED"
    elif "WEAK" in cycle or momentum in {"diverging", "fading"} or (bulls is not None and bears is not None
                                                                     and bears > bulls):
        event_energy = "WEAK_OR_DIVERGING"
    else:
        event_energy = "MIXED_OR_TRANSITIONAL"
    dollars = num(topology.get("eventDollarVolume"))
    rvol = num(topology.get("rvol"))
    if dollars is None:
        participation = "DOLLAR_DEPTH_UNKNOWN"
    elif dollars < 1_000_000:
        participation = "THIN_UNDER_1M_DOLLARS"
    elif dollars < 10_000_000:
        participation = "MODEST_1M_TO_10M_DOLLARS"
    elif rvol is not None and rvol >= 2:
        participation = "DEEP_WITH_RVOL_EXPANSION"
    elif rvol is not None and rvol < 0.8:
        participation = "DEEP_QUIET_PARTICIPATION"
    else:
        participation = "DEEP_NORMAL_PARTICIPATION"
    enrichment = topology.get("eventEnrichment") or []
    return {
        "preEventPhase": cycle_state(features),
        "preEventStructure": base_type(features),
        "eventEnergy": event_energy,
        "eventParticipation": participation,
        "eventEnrichmentSignature": "+".join(enrichment) or "NO_EVENT_ENRICHMENT",
    }


# -- tensor_market_scan -----------------------------------------------------------------------------------------------
def point_in_time_bundle(bars, tensor, benchmark_bars):
    if not benchmark_bars:
        return ({"state": "UNAVAILABLE", "reason": "SPY_COMPLETED_BAR_BENCHMARK_UNAVAILABLE",
                 "taxonomyVersion": PHENOTYPE_TAXONOMY_VERSION}, {})
    spy_by_date = {datetime.fromtimestamp(int(row["time"]), timezone.utc).date().isoformat(): float(row["close"])
                   for row in benchmark_bars}
    advanced = technical_tape(bars, spy_by_date, only_latest=True)[-1]
    structural = feature_tape(bars, only_latest=True)[-1]
    evidence = {**structural, **advanced}
    required = ("rsi14", "return13", "relativeStrength13", "compression20To60", "range4To13", "breakout26", "regime")
    missing = [name for name in required if evidence.get(name) is None]
    if missing:
        return ({"state": "UNAVAILABLE", "reason": "MISSING_POINT_IN_TIME_FEATURES", "missing": missing,
                 "taxonomyVersion": PHENOTYPE_TAXONOMY_VERSION}, evidence)
    research = list(tensor.get("researchTail") or [])
    latest = research[-1] if research else {}
    cycle = ((latest.get("tensorContext") or {}).get("cycle") or {})
    enrichment = sorted("enrichment:" + str(item["id"])
                        for item in ((latest.get("enrichment") or {}).get("signals") or []) if item.get("id"))
    close = float(bars[-1]["close"]); volume = float(bars[-1]["volume"])
    topology = {
        "cycleState": cycle.get("state"), "cycleMomentum": cycle.get("momentum"),
        "bullishVotes": latest.get("bullishVotes"), "bearishVotes": latest.get("bearishVotes"),
        "rvol": latest.get("rvol"), "eventDollarVolume": close * volume,
        "eventEnrichment": enrichment,
    }
    return ({"state": "READY", "taxonomyVersion": PHENOTYPE_TAXONOMY_VERSION, **prospective_taxonomy(evidence, topology),
             "pointInTimeFeatureHash": digest({name: evidence.get(name) for name in required})}, evidence)


def frozen_daily_green_g1(point_features, primary_markers, frame):
    up_volume = point_features.get("upVolumeShare13")
    return {
        "freshDailyGreen": frame == "1d" and "buy-green" in set(primary_markers),
        "aboveRisingEma200": point_features.get("regime") == "above rising EMA200",
        "compression20To60Le075": point_features.get("compression20To60") is not None
        and float(point_features["compression20To60"]) <= 0.75,
        "breakout20": point_features.get("breakout20") is True,
        "ema21DistanceLt015": point_features.get("ema21Distance") is not None
        and float(point_features["ema21Distance"]) < 0.15,
        "constructiveParticipation": (up_volume is not None and float(up_volume) >= 0.50)
        or "participation-footprint" in set(point_features.get("allSignals") or []),
    }


def tail_features(bars, tensor, benchmark_bars=None, frame=None):
    closes = [float(row["close"]) for row in bars]
    volumes = [float(row["volume"]) for row in bars]
    ranges = [max(float(row["high"]) - float(row["low"]), 0.0) for row in bars]
    latest = closes[-1]

    def mean_(values):
        return sum(values) / len(values) if values else 0.0
    sma20, sma50 = mean_(closes[-20:]), mean_(closes[-50:])
    atr20 = mean_(ranges[-20:])
    prior_atr = mean_(ranges[-60:-20]) or atr20
    research = list(tensor.get("researchTail") or [])
    latest_bar = research[-1] if research else {}
    marker_rows = [row for row in research if row.get("primaryMarkers") or row.get("dcbMarker")
                   or row.get("warningMarker") or (row.get("enrichment") or {}).get("signals")]
    marker_counts = Counter(marker for row in research for marker in list(row.get("primaryMarkers") or []))
    enrichment_counts = Counter(str(item.get("id")) for row in research
                                for item in list((row.get("enrichment") or {}).get("signals") or []))
    analysis = tensor.get("analysis") or {}; current = analysis.get("current") or {}
    phenotype, point_features = point_in_time_bundle(bars, tensor, benchmark_bars)
    up_volume = point_features.get("upVolumeShare13")
    g1_criteria = frozen_daily_green_g1(point_features, list(latest_bar.get("primaryMarkers") or []), frame)
    return {
        "close": latest, "return5": latest / closes[-6] - 1 if len(closes) > 5 else None,
        "return20": latest / closes[-21] - 1 if len(closes) > 20 else None,
        "distanceSma20Atr": (latest - sma20) / atr20 if atr20 else None,
        "distanceSma50Atr": (latest - sma50) / atr20 if atr20 else None,
        "sma20AboveSma50": sma20 > sma50, "rangeCompression": atr20 / prior_atr if prior_atr else None,
        "volumeRatio20": volumes[-1] / mean_(volumes[-20:]) if mean_(volumes[-20:]) else None,
        "tensorState": current.get("state"), "tensorDirection": current.get("direction"),
        "currentMarkers": list(latest_bar.get("primaryMarkers") or []),
        "markerCounts64": dict(sorted(marker_counts.items())), "enrichmentCounts64": dict(sorted(enrichment_counts.items())),
        "markerBars64": len(marker_rows),
        "barsSinceLastMarker": (len(research) - 1 - max((i for i, row in enumerate(research) if row in marker_rows),
                                                        default=-1)) if research else None,
        "rvol": latest_bar.get("rvol"), "fastState": latest_bar.get("fastState"), "slowState": latest_bar.get("slowState"),
        "candleRegime": latest_bar.get("candleRegime"), "warning": bool(latest_bar.get("warningMarker")),
        "phenotype": phenotype,
        "dailyGreenG1": {
            "version": "H4_DAILY_GREEN_BASE_EXPANSION/1.0.0",
            "state": "MATCH" if all(g1_criteria.values()) else "NO_MATCH",
            "criteria": g1_criteria,
            "compression20To60": point_features.get("compression20To60"),
            "ema21Distance": point_features.get("ema21Distance"),
            "upVolumeShare13": up_volume,
            "regime": point_features.get("regime"),
        },
    }


def get_path(value, path):
    current = value
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def condition(actual, operator, expected):
    if operator == "eq": return actual == expected
    if operator == "ne": return actual != expected
    if operator == "in": return actual in expected if isinstance(expected, list) else False
    if operator == "contains": return expected in actual if isinstance(actual, (list, str, dict)) else False
    if actual is None or isinstance(actual, bool): return False
    try:
        left, right = float(actual), float(expected)
        return {"gt": left > right, "gte": left >= right, "lt": left < right, "lte": left <= right}.get(operator, False)
    except (TypeError, ValueError):
        return False


def evaluate_specs(context, specs):
    matches = []
    for spec in specs:
        if not spec.get("enabled", False):
            continue
        required = list(spec.get("required") or []); optional = list(spec.get("optional") or [])
        required_results = [condition(get_path(context, str(rule["path"])), str(rule["op"]), rule.get("value"))
                            for rule in required]
        optional_results = [condition(get_path(context, str(rule["path"])), str(rule["op"]), rule.get("value"))
                            for rule in optional]
        if required_results and all(required_results):
            score = 100.0 * (len(required_results) + sum(optional_results)) / max(1, len(required_results) + len(optional_results))
            matches.append({"phenotypeId": spec["id"], "phenotypeVersion": spec["version"],
                            "state": spec.get("state", "DEVELOPING"), "score": round(score, 4),
                            "required": len(required_results), "optionalSatisfied": sum(optional_results),
                            "explanation": spec.get("explanation", "")})
    return sorted(matches, key=lambda row: (-row["score"], row["phenotypeId"]))


# -- tensor_counterfactual_policy_lab / tensor_higher_timeframe ------------------------------------------------------
def true_range(row, previous_close):
    return max(float(row["high"]) - float(row["low"]), abs(float(row["high"]) - previous_close),
               abs(float(row["low"]) - previous_close))


def atr(rows, index, lookback=14):
    left = max(1, index - lookback + 1)
    values = [true_range(rows[i], float(rows[i - 1]["close"])) for i in range(left, index + 1)]
    return mean(values) if values else max(float(rows[index]["high"]) - float(rows[index]["low"]), 0.01)


class TensorAdmissionError(RuntimeError):
    pass


def admit_completed(raw, frame, now):
    """tensor_higher_timeframe.admit_completed over {t (ISO), o, h, l, c, v} rows at `now` (aware datetime)."""
    current = now.astimezone(ET); by_time = {}; rejected = {"forming": 0, "malformed": 0, "duplicate": 0}
    for row in raw:
        try:
            opened = datetime.fromisoformat(str(row["t"]).replace("Z", "+00:00")).astimezone(timezone.utc)
            local = opened.astimezone(ET); values = {k: float(row[k]) for k in ("o", "h", "l", "c", "v")}
            if min(values.values()) < 0 or values["o"] <= 0 or values["h"] < max(values["o"], values["c"]) \
                    or values["l"] > min(values["o"], values["c"]):
                raise ValueError("malformed")
            if frame == "1d":
                if local.weekday() >= 5:
                    raise ValueError("non-session daily bar")
                complete = local.date() < current.date() or (local.date() == current.date() and current.weekday() < 5
                                                             and (current.hour, current.minute) >= (16, 0))
            elif frame == "1wk":
                week = (local.isocalendar().year, local.isocalendar().week)
                now_week = (current.isocalendar().year, current.isocalendar().week)
                complete = week < now_week or (week == now_week and (current.weekday() > 4 or (
                    current.weekday() == 4 and (current.hour, current.minute) >= (16, 0))))
            else:
                raise ValueError("unsupported frame")
            if not complete:
                rejected["forming"] += 1; continue
            epoch = int(opened.timestamp())
            if epoch in by_time:
                rejected["duplicate"] += 1
            by_time[epoch] = {"time": epoch, "open": values["o"], "high": values["h"], "low": values["l"],
                              "close": values["c"], "volume": values["v"]}
        except (KeyError, TypeError, ValueError):
            rejected["malformed"] += 1
    bars = [by_time[key] for key in sorted(by_time)]
    if len(bars) < 200:
        raise TensorAdmissionError(f"Tensor requires at least 200 admitted {frame} bars; received {len(bars)}")
    return bars, {"status": "admitted", "interval": frame, "finality": "closed",
                  "sessionAuthority": "completed_sessions" if frame == "1d" else "completed_weeks",
                  "admitted": len(bars), "rejected": rejected, "latestBarAt": bars[-1]["time"]}


# -- tensor_experimental_strategy -------------------------------------------------------------------------------------
EXPERIMENT_STRATEGY_ID = "TENSOR_PHENOTYPE_EXPERIMENTAL"
EXPERIMENT_VERSION = "TENSOR_EXPERIMENTAL_1_1_0"
EXPERIMENT_POLICY_ID = "HIGH_BREAK_4|TP25_STOP2ATR_H26"
EXPERIMENT_AUTHORITY = "T4_QUALIFIED_EXPERIMENTAL_PAPER_ONLY_VIA_EXISTING_EXECUTION_CONTROLS"


def decision_from_prediction(row, completed, qualification_state):
    """decision_from_prediction over admitted completed bars: the StrategyDecision fields (dict) or None."""
    if qualification_state not in {"QUALIFIED", "AUTHORIZED_PAPER_EXPERIMENT"}:
        return None
    lookup = {int(bar["time"]): index for index, bar in enumerate(completed)}
    cutoff = int(row["event_cutoff"])
    if cutoff not in lookup:
        return None
    event_index = lookup[cutoff]
    event_atr = float(atr(completed, event_index))
    event = completed[event_index]
    trigger = float(event["high"])
    limit_price = trigger + 0.10 * event_atr
    stop = float(event["close"]) - 2.0 * event_atr
    daily = str(row["timeframe"]) == "1d"
    policy_id = "HIGH_BREAK_4|TP10_STOP2ATR_H26" if daily else EXPERIMENT_POLICY_ID
    target = limit_price * (1.10 if daily else 1.25)
    if not (event_atr > 0 and stop > 0 and stop < trigger <= limit_price < target):
        return None
    identity = {"predictionId": row["prediction_id"], "observationHash": row["observation_hash"],
                "specificationId": row["specification_id"], "policyId": policy_id}
    evidence_hash = digest(identity)
    return dict(
        decisionId=f"tensor-experimental:{evidence_hash[:24]}", strategyId=EXPERIMENT_STRATEGY_ID,
        scannerVersion=EXPERIMENT_VERSION, symbol=str(row["symbol"]),
        asOf=datetime.fromtimestamp(cutoff, timezone.utc).isoformat(), evidenceHash=evidence_hash,
        status="BUY", score=100.0, engine="FROZEN_TENSOR_PHENOTYPE",
        setupClass=str(row["specification_id"]), entryReference=round(limit_price, 8),
        invalidationReference=round(stop, 8), horizonSessions=26 if daily else 130,
        reasonCodes=(("T4_QUALIFIED_EXPERIMENTAL" if qualification_state == "QUALIFIED"
                      else "AUTHORIZED_UNQUALIFIED_PAPER"), "FROZEN_PROSPECTIVE_PHENOTYPE", "FOUR_BAR_HIGH_BREAK",
                     "TWO_ATR_STOP", "TEN_PERCENT_TARGET" if daily else "TWENTY_FIVE_PERCENT_TARGET"),
        metrics={
            "authority": EXPERIMENT_AUTHORITY, "experimental": True, "qualified": qualification_state == "QUALIFIED",
            "qualificationState": qualification_state, "predictionId": row["prediction_id"],
            "specificationId": row["specification_id"], "policyId": policy_id,
            "triggerPrice": trigger, "limitPrice": limit_price, "initialStop": stop,
            "target": target, "eventAtr": event_atr, "eventCutoff": cutoff,
            "timeframe": row["timeframe"], "entryWindowDays": 7 if daily else 28,
        },
    )
