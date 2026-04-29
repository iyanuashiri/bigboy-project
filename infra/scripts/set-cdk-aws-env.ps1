# CDK does not always pick up `aws login` credentials. Run from PowerShell before `cdk bootstrap` / `cdk deploy`:
#   . .\scripts\set-cdk-aws-env.ps1
$j = aws configure export-credentials | ConvertFrom-Json
$env:AWS_ACCESS_KEY_ID = $j.AccessKeyId
$env:AWS_SECRET_ACCESS_KEY = $j.SecretAccessKey
$env:AWS_SESSION_TOKEN = $j.SessionToken
if (-not $env:CDK_DEFAULT_REGION) { $env:CDK_DEFAULT_REGION = "us-east-1" }
if (-not $env:CDK_DEFAULT_ACCOUNT) {
  $env:CDK_DEFAULT_ACCOUNT = (aws sts get-caller-identity --query Account --output text)
}
Write-Host "CDK_DEFAULT_ACCOUNT=$($env:CDK_DEFAULT_ACCOUNT) CDK_DEFAULT_REGION=$($env:CDK_DEFAULT_REGION) (session exported)"
