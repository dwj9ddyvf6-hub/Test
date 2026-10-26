"""Two recorders converted into funded paper books (the owner's ruling D32, 2026-10-26: "Convert where rules exist"):
each trades its source's own printer signal by the Galath printer convention already on the desk, and reads the
producer its monitor read. docs/research/2026-10-26-recorders/CONVERT.md carries the source lines behind each rule.

  mon_galath_tensor2washoutreclaimtransition    the Tensor 2 replica (galath-desk@652db7af src/lib/tensor/engine.ts
      buildTensorReplica) on the watch desk's 1h frame, the default watch list (13 names). Its signal is the source's
      own persisted state (engine.ts 255-259): "buy" from a GREEN_BUY print until a RED / MAGENTA sell, or until the
      close loses EMA21 on a red bar (the buy cancelled). A read counts once the analysis has authority: 200 bars
      on the frame (engine.ts AUTHORITY_BARS, adapter.ts `authority`). Producer: the job mon_galath_tensor (one Node
      run of the vendored stack per completed canonical hour, desk/sleeves/monitor/galath_tensor_mon.py).
  mon_galath_annaphdlocationoverriddenprintergrid  the gospel PhD replay's printer (galath-desk-backup@3e93f984
      scripts/anna-phd-replay.mjs buildAnnaReplica) on daily bars over Anna's census names (115). Its signal persists
      (833-845): "buy" on a CYAN / GREEN print, "sell" on a RED / MAGENTA print or when the close loses EMA200 while
      long. Producer: the job mon_galath_phd (the replay under Node after each close, galath_phd_mon.py).

The convention (desk/sleeves/families/galath.py divergence 8, AnnaPrinter): the printers have no sizing, so each name
holds an equal slot of equity / N names of the book's list; hold while the signal is buy, flat when it is no longer
buy; a completed bar's decision trades at the book's next pass in the session. The book takes up the printer's
current state when it starts, as AnnaPrinter does (a name whose signal is buy is bought, not only a fresh print).

Named divergences (plumbing, not rules):
  1. the books' session passes begin at open+5: a decision on the bar that completed after the close trades then,
     not in the desk's open pass (the heaviest pass of the day; the brief's lean-open rule);
  2. fills: market orders at the book's pass after the decision (the printers name no order type); a name with no
     live equity quote is not bought (an index or a name the equity feed does not print);
  3. a decision not sent by the close of the session after its bar lapses (the producer's next read decides again);
     an order still working for a name holds that name's next decision until it ends.
Removed gates: none (the monitors had none; the producers are the monitors' own jobs)."""
from ... import calendar as cal
from ...contract import Intent, Sleeve, SleeveConfig
from ...util import et_date
from . import galath_phd_mon as PH
from . import galath_tensor_mon as GTM
from . import reads as R

CONVENTION = "galath printer: hold while buy, flat when not; equal slot equity/N; next pass (galath.py divergence 8)"
WINDOW = "rth&open+5:open+400"           # the session passes (divergence 1); open+400 runs past every close
CADENCE = 300
AUTHORITY_BARS = 200                     # galath-desk engine.ts AUTHORITY_BARS: adapter.ts `authority`


def _held(view):
    return {inst.split(":", 1)[1] for inst, p in (view.positions or {}).items()
            if inst.startswith("EQ:") and abs(float(p.get("qty") or 0)) > 1e-12}


def _working(view):
    return {str(o.get("inst") or "").split(":", 1)[-1] for o in (view.extra or {}).get("pending_orders") or []}


def _lapse(day):
    """a decision on a bar of session `day` lapses at the close of the next session."""
    return cal.session_close(cal.next_trading_day(day))


class PrinterBook(Sleeve):
    """the Galath printer convention over a producer's cache: fresh() reads the producer's decisions not yet taken
    ({symbol: decision}, without changing the state); the book sends each decision once, in its session window."""
    LABEL = "printer"

    def __init__(self, spec, schedule, params):
        self.spec = spec
        self.CONFIG = SleeveConfig(sleeve_id=spec.sleeve_id, family="monitor", cadence_s=CADENCE,
                                   universe=tuple(spec.universe), schedule=schedule,
                                   needs={"quotes": {"source": "equity"}},
                                   params=dict(params, convention=CONVENTION, names=len(spec.universe)),
                                   source=dict(spec.source))
        self.engine = None
        self._st = None

    def bind(self, engine):
        self.engine = engine

    def _root(self):
        return getattr(self.engine, "root", None)

    def quote_universe(self, now, book=None):
        """only the names with a buy to send this pass need a quote: the decisions kept and the new ones."""
        st = {}
        if self.engine is not None:
            try:
                st = self.engine.store.sleeve_get(self.CONFIG.sleeve_id) or {}
            except Exception:
                st = {}
        want = {s for s, d in (st.get("todo") or {}).items() if d.get("want") == "long"}
        if cal.is_rth(now):
            want |= {s for s, d in self.fresh(now, st).items() if d["want"] == "long"}
        return sorted(want)

    def fresh(self, now, st):                        # -> {symbol: decision} of the reads not yet decided
        raise NotImplementedError

    def taken(self, now, st, new):                   # records that the reads behind `new` are decided
        raise NotImplementedError

    def signal(self, view):
        st = dict(view.state or {})
        st["todo"] = dict(st.get("todo") or {})
        intents = []
        new = self.fresh(view.now, st)
        self.taken(view.now, st, new)
        if new:
            st["todo"].update(new)
            intents.append(Intent("signal", self.LABEL, reason=("%s: " % self.LABEL + ", ".join(
                "%s %s" % (s, d["signal"] or "none") for s, d in sorted(new.items())))[:300],
                signal_key="%s:%s" % (self.LABEL, max(d["t"] for d in new.values())),
                meta={"decisions": {s: {k: d[k] for k in ("t", "signal", "marker", "want")} for s, d in new.items()}}))
        if cal.is_rth(view.now):
            intents += self._send(view, st)
        self._st = st
        return intents

    def _send(self, view, st):
        held, working = _held(view), _working(view)
        slot = view.equity / len(self.CONFIG.universe)
        out = []
        for s, d in sorted(st["todo"].items()):
            if view.now > d["lapse"]:
                del st["todo"][s]                    # divergence 3: lapsed unsent
                continue
            if s in working:
                continue                             # an order for the name is still working
            why = "%s %s (%s)" % (self.LABEL, d["signal"] or "none", d.get("marker") or "held signal")
            if d["want"] == "long" and s not in held:
                px = float(((view.quotes or {}).get(s) or {}).get("last") or 0)
                if not (px > 0):
                    continue                         # no live quote: kept until it lapses
                out.append(Intent("enter", s, notional=float(slot), price_hint=px, reason=why[:300],
                                  signal_key="%s:%s:%s:buy" % (self.CONFIG.sleeve_id, s, d["t"]),
                                  meta={"bar_t": d["t"], "slot": slot}))
            elif d["want"] == "flat" and s in held:
                out.append(Intent("exit", s, reason=why[:300], signal_key="%s:%s:%s:sell" % (
                    self.CONFIG.sleeve_id, s, d["t"]), meta={"bar_t": d["t"]}))
            del st["todo"][s]
        return out

    def update_state(self, view, intents):
        st, self._st = self._st, None
        return st if st is not None else dict(view.state or {})


class Tensor2Book(PrinterBook):
    """the Tensor 2 replica's signal on the 1h frame (mon_galath_tensor's cache, one read per completed hour)."""
    LABEL = "tensor2"

    def fresh(self, now, st):
        reads = R.read(self._root(), GTM.CACHE, now, GTM.MAX_AGE)
        seen = st.get("seen") or {}
        out = {}
        for s in self.CONFIG.universe:
            r = reads.get(s) or {}
            last = (r.get("tensor2") or {}).get("last")
            if not last or int(r.get("barCount") or 0) < AUTHORITY_BARS:
                continue                             # no read, or a read without the source's authority
            t = int(last["t"])
            if t <= int(seen.get(s) or 0):
                continue
            day = cal._as_date(t / 1000.0)
            out[s] = {"t": t, "signal": last.get("signal"), "marker": last.get("marker"), "c": last.get("c"),
                      "want": "long" if last.get("signal") == "buy" else "flat", "lapse": _lapse(day)}
        return out

    def taken(self, now, st, new):
        if new:
            st["seen"] = dict(st.get("seen") or {}, **{s: d["t"] for s, d in new.items()})


class PhdBook(PrinterBook):
    """the PhD replay's signal on the session's completed daily bar (mon_galath_phd's cache, after each close)."""
    LABEL = "phd"

    def _ran(self, now, st):
        """the session whose replay is written and not yet decided, else None."""
        day = et_date(now)
        if not cal.is_trading_day(day) or now < cal.session_close(day) or st.get("printed") == day:
            return None
        ran = R.read_at(self._root(), PH.CACHE)
        return day if ran is not None and ran >= cal.session_close(day) else None

    def fresh(self, now, st):
        day = self._ran(now, st)
        if day is None:
            return {}
        reads = R.read(self._root(), PH.CACHE, now, PH.MAX_AGE)
        out = {}
        for s in self.CONFIG.universe:
            last = (reads.get(s) or {}).get("last")
            if not last or et_date(int(last["t"]) / 1000.0) != day:
                continue                             # the session's bar is not in the replay
            out[s] = {"t": int(last["t"]), "signal": last.get("signal"), "marker": last.get("marker"),
                      "c": last.get("c"), "want": "long" if last.get("signal") == "buy" else "flat",
                      "lapse": _lapse(day)}
        return out

    def taken(self, now, st, new):
        day = self._ran(now, st)
        if day is not None:
            st["printed"] = day


def _spec(mod, sid):
    return next(s for s in mod.SPECS if s.sleeve_id == sid)


BOOKS = {
    "mon_galath_tensor2washoutreclaimtransition": lambda: Tensor2Book(
        _spec(GTM, "mon_galath_tensor2washoutreclaimtransition"), WINDOW + ",ext&et:16:00-17:30",
        {"frame": GTM.FRAME, "watch": "DEFAULT_WATCH", "producer": "mon_galath_tensor", "signal": "engine.ts 255-259"}),
    "mon_galath_annaphdlocationoverriddenprintergrid": lambda: PhdBook(
        _spec(PH, "mon_galath_annaphdlocationoverriddenprintergrid"), WINDOW + ",after_close+30:after_close+420",
        {"frame": "1d", "list": "scored-events.json census", "producer": "mon_galath_phd",
         "signal": "anna-phd-replay.mjs 833-845"}),
}
