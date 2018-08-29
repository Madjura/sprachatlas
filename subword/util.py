import re

import numpy


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


def word_to_chars(word):
    return re.findall("[a-z][^a-z]*", word, re.IGNORECASE)


def make_word_vectors(words, char_vectors):
    wv = []
    for w in words:
        vector = numpy.zeros((2000, ))
        chars = word_to_chars(w)
        for c in chars:
            vector += char_vectors[c]
        wv.append(vector)
    return wv


def normalize_vectors(d):
    for k, v in d.items():
        d[k] /= numpy.linalg.norm(v)
    return d