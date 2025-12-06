# -*- mode: python ; coding: utf-8 -*-

# Ursina + Panda3D için gerekli tüm dosyaları otomatik ekliyoruz
from PyInstaller.utils.hooks import collect_data_files
from PyInstaller.utils.hooks import collect_all

# panda3d ve ursina'nın tüm veri dosyalarını (shader, model, ses vs.) al
datas_panda3d, binaries_panda3d, hiddenimports_panda3d = collect_all('panda3d')
datas_ursina, binaries_ursina, hiddenimports_ursina = collect_all('ursina')

block_cipher = None

a = Analysis(
    ['ursina_main.py'],
    pathex=['.'],  # mevcut klasör
    binaries=binaries_panda3d + binaries_ursina,
    datas=collect_data_files('panda3d') + collect_data_files('ursina') + 
          collect_data_files('ursina.shaders') + 
          [('oyun.ico', '.')],  # icon’u da ekle
    hiddenimports=hiddenimports_panda3d + hiddenimports_ursina + 
                  ['panda3d.core', 'panda3d.direct', 'direct.showbase.ShowBase'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='The Game',           # exe adı artık "The Game.exe"
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='oyun.ico',           # icon doğru şekilde
	#version='version.txt'      # istersen version bilgisi ekleyebilirsin
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='The Game'            # klasör adı da "The Game" olacak
)