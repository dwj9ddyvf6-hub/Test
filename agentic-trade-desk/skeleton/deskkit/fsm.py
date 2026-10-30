"""Per-(sleeve, symbol) position state machine: flat -> pending -> open -> exiting -> flat.

Illegal transitions raise. That is deliberate: a refused exit re-sent under the same id once
drove an illegal exiting->flat transition in a real desk; the guard made the bug loud.
"""
ALLOWED = {
    "flat": {"pending"},
    "pending": {"open", "flat"},       # filled, or refused/expired/cancelled with no fill
    "open": {"exiting", "open"},       # open->open = add / partial fill top-up
    "exiting": {"flat", "open"},       # exit filled, or exit refused/cancelled (position still open)
}


class IllegalTransition(Exception):
    pass


class Position:
    def __init__(self, sleeve: str, symbol: str):
        self.sleeve, self.symbol = sleeve, symbol
        self.state = "flat"
        self.qty = 0.0

    def to(self, new: str):
        if new not in ALLOWED[self.state]:
            raise IllegalTransition(f"{self.sleeve}/{self.symbol}: {self.state} -> {new}")
        self.state = new
