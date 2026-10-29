"""Host for Lazarus sleeves. Lazarus is the reference/rollback desk and is only READ: its sleeve roster
(config/sleeves.json), its pure signal functions (lazarus/signals.py) and the producer files they read.
md2 never writes into /workspace/lazarus and never touches its state/ledger/orders (Lazarus ids are lz1-*, md2 ids md2-*)."""
import sys, json, subprocess, os
LZ = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "lz_engine")   # md2's pinned copy: the retired /workspace/lazarus tree is no longer a runtime dependency
from ..sleeve import Sleeve, Signal
from ..data import Missing
from .. import ind

def pinned_sha():
    try: return subprocess.check_output(["git", "-C", LZ, "rev-parse", "HEAD"], text=True).strip()
    except Exception: return None

_INPUTS = {}
def inputs(now):
    """load Lazarus' pass inputs once per pass (fan-out to every Lazarus sleeve)."""
    if LZ not in sys.path: sys.path.insert(0, LZ)
    from lazarus import desk, cal
    import pandas as pd
    k = int(now // 300)
    if k not in _INPUTS:
        _INPUTS.clear(); C, SC = desk.load_config(); I, health = desk.load_inputs(C, cal.ts(pd.Timestamp(now, unit="s", tz="UTC")))
        _INPUTS[k] = (C, SC, I, health)
    return _INPUTS[k]

KIND_TF = {"1h": "1h", "1d": "1d", "1w": "1wk"}
DISASTER_STOP = 15.0   # Lazarus C.broker_stop_pct (L-134) - the stop every live Lazarus lot holds at the broker
MIDNA = "/workspace/Trader-research/shadow/paper_sleeve"
FORWARD_RUIN = 40.0     # sleeve_midna.FORWARD_RUIN_PCT, applied here WITHOUT its halt-file side effect (md2 is a separate book)

def midna_exit(lane, pos, px, b, now):
    """Midna's researched signal exits (turtle 2N/10-day, MACD/VWAP down + 3-ATR chandelier, Faber, reversal, pairs, hedge flip)
    - before this, md2's shadow copies of the s_mn_* lanes had NO signal exit (only plan time), so e.g. turtle/macd/vwap/faber/pairs
    (max_bars 0) could never close. Forward lanes: the 40% adverse circuit is evaluated natively so md2 never writes Midna's halt file."""
    import pandas as pd
    if MIDNA not in sys.path: sys.path.insert(0, MIDNA)
    import sleeve_midna as MX
    if LZ not in sys.path: sys.path.insert(0, LZ)
    from lazarus import cal
    e = float(pos["avg"])
    if lane in {v[0] for v in MX.FORWARD_LANES.values()}:
        return f"Midna forward: {FORWARD_RUIN:g}% adverse circuit" if px <= e * (1 - FORWARD_RUIN / 100) else None
    p = dict(sym=pos["symbol"], lane=lane, entry_avg=e, fire_key=pos.get("signal_key"), opened_at=str(pd.Timestamp(pos.get("fill_ts") or now, unit="s", tz="UTC")))
    try: return MX.midna_exit_reason(p, cal.ts(pd.Timestamp(now, unit="s", tz="UTC")), cal.next_td, px, float(pos.get("peak") or px))
    except Exception: return None   # a failed signal read is missing evidence: stop/time exits stay live

class LazarusSleeve(Sleeve):
    source = "lazarus"; venue = "shadow"
    def __init__(self, s):
        self.s = s; self.sid = "lz_" + s["id"]; self.lz_id = s["id"]; self.family = s.get("kind"); self.tf = s.get("kind") if s.get("kind") in KIND_TF else "1d"
        z = s.get("sizing") or {}; self.slots = z.get("max_slots") or 10; self.principal = float(z.get("budget_usd") or 50000)
        self.pos_usd = float(z.get("position_usd") or z.get("global_slot_usd") or self.principal / self.slots); self.owner = f"lazarus:{s.get('account')}"
        self.label = s.get("label")
    def scan(self, hub, ctx):
        if LZ not in sys.path: sys.path.insert(0, LZ)
        from lazarus import signals
        C, SC, I, health = inputs(ctx["now"]); fn = signals.resolve(self.s)
        if fn is None: return []
        out = []
        for f in fn(I):
            if not signals.valid_fire(f) or (f.get("shadow") and self.s.get("state") == "live") or f.get("size_class") == "log_only": continue
            px = f.get("close") or f.get("ref_price")
            if not px:
                b = hub.equity(f["sym"])
                if isinstance(b, Missing): continue      # no price evidence: cannot size, not a negative signal
                px = float(b.c[-1])
            out.append(Signal(f["sym"], f["key"], float(px), 0.0, meta=dict(plan=f.get("plan") or {}, fire_bar=str(f.get("fire_bar")), strategy=f.get("strategy"))))
        return out
    def exit_reason(self, hub, pos, ctx):
        """Lazarus plan semantics: stop_pct from entry; T1 (+first_target_pct) sells sell_fraction, rest floors at entry
        (trailK: peak - K*ATR, floored at entry); time exit after max_bars of the sleeve's bar kind."""
        pl = (pos.get("meta") or {}).get("plan") or {}; b = hub.equity(pos["symbol"], KIND_TF.get(self.tf, "1d"))
        mb = pl.get("max_bars")
        if isinstance(b, Missing): return "time" if mb and pos.get("bars_held", 0) >= int(mb) else None
        px, e = float(b.c[-1]), float(pos["avg"])
        st = float(pl.get("stop_pct") or 99)
        st = st if st < 99 else DISASTER_STOP   # L-134/L-147 parity: every md2-owned Lazarus lot carries the 15% disaster stop
        if px <= e * (1 - st / 100): return f"stop -{st:g}%"
        t1 = pl.get("first_target_pct")
        if t1 and not pos.get("t1_done") and px >= e * (1 + float(t1) / 100):
            fr = float(pl.get("sell_fraction") or 1)
            return f"T1 +{t1}%" if fr >= 1 else ("partial", fr, f"T1 +{t1}% sell {fr}")
        if pos.get("t1_done"):
            rest = str(pl.get("rest") or "time"); floor = e
            if rest.startswith("trail"):
                a = ind.atr(b.h, b.l, b.c)[-1]; floor = max(e, pos.get("peak", px) - int(rest[-1]) * a)
            if px <= floor: return f"rest {rest} <= {floor:.2f}"
        if self.lz_id.startswith("s_mn_"):
            why = midna_exit(self.lz_id, pos, px, b, ctx["now"])
            if why: return why
        if mb and pos.get("bars_held", 0) >= int(mb): return f"time {mb} bars"
        return None

def load():
    with open(f"{LZ}/config/sleeves.json") as fh: SC = json.load(fh); out, cat = [], []
    for s in SC["sleeves"]:
        live = bool(s.get("enabled")) and s.get("state") in ("live", "shadow")   # Lazarus "on" = enabled (64 live + 4 shadow); md2 runs all as shadow
        st, why = ("installed", "") if live else ("off", f"off in Lazarus (state={s.get('state')}, enabled={s.get('enabled')}): kept off, not counted")
        if live: out.append(LazarusSleeve(s))
        src = s.get("source") or {}
        cat.append(dict(sid="lz_" + s["id"], source="lazarus", family=s.get("kind"), strategy=s.get("label"), entry=json.dumps(s.get("entry"))[:300],
                        exit=json.dumps(s.get("exit"))[:300], data=f"{src.get('producer')} :: {src.get('file')}", status=st, reason=why, merged_into=None,
                        origin=f"lazarus-desk@{(pinned_sha() or '')[:7]}:config/sleeves.json#{s['id']}"))
    return out, cat
