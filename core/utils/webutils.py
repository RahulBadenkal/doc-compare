"""
Web related utility functions
"""

from datetime import datetime
from urllib.request import urlopen
import logging
import socket
import time


def get_current_datetime() -> datetime:
    """Get current datetime from internet

    Returns:
        current datetime
    """
    now = None
    try:
        res = urlopen('http://just-the-time.appspot.com/')
        result = res.read().strip()
        now_str = result.decode('utf-8')
        now = datetime.strptime(now_str, "%Y-%m-%d %H:%M:%S")
    except Exception:
        logging.exception("Couldn't get time from internet")
    return now


def ping_server(ip, port, retry=3, delay=2, timeout=2):
    ipup = False
    # retry = 3  # No. of tries
    # delay = 2  # Time gap between successive tries
    # timeout = 2  # How long to wait for the server to respond in any try
    msg = ''
    for i in range(retry):
        result = is_server_alive(ip, port, timeout)
        if result['result'] is True:
            ipup = True
            break
        else:
            msg = msg + "Try No.: {}, Couldn't connect to server at ip: {}, port: {} due to {}".format(
                i, ip, port, result['err_msg']) + '\n'
            time.sleep(delay)

    return ipup, msg


def is_server_alive(ip, port, timeout=2):
    retval = {'result': True, 'err_no': 0, 'err_msg': '', 'data': {}}

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((ip, int(port)))
        s.shutdown(socket.SHUT_RDWR)
    except Exception as e:
        retval['result'] = False
        retval['err_no'] = 1
        retval['err_msg'] = e.args
    finally:
        s.close()
        return retval

