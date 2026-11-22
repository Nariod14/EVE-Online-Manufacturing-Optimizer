# manuoptimizer.spec

# -*- mode: python ; coding: utf-8 -*-

import os
import pulp

block_cipher = None

# PuLP's CBC solver is a data file inside the package; no PyInstaller hook collects it,
# so without this the exe fails with "Pulp: cannot execute ...cbc.exe".
# Taken from the PuLP installed in the environment that runs PyInstaller (use the .venv).
PULP_CBC_DIR = os.path.join(os.path.dirname(pulp.__file__), 'solverdir', 'cbc', 'win', 'i64')

a = Analysis(
    ['run.py'],  # This is your entry point, so keep this as-is
    pathex=[],
    binaries=[],
    datas=[
        ('out', 'out'),
        ('sde/mini_sde.sqlite', 'sde'),  # Add the mini SDE here
        ('.env', '.'),
        (os.path.join(PULP_CBC_DIR, 'cbc.exe'), 'pulp/solverdir/cbc/win/i64'),
        (os.path.join(PULP_CBC_DIR, 'coin-license.txt'), 'pulp/solverdir/cbc/win/i64'),
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
    a.binaries,
    a.datas,
    [],
    name='run',  # This controls the output executable name (run.exe)
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
)
