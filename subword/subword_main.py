from subword.parse_subword import parse_theutonista_to_ngrams
from subword.util import load_theutonista

if __name__ == "__main__":
    p = "E:\PycharmProjects\sprachatlas\dragn-folders\\texts\\t5.txt"
    t = load_theutonista(p)
    # TODO: parse into words
    parse_theutonista_to_ngrams(t)
