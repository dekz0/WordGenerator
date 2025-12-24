# -*- mode: python ; coding: utf-8 -*-
"""
Конфигурация PyInstaller для сборки exe файла.
"""

block_cipher = None

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('templates', 'templates'),  # Включаем папку с шаблонами
    ],
    hiddenimports=[
        'customtkinter',
        'docxtpl',
        'pandas',
        'openpyxl',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy.testing',
        'scipy',
        'PIL',
        'cv2',
        'tensorflow',
        'torch',
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='WordGenerator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Сжатие для уменьшения размера
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Без консоли
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Можно добавить иконку: 'icon.ico'
)
