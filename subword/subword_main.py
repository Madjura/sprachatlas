from parse.parse import parse_all
from segmentation.translate import teuthonista_split, add_theutonista_to_segmented
from subword.parse_subword import parse_theutonista_to_ngrams
from subword.util import load_theutonista

if __name__ == "__main__":
    word = "o=x6"
    r = parse_all.scanString(word)
    r = list(r)
    for match in r:
        m, _, _ = match
        print(m)
    print(r)

    p = "E:\PycharmProjects\sprachatlas\dragn-folders\\texts\\t5.txt"
    t = load_theutonista(p)
    # TODO: parse into words
    tt = "u5ntdo5-2ha2+-2nsda5nmi-2det1s2wo2-he2nta2+-2e2+(:)ts9a2k2"
    segs = teuthonista_split(tt)
    w = add_theutonista_to_segmented(tt, segs)
    print(w)
    w = list(w.values())
    parse_theutonista_to_ngrams(w)
