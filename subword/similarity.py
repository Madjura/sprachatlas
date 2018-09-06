import os
import pickle
from collections import defaultdict

from scipy.spatial.distance import cosine

from util import paths


def vector_similarities(alias=None):
    alias_text = ""
    if alias:
        alias_text = alias.identifier
    with open(os.path.join(paths.SUBWORD_MODEL_PATH, alias_text, "word_vectors_l2.p"), "rb") as f:
        vectors = pickle.load(f)
    centroids = {}
    for term, vecs in vectors.items():
        v = sum(vecs) / len(vecs)
        centroids[term] = v
    with open(os.path.join(paths.SUBWORD_MODEL_PATH, alias_text, "centroids_l2.p"), "wb") as f:
        pickle.dump(centroids, f)
    centroids = list(centroids.items())
    cosines = defaultdict(lambda: defaultdict(float))
    for i, (term, centroid) in enumerate(centroids):
        for term2, centroid2 in centroids[i+1:]:
            cosines[term][term2] = cosine(centroid, centroid2)
    for k, v in cosines.items():
        cosines[k] = dict(v)
    cosines = dict(cosines)
    with open(os.path.join(paths.SUBWORD_MODEL_PATH, alias_text, "cosines_l2.p"), "wb") as f:
        pickle.dump(cosines, f)
    return cosines


def vector_similarities_text(alias):
    with open(os.path.join(paths.SUBWORD_MODEL_PATH, alias.identifier, "word_vectors_l2.p"), "rb") as f:
        vectors = pickle.load(f)
    centroids = {}
    for term, vecs in vectors.items():
        v = sum(vecs) / len(vecs)
        centroids[term] = v
    p = os.path.join(paths.SUBWORD_MODEL_PATH, alias.identifier, "centroids_l2.p")
    if not os.path.exists(p):
        os.makedirs(p)
    # with open(p, "wb") as f:
    #     pickle.dump(centroids, f)
    centroids = list(centroids.items())
    cosines = defaultdict(lambda: defaultdict(float))
    for i, (term, centroid) in enumerate(centroids):
        for term2, centroid2 in centroids[i + 1:]:
            sim = cosine(centroid, centroid2)
            cosines[term][term2] = sim
            cosines[term2][term] = sim
    for k, v in cosines.items():
        cosines[k] = dict(v)
    # import pprint
    # pprint.pprint(cosines)
    return dict(cosines)


def vector_similarities_compare(alias1, alias2):
    with open(os.path.join(paths.SUBWORD_MODEL_PATH, alias1.identifier, "word_vectors_l2.p"), "rb") as f:
        vectors1 = pickle.load(f)
    with open(os.path.join(paths.SUBWORD_MODEL_PATH, alias2.identifier, "word_vectors_l2.p"), "rb") as f:
        vectors2 = pickle.load(f)
    centroids1 = {}
    for term, vecs in vectors1.items():
        v = sum(vecs) / len(vecs)
        centroids1[term] = v
    p = os.path.join(paths.SUBWORD_MODEL_PATH, alias1.identifier, "centroids_l2.p")
    if not os.path.exists(p):
        os.makedirs(p)
    # with open(p, "wb") as f:
    #     pickle.dump(centroids1, f)

    centroids2 = {}
    for term, vecs in vectors2.items():
        v = sum(vecs) / len(vecs)
        centroids2[term] = v
    p = os.path.join(paths.SUBWORD_MODEL_PATH, alias2.identifier, "centroids_l2.p")
    if not os.path.exists(p):
        os.makedirs(p)
    # with open(p, "wb") as f:
    #     pickle.dump(centroids2, f)

    centroids1 = defaultdict(lambda k: None, centroids1)
    centroids2 = defaultdict(lambda k: None, centroids2)
    cosines = {}
    for term, centroid1 in centroids1.items():
        centroid2 = centroids2[term]
        if centroid2 is None:
            continue
        cosines[term] = cosine(centroid1, centroid2)
    return cosines
