#!/bin/bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

cd frontend
corepack pnpm install --frozen-lockfile
NEXT_TELEMETRY_DISABLED=1 corepack pnpm exec next build
cd "$PROJECT_ROOT"

python3 -m venv packaging/.venv-build
packaging/.venv-build/bin/python -m pip install -r backend/requirements.txt
packaging/.venv-build/bin/python -m pip install -r packaging/requirements-build.txt
packaging/.venv-build/bin/pyinstaller --noconfirm --clean packaging/Paperdown.spec

mkdir -p outputs
hdiutil create \
  -volname "Paperdown" \
  -srcfolder "dist/Paperdown.app" \
  -ov \
  -format UDZO \
  "outputs/Paperdown-macOS.dmg"

echo "Created outputs/Paperdown-macOS.dmg"
