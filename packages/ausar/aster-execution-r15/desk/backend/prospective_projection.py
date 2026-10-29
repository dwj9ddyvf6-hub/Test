"""Read-only view of independently owned prospective paper/research journals."""
import importlib
import os
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path


def _amount(value, *, positive=False):
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        raise ValueError("Missing or invalid monetary/quantity value")
    try:
        amount = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError("Invalid decimal value") from exc
    if not amount.is_finite() or amount < 0 or (positive and amount == 0):
        raise ValueError("Nonfinite, negative or invalid zero value")
    return amount


def _mark_clock(value):
    if not isinstance(value, str) or not value:
        raise ValueError("Observed quote requires an aware timestamp")
    stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if stamp.tzinfo is None:
        raise ValueError("Observed quote requires an aware timestamp")
    return stamp.astimezone(timezone.utc)


def _observed_marks(component, kind, now):
    """Add bid valuations to an existing projection; no feed, DB or writer calls.

    A dated valid bid remains a dated mark. It never becomes a current quote
    merely because this read clock advances. Legacy midpoint fields and all
    unknown fields keep their original values.
    """
    if not isinstance(component, dict) or not isinstance(component.get("books"), list):
        return component
    currency = "USD" if kind == "native" else "USDT"
    maximum_age = 30 if kind == "native" else 10
    output = dict(component)
    output["books"] = []
    for source in component["books"]:
        if not isinstance(source, dict):
            output["books"].append(source)
            continue
        book = dict(source)
        book.update(observed_marked_equity=None, net_pnl=None, mark_as_of=None,
                    mark_age_seconds=None, mark_fresh=False, mark_status="withheld",
                    mark_currency=currency, mark_max_age_seconds=maximum_age,
                    observed_mark_scope=(currency + " book cash plus gross position bid marks from dated received snapshots; "
                        "incurred fees already reduce cash; future liquidation fees, depth and market impact excluded; "
                        "not broker equity or proof of profitability"))
        try:
            cash = _amount(book["cash"])
            principal = _amount(book["virtual_principal"])
            if book.get("quote_currency", currency) != currency:
                raise ValueError("Book quote currency differs from its companion")
            held = {}
            if kind == "native":
                positions = book["positions"]
                if not isinstance(positions, dict):
                    raise ValueError("Native position ownership is unavailable")
                for symbol, quantity in positions.items():
                    if not isinstance(symbol, str) or not symbol.endswith("-USD"):
                        raise ValueError("Native held asset has no USD identity")
                    quantity = _amount(quantity)
                    if quantity:
                        held[symbol] = quantity
                capture = (component.get("market_data") or {}) if held else {}
                quotes = (capture.get("quotes") or {}) if held else {}
            else:
                position = book["position"]
                if position is not None:
                    if not isinstance(position, dict) or position.get("side") != "long":
                        raise ValueError("Public recipe position is not an owned spot long")
                    quantity = _amount(position["qty"])
                    if quantity:
                        symbol = book["symbol"]
                        if not isinstance(symbol, str) or not symbol.endswith("USDT"):
                            raise ValueError("Recipe held asset has no USDT identity")
                        held[symbol] = quantity
                receipt = (book.get("last_receipt") or {}) if held else {}
                capture = (receipt.get("capture") or {}) if held else {}
                quotes = {book.get("symbol"): capture.get("quote")} if held else {}
            value = cash
            clocks = []
            for symbol, quantity in held.items():
                quote = quotes.get(symbol)
                if not isinstance(quote, dict):
                    raise ValueError("Held asset has no observed bid/ask snapshot")
                bid, ask = _amount(quote["bid"], positive=True), _amount(quote["ask"], positive=True)
                if bid > ask:
                    raise ValueError("Received bid/ask snapshot is inverted")
                stamp = _mark_clock(quote["as_of" if kind == "native" else "asof"])
                if kind == "native":
                    received = _mark_clock(quote["received_at"])
                    complete_capture = _mark_clock(capture["at"])
                else:
                    received = _mark_clock(capture["receipts"]["quote"]["received_at"])
                    complete_capture = received
                    contract = capture.get("contract")
                    if (not isinstance(contract, dict) or contract.get("symbol") != symbol
                            or contract.get("quote_asset") != currency):
                        raise ValueError("Received recipe contract has a different instrument or currency")
                if not stamp <= received <= complete_capture <= now:
                    raise ValueError("Quote receipt is future or contradicts its observation clock")
                value += quantity * bid
                clocks.append(stamp)
            if clocks:
                mark_at = min(clocks)
                age = (now - mark_at).total_seconds()
                fresh = age <= maximum_age
                status = "fresh_received_quote_mark" if fresh else "dated_received_quote_mark"
            else:
                mark_at, age, fresh, status = now, 0.0, True, "cash_only"
                book["observed_mark_scope"] = (currency + " cash-only owned ledger balance at projection read; "
                    "incurred fees already reduce cash; no market quote or broker balance claim")
            book.update(observed_marked_equity=str(value), net_pnl=str(value-principal),
                        mark_as_of=mark_at.isoformat(), mark_age_seconds=age,
                        mark_fresh=fresh, mark_status=status)
        except (ValueError, TypeError, KeyError, AttributeError, ArithmeticError) as exc:
            book["mark_error"] = str(exc)
        output["books"].append(book)
    return output


def prospective_snapshot(primary_db):
    directory = Path(primary_db).parent
    components = {
        "native": ("backend.prospective_native", "ASTER_NATIVE_DB_PATH", "native-prospective.sqlite"),
        "public_recipes": ("backend.public_recipe_runtime", "ASTER_RECIPE_DB_PATH", "public-recipes.sqlite"),
        "original_research": ("backend.original_research_runtime", "ASTER_ORIGINAL_RESEARCH_DB_PATH", "original-research.sqlite"),
    }
    observed = datetime.now(timezone.utc)
    result = {"observed_at": observed.isoformat(), "paper_only": True,
              "capital_scope": "Each companion owns its own virtual principal and journal; equities are never added to the main books."}
    for key, (module, variable, filename) in components.items():
        path = Path(os.environ.get(variable) or directory / filename)
        if not path.is_file():
            result[key] = {"status": "not_installed", "installed": False, "books": [], "worker": {"running": False}}
            continue
        try:
            result[key] = importlib.import_module(module).read_status(path)
            if key in {"native", "public_recipes"}:
                result[key] = _observed_marks(result[key], key, observed)
        except Exception:
            # A corrupt/unavailable companion cannot break the operating desk
            # or be represented as empty/healthy. No write-side constructor.
            result[key] = {"status": "unavailable", "installed": None, "books": [],
                           "runtime_health": "unobserved", "error": "Companion journal could not be read"}
    return result
