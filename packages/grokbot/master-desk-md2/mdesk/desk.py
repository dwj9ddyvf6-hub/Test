"""md2 core: one scheduler pass = data once -> exits first -> manage -> plan (Best Setups when slots bind) -> entries
-> reconcile -> snapshot. Single writer (the ledger), idempotent ids, restart = ledger replay."""
import os, sys, json, time, math, traceback, hashlib, re
OCC = re.compile(r"^([A-Z0-9.]+)(\d{6})([CP])(\d{8})$")
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from .ledger import Ledger, cid as mkcid
from .fsm import Book, FLAT, PENDING, OPEN, EXITING
from .data import DataHub, Missing
from .broker import ShadowBroker, BrokerError
from . import bestsetups as BSX
ET = ZoneInfo("America/New_York"); ROOT = "/workspace/desk2"
TFSEC = {"1h": 3600, "1d": 86400, "4h": 14400, "1w": 604800}
TF2IV = {"1h": "1h", "1d": "1d", "1w": "1wk"}
REVALIDATE_ATR = 3.0
ENTRY_TRIES = 3          # E13 (L-46): a broker refusal/void no longer burns the signal - bounded re-attempts, each re-validated
WORKING = {"accepted", "new", "pending_new", "partially_filled", "accepted_for_bidding", "pending", "held", "calculated",
           "done_for_day", "stopped", "suspended", "pending_replace", "replaced", "pending_cancel"}   # E14 (L-49): not final   # Edge 4/9: an entry is re-checked against the price it will actually fill at

def rth(now):
    d = datetime.fromtimestamp(now, ET)
    return d.weekday() < 5 and (9 * 60 + 30) <= d.hour * 60 + d.minute < 16 * 60

POS_FIELDS = ("condor", "entry_credit", "spread", "entry_debit", "expiry", "occ", "box_lo", "box_hi", "datr14_prior", "entry_spot", "kind", "debit")
def _pos_fields(it):
    """the entry-intent fields muse's journal carries into the sleeve's position view (runtime/journal.positions_from_journal)."""
    d = dict(exit_rules=it.get("exit_rules"), stop_px=it.get("stop_price"), target=it.get("target"))
    d.update({k: it[k] for k in POS_FIELDS if it.get(k) is not None}); return d

def _epoch(t):
    if isinstance(t, (int, float)): return float(t)
    return datetime.fromisoformat(str(t).replace("Z", "+00:00")).timestamp()

class Desk:
    def __init__(self, sleeves, ledger_path=f"{ROOT}/state/ledger.sqlite", hub=None, broker=None, muse=None, muse_cache=None,
                 snapshot=f"{ROOT}/terminal/state.json", use_bs=False, clock=time.time, marks=None, force_open=False):
        self.sleeves = {s.sid: s for s in sleeves}; self.L = Ledger(ledger_path); self.hub = hub or DataHub(); self.broker = broker or ShadowBroker()
        self.muse = {s.sid: s for s in (muse or [])}; self.mcache = muse_cache; self.snapshot_path = snapshot; self.use_bs = use_bs
        self.clock = clock; self.marks_fn = marks; self.force_open = force_open; self._t0 = time.time(); self._lat = []; self._muse_reads = {}; self._muse_sig = {}; self._muse_full = {}; self.muse_skipped = 0
        self.book = Book.replay(self.L); self.alerts = []; self.plan = {}; self.metrics = {}; self.errors = {}; self.last_muse = {}
        for sid, s in list(self.sleeves.items()) + list(self.muse.items()):   # fund each sleeve's virtual principal once (idempotent)
            self._emit([dict(sleeve=sid, kind="fund", cid=f"md2-fund-{sid}", body=dict(amount=float(getattr(s, "principal", 0) or 0)))])

    # ---------- ledger helpers ----------
    def _emit(self, rows):
        n = self.L.append_many(rows)
        if n:
            for e in self.L.events(since=self.book.seq): self.book.apply(e)
        return n

    def _mark(self, sleeve, sym):
        if self.marks_fn: return self.marks_fn(sym)
        own = getattr(self.sleeves.get(sleeve), "mark", None)   # a sleeve with its own intraday feed (t_kz_sweep) marks its own symbols
        if own: return own(self.hub, sym)
        if sym.endswith("USDT"): b = self.hub.okx_4h(sym.replace("USDT", "-USDT"))
        elif sym.endswith("-USD"): b = self.hub.coinbase_1d(sym)
        else: b = self.hub.equity(sym)
        return None if isinstance(b, Missing) else float(b.c[-1])

    def _held_view(self, sleeve, sym, p):
        """position + data-derived bars_held / peak (no per-bar ledger writes)."""
        s = self.sleeves.get(sleeve); v = dict(p, symbol=sym)
        tf = getattr(s, "tf", "1d"); ft = p.get("fill_ts") or p.get("entry_ts") or 0
        if tf in TF2IV and not sym.endswith(("USDT", "-USD")):
            b = self.hub.equity(sym, TF2IV[tf])
            if not isinstance(b, Missing):
                m = b.t > ft; v["bars_held"] = int(m.sum()); v["peak"] = float(max([p.get("avg", 0)] + list(b.h[m])))
        elif tf == "4h": v["bars_held"] = int((self.clock() - ft) // 14400)
        return v

    def _venue_open(self, sym, now):
        return self.force_open or sym.endswith(("USDT", "-USD")) or rth(now)

    # ---------- pass ----------
    def run_pass(self):
        t0 = self._t0 = time.time(); self._lat = []; c0 = time.process_time(); now = self.clock(); self.hub.new_pass(); self.alerts = []; w0 = self.L.writes
        if self.mcache: self.mcache.new_pass()
        self.recover(now)
        n_exit = self.exits(now)
        n_ent = self.entries(now)
        n_muse = self.run_muse(now)
        rec = self.reconcile()
        self.metrics = dict(pass_wall_s=round(time.time() - t0, 3), pass_cpu_s=round(time.process_time() - c0, 3), ledger_writes=self.L.writes - w0,
                            exits=n_exit, entries=n_ent, order_lat_ms=dict(n=len(self._lat), max=round(max(self._lat, default=0) * 1e3, 1), first=round(self._lat[0] * 1e3, 1) if self._lat else None), muse_intents=n_muse, muse_skipped_unchanged=self.muse_skipped, data=dict(self.hub.stats), recon=rec, at=now)
        self.snapshot(now); return self.metrics

    def recover(self, now):
        """after a crash: pending/exiting orders are resolved. Shadow: deterministic re-fill at the mark (same cid -> same event ids)."""
        for (sl, sym), p in list(self.book.open_positions().items()):
            if p["state"] == PENDING:
                if not self._venue_open(sym, now): continue
                mk = self._mark(sl, sym); q = float(p.get("meta", {}).get("qty", 0) or 0)   # sign = side: sell-to-open/short intents carry a negative qty
                r = self.broker.lookup(p["cid"]) or self._submit(p["cid"], sym, "buy" if q >= 0 else "sell", q, mk)
                self._apply_fill(sl, sym, p["cid"], "entry", r)
            elif p["state"] == EXITING:
                if not self._venue_open(sym, now): continue
                mk = self._mark(sl, sym); r = self.broker.lookup(p["exit_cid"]) or self._submit(p["exit_cid"], sym, "sell" if p["qty"] > 0 else "buy", p["qty"], mk)   # a short is closed by a buy
                self._apply_fill(sl, sym, p["exit_cid"], "exit", r)

    def _submit(self, cid, sym, side, qty, mark, fee_bps=0.0):
        try: return self.broker.submit(cid, sym, side, qty, mark, fee_bps)
        except BrokerError as e: self.alerts.append(dict(level="warn", what=f"broker error {cid}: {e}")); return None

    def _next_cid(self, sl, sym, key, leg):
        """E13 (L-46/L-51): attempt-numbered cid. A voided attempt gets a NEW id on retry (a resend under a voided id was a no-op ->
        refused exits were never re-sent, and a re-used exit id could drive an illegal exiting->flat transition)."""
        void = "exit_void" if leg == "EX" else "entry_void"; n = 0
        while self.L.has(mkcid(sl, sym, key, leg, n), void): n += 1
        return mkcid(sl, sym, key, leg, n), n

    def _apply_fill(self, sl, sym, cid, leg, r):
        if r is None: return False   # broker error: stays pending/exiting, retried next pass with the SAME cid
        self._lat.append(time.time() - self._t0)
        st = r.get("status")
        if st in WORKING: return False   # E14: working at the broker - recover() reads it back next pass by the same cid
        p = self.book.pos.get((sl, sym)) or {}
        want = float((p.get("meta") or {}).get("qty", 0) or 0) if leg == "entry" else float(p.get("qty", 0) or 0)
        if "filled_abs" in r:   # real broker read-back: unsigned filled qty -> position-signed; partial fills honoured (L-56)
            fq = math.copysign(float(r["filled_abs"]), want or 1.0)
            if fq and (st == "filled" or leg == "entry"): r = dict(r, status="filled", qty=fq)
            elif fq and leg == "exit":   # partial exit then cancel/expire: book the filled part, re-arm the rest
                self._emit([dict(sleeve=sl, kind="exit_void", symbol=sym, cid=cid, body=dict(reason=f"partial {fq} of {want}: {st}")),
                            dict(sleeve=sl, kind="adjust_filled", symbol=sym, cid=cid + "-pf", body=dict(dqty=-fq, price=r["price"], fee=r.get("fee", 0)))]); return False
        if r.get("status") == "filled":
            self._emit([dict(sleeve=sl, kind=f"{leg}_filled", symbol=sym, cid=cid, body=dict(qty=r["qty"], price=r["price"], fee=r.get("fee", 0), venue=self.broker.mode))]); return True
        self._emit([dict(sleeve=sl, kind=f"{leg}_void", symbol=sym, cid=cid, body=dict(reason=r.get("reason") or r.get("status")))]); return False

    def exits(self, now):
        n = 0
        for (sl, sym), p in list(self.book.open_positions().items()):
            s = self.sleeves.get(sl)
            if s is None or p["state"] != OPEN: continue
            try: why = ("retired: replaced by genuine Ausar desk" if getattr(s, "exit_only", False)
                        else s.exit_reason(self.hub, self._held_view(sl, sym, p), dict(now=now)))
            except Exception as e: self.errors[sl] = f"exit_reason {type(e).__name__}: {e}"[:200]; self.alerts.append(dict(level="warn", what=f"{sl} exit error")); continue
            if not why or not self._venue_open(sym, now): continue
            mk = self._mark(sl, sym)
            if isinstance(why, tuple):   # partial: ('partial', fraction, reason)
                q = math.floor(p["qty"] * why[1]); c = mkcid(sl, sym, p.get("signal_key"), "PX", 0)
                if q > 0 and not self.L.has(c, "adjust_filled") and mk:
                    self._emit([dict(sleeve=sl, kind="adjust_filled", symbol=sym, cid=c, body=dict(dqty=-q, price=mk, reason=why[2])),
                                dict(sleeve=sl, kind="note", symbol=sym, cid=c + "-t1", body=dict(t1_done=True))]); n += 1
                continue
            if not mk: self.alerts.append(dict(level="warn", what=f"{sl}: exit due on {sym} but no mark (retried next pass)")); continue
            c, _ = self._next_cid(sl, sym, p.get("signal_key"), "EX")
            if not self._emit([dict(sleeve=sl, kind="exit_sent", symbol=sym, cid=c, body=dict(reason=why))]): continue
            self._apply_fill(sl, sym, c, "exit", self._submit(c, sym, "sell" if p["qty"] > 0 else "buy", p["qty"], mk, getattr(s, "fee_bps", 0) or 0)); n += 1   # E13: a short is covered by a buy
        return n

    def entries(self, now):
        n = 0; self.plan = {}
        cands = {}
        for sid, s in self.sleeves.items():
            if not hasattr(s, "scan") or getattr(s, "exit_only", False): continue
            try:
                if hasattr(s, "targets"): n += self.rebalance(s, now); continue
                sig = s.scan(self.hub, dict(now=now))
            except Exception as e:
                self.errors[sid] = f"scan {type(e).__name__}: {e}"[:200]; self.alerts.append(dict(level="warn", what=f"{sid} scan error (sleeve isolated; others continue)")); continue
            self.errors.pop(sid, None)
            held = {k[1] for k in self.book.open_positions(sid)}
            fresh, seen = [], set(held)
            for x in sorted(sig, key=lambda x: -x.score):   # one position per (sleeve, symbol): first/best signal wins this pass
                if x.symbol in seen: continue
                c, na = self._next_cid(sid, x.symbol, x.key, "EN")
                if na >= ENTRY_TRIES or self.L.has(c, "entry_sent"): continue
                seen.add(x.symbol); fresh.append(x)
            if fresh: cands[sid] = fresh
        need_bs = {x.symbol for sid, xs in cands.items() for x in xs if len(xs) > self._free(sid)}
        bs = BSX.rank(sorted(need_bs)) if (self.use_bs and need_bs) else {}
        for sid, xs in cands.items():
            s = self.sleeves[sid]; free = self._free(sid); binds = len(xs) > free
            xs.sort(key=lambda x: ((bs.get(x.symbol) or {}).get("rank", 4) if binds else 0, -x.score))
            take = xs[:max(free, 0)]
            self.plan[sid] = dict(candidates=len(xs), free_slots=free, cap_binds=binds, ranked_by="best_setups" if binds else "sleeve_score",
                                  take=[dict(sym=x.symbol, px=x.px, bs=(bs.get(x.symbol) or {}).get("tier")) for x in take][:25])
            for x in take:
                if not self._venue_open(x.symbol, now): continue   # planned; filled at the next open venue
                mk = self._mark(sid, x.symbol)
                if not mk: continue                      # no observable price: cannot fill (missing != negative)
                a = x.meta.get("atr")                    # Edge: revalidate at the submission boundary - a fill price more than
                if a and abs(mk - x.px) > REVALIDATE_ATR * a:   # 3 ATR from the signal close means the signal's premise no longer holds
                    self.alerts.append(dict(level="info", what=f"{sid}: {x.symbol} entry skipped, mark {mk:.4g} vs signal {x.px:.4g} > {REVALIDATE_ATR} ATR")); continue
                eq = self.book.cash.get(sid, 0.0); qty = self._size(s, x, eq, mk)
                if qty <= 0: continue
                side = "sell" if x.meta.get("side") == "sell" else "buy"   # native short (opt-in via meta side; only t_kz_sweep sets it)
                if side == "sell": qty = -qty
                c = self._next_cid(sid, x.symbol, x.key, "EN")[0]; meta = dict(x.meta, qty=qty)
                if x.meta.get("atr") and s.family == "public_recipe": meta["stop"] = x.px - 2 * x.meta["atr"]
                if not self._emit([dict(sleeve=sid, kind="entry_sent", symbol=x.symbol, cid=c, body=dict(signal_key=x.key, meta=meta, ref=x.px))]): continue
                self._apply_fill(sid, x.symbol, c, "entry", self._submit(c, x.symbol, side, qty, mk, getattr(s, "fee_bps", 0) or 0)); n += 1
        return n

    def _free(self, sid):
        s = self.sleeves[sid]; return (s.slots or 10) - len(self.book.open_positions(sid))

    def _size(self, s, x, cash, px):
        """sized at the FILL price (mark), fee-funded, never above available sleeve cash."""
        fee = (getattr(s, "fee_bps", 0) or 0) / 1e4; room = max(cash, 0) / (1 + fee)
        if x.qty is not None: usd = min(x.qty * px, room)
        else:
            usd = getattr(s, "pos_usd", None) or s.principal * s.pos_frac
            dv = x.meta.get("dv20")
            if dv and s.dv_cap: usd = min(usd, dv * s.dv_cap)
            usd = min(usd, room)
        q = usd / px
        return math.floor(q * 1e6) / 1e6 if x.symbol.endswith(("USDT", "-USD")) else math.floor(q)

    def rebalance(self, s, now):
        """target-weight books (fixed ETF portfolios). BUY_HOLD: allocate once. MONTHLY: first session of each month."""
        d = datetime.fromtimestamp(now, ET); held = self.book.open_positions(s.sid)
        period = "init" if not held else (d.strftime("%Y-%m") if s.monthly else None)
        if period is None: return 0
        eq = self.book.equity(s.sid, {k[1]: self._mark(s.sid, k[1]) or v["avg"] for k, v in held.items()})
        tg = s.targets(self.hub, eq)
        if isinstance(tg, Missing): self.alerts.append(dict(level="info", what=f"{s.sid}: {tg.reason}")); return 0
        self.plan[s.sid] = dict(targets=tg, period=period)
        if not self._venue_open("SPY", now): return 0
        n = 0
        for sym, q in sorted(tg.items(), key=lambda kv: (kv[1] - (held.get((s.sid, kv[0])) or {}).get("qty", 0))):   # sells before buys
            cur = (held.get((s.sid, sym)) or {}); dq = q - cur.get("qty", 0); mk = self._mark(s.sid, sym)
            if not dq or not mk: continue
            key = f"{sym}|{period}"; c = mkcid(s.sid, sym, key, "RB")
            if cur.get("state") == OPEN:
                if self.L.has(c, "adjust_filled"): continue
                self._emit([dict(sleeve=s.sid, kind="adjust_filled", symbol=sym, cid=c, body=dict(dqty=dq, price=mk, fee=abs(dq) * mk * s.fee_bps / 1e4))]); n += 1
            elif dq > 0:
                c = mkcid(s.sid, sym, key)
                if self._emit([dict(sleeve=s.sid, kind="entry_sent", symbol=sym, cid=c, body=dict(signal_key=key, meta=dict(qty=dq)))]):
                    self._apply_fill(s.sid, sym, c, "entry", self._submit(c, sym, "buy", dq, mk, s.fee_bps)); n += 1
        return n

    def run_muse(self, now):
        if not self.muse or self.mcache is None: return 0
        from .engines.muse import ET as MET
        dt = datetime.fromtimestamp(now, MET); n = 0; self.muse_skipped = 0
        if rth(now) and self.mcache.requests:   # fresh intraday bars for the intraday muse sleeves (one batched call per timeframe)
            from . import warm
            r = warm.intraday(self.mcache, sorted(self.mcache.requests))
            if r.get("error"): self.alerts.append(dict(level="warn", what=f"intraday warm failed: {r['error']} (sleeves fail closed on stale bars)"))
        for sid, s in self.muse.items():
            if now - self.last_muse.get(sid, 0) < s.cadence_s: continue
            self.last_muse[sid] = now
            op = {k[1]: v for k, v in self.book.open_positions(sid).items() if v["state"] == OPEN}
            n += self._muse_host_exits(sid, s, op, now, dt)   # runtime duties muse core performed (flat-by-close, protection stop)
            op = {k[1]: v for k, v in self.book.open_positions(sid).items() if v["state"] == OPEN}
            # the sleeve sees its position exactly as muse's journal rebuilt it: contracts (not share-equivalents) for options,
            # and the stop/target/exit_rules/structure fields its own exit logic reads (they were dropped before -> exits blind)
            pos = [dict(symbol=sym, qty=(v.get("meta") or {}).get("contracts") and math.copysign((v["meta"]["contracts"]), v["qty"]) or v["qty"],
                        avg_price=v["avg"], opened_at=datetime.fromtimestamp(v.get("fill_ts", now), MET).isoformat(), intent_id=v.get("signal_key"),
                        **((v.get("meta") or {}).get("pos_fields") or {})) for sym, v in op.items()]
            # E16 Efficiency: off-session, a sleeve whose every input file, position and cash is unchanged since its last evaluation
            # would recompute the identical result (no venue to act on) - skip it (re-evaluated at least hourly; RTH never skipped).
            sig = None
            if not rth(now) and sid in self._muse_reads:
                sig = (tuple(self.mcache.sig(k) for k in self._muse_reads[sid]), repr(sorted(op.items(), key=str)), round(self.book.cash.get(sid, 0.0), 6))
                if sig == self._muse_sig.get(sid) and now - self._muse_full.get(sid, 0) < 3600: self.muse_skipped += 1; continue
            self.mcache.requests_seen = set()
            its, err = s.evaluate(self.mcache, dt, pos, self.book.cash.get(sid, 0.0), f"{ROOT}/state/muse_journal/{sid}.jsonl")
            self._muse_reads[sid] = sorted(self.mcache.requests_seen); self._muse_full[sid] = now
            self._muse_sig[sid] = (tuple(self.mcache.sig(k) for k in self._muse_reads[sid]), repr(sorted(op.items(), key=str)), round(self.book.cash.get(sid, 0.0), 6)) if not its and not err else None
            if err: self.errors[sid] = err; self.alerts.append(dict(level="warn", what=f"{sid}: {err[:80]}")); continue
            self.errors.pop(sid, None)
            for it in its:
                sym = it["symbol"]; key = it["intent_id"]; p = self.book.pos.get((sid, sym)) or dict(state=FLAT)
                mk = float(it.get("limit_price") or self._muse_mark(sym) or 0) or None
                mult = 100.0 if OCC.match(sym) else 1.0   # US equity options: 100 shares per contract; book qty is share-equivalent
                if it["kind"] == "entry" and p["state"] == FLAT and it["side"] in ("buy", "sell"):
                    if not self._venue_open(sym, now): continue
                    if OCC.match(sym) and not it.get("limit_price"):   # an option needs its own premium: missing data, never a guessed price
                        self.alerts.append(dict(level="warn", what=f"{sid}: option intent {sym} without a premium (missing data; not filled)")); continue
                    sq = float(it["qty"]) * mult * (1 if it["side"] == "buy" else -1)   # sell-to-open / short = negative qty (sim money)
                    c, na = self._next_cid(sid, sym, key, "EN")
                    if na >= ENTRY_TRIES: continue
                    if self._emit([dict(sleeve=sid, kind="entry_sent", symbol=sym, cid=c, body=dict(signal_key=key, meta=dict(qty=sq, contracts=float(it["qty"]) if mult > 1 else None, side=it["side"], reason=str(it.get("reason", ""))[:200], pos_fields=_pos_fields(it))))]):
                        self._apply_fill(sid, sym, c, "entry", self._submit(c, sym, it["side"], sq, mk)); n += 1
                elif it["kind"] == "exit" and p["state"] == OPEN:
                    if not self._venue_open(sym, now): continue
                    c = self._next_cid(sid, sym, key, "EX")[0]
                    if self._emit([dict(sleeve=sid, kind="exit_sent", symbol=sym, cid=c, body=dict(reason=str(it.get("reason", ""))[:200]))]):
                        self._apply_fill(sid, sym, c, "exit", self._submit(c, sym, "sell" if p["qty"] > 0 else "buy", p["qty"], mk)); n += 1
                else:
                    self._emit([dict(sleeve=sid, kind="intent_skipped", symbol=sym, cid=f"md2-sk-{hashlib.sha1((sid + key).encode()).hexdigest()[:16]}",
                                     body=dict(why=f"{it['kind']}/{it['side']} while {p['state']} (one position per sleeve+symbol)"))])
        n += self.settle_expired_options(now)
        return n

    def _muse_mark(self, sym):
        """freshest observed price across the cached timeframes (was: the daily close first, i.e. yesterday's price intraday)."""
        best = None
        for tf in ("1Min", "5Min", "1Day"):
            b = self.mcache.read_bars(sym, tf, 1)
            if b:
                t = _epoch(b[-1].t)
                if best is None or t > best[0]: best = (t, float(b[-1].c))
        return best[1] if best else None

    def _muse_host_exits(self, sid, s, op, now, dt):
        """Duties muse-desk-v2's runtime (not its sleeves) performed: DESIGN 4d flat-by-close at flatten_time_et, and the
        protection stop core placed on fill from the entry intent's stop_price (e.g. qullamaggie_paper's ONLY exit route)."""
        n = 0; e = s.entry if hasattr(s, "entry") else {}
        flat = e.get("flat_by_close") and e.get("flatten_time_et") and dt.weekday() < 5 and dt.strftime("%H:%M") >= e["flatten_time_et"]
        for sym, v in op.items():
            why = None
            if flat: why = f"flat_by_close {e['flatten_time_et']} ET"
            else:
                st = ((v.get("meta") or {}).get("pos_fields") or {}).get("stop_px")
                if st and not OCC.match(sym):
                    mk = self._muse_mark(sym)
                    if mk and ((v["qty"] > 0 and mk <= float(st)) or (v["qty"] < 0 and mk >= float(st))): why = f"protection stop {float(st):g} (mark {mk:g})"
            if not why or not self._venue_open(sym, now): continue
            c = self._next_cid(sid, sym, f"{v.get('signal_key')}|host|{dt:%F}", "EX")[0]
            if self._emit([dict(sleeve=sid, kind="exit_sent", symbol=sym, cid=c, body=dict(reason=why))]):
                self._apply_fill(sid, sym, c, "exit", self._submit(c, sym, "sell" if v["qty"] > 0 else "buy", v["qty"], self._muse_mark(sym))); n += 1
        return n

    def settle_expired_options(self, now):
        """an option still open after its expiry date settles at intrinsic value (underlying daily close on expiry), sim money only."""
        n = 0
        for (sl, sym), p in list(self.book.open_positions().items()):
            m = OCC.match(sym)
            if not m or p["state"] != OPEN or sl not in self.muse: continue
            und, ymd, right, k = m.group(1), m.group(2), m.group(3), int(m.group(4)) / 1000.0
            exp = datetime.strptime("20" + ymd, "%Y%m%d").replace(hour=16, tzinfo=ET)
            if now < exp.timestamp() + 3600: continue
            bars = [b for b in (self.mcache.read_bars(und, "1Day", 10) or []) if datetime.fromtimestamp(b.t if isinstance(b.t, (int, float)) else datetime.fromisoformat(str(b.t)).timestamp(), ET).date() <= exp.date()] if self.mcache else []
            if not bars: self.alerts.append(dict(level="warn", what=f"{sl}: expired {sym} awaits the underlying expiry close (missing data)")); continue
            u = float(bars[-1].c); iv = max(0.0, (u - k) if right == "C" else (k - u))
            c = mkcid(sl, sym, f"expiry:{ymd}", "EX")
            if self._emit([dict(sleeve=sl, kind="exit_sent", symbol=sym, cid=c, body=dict(reason=f"expired {ymd}: intrinsic {iv:.4f} (underlying {u})"))]):
                self._apply_fill(sl, sym, c, "exit", dict(status="filled", price=iv, qty=p["qty"], fee=0.0)); n += 1
        return n

    def reconcile(self):
        """the in-memory book must equal a cold replay of the ledger (determinism), cash never negative, no position without an owner."""
        cold = Book.replay(self.L); bad = []
        if {k: (v["state"], round(v["qty"], 6)) for k, v in cold.pos.items()} != {k: (v["state"], round(v["qty"], 6)) for k, v in self.book.pos.items()}: bad.append("book!=replay")
        for sl, c in cold.cash.items():
            g = getattr(self.sleeves.get(sl), "gross", 1.0) or 1.0
            floor = -(g - 1.0) * float(getattr(self.sleeves.get(sl) or self.muse.get(sl), "principal", 0) or 0) * 1.05 if g > 1 else -1e-6
            if c < floor: bad.append(f"{sl} cash<{'margin floor' if g > 1 else '0'}")
        for (sl, sym) in cold.open_positions():
            if sl not in self.sleeves and sl not in self.muse: bad.append(f"orphan {sl}:{sym}")
        for b in bad: self.alerts.append(dict(level="alert", what=f"reconcile: {b}"))
        return dict(ok=not bad, issues=bad[:10])

    def snapshot(self, now):
        sl = []
        for sid, s in list(self.sleeves.items()) + list(self.muse.items()):
            op = self.book.open_positions(sid)
            sl.append(dict(sid=sid, source=s.source, family=s.family, open=len(op), cash=round(self.book.cash.get(sid, 0), 2),
                           realized=round(self.book.realized.get(sid, 0), 2), error=self.errors.get(sid), plan=self.plan.get(sid)))
        pos = [dict(sleeve=k[0], sym=k[1], state=v["state"], qty=v["qty"], avg=round(v["avg"], 4), since=v.get("fill_ts")) for k, v in self.book.open_positions().items()]
        doc = dict(desk="md2", mode=self.broker.mode, at=now, at_et=datetime.fromtimestamp(now, ET).strftime("%Y-%m-%d %H:%M:%S %Z"), metrics=self.metrics,
                   alerts=self.alerts, sleeves=sl, positions=pos, ledger_events=self.L.count())
        os.makedirs(os.path.dirname(self.snapshot_path), exist_ok=True); tmp = self.snapshot_path + ".tmp"
        json.dump(doc, open(tmp, "w"), default=str); os.replace(tmp, self.snapshot_path); return doc
