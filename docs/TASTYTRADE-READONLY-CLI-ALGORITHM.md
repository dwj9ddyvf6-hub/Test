# tastytrade read-only CLI

Created by Ausar. Packaged into the Test repo on 2026-10-29 (packaging pass).

Origin: dwj9ddyvf6-hub/Silicon branch codex/shipyard-live-terminal, apps/tastytrade-readonly-cli/.

A small local command-line app (Python 3.10+, tastytrade_cli.py with PowerShell launchers run.ps1 and Set-TastytradeCredentials.ps1) that lists tastytrade accounts, balances, and open positions and downloads transaction history with pagination, optional date and type filters, a terminal table, and optional CSV export. It uses OAuth2 with the read scope only, keeps access tokens in memory only, parses all amounts and quantities with Decimal, and sends a 15-second timeout on every API request to the official tastytrade host. It has no order, market-data, streaming, strategy, scheduling, web, or hosted-service features, and it does not calculate or display P/L.

## Files in this package

- `packages/ausar/tastytrade-readonly-cli/apps/tastytrade-readonly-cli/.gitignore`
- `packages/ausar/tastytrade-readonly-cli/apps/tastytrade-readonly-cli/README.md`
- `packages/ausar/tastytrade-readonly-cli/apps/tastytrade-readonly-cli/Set-TastytradeCredentials.ps1`
- `packages/ausar/tastytrade-readonly-cli/apps/tastytrade-readonly-cli/run.ps1`
- `packages/ausar/tastytrade-readonly-cli/apps/tastytrade-readonly-cli/tastytrade_cli.py`

Source files are verbatim copies from the origin location named above unless a sanitization note appears in this doc.
