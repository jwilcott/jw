param(
    [string]$DestinationRoot = ""
)

$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$sourceFile = Join-Path $scriptDir 'JW_CommandSearch_Macro.txt'
$macroFolderName = 'JW'
$macroFileName = 'JW Command Search.txt'

if (-not (Test-Path -LiteralPath $sourceFile)) {
    Write-Host "Macro source not found:" -ForegroundColor Red
    Write-Host "  $sourceFile"
    exit 1
}

$candidateRoots = @()

if ($DestinationRoot) {
    $candidateRoots += $DestinationRoot
}

$candidateRoots += @(
    'C:\Program Files\Maxon ZBrush 2025\ZStartup\Macros',
    'C:\Program Files\Maxon ZBrush 2025\ZStartup',
    'C:\Program Files\Pixologic\ZBrush 2025\ZStartup\Macros',
    'C:\Program Files\Pixologic\ZBrush 2025\ZStartup',
    'C:\Users\Public\Documents\ZBrushData2025\ZStartup\Macros',
    'C:\Users\Public\Documents\ZBrushData2025\ZStartup'
) | Select-Object -Unique

$resolvedTarget = $null

foreach ($candidate in $candidateRoots) {
    if ([string]::IsNullOrWhiteSpace($candidate)) {
        continue
    }

    if (Test-Path -LiteralPath $candidate) {
        if ((Split-Path -Leaf $candidate) -ieq 'Macros') {
            $resolvedTarget = $candidate
            break
        }

        $childTarget = Join-Path $candidate 'Macros'
        $resolvedTarget = $childTarget
        break
    }
}

if (-not $resolvedTarget) {
    $resolvedTarget = 'C:\Program Files\Maxon ZBrush 2025\ZStartup\Macros'
}

if (-not (Test-Path -LiteralPath $resolvedTarget)) {
    New-Item -ItemType Directory -Path $resolvedTarget -Force | Out-Null
}

$destinationFolder = Join-Path $resolvedTarget $macroFolderName
if (-not (Test-Path -LiteralPath $destinationFolder)) {
    New-Item -ItemType Directory -Path $destinationFolder -Force | Out-Null
}

$destinationFile = Join-Path $destinationFolder $macroFileName
$obsoletePluginPaths = @(
    'C:\Program Files\Maxon ZBrush 2025\ZStartup\ZPlugs64\JW_CommandSearch.txt',
    'C:\Users\Public\Documents\ZBrushData2025\ZStartup\ZPlugs64\JW_CommandSearch.txt'
)

if (Test-Path -LiteralPath $destinationFile) {
    $timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
    $backupFile = Join-Path $destinationFolder ("JW_CommandSearch.backup_{0}.txt" -f $timestamp)
    Copy-Item -LiteralPath $destinationFile -Destination $backupFile -Force
    Write-Host "Backed up existing macro to:" -ForegroundColor Yellow
    Write-Host "  $backupFile"
}

$content = Get-Content -LiteralPath $sourceFile -Raw
[System.IO.File]::WriteAllText($destinationFile, $content, [System.Text.Encoding]::ASCII)

foreach ($obsoletePath in $obsoletePluginPaths) {
    if (Test-Path -LiteralPath $obsoletePath) {
        Remove-Item -LiteralPath $obsoletePath -Force -ErrorAction SilentlyContinue
    }
}

Write-Host ""
Write-Host "Deployed JW Command Search macro to:" -ForegroundColor Green
Write-Host "  $destinationFile"
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Restart ZBrush 2025.3 if it is open."
Write-Host "  2. Open Macro > JW."
Write-Host "  3. Ctrl+Alt+click JW Command Search, then press Ctrl+F."
Write-Host "  4. Save the hotkey in Preferences > Hotkeys > Store."

exit 0
