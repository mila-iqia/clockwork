import re

FIELD = re.compile("([a-zA-z]+)=(.*?)(?: ([a-zA-Z]+=.*)|$)")


def gen_dicts(f):
    """Yields dicts from blocks in the 'scontrol show' output format."""
    curd = dict()
    for line in f:
        line = line.strip()
        if line == "":
            if curd:
                yield curd
            curd = dict()
            continue
        while line:
            m = FIELD.match(line)
            if m is None:
                raise ValueError("Unexpected non-matching expression: " + line)
            curd[m.group(1)] = m.group(2)
            line = m.group(3)
    if curd:
        yield curd
