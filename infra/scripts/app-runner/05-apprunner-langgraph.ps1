<#
.SYNOPSIS
  Deploys LangGraph to App Runner (public egress, no VPC connector). Step 5 of 6.
  Generates RESEARCH_SERVICE_API_KEY and stores it in state.json for Django (step 6).
#>
param(
    [string]$ImageUri = "726101440593.dkr.ecr.us-east-2.amazonaws.com/langgraph-service-repo:latest",
    [string]$ServiceName = "bigboy-langgraph"
)
$ErrorActionPreference = "Stop"
. "$PSScriptRoot\_Common.ps1"

$state = Get-AppRunnerState
if (-not $state.InstanceRoleArn -or -not $state.EcrAccessRoleArn) { throw "Run 02-iam-roles.ps1 first." }

# A failed create-service could have written empty LangGraph fields; strip them so this run can succeed.
$corrupt = ($state.LanggraphServiceUrl -eq "https://") -or (
    $state.LanggraphServiceArn -and ([string]$state.LanggraphServiceArn).Trim() -eq ""
)
if ($corrupt -and (Test-Path $script:StatePath)) {
    $raw = Get-Content $script:StatePath -Raw -Encoding UTF8 | ConvertFrom-Json
    $o = [ordered]@{}
    foreach ($p in $raw.PSObject.Properties) {
        if ($p.Name -in @("LanggraphServiceArn", "LanggraphServiceUrl", "LanggraphServiceName", "ResearchServiceApiKey")) { continue }
        $o[$p.Name] = $p.Value
    }
    Write-TextUtf8NoBom -Path $script:StatePath -Content (($o | ConvertTo-Json -Depth 8) + [Environment]::NewLine)
    Write-Host "Repaired state.json (removed incomplete LangGraph entries from a failed run)."
    $state = Get-AppRunnerState
}

$list = Invoke-Aws -AwsArgs @("apprunner", "list-services", "--output", "json") | ConvertFrom-Json
$hit = $list.ServiceSummaryList | Where-Object { $_.ServiceName -eq $ServiceName } | Select-Object -First 1
if ($hit) {
    $svc = Invoke-Aws -AwsArgs @("apprunner", "describe-service", "--service-arn", $hit.ServiceArn, "--output", "json") | ConvertFrom-Json
    $url = $svc.Service.ServiceUrl
    Write-Host "Service already exists: https://$url"
    Save-AppRunnerState @{
        LanggraphServiceArn = $hit.ServiceArn
        LanggraphServiceUrl = "https://$url"
        LanggraphServiceName = $ServiceName
    }
    if (-not $state.ResearchServiceApiKey) {
        Write-Warning "state.json missing ResearchServiceApiKey - set it manually for Django or delete service and re-run to generate."
    }
    Write-Host "OK - run 06-apprunner-django.ps1 next."
    exit 0
}

$key = -join ((48..57 + 65..90 + 97..122 | Get-Random -Count 40 | ForEach-Object { [char]$_ }))

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
        "Port": "8765",
        "RuntimeEnvironmentVariables": {
          "AWS_REGION_NAME": "$script:AppRunnerRegion",
          "BEDROCK_MODEL_ID": "global.amazon.nova-2-lite-v1:0",
          "RESEARCH_SERVICE_API_KEY": "$key"
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
    "Interval": 10,
    "Path": "/health",
    "Protocol": "HTTP",
    "Timeout": 5,
    "UnhealthyThreshold": 5
  },
  "NetworkConfiguration": {
    "EgressConfiguration": {
      "EgressType": "DEFAULT"
    },
    "IngressConfiguration": {
      "IsPubliclyAccessible": true
    }
  }
}
"@

$tmp = New-AwsCliInputJsonTempPath
try {
    # BOM on cli-input-json causes "Invalid JSON received" (same class of bug as IAM trust files).
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
        ResearchServiceApiKey = $key
        LanggraphServiceArn   = $arn
        LanggraphServiceUrl   = "https://$url"
        LanggraphServiceName  = $ServiceName
    }
}
finally { Remove-Item $tmp -Force -ErrorAction SilentlyContinue }

Write-Host "Waiting for service to reach RUNNING (can take several minutes)..."
for ($i = 0; $i -lt 120; $i++) {
    $svc = Invoke-Aws -AwsArgs @("apprunner", "describe-service", "--service-arn", $arn, "--output", "json") | ConvertFrom-Json
    $st = $svc.Service.Status
    Write-Host "  Status: $st"
    if ($st -eq "RUNNING") { break }
    if ($st -eq "CREATE_FAILED" -or $st -eq "DELETE_FAILED") { throw "App Runner service failed: $st" }
    Start-Sleep -Seconds 10
}

Write-Host "OK - run 06-apprunner-django.ps1 next (pass DB password and Django SECRET_KEY)."
