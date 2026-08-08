$ErrorActionPreference = "Stop"

$RepositoryRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepositoryRoot

& (Join-Path $PSScriptRoot "build_windows.ps1")

$CompilerCandidates = @(
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
    "$env:ChocolateyInstall\bin\ISCC.exe"
)
$Compiler = $CompilerCandidates | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1
if (-not $Compiler) {
    throw "Inno Setup 6 compiler was not found."
}

& $Compiler (Join-Path $RepositoryRoot "packaging\AIContentStudio.iss")
if ($LASTEXITCODE -ne 0) {
    throw "Inno Setup failed with exit code $LASTEXITCODE"
}

$Installer = Join-Path $RepositoryRoot "release\AIContentStudio-Setup-0.19.0-windows-x64.exe"
if (-not (Test-Path $Installer)) {
    throw "Installer build completed without the expected output: $Installer"
}
Write-Host "Built $Installer"
