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

Start-AdminElevationIfNeeded

if (-not (Test-Path -LiteralPath $SourceDir)) {
    throw "Source directory does not exist: $SourceDir"
}

$scriptFiles = @(
    'aeVersionUpSelected.jsx',
    'aeVersionUpSelectedTimeline.jsx',
    'aeVersionDownSelectedTimeline.jsx'
)

$panelFiles = @(
    'aeVersionDockPanel.jsx'
)

$includeFile = 'aeVersionCore.jsxinc'

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
    $scriptsDir = Join-Path $root 'Scripts'
    $panelsDir = Join-Path $scriptsDir 'ScriptUI Panels'

    New-Item -ItemType Directory -Path $scriptsDir -Force | Out-Null
    New-Item -ItemType Directory -Path $panelsDir -Force | Out-Null

    foreach ($file in $scriptFiles) {
        Copy-IfExists -From (Join-Path $SourceDir $file) -To (Join-Path $scriptsDir $file)
    }

    foreach ($file in $panelFiles) {
        Copy-IfExists -From (Join-Path $SourceDir $file) -To (Join-Path $panelsDir $file)
    }

    Copy-IfExists -From (Join-Path $SourceDir $includeFile) -To (Join-Path $scriptsDir $includeFile)
    Copy-IfExists -From (Join-Path $SourceDir $includeFile) -To (Join-Path $panelsDir $includeFile)
}

Write-Host ''
Write-Host 'Done. Restart After Effects to load updated scripts/panels.' -ForegroundColor Green
