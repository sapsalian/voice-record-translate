# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

webview_datas, webview_binaries, webview_hiddenimports = collect_all('webview')
av_datas, av_binaries, av_hiddenimports = collect_all('av')

a = Analysis(
    ['run.py'],
    pathex=['../src'],
    datas=[
        ('../src/vrt/static', 'vrt/static'),
        *webview_datas,
        *av_datas,
    ],
    binaries=[*webview_binaries, *av_binaries],
    hiddenimports=[
        *webview_hiddenimports,
        *av_hiddenimports,
        'flask_cors',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='VRT',
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
    name='VRT',
)

app = BUNDLE(
    coll,
    name='VRT.app',
    icon=None,
    bundle_identifier='com.vrt.app',
    info_plist={
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '10.15.0',
    },
)
