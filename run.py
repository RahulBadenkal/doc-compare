"""
Entry Point to The App
"""

from datetime import datetime
import logging
import os
import sys
from tkinter import Tk, messagebox

import eel

from core.utils.sysutils import ensure_dir, empty_dir
from core.utils.strutils.strutils import is_valid_jsonstr
from core.datastore.datastore import ShelveStrgFile
from core.utils.dbgutils import time_tracker

import settings
from app import eel_funcs  # To expose python functions to eel


def show_error(title, msg):
    root = Tk()
    root.withdraw()  # hide main window
    messagebox.showerror(title, msg)
    root.destroy()


@time_tracker
def get_config_from_disk(config_filepath):
    if not os.path.isfile(config_filepath):
        raise ValueError("No config file found at {}".format(config_filepath))

    with open(config_filepath, 'r', encoding='utf-8') as f:
        filecontents = f.read()

    config = dict()
    result = is_valid_jsonstr(filecontents)
    if result['result'] is False:
        raise ValueError("Config file is not in proper json format. " + result['err_msg'])
    config = result['data']['json']

    return config


@time_tracker
def setup_dirs():
    # Set up working directories
    try:
        for each in [settings.CACHEDIR, settings.LOGDIR,
                     settings.SESSIONDIR,
                     settings.USERSETTINGSDIR, settings.APPDATADIR, settings.OUTPUTDIR, settings.TEMPDIR]:
            ensure_dir(each)
        for each in [settings.CACHEDIR, settings.SESSIONDIR]:
            empty_dir(each)

        # Set Log Config
        settings.set_log_config()
        logging.info("\n\n{}".format("*" * 50))
        logging.info("Program Started @ {}".format(datetime.today()))
        logging.info('Successfully set up working directories')
    except Exception as e:
        errmsg = 'Some problem occurred while setting up working directories'
        logging.exception('{}\n{}'.format(errmsg, e.args))
        show_error(title='App Initial Setup Failed', msg=errmsg)
        logging.info('Closing App')
        sys.exit()


@time_tracker
def set_session():
    # Create an save various parameters in session object
    try:
        # Create a user settings storage handler
        g_userSettings = ShelveStrgFile(settings.USERSETTINGSPATH)

        # Create a App data storage handler
        g_appdata = ShelveStrgFile(settings.APPDATAFILEPATH)

        # Store config and storage handlers in session
        session = dict()
        session['g_userSettings'] = g_userSettings
        session['g_appdata'] = g_appdata
        settings.g_session.set_data(session)
        logging.info('Successfully set up session')
    except Exception as e:
        err_msg = 'Some problem occurred while setting up Session'
        logging.error('{}\n{}'.format(err_msg, e.args))
        show_error(title='Failed to initialise session', msg=err_msg)
        logging.info('Closing App')
        sys.exit()


def start_app():
    # Start the server
    try:
        web_dir = settings.WEBDIR
        start_html_page = settings.STARTPAGENAME
        eel.init(web_dir)
        logging.info("App Started")
        options = {'host': 'localhost', 'port': 0}
        eel.start(start_html_page, options=options, suppress_error=True)
    except Exception as e:
        err_msg = 'Could not launch a local server'
        logging.error('{}\n{}'.format(err_msg, e.args))
        show_error(title='Failed to initialise server', msg=err_msg)
        logging.info('Closing App')
        sys.exit()


if __name__ == "__main__":
    setup_dirs()
    # config = get_app_config()
    set_session()
    start_app()

