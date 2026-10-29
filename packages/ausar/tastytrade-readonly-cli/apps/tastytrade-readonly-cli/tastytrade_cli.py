#!/usr/bin/env python3
"""Small, personal, read-only tastytrade account viewer."""

from __future__ import annotations

import argparse
import csv
from datetime import date
from decimal import Decimal, InvalidOperation
import json
import os
from pathlib import Path
import random
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


SANDBOX_URL = "https://api.cert.tastyworks.com"
PRODUCTION_URL = "https://api.tastyworks.com"
USER_AGENT = "my-portfolio-viewer/1.0"
REQUEST_TIMEOUT_SECONDS = 15
MAX_GET_ATTEMPTS = 5
TOKEN_REFRESH_AFTER_SECONDS = 10 * 60
TRANSACTION_PAGE_SIZE = 250
PAGE_PAUSE_SECONDS = 0.2

BALANCE_FIELDS = (
    "cash-balance",
    "net-liquidating-value",
    "equity-buying-power",
    "derivative-buying-power",
    "maintenance-requirement",
    "cash-available-to-withdraw",
    "pending-cash",
)
POSITION_FIELDS = (
    "symbol",
    "instrument-type",
    "underlying-symbol",
    "quantity",
    "quantity-direction",
    "average-open-price",
    "close-price",
    "multiplier",
)
TRANSACTION_FIELDS = (
    "id",
    "transaction-type",
    "transaction-sub-type",
    "description",
    "symbol",
    "action",
    "quantity",
    "price",
    "value",
    "net-value",
    "executed-at",
    "transaction-date",
)
TRANSACTION_ALWAYS_EFFECT_FIELDS = {"value-effect", "net-value-effect"}
DECIMAL_FIELDS = {
    "cash-balance",
    "net-liquidating-value",
    "equity-buying-power",
    "derivative-buying-power",
    "maintenance-requirement",
    "cash-available-to-withdraw",
    "pending-cash",
    "quantity",
    "average-open-price",
    "close-price",
    "multiplier",
    "price",
    "value",
    "net-value",
}


class CLIError(Exception):
    """An actionable local configuration or input error."""


class NetworkFailure(Exception):
    """A network/timeout failure with no sensitive exception detail."""


class ApiFailure(Exception):
    def __init__(
        self,
        status: int,
        code: str | None,
        message: str | None,
        *,
        has_json_error: bool = False,
        is_json: bool = False,
        details: list[object] | None = None,
    ) -> None:
        self.status = status
        self.code = code
        self.message = message
        self.has_json_error = has_json_error
        self.is_json = is_json
        self.details = details or []
        super().__init__(f"HTTP {status}")


class TokenFailure(Exception):
    def __init__(self, status: int | None, code: str | None) -> None:
        self.status = status
        self.code = code
        super().__init__("OAuth token request failed")


def parse_json(body: bytes) -> object | None:
    try:
        return json.loads(body.decode("utf-8"), parse_float=Decimal)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None


def error_details(payload: object | None) -> tuple[str | None, str | None, bool]:
    if not isinstance(payload, dict):
        return None, None, False
    error = payload.get("error")
    if not isinstance(error, dict):
        return None, None, False
    code = error.get("code")
    message = error.get("message")
    return (
        str(code) if code is not None else None,
        str(message) if message is not None else None,
        code is not None,
    )


def decimal_text(value: object) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return format(value, "f")
    try:
        return format(Decimal(str(value)), "f")
    except (InvalidOperation, ValueError):
        return str(value)


def cell_text(field: str, value: object) -> str:
    if value is None:
        return ""
    if field in DECIMAL_FIELDS or isinstance(value, Decimal):
        rendered = decimal_text(value)
    elif isinstance(value, bool):
        rendered = str(value).lower()
    elif isinstance(value, (dict, list)):
        rendered = json.dumps(value, ensure_ascii=False, default=decimal_text)
    else:
        rendered = str(value)
    return rendered.replace("\r", " ").replace("\n", " ")


def render_table(headers: list[str], rows: list[list[object]]) -> str:
    rendered = [[str(value) for value in row] for row in rows]
    widths = [len(header) for header in headers]
    for row in rendered:
        for index, value in enumerate(row):
            widths[index] = max(widths[index], len(value))
    separator = "-+-".join("-" * width for width in widths)
    header_row = " | ".join(header.ljust(widths[i]) for i, header in enumerate(headers))
    lines = [header_row, separator]
    for row in rendered:
        lines.append(" | ".join(value.ljust(widths[i]) for i, value in enumerate(row)))
    return "\n".join(lines)


def items_from(payload: object, endpoint: str) -> list[dict[str, object]]:
    if not isinstance(payload, dict):
        raise CLIError(f"Unexpected response for {endpoint}: expected a JSON object.")
    data = payload.get("data")
    if not isinstance(data, dict) or not isinstance(data.get("items"), list):
        raise CLIError(f"Unexpected response for {endpoint}: expected data.items.")
    if any(not isinstance(item, dict) for item in data["items"]):
        raise CLIError(f"Unexpected response for {endpoint}: an item was not an object.")
    return data["items"]  # type: ignore[return-value]


def object_data_from(payload: object, endpoint: str) -> dict[str, object]:
    if not isinstance(payload, dict) or not isinstance(payload.get("data"), dict):
        raise CLIError(f"Unexpected response for {endpoint}: expected a data object.")
    return payload["data"]  # type: ignore[return-value]


class TastytradeClient:
    def __init__(self, base_url: str, client_secret: str, refresh_token: str, client_id: str | None) -> None:
        self.base_url = base_url
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.client_id = client_id
        self.access_token: str | None = None
        self.token_received_at: float | None = None

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: list[tuple[str, str]] | None = None,
        body: dict[str, str] | None = None,
        access_token: str | None = None,
    ) -> tuple[int, bytes]:
        url = self.base_url + path
        if params:
            url += "?" + urlencode(params)
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        }
        if access_token is not None:
            headers["Authorization"] = f"Bearer {access_token}"
        request_body = None
        if body is not None:
            headers["Content-Type"] = "application/json"
            request_body = json.dumps(body).encode("utf-8")
        request = Request(url, data=request_body, headers=headers, method=method)
        try:
            with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
                return response.status, response.read()
        except HTTPError as error:
            try:
                return error.code, error.read()
            finally:
                error.close()
        except (URLError, TimeoutError, OSError):
            raise NetworkFailure() from None

    def _parse_response(self, status: int, body: bytes) -> dict[str, object]:
        payload = parse_json(body)
        if not 200 <= status < 300:
            code, message, has_json_error = error_details(payload)
            details: list[object] = []
            if isinstance(payload, dict) and isinstance(payload.get("error"), dict):
                errors = payload["error"].get("errors")
                if isinstance(errors, list):
                    details = errors
            raise ApiFailure(
                status,
                code,
                message,
                has_json_error=has_json_error,
                is_json=payload is not None,
                details=details,
            )
        if not isinstance(payload, dict):
            raise ApiFailure(status, "invalid_response", "The API returned a non-JSON response.")
        return payload

    def _refresh_access_token(self) -> None:
        token_body = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_secret": self.client_secret,
            "scope": "read",
        }
        if self.client_id:
            token_body["client_id"] = self.client_id
        try:
            status, body = self._request("POST", "/oauth/token", body=token_body)
        except NetworkFailure:
            self.access_token = None
            self.token_received_at = None
            raise TokenFailure(None, None) from None
        payload = parse_json(body)
        if not 200 <= status < 300:
            code, _, _ = error_details(payload)
            self.access_token = None
            self.token_received_at = None
            raise TokenFailure(status, code)
        if not isinstance(payload, dict) or not isinstance(payload.get("access_token"), str) or not payload["access_token"]:
            self.access_token = None
            self.token_received_at = None
            raise TokenFailure(status, "invalid_response")
        self.access_token = payload["access_token"]
        self.token_received_at = time.monotonic()

    def _ensure_access_token(self) -> None:
        if self.access_token is None or self.token_received_at is None:
            self._refresh_access_token()
        elif time.monotonic() - self.token_received_at > TOKEN_REFRESH_AFTER_SECONDS:
            self._refresh_access_token()

    def _get_with_retries(self, path: str, params: list[tuple[str, str]] | None) -> dict[str, object]:
        for attempt in range(MAX_GET_ATTEMPTS):
            try:
                status, body = self._request(
                    "GET",
                    path,
                    params=params,
                    body=None,
                    access_token=self.access_token,
                )
                return self._parse_response(status, body)
            except NetworkFailure:
                if attempt + 1 >= MAX_GET_ATTEMPTS:
                    raise CLIError("GET request failed after five attempts due to a network or timeout error.") from None
            except ApiFailure as failure:
                if failure.status == 401 or (failure.status != 429 and not 500 <= failure.status <= 599):
                    raise failure
                if attempt + 1 >= MAX_GET_ATTEMPTS:
                    raise failure
            delay = min(2**attempt, 8) + random.uniform(0.0, 0.25)
            time.sleep(delay)
        raise CLIError("GET request stopped unexpectedly.")

    def get(self, path: str, params: list[tuple[str, str]] | None = None) -> dict[str, object]:
        self._ensure_access_token()
        try:
            return self._get_with_retries(path, params)
        except ApiFailure as failure:
            if failure.status != 401 or not failure.is_json:
                raise
        self._refresh_access_token()
        return self._get_with_retries(path, params)


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read-only tastytrade account viewer. It cannot submit, replace, or cancel orders."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("accounts", help="list accessible accounts")

    balances = commands.add_parser("balances", help="show balances for a selected account")
    balances.add_argument("--account", help="account number; omit to choose from the account list")

    positions = commands.add_parser("positions", help="show open positions for a selected account")
    positions.add_argument("--account", help="account number; omit to choose from the account list")

    transactions = commands.add_parser("transactions", help="download and display transaction history")
    transactions.add_argument("--account", help="account number; omit to choose from the account list")
    transactions.add_argument("--start-date", help="first transaction date, YYYY-MM-DD")
    transactions.add_argument("--end-date", help="last transaction date, YYYY-MM-DD; omitted means API default")
    transactions.add_argument("--symbol", help="filter by symbol")
    transactions.add_argument("--instrument-type", help="filter by instrument type")
    transactions.add_argument("--type", dest="types", action="append", help="transaction type; repeat to add filters")
    transactions.add_argument("--csv", type=Path, help="write the displayed transaction fields to a new CSV file")
    return parser


def format_account(account_item: dict[str, object]) -> dict[str, object]:
    account = account_item.get("account")
    if not isinstance(account, dict):
        raise CLIError("Unexpected account response: an item did not include an account object.")
    return {
        "account-number": account.get("account-number", ""),
        "nickname": account.get("nickname", ""),
        "account-type-name": account.get("account-type-name", ""),
        "margin-or-cash": account.get("margin-or-cash", ""),
        "authority-level": account_item.get("authority-level", ""),
        "is-closed": account.get("is-closed", ""),
    }


def print_accounts(accounts: list[dict[str, object]]) -> None:
    fields = ("account-number", "nickname", "account-type-name", "margin-or-cash", "authority-level", "is-closed")
    rows = [[cell_text(field, item.get(field)) for field in fields] for item in map(format_account, accounts)]
    print(render_table(list(fields), rows) if rows else "No accounts were returned.")


def choose_account(client: TastytradeClient, requested: str | None) -> str:
    accounts = items_from(client.get("/customers/me/accounts"), "/customers/me/accounts")
    if not accounts:
        raise CLIError("No accessible tastytrade accounts were returned.")
    formatted = [format_account(item) for item in accounts]
    valid_numbers = [str(item["account-number"]) for item in formatted]
    if requested:
        if requested not in valid_numbers:
            raise CLIError("That account number was not present in the accessible account list.")
        return requested
    if len(formatted) == 1:
        return valid_numbers[0]
    fields = ("account-number", "nickname", "account-type-name", "margin-or-cash", "authority-level", "is-closed")
    rows = [[cell_text(field, item.get(field)) for field in fields] for item in formatted]
    print(render_table(list(fields), rows))
    try:
        choice = input("Enter the account number you want to use: ").strip()
    except EOFError:
        raise CLIError("More than one account is available; rerun with --account ACCOUNT_NUMBER.") from None
    if choice not in valid_numbers:
        raise CLIError("The selected value did not match an account number in the list.")
    return choice


def effect_columns(fields: tuple[str, ...], rows: list[dict[str, object]]) -> list[str]:
    columns: list[str] = []
    for field in fields:
        columns.append(field)
        effect = f"{field}-effect"
        if effect in TRANSACTION_ALWAYS_EFFECT_FIELDS or any(effect in row for row in rows):
            columns.append(effect)
    return columns


def row_for_fields(row: dict[str, object], fields: list[str]) -> list[str]:
    return [cell_text(field, row.get(field)) for field in fields]


def validate_date(value: str | None, flag: str) -> str | None:
    if value is None:
        return None
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        raise CLIError(f"{flag} must use YYYY-MM-DD.") from None
    if parsed.isoformat() != value:
        raise CLIError(f"{flag} must use YYYY-MM-DD.")
    return value


def transaction_history(client: TastytradeClient, account_number: str, args: argparse.Namespace) -> list[dict[str, object]]:
    start_date = validate_date(args.start_date, "--start-date")
    end_date = validate_date(args.end_date, "--end-date")
    if start_date and end_date and start_date > end_date:
        raise CLIError("--start-date must be on or before --end-date.")

    account_path = quote(account_number, safe="")
    path = f"/accounts/{account_path}/transactions"
    all_rows: list[dict[str, object]] = []
    page_offset = 0
    while True:
        params: list[tuple[str, str]] = [
            ("page-offset", str(page_offset)),
            ("per-page", str(TRANSACTION_PAGE_SIZE)),
            ("sort", "Desc"),
        ]
        if start_date:
            params.append(("start-date", start_date))
        if end_date:
            params.append(("end-date", end_date))
        if args.symbol:
            params.append(("symbol", args.symbol))
        if args.instrument_type:
            params.append(("instrument-type", args.instrument_type))
        for transaction_type in args.types or []:
            params.append(("types[]", transaction_type))

        payload = client.get(path, params)
        page_rows = items_from(payload, path)
        all_rows.extend(page_rows)
        pagination = payload.get("pagination") if isinstance(payload, dict) else None
        if isinstance(pagination, dict) and pagination.get("total-pages") is not None:
            try:
                total_pages = int(pagination["total-pages"])
            except (TypeError, ValueError):
                raise CLIError("Transaction response contained invalid pagination.total-pages.") from None
            if page_offset + 1 >= total_pages:
                break
        elif not page_rows or len(page_rows) < TRANSACTION_PAGE_SIZE:
            break
        page_offset += 1
        time.sleep(PAGE_PAUSE_SECONDS)
    return all_rows


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    try:
        with path.open("x", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            for row in rows:
                writer.writerow({field: cell_text(field, row.get(field)) for field in fields})
    except FileExistsError:
        raise CLIError(f"CSV file already exists: {path}. Choose a new filename to avoid overwriting it.") from None
    except OSError as error:
        raise CLIError(f"Could not write CSV file to {path} ({type(error).__name__}).") from None


def make_client(base_url: str) -> TastytradeClient:
    missing = [
        name
        for name in ("TASTYTRADE_CLIENT_SECRET", "TASTYTRADE_REFRESH_TOKEN")
        if not os.environ.get(name)
    ]
    if missing:
        names = " and ".join(missing)
        raise CLIError(f"Missing required environment variable(s): {names}. Set them locally; do not paste secrets into chat.")
    return TastytradeClient(
        base_url,
        os.environ["TASTYTRADE_CLIENT_SECRET"],
        os.environ["TASTYTRADE_REFRESH_TOKEN"],
        os.environ.get("TASTYTRADE_CLIENT_ID") or None,
    )


def show_balances(client: TastytradeClient, account_number: str) -> None:
    path = f"/accounts/{quote(account_number, safe='')}/balances"
    data = object_data_from(client.get(path), path)
    fields = list(BALANCE_FIELDS)
    for field in BALANCE_FIELDS:
        effect = f"{field}-effect"
        if effect in data and effect not in fields:
            fields.insert(fields.index(field) + 1, effect)
    rows = [[cell_text(field, data.get(field)) for field in fields]]
    print(render_table(fields, rows))


def show_positions(client: TastytradeClient, account_number: str) -> None:
    path = f"/accounts/{quote(account_number, safe='')}/positions"
    positions = items_from(client.get(path), path)
    rows = [row_for_fields(position, list(POSITION_FIELDS)) for position in positions]
    print(render_table(list(POSITION_FIELDS), rows) if rows else "No open positions were returned.")


def show_transactions(client: TastytradeClient, account_number: str, args: argparse.Namespace) -> None:
    rows = transaction_history(client, account_number, args)
    fields = effect_columns(TRANSACTION_FIELDS, rows)
    if args.csv:
        write_csv(args.csv, rows, fields)
        print(f"Wrote {len(rows)} transaction(s) to {args.csv}.")
    rendered_rows = [row_for_fields(row, fields) for row in rows]
    print(render_table(fields, rendered_rows) if rendered_rows else "No transactions matched the selected filters.")


def permitted_base_url() -> str:
    raw = os.environ.get("TASTYTRADE_BASE_URL", SANDBOX_URL).rstrip("/")
    if raw not in {SANDBOX_URL, PRODUCTION_URL}:
        print("tastytrade API base URL: invalid; only the official sandbox or production URL is accepted.")
        raise CLIError(f"TASTYTRADE_BASE_URL must be {SANDBOX_URL} or {PRODUCTION_URL}.")
    print(f"tastytrade API base URL: {raw}")
    return raw


def report_api_failure(failure: ApiFailure, secrets: list[str]) -> str:
    def redact(value: str | None) -> str:
        text = value or "unavailable"
        for secret in secrets:
            if secret and len(secret) >= 4:
                text = text.replace(secret, "[redacted]")
        return text

    if failure.status == 401 and not failure.is_json:
        return "tastytrade returned HTTP 401 without a JSON error code. Check the required User-Agent format: product/version."
    code = redact(failure.code)
    message = redact(failure.message)
    result = f"tastytrade API error: HTTP {failure.status}; error.code={code}; message={message}"
    if failure.status == 422 and failure.details:
        detail_lines = []
        for item in failure.details:
            if isinstance(item, dict):
                parts = [f"{key}={redact(str(item[key]))}" for key in ("code", "message", "domain") if item.get(key) is not None]
                detail_lines.append(", ".join(parts) if parts else redact(json.dumps(item, default=decimal_text)))
            else:
                detail_lines.append(redact(str(item)))
        result += "; error.errors=[" + "; ".join(detail_lines) + "]"
    if failure.status == 401 and failure.code:
        result += ". The app refreshed the access token and retried this GET once if this was the first 401."
    return result


def main(argv: list[str] | None = None) -> int:
    parser = make_parser()
    args = parser.parse_args(argv)
    try:
        base_url = permitted_base_url()
        client = make_client(base_url)
        if args.command == "accounts":
            accounts = items_from(client.get("/customers/me/accounts"), "/customers/me/accounts")
            print_accounts(accounts)
            return 0

        account_number = choose_account(client, args.account)
        if args.command == "balances":
            show_balances(client, account_number)
        elif args.command == "positions":
            show_positions(client, account_number)
        elif args.command == "transactions":
            show_transactions(client, account_number, args)
        return 0
    except TokenFailure as failure:
        status = str(failure.status) if failure.status is not None else "unavailable"
        code = failure.code or "unavailable"
        print(f"OAuth token request failed: HTTP status={status}; error.code={code}.", file=sys.stderr)
        return 1
    except ApiFailure as failure:
        secrets = [
            os.environ.get("TASTYTRADE_CLIENT_SECRET", ""),
            os.environ.get("TASTYTRADE_REFRESH_TOKEN", ""),
        ]
        if "client" in locals() and client.access_token:
            secrets.append(client.access_token)
        print(report_api_failure(failure, secrets), file=sys.stderr)
        if failure.status == 403:
            print("Check the OAuth read scope and the selected account authority level.", file=sys.stderr)
        elif failure.status == 404:
            print("Check the account number and confirm the sandbox/production environment matches the credentials.", file=sys.stderr)
        elif failure.status == 422:
            print("Review the request parameters and the API error details before retrying.", file=sys.stderr)
        return 1
    except CLIError as error:
        print(str(error), file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Cancelled.", file=sys.stderr)
        return 130
    except Exception as error:  # Avoid traceback output that could include request objects or secrets.
        print(f"Unexpected local error ({type(error).__name__}); details withheld to protect credentials.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
