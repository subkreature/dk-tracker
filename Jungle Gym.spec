# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['dashboard.py'],
    pathex=[],
    binaries=[],
    datas=[
        (
            'plugins/dktracker/init.lua',
            'plugins/dktracker',
        ),
    ],
    hiddenimports=[],
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
    [],
    exclude_binaries=True,
    name='Jungle Gym',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Jungle Gym',
)
app = BUNDLE(
    coll,
    name='Jungle Gym.app',
    icon=None,
    bundle_identifier=None,
)
