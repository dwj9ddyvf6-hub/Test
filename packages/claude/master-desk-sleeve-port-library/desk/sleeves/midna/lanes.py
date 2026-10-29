"""midna_nostop / midna_w_cyan_breadth / midna_hourly_1d / midna_hourly_1w — the Midna lanes of lazarus-desk
config/sleeves.json (a3319569, blob 7097760b: s_mn_nostop, s_mn_w_cyan_breadth, s_mn_hourly_1d, s_mn_hourly_1w), each
on the Lazarus runtime the lazarus family ported (desk/sleeves/families/lazarus.py LazarusLane: Lazarus' desk.run_pass
/ decide / queue_pos / book.hold_exit / exits, parity tools/parity/lazarus_*.py), fed by the sleeve_midna producer
(desk/feedlib/midna_fires.py) instead of its file midna_fires_v1.json.

  s_mn_nostop          1H; entry window [the next hour bar's open, + 30 min], a DAY limit capped at the fire close
                       + 3% (live ref + 1%); $1,000 a position, 2 slots, $2,000 budget, dv20 >= $100,000; no stop,
                       time exit 60 hour bars
  s_mn_w_cyan_breadth  entries on the session after the signal (kind 1d: [09:30, + 65 min], the fire close + 5%);
                       the same sizing; time exit 126 sessions
  s_mn_hourly_1d       the canonical tracker's 1D fires (sleeve_midna.hourly_fires); entries on the session after the
                       fire's daily bar ([09:30, + 65 min]), a DAY limit capped at the fire close + 5%; the same
                       sizing; the plan rules.ts planForNewEntry gives (the tracker's calibrated stop / max bars, else
                       40 sessions)
  s_mn_hourly_1w       the tracker's 1W fires; entries on the session after the fire week's last session; the same
                       limit and sizing; the calibrated plan, else 52 weeks

Removed (cutover doctrine): the entry policy midna_block — Midna's green.ts buyBlockReason (QQQ red AND VIX up AND
the name red on the session, a desk-wide red-day gate the Lazarus port applied to these lanes); held_by_account (one
TEST_MWJW account never holding a symbol twice across lanes — a cross-sleeve overlap check); the shared account cash
pool (0.9 x Reg-T buying power of TEST_MWJW). The lane's budget, slots, dv20 floor and cap stay.

Named divergences: the lazarus family's (desk/sleeves/families/lazarus.py: pass slots, the lane's own virtual book,
the reference-price rule on the desk quote, engine children keyed by the fire key, start flat) and the producer's
(desk/feedlib/midna_fires.py)."""
from ...contract import SleeveConfig
from ...vendor.lazarus import signals
from ..families import lazarus as L

ROWS = {r["id"]: r for r in L.CONFIG["sleeves"] if r["id"].startswith("s_mn_")}
IDS = {"s_mn_nostop": "midna_nostop", "s_mn_w_cyan_breadth": "midna_w_cyan_breadth",
       "s_mn_hourly_1d": "midna_hourly_1d", "s_mn_hourly_1w": "midna_hourly_1w"}
REMOVED = ["midna_block: green.ts buyBlockReason (QQQ red AND VIX up AND the name red: desk-wide red-day gate)",
           "held_by_account: one TEST_MWJW account never holding a symbol twice across lanes (cross-sleeve overlap)",
           "account cash pool: the shared TEST_MWJW 0.9 x Reg-T buying power ('insufficient cash')"]


class MidnaLane(L.LazarusLane):
    RECORD = False              # the Lazarus lanes' FEED-01 record is theirs (the 75 lanes); these keep their record as it was

    def __init__(self, lane):
        row = ROWS[lane]
        self.row = row
        self.family = "midna_tensor"
        self.feed = "midna_fires"
        self.fn = signals.resolve(row)
        z = row["sizing"]
        self.CONFIG = SleeveConfig(
            sleeve_id=IDS[lane], family="midna_tensor", cadence_s=60, universe=(), capital=float(z["budget_usd"]),
            needs={"bars": [{"source": "yahoo", "interval": "1d", "n": 30, "symbols_for": "lazarus"}],
                   "quotes": {"source": "equity"}, "feeds": [self.feed]},
            schedule="rth", status="active",
            params={"lane": row["id"], "account": row["broker_account"], "kind": row["kind"], "state": row["state"],
                    "entry": row["entry"], "exit": row["exit"], "sizing": row["sizing"], "label": row["label"],
                    "removed_gates": REMOVED},
            source=dict(L.SOURCE, lane=row["id"], producer=row["source"]["producer"], file=row["source"]["file"]),
            state_schema={"seen": "dict", "pending": "dict"})
        self.engine = None
        self._st = None


def sleeves():
    return [MidnaLane("s_mn_nostop"), MidnaLane("s_mn_w_cyan_breadth"), MidnaLane("s_mn_hourly_1d"),
            MidnaLane("s_mn_hourly_1w")]
