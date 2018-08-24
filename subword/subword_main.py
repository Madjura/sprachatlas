import pickle

import numpy
from scipy.spatial.distance import cosine, cityblock

from subword.freqs_to_graph import freqs_to_graph
from subword.parse_subword import window_ngrams, ngram_freqs
from subword.vectorspace import vectorspace_from_theutonista


def vector_similarities(path_euclidean, path_cosine, vectors=None, sort=False):
    if not vectors:
        with open("updated_vectors_l2.p", "rb") as f:
            vectors = pickle.load(f)
    i = list(vectors.items())
    d = []
    for index, (term, v) in enumerate(i):
        print(f"---Processing vector {index+1} out of {len(i)} for distance calculation---")
        try:
            for second_term, second_v in i[index+1:]:
                c = 1 - cosine(v, second_v)
                d.append((term, second_term, numpy.linalg.norm(v-second_v), c))
        except IndexError:
            # last element
            continue
    with open(path_euclidean, "w", encoding="utf8") as f:
        if sort:
            d = sorted(d, key=lambda k: k[2])
        for i, (t, t2, euclidean_dist, cosine_sim) in enumerate(d):
            print(f"---Writing euclidean distance {i+1} of {len(d)}---")
            f.write(f"{t} {t2} {euclidean_dist}\n")
    with open(path_cosine, "w", encoding="utf8") as f:
        if sort:
            d = sorted(d, key=lambda k: k[3], reverse=True)
        for i, (t, t2, euclidean_dist, cosine_sim) in enumerate(d):
            print(f"---Writing cosine similarity {i+1} of {len(d)}---")
            f.write(f"{t} {t2} {cosine_sim}\n")


def cityblock_distance(path_cityblock, vectors=None, sort=False):
    if not vectors:
        with open("updated_vectors_l1.p", "rb") as f:
            vectors = pickle.load(f)
    i = list(vectors.items())
    d = []
    for index, (term, v) in enumerate(i):
        print(f"---Processing vector {index+1} out of {len(i)} for cityblock distance calculation---")
        try:
            for second_term, second_v in i[index + 1:]:
                d.append((term, second_term, cityblock(v, second_v)))
        except IndexError:
            # last element
            continue
    with open(path_cityblock, "w", encoding="utf8") as f:
        d = sorted(d, key=lambda k: k[2])
        for i, (t, t2, dist) in enumerate(d):
            print(f"---Writing cityblock distance {i+1} of {len(d)}---")
            f.write(f"{t} {t2} {dist}\n")


if __name__ == "__main__":
    try:
        with open("initial_vectors.p", "rb") as f:
            initial = pickle.load(f)
        with open("updated_vectors.p", "rb") as f:
            updated = pickle.load(f)
        with open("initial_vectors_readable.p", "rb") as f:
            initial_r = pickle.load(f)
        with open("updated_vectors_readable.p", "rb") as f:
            updated_r = pickle.load(f)
    except FileNotFoundError:
        p = "E:\PycharmProjects\sprachatlas\dragn-folders\\texts\\t5.txt"
        ngrams, readable, index = window_ngrams(p, 2)
        tmp = [item for sublist in list(ngrams.values()) for item in sublist]
        flat = [x for s in tmp for x in s]
        initial, updated, initial_r, updated_r = vectorspace_from_theutonista(flat, readable)
        with open("initial_vectors.p", "wb") as f:
            pickle.dump(dict(initial), f)
        with open("updated_vectors.p", "wb") as f:
            pickle.dump(dict(updated), f)
        with open("initial_vectors_readable.p", "wb") as f:
            pickle.dump(dict(initial_r), f)
        with open("updated_vectors_readable.p", "wb") as f:
            pickle.dump(dict(updated_r), f)
    vector_similarities("vectors/euclidean_distances.txt", "vectors/cosine_similarities.txt", updated, sort=True)
    # TODO: cityblock needs adjustments for u1 and u2, but that bloats the code but its trivial to add
    # cityblock_distance("vectors/cityblock.txt", updated)
    vector_similarities("vectors/euclidean_distances_r.txt", "vectors/cosine_similarities_r.txt", updated_r, sort=True)
    # cityblock_distance("vectors/cityblock_r.txt", updated_r)

    # freqs, freqs_readable = ngram_freqs(ngrams, readable)
    # g = freqs_to_graph(freqs, freqs_readable)
    # with open("test_graph.json", "w") as f:
    #     f.write(g.to_json())