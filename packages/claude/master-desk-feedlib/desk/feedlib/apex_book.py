"""The source's options Book for one live decision (APEX options sleeves, N7 / C7 / the Council's Variance Value).

Pure: the source's sim module arrives as an argument (the vendored desk/vendor/apex/sim.py in the desk; cursor2's own
desk/options/sim.py in the parity harness, which runs this same file in the source tree).

make_live_book(VS) -> LiveBook, a subclass of VS.Book. A source strategy function constructs its Book itself
(`Book(x.dates, x.S, ...)` from its module global) and calls book.run(decide, start); bound in place of that
global, LiveBook.run calls the strategy's own decide() once per step instead of looping over history:

  live step ...... {"legs_live": the sleeve's held contracts, "nav": its equity (or its share), "o12": state}:
                   today = the last date; each held contract becomes a source Leg (units = contracts x 100, signed;
                   its monthly expiry's index; marked at the model price of today, as Book.run marked it); a leg
                   whose expiry is today or earlier is dropped (Book.run settled it before deciding); core = nav -
                   the legs' value; nav_prev = 0 (O12's futures P&L line: the book's marks carry it).
  replay step .... {"t", "core", "nav_prev", "legs": [(is_call, K, exp_i, units, px, tag)], "o12"}: a state the
                   source's own Book.run handed to decide() (the parity harness).
O12's closure state ({"fut", "wait_month"}) is the step's, set in the closure's own dict; its value after the
decision is kept (o12_after). open / close / adjust are the source's, recorded (ops). With a listing (live),
expiry_near / next_expiry choose among the listed monthly expirations (expiry_dates = their third Fridays), an open
takes the listed strike nearest the source's strike and whole contracts (rounded; under one: skipped, recorded),
and an adjustment trades whole contracts."""
import math


def make_live_book(VS):
    import pandas as pd

    class LiveBook(VS.Book):
        STATE = None
        INSTANCES = None

        def __post_init__(self):
            super().__post_init__()
            st = type(self).STATE or {}
            self.listing = st.get("listing")
            self.ops = []
            self.steps_out = []
            self.o12_after = None
            if self.listing:
                tfs = sorted(set(self.listing["expiries"]) | {l["tf"] for l in st.get("legs_live") or []})
                self.expiry_dates = pd.DatetimeIndex([pd.Timestamp(x) for x in tfs])
            if type(self).INSTANCES is not None:
                type(self).INSTANCES.append(self)

        # -- the listing ----------------------------------------------------------------------------------------------
        def _exp_iso(self, exp_i):
            tf = self.exp_date(exp_i).date().isoformat()
            return (self.listing or {}).get("actual", {}).get(tf, tf)

        def _snap(self, exp_i, is_call, K):
            ks = self.listing["strikes"].get((self._exp_iso(exp_i), "call" if is_call else "put")) or []
            if not ks:
                return None
            return min(ks, key=lambda k: (abs(k - K), k))

        @staticmethod
        def _contracts(units):
            n = math.floor(abs(units) / 100.0 + 0.5)
            return n if units > 0 else -n

        # -- the source's trades, recorded ----------------------------------------------------------------------------
        def open(self, t, is_call, K, exp_i, units, tag):
            K0, u0 = K, units
            if self.listing is not None and units != 0 and math.isfinite(units):
                K = self._snap(exp_i, is_call, K)
                n = self._contracts(units)
                if K is None or n == 0:
                    self.ops.append({"op": "skip_open", "tag": tag, "is_call": bool(is_call), "K_model": float(K0),
                                     "exp_i": int(exp_i), "units_model": float(u0),
                                     "why": "no listed strike" if K is None else "under one contract"})
                    return None
                units = 100.0 * n
            leg = super().open(t, is_call, K, exp_i, units, tag)
            if leg is not None:
                occ = None
                if self.listing is not None:
                    occ = self.listing["occ"].get((self._exp_iso(exp_i), "call" if is_call else "put", K))
                self.ops.append({"op": "open", "tag": tag, "is_call": bool(is_call), "K": float(K),
                                 "exp_i": int(exp_i), "units": float(units), "K_model": float(K0),
                                 "units_model": float(u0), "px": float(leg.px), "occ": occ})
            return leg

        def close(self, t, leg):
            self.ops.append({"op": "close", "tag": leg.tag, "is_call": bool(leg.is_call), "K": float(leg.K),
                             "exp_i": int(leg.exp_i), "units": float(leg.units), "occ": getattr(leg, "occ", None)})
            super().close(t, leg)

        def adjust(self, t, leg, delta_units):
            d0 = delta_units
            if delta_units == 0 or not math.isfinite(delta_units):
                return super().adjust(t, leg, delta_units)
            if self.listing is not None:
                n = self._contracts(delta_units)
                if n == 0:
                    self.ops.append({"op": "skip_adjust", "tag": leg.tag, "occ": getattr(leg, "occ", None),
                                     "delta_model": float(d0)})
                    return None
                delta_units = 100.0 * n
            self.ops.append({"op": "adjust", "tag": leg.tag, "is_call": bool(leg.is_call), "K": float(leg.K),
                             "exp_i": int(leg.exp_i), "delta": float(delta_units), "delta_model": float(d0),
                             "occ": getattr(leg, "occ", None), "units_before": float(leg.units)})
            return super().adjust(t, leg, delta_units)

        # -- one decision per step ------------------------------------------------------------------------------------
        @staticmethod
        def closure_state(decide):
            for cell in (decide.__closure__ or ()):
                try:
                    v = cell.cell_contents
                except ValueError:
                    continue
                if isinstance(v, dict) and set(v) == {"fut", "wait_month"}:
                    return v
            return None

        def run(self, decide, start):
            st = type(self).STATE or {}
            o12 = self.closure_state(decide)
            for step in st.get("steps") or []:
                self.ops = []
                if "core" in step:                           # a state the source's own Book.run decided on, its
                    t = int(step["t"])                       # numbers' types kept (numpy or Python floats: sum()
                    self.legs = [VS.Leg(bool(a), k, int(e), u, p, str(g))          # adds them differently)
                                 for a, k, e, u, p, g in step["legs"]]
                    self.core, self.nav_prev = step["core"], step["nav_prev"]
                else:                                        # the live book
                    t = len(self.dates) - 1
                    today = self.dates[t]
                    self.legs = []
                    for l in step.get("legs_live") or []:
                        exp_i = int(self.expiry_dates.get_loc(pd.Timestamp(l["tf"])))
                        if self.exp_date(exp_i) <= today:
                            continue
                        leg = VS.Leg(bool(l["is_call"]), float(l["K"]), exp_i, float(l["units"]), 0.0, l["tag"])
                        leg.px = self.quote(t, leg.is_call, leg.K, leg.exp_i)[0]
                        leg.occ = l.get("occ")
                        self.legs.append(leg)
                    self.core = float(step["nav"]) - sum(l.units * l.px for l in self.legs)
                    self.nav_prev = 0.0
                self._t = t
                if o12 is not None and step.get("o12") is not None:
                    o12.update(step["o12"])
                decide(self, t)
                self.steps_out.append(list(self.ops))
                self.o12_after = dict(o12) if o12 is not None else None
            return pd.DataFrame({"ret": [0.0]})

    return LiveBook
