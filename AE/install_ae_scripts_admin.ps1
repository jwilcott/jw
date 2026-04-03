param(
    [string]$SourceDir = $PSScriptRoot
)

$ErrorActionPreference = 'Stop'

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

$includeFiles = @(
    'aeVersionCore.jsxinc',
    'aeRenderFolderTools.jsxinc'
)

$managedFileNames = @(
    $scriptFiles +
    $panelFiles +
    $legacyPanelFiles +
    $includeFiles
) | Sort-Object -Unique

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
        Write-Warning "Unable to copy to $To : $($_.Exception.Message)"
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
        Write-Warning "Unable to remove $Path : $($_.Exception.Message)"
    }
}

if (-not (Test-Path -LiteralPath $SourceDir)) {
    throw "Source directory does not exist: $SourceDir"
}

function Get-InstalledAERoots {
    $roots = @()
    $programFilesAdobe = 'C:\Program Files\Adobe'

    if (-not (Test-Path -LiteralPath $programFilesAdobe)) {
        return $roots
    }

    Get-ChildItem -LiteralPath $programFilesAdobe -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match '^Adobe After Effects (\d{4})$' } |
        ForEach-Object {
            $supportFilesRoot = Join-Path $_.FullName 'Support Files'
            $scriptsRoot = Join-Path $supportFilesRoot 'Scripts'

            if (Test-Path -LiteralPath $supportFilesRoot) {
                $roots += [PSCustomObject]@{
                    Year = [int]$Matches[1]
                    ScriptsDir = $scriptsRoot
                }
            }
        }

    return $roots | Sort-Object Year -Unique
}

function Get-CanonicalUserScriptRoot {
    param(
        [int]$Year
    )

    $documentsRoot = Join-Path $env:USERPROFILE ("Documents\Adobe\After Effects {0}\Scripts" -f $Year)
    return $documentsRoot
}

function Get-ManagedScriptRoots {
    $roots = New-Object System.Collections.Generic.HashSet[string]([System.StringComparer]::OrdinalIgnoreCase)
    $searchBases = @(
        'C:\Program Files\Adobe',
        (Join-Path $env:USERPROFILE 'Documents\Adobe'),
        (Join-Path $env:APPDATA 'Adobe\After Effects')
    )

    foreach ($base in $searchBases) {
        if (-not (Test-Path -LiteralPath $base)) {
            continue
        }

        Get-ChildItem -LiteralPath $base -Recurse -File -ErrorAction SilentlyContinue |
            Where-Object { $managedFileNames -contains $_.Name } |
            ForEach-Object {
                $parent = $_.Directory
                if ($parent -and $parent.Name -eq 'ScriptUI Panels') {
                    $parent = $parent.Parent
                }

                if ($parent) {
                    [void]$roots.Add($parent.FullName)
                }
            }
    }

    return @($roots)
}

function Remove-ManagedFilesFromRoot {
    param(
        [string]$ScriptsDir
    )

    $panelsDir = Join-Path $ScriptsDir 'ScriptUI Panels'

    foreach ($file in $scriptFiles) {
        Remove-IfExists -Path (Join-Path $ScriptsDir $file)
    }

    foreach ($file in $panelFiles) {
        Remove-IfExists -Path (Join-Path $panelsDir $file)
    }

    foreach ($file in $legacyPanelFiles) {
        Remove-IfExists -Path (Join-Path $panelsDir $file)
    }

    foreach ($file in $includeFiles) {
        Remove-IfExists -Path (Join-Path $ScriptsDir $file)
        Remove-IfExists -Path (Join-Path $panelsDir $file)
    }
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

    foreach ($file in $includeFiles) {
        Copy-IfExists -From (Join-Path $SourceDir $file) -To (Join-Path $ScriptsDir $file)
        Remove-IfExists -Path (Join-Path $panelsDir $file)
    }
}

$installedRoots = Get-InstalledAERoots
if (-not $installedRoots) {
    throw 'No After Effects installations found in C:\Program Files\Adobe.'
}

Write-Host 'Detected AE installs:'
$installedRoots | ForEach-Object { Write-Host ("- After Effects {0}" -f $_.Year) }

$canonicalRoots = $installedRoots |
    ForEach-Object {
        [PSCustomObject]@{
            Year = $_.Year
            ScriptsDir = (Get-CanonicalUserScriptRoot -Year $_.Year)
        }
    }

Write-Host 'Deploying managed scripts to canonical user roots:'
$canonicalRoots | ForEach-Object { Write-Host "- $($_.ScriptsDir)" }

$managedRoots = Get-ManagedScriptRoots
$canonicalRootLookup = New-Object System.Collections.Generic.HashSet[string]([System.StringComparer]::OrdinalIgnoreCase)
$canonicalRoots | ForEach-Object { [void]$canonicalRootLookup.Add($_.ScriptsDir) }

Write-Host 'Cleaning managed duplicates from non-canonical roots:'
foreach ($root in $managedRoots | Sort-Object) {
    if ($canonicalRootLookup.Contains($root)) {
        continue
    }

    Write-Host "- $root"
    Remove-ManagedFilesFromRoot -ScriptsDir $root
}

foreach ($root in $canonicalRoots) {
    Sync-AE-ScriptRoot -ScriptsDir $root.ScriptsDir
}

Write-Host ''
Write-Host 'Done. If Teamocil Rx is already open, close and reopen that panel once. A full After Effects restart should not be necessary.' -ForegroundColor Green
