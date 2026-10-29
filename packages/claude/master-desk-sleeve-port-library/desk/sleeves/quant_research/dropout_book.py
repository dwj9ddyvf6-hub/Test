"""The six-strategy reconstruction's TopkDropout book on the desk (shared/portfolio.py backtest(mode='dropout') with
shared/dropout.py's selector): each session, from the model scores of the previous completed session, hold the
top-k names, replacing at most n_drop of the worst-ranked holdings with the best-ranked new candidates; sales are
capped at 1% of the 20-session dollar volume, buys share the post-sale cash times the risk degree, every trade is
capped at 1% of that volume and buys are scaled to the affordable cash. Executed at the market from the first pass
of the session (sells first, buys on the following pass)."""
import numpy as np

from ... import calendar as cal
from ...contract import Sleeve, SleeveConfig
from . import common as C
from . import sixai as S


class DropoutBook(Sleeve):
    SID, NAME, STUDY = "", "", ""
    TOPK, NDROP, MIN_HOLD, RISK = 50, 5, 1, 0.95
    BUY_BPS, SELL_BPS = 10.0, 10.0
    SYMBOLS = S.SYMBOLS
    FEED = "qr_scores"
    SOURCE = {}

    def __init__(self):
        self.engine = None
        self.CONFIG = SleeveConfig(
            sleeve_id=self.SID, family="quant_research", cadence_s=300, universe=tuple(self.SYMBOLS),
            capital=1_000_000.0, schedule="rth",
            needs={"feeds": [self.FEED], "quotes": {"source": "equity"}},
            params={"topk": self.TOPK, "n_drop": self.NDROP, "min_hold": self.MIN_HOLD, "risk_degree": self.RISK,
                    "budget_bps": [self.BUY_BPS, self.SELL_BPS], "participation": 0.01,
                    "signal": "previous completed session's model score", "study": self.STUDY},
            source=self.SOURCE, state_schema={"decided": "str", "target": "dict", "entered": "dict", "log": "list"})

    def bind(self, engine):
        self.engine = engine

    def doc(self, root):
        from . import scores
        return scores.read(root)

    def is_signal_date(self, d):
        """sessions whose scores are traded the next session (every session; Kronos: its forecast dates)."""
        return True

    def candidates(self, doc, held):
        sc = doc.get(self.NAME) or {}
        elig = set(doc.get("eligible") or ())
        order = sorted((s for s in sc if s in elig and s not in held), key=lambda s: (-sc[s], s))
        return order[: self.TOPK + self.NDROP]

    def quote_universe(self, now, book):
        held = {i.split(":", 1)[1] for i, p in (book.positions or {}).items() if i.startswith("EQ:")
                and float(p["qty"]) > 0}
        doc = self.doc(self.engine.root) if self.engine is not None else None
        return sorted(held | set(self.candidates(doc, held) if doc else ()))

    def signal(self, view):
        st = dict(view.state or {})
        for k, v in (("log", []), ("entered", {})):
            st.setdefault(k, v)
        self._st = st
        if not cal.is_rth(view.now):
            return []
        d = C.prev_session(view.session)
        if st.get("decided") != d and not self.is_signal_date(d):
            d = st.get("decided")                             # no new scores: finish the last plan, then hold
            if not d:
                return []
        if st.get("decided") != d:
            doc = (view.extra or {}).get(self.FEED)
            if not doc or doc.get("asof") != d or self.NAME not in doc:
                st["log"] = (st["log"] + [{"at": view.session, "why": f"scores for {d} not in"}])[-50:]
                return []
            plan = self.plan(view, doc, d)
            if plan is None:
                return []
            st.update(decided=d, target=plan)
        out, _ = C.rebalance(view, st.get("target") or {}, f"{self.NAME}:{d}", f"{self.SID} TopkDropout on {d}")
        return out

    def plan(self, view, doc, d):
        st = self._st
        syms = list(self.SYMBOLS)
        col = {s: j for j, s in enumerate(syms)}
        N = len(syms)
        sc = doc.get(self.NAME) or {}
        score = np.full(N, np.nan)
        for s, v in sc.items():
            if s in col:
                score[col[s]] = v
        elig = np.zeros(N, dtype=bool)
        for s in doc.get("eligible") or ():
            if s in col:
                elig[col[s]] = True
        held = C.held(view)
        q = np.zeros(N)
        for s, x in held.items():
            if s in col:
                q[col[s]] = x
        sessions = np.zeros(N, dtype=int)
        for s, e in (st.get("entered") or {}).items():
            if s in col:
                sessions[col[s]] = len(C.sessions_between(e, view.session)) - 1
        bid, ask = np.full(N, np.nan), np.full(N, np.nan)
        for s, qt in (view.quotes or {}).items():
            if s in col:
                b, a = qt.get("bid") or qt.get("last"), qt.get("ask") or qt.get("last")
                bid[col[s]], ask[col[s]] = (float(b) if b else np.nan), (float(a) if a else np.nan)
        need = set(held) | set(self.candidates(doc, held))
        if any(not np.isfinite(ask[col[s]]) for s in need if s in col):
            missing = sorted(s for s in need if s in col and not np.isfinite(ask[col[s]]))
            st["log"] = (st["log"] + [{"at": view.session, "why": f"quotes pending {missing[:5]}"}])[-50:]
            return None
        adv = np.full(N, np.nan)
        for s, v in (doc.get("adv20") or {}).items():
            if s in col:
                adv[col[s]] = v
        desired, sel = S.dropout_plan(syms, score, elig, q, sessions, bid, ask, float(view.cash), adv, self.TOPK,
                                      self.NDROP, self.MIN_HOLD, self.RISK, self.BUY_BPS, self.SELL_BPS)
        target = {}
        for j in np.flatnonzero((np.abs(desired - q) > 1e-12) | (q > 1e-12)):
            target[syms[j]] = float(max(desired[j], 0.0))
            if q[j] <= 1e-12 and desired[j] > 1e-12:
                st["entered"][syms[j]] = view.session
        for s in list(st["entered"]):
            if s not in target or target[s] <= 1e-12:
                if held.get(s, 0) <= 1e-12:
                    st["entered"].pop(s, None)
        st["log"] = (st["log"] + [{"at": view.session, "signal": d, "sell": [syms[j] for j in sel["actual_sell"]],
                                   "buy": [syms[j] for j in sel["actual_buy"]]}])[-50:]
        return target

    def update_state(self, view, intents):
        return getattr(self, "_st", None) or dict(view.state or {})
