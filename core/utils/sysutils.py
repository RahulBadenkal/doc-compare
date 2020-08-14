"""
System os level utility functions
"""

import os
import shutil
import subprocess
import logging


def ensure_dir(dir_path: str) -> None:
    """Create the given directory structure if it doesn't exists.
    If it exists do nothing.

    Args:
        dir_path: path to directory
    """
    os.makedirs(dir_path, exist_ok=True)


def empty_dir(dir_path: str) -> None:
    """Clear all the contents of the directory

    Args:
        dir_path: path to directory
    """
    for the_file in os.listdir(dir_path):
        file_path = os.path.join(dir_path, the_file)
        if os.path.isfile(file_path):
            os.unlink(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)


def get_filename_and_type(filepath: str) -> tuple:
    """Get filename and file extension from filepath

    Args:
        filepath: path to file

    Returns: 2 element tuple -> (filename, file extension)
    """
    base = os.path.basename(filepath)
    return os.path.splitext(base)


def subprocess_args(include_stdout: bool = True) -> dict:
    """Hide the popping of terminal in case of a subprocess call

    To make console disappear in during subprocess call (when running via exe)
    Create a set of arguments which make a ``subprocess.Popen`` (and
    variants) call work with or without Pyinstaller, ``--noconsole`` or
    not, on Windows and Linux. Typical use::
    subprocess.call(['program_to_run', 'arg_1'], **subprocess_args())

    When calling ``check_output``::

    subprocess.check_output(['program_to_run', 'arg_1'],
                            **subprocess_args(False))

    Args:
        include_stdout: Bool, whether to show stdout or not

    Result:
        Dict with values for different stdout properties set
    """
    # The following is true only on Windows.
    if hasattr(subprocess, 'STARTUPINFO'):
        # On Windows, subprocess calls will pop up a command window by default
        # when run from Pyinstaller with the ``--noconsole`` option. Avoid this
        # distraction.
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        # Windows doesn't search the path by default. Pass it an environment so
        # it will.
        env = os.environ
    else:
        si = None
        env = None

    # ``subprocess.check_output`` doesn't allow specifying ``stdout``::
    #
    #   Traceback (most recent call last):
    #     File "test_subprocess.py", line 58, in <module>
    #       **subprocess_args(stdout=None))
    #     File "C:\Python27\lib\subprocess.py", line 567, in check_output
    #       raise ValueError('stdout argument not allowed, it will be overridden.')
    #   ValueError: stdout argument not allowed, it will be overridden.
    #
    # So, add it only if it's needed.
    if include_stdout:
        ret = {'stdout': subprocess.PIPE}
    else:
        ret = {}

    # On Windows, running this from the binary produced by Pyinstaller
    # with the ``--noconsole`` option requires redirecting everything
    # (stdin, stdout, stderr) to avoid an OSError exception
    # "[Error 6] the handle is invalid."
    ret.update({'stdin': subprocess.PIPE,
                'stderr': subprocess.PIPE,
                'startupinfo': si,
                'env': env})
    return ret


