# -*- mode: python ; coding: utf-8 -*-
"""
ODF PyInstaller spec — the single source of build settings.
Used by both build_exe.py and .github/workflows/build-windows.yml.

Run from the project root:
    pyinstaller --noconfirm --clean packaging/odf.spec
Output: dist/ODF/  (folder distribution, no console window)
"""

import os
from PyInstaller.utils.hooks import collect_all

ROOT = os.path.abspath(os.path.join(SPECPATH, '..'))

# Packages that load data files / submodules dynamically
COLLECT_ALL = [
    'chromadb',
    'fastembed',
    'onnxruntime',
    'tokenizers',
    'huggingface_hub',
    'customtkinter',
    'pdfminer',
]

# Hidden imports that PyInstaller may miss
HIDDEN_IMPORTS = [
    'fastembed',
    'fastembed.common',
    'fastembed.text',
    'fastembed.text.text_embedding',
    'pdfminer.high_level',
    'pdfminer.layout',
    'docx',
    'keyboard',
    'chromadb.migrations',
    'sqlite3',
]

# Heavy packages that are not used
EXCLUDES = [
    'matplotlib',
    'scipy',
    'PyQt5',
    'PyQt6',
    'wx',
    'IPython',
    'notebook',
    'pytest',
    'unittest',
]

datas, binaries, hiddenimports = [], [], list(HIDDEN_IMPORTS)
for pkg in COLLECT_ALL:
    pkg_datas, pkg_binaries, pkg_hidden = collect_all(pkg)
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hidden

icon = os.path.join(ROOT, 'ODF_Logo.ico')
if not os.path.exists(icon):
    icon = None

a = Analysis(
    [os.path.join(ROOT, 'src', 'odf', '__main__.py')],
    pathex=[os.path.join(ROOT, 'src')],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=EXCLUDES,
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ODF',
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
    icon=icon,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ODF',
)
