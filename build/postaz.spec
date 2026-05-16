# PyInstaller spec for Postaz — bundles main.py + the `app/` package
# into a single Windows folder under `build/dist/Postaz`.
#
# Run from the project root:
#     pyinstaller build/postaz.spec --noconfirm
#
# Then point the Inno Setup script at `build/dist/Postaz` to wrap the
# folder in a Next/Next/Finish installer.

from pathlib import Path
import sys

block_cipher = None
HERE = Path(SPECPATH).resolve()
ROOT = HERE.parent
ENTRY = ROOT / "main.py"
ICON  = HERE / "postaz.ico"

a = Analysis(
    [str(ENTRY)],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        # Anything the runtime reads from disk would go here. Postaz keeps
        # everything in Python modules, so this is intentionally empty.
    ],
    hiddenimports=[
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtWidgets",
        "PySide6.QtSvg",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Trim down the bundle — these PySide6 modules are huge and unused.
        "PySide6.QtWebEngineCore",
        "PySide6.QtWebEngineWidgets",
        "PySide6.QtNetwork",
        "PySide6.QtQml",
        "PySide6.QtQuick",
        "PySide6.QtSql",
        "PySide6.QtTest",
        "PySide6.QtMultimedia",
        "PySide6.Qt3DCore",
        "PySide6.Qt3DRender",
        "tkinter",
        "unittest",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Postaz",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,                  # GUI app — no terminal pop-up
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ICON),
    version=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,                       # UPX slows first-launch on some AV products
    upx_exclude=[],
    name="Postaz",
)
