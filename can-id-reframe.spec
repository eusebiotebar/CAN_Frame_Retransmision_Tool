"""PyInstaller spec for CAN_ID_Reframe.

Generates a Windows standalone executable: can-id-reframe.exe
"""

# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['can_id_reframe_cli.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('core/version_info.txt', 'core'),
        ('core/gui.ui', 'core'),
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
    name='can-id-reframe',
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
