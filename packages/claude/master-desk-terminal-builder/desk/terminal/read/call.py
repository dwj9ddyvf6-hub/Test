"""The call: everything measured on a name, weighed into one decisive long plan (the model:
docs/research/2026-10-18-terminal/MODEL.md).

  evidence    one vote per kind of evidence: a family's facts sum (structure counts twice, momentum, volume and
              the desk's own strategies once, the market and events not at all) and saturate, tanh(S / 1.5), so a
              family casts at most one vote however many facts it has (the 2026-10-19 audit: one trend voted about
              four times). E, the sum over families, reads as the kinds of evidence that agree, net
  the plan    the form the evidence earns: a buy now or on a pullback only when the evidence nets for the long; a
              breakout or a turn (both wait for a daily close over a line) otherwise. Never the side the evidence
              nets against: a falling chart gets the close that would prove it wrong as its trigger.
  conviction  how many kinds of evidence clearly agree, net (a kind's one vote at least half a vote for the long, less
              the kinds at least half a vote against it): High at four, Solid at three, Speculative otherwise, from
              the evidence alone; reward-to-risk is a gate (1R or better), never a booster, since a tight stop
              inflates it. (Until 2026-10-25 it read E, High at 3: every listed call read High, batch bs1 item 8)
  the take    Strong, For, Leaning or Against: the evidence and the cues it does not hold (support stacked at the
              buy, the fund it follows, earnings inside the hold), one kind each; no fact counts twice (the conflicts
              are in the evidence and named, not counted again); it sits beside conviction and moves no number
  the read    3 to 5 standouts (unusual times trustworthy, one per family, market facts excluded), what argues
              against it, what would change the desk's mind (always against the call), everything else checked, and
              what the desk has no data for
Every number in every sentence comes from a fact or the plan; nothing is parsed back out of words."""
import math

from ... import calendar as cal
from . import candles, indicators, lines, momentum, patterns, structure, trend, volatility, volume, waves, words, wyckoff
from . import optnews
from .core import CLASS_WEIGHT, Fact
from .words import join

FAMILIES = (trend, structure, momentum, volume, volatility, candles, patterns, wyckoff, waves, lines,
            indicators)  # one wave count:
# Echo's (waves.py). elliott.py's reader moved nothing (C-H3) and named another count beside it on 1,104 reads
CONVICTION = {3: "High conviction", 2: "Solid", 1: "Speculative"}
GUT = ("Against", "Leaning", "For", "Strong")
ACTION = {"now": "Buy", "pullback": "Buy on a pullback", "breakout": "Buy on a breakout", "turn": "Buy on a turn",
          "wait": "Stand aside"}

def all_facts(x):
    out = []
    for fam in FAMILIES:
        out += fam.facts(x)
    return reconcile(waves.reframe(x, out))


def reconcile(fs):
    """one reading per stretch of bars. A bull flag is a pole and then a drift: the drift's lower high and lower low
    are the flag, which the pattern reads for the long, and the swings read them again against it (A and BURL on
    2026-10-16). Inside a flag the swings are the flag's drift (a bear flag's bounce), context, not a vote; so inside a
    wedge, whose rising or falling swings are the wedge (formations: a pattern that names its swings, data "drift")"""
    flag = next((f for f in fs if f.side and (f.key == "pattern.flag" or (f.family == "Pattern" and
                                                                          (f.data or {}).get("drift")))), None)
    if flag:
        for f in fs:
            if f.key == "trend.swings" and f.side == -flag.side:
                drift = (flag.data or {}).get("drift") or ("the flag's drift" if flag.side > 0 else "the flag's bounce")
                f.side, f.strength, f.clause = 0, 0.0, ""
                f.text = f.text.rstrip(".") + f": {drift}."
                f.reading = f"{f.reading} ({drift})"
    return fs


def context_facts(x, extra):
    """the desk's strategies, the fear-day rule, earnings, the fund it follows, the market and liquidity, and the
    options and news of the session's gather (read/optnews.py: context, voting nothing)"""
    out = []
    d = extra.get("desk") or {}
    engines = d.get("engines") or []
    if engines:
        k = len(engines)
        out.append(Fact("desk.strategies", "The desk", "desk", 1, min(0.8, 0.35 + 0.2 * (k - 1)),
                        f"{k} of the desk's strategy kind{'s' if k != 1 else ''} buying",
                        f"The desk's own strategies signaled a buy: {k} kind{'s' if k != 1 else ''} of strategy.",
                        f"Desk strategies: {k} kind{'s' if k != 1 else ''} buying", "strategies", 0.3 + 0.1 * k,
                        {"engines": engines}))
    if d.get("holds"):
        out.append(Fact("desk.holds", "The desk", "context", 0, 0.0, "Held", "Held.", "Held",   # the held chip says it
                        "strategies"))
    f = extra.get("fear")
    if f:
        side = 1 if f.get("state") == "came" else 0
        out.append(Fact("ctx.fear", "Timing", "context", side, 0.5 if side else 0.0, f.get("label") or "Fear day",
                        f.get("text") or "", f"Fear-day rule: {f.get('short') or f.get('state')}", "fear_day",
                        0.5 if side else 0.0, {"state": f.get("state")}))
    e = extra.get("earnings")
    if e:
        out.append(Fact("ctx.earnings", "Events", "context", 0, 0.0, f"Earnings {words.short_day(e)}",
                        f"It reports earnings on {words.day(e)}.", f"Earnings: {words.short_day(e)}", "earnings", 0.0,
                        {"date": e}))
    if x.index_bars and x.index_sym and x.index_sym != x.sym:
        ic = [float(b["c"]) for b in x.index_bars]
        if len(ic) >= 200:
            m50, m200 = sum(ic[-50:]) / 50, sum(ic[-200:]) / 200
            fund = x.index_sym
            if ic[-1] > m50 and ic[-1] > m200:
                side, txt = 1, f"{fund}, the fund it follows, is above its 50-day and 200-day averages."
            elif ic[-1] < m200:
                side, txt = -1, f"{fund}, the fund it follows, is below its 200-day average."
            else:
                side, txt = 0, f"{fund}, the fund it follows, is between its 50-day and 200-day averages."
            out.append(Fact("ctx.fund", "Market", "context", side, 0.3 if side else 0.0, f"{fund}: "
                            + ("in an uptrend" if side > 0 else "below its 200-day" if side < 0 else "pulling back"),
                            txt, f"{fund}: " + ("above its averages" if side > 0 else "below its 200-day" if side < 0
                                                else "between its averages"), "moving_average", 0.0))
    m = extra.get("market") or {}
    chips = {c.get("id"): c for c in m.get("chips") or []}
    if chips:
        part, vol = chips.get("participation"), chips.get("volatility")
        bits = []
        if part:
            bits.append(f"{part.get('value')} of stocks above their 50-day average")
        if vol:
            bits.append(f"volatility {str(vol.get('value')).lower()}")
        if bits:
            out.append(Fact("ctx.market", "Market", "context", 0, 0.0, "The market",
                            "Market: " + join(bits) + ".", "Market: " + join(bits), "", 0.0))
    if x.n >= 20:
        dv = sorted(float(b["c"]) * float(b.get("v") or 0) for b in x.bars[-20:])[10]
        words_dv = (f"{dv / 1e9:.1f} billion" if dv >= 1e9 else f"{dv / 1e6:.0f} million")
        out.append(Fact("ctx.liquidity", "Liquidity", "context", 0, 0.0, "Liquidity",
                        f"About {words_dv} dollars trade in it on a typical day.",
                        f"Liquidity: about {words_dv} dollars a day", "", 0.0, {"dollar_volume": dv}))
    return out + optnews.facts_of(x, extra)


# the kinds of evidence: one vote each (the daily and weekly wave counts are one kind, so are a session's candle and
# gap: the audit's C-M10 and B-H4)
FAMILY = {"Trend": "trend", "Levels": "levels", "Momentum": "momentum", "Divergence": "divergence",
          "Volume": "volume", "Volatility": "volatility", "Candles": "session", "Gaps": "session",
          "Pattern": "pattern", "Wyckoff": "wyckoff", "Elliott wave": "waves", "Weekly wave": "waves",
          "The desk": "desk"}
SCALE = 1.5                          # one 0.8-strength structure fact (a vote of 1.6) is 0.79 of a vote
E_HIGH, E_SOLID = 3.0, 2.0           # the evidence's own reading: three kinds net, two (the take's reasons say so)
AGREE = 0.5                          # a kind clearly agrees when its one vote is at least half a vote
R_HIGH = 1.3                         # High conviction needs reward-to-risk of 1.3 or more (owner, 2026-10-26)
K_HIGH, K_SOLID = 4, 3               # conviction: four kinds clearly agree, net; three. E at 3 or more (High until
# 2026-10-25) held about 100 of the session's 765 board-eligible reads, twenty times the board's five places, so every
# listed call read High; E sums part-votes, so many weak kinds made it. These bands keep the design's selectivity on
# the roster (2026-10-23: 62 High and 210 Solid of 1,664 plans, against 135 and 356) and split the board's calls
# (the 27 listed to 2026-10-23, by their recorded facts: 17 High, 9 Solid, 1 Speculative). No outcome is used
T_STRONG, T_FOR = 3.0, 1.5           # the take, in the same units: the evidence and the outside cues


def family_votes(fs):
    """{kind: its one vote in (-1, 1)}: the kind's fact votes summed and saturated"""
    sums = {}
    for f in fs:
        if f.vote:
            k = FAMILY.get(f.family, f.family.lower())
            sums[k] = sums.get(k, 0.0) + f.vote
    return {k: math.tanh(v / SCALE) for k, v in sums.items()}


def evidence(fs):
    """E: the sum of the kinds' votes"""
    return sum(family_votes(fs).values())


def take_word(t):
    return "Strong" if t >= T_STRONG else "For" if t >= T_FOR else "Leaning" if t >= 0 else "Against"


def _uptrend(fs):
    return any(f.key == "trend.stack" and f.side > 0 and f.strength >= 0.45 for f in fs)


def _downtrend(fs):
    st = next((f for f in fs if f.key == "trend.stack"), None)
    sw = next((f for f in fs if f.key == "trend.swings"), None)
    return bool(st and st.side < 0 and st.strength >= 0.45 and (sw is None or sw.side <= 0))


BEARISH = -1.0                       # a kind of evidence net against the long: only a close over a line buys


def allowed(pl, e, down):
    """never buy into evidence that nets against the long: a falling chart or bearish evidence waits for a close over
    a line; a buy right here also needs the evidence at least even"""
    if pl.form in ("now", "pullback") and (down or e <= BEARISH):
        return False
    return not (pl.form == "now" and e < 0)


def choose(x, fs, plans):
    """the plan the evidence earns, or None: the strongest form, the nearer buy, then the better reward to risk"""
    e = evidence(fs)
    up, down = _uptrend(fs), _downtrend(fs)

    at_high = any(f.key == "trend.range52" and (f.data.get("off_hi") or -99) > -5 for f in fs) or \
        any(f.key == "trend.high52" for f in fs)

    def q(pl):
        textbook = pl.source.startswith("pattern") or (up and at_high)   # a base, or a leader at its highs
        base = {"now": 3.0, "pullback": 2.2, "breakout": 2.6 if textbook else 1.6, "turn": 0.5}[pl.form]
        if pl.form == "pullback" and not up:
            base -= 0.8
        if pl.form == "turn" and not down:
            base -= 1.0
        wave = 1.0 if pl.source in ("wave2", "wave4") else 0.0   # a clean wave count names the zone: it leads
        return base + wave + min(pl.r, 3.0) * 0.25 + (pl.p_fill - 1.0 if pl.form == "pullback" else 0.0)
    ok = [pl for pl in plans if allowed(pl, e, down)]
    return max(ok, key=q) if ok else None


def kinds_net(fs):
    """the kinds of evidence that clearly agree with the long (one vote of AGREE or more), less those clearly against"""
    votes = family_votes(fs).values()
    return sum(1 for v in votes if v >= AGREE) - sum(1 for v in votes if v <= -AGREE)


def conviction(fs, pl):
    """(level 1-3, E, the reasons): from the evidence alone, by how many kinds clearly agree, net (kinds_net)"""
    e = evidence(fs)
    votes = family_votes(fs)
    net = kinds_net(fs)
    level = 3 if net >= K_HIGH else 2 if net >= K_SOLID else 1
    agree = [k for k, v in votes.items() if v >= AGREE]
    why = [f"{len(agree)} kinds of evidence agree"] if len(agree) >= 3 else []
    desk = next((f for f in fs if f.key == "desk.strategies"), None)
    if desk and len(desk.data.get("engines") or []) >= 2:
        why.append("the desk's strategies agree")
    cap = 3 if pl.r >= R_HIGH else 2                 # High needs room: a thin reward-to-risk is Solid at best (2026-10-26)
    if (pl.form == "turn" and _downtrend(fs)) or e < 0:      # a turn on a falling chart (D-C3)
        cap = 1
    elif pl.source.startswith("pattern"):
        pf = next((f for f in fs if f.family == "Pattern" and f.side > 0), None)
        if pf and pf.data.get("vol") is not None and pf.data["vol"] < patterns.VOL_CONFIRM:
            cap = 2
    return min(level, cap), e, why


def gut(x, fs, pl, until):
    """(word, score, reasons): the desk's judgment. The evidence (E), and the cues it does not hold, a kind each:
    support stacked at the buy, the fund it follows, earnings inside the hold. The sharpest conflict is named, not
    counted again (the audit's D-H2: a failed trigger counted in the evidence, the conviction and the take). The
    Elliott reader is context and moves nothing (C-H3)"""
    e = evidence(fs)
    t, why = e, ["the evidence is broad"] if e >= E_HIGH else ["the evidence leans its way"] if e >= 1.5 else \
        ["the evidence nets against it"] if e < 0 else []

    def has(key, side=1):
        return any(f.key.startswith(key) and f.side == side for f in fs)
    zone_conf = max([a.confluence for a in x.areas if a.lo <= pl.zone_hi and a.hi >= pl.zone_lo] or [0])
    if zone_conf >= 3 and pl.form in ("now", "pullback"):
        t, why = t + 1, why + ["support stacked at the buy"]
    if has("ctx.fund"):
        t, why = t + 1, why + ["the fund it follows is rising"]
    if has("ctx.fund", -1):
        t, why = t - 1, why + ["the fund it follows is below its 200-day"]
    ev = next((f for f in fs if f.key == "ctx.earnings"), None)
    as_of = cal._as_date(float(x.bars[-1]["t"])).isoformat()
    if ev and until and ev.data.get("date") and as_of < ev.data["date"] <= until.isoformat():
        t, why = t - 1, why + ["earnings inside the hold"]          # until: the hold's last session (D-H4)
    sharp = sharpest(fs)
    if sharp and sharp.vote <= -0.8:
        why = why + [sharp.as_clause()]                  # the same fact the take names and the page lists first
    word = take_word(t)
    five = any(f.key in ("wave.five", "wave.w.five") and f.side < 0 and f.cls != "context" for f in fs)
    if pl.form in ("breakout", "now") and five and word in ("Strong", "For"):
        word, why = "Leaning", why + ["chasing a finished fifth wave"]   # his rule: the buy is the next wave 2;
    return word, t, why                                                  # a cap on this plan's form, not a vote


def against(fs, k=3):
    """what argues against the long, the strongest vote first: the facts on the short side at strength 0.3 or more,
    and earnings inside the hold"""
    return [f for f in sorted(fs, key=lambda f: f.vote) if f.side < 0 and (f.strength >= 0.3 or
                                                                          f.key == "ctx.earnings")][:k]


def sharpest(fs, skip=()):
    """the sharpest conflict: the strongest vote against the long, first in what argues against it; the desk's
    reasons and its take name this one fact (332 reads on 2026-10-16 named one in each)"""
    return next((f for f in against(fs, 99) if f.vote < 0 and f.key not in skip), None)


def surprise(f, rates):
    """bits: -log2 of the share of the session's roster showing this reading (its key and side), so a reading every
    name shows says nothing about this one and one in a hundred says almost seven bits; a reading no other read
    showed counts as one read of the roster. None without the roster's shares (rates: {key|side: share, "_n": reads})"""
    if not rates:
        return None
    n = rates.get("_n") or 0
    r = rates.get(f"{f.key}|{f.side}") or (1.0 / n if n else None)
    return -math.log2(r) if r else None


def _salience(f, rates=None):
    s = surprise(f, rates)
    if s is None:                                       # no roster read yet: the reading's fixed rarity
        return CLASS_WEIGHT[f.cls] * f.strength * (0.6 + f.rarity)
    return CLASS_WEIGHT[f.cls] * f.strength * s


COMMON = 0.5                         # a reading more than half the session's roster shows describes the market


def standouts(fs, side, k=5, rates=None):
    """the most unusual, most trustworthy facts on one side, one per family, never the market: unusual against the
    session's whole roster (surprise) when its shares are known, else by each reading's fixed rarity. On 2026-10-16
    the fixed rarity put a reading shared by more than 30% of the roster among 89% of reads' standouts ("support
    below" fired on 87%); a reading more than half the roster shows that session is the market's, not a standout"""
    seen, out = set(), []
    common = (lambda f: (rates.get(f"{f.key}|{f.side}") or 0.0) > COMMON) if rates else (lambda f: False)
    for f in sorted((f for f in fs if f.side == side and f.cls != "context" and f.strength > 0 and not common(f)),
                    key=lambda f: -_salience(f, rates)):
        if f.family in seen:
            continue
        seen.add(f.family)
        out.append(f)
        if len(out) == k:
            break
    return out
