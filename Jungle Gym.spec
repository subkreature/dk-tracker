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
        (
            'assets/Credits.html',
            '.',
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
import os

icon_path = os.path.abspath(
    os.path.join(
        SPECPATH,
        'assets',
        'JungleGym.icns',
    )
)

assert os.path.isfile(icon_path), (
    f'App icon not found: {icon_path}'
)

print(f'Using app icon: {icon_path}')

app = BUNDLE(
    coll,
    name='Jungle Gym.app',
    icon=icon_path,
    bundle_identifier='com.subkreature.junglegym',
    info_plist={
        'CFBundleShortVersionString': '0.1.0',
        'CFBundleVersion': '1',
        'NSHumanReadableCopyright': (
            'Copyright © 2026 Subkreature (SK.)'
        ),
    },
)
