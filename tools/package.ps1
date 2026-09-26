param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z]+(?:[.-][0-9A-Za-z]+)*)?$')]
    [string]$Version,
    [string]$InputPath,
    [string]$ArchivePath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
if (-not $InputPath) {
    $InputPath = Join-Path $root 'Data'
}
$InputPath = (Resolve-Path -LiteralPath $InputPath).Path
if (-not (Test-Path -LiteralPath $InputPath -PathType Container)) {
    throw "Package input must be an installable Data directory: $InputPath"
}
if (-not $ArchivePath) {
    $ArchivePath = Join-Path $root "build\HomeRunBat-$Version.zip"
}
$ArchivePath = [IO.Path]::GetFullPath($ArchivePath)
if ([IO.Path]::GetExtension($ArchivePath) -ine '.zip') {
    throw "ArchivePath must end in .zip: $ArchivePath"
}
if (Test-Path -LiteralPath $ArchivePath) {
    throw "Archive already exists; choose another ArchivePath or remove it explicitly: $ArchivePath"
}

# Archive names are relative to Skyrim's Data directory, not an enclosing Data folder.
$packagePaths = @(
    'HomeRunBat.esp'
    'Scripts/HRBLaunchEffect.pex'
    'Meshes/HomeRunBat/HomeRunBat.nif'
    'Textures/HomeRunBat/HomeRunBat.dds'
    'Textures/HomeRunBat/HomeRunBat_n.dds'
    'Sound/fx/HomeRunBat/impact.wav'
)
foreach ($relativePath in $packagePaths) {
    $source = Join-Path $InputPath $relativePath
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
        throw "Required package file is missing; run tools/build.ps1 first: $source"
    }
}

Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $ArchivePath) | Out-Null
$archive = [IO.Compression.ZipFile]::Open($ArchivePath, [IO.Compression.ZipArchiveMode]::Create)
try {
    try {
        foreach ($relativePath in $packagePaths) {
            $source = Join-Path $InputPath $relativePath
            [IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
                $archive, $source, $relativePath, [IO.Compression.CompressionLevel]::Optimal
            ) | Out-Null
        }
    }
    finally {
        $archive.Dispose()
    }
}
catch {
    Remove-Item -LiteralPath $ArchivePath -Force
    throw
}
Write-Output $ArchivePath
