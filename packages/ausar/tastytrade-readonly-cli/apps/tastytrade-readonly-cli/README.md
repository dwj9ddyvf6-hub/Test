# tastytrade Personal Read-Only CLI

A small local command-line app for listing your tastytrade accounts, viewing balances and open positions, and downloading transaction history. It uses OAuth2 and the tastytrade REST API. It has no order, market-data, streaming, strategy, scheduling, web, or hosted-service features.

## What it reads

- Accessible accounts: account number, nickname, account type, margin/cash type, authority level, and closed status.
- Selected account balances: cash, net liquidation value, buying power, maintenance requirement, withdrawable cash, and pending cash.
- Selected account open positions: symbol, instrument type, underlying, quantity and direction, average open price, close price, and multiplier. It does not calculate or display P/L.
- Transaction history, with pagination, optional dates and filters, a terminal table, and optional CSV export.

All amounts and quantities are parsed with `Decimal`; no binary floating-point calculations are used. The app stores access tokens only in memory and explicitly requests the OAuth `read` scope on token exchange. It sends the OAuth bearer token only to the official tastytrade host, and sends a `User-Agent`, `Accept: application/json`, and a 15-second timeout on every API request.

## Create your own OAuth credentials

The app does not create a brokerage account or complete identity/financial attestations. You must already have an account and create a personal OAuth application and grant in tastytrade yourself. Use the `read` scope only. Sandbox and production credentials are separate; start with sandbox.

Follow tastytrade's [OAuth2 instructions](https://developer.tastytrade.com/oauth/) and [sandbox guide](https://developer.tastytrade.com/docs/sandbox/). In your tastytrade profile, create an OAuth client and a personal grant for your own account. Keep the client secret and refresh token private. Do not send them in chat or commit them to Git.

## Run in sandbox

Requires Python 3.10 or newer. On Windows, from this directory:

```powershell
. .\Set-TastytradeCredentials.ps1
.\run.ps1 accounts
.\run.ps1 balances
.\run.ps1 positions
.\run.ps1 transactions --start-date 2026-01-01 --csv .\transactions.csv
```

The setup script asks whether to use sandbox or production (sandbox is the default), then prompts for the matching client secret and refresh token without echoing them. It holds credentials only in the current PowerShell process environment. It does not write a `.env` file or save credentials to disk. Closing the PowerShell window clears these process-scoped values. The optional client ID is not secret, but the prompt still keeps it out of the command history. Choose the same environment where you created the OAuth client and personal grant.

The Python app defaults to sandbox when `TASTYTRADE_BASE_URL` is unset and prints the selected base URL at startup. It accepts only tastytrade's official sandbox and production API URLs so credentials cannot be sent to an arbitrary host.

When more than one account is available, the app asks you to choose. You can also specify one explicitly:

```powershell
.\run.ps1 positions --account YOUR_ACCOUNT_NUMBER
```

For transaction history, `--type` can be repeated. `--end-date` is optional; if omitted, tastytrade applies its documented default. CSV output uses a new-file-only write, so an existing file is never overwritten.

## Production

Use production only with a production OAuth client and its production personal grant. Select `production` when the setup script asks for an environment. Production and sandbox clients, grants, and data are separate; never mix their credentials.

## Commands

```text
accounts
balances [--account ACCOUNT_NUMBER]
positions [--account ACCOUNT_NUMBER]
transactions [--account ACCOUNT_NUMBER] [--start-date YYYY-MM-DD] [--end-date YYYY-MM-DD]
             [--symbol SYMBOL] [--instrument-type TYPE] [--type TYPE ...] [--csv PATH]
```

Transaction pages use `per-page=250`, `sort=Desc`, and the endpoint's pagination metadata. GET network errors, HTTP 429, and HTTP 5xx responses use bounded exponential backoff with jitter. A JSON 401 refreshes the access token and retries that GET once. The token request itself is never retried. The CLI never calls an order endpoint.

## Current verification boundary

The client is ready to run locally. Account authentication and live account data cannot be verified until you create the OAuth grant and enter its credentials locally. No credentials are included in this repository.
