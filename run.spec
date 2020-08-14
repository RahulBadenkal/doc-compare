# -*- mode: python ; coding: utf-8 -*-
# Config file for creating an executable

""" Command to run this file """
# >> pyinstaller --clean -D run.spec


""" Fill The Properties """
block_cipher = None
main_file_name = "run.py"
venv_name = "venv"
python_ver = "python3.6"  # For linux venv path config
icon_file_name = "favicon.ico"


""" Adding settings.py file to system path """
import os
spec_root = os.path.abspath(SPECPATH)  # Make sure this .spec file is in the main project directory
import sys
sys.path.append(spec_root)
print(len(sys.path))
print(sys.path)
print("--------------------------------------------------")
import settings


""" Getting path of eel js file """
if settings.isWindows:
    eel_file_path = os.path.abspath(os.path.join(settings.BASEDIR, venv_name, "lib", "site-packages", "eel", "eel.js"))
elif settings.isLinux or settings.isMac:
    eel_file_path = os.path.abspath(os.path.join(settings.BASEDIR, venv_name, "lib", python_ver, "site-packages", "eel", "eel.js"))


""" Setting the version info """
# To get a version file template, run the following command on any known executable and modify ita
# >> pyi-grab_version executable_with_version_resource
# Ex: >> pyi-grab_version Notepad.exe
def set_windows_version_file(filepath):
    txt = """
# UTF-8
#
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx
VSVersionInfo(
  ffi=FixedFileInfo(
    # filevers and prodvers should be always a tuple with four items: (1, 2, 3, 4)
    # Set not needed items to zero 0.
    filevers={filevers},  # (7, 6, 0, 0),
    prodvers={prodvers},  # (7, 6, 0, 0),
    # Contains a bitmask that specifies the valid bits 'flags'r
    mask=0x3f,
    # Contains a bitmask that specifies the Boolean attributes of the file.
    flags=0x0,
    # The operating system for which this file was designed.
    # 0x4 - NT and there is no need to change it.
    OS=0x40004,
    # The general type of file.
    # 0x1 - the file is an application.
    fileType=0x1,
    # The function of the file.
    # 0x0 - the function is not defined for this fileType
    subtype=0x0,
    # Creation date and time stamp.
    date=(0, 0)
    ),
  kids=[
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])]),
    StringFileInfo(
      [
      StringTable(
        u'040904b0',
        [StringStruct(u'CompanyName', '{CompanyName}'),  # u'Don HO don.h@free.fr'),
        StringStruct(u'FileDescription', '{FileDescription}'),  # u'Notepad++ : a free (GNU) source code editor'),
        StringStruct(u'FileVersion', '{FileVersion}'),  # u'7.6'),
        StringStruct(u'InternalName', '{InternalName}.exe'),  # u'npp.exe'),
        StringStruct(u'LegalCopyright', '{LegalCopyright}'),  # u'Copyleft 1998-2016 by Don HO'),
        StringStruct(u'OriginalFilename', '{OriginalFilename}.exe'),  # u'Notepad++.exe'),
        StringStruct(u'ProductName', '{ProductName}'),  # u'Notepad++'),
        StringStruct(u'ProductVersion', '{ProductVersion}')])  # u'7.6')])
      ])
  ]
)
"""
    params = {'filevers': settings.APPVER, 'prodvers': settings.APPVER, 'CompanyName': settings.AUTHOR, 'FileDescription':
    settings.APPDESCRIPTION, 'FileVersion' : settings.APPVERSTR, 'InternalName': settings.APPMARK, 'LegalCopyright': settings.COPYRIGHT,
    'OriginalFilename': settings.APPNAME, 'ProductName': settings.APPNAME, 'ProductVersion': settings.APPVERSTR
    }
    txt = txt.format(**params)
    with open(filepath, 'w') as f:
        f.write(txt)
if settings.isWindows:
    version_file = 'windows_file_version_info.rc'
    set_windows_version_file(version_file)
else:
    version_file = None


""" Setting Pyinstaller configurations """
a = Analysis([os.path.abspath(os.path.join(settings.BASEDIR, main_file_name))],
             pathex=[settings.BASEDIR], #[spec_root],
             binaries=[],
             datas=[(eel_file_path, 'eel'),
                    (settings.WEBDIR, 'web'),
                    (settings.BINDIR, 'bin'),
                    (settings.DOCSDIR, 'docs')],
             hiddenimports=['bottle_websocket'],
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
          [],
          exclude_binaries=True,
          name=settings.APPNAME,
          debug=False,
          bootloader_ignore_signals=False,
          version=version_file,
          strip=False,
          upx=True,
          console=False,
          icon=os.path.abspath(os.path.join(settings.WEBDIR, 'icons8-document-64.ico')))
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[], #['vcruntime140.dlll'],
               name=settings.APPNAME)


""" Deleting intermediate generated version file """
if version_file is not None:
    os.remove(version_file)


""" TODO: Here write code to pop the above appended path """
print("---------------------------------------------")
print(len(sys.path))
print(sys.path)





