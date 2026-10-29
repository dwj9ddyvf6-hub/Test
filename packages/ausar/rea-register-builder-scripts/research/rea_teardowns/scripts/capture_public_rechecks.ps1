[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$captureDate = '2026-10-26'
$artifactRoot = Join-Path (Split-Path -Parent $PSScriptRoot) 'artifacts/public-rechecks-2026-10-26'

# Anonymous GET requests only. No cookies, credentials, proxy rotation, or login flows.
$captures = @(
    @{ Target = 'zeiierman'; File = 'pricing.html'; Url = 'https://www.zeiierman.com/pricing' },
    @{ Target = 'zeiierman'; File = 'quickstart.md'; Url = 'https://docs.zeiierman.com/getting-started/quickstart' },
    @{ Target = 'zeiierman'; File = 'neural-weight-oscillator-page.html'; Url = 'https://www.tradingview.com/script/bfu1hmkS-Neural-Weight-Oscillator-Zeiierman/' },
    @{ Target = 'tradingkit'; File = 'install.html'; Url = 'https://app.tradingkit.com/install' },
    @{ Target = 'tradingkit'; File = 'docs-mcp.html'; Url = 'https://kb.tradingkit.com/integrations/docs-mcp/' },
    @{ Target = 'kucoin-app-4.43.0'; File = 'android-download.html'; Url = 'https://www.kucoin.com/download/android' },
    @{ Target = 'kucoin-app-4.43.0'; File = 'android-guide.html'; Url = 'https://www.kucoin.com/support/900006694223' },
    @{ Target = 'zerith-macd-martingale-grid-v2.20'; File = 'home.html'; Url = 'https://zerith.io/' },
    @{ Target = 'zerith-macd-martingale-grid-v2.20'; File = 'algos.html'; Url = 'https://zerith.io/algos/' },
    @{ Target = 'deepseek-news-grid-scalper-v2'; File = 'unlocked-ai-market-candidate.html'; Url = 'https://www.mql5.com/en/market/product/175271' },
    @{ Target = 'deepseek-news-grid-scalper-v2'; File = 'unlocked-ai-vendor-guide.html'; Url = 'https://www.mql5.com/en/blogs/post/769489' },
    @{ Target = 'guardian-ftmo-swing-free'; File = 'ctrader-listing.html'; Url = 'https://ctrader.com/products/4616' },
    @{ Target = 'guardian-ftmo-swing-free'; File = 'vendor-guide.html'; Url = 'https://realbacktesting.com/guardian.html' },
    @{ Target = 'guardian-ftmo-swing-free'; File = 'vendor-results.html'; Url = 'https://realbacktesting.com/results.html' },
    @{ Target = 'guardian-ftmo-swing-free'; File = 'ctrader-store-faq.html'; Url = 'https://help.ctrader.com/ctrader-store/faq/' },
    @{ Target = 'm-algo-eurusd-m1-core'; File = 'core-listing.html'; Url = 'https://ctrader.com/products/5052' },
    @{ Target = 'm-algo-eurusd-m1-core'; File = 'trial-listing.html'; Url = 'https://ctrader.com/products/5733' },
    @{ Target = 'm-algo-eurusd-m1-core'; File = 'ctrader-store-faq.html'; Url = 'https://help.ctrader.com/ctrader-store/faq/' }
)

foreach ($target in ($captures.Target | Select-Object -Unique)) {
    $targetDirectory = Join-Path $artifactRoot $target
    New-Item -ItemType Directory -Path $targetDirectory -Force | Out-Null
}

$manifestByTarget = @{}
foreach ($capture in $captures) {
    $targetDirectory = Join-Path $artifactRoot $capture.Target
    $path = Join-Path $targetDirectory $capture.File
    $record = [ordered]@{
        File = $capture.File
        RequestedURL = $capture.Url
        FinalURL = $null
        Status = $null
        ContentType = $null
        Bytes = $null
        SHA256 = $null
        CaptureDate = $captureDate
    }

    try {
        $response = Invoke-WebRequest -Uri $capture.Url -MaximumRedirection 5 -TimeoutSec 30
        $body = [string]$response.Content
        [System.IO.File]::WriteAllText($path, $body, [System.Text.UTF8Encoding]::new($false))
        $record.Status = [int]$response.StatusCode
        $record.FinalURL = $response.BaseResponse.RequestMessage.RequestUri.AbsoluteUri
        $record.ContentType = $response.BaseResponse.Content.Headers.ContentType.ToString()
        $record.Bytes = (Get-Item -LiteralPath $path).Length
        $record.SHA256 = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToUpperInvariant()
    }
    catch {
        $record.Error = $_.Exception.Message
        if ($_.Exception.Response -and $_.Exception.Response.StatusCode) {
            $record.Status = [int]$_.Exception.Response.StatusCode
        }
    }

    if (-not $manifestByTarget.ContainsKey($capture.Target)) {
        $manifestByTarget[$capture.Target] = [System.Collections.Generic.List[object]]::new()
    }
    $manifestByTarget[$capture.Target].Add([pscustomobject]$record)
    Write-Output ("{0}: HTTP {1}, {2} bytes" -f $capture.Target, $record.Status, $record.Bytes)
}

foreach ($target in $manifestByTarget.Keys) {
    $manifestPath = Join-Path (Join-Path $artifactRoot $target) 'capture-manifest.json'
    $manifestByTarget[$target] | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $manifestPath -Encoding utf8
}
