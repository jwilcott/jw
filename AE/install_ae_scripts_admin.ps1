param(
    [string]$SourceDir = $PSScriptRoot
)

$ErrorActionPreference = 'Stop'

function Start-AdminElevationIfNeeded {
    $currentIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentIdentity)
    $isAdmin = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

    if (-not $isAdmin) {
        Write-Host 'Requesting Administrator privileges...'
        $argList = @(
            '-NoProfile'
            '-ExecutionPolicy', 'Bypass'
            '-File', ('"{0}"' -f $PSCommandPath)
            '-SourceDir', ('"{0}"' -f $SourceDir)
        ) -join ' '

        Start-Process -FilePath 'powershell.exe' -Verb RunAs -ArgumentList $argList | Out-Null
        exit 0
    }
}

function Copy-IfExists {
    param(
        [string]$From,
        [string]$To
    )

    if (-not (Test-Path -LiteralPath $From)) {
        Write-Warning "Missing source file: $From"
        return
    }

    Copy-Item -LiteralPath $From -Destination $To -Force
    Write-Host "Copied: $(Split-Path -Leaf $From) -> $To"
}

function Remove-IfExists {
    param(
        [string]$Path
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        return
    }

    Remove-Item -LiteralPath $Path -Force
    Write-Host "Removed legacy file: $Path"
}

Start-AdminElevationIfNeeded

if (-not (Test-Path -LiteralPath $SourceDir)) {
    throw "Source directory does not exist: $SourceDir"
}

$scriptFiles = @(
    'aeExportTrackedCameraToMaya.jsx',
    'aeVersionUpSelected.jsx',
    'aeVersionUpSelectedTimeline.jsx',
    'aeVersionDownSelectedTimeline.jsx'
)

$panelFiles = @(
    'Teamocil Rx.jsx'
)

$legacyPanelFiles = @(
    'aeVersionDockPanel.jsx'
)

$includeFile = 'aeVersionCore.jsxinc'

function Get-UserScriptRoots {
    $roots = New-Object System.Collections.Generic.List[string]

    $documentsAdobe = Join-Path $env:USERPROFILE 'Documents\Adobe'
    if (Test-Path -LiteralPath $documentsAdobe) {
        Get-ChildItem -LiteralPath $documentsAdobe -Directory -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -like 'After Effects *' } |
            ForEach-Object {
                $scriptsRoot = Join-Path $_.FullName 'Scripts'
                if (-not $roots.Contains($scriptsRoot)) {
                    $roots.Add($scriptsRoot)
                }
            }
    }

    $roamingAdobe = Join-Path $env:APPDATA 'Adobe\After Effects'
    if (Test-Path -LiteralPath $roamingAdobe) {
        Get-ChildItem -LiteralPath $roamingAdobe -Directory -ErrorAction SilentlyContinue |
            ForEach-Object {
                $scriptsRoot = Join-Path $_.FullName 'Scripts'
                if (-not $roots.Contains($scriptsRoot)) {
                    $roots.Add($scriptsRoot)
                }
            }
    }

    return $roots
}

function Sync-AE-ScriptRoot {
    param(
        [string]$ScriptsDir
    )

    $panelsDir = Join-Path $ScriptsDir 'ScriptUI Panels'

    New-Item -ItemType Directory -Path $ScriptsDir -Force | Out-Null
    New-Item -ItemType Directory -Path $panelsDir -Force | Out-Null

    foreach ($file in $scriptFiles) {
        Copy-IfExists -From (Join-Path $SourceDir $file) -To (Join-Path $ScriptsDir $file)
    }

    foreach ($file in $panelFiles) {
        Copy-IfExists -From (Join-Path $SourceDir $file) -To (Join-Path $panelsDir $file)
    }

    foreach ($file in $legacyPanelFiles) {
        Remove-IfExists -Path (Join-Path $panelsDir $file)
    }

    Copy-IfExists -From (Join-Path $SourceDir $includeFile) -To (Join-Path $ScriptsDir $includeFile)
    Copy-IfExists -From (Join-Path $SourceDir $includeFile) -To (Join-Path $panelsDir $includeFile)
}

$aeRoots = Get-ChildItem 'C:\Program Files\Adobe' -Directory |
    Where-Object { $_.Name -like 'Adobe After Effects *' } |
    ForEach-Object { Join-Path $_.FullName 'Support Files' } |
    Where-Object { Test-Path -LiteralPath $_ }

if (-not $aeRoots) {
    throw 'No After Effects installations found in C:\Program Files\Adobe.'
}

Write-Host 'Detected AE installs:'
$aeRoots | ForEach-Object { Write-Host "- $_" }

foreach ($root in $aeRoots) {
    Sync-AE-ScriptRoot -ScriptsDir (Join-Path $root 'Scripts')
}

$userScriptRoots = Get-UserScriptRoots
if ($userScriptRoots.Count -gt 0) {
    Write-Host 'Detected user AE script folders:'
    $userScriptRoots | ForEach-Object { Write-Host "- $_" }

    foreach ($scriptsDir in $userScriptRoots) {
        Sync-AE-ScriptRoot -ScriptsDir $scriptsDir
    }
}

Write-Host ''
Write-Host 'Done. Restart After Effects to load updated scripts/panels.' -ForegroundColor Green
