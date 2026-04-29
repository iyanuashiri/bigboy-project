<#
.SYNOPSIS
  Points the Django App Runner health check at GET /healthz (plain 200, no DB).
  Run after rebuilding and pushing the backend image that includes config/health.py.
#>
param(
    [string]$HealthCheckPath = "/healthz",
    [int]$Interval = 15,
    [int]$Timeout = 10,
    [int]$HealthyThreshold = 1,
    [int]$UnhealthyThreshold = 5
)
$ErrorActionPreference = "Stop"
. "$PSScriptRoot\_Common.ps1"

$state = Get-AppRunnerState
if (-not $state.DjangoServiceArn) {
    throw "state.json missing DjangoServiceArn. Create the service with 06 first."
}

Write-Host "Updating health check on $($state.DjangoServiceArn) -> Path=$HealthCheckPath ..."
Invoke-Aws -AwsArgs @(
    "apprunner", "update-service",
    "--service-arn", $state.DjangoServiceArn,
    "--health-check-configuration",
    "Protocol=HTTP,Path=$HealthCheckPath,Interval=$Interval,Timeout=$Timeout,HealthyThreshold=$HealthyThreshold,UnhealthyThreshold=$UnhealthyThreshold",
    "--output", "json"
) | Out-Null

Write-Host "OK. App Runner will start a new deployment; ensure :latest includes the /healthz route."
