# Dot-source from numbered scripts:  . "$PSScriptRoot\_Common.ps1"
$script:AppRunnerRegion = if ($env:AWS_DEFAULT_REGION) { $env:AWS_DEFAULT_REGION } else { "us-east-2" }
$script:StatePath = Join-Path $PSScriptRoot "state.json"

function Write-TextUtf8NoBom([string]$Path, [string]$Content) {
    $enc = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($Path, $Content, $enc)
}

# AWS CLI --cli-input-json breaks when the path contains spaces (e.g. C:\Users\First Last\...).
# Use %WINDIR%\Temp (usually C:\Windows\Temp) and a proper file: URI with %20 encoding.
function New-AwsCliInputJsonTempPath([string]$Extension = ".json") {
    $base = if ($env:WINDIR) { $env:WINDIR } elseif ($env:SystemRoot) { $env:SystemRoot } else { $null }
    $dir = if ($base) { Join-Path $base "Temp" } else { $null }
    if (-not $dir -or -not (Test-Path -LiteralPath $dir)) {
        $dir = [IO.Path]::GetTempPath()
    }
    return Join-Path $dir ("bb-aws-cli-" + [Guid]::NewGuid().ToString("N") + $Extension)
}

function Get-AwsCliInputJsonFileUri([string]$LocalPath) {
    $full = [IO.Path]::GetFullPath($LocalPath)
    $norm = $full -replace '\\', '/'
    # AWS CLI v2 on Windows: file:///C:/... from .NET AbsoluteUri breaks paramfile load (Errno 22).
    # Use file://C:/... and percent-encode path segments (spaces, etc.).
    $isWin = $env:OS -match 'Windows'
    if ($isWin -and $norm -match '^[A-Za-z]:(/.*)?$') {
        $drive = $norm.Substring(0, 1)
        $tail = $norm.Substring(2).TrimStart('/')
        if (-not $tail) { return "file://$drive`:/" }
        $encoded = ($tail.Split([char]'/') | Where-Object { $_ } | ForEach-Object { [Uri]::EscapeDataString($_) }) -join '/'
        return "file://$drive`:/$encoded"
    }
    return ([Uri]::new($full)).AbsoluteUri
}

function Get-AppRunnerState {
    if (-not (Test-Path $script:StatePath)) {
        return [ordered]@{}
    }
    $raw = Get-Content $script:StatePath -Raw -Encoding UTF8 | ConvertFrom-Json
    $h = [ordered]@{}
    foreach ($p in $raw.PSObject.Properties) {
        $h[$p.Name] = $p.Value
    }
    return $h
}

function Save-AppRunnerState([System.Collections.IDictionary]$Patch) {
    $cur = Get-AppRunnerState
    foreach ($k in $Patch.Keys) {
        $cur[$k] = $Patch[$k]
    }
    Write-TextUtf8NoBom -Path $script:StatePath -Content (($cur | ConvertTo-Json -Depth 8) + [Environment]::NewLine)
    Write-Host "Wrote $script:StatePath"
}

function Invoke-Aws {
    param(
        [Parameter(Mandatory = $true)][string[]]$AwsArgs,
        [string]$RegionOverride
    )
    $r = if ($RegionOverride) { $RegionOverride } else { $script:AppRunnerRegion }
    $all = @("--region", $r) + $AwsArgs
    # PS 7.2+: native stderr / non-zero can throw under $ErrorActionPreference=Stop before we read $LASTEXITCODE.
    $prevEap = $ErrorActionPreference
    $prevNative = $null
    if (Test-Path variable:PSNativeCommandUseErrorActionPreference) {
        $prevNative = $PSNativeCommandUseErrorActionPreference
        $PSNativeCommandUseErrorActionPreference = $false
    }
    $ErrorActionPreference = "Continue"
    $stderrPath = New-AwsCliInputJsonTempPath -Extension ".aws-stderr.txt"
    try {
        $raw = & aws @all 2>$stderrPath
        $code = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $prevEap
        if ($null -ne $prevNative) { $PSNativeCommandUseErrorActionPreference = $prevNative }
    }
    $stderrText = ""
    if (Test-Path -LiteralPath $stderrPath) {
        $stderrText = Get-Content -LiteralPath $stderrPath -Raw -ErrorAction SilentlyContinue
        Remove-Item -LiteralPath $stderrPath -Force -ErrorAction SilentlyContinue
    }
    if ($code -ne 0) {
        $msg = "aws failed (exit $code): $($AwsArgs -join ' ')"
        if ($null -ne $stderrText -and $stderrText.Trim()) { $msg += "`n" + $stderrText.Trim() }
        throw $msg
    }
    if ($null -eq $raw) { return "" }
    if ($raw -is [System.Array]) { return ($raw -join [Environment]::NewLine) }
    return [string]$raw
}

function Unwrap-SecureString([SecureString]$s) {
    $b = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($s)
    try { [Runtime.InteropServices.Marshal]::PtrToStringUni($b) }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($b) }
}
