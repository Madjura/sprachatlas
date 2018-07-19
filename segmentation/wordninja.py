import gzip, os, re
from math import log

# taken from and modified for bavarian https://github.com/keredson/wordninja
from segmentation.db import bavarian_frequencies

__version__ = '0.1.3'


# I did not author this code, only tweaked it from:
# http://stackoverflow.com/a/11642687/2449774
# Thanks Generic Human!


# Build a cost dictionary, assuming Zipf's law and cost = -math.log(probability).
words = bavarian_frequencies()
_wordcost = dict((k, log((i+1)*log(len(words)))) for i, k in enumerate(words))
_maxword = max(len(x) for x in words)
_SPLIT_RE = re.compile("[^a-zA-Z0-9]+")


def segmentation(s):
    """Uses dynamic programming to infer the location of spaces in a string without spaces."""
    l = [_split(x) for x in _SPLIT_RE.split(s)]
    return [item for sublist in l for item in sublist]


def _split(s):
    # Find the best match for the i first characters, assuming cost has
    # been built for the i-1 first characters.
    # Returns a pair (match_cost, match_length).
    def best_match(ii):
        candidates = enumerate(reversed(cost[max(0, ii-_maxword):ii]))
        return min((cc + _wordcost.get(s[ii-kk-1:ii], 9e999), kk+1) for kk, cc in candidates)

    # Build the cost array.
    cost = [0]
    for i in range(1, len(s)+1):
        c, k = best_match(i)
        cost.append(c)

    # Backtrack to recover the minimal-cost string.
    out = []
    i = len(s)
    while i > 0:
        c, k = best_match(i)
        assert c == cost[i]
        out.append(s[i-k:i])
        i -= k
    return reversed(out)


if __name__ == "__main__":
    "de2-2ho5-da2rex68d2a2gro5$o2s81ma-2o2lvo2-na,du5-2ndhi5nt1"
    test = "dehodarechdagrosmaovonadundhint"
    print(segmentation(test))
