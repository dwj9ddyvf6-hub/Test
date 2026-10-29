function Set-TastytradeSecretFromPrompt {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string]$Prompt
    )

    $secureValue = Read-Host -Prompt $Prompt -AsSecureString
    if ($secureValue.Length -eq 0) {
        throw "$Name cannot be empty."
    }

    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureValue)
    try {
        $plainValue = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
        [Environment]::SetEnvironmentVariable($Name, $plainValue, "Process")
    }
    finally {
        if ($null -ne $plainValue) { $plainValue = $null }
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
        $secureValue.Dispose()
    }
}

$ErrorActionPreference = "Stop"
$environment = Read-Host -Prompt "Environment [sandbox/production] (default sandbox)"
if ([string]::IsNullOrWhiteSpace($environment)) {
    $environment = "sandbox"
}

switch ($environment.Trim().ToLowerInvariant()) {
    "sandbox" {
        $environmentLabel = "Sandbox"
        $baseUrl = "https://api.cert.tastyworks.com"
    }
    "production" {
        $environmentLabel = "Production"
        $baseUrl = "https://api.tastyworks.com"
    }
    default {
        throw "Choose sandbox or production."
    }
}

Set-TastytradeSecretFromPrompt -Name "TASTYTRADE_CLIENT_SECRET" -Prompt "$environmentLabel OAuth client secret"
Set-TastytradeSecretFromPrompt -Name "TASTYTRADE_REFRESH_TOKEN" -Prompt "$environmentLabel OAuth refresh token"
$clientId = Read-Host -Prompt "$environmentLabel OAuth client ID (optional; press Enter to omit)"
if ([string]::IsNullOrWhiteSpace($clientId)) {
    [Environment]::SetEnvironmentVariable("TASTYTRADE_CLIENT_ID", $null, "Process")
} else {
    [Environment]::SetEnvironmentVariable("TASTYTRADE_CLIENT_ID", $clientId.Trim(), "Process")
}
[Environment]::SetEnvironmentVariable("TASTYTRADE_BASE_URL", $baseUrl, "Process")
Write-Host "$environmentLabel credentials are set for this PowerShell session. Values were not written to a file."
