def match_recursion(v, t, c):
    new_chars = []
    try:
        for k, vv in v.asDict().items():
            if k == t:
                continue
            new_char = f"{c}--{k.lower()}"
            new_chars.append(new_char)
            new_chars.extend(match_recursion(v[k], t, c))
    except AttributeError:
        pass  # recursion end
    return new_chars
