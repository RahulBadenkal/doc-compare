import eel


def calljs_func_by_name(jsfunc_name, *args):
    return eel.executeFunctionByName(jsfunc_name, *args)()


def progress_msg(jsfunc_name, msg):
    calljs_func_by_name(jsfunc_name, msg)


def to_cancel(jsfunc_name):
    return calljs_func_by_name(jsfunc_name)
