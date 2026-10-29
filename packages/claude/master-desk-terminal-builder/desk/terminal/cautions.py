"""Cautions: ChartsLector's grade-A warnings on a read (P1) and the analysis engine's veto (P5), compact (a short
head, its detail on tap) and credited. A warning shows only in the tiers whose own row of the study is grade A
(eyes/DEEP/evidence.csv: robustness grade A, use VETO, outcome u20, the 20-session percentile against equally volatile
names of the same tier):

  lod_stop   micro and nano (R00215, R00216), and only above the tier's top-decile cut (LOD_CUT)
  gapfill+   micro and nano (R00179, R00180)
  stg+6      micro and nano (R00197, R00198)
  crsi_ext-  nano (R00173)

A liquid or small name never carries one, and every board and watching name is liquid (the board's bar), so in
practice they show on Look-up reads of micro and nano names. Each is kept on the read's record (records[].cautions)
and its forward ledger row, so it is scored forward. Its words are the row's own numbers (read/clx.py says what each
one measures).

The engine's veto (engine_veto) shows on a name its screen vetoes where the veto is in force (small, micro and nano;
engine.vetoed), in words from SEC-V's walk-forward test (VETO_ROWS). It is kept on the call's engine line, not on the
record's cautions: FB2 scores the veto, and this scores nothing new.

Context only: a caution votes nothing and moves no take, conviction, plan or place on the board.

cautions(readings, tier, bars) -> [{key, head, text, credit}]
veto(tier)                     -> {key, head, text, credit} for a vetoed name's tier, or None"""
from .read import words as W

CREDIT = "ChartsLector"
# the study's numbers (evidence.csv, the holdout 2023-26): the 20-session percentile points below equally volatile
# names in the tier after the event fired, and for the stop the top tenth's mean 20-session return against its cell
ROWS = {"lod_stop": {"micro": ("R00215", 1.46), "nano": ("R00216", 0.36)},
        "gapfill+": {"micro": ("R00179", 0.65), "nano": ("R00180", 1.57)},
        "stg+6": {"micro": ("R00197", 7.53), "nano": ("R00198", 7.46)},
        "crsi_ext-": {"nano": ("R00173", 7.13)}}
# the tier's top-decile cut of lod_stop over the study's discovery years (2016-22): clxp.parquet's clxp_lod_stop on
# the panel's micro and nano rows (225,790 and 217,293 rows): 5.5049% and 6.254% (the holdout's are 6.15% and 8.17%)
LOD_CUT = {"micro": 5.5049, "nano": 6.254}
HEAD = {"lod_stop": "Wide low-of-day stop", "gapfill+": "Down gap filled", "stg+6": "Stretched advance",
        "crsi_ext-": "Overbought extreme"}
ORDER = ("lod_stop", "gapfill+", "stg+6", "crsi_ext-")
VETO, ENGINE = "engine_veto", "Analysis engine"
# SEC-V's walk-forward test, 2018-22 out of fold (eyes/DEEP/out2/ENGINE_FINAL.md): the names it vetoed minus the
# names it passed, each against equally volatile names of its tier: the 20-session percentile in points (u20 gap) and
# the bottom-5% losers per 100 names (lose5 gap)
VETO_ROWS = {"small": (1.06, 2.30), "micro": (1.23, 2.42), "nano": (1.55, 2.61)}


def _day(bars, k):
    """the session k sessions before the last, in words (Oct 14)"""
    from .. import calendar as cal
    return W.short_day(cal._as_date(float(bars[len(bars) - 1 - k]["t"])))


def cautions(readings, tier, bars):
    """[{key, head, text, credit}]: the warnings that fired on the read in a tier whose row is grade A"""
    out = []
    for key in ORDER:
        row = ROWS[key].get(tier)
        v = (readings or {}).get(key)
        if row is None or v is None:
            continue
        if key == "lod_stop" and v <= LOD_CUT[tier]:
            continue
        out.append({"key": key, "head": HEAD[key], "credit": CREDIT,
                    "text": TEXT[key].format(v=v, x=row[1], tier=tier, day=_day(bars, v) if key != "lod_stop" else "")})
    return out


# one sentence a warning, each its own words (a card can carry several: no phrase said twice, the language diet)
TEXT = {"lod_stop": "Its stop under the low sits {v:.1f}% below the close; at this width, {tier} caps lagged similar "
                    "stocks by {x:.1f}% in the next 20 sessions.",
        "gapfill+": "{day}: the close filled a down gap; {tier} caps that did this ranked {x:.1f} percentile points "
                    "lower over the next month.",
        "stg+6": "{day}: it entered his stretched stage 2D; afterwards {tier} caps trailed equally volatile peers by "
                 "{x:.1f} points of rank.",
        "crsi_ext-": "{day}: his calibrated RSI crossed into its overbought extreme; over 20 sessions it ranked {x:.1f} "
                     "points below peers, for {tier} caps."}
VETO_TEXT = ("The engine's loser screen flags it: in its 2018–22 test, flagged {tier} caps ranked {u:.1f} points lower "
             "than equally volatile ones over 20 sessions, and {l5:.1f} more in every 100 landed in the worst 5%.")


def veto(tier):
    """the engine's veto as a caution for a name vetoed in `tier` (engine.vetoed), or None outside its tiers"""
    row = VETO_ROWS.get(tier)
    if row is None:
        return None
    return {"key": VETO, "head": "Loser screen flag", "credit": ENGINE,
            "text": VETO_TEXT.format(tier=tier, u=row[0], l5=row[1])}
