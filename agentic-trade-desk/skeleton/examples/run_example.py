"""End-to-end toy: one sleeve, frozen bars, ShadowBroker, restart-safety demonstrated.

    python3 skeleton/examples/run_example.py

PAPER / SIMULATED ONLY. The strategy below is a toy and has no claimed edge.
"""
import os, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from deskkit.alerts import Alerts
from deskkit.broker import ShadowBroker
from deskkit.caps import Lane
from deskkit.desk import Desk
from deskkit.ledger import Ledger

# frozen fixture: date -> close for one ETF
BARS = {"2026-03-02": 100.0, "2026-03-03": 99.0, "2026-03-04": 99.5, "2026-03-05": 100.2,
        "2026-03-06": 100.4, "2026-03-09": 101.0}
DAYS = sorted(BARS)


class DipBuyer:
    """Toy rule: if the last closed bar is down vs the previous one, buy 1 share; sell 3 sessions after the fill."""
    name = "toy_dip"

    def __init__(self, ledger, asof_idx):
        self.ledger, self.i = ledger, asof_idx

    def entries(self):
        if self.i < 1:
            return []
        d, p = DAYS[self.i], DAYS[self.i - 1]
        if BARS[d] < BARS[p]:
            # bar_ts is the DATA bar that triggered the decision, not now()
            return [dict(sleeve=self.name, symbol="ETF", bar_ts=d, kind="entry", side="buy", qty=1)]
        return []

    def exits(self):
        out = []
        held = self.ledger.positions().get((self.name, "ETF"), 0)
        if held and self.i >= 3 + DAYS.index("2026-03-03"):   # 3 sessions after the fill session (toy: hold 3 sessions after the 03-03 entry)
            out.append(dict(sleeve=self.name, symbol="ETF", bar_ts=DAYS[self.i], kind="exit", side="sell", qty=held))
        return out


def main():
    d = tempfile.mkdtemp()
    ledger = Ledger(os.path.join(d, "ledger.sqlite"))
    for i, day in enumerate(DAYS):
        marks = {"ETF": BARS[day]}
        for attempt in ("first process", "restarted process"):   # second run simulates a supervisor restart
            desk = Desk(ledger, ShadowBroker(marks), Alerts(ledger),
                        [DipBuyer(ledger, i)], {"toy_dip": Lane("toy_dip", 2, 200)}, marks.get)
            s = desk.run_pass()
            print(f"{day} {attempt:17s} orders={s['orders']} skipped={s['skipped']} errors={s['errors']}")
    print("book (replayed from ledger):", ledger.positions() or "flat")
    print("chain ok:", ledger.verify_chain())


if __name__ == "__main__":
    main()
