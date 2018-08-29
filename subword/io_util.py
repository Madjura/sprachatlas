import pickle
from collections import defaultdict

import numpy
import os

from subword.util import make_word_vectors


def load_vectorspace_model(l1=False):
    if l1:
        t = "_l1"
    else:
        t = "_l2"
    with open(os.path.join("models", f"initial_vectors{t}.p"), "rb") as f:
        initial = pickle.load(f)
    with open(os.path.join("models", f"updated_vectors{t}.p"), "rb") as f:
        updated = pickle.load(f)
    with open(os.path.join("models", f"initial_vectors_readable{t}.p"), "rb") as f:
        initial_r = pickle.load(f)
    with open(os.path.join("models", f"updated_vectors_readable{t}.p"), "rb") as f:
        updated_r = pickle.load(f)
    with open(os.path.join("models", f"words_all{t}.p"), "rb") as f:
        words_all = pickle.load(f)
    return initial, updated, initial_r, updated_r, words_all


def save_vectorspace_model(initial, updated, initial_r, updated_r, words_all, l1=False):
    if l1:
        t = "_l1"
    else:
        t = "_l2"
    with open(os.path.join("models", f"initial_vectors{t}.p"), "wb") as f:
        pickle.dump(dict(initial), f)
    with open(os.path.join("models", f"updated_vectors{t}.p"), "wb") as f:
        pickle.dump(dict(updated), f)
    with open(os.path.join("models", f"initial_vectors_readable{t}.p"), "wb") as f:
        pickle.dump(dict(initial_r), f)
    with open(os.path.join("models", f"updated_vectors_readable{t}.p"), "wb") as f:
        pickle.dump(dict(updated_r), f)
    with open(os.path.join("models", f"words_all{t}.p"), "wb") as f:
        pickle.dump(words_all, f)


def save_word_vectors(words_all, updated, m, l1=False):
    if l1:
        t = "_l1"
    else:
        t = "_l2"
    word_vectors = {}
    updated = defaultdict(lambda k: numpy.zeros((m,)), updated)
    for word, pronunciations in words_all.items():
        vectors = make_word_vectors(pronunciations, updated)
        word_vectors[word] = vectors
    with open(os.path.join("models", f"word_vectors{t}.p"), "wb") as f:
        pickle.dump(word_vectors, f)
