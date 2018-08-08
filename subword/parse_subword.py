from parse.parse import vokale, konsonanten
from parse.util import match_recursion


def parse_theutonista_to_ngrams(words, ngram_start=3, ngram_end=6):
    # TODO: needs to be a list of theutonista WORDS, not LINES
    ngrams_d = {x: [] for x in range(ngram_start, ngram_end+1)}
    ngrams_done = {x: [] for x in range(ngram_start, ngram_end+1)}
    print(ngrams_d)
    for i, (_start, _end, c) in enumerate(words):
        char = c[0]
        ngrams_add = []
        if char in "aeiouAEIOU":
            # vocal
            r = vokale.scanString(c)
            # r = halbvokal.scanString(cc)
            for match in r:
                m, _, _ = match
                new_chars = match_recursion(m, "Vokale", char)
                for n in new_chars:
                    ngrams_add.append(n.lower())
        else:
            # consonant
            r = konsonanten.scanString(c)
            for match in r:
                m, _, _ = match
                new_chars = match_recursion(m, "Konsonanten", char)
                for n in new_chars:
                    ngrams_add.append(n.lower())
        ngrams_add = list(set(ngrams_add))
        c = 0
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
            c += 1
