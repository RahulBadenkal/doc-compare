import os
import logging
import subprocess
import platform
from typing import List

from core.utils.sysutils import get_filename_and_type, subprocess_args, ensure_dir


supported_filetypes = [".doc", ".docx", ".ppt", ".pptx"]

# TODO: Rewrite it so that the caller has to specifically say by whoch method he wants to convert.
# TODO: When converting 5 files, if first 3 files are converted using msoffice and due to some problem file 4 was not
#  converted, then the control will go to libreoffice and it will delete the 3 converted files and redo converting all
#  5 files from beginning. Fix this behaviour
def doc_to_pdf(infilepaths: List[str], outfilepaths: List[str]) -> dict:
    """Converts the given set of files to pdf format

    Args:
        infilepaths: List of filepaths that are to converted to pdf
        outfilepaths: List of filepaths where the generated pdf files will be stored

    Returns:

    """
    retval = {'result': True, 'errmsg': '', 'errno': 0,
              'data': {'infilepaths_converted': list(), 'outfilepaths_converted': list()}}

    def _set_retval(result, err_msg, err_code, infilepaths_converted, outfilepaths_converted):
        retval['result'] = result
        retval['errmsg'] = err_msg
        retval['errno'] = err_code
        retval['data']['infilepaths_converted'] = infilepaths_converted
        retval['data']['outfilepaths_converted'] = outfilepaths_converted

    for infilepath, outfilepath in zip(infilepaths, outfilepaths):
        filename, file_extension = get_filename_and_type(infilepath)

        # If the file is already a pdf
        if file_extension == ".pdf":
            msg = "The file: {} is already a PDF".format(infilepath)
            _set_retval(False, msg, 1, list(), list())
            return retval

        # If path of the to be converted pdf already exists
        if os.path.isfile(outfilepath):
            msg = "There is already a file with the name: {}".format(outfilepath)
            _set_retval(False, msg, 2, list(), list())
            return retval

        # If the conversion of file to pdf is not supported
        if file_extension not in supported_filetypes:
            msg = "Conversion to pdf of the file type {} is not yet supported".format(file_extension)
            _set_retval(False, msg, 3, list(), list())
            return retval

    # No two outfilepath must be same
    if len(set(outfilepaths)) != len(outfilepaths):  # duplicates exist
        def _list_duplicates(seq):
            seen = set()
            seen_add = seen.add
            # adds all elements it doesn't know yet to seen and all other to seen_twice
            seen_twice = set(x for x in seq if x in seen or seen_add(x))
            return list(seen_twice)

        dups = _list_duplicates(outfilepaths)
        msg = "Two or more output files have the same path: {}".format(dups)
        _set_retval(False, msg, 4, list(), list())
        return retval

    success_msg = "All files at {} successfully converted to pdf at {}".format(infilepaths, outfilepaths)

    result = msoffice_doc_to_pdf(infilepaths, outfilepaths)
    if result['result']:
        msg = success_msg + " using MS Word"
        _set_retval(True, msg, 0, infilepaths, outfilepaths)
        return retval
    else:
        logging.error(result['errmsg'])

    result = libreoffice_doc_to_pdf(infilepaths, outfilepaths)
    if result['result']:
        msg = success_msg + " using LibreOffice"
        _set_retval(True, msg, 0, infilepaths, outfilepaths)
        return retval
    else:
        logging.error(result['errmsg'])

    result = py_doc_to_pdf(infilepaths, outfilepaths)
    if result['result']:
        msg = success_msg + " using system independent python libraries"
        _set_retval(True, msg, 0, infilepaths, outfilepaths)
        return retval
    else:
        logging.error(result['errmsg'])

    err_msg = "Could not convert file at {} to pdf at {} using any of the existing methods".format(infilepaths,
                                                                                                   outfilepaths)
    _set_retval(False, err_msg, 10, None)
    return retval


def msoffice_doc_to_pdf(infilepaths: List[str], outfilepaths: List[str]) -> dict:
    """Converting word files to pdf using MS Word

    Args:
        infilepaths: List of filepaths that are to converted to pdf
        outfilepaths: List of filepaths where the generated pdf files will be stored

    Returns:

    """
    retval = {'result': True, 'errmsg': '', 'errno': 0,
              'data': {'infilepaths_converted': list(), 'outfilepaths_converted': list()}}
    word = None
    infilepaths_converted = list()
    outfilepaths_converted = list()
    try:
        import win32com.client
        word = win32com.client.DispatchEx("Word.Application")  # Using DispatchEx for an entirely new Word instance
        # word.Visible = True
        wdFormatPDF = 17
        for infilepath, outfilepath in zip(infilepaths, outfilepaths):
            # # Delete the file if it already exists.
            # if os.path.isfile(outfilepath):
            #     os.remove(outfilepath)
            doc = word.Documents.Open(infilepath)
            doc.SaveAs(outfilepath, FileFormat=wdFormatPDF)
            doc.Close()
            infilepaths_converted.append(infilepath)
            outfilepaths_converted.append(outfilepath)
    except Exception as e:
        fail_msg = "Couldn't convert doc(x) to pdf using MS Word due to: {}".format(e.args)
        retval['result'] = False
        retval['errmsg'] = fail_msg
        retval['errno'] = 1
    finally:
        if word is not None:
            word.Quit()
        retval['data']['infilepaths_converted'] = infilepaths_converted
        retval['data']['outfilepaths_converted'] = outfilepaths_converted
        return retval


# TODO: BUG, Libreoffice conversion keeps the filename same as the input filename and not the outfilename provided.
def libreoffice_doc_to_pdf(infilepaths: List[str], outfilepaths: List[str]) -> dict:
    """Converting word files to pdf using Libreoffice

       Args:
           infilepaths: List of filepaths that are to converted to pdf
           outfilepaths: List of filepaths where the generated pdf files will be stored

       Returns:

       """
    retval = {'result': True, 'errmsg': '', 'errno': 0,
              'data': {'infilepaths_converted': list(), 'outfilepaths_converted': list()}}
    infilepaths_converted = list()
    outfilepaths_converted = list()

    libreoffice_path = ""
    if platform.system() == "Windows":
        libreoffice_path = "C:\\Program Files\\LibreOffice\\program\\soffice.exe"
    elif platform.system() == "Linux":
        libreoffice_path = "libreoffice"
    elif platform.system() == "Darwin":
        libreoffice_path = "/Applications/LibreOffice.app/Contents/MacOS/soffice"


    try:
        for infilepath, outfilepath in zip(infilepaths, outfilepaths):
            # # Delete the file if it already exists
            # if os.path.isfile(outfilepath):
            #     os.remove(outfilepath)
            output_dir = os.path.dirname(outfilepath)
            process = subprocess.call([libreoffice_path, '--headless', '--convert-to', 'pdf', '--outdir',
                                       output_dir, infilepath], **subprocess_args())
            infilepaths_converted.append(infilepath)
            outfilepaths_converted.append(outfilepath)
    except Exception as e:
        fail_msg = "Couldn't convert doc(x) to pdf using Libreoffice due to: {}".format(e.args)
        retval['result'] = False
        retval['errmsg'] = fail_msg
        retval['errno'] = 1
    finally:
        retval['data']['infilepaths_converted'] = infilepaths_converted
        retval['data']['outfilepaths_converted'] = outfilepaths_converted
        return retval


# TODO: Implement doc to pdf conversion using pure python libraries
def py_doc_to_pdf(infilepaths: List[str], outfilepaths: List[str]) -> dict:
    """Converting word files to pdf using pure python libraries

       Args:
           infilepaths: List of filepaths that are to converted to pdf
           outfilepaths: List of filepaths where the generated pdf files will be stored

       Returns:

       """
    retval = {'result': True, 'errmsg': '', 'errno': 0,
              'data': {'infilepaths_converted': list(), 'outfilepaths_converted': list()}}
    infilepaths_converted = list()
    outfilepaths_converted = list()

    try:
        for infilepath, outfilepath in zip(infilepaths, outfilepaths):
            # # Delete the file if it already exists
            # if os.path.isfile(outfilepath):
            #     os.remove(outfilepath)
            raise NameError("Doc to pdf conversion using system independent python libraries not yet implemented")
    except Exception as e:
        fail_msg = "Couldn't convert doc(x) to pdf using python libraries due to: {}".format(e.args)
        retval['result'] = False
        retval['errmsg'] = fail_msg
        retval['errno'] = 1
    finally:
        retval['data']['infilepaths_converted'] = infilepaths_converted
        retval['data']['outfilepaths_converted'] = outfilepaths_converted
        return retval
