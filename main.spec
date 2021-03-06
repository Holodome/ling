# -*- mode: python ; coding: utf-8 -*-


block_cipher = None
import pymorphy2_dicts_ru
pymorph_data = pymorphy2_dicts_ru.get_path()


a = Analysis(['main.py'],
             pathex=[],
             binaries=[],
            datas=[(pymorph_data, 'pymorphy2_dicts_ru/data'), ("sql/tables.sql", ".")],
             hiddenimports=[],
             hookspath=[],
             hooksconfig={},
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
          name='анализ',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None )
