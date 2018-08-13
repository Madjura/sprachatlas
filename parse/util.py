def match_recursion(v, t, c):
    new_chars = []
    try:
        vvv = v.asDict()
        for k, vv in vvv.items():
            if k == t:
                continue
            new_char = f"{c}--{k.lower()}"
            if k[0] != ">":
                new_chars.append(new_char)
            new_chars.extend(match_recursion(v[k], t, c))
    except AttributeError:
        pass  # recursion end
    return new_chars


def match_recursion2(v, t, c, foo=False):
    new_chars = []
    try:
        if type(v) is list:
            vvv = v[0]
        else:
            vvv = v.asDict()
        for k, vv in vvv.items():
            if k == t:
                continue
            new_char = f"{c}--{k.lower()}"
            if k[0] == ">":
                continue
            new_chars.append(new_char)
            to_add = match_recursion2(vv, t, c, foo=True)
            new_chars.extend(to_add)
    except AttributeError:
        pass  # recursion end
    return new_chars
