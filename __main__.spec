# -*- mode: python ; coding: utf-8 -*-
import sklearn
import xgboost
import numpy
import scipy


from PyInstaller.utils.hooks import collect_all

block_cipher = None

datas, binaries, hiddenimports = collect_all("xgboost")
datas, binaries, hiddenimports = collect_all("scipy")
datas, binaries, hiddenimports = collect_all("numpy")

a = Analysis(['__main__.py'],
             pathex=['C:\\Users\\mhamilton\\Documents\\Projects\\forecast\\production'],
             binaries=[('C:\\Users\\mhamilton\\AppData\\Local\\Programs\\Python\\Python38\\Lib\\site-packages\\sklearn\\.libs\\vcomp140.dll','.'),
                        ('C:\\Users\\mhamilton\\AppData\\Local\\Programs\\Python\\Python38\\xgboost\\xgboost.dll','.')],
             datas=[('C:\\Users\\mhamilton\\AppData\\Local\\Programs\\Python\\Python38\\xgboost\\xgboost.dll','.')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='forecaster',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True )
