"""Griffith R4 factor candidates — the parallel strategy lab's five monthly books and the tournament's two daily
candidates, decided by the vendored, hash-pinned source functions (agentic-trading-desk main @4c8c179c):

  r4_parallel_strategy_lab.py   evaluate_cross_section (XSMOM_12_1 / XSMOM_6_1 / HIGH52: features on completed bars at
                                or before the cutoff, >= 10 synchronized peers, the top half by 60-day median dollar
                                volume, the top decile by score, ties by symbol) and evaluate_etf_candidate
                                (ETF_TSMOM_12M: 252-session return > 0; ETF_SMA10: month-end close > the mean of
                                the last 10 month-end closes; the frozen 17-ETF basket);
  strategy_tournament.py        evaluate_daily_candidate (SIMPLE_TREND: close > SMA200 and SMA50 > SMA200;
                                LIQUID_MOMENTUM_TREND: that plus close[-22]/close[-253] - 1 > 0 and 20-day average
                                dollar volume >= $20M).
The source runs them as shadow research on its SCOPE evidence (feed griffith_iex_1d: the 552-name universe's Alpaca
IEX raw daily bars): r4_parallel_materializer decides at every SPY month end and books the selected names equally
weighted for 21 sessions at 10 bps per side; r4_candidate_evidence observes every name every completed session and
books each observation's 20-session close-to-close return. This module forward-tests exactly those rules:

  monthly books   at the first pass of each month (the previous month's last SPY bar is the cutoff, as the
                  materializer's month ends): the source selection; the book is rebalanced to equal weights over
                  the selected names (names not selected go to zero; an empty or unavailable selection is all
                  cash — the materializer's "WAIT is not an invested outcome"); 10 bps per side (its
                  adverse_one_way_bps). Rebalance children retry on the month's first 5 sessions. A month is
                  decided only on a tape carrying 99% of the names a tape can carry at the cutoff (coverage(),
                  EQ-02); until then it waits, undecided, a blocker on the record, and the next pass asks again.
  daily books     each session, every eligible name observed SETUP on the last completed bar and not held opens
                  one 20-session cohort at the open: a fixed slot of capital / 550 (the universe), exited at the
                  official close (market-on-close) of its 20th session (the observation bar + 20, the study's
                  exit bar).

Gone under the cutover doctrine: nothing desk-wide was applied to these candidates (offline shadow authority); the
tournament's promotion gates are research bookkeeping, not trading rules.

Named divergences:
  * entries trade the next regular open after the completed decision bar (the studies book the decision bar's own
    close, which a completed-bar decision cannot trade); monthly books hold until the next month's rebalance
    (19-23 sessions) where the materializer's label measured exactly 21;
  * daily books: one cohort per name at a time (an observation on a held name does not add a second cohort), a
    fixed equal slot per universe name (the source books unsized per-observation returns);
  * the tape falls back to Yahoo daily bars without Alpaca credentials (see desk/feedlib/griffith.py)."""
from ... import calendar as cal
from ...contract import Intent, OrderSpec, Sleeve, SleeveConfig
from ...feedlib import griffith as tape
from ...util import et_date
from .griffith import FEED, SOURCE, vendored

MONTHLY = {"griffith_xs_mom_12_1": "XSMOM_12_1_MONTHLY_1_0_0", "griffith_xs_mom_6_1": "XSMOM_6_1_MONTHLY_1_0_0",
           "griffith_52w_high_rs": "HIGH52_MONTHLY_1_0_0", "griffith_etf_tsmom12": "ETF_TSMOM_12M_1_0_0",
           "griffith_etf_sma10m": "ETF_SMA10_MONTHLY_1_0_0"}
DAILY = {"griffith_simple_daily_trend": "SIMPLE_TREND_1_0_0",
         "griffith_liquid_momentum_trend": "LIQUID_MOMENTUM_TREND_1_0_0"}
LAB = dict(SOURCE, path="r4_parallel_strategy_lab.py", blob="224b31c200b277bc82fefac552ff22b01a51cdb4")
TOURNAMENT = dict(SOURCE, path="strategy_tournament.py", blob="a7ef5ee9a901899315711e703d99586c9a31f87d")
ONE_WAY_BPS = 10.0          # r4_parallel_materializer.run(adverse_one_way_bps=10.0)
RETRY_SESSIONS = 5
HORIZON = 20                # r4_candidate_evidence.HORIZON
UNIVERSE_SLOTS = 550        # the SCOPE universe's equity names (552 less the two accounting-only rows)
COVERAGE = 0.99             # a month is decided only on a tape carrying 99% of the names a tape can carry (EQ-02)
# The SCOPE names no exchange lists: neither nasdaqlisted.txt (sha256 59ac9b74ff66...) nor otherlisted.txt
# (94335ed3f4ab...) of Nasdaq Trader's symbol directory, created 2026-10-23 21:31 ET, names them. They are names traded
# over the counter, which IEX never prints (ABBNY, IMPUY, ...), and names delisted or renamed (SQ is XYZ, SMAR went
# private). No tape carries them at a cutoff: the record's IEX tape of 2026-10-22 held 534 of the 550 names, 16
# missing (the griffith scanners' state), so 99% of all 550 could never be met on the source's own tape.
NOT_LISTED = frozenset((
    "ABBNY", "AIXXF", "ALRIB", "ALTM", "APLS", "ARRNF", "BESIY", "BITF", "CTRA", "CYBR", "DRO", "EA", "ENAFF",
    "FLTCF", "FREY", "GOEV", "IMPUY", "IQEPF", "LITM", "MAG", "NYNOF", "QRVO", "REEMF", "SIVEF", "SLOIF", "SMAR",
    "SMTOY", "SQ", "TOWCF", "WBD"))


def expected_names(version_id):
    """the names a complete tape carries at a cutoff: the SCOPE universe less NOT_LISTED (the ETF books: the frozen
    basket's names in it; the source tape never stored XLB, XLRE, XLY or IEF), sorted."""
    names = set(tape.tape_symbols()) - NOT_LISTED
    if version_id.startswith("ETF_"):
        names &= set(vendored().r4_parallel_strategy_lab.ETF_BASKET)
    return sorted(names)


def coverage(version_id, bars, cutoff, source):
    """EQ-02: the share of expected_names the tape carries at `cutoff` (bars: {SYM: epoch bars}). 2026-10-16 the
    keyless desk's Yahoo fallback carried 47 of the 550 names and the books bought 3-name (ETF: 4-name) months.
    On the source's own IEX tape a name counts when the load carries it at or before the cutoff: that load is all or
    nothing (a failed request raises and the feed serves nothing), so a thin name IEX did not print on the cutoff day
    is the venue's answer, which the source's cross-section leaves out, not missing data. On the consolidated
    fallback, which serves a refused name its stale cache or nothing, a name counts with its cutoff bar."""
    want = expected_names(version_id)
    day = cutoff[:10]
    have = []
    for s in want:
        stamp = None
        for b in reversed(bars.get(s) or ()):
            stamp = tape.iso(b["t"])
            if stamp <= cutoff:
                break
            stamp = None
        if stamp is not None and (source == tape.SRC or stamp[:10] == day):
            have.append(s)
    n, k = len(want), len(have)
    missing = sorted(set(want) - set(have))
    return {"cutoff": cutoff, "source": source, "names": n, "covered": k, "share": round(k / n, 4) if n else 0.0,
            "need": COVERAGE, "ok": bool(n) and k >= COVERAGE * n - 1e-9, "n_missing": len(missing),
            "missing": missing[:25]}


def month_end_cutoff(spy_rows, session):
    """the materializer's month end for the month before `session`: SPY's last bar stamp of that month."""
    prev = [r["t"] for r in spy_rows if str(r["t"])[:7] < session[:7]]
    return prev[-1] if prev else None


def monthly_selection(version_id, rows, cutoff):
    """r4_parallel_materializer._decision's selection over the panel at `cutoff` (rows: {SYM: raw source bars})."""
    V = vendored()
    lab = V.r4_parallel_strategy_lab
    if version_id.startswith("XSMOM") or version_id == "HIGH52_MONTHLY_1_0_0":
        result = lab.evaluate_cross_section(version_id, rows, cutoff)
        return list(result.get("selected") or []), result.get("status")
    arms = [s for s in sorted(lab.ETF_BASKET)
            if lab.evaluate_etf_candidate(version_id, s, rows.get(s, []), cutoff).get("status") == "SETUP"]
    return arms, ("SETUP" if arms else "WAIT")


def _px(q):
    q = q or {}
    return q.get("ask") or q.get("last")


class _Base(Sleeve):
    def __init__(self):
        self.engine = None

    def bind(self, engine):
        self.engine = engine

    def _stored(self):
        if self.engine is None:
            return {}
        return self.engine.store.sleeve_get(self.CONFIG.sleeve_id) or {}

    def quote_universe(self, now, book):
        st = self._stored()
        names = [i.split(":", 1)[1] for i in book.positions if i.startswith("EQ:")]
        return sorted(set(names) | set(st.get("targets") or {}) | set(st.get("entries") or []))


class R4MonthlyBook(_Base):
    """one of the parallel lab's monthly candidates, rebalanced to its equal-weight selection each month."""

    def __init__(self, sleeve_id, version_id):
        super().__init__()
        self.version_id = version_id
        etf = version_id.startswith("ETF_")
        self.CONFIG = SleeveConfig(
            sleeve_id=sleeve_id, family="griffith_factor", cadence_s=300,
            universe=tuple(tape.tape_symbols()), needs={"feeds": [FEED], "quotes": {"source": "equity"}},
            schedule="rth", params={"version_id": version_id, "cost_bps": ONE_WAY_BPS,
                                    "selection": "ETF basket" if etf else "top decile, top half by liquidity"},
            source=dict(LAB, spec=version_id), state_schema={"month": "str|None", "targets": "dict"})

    def _fallback_month(self, st):
        """the month was decided on the keyless fallback tape (Yahoo, a named divergence) and the desk now reads the
        source's own IEX tape: that month is decided again on it, once. 2026-10-16 the fallback carried 47 of the
        550 names and the October selections froze on it (the ETF books held the only four basket ETFs it had)."""
        hub = getattr(self.engine, "hub", None) if self.engine is not None else None
        return st.get("tape_source") == "yahoo" and getattr(hub, "alpaca", None) is not None

    def wants_tape(self, now):
        st = self._stored()
        return et_date(now)[:7] != st.get("month") or self._fallback_month(st)

    def signal(self, view):
        st = dict(view.state or {})
        session = view.session
        t = view.extra.get(FEED)
        again = st.get("month") == session[:7] and st.get("tape_source") == "yahoo" and isinstance(t, dict) \
            and t.get("source") == tape.SRC
        if st.get("month") != session[:7] or again:
            bars = t.get("bars") if isinstance(t, dict) else None
            if not bars or "SPY" not in bars:
                self._st = st
                return []
            cutoff = month_end_cutoff(tape.raw_rows(bars["SPY"]), session)
            if cutoff is None:
                self._st = st
                return []
            cov = coverage(self.version_id, bars, cutoff, t.get("source"))
            st["coverage"] = dict(cov, session=session)
            if cov["ok"]:
                rows = {s: tape.raw_rows(bl) for s, bl in bars.items()}
                selected, status = monthly_selection(self.version_id, rows, cutoff)
                w = 1.0 / len(selected) if selected else 0.0
                st.update(month=session[:7], cutoff=cutoff, status=status, first_session=session, tries=[],
                          targets={s: w for s in selected}, tape_source=t.get("source"))
                if again:                              # fresh order keys: the fallback's rebalance children filled
                    st["rekey"] = tape.SRC
                else:
                    st.pop("rekey", None)
            elif not again:                            # the month waits, undecided: the next pass asks again
                self._st = st
                why = "TAPE_COVERAGE: %d of %d names at the %s cutoff (%s tape), under %d%%" % (
                    cov["covered"], cov["names"], cutoff[:10], cov["source"], round(COVERAGE * 100))
                return [Intent("signal", "SPY", reason=("blocker: " + why)[:300],
                               meta={"blocker": "TAPE_COVERAGE", "coverage": cov},
                               signal_key="blk:coverage:%s:%s" % (cutoff[:10], session))]
            # else: an incomplete source tape leaves the fallback's month (its targets and retries) until a full one
        targets = st.get("targets") or {}
        tries = list(st.get("tries") or [])
        sessions_in = cal.trading_days_between(st.get("first_session") or session, session) + 1
        held = {i.split(":", 1)[1]: float(p["qty"]) for i, p in view.positions.items() if i.startswith("EQ:")}
        names = [s for s in sorted(set(held) | set(targets)) if targets.get(s, 0.0) > 0 or held.get(s, 0.0) != 0]
        intents = []
        if session not in tries and sessions_in <= RETRY_SESSIONS and names \
                and all(_px(view.quotes.get(s)) for s in names):         # sized on live quotes (next pass if not yet)
            tries.append(session)
            key = st.get("cutoff") + (":" + st["rekey"] if st.get("rekey") else "")
            for s in names:
                w = targets.get(s, 0.0)
                intents.append(Intent("target", s, weight=w, signal_key=f"{s}:{key}", price_hint=_px(view.quotes[s]),
                                      reason=f"{self.version_id} rebalance at {key}: weight {w:.4f}",
                                      order=OrderSpec(window_s=1800)))
        st["tries"] = tries
        self._st = st
        return intents

    def update_state(self, view, intents):
        return getattr(self, "_st", None)


class R4DailyCandidate(_Base):
    """a tournament daily candidate: each SETUP observation opens a 20-session cohort in a fixed slot."""

    def __init__(self, sleeve_id, version_id):
        super().__init__()
        self.version_id = version_id
        self.CONFIG = SleeveConfig(
            sleeve_id=sleeve_id, family="griffith_factor", cadence_s=300, universe=tuple(tape.tape_symbols()),
            needs={"feeds": [FEED], "quotes": {"source": "equity"}}, schedule="rth",
            params={"version_id": version_id, "horizon_sessions": HORIZON, "slots": UNIVERSE_SLOTS},
            source=dict(TOURNAMENT, spec=version_id), state_schema={"observed": "str|None", "entries": "list"})

    def wants_tape(self, now):
        return self._stored().get("observed") != et_date(now)

    def observe(self, bars):
        """evaluate_daily_candidate on each eligible name's completed bars -> SETUP names, universe order."""
        V = vendored()
        out = []
        for s in tape.tape_symbols():
            bl = bars.get(s)
            if not bl:
                continue
            r = V.strategy_tournament.evaluate_daily_candidate(self.version_id, tape.raw_rows(bl))
            if r.get("status") == "SETUP":
                out.append(s)
        return out

    def signal(self, view):
        st = dict(view.state or {})
        now, session = float(view.now), view.session
        intents = []
        held = {i.split(":", 1)[1]: p for i, p in view.positions.items() if i.startswith("EQ:") and float(p["qty"]) > 0}
        pending = {po["inst"].split(":", 1)[1] for po in view.extra.get("pending_orders") or []}
        if st.get("observed") != session:
            t = view.extra.get(FEED)
            bars = t.get("bars") if isinstance(t, dict) else None
            if bars:
                setups = self.observe(bars)
                obs = str(tape.iso(max(bl[-1]["t"] for bl in bars.values())))[:10]
                st.update(observed=session, obs=obs, setups=len(setups), tape_source=t.get("source"),
                          entries=[s for s in setups if s not in held and s not in pending])
        slot = float(self.CONFIG.capital) / UNIVERSE_SLOTS
        waiting = []
        for s in st.get("entries") or []:
            px = _px(view.quotes.get(s))
            if s in held:
                continue
            if not px:                                    # entries trade on a live quote; the next pass retries
                waiting.append(s)
                continue
            intents.append(Intent("enter", s, notional=slot, price_hint=px, signal_key=f"{s}:{st['obs']}:obs",
                                  reason=f"{self.version_id} SETUP on {st['obs']}: 20-session cohort",
                                  order=OrderSpec(window_s=3600), meta={"observation": st["obs"]}))
        st["entries"] = waiting
        if (cal.minutes_to_close(now) or 99) <= 25:
            for s, p in held.items():
                n = cal.trading_days_between(float(p.get("opened_at") or now), now) + 1
                if n >= HORIZON:
                    intents.append(Intent("exit", s, signal_key=f"{s}:{p.get('opened_at')}:h{HORIZON}",
                                          reason=f"{self.version_id} cohort session {n} of {HORIZON}: "
                                                 "exit at the close",
                                          order=OrderSpec(type="market", tif="cls", window_s=3600)))
        self._st = st
        return intents

    def update_state(self, view, intents):
        return getattr(self, "_st", None)


def sleeves():
    return [R4MonthlyBook(sid, v) for sid, v in MONTHLY.items()] + \
        [R4DailyCandidate(sid, v) for sid, v in DAILY.items()]
