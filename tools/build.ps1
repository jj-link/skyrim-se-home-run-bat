param(
    [string]$GamePath,
    [string]$OutputPath,
    [switch]$Diagnostics
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
$assetPaths = @(
    'Meshes\HomeRunBat\HomeRunBat.nif'
    'Textures\HomeRunBat\HomeRunBat.dds'
    'Textures\HomeRunBat\HomeRunBat_n.dds'
    'Sound\fx\HomeRunBat\impact.wav'
)
$assetRoot = Join-Path $root 'Data'
foreach ($relativePath in $assetPaths) {
    $asset = Join-Path $assetRoot $relativePath
    if (-not (Test-Path -LiteralPath $asset -PathType Leaf)) {
        throw "Required Home Run Bat asset is missing: $asset"
    }
}
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
    & (Join-Path $PSScriptRoot 'build-native.ps1') -OutputPath $OutputPath -Diagnostics:$Diagnostics
    & dotnet restore $builder --locked-mode --nologo
    if ($LASTEXITCODE -ne 0) { throw 'Plugin dependency restore failed.' }
    & dotnet run --project $builder --configuration Release --no-restore -- (Join-Path $GamePath 'Data') $OutputPath
    if ($LASTEXITCODE -ne 0) { throw 'Plugin generation failed.' }

    Push-Location $baseSources
    try {
        & $compiler HRBLaunchController '-f=TESV_Papyrus_Flags.flg' "-i=$sources;$baseSources" "-o=$scriptOutput"
        if ($LASTEXITCODE -ne 0) { throw 'Papyrus compilation failed.' }
    }
    finally {
        Pop-Location
    }

    foreach ($relativePath in $assetPaths) {
        $source = Join-Path $assetRoot $relativePath
        $destination = Join-Path $OutputPath $relativePath
        if (-not [string]::Equals($source, $destination, [StringComparison]::OrdinalIgnoreCase)) {
            New-Item -ItemType Directory -Force -Path (Split-Path -Parent $destination) | Out-Null
            Copy-Item -LiteralPath $source -Destination $destination -Force
        }
    }
}
finally {
    foreach ($name in $previousEnvironment.Keys) {
        [Environment]::SetEnvironmentVariable($name, $previousEnvironment[$name], 'Process')
    }
}
