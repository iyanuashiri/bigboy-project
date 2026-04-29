<#
.SYNOPSIS
  S3-only setup for Django media (post-deploy): bucket, public-access block, IAM on BigboyAppRunnerInstance,
  state.json, and optionally push AWS_S3_* env vars to the existing Django App Runner service.
.DESCRIPTION
  Use this when Django + LangGraph are already on App Runner. Does not create VPC, RDS, or new services.
  Requires IAM role BigboyAppRunnerInstance (from 02-iam-roles.ps1). AccountId is read from state.json or STS.
.PARAMETER BucketName
  Optional globally-unique bucket name. Default: bigboy-media-<AccountId>.
.PARAMETER NoAppRunnerUpdate
  If set, skip apprunner update-service (only bucket + IAM + state.json).
#>
param(
    [string]$BucketName = "",
    [switch]$NoAppRunnerUpdate
)
$ErrorActionPreference = "Stop"
. "$PSScriptRoot\_Common.ps1"

$state = Get-AppRunnerState
$account = $null
if ($state.AccountId) { $account = [string]$state.AccountId }
if (-not $account) {
    $idJson = Invoke-Aws -AwsArgs @("sts", "get-caller-identity", "--output", "json")
    $account = ($idJson | ConvertFrom-Json).Account
    if (-not $account) { throw "Could not resolve AWS account (state.json or STS)." }
}

$instRoleName = "BigboyAppRunnerInstance"
$name = if ($BucketName) { $BucketName.Trim().ToLower() } else { "bigboy-media-$account".ToLower() }
if ($name.Length -lt 3 -or $name.Length -gt 63) { throw "Invalid bucket name length: $name" }

$r = $script:AppRunnerRegion
Write-Host "=== S3 media (bucket + IAM) ==="
Write-Host "Bucket: $name | Region: $r | Instance role: $instRoleName"

# --- Head / create bucket ---
$prevEap = $ErrorActionPreference
$prevNative = $null
if (Test-Path variable:PSNativeCommandUseErrorActionPreference) {
    $prevNative = $PSNativeCommandUseErrorActionPreference
    $PSNativeCommandUseErrorActionPreference = $false
}
$ErrorActionPreference = "Continue"
& aws --region $r s3api head-bucket --bucket $name 2>$null | Out-Null
$headCode = $LASTEXITCODE
$ErrorActionPreference = $prevEap
if ($null -ne $prevNative) { $PSNativeCommandUseErrorActionPreference = $prevNative }

if ($headCode -ne 0) {
    Write-Host "Creating bucket..."
    if ($r -eq "us-east-1") {
        Invoke-Aws -AwsArgs @("s3api", "create-bucket", "--bucket", $name)
    }
    else {
        $cfgPath = New-AwsCliInputJsonTempPath -Extension ".bucketcfg.json"
        try {
            Write-TextUtf8NoBom -Path $cfgPath -Content ('{"LocationConstraint":"' + $r + '"}')
            $cfgUri = Get-AwsCliInputJsonFileUri $cfgPath
            Invoke-Aws -AwsArgs @(
                "s3api", "create-bucket", "--bucket", $name,
                "--create-bucket-configuration", $cfgUri
            )
        }
        finally { Remove-Item $cfgPath -Force -ErrorAction SilentlyContinue }
    }
}
else {
    Write-Host "Bucket already exists."
}

Invoke-Aws -AwsArgs @(
    "s3api", "put-public-access-block",
    "--bucket", $name,
    "--public-access-block-configuration",
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
)

# --- IAM inline policy on App Runner instance role ---
$bucketArn = "arn:aws:s3:::$name"
$policyDoc = @"
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "BigboyMediaBucketRW",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:AbortMultipartUpload",
        "s3:ListMultipartUploadParts"
      ],
      "Resource": "$bucketArn/*"
    },
    {
      "Sid": "BigboyMediaBucketList",
      "Effect": "Allow",
      "Action": ["s3:ListBucket"],
      "Resource": "$bucketArn"
    }
  ]
}
"@

$polPath = New-AwsCliInputJsonTempPath -Extension ".s3-policy.json"
try {
    Write-TextUtf8NoBom -Path $polPath -Content $policyDoc
    $polUri = Get-AwsCliInputJsonFileUri $polPath
    Write-Host "Attaching inline policy BigboyMediaS3 to $instRoleName ..."
    Invoke-Aws -AwsArgs @(
        "iam", "put-role-policy",
        "--role-name", $instRoleName,
        "--policy-name", "BigboyMediaS3",
        "--policy-document", $polUri
    ) | Out-Null
}
finally { Remove-Item $polPath -Force -ErrorAction SilentlyContinue }

Save-AppRunnerState @{
    MediaBucketName    = $name
    MediaBucketRegion  = $r
    MediaBucketArn     = $bucketArn
    S3MediaCompletedAt = (Get-Date).ToString("o")
}

Write-Host "state.json updated (MediaBucketName)."

# --- Optional: push env to existing Django App Runner service ---
if ($NoAppRunnerUpdate) {
    Write-Host ('Skipped App Runner update (-NoAppRunnerUpdate). Set AWS_S3_MEDIA_BUCKET_NAME=' + $name + ' and AWS_S3_REGION_NAME=' + $r + ' on your Django service, then deploy.')
    exit 0
}

$svcArn = $null
if ($state.DjangoServiceArn) { $svcArn = [string]$state.DjangoServiceArn }
if (-not $svcArn) {
    Write-Host ''
    Write-Host 'No DjangoServiceArn in state.json - set these on the Django App Runner service manually:'
    Write-Host ('  AWS_S3_MEDIA_BUCKET_NAME = ' + $name)
    Write-Host ('  AWS_S3_REGION_NAME       = ' + $r)
    Write-Host 'Then start a deployment (redeploy same image is fine).'
    exit 0
}

Write-Host ''
Write-Host ('=== Updating Django App Runner env (' + $svcArn + ') ===')
$descJson = Invoke-Aws -AwsArgs @("apprunner", "describe-service", "--service-arn", $svcArn, "--output", "json")
$desc = $descJson | ConvertFrom-Json
$src = $desc.Service.SourceConfiguration
if (-not $src.ImageRepository) {
    throw 'Django service is not an ImageRepository source; update env vars in the console.'
}
$img = $src.ImageRepository
$ic = $img.ImageConfiguration
if (-not $ic) { throw 'Missing ImageConfiguration on describe-service response.' }

$envMap = [ordered]@{}
$rv = $ic.RuntimeEnvironmentVariables
if ($rv) {
    foreach ($p in $rv.PSObject.Properties) {
        $envMap[$p.Name] = [string]$p.Value
    }
}
$envMap['AWS_S3_MEDIA_BUCKET_NAME'] = $name
$envMap['AWS_S3_REGION_NAME'] = $r

$envHt = @{}
foreach ($k in $envMap.Keys) { $envHt[$k] = [string]$envMap[$k] }

$portStr = if ($null -eq $ic.Port) { '8000' } else { [string]$ic.Port }
$newIc = [ordered]@{
    Port                        = $portStr
    RuntimeEnvironmentVariables = $envHt
}
if ($null -ne $ic.StartCommand -and [string]$ic.StartCommand) {
    $newIc['StartCommand'] = [string]$ic.StartCommand
}

$autoDep = $src.AutoDeploymentsEnabled
if ($null -eq $autoDep) { $autoDep = $false }
elseif ($autoDep -isnot [bool]) { $autoDep = [string]$autoDep -eq 'true' }

$updatePayload = [ordered]@{
    ServiceArn            = $svcArn
    SourceConfiguration   = [ordered]@{
        ImageRepository               = [ordered]@{
            ImageIdentifier     = [string]$img.ImageIdentifier
            ImageRepositoryType = [string]$img.ImageRepositoryType
            ImageConfiguration  = $newIc
        }
        AuthenticationConfiguration = $src.AuthenticationConfiguration
        AutoDeploymentsEnabled      = [bool]$autoDep
    }
}

$updPath = New-AwsCliInputJsonTempPath -Extension ".apprunner-update.json"
try {
    $updJson = ($updatePayload | ConvertTo-Json -Depth 20) + [Environment]::NewLine
    Write-TextUtf8NoBom -Path $updPath -Content $updJson
    $updUri = Get-AwsCliInputJsonFileUri $updPath
    $out = Invoke-Aws -AwsArgs @("apprunner", "update-service", "--cli-input-json", $updUri, "--output", "json")
    $op = $out | ConvertFrom-Json
    Write-Host ('update-service accepted. OperationId: ' + $op.OperationId)
    Write-Host 'Wait until the service finishes deploying, then retry uploads.'
}
finally { Remove-Item $updPath -Force -ErrorAction SilentlyContinue }
