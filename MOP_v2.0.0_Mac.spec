# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['auto_exe_with_rnat_v2.1.py'],  # The main Python script
    pathex=['/path/to/your/python/environment'],  # Ensure this is the correct Python environment path
    binaries=[],
    datas=[('images', 'images')],  # Include the images folder if needed
    hiddenimports=['docx'],  # Ensure 'docx' is included in hiddenimports
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Ensure any additional data files are added here
a.datas += [('is_rnat_icon.png', 'images/is_rnat_icon.png', "DATA")]

# Create the application bundle
coll = COLLECT(
    a.binaries,
    a.scripts,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Magic_Doc_Generator',  # Application name
    icon='images/is_rnat_icon.icns',  # Path to the application icon
)
