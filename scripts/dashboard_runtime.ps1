param(
    [ValidateSet('Resolve', 'Check')][string]$Mode = 'Check',
    [string]$HealthUrl = 'http://127.0.0.1:8000/health',
    [int]$TimeoutSeconds = 0
)

if ($Mode -eq 'Resolve') {
    $revision = & git -C (Split-Path $PSScriptRoot -Parent) rev-parse HEAD 2>$null
    if ($LASTEXITCODE -eq 0 -and $revision -cmatch '\A[0-9a-f]{40}\z') {
        Write-Output $revision
        exit 0
    }
    exit 1
}

$expected = $env:AI_INFRA_SOURCE_REVISION
if ($expected -cnotmatch '\A[0-9a-f]{40}\z') { exit 1 }
$deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
do {
    try {
        $health = Invoke-RestMethod -Uri $HealthUrl -TimeoutSec 2
        if ($health.status -eq 'OK' -and $health.database -eq 'READY') {
            $actual = $health.source_revision
            if ($actual -is [string] -and $actual -cmatch '\A[0-9a-f]{40}\z') {
                if ($actual -ceq $expected) { exit 0 }
            } else { $actual = 'missing-or-invalid' }
            Write-Output "[ERROR] Stale backend/version mismatch: checkout=$expected running=$actual."
            Write-Output 'Close/restart the existing dashboard process. No process was terminated.'
            exit 2
        }
    } catch {}
    if ([DateTime]::UtcNow -ge $deadline) { exit 1 }
    Start-Sleep -Seconds 1
} while ($true)
