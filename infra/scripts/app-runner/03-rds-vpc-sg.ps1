<#
.SYNOPSIS
  Ensures a security group for App Runner VPC egress exists and allows RDS PostgreSQL from it. Step 3 of 6.
#>
param(
    [string]$DbInstanceId = "bigboy-backend-db-instance-1",
    [string]$EgressSgName = "bigboy-apprunner-vpc-egress"
)
$ErrorActionPreference = "Stop"
. "$PSScriptRoot\_Common.ps1"

$state = Get-AppRunnerState
if (-not $state.AccountId) { throw "Run 01-verify-aws.ps1 first." }

$rdsJson = Invoke-Aws -AwsArgs @("rds", "describe-db-instances", "--db-instance-identifier", $DbInstanceId, "--output", "json")
$db = ($rdsJson | ConvertFrom-Json).DBInstances[0]
$vpcId = $db.DBSubnetGroup.VpcId
$rdsSgs = @($db.VpcSecurityGroups | ForEach-Object { $_.VpcSecurityGroupId })
$connectorSubnets = @(
    $db.DBSubnetGroup.Subnets[0].SubnetIdentifier
    $db.DBSubnetGroup.Subnets[1].SubnetIdentifier
) | ForEach-Object { $_ }
$connectorSubnetCsv = $connectorSubnets -join ","
Write-Host "VPC connector subnets: $connectorSubnetCsv"

Write-Host "RDS VPC: $vpcId RDS SGs: $($rdsSgs -join ', ')"

$existing = aws ec2 describe-security-groups --region $script:AppRunnerRegion --filters "Name=vpc-id,Values=$vpcId" "Name=group-name,Values=$EgressSgName" --query "SecurityGroups[0].GroupId" --output text 2>$null
$egressSg = $existing.Trim()
if (-not $egressSg -or $egressSg -eq "None") {
    $egressSg = (aws ec2 create-security-group --region $script:AppRunnerRegion --group-name $EgressSgName --description "App Runner VPC connector egress to RDS" --vpc-id $vpcId --query "GroupId" --output text).Trim()
    Write-Host "Created security group: $egressSg"
} else {
    Write-Host "Using existing security group: $egressSg"
}

foreach ($rdsSg in $rdsSgs) {
    $rules = aws ec2 describe-security-groups --region $script:AppRunnerRegion --group-ids $rdsSg --output json | ConvertFrom-Json
    $already = $false
    foreach ($ip in $rules.SecurityGroups[0].IpPermissions) {
        if ($ip.FromPort -eq 5432 -and $ip.ToPort -eq 5432) {
            foreach ($pair in $ip.UserIdGroupPairs) {
                if ($pair.GroupId -eq $egressSg) { $already = $true }
            }
        }
    }
    if ($already) {
        Write-Host "RDS SG $rdsSg already allows 5432 from $egressSg"
        continue
    }
    Write-Host "Authorizing 5432 on $rdsSg from $egressSg"
    aws ec2 authorize-security-group-ingress --group-id $rdsSg --protocol tcp --port 5432 --source-group $egressSg --region $script:AppRunnerRegion
    if ($LASTEXITCODE -ne 0) { throw "authorize-security-group-ingress failed" }
}

Save-AppRunnerState @{
    RdsVpcId              = $vpcId
    VpcConnectorSubnetIds = $connectorSubnetCsv
    RdsSecurityGroupIds   = ($rdsSgs -join ",")
    VpcConnectorEgressSgId = $egressSg
    RdsInstanceId         = $DbInstanceId
    RdsEndpointAddress    = $db.Endpoint.Address
    RdsPort               = [string]$db.Endpoint.Port
    RdsMasterUsername     = $db.MasterUsername
    RdsVpcSgCompletedAt   = (Get-Date).ToString("o")
}

Write-Host "OK - run 04-vpc-connector.ps1 next."
