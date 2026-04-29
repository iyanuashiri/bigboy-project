<#
.SYNOPSIS
  Verifies AWS CLI + credentials and writes account/region to state.json (step 1 of 6).
#>
$ErrorActionPreference = "Stop"
. "$PSScriptRoot\_Common.ps1"

Write-Host "Region: $script:AppRunnerRegion"
$id = Invoke-Aws -AwsArgs @("sts", "get-caller-identity", "--output", "json") | ConvertFrom-Json
Write-Host "Account: $($id.Account) ARN: $($id.Arn)"

Save-AppRunnerState @{
    AccountId   = $id.Account
    Region      = $script:AppRunnerRegion
    VerifiedAt  = (Get-Date).ToString("o")
}

Write-Host "OK - run 02-iam-roles.ps1 next."
