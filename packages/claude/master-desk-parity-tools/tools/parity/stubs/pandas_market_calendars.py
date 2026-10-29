"""Stand-in for pandas_market_calendars (not installed): importable, but any use raises -- the decision paths the
quant_research parity harnesses exercise never call it."""


def get_calendar(name="NYSE"):
    raise RuntimeError("pandas_market_calendars stub: the calendar is not available in the parity harness")


def get_calendar_names():
    raise RuntimeError("pandas_market_calendars stub: the calendar is not available in the parity harness")
