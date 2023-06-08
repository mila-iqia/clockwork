"""
This file gathers the function shared by the job parser and the node parser
"""


def ignore(k, v, res):
    pass


def copy(k, v, res):
    res[k] = v


def copy_with_none_as_empty_string(k, v, res):
    if v == "":
        res[k] = None
    else:
        copy(k, v, res)


def rename(name):
    def renamer(k, v, res):
        res[name] = v

    return renamer
