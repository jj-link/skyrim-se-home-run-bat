param(
    [string]$OutputPath,
    [string]$SkseSourcePath,
    [string]$CommonSourcePath,
    [switch]$Diagnostics
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
if (-not $OutputPath) { $OutputPath = Join-Path $root 'Data' }
if (-not $SkseSourcePath) { $SkseSourcePath = Join-Path $root '.local\native\skse64' }
if (-not $CommonSourcePath) { $CommonSourcePath = Join-Path $root '.local\native\common' }
if (-not [IO.Path]::IsPathRooted($OutputPath)) { $OutputPath = Join-Path $root $OutputPath }
$OutputPath = [IO.Path]::GetFullPath($OutputPath)
$projectPrefix = [IO.Path]::GetFullPath($root).TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar
if (-not $OutputPath.StartsWith($projectPrefix, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Native build output must stay inside this project. Stage a Data directory here; do not build into Skyrim or MO2.'
}

# No downloads or source modifications. Use the same pinned official checkouts
# as the isolated SKSE runtime build; CMake verifies both revisions explicitly.
foreach ($source in @($SkseSourcePath, $CommonSourcePath)) {
    if (-not (Test-Path -LiteralPath (Join-Path $source 'CMakeLists.txt') -PathType Leaf)) {
        throw "Required official source checkout is missing: $source"
    }
}
$SkseSourcePath = (Resolve-Path -LiteralPath $SkseSourcePath).Path
$CommonSourcePath = (Resolve-Path -LiteralPath $CommonSourcePath).Path
$vswhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'
if (-not (Test-Path -LiteralPath $vswhere -PathType Leaf)) {
    throw 'Visual Studio Installer/vswhere is required to locate MSVC.'
}
$visualStudio = & $vswhere -latest -version '[18.0,19.0)' -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
if ($LASTEXITCODE -ne 0 -or -not $visualStudio) {
    throw 'Visual Studio 2026 with the C++ x64 tools is required.'
}
$cmake = Join-Path $visualStudio 'Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe'
if (-not (Test-Path -LiteralPath $cmake -PathType Leaf)) {
    throw 'Install the Visual Studio C++ CMake tools component.'
}
$buildPath = Join-Path $root '.local\native\home-run-bat-build'
$workPath = Join-Path $root '.local\work'
$diagnosticOption = if ($Diagnostics) { 'ON' } else { 'OFF' }
$previousEnvironment = @{}
try {
    New-Item -ItemType Directory -Force -Path $workPath | Out-Null
    foreach ($name in @('TMP', 'TEMP')) {
        $previousEnvironment[$name] = [Environment]::GetEnvironmentVariable($name, 'Process')
        [Environment]::SetEnvironmentVariable($name, $workPath, 'Process')
    }
    & $cmake -S (Join-Path $root 'native') -B $buildPath -G 'Visual Studio 18 2026' -A x64 `
        "-DCMAKE_GENERATOR_INSTANCE=$visualStudio" "-DSKSE_SOURCE_DIR=$SkseSourcePath" `
        "-DXSE_COMMON_SOURCE_DIR=$CommonSourcePath" "-DHRB_DATA_OUTPUT=$OutputPath" `
        "-DHRB_DIAGNOSTICS=$diagnosticOption"
    if ($LASTEXITCODE -ne 0) { throw 'Native CMake configuration failed.' }
    & $cmake --build $buildPath --config Release --target HomeRunBat --parallel
    if ($LASTEXITCODE -ne 0) { throw 'HomeRunBat.dll compilation failed.' }
    & $cmake --install $buildPath --config Release
    if ($LASTEXITCODE -ne 0) { throw 'HomeRunBat.dll staging failed.' }
    Write-Host "Native plugin: $(Join-Path $OutputPath 'SKSE\Plugins\HomeRunBat.dll')"
    if ($Diagnostics) {
        Write-Host 'Development contact logging is enabled. Rebuild without -Diagnostics before packaging.'
    }
}
finally {
    foreach ($name in $previousEnvironment.Keys) {
        [Environment]::SetEnvironmentVariable($name, $previousEnvironment[$name], 'Process')
    }
}
