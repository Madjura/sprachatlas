from collections import defaultdict

from parse.parse import vokale, konsonanten
from parse.util import match_recursion2
from segmentation.translate import teuthonista_split, add_theutonista_to_segmented
from subword.util import load_theutonista


def get_ngrams_range(chars, start=2, end=4):
    chars.insert(0, "<")
    chars.append(">")
    ngrams_d = defaultdict(lambda: list())
    for n in range(start, end+1):
        for pos in range(0, len(chars)-n+1):
            c = chars[pos:pos+n]
            ngrams_d[n].append(c)
    ngrams_d = dict(ngrams_d)
    return ngrams_d


def parse_theutonista_to_ngrams(words, ngram_start=2, ngram_end=4):
    char_to_pos = defaultdict(lambda: list())
    pos_to_chars = defaultdict(lambda: list())
    ngrams_total = defaultdict(lambda: list())
    readable_total = {}
    for i, word in enumerate(words):
        prev = 0
        chars_to_check = []
        flag = False
        pos = 0
        for j, c in enumerate(word):
            if c.isalpha():
                if not flag:
                    flag = True
                if flag:
                    to_add = word[prev:j]
                    if to_add:
                        chars_to_check.append(word[prev:j])
                    prev = j
                    flag = False
                char_to_pos[c].append(pos)
                pos_to_chars[pos].append(c)
                pos += 1
        chars_to_check.append(word[prev:])
        ngrams = get_ngrams_range(chars_to_check, start=ngram_start, end=ngram_end)
        ngrams = dict(ngrams)
        for k, v in ngrams.items():
            ngrams_total[k].extend(v)
        chars_to_readable = defaultdict(lambda: list())
        for ngram_size, ngrams_list in ngrams.items():
            for ngram in ngrams_list:
                c = ngram[0]
                if c == "<":
                    ngram = ngram[1:]
                elif c == ">":
                    ngram = ngram[:-1]
                for char in ngram:
                    if char in "<>":
                        continue
                    if not chars_to_readable[char]:
                        if char[0] in "aeiou":
                            r = vokale.scanString(char)
                            t = "Vokale"
                        else:
                            r = konsonanten.scanString(char)
                            t = "Konsonanten"
                        for match in r:
                            m, _, _ = match
                            new_chars = match_recursion2(m, t, char[0])
                            chars_to_readable[char] = new_chars
        chars_to_readable = dict(chars_to_readable)
        for k, v in chars_to_readable.items():
            readable_total[k] = v
    return dict(ngrams_total), dict(readable_total)


def window_ngrams(path, debug_limit=None):
    t = load_theutonista(path)
    readable_all = defaultdict(lambda: list())
    ngrams_all = defaultdict(lambda: list())
    for i, (_start, _end, raw) in enumerate(t):
        if i == debug_limit:
            break
        raw = raw.replace("\n", "")
        segs = teuthonista_split(raw)
        w = add_theutonista_to_segmented(raw, segs)
        print(w)
        w = list(w.values())
        ngrams, readable = parse_theutonista_to_ngrams(w)
        for k, v in readable.items():
            l = readable_all[k]
            l.extend(v)
            readable_all[k] = list(set(l))
        for k, v in ngrams.items():
            ngrams_all[k].extend(v)
    return ngrams_all, readable_all


def ngram_freqs(ngrams, readable):
    freqs = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    freqs_readable = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    for size, ngrams in ngrams.items():
        for ngram in ngrams:
            prev = ngram[0]
            prev_readable = readable[prev]  # is a list
            if not prev_readable:
                if prev not in "<>":
                    print(f"---> SUSPICIOUS CHARACTER, NOT FOUND IN READABLE: {char}")
                prev_readable = [prev]
            for char in ngram[1:]:
                freqs[size][prev][char] += 1
                char_readable = readable[char]
                if not char_readable:
                    if char not in "<>":
                        print(f"---> SUSPICIOUS CHARACTER, NOT FOUND IN READABLE: {char}")
                    char_readable = [char]  # beginning/end characters <>
                for r in char_readable:
                    for p in prev_readable:
                        freqs_readable[size][p][r] += 1
                prev = char
                prev_readable = char_readable
    print(freqs)
    print(freqs_readable)