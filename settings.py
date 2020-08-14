"""
All app related configurations are set here.
"""

import os
import platform
import logging
from appdirs import AppDirs

from core.datastore.datastore import ShelveStrgFile

# Providing support for the following platforms only
isWindows = platform.system() == "Windows"
isLinux = platform.system() == "Linux"
isMac = platform.system() == "Darwin"

"""APP DETAILS"""
APPNAME = "Doc Compare"
APPMARK = "doccompare"
APPVER = (1, 0, 0, 0)
APPVERSTR = '.'.join(str(x) for x in APPVER)
APPNAMEWITHVER = APPNAME + '-' + APPVERSTR
AUTHOR = "Sarci"
APPDESCRIPTION = ""
COPYRIGHT = ""


"""Deployment settings"""
ISDEBUG = True

"""Web files and external binaries paths"""
BASEDIR = os.path.abspath(os.path.dirname(__file__))

WEBDIR = os.path.abspath(os.path.join(BASEDIR, 'web'))
STARTPAGENAME = os.path.join('doctool', 'index.html')

BINDIR = os.path.abspath(os.path.join(BASEDIR, 'bin'))
BINPATHS = {
    'pdftotext': os.path.abspath(os.path.join(BINDIR, 'Windows', 'poppler', 'pdftotext.exe'))
    if isWindows else "pdftotext"
    # TODO: Add binaries for linux and macos and include the path here
}

# All user docs and config files are stored here
DOCSDIR = os.path.abspath(os.path.join(BASEDIR, 'docs'))

# App specific config file: JSON. (Read only) Packaged with the exe
CONFIGDIR = os.path.abspath(os.path.join(DOCSDIR, 'configs'))
CONFIGFILEPATH = os.path.abspath(os.path.join(CONFIGDIR, 'config.json'))


"""App generated data folders/file paths"""
dirs = AppDirs(appname=APPNAME, appauthor=AUTHOR)
if ISDEBUG:
    dev_data_dir = os.path.abspath(os.path.join(BASEDIR, 'appdata'))
    DATADIR = dev_data_dir
    CACHEDIR = os.path.abspath(os.path.join(dev_data_dir, 'Cache'))
    LOGDIR = os.path.abspath(os.path.join(dev_data_dir, 'Logs'))
else:
    DATADIR = dirs.user_data_dir
    CACHEDIR = dirs.user_cache_dir  # This will be deleted upon uninstall
    LOGDIR = dirs.user_log_dir  # This will be deleted upon uninstall

OUTPUTDIR = os.path.abspath(os.path.join(DATADIR, 'Output'))

TEMPDIR = os.path.abspath(os.path.join(DATADIR, 'Temp'))

# Logs: txt. (Write Only) (Stored permanently on disk)
LOGFILEPATH = os.path.abspath(os.path.join(LOGDIR, APPNAME + '.log'))

# Session object to hold session specific data: Shelve. (Read and write) (Stored Temporarily on disk)
SESSIONDIR = os.path.abspath(os.path.join(DATADIR, 'Session'))
SESSIONFILEPATH = os.path.abspath(os.path.join(SESSIONDIR, 'session'))
g_session = ShelveStrgFile(SESSIONFILEPATH)


"""Storage Objects (Read and write) (Stored permanently on disk)"""
# User specific settings: Shelve.
USERSETTINGSDIR = os.path.abspath(os.path.join(DATADIR, 'User_Settings'))
USERSETTINGSPATH = os.path.abspath(os.path.join(USERSETTINGSDIR, 'user_settings'))

# App data: Shelve.
APPDATADIR = os.path.abspath(os.path.join(DATADIR, 'Database'))
APPDATAFILEPATH = os.path.abspath(os.path.join(APPDATADIR, 'db'))


def set_log_config():
    """Sets the logging configuration

    """
    if ISDEBUG:
        logging.basicConfig(level=logging.INFO)  # For developing
    else:
        logging.basicConfig(filename=LOGFILEPATH, filemode='w+', level=logging.INFO)  # For production
