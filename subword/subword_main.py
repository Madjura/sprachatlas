from subword.io_util import load_vectorspace_model, save_vectorspace_model, save_word_vectors
from subword.parse_subword import window_ngrams
from subword.similarity import vector_similarities
from subword.util import normalize_vectors
from subword.vectorspace import vectorspace_from_theutonista


def create_vectorspace_and_word_vectors(l1=False, m=2000):
    try:
        initial, updated, initial_r, updated_r, words_all = load_vectorspace_model(l1=l1)
    except FileNotFoundError:
        p = "sample.txt"
        ngrams, readable, index, words_all = window_ngrams(p)
        tmp = [item for sublist in list(ngrams.values()) for item in sublist]
        flat = [x for s in tmp for x in s]
        initial, updated, initial_r, updated_r = vectorspace_from_theutonista(flat, readable, l1=l1, m=m)
        initial = normalize_vectors(initial)
        updated = normalize_vectors(updated)
        initial_r = normalize_vectors(initial_r)
        updated_r = normalize_vectors(updated_r)
        save_vectorspace_model(initial, updated, initial_r, updated_r, words_all)
    save_word_vectors(words_all, updated, m)


if __name__ == "__main__":
    # create_vectorspace_and_word_vectors(l1=False)
    # create_vectorspace_and_word_vectors(l1=True)
    vector_similarities()

    # freqs, freqs_readable = ngram_freqs(ngrams, readable)
    # g = freqs_to_graph(freqs, freqs_readable)
    # with open("test_graph.json", "w") as f:
    #     f.write(g.to_json())
