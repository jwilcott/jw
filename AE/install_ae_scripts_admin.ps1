param(
    [string]$SourceDir = $PSScriptRoot
)

$ErrorActionPreference = 'Stop'

$currentIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($currentIdentity)
$isAdministrator = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdministrator) {
    $argumentList = @(
        '-ExecutionPolicy', 'Bypass',
        '-File', ('"{0}"' -f $PSCommandPath),
        '-SourceDir', ('"{0}"' -f $SourceDir)
    )

    Start-Process -FilePath 'powershell.exe' -Verb RunAs -ArgumentList $argumentList | Out-Null
    return
}

$targetYear = 2026
$aeRoot = "C:\Program Files\Adobe\Adobe After Effects $targetYear\Support Files"
$targetScriptsDir = Join-Path $aeRoot 'Scripts'
$targetPanelsDir = Join-Path $targetScriptsDir 'ScriptUI Panels'

$scriptFiles = @(
    'aeExportTrackedCameraToMaya.jsx',
    'aeVersionUpSelected.jsx',
    'aeVersionUpSelectedTimeline.jsx',
    'aeVersionDownSelectedTimeline.jsx'
)

$panelFiles = @(
    'Teamocil Rx.jsx'
)

$includeFiles = @(
    'aeVersionCore.jsxinc',
    'aeRenderFolderTools.jsxinc'
)

$legacyFilesToRemove = @(
    (Join-Path $targetPanelsDir 'aeVersionDockPanel.jsx')
)

function Copy-IfExists {
    param(
        [string]$From,
        [string]$To
    )

    if (-not (Test-Path -LiteralPath $From)) {
        Write-Warning "Missing source file: $From"
        return
    }

    try {
        Copy-Item -LiteralPath $From -Destination $To -Force
        Write-Host "Copied: $(Split-Path -Leaf $From) -> $To"
    } catch {
        Write-Warning ("Unable to copy to {0} : {1}" -f $To, $_.Exception.Message)
    }
}

function Remove-IfExists {
    param(
        [string]$Path
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        return
    }

    try {
        Remove-Item -LiteralPath $Path -Force
        Write-Host "Removed legacy file: $Path"
    } catch {
        Write-Warning ("Unable to remove {0} : {1}" -f $Path, $_.Exception.Message)
    }
}

if (-not (Test-Path -LiteralPath $SourceDir)) {
    throw "Source directory does not exist: $SourceDir"
}

if (-not (Test-Path -LiteralPath $aeRoot)) {
    throw "After Effects $targetYear Support Files folder does not exist: $aeRoot"
}

New-Item -ItemType Directory -Path $targetScriptsDir -Force | Out-Null
New-Item -ItemType Directory -Path $targetPanelsDir -Force | Out-Null

Write-Host ("Installing AE scripts to After Effects {0}:" -f $targetYear)
Write-Host "- $targetScriptsDir"

foreach ($legacyPath in $legacyFilesToRemove) {
    Remove-IfExists -Path $legacyPath
}

foreach ($file in $scriptFiles) {
    Copy-IfExists -From (Join-Path $SourceDir $file) -To (Join-Path $targetScriptsDir $file)
}

foreach ($file in $panelFiles) {
    Copy-IfExists -From (Join-Path $SourceDir $file) -To (Join-Path $targetPanelsDir $file)
}

foreach ($file in $includeFiles) {
    Copy-IfExists -From (Join-Path $SourceDir $file) -To (Join-Path $targetScriptsDir $file)
    Remove-IfExists -Path (Join-Path $targetPanelsDir $file)
}

Write-Host ''
Write-Host 'Done. Opening the Scripts folder now.' -ForegroundColor Green
Invoke-Item -LiteralPath $targetScriptsDir
