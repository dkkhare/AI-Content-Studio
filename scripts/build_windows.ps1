$ErrorActionPreference = "Stop"

$RepositoryRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepositoryRoot

python -m pip install --upgrade pip
python -m pip install -r requirements.txt -r requirements-build.txt
python -m PyInstaller --noconfirm --clean AIContentStudio.spec

$Executable = Join-Path $RepositoryRoot "dist\AIContentStudio\AIContentStudio.exe"
if (-not (Test-Path $Executable)) {
    throw "Windows build completed without the expected executable: $Executable"
}

Write-Host "Built $Executable"
