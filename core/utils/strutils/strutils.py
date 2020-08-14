import json

from core.utils.strutils import diff_match_patch


class InvalidJSONError(Exception):
    pass


# TODO: Check out whether the default timeout is appropriate or not
def get_text_diffs(original, revised, diff_mode=0, timeout=2):
    """ Get differences between two texts

    3 Modes available:
        0: Character wise diff
        1: Word wise diff
        2: Line wise diff
    """
    dmp = diff_match_patch.diff_match_patch()
    dmp.Diff_Timeout = timeout
    if diff_mode == 0:
        diffs = dmp.diff_main(original, revised)
        dmp.diff_cleanupSemantic(diffs)

    elif diff_mode == 1:
        diff_struct = dmp.diff_linesToWords(original, revised)

        lineText1 = diff_struct[0]  # .chars1;
        lineText2 = diff_struct[1]  # .chars2;
        lineArray = diff_struct[2]  # .lineArray;

        diffs = dmp.diff_main(lineText1, lineText2, checklines=False)
        dmp.diff_charsToLines(diffs, lineArray)

    elif diff_mode == 2:
        diff_struct = dmp.diff_linesToChars(original, revised)

        lineText1 = diff_struct[0]  # .chars1;
        lineText2 = diff_struct[1]  # .chars2;
        lineArray = diff_struct[2]  # .lineArray;

        diffs = dmp.diff_main(lineText1, lineText2, checklines=False)
        dmp.diff_charsToLines(diffs, lineArray)
    else:
        raise ValueError("Given value of diff_mode: {}.\ndiff_mode must be one of {}.".format(diff_mode, [0, 1, 2]))

    return diffs


def is_valid_jsonstr(jsonstr):
    retval = {'result': True, 'err_msg': '', 'err_code': '', 'data': {'json': dict()}}
    # Checking if the file data is in proper json format

    try:
        data = json.loads(jsonstr)
    except json.JSONDecodeError as e:
        err_msg = "msg: {},\n" \
                  "doc: {},\n" \
                  "pos: {},\n" \
                  "lineno: {},\n" \
                  "colno: {}\n".format(e.msg, e.doc, e.pos, e.lineno, e.colno)
        retval['result'] = False
        retval['err_msg'] = err_msg
        return retval

    # json.loads accepts '10', "foo" as a valid json, even though its is not, so weed it out
    if not isinstance(data, dict):
        retval['result'] = False
        retval['err_msg'] = "{} is not a dict".format(data)
        return retval

    retval['result'] = True
    retval['data']['json'] = data
    return retval
