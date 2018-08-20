from subword.freqs_to_graph import freqs_to_graph
from subword.parse_subword import window_ngrams, ngram_freqs

if __name__ == "__main__":
    p = "E:\PycharmProjects\sprachatlas\dragn-folders\\texts\\t5.txt"
    ngrams, readable, index = window_ngrams(p, 2)
    freqs, freqs_readable = ngram_freqs(ngrams, readable)
    g = freqs_to_graph(freqs, freqs_readable)
    with open("test_graph.json", "w") as f:
        f.write(g.to_json())