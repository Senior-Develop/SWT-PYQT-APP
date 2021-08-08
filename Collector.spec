# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['Main.py'],
             pathex=['C:\\workspace\\Upwork\\SwT'],
             binaries=[],
             datas=[],
             hiddenimports=['pkg_resources.py2_warn', 'talib.stream'],
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
          name='SwT-Collector',
          debug=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          icon='C:\\workspace\\Upwork\\SwT\\UI\\Icon\\eth.ico',
          console=True )
