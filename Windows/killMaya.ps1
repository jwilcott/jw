param(
    [int]$TimeoutSeconds = 15
)

$names = @('maya', 'mayabatch', 'mayapy')
$deadline = (Get-Date).AddSeconds($TimeoutSeconds)
$frozenLeft = $false

do {
    $frozen = Get-Process -Name $names -ErrorAction SilentlyContinue | Where-Object { $_.Responding -eq $false }

    foreach ($proc in $frozen) {
        try {
            $cimProc = Get-CimInstance Win32_Process -Filter ("ProcessId=" + $proc.Id) -ErrorAction Stop
            Invoke-CimMethod -InputObject $cimProc -MethodName Terminate -ErrorAction Stop | Out-Null
        }
        catch {
            try {
                Stop-Process -Id $proc.Id -Force -ErrorAction Stop
            }
            catch {
            }
        }
    }

    if (-not $frozen) {
        Get-Process -Name $names -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    }

    Start-Sleep -Milliseconds 400
    $frozenLeft = @(Get-Process -Name $names -ErrorAction SilentlyContinue | Where-Object { $_.Responding -eq $false }).Count -gt 0
}
while ($frozenLeft -and (Get-Date) -lt $deadline)

if ($frozenLeft) {
    exit 2
}

exit 0
