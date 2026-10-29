$ErrorActionPreference = "Stop"
$app = Join-Path $PSScriptRoot "tastytrade_cli.py"
$pythonCommand = Get-Command py -ErrorAction SilentlyContinue

if ($null -ne $pythonCommand) {
    & $pythonCommand.Source -3 $app @args
    $cliExitCode = $LASTEXITCODE
    $global:LASTEXITCODE = $cliExitCode
    if ($cliExitCode -ne 0) { throw "tastytrade CLI exited with code $cliExitCode." }
    return
}

$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
if ($null -ne $pythonCommand -and $pythonCommand.Source -notlike "*\WindowsApps\python.exe") {
    & $pythonCommand.Source $app @args
    $cliExitCode = $LASTEXITCODE
    $global:LASTEXITCODE = $cliExitCode
    if ($cliExitCode -ne 0) { throw "tastytrade CLI exited with code $cliExitCode." }
    return
}

$bundledPython = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if (Test-Path -LiteralPath $bundledPython) {
    & $bundledPython $app @args
    $cliExitCode = $LASTEXITCODE
    $global:LASTEXITCODE = $cliExitCode
    if ($cliExitCode -ne 0) { throw "tastytrade CLI exited with code $cliExitCode." }
    return
}

throw "Python 3.10 or newer is required. Install Python, then reopen PowerShell and try again."
