"""PyInstaller spec for CAN_ID_Reframe.

Generates a Windows standalone executable: can-id-reframe-{version}.exe
"""

# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

# Add the core directory to sys.path to import version
# Use current working directory since __file__ is not available in PyInstaller context
project_root = Path.cwd()
sys.path.insert(0, str(project_root / 'core'))

from version import __version__

a = Analysis(
    ['can_id_reframe_cli.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('core/version_info.txt', 'core'),
        ('core/gui.ui', 'core'),
        ('core/settings_dialog.ui', 'core'),
        ('resources/images/app_icon.ico', 'resources/images'),
        ('resources/images/can_relay_icon.svg', 'resources/images'),
    ],
    hiddenimports=['uptime'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=f'can-id-reframe-{__version__}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/images/app_icon.ico',
)

# Additional console-enabled executable for CI smoke tests
exe_cli = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=f'can-id-reframe-cli-{__version__}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/images/app_icon.ico',
)
