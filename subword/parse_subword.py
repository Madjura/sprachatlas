from collections import defaultdict

from parse.parse import parse_all, vokale, konsonanten
from parse.util import match_recursion, match_recursion2


def parse_theutonista_to_ngrams(words, ngram_start=3, ngram_end=3):
    # TODO: needs to be a list of theutonista WORDS, not LINES
    ngrams_d = {x: [] for x in range(ngram_start, ngram_end+1)}
    ngrams_done = {x: [] for x in range(ngram_start, ngram_end+1)}
    print(ngrams_d)
    char_to_pos = defaultdict(lambda: list())
    pos_to_chars = defaultdict(lambda: list())
    for i, word in enumerate(words):
        ngrams_add = []
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
        for char in chars_to_check:
            if char[0] in "aeiou":
                r = vokale.scanString(char)
                t = "Vokale"
            else:
                r = konsonanten.scanString(char)
                t = "Konsonanten"
            for match in r:
                m, _, _ = match
                new_chars = match_recursion2(m, t, char[0])
                for n in new_chars:
                    ngrams_add.append(n.lower())
        char_to_pos = dict(char_to_pos)
        pos_to_chars = dict(pos_to_chars)
        ngrams_add = list(set(ngrams_add))
        done = []
        last = max(list(pos_to_chars.keys()))
        firsts = []
        lasts = []
        for n in ngrams_add:
            nn = n[0]  # first char
            if nn in pos_to_chars[0]:
                firsts.append(n)
            if nn in pos_to_chars[last]:
                lasts.append(n)
        current = 1
        while current <= last:
            for ngram_size, ngrams in ngrams_d.items():
                if ngrams and len(ngrams[0]) == ngram_size:
                    # full, move
                    new_sublists = []
                    for sublist in ngrams:
                        ngrams_done[ngram_size].append("".join(sublist))
                        new_sublists.append(sublist[1:])
                    ngrams_d[ngram_size] = new_sublists
                    if current == last:
                        for sublist in new_sublists:
                            sublist.append(">")
                            ngrams_done[ngram_size].append("".join(sublist))
                        break
                else:
                    # check empty
                    if not ngrams:
                        for f in firsts:
                            ngrams_d[ngram_size].append(["<", f"||{f}"])
                    else:
                        for sublist in ngrams:
                            for char in pos_to_chars[current]:
                                sublist.append(char)
                        current += 1
        for ngram_size, ngrams in ngrams_d.items():
            if ngrams and len(ngrams[0]) == ngram_size:
                ngrams_done[ngram_size].append("".join(ngrams))
                ngrams_d[ngram_size] = ngrams[1:]
            else:
                if not ngrams:
                    # initial character
                    for ngram_add in ngrams_add:
                        ngrams_d[ngram_size].append(["<", f"||{ngram_add}"])
                # TODO: this case is wrong - needs a solution
                elif len(ngrams[0]) == ngram_size - 1:
                    # last character
                    for sublist in ngrams:
                        for ngram_add in ngrams_add:
                            sublist.append(f"||{ngram_add}")
                        sublist.append("||>")
                else:
                    for sublist in ngrams:
                        for ngram_add in ngrams_add:
                            sublist.append(f"||{ngram_add}")