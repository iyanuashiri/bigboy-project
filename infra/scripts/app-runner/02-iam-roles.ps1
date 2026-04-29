<#
.SYNOPSIS
  Creates IAM roles for App Runner (ECR pull + Bedrock instance role) if missing. Step 2 of 6.
  IAM is global; region flag only affects CLI session, not role location.
#>
$ErrorActionPreference = "Stop"
. "$PSScriptRoot\_Common.ps1"

$state = Get-AppRunnerState
if (-not $state.AccountId) { throw "Run 01-verify-aws.ps1 first." }

$account = $state.AccountId
$ecrRoleName = "BigboyAppRunnerEcrAccess"
$instRoleName = "BigboyAppRunnerInstance"

$ecrTrust = @"
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "Service": "build.apprunner.amazonaws.com" },
      "Action": "sts:AssumeRole"
    }
  ]
}
"@

$taskTrust = @"
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "Service": "tasks.apprunner.amazonaws.com" },
      "Action": "sts:AssumeRole"
    }
  ]
}
"@

$bedrockPolicy = @"
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": "*"
    }
  ]
}
"@

function Write-TextUtf8NoBom([string]$Path, [string]$Content) {
    $enc = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($Path, $Content, $enc)
}

function Ensure-Role([string]$Name, [string]$TrustJson) {
    # PS7: stderr from "role not found" can trigger Stop and abort the script.
    $saved = $ErrorActionPreference
    $ErrorActionPreference = "SilentlyContinue"
    try {
        aws iam get-role --role-name $Name *> $null
    }
    finally {
        $ErrorActionPreference = $saved
    }
    if ($LASTEXITCODE -eq 0) {
        Write-Host "IAM role exists: $Name"
        return
    }
    $trustPath = New-AwsCliInputJsonTempPath -Extension ".trust.json"
    try {
        # Set-Content -Encoding UTF8 writes a BOM; IAM rejects the JSON as MalformedPolicyDocument.
        Write-TextUtf8NoBom -Path $trustPath -Content $TrustJson
        $trustUri = Get-AwsCliInputJsonFileUri $trustPath
        aws iam create-role --role-name $Name --assume-role-policy-document $trustUri
        if ($LASTEXITCODE -ne 0) { throw "create-role $Name failed" }
        Write-Host "Created IAM role: $Name"
    }
    finally { Remove-Item $trustPath -Force -ErrorAction SilentlyContinue }
}

Ensure-Role $ecrRoleName $ecrTrust
$ErrorActionPreference = "SilentlyContinue"
aws iam attach-role-policy --role-name $ecrRoleName --policy-arn "arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess" *> $null
$attachEcr = $LASTEXITCODE
$ErrorActionPreference = "Stop"
if ($attachEcr -ne 0) { Write-Host "(attach ECR policy: may already be attached; verify in IAM console)" }

Ensure-Role $instRoleName $taskTrust
$polPath = New-AwsCliInputJsonTempPath -Extension ".policy.json"
try {
    Write-TextUtf8NoBom -Path $polPath -Content $bedrockPolicy
    $polUri = Get-AwsCliInputJsonFileUri $polPath
    aws iam put-role-policy --role-name $instRoleName --policy-name BigboyBedrockInvoke --policy-document $polUri
    if ($LASTEXITCODE -ne 0) { throw "put-role-policy failed" }
    Write-Host "Attached inline Bedrock policy to $instRoleName"
}
finally { Remove-Item $polPath -Force -ErrorAction SilentlyContinue }

$ecrArn = (aws iam get-role --role-name $ecrRoleName --query "Role.Arn" --output text).Trim()
$instArn = (aws iam get-role --role-name $instRoleName --query "Role.Arn" --output text).Trim()

Save-AppRunnerState @{
    EcrAccessRoleArn   = $ecrArn
    InstanceRoleArn    = $instArn
    IamRolesCompletedAt = (Get-Date).ToString("o")
}

Write-Host "OK - optional: .\s3-media-only.ps1 for S3 media — then run 03-rds-vpc-sg.ps1 next."
