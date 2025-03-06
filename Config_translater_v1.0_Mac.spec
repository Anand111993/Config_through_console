# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(
    ['configTranslaatter_using_regex.py'],
    pathex=[],
    binaries=[],
    datas=[('images','images')],
    hiddenimports=['docx'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
a.datas += [('images/is_rnat_icon.png','images/is_rnat_icon.png', "DATA")] 


pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ConfigTranslater',
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
    icon='images/is_rnat_icon.icns',
)
app = BUNDLE(
    exe,
    name='ConfigTranslater.app',
    icon='images/is_rnat_icon.icns',
    bundle_identifier=None,
)
