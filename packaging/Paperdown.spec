# -*- mode: python ; coding: utf-8 -*-

import platform
from pathlib import Path

from PyInstaller.utils.hooks import collect_all, collect_submodules


project_root = Path(SPECPATH).parent
frontend_out = project_root / "frontend" / "out"

datas = [(str(frontend_out), "frontend-out")]
binaries = []
hiddenimports = collect_submodules("webview")

for package in ("fitz", "pymupdf", "webview"):
    package_datas, package_binaries, package_hiddenimports = collect_all(package)
    datas += package_datas
    binaries += package_binaries
    hiddenimports += package_hiddenimports

a = Analysis(
    [str(project_root / "backend" / "desktop.py")],
    pathex=[str(project_root / "backend")],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter", "PyQt5", "PyQt6", "PySide2", "PySide6"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="Paperdown",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=platform.system() == "Darwin",
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

if platform.system() == "Darwin":
    app = BUNDLE(
        exe,
        name="Paperdown.app",
        bundle_identifier="com.paperdown.desktop",
        info_plist={
            "CFBundleDisplayName": "Paperdown",
            "CFBundleShortVersionString": "1.0.0",
            "NSHighResolutionCapable": True,
        },
    )
