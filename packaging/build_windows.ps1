$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

Set-Location frontend
corepack pnpm install --frozen-lockfile
$env:NEXT_TELEMETRY_DISABLED = "1"
corepack pnpm exec next build
Set-Location $ProjectRoot

python -m venv packaging\.venv-build
packaging\.venv-build\Scripts\python.exe -m pip install -r backend\requirements.txt
packaging\.venv-build\Scripts\python.exe -m pip install -r packaging\requirements-build.txt
packaging\.venv-build\Scripts\pyinstaller.exe --noconfirm --clean packaging\Paperdown.spec

New-Item -ItemType Directory -Force -Path outputs | Out-Null
& "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe" packaging\paperdown.iss

Write-Host "Created outputs\Paperdown-Windows-Setup.exe"
