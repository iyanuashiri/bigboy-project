<#
.SYNOPSIS
  Deploys Django to App Runner with VPC connector to RDS. Step 6 of 6.
.PARAMETER DatabasePassword
  Aurora / Postgres master password for DATABASE_USER (default postgres).
.PARAMETER DjangoSecretKey
  Django SECRET_KEY (generate a long random string for production).
#>
param(
    [Parameter(Mandatory = $true)][SecureString]$DatabasePassword,
    [Parameter(Mandatory = $true)][SecureString]$DjangoSecretKey,
    [string]$ImageUri = "726101440593.dkr.ecr.us-east-2.amazonaws.com/bigboy-backend-repo:latest",
    [string]$ServiceName = "bigboy-django",
    [string]$DatabaseName = "postgres",
    [string]$DatabaseUser = "postgres"
)
$ErrorActionPreference = "Stop"
. "$PSScriptRoot\_Common.ps1"

$state = Get-AppRunnerState
foreach ($req in @(
        "InstanceRoleArn", "EcrAccessRoleArn", "VpcConnectorArn",
        "RdsEndpointAddress", "RdsPort", "LanggraphServiceUrl", "ResearchServiceApiKey"
    )) {
    if (-not $state.$req) { throw "state.json missing '$req'. Run earlier steps (05 must finish first)." }
}

$dbPass = Unwrap-SecureString $DatabasePassword
$secKey = Unwrap-SecureString $DjangoSecretKey
# Escape for JSON
$dbPassJson = $dbPass.Replace('\', '\\').Replace('"', '\"')
$secKeyJson = $secKey.Replace('\', '\\').Replace('"', '\"')

$reg = $script:AppRunnerRegion
$s3EnvJson = ""
if ($state.MediaBucketName) {
    $bn = [string]$state.MediaBucketName
    $s3EnvJson = ",`n          ""AWS_S3_MEDIA_BUCKET_NAME"": ""$($bn.Replace('\','\\').Replace('"','\"'))"",`n          ""AWS_S3_REGION_NAME"": ""$reg"""
}

$list = Invoke-Aws -AwsArgs @("apprunner", "list-services", "--output", "json") | ConvertFrom-Json
$hit = $list.ServiceSummaryList | Where-Object { $_.ServiceName -eq $ServiceName } | Select-Object -First 1
if ($hit) {
    $svc = Invoke-Aws -AwsArgs @("apprunner", "describe-service", "--service-arn", $hit.ServiceArn, "--output", "json") | ConvertFrom-Json
    $url = $svc.Service.ServiceUrl
    Write-Host "Service already exists: https://$url"
    Save-AppRunnerState @{
        DjangoServiceArn  = $hit.ServiceArn
        DjangoServiceUrl  = "https://$url"
        DjangoServiceName = $ServiceName
    }
    Write-Host "Amplify: set VITE_API_BASE_URL=https://$url/api/v1 and rebuild."
    exit 0
}

$json = @"
{
  "ServiceName": "$ServiceName",
  "SourceConfiguration": {
    "AuthenticationConfiguration": {
      "AccessRoleArn": "$($state.EcrAccessRoleArn)"
    },
    "AutoDeploymentsEnabled": false,
    "ImageRepository": {
      "ImageConfiguration": {
        "Port": "8000",
        "RuntimeEnvironmentVariables": {
          "DEBUG": "False",
          "SECRET_KEY": "$secKeyJson",
          "DATABASE_NAME": "$DatabaseName",
          "DATABASE_USER": "$DatabaseUser",
          "DATABASE_PASSWORD": "$dbPassJson",
          "DATABASE_HOST": "$($state.RdsEndpointAddress)",
          "DATABASE_PORT": "$($state.RdsPort)",
          "LANGGRAPH_SERVICE_URL": "$($state.LanggraphServiceUrl)",
          "LANGGRAPH_SERVICE_API_KEY": "$($state.ResearchServiceApiKey)",
          "LANGGRAPH_SERVICE_TIMEOUT": "120"$s3EnvJson
        }
      },
      "ImageIdentifier": "$ImageUri",
      "ImageRepositoryType": "ECR"
    }
  },
  "InstanceConfiguration": {
    "Cpu": "1024",
    "Memory": "2048",
    "InstanceRoleArn": "$($state.InstanceRoleArn)"
  },
  "HealthCheckConfiguration": {
    "HealthyThreshold": 1,
    "Interval": 15,
    "Path": "/healthz",
    "Protocol": "HTTP",
    "Timeout": 10,
    "UnhealthyThreshold": 5
  },
  "NetworkConfiguration": {
    "EgressConfiguration": {
      "EgressType": "VPC",
      "VpcConnectorArn": "$($state.VpcConnectorArn)"
    },
    "IngressConfiguration": {
      "IsPubliclyAccessible": true
    }
  }
}
"@

$tmp = New-AwsCliInputJsonTempPath
try {
    Write-TextUtf8NoBom -Path $tmp -Content $json
    $tmpUri = Get-AwsCliInputJsonFileUri $tmp
    Write-Host "Creating App Runner service $ServiceName ..."
    $createOut = Invoke-Aws -AwsArgs @("apprunner", "create-service", "--cli-input-json", $tmpUri, "--output", "json")
    $created = $createOut | ConvertFrom-Json
    $arn = $created.Service.ServiceArn
    $url = $created.Service.ServiceUrl
    if (-not $arn -or -not $url) { throw "create-service returned unexpected response (missing ARN or URL)." }
    Write-Host "Create started. ARN=$arn URL=https://$url"
    Save-AppRunnerState @{
        DjangoServiceArn   = $arn
        DjangoServiceUrl   = "https://$url"
        DjangoServiceName  = $ServiceName
    }
}
finally { Remove-Item $tmp -Force -ErrorAction SilentlyContinue }

Write-Host "Waiting for RUNNING..."
for ($i = 0; $i -lt 120; $i++) {
    $svc = Invoke-Aws -AwsArgs @("apprunner", "describe-service", "--service-arn", $arn, "--output", "json") | ConvertFrom-Json
    $st = $svc.Service.Status
    Write-Host "  Status: $st"
    if ($st -eq "RUNNING") { break }
    if ($st -eq "CREATE_FAILED" -or $st -eq "DELETE_FAILED") { throw "App Runner service failed: $st" }
    Start-Sleep -Seconds 10
}

Write-Host ""
Write-Host "Done. Set Amplify env:"
Write-Host "  VITE_API_BASE_URL=https://$url/api/v1"
Write-Host "Then trigger a new Amplify build."
