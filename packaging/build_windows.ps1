$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

Set-Location frontend
corepack pnpm install --frozen-lockfile
if ($LASTEXITCODE -ne 0) { throw "Build command failed with exit code $LASTEXITCODE" }
$env:NEXT_TELEMETRY_DISABLED = "1"
corepack pnpm exec next build
if ($LASTEXITCODE -ne 0) { throw "Build command failed with exit code $LASTEXITCODE" }
Set-Location $ProjectRoot

python -m venv packaging\.venv-build
if ($LASTEXITCODE -ne 0) { throw "Build command failed with exit code $LASTEXITCODE" }
packaging\.venv-build\Scripts\python.exe -m pip install -r backend\requirements.txt
if ($LASTEXITCODE -ne 0) { throw "Build command failed with exit code $LASTEXITCODE" }
packaging\.venv-build\Scripts\python.exe -m pip install -r packaging\requirements-build.txt
if ($LASTEXITCODE -ne 0) { throw "Build command failed with exit code $LASTEXITCODE" }
packaging\.venv-build\Scripts\pyinstaller.exe --noconfirm --clean packaging\Paperdown.spec
if ($LASTEXITCODE -ne 0) { throw "Build command failed with exit code $LASTEXITCODE" }

New-Item -ItemType Directory -Force -Path outputs | Out-Null
& "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe" packaging\paperdown.iss
if ($LASTEXITCODE -ne 0) { throw "Build command failed with exit code $LASTEXITCODE" }

Write-Host "Created outputs\Paperdown-Windows-Setup.exe"
