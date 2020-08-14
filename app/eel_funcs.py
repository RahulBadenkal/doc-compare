"""
All Python functions called by js defined here
"""

import os
from tkinter import Tk
from tkinter.filedialog import askopenfilename
import base64
import logging

import eel

from core.utils.sysutils import get_filename_and_type
from core.datastore.datastore import InvalidJSONError

from app.diff_doc import diff_pdfs
# from settings import g_userSettinget_diffgs


@eel.expose
def ask_file(docno, file_choices=None):
    """Ask the user to select a file

    """
    retval = {'result': True, 'errno': 0, 'errmsg': '', 'data': {'filepath': '', 'filename': ''}}

    try:
        try:
            user_settings = dict()  # g_userSettings.get_data()
        except Exception as e:
            logging.error("Could not read user settings due to : {}".format(e.args))
            user_settings = dict()

        default_dir = user_settings.get('infile1_dirpath', "") if docno == 0 else user_settings.get('infile2_dirpath',
                                                                                                    "")
        default_dir = os.path.abspath(default_dir) if os.path.isdir(default_dir) else ""

        root = Tk()
        root.withdraw()
        root.wm_attributes('-topmost', 1)
        # if (file_choices is None) or (platform.system() == "Darwin"):
        #     file_path = askopenfilename(parent=root, initialdir=default_dir)
        # else:
        file_types = [('All files', '*')]
        # TODO: Speed up the time it takes to for the askfile dialogue to open
        # TODO: When clicked multiple times multiple windows open.
        # TODO: Check cross compatibility of the askopenfile code with the 3 platforms
        if default_dir != "":
            x = askopenfilename(parent=root, initialdir=default_dir, filetypes=file_types)
        else:
            x = askopenfilename(parent=root, filetypes=file_types)
        if x == tuple():
            filepath, filename = '', ''
        else:
            filepath = os.path.abspath(x)
            filename = ''.join(get_filename_and_type(filepath))
        root.update()

        retval['data']['filepath'] = filepath
        retval['data']['filename'] = filename
    except Exception as e:
        logging.error('Something went wrong due to: {}'.format(e.args))
        retval['result'] = False
        retval['errno'] = 1
        retval['errmsg'] = retval['errmsg'] + 'An error occurred: .....{}.....'.format(str(e))

    finally:
        return retval


@eel.expose
def check_if_file_exists(file):
    """ Checks if a file exists

    """
    retval = {'result': True, 'errno': 0, 'errmsg': '', 'data': {'isfile': bool()}}

    try:
        retval['data']['isfile'] = os.path.isfile(file)
    except Exception as e:
        logging.error('Something went wrong due to: {}'.format(e.args))
        retval['result'] = False
        retval['errno'] = 1
        retval['errmsg'] = retval['errmsg'] + 'An error occurred: .....{}.....'.format(str(e))
    finally:
        return retval


@eel.expose
def pdf_to_base64(filepath):
    """Get the base64 representation of the file at given filepath

    """
    retval = {'result': True, 'errno': 0, 'errmsg': '', 'data': {'blob': ''}}
    try:
        with open(filepath, 'rb') as f:
            blob = base64.b64encode(f.read())
        blob = blob.decode("utf-8")
        retval['data']['blob'] = blob
    except Exception as e:
        logging.error('Something went wrong due to: {}'.format(e.args))
        retval['result'] = False
        retval['errno'] = 1
        retval['errmsg'] = retval['errmsg'] + 'An error occurred: .....{}.....'.format(str(e))
    return retval


@eel.expose
def get_settings():
    retval = {'result': True, 'errno': 0, 'errmsg': '',
              'data': {'userSettings': dict()}}
    try:
        retval['data']['userSettings'] = dict()  # g_userSettings.get_data()
    except Exception as e:
        err_msg = "Could not read user settings due to : {}".format(e.args)
        logging.error(err_msg)
        retval['result'] = False
        retval['errno'] = 1
        retval['errmsg'] = err_msg
    finally:
        return retval


@eel.expose
def set_settings(data):
    retval = {'result': True, 'errno': 0, 'errmsg': '',
              'data': {}}
    try:
        pass
        # g_userSettings.set_data(data)
    except Exception as e:
        err_msg = "Could not set user settings due to : {}".format(e.args)
        logging.error(err_msg)
        retval['result'] = False
        retval['errno'] = 1
        retval['errmsg'] = err_msg
    finally:
        return retval


@eel.expose
def update_settings(data):
    retval = {'result': True, 'errno': 0, 'errmsg': '',
              'data': {'userSettings': dict()}}
    try:
        retval['data']['userSettings'] = dict()  # g_userSettings.update_data(data)
    except InvalidJSONError as e:
        logging.error("User settings data is corrupted due to: {}".format(e.args))
        logging.warning("Deleting the corrupted user settings data")
        #  g_userSettings.set_data(data)
        retval['data']['userSettings'] = data
    except Exception as e:
        err_msg = "Could not update user settings due to : {}".format(e.args)
        logging.error(err_msg)
        retval['result'] = False
        retval['errno'] = 1
        retval['errmsg'] = err_msg
    finally:
        return retval


@eel.expose
def get_diff(filepath1, filepath2, js_progress_funcname=None, js_cancel_funcname=None):
    """Get File Differences

    """
    retval = {'result': True, 'errno': 0, 'errmsg': '',
              'data': {'outfilespath': list(), 'outfilesname': list(), 'diff_locs': list()}}

    try:
        # Store the input file folder locations for future use
        new_dirs = {'infile1_dirpath': os.path.dirname(filepath1),
                    'infile2_dirpath': os.path.dirname(filepath2)}
        try:
            pass
            # g_userSettings.update_data(new_dirs)
        except InvalidJSONError as e:
            logging.error("User settings data is corrupted due to: {}".format(e.args))
            logging.info("Deleting the corrupted user settings data")
            # g_userSettings.set_data(new_dirs)
        except Exception as e:
            logging.error('Something went wrong due to: {}'.format(e.args))

        # Get Diff
        diff_locs, outfilespath = diff_pdfs(filepath1, filepath2, js_progress_funcname)

        locs = [
            {"index": change['pdf']['index'],
             'normYPos': round((change['abs_y'] / change['pdf']['tot_pdf_height']) * 100, 5),
             'normHeight': round(((change['yMax'] - change['yMin']) / change['pdf']['tot_pdf_height']) * 100, 5),
             }
            if change != "*" else "*"
            for change in diff_locs
        ]
        outfilesname = [get_filename_and_type(each)[0] for each in outfilespath]

        retval['data']['outfilespath'] = outfilespath
        retval['data']['outfilesname'] = outfilesname
        retval['data']['diff_locs'] = locs
        print(retval)
    except Exception as e:
        logging.error('Something went wrong due to: {}'.format(e.args))
        retval['result'] = False
        retval['errno'] = 1
        retval['errmsg'] = 'An error occurred: .....{}.....'.format(str(e))
    finally:
        return retval
