<#
.SYNOPSIS
  Creates App Runner VPC connector (or reuses by name). Step 4 of 6.
#>
param(
    [string]$ConnectorName = "bigboy-django-vpc-connector"
)
$ErrorActionPreference = "Stop"
. "$PSScriptRoot\_Common.ps1"

$state = Get-AppRunnerState
if (-not $state.VpcConnectorEgressSgId) { throw "Run 03-rds-vpc-sg.ps1 first." }

$list = Invoke-Aws -AwsArgs @("apprunner", "list-vpc-connectors", "--output", "json") | ConvertFrom-Json
$found = $list.VpcConnectors | Where-Object { $_.VpcConnectorName -eq $ConnectorName } | Select-Object -First 1
if ($found) {
    Write-Host "VPC connector already exists: $($found.VpcConnectorArn)"
    Save-AppRunnerState @{
        VpcConnectorArn = $found.VpcConnectorArn
        VpcConnectorName = $ConnectorName
    }
    Write-Host "OK - run 05-apprunner-langgraph.ps1 next."
    exit 0
}

$subnets = ($state.VpcConnectorSubnetIds -split "," | ForEach-Object { $_.Trim() } | Where-Object { $_ })
$sg = $state.VpcConnectorEgressSgId
$subnetArgs = @()
foreach ($s in $subnets) { $subnetArgs += $s }

Write-Host "Creating VPC connector $ConnectorName subnets=$($subnets -join ',') sg=$sg"
# One --subnets argument per subnet (space-separated single token fails CreateVpcConnector).
$createArgs = @("apprunner", "create-vpc-connector", "--vpc-connector-name", $ConnectorName)
foreach ($s in $subnets) {
    $createArgs += "--subnets"
    $createArgs += $s
}
$createArgs += "--security-groups"
$createArgs += $sg
$createArgs += "--output"
$createArgs += "json"
$out = Invoke-Aws -AwsArgs $createArgs | ConvertFrom-Json

$arn = $out.VpcConnector.VpcConnectorArn
Write-Host "Created: $arn (status may be IN_PROGRESS; polling until ACTIVE)"
Save-AppRunnerState @{
    VpcConnectorArn  = $arn
    VpcConnectorName = $ConnectorName
}

# Poll until AVAILABLE (up to ~5 min)
for ($i = 0; $i -lt 60; $i++) {
    $d = Invoke-Aws -AwsArgs @("apprunner", "describe-vpc-connector", "--vpc-connector-arn", $arn, "--output", "json") | ConvertFrom-Json
    $st = $d.VpcConnector.Status
    Write-Host "VPC connector status: $st"
    if ($st -eq "ACTIVE") { break }
    Start-Sleep -Seconds 5
}

Write-Host "OK - run 05-apprunner-langgraph.ps1 next."
