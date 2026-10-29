"""Stub of the old desk's ~/workspace/skills/alpaca-paper/bin/alpaca_lib (not in any repo). The parity harnesses
call only the old modules' PURE decision functions; any network call through this stub is a harness bug."""


def _no_network(*a, **k):
    raise RuntimeError("parity harness: alpaca_lib network call attempted")


api_request = data_base = quote_path = data_request = trading_base = _no_network


def base_url(*a, **k):
    return "https://paper-api.alpaca.markets"
