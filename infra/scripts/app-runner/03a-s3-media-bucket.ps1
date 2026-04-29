<#
.SYNOPSIS
  Alias for s3-media-only.ps1 (numbered flow). Same behavior.
#>
param(
    [string]$BucketName = "",
    [switch]$NoAppRunnerUpdate
)
$ErrorActionPreference = "Stop"
$splat = @{ BucketName = $BucketName }
if ($NoAppRunnerUpdate) { $splat['NoAppRunnerUpdate'] = $true }
& "$PSScriptRoot\s3-media-only.ps1" @splat
