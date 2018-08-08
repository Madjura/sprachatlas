def load_theutonista(path):
    with open(path, "r", encoding="utf8") as f:
        lines = f.readlines()
    out = []
    for line in lines:
        try:
            start, end, content = line.split("\t")
            out.append((start, end, content))
        except ValueError:
            print(f"ERROR LINE: {line}")
    return out
