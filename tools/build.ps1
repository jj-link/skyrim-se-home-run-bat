param(
    [string]$GamePath,
    [string]$OutputPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
if (-not $GamePath) {
    $GamePath = (Get-ItemProperty 'HKLM:\SOFTWARE\WOW6432Node\Bethesda Softworks\Skyrim Special Edition').'Installed Path'
}
$GamePath = (Resolve-Path -LiteralPath $GamePath).Path
if (-not $OutputPath) {
    $OutputPath = Join-Path $root 'Data'
}
$OutputPath = [IO.Path]::GetFullPath($OutputPath)
$compiler = Join-Path $GamePath 'Papyrus Compiler\PapyrusCompiler.exe'
$baseSources = Join-Path $GamePath 'Data\Source\Scripts'
$sources = Join-Path $root 'Data\Scripts\Source'
$scriptOutput = Join-Path $OutputPath 'Scripts'
$builder = Join-Path $PSScriptRoot 'PluginBuilder\PluginBuilder.csproj'
foreach ($required in @($compiler, (Join-Path $baseSources 'TESV_Papyrus_Flags.flg'), (Join-Path $GamePath 'Data\Skyrim.esm'))) {
    if (-not (Test-Path -LiteralPath $required)) {
        throw "Required Creation Kit/game file is missing: $required"
    }
}

$previousEnvironment = @{}
$buildEnvironment = @{
    TEMP = (Join-Path $root '.local\work')
    TMP = (Join-Path $root '.local\work')
    DOTNET_CLI_HOME = (Join-Path $root '.local\dotnet')
    NUGET_PACKAGES = (Join-Path $root '.local\nuget')
    DOTNET_CLI_TELEMETRY_OPTOUT = '1'
}
try {
    foreach ($name in $buildEnvironment.Keys) {
        $previousEnvironment[$name] = [Environment]::GetEnvironmentVariable($name, 'Process')
        if ($name -ne 'DOTNET_CLI_TELEMETRY_OPTOUT') {
            New-Item -ItemType Directory -Force -Path $buildEnvironment[$name] | Out-Null
        }
        [Environment]::SetEnvironmentVariable($name, $buildEnvironment[$name], 'Process')
    }
    New-Item -ItemType Directory -Force -Path $scriptOutput | Out-Null
    & dotnet restore $builder --locked-mode --nologo
    if ($LASTEXITCODE -ne 0) { throw 'Plugin dependency restore failed.' }
    & dotnet run --project $builder --configuration Release --no-restore -- (Join-Path $GamePath 'Data') $OutputPath
    if ($LASTEXITCODE -ne 0) { throw 'Plugin generation failed.' }

    Push-Location $baseSources
    try {
        & $compiler HRBLaunchEffect '-f=TESV_Papyrus_Flags.flg' "-i=$sources;$baseSources" "-o=$scriptOutput"
        if ($LASTEXITCODE -ne 0) { throw 'Papyrus compilation failed.' }
    }
    finally {
        Pop-Location
    }
}
finally {
    foreach ($name in $previousEnvironment.Keys) {
        [Environment]::SetEnvironmentVariable($name, $previousEnvironment[$name], 'Process')
    }
}
