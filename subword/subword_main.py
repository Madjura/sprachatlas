from subword.parse_subword import window_ngrams, ngram_freqs

if __name__ == "__main__":
    p = "E:\PycharmProjects\sprachatlas\dragn-folders\\texts\\t5.txt"
    ngrams, readable = window_ngrams(p, 2)
    ngram_freqs(ngrams, readable)