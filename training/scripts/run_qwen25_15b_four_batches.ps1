param(
    [Parameter(Mandatory = $true)] [string] $CliPath,
    [Parameter(Mandatory = $true)] [string] $AConfigPath,
    [Parameter(Mandatory = $true)] [string] $BConfigPath,
    [Parameter(Mandatory = $true)] [string] $AOutputPath,
    [Parameter(Mandatory = $true)] [string] $BOutputPath,
    [Parameter(Mandatory = $true)] [string] $ALogPath,
    [Parameter(Mandatory = $true)] [string] $BLogPath,
    [Parameter(Mandatory = $true)] [string] $StatusPath
)

$ErrorActionPreference = 'Continue'
$logDirectory = Split-Path -Parent $ALogPath
New-Item -ItemType Directory -Force $logDirectory | Out-Null

function Write-Status([string] $status, [hashtable] $extra = @{}) {
    $payload = @{ status = $status; timestamp = (Get-Date).ToString('o') }
    foreach ($entry in $extra.GetEnumerator()) { $payload[$entry.Key] = $entry.Value }
    $payload | ConvertTo-Json -Compress | Set-Content -Encoding utf8 -LiteralPath $StatusPath
}

Write-Status 'A_RUNNING' @{ model = 'Qwen2.5-1.5B-Instruct'; log = $ALogPath }
& $CliPath train $AConfigPath *> $ALogPath
$aExit = $LASTEXITCODE
$aAdapter = Join-Path $AOutputPath 'adapter_model.safetensors'
$aResults = Join-Path $AOutputPath 'train_results.json'
if ($aExit -ne 0 -or -not (Test-Path $aAdapter) -or -not (Test-Path $aResults)) {
    Write-Status 'A_FAILED_B_NOT_STARTED' @{ exit_code = $aExit; model = 'Qwen2.5-1.5B-Instruct'; log = $ALogPath }
    exit 2
}

Write-Status 'A_COMPLETE_B_RUNNING' @{ a_exit_code = $aExit; model = 'Qwen2.5-1.5B-Instruct'; log = $BLogPath }
& $CliPath train $BConfigPath *> $BLogPath
$bExit = $LASTEXITCODE
$bAdapter = Join-Path $BOutputPath 'adapter_model.safetensors'
$bResults = Join-Path $BOutputPath 'train_results.json'
if ($bExit -ne 0 -or -not (Test-Path $bAdapter) -or -not (Test-Path $bResults)) {
    Write-Status 'B_FAILED' @{ exit_code = $bExit; model = 'Qwen2.5-1.5B-Instruct'; log = $BLogPath }
    exit 3
}

Write-Status 'A_AND_B_COMPLETE' @{ a_exit_code = $aExit; b_exit_code = $bExit; model = 'Qwen2.5-1.5B-Instruct' }
exit 0
