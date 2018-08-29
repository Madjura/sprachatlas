import os
import pickle
from collections import defaultdict

from scipy.spatial.distance import cosine


def vector_similarities():
    with open(os.path.join("models", "word_vectors_l2.p"), "rb") as f:
        vectors = pickle.load(f)
    centroids = {}
    for term, vecs in vectors.items():
        v = sum(vecs) / len(vecs)
        centroids[term] = v
    with open(os.path.join("models", "centroids_l2.p"), "wb") as f:
        pickle.dump(centroids, f)
    centroids = list(centroids.items())
    cosines = defaultdict(lambda: defaultdict(float))
    tmp = []
    for i, (term, centroid) in enumerate(centroids):
        for term2, centroid2 in centroids[i+1:]:
            cosines[term][term2] = cosine(centroid, centroid2)
            if len(term) >= 4 and len(term2) >= 4:
                tmp.append((term, term2, cosine(centroid, centroid2)))
    for k, v in cosines.items():
        cosines[k] = dict(v)
    tmp = sorted(tmp, key=lambda k: k[2], reverse=True)
    print(tmp[:10])
    cosines = dict(cosines)
    with open(os.path.join("models", "cosines_l2.p"), "wb") as f:
        pickle.dump(cosines, f)
