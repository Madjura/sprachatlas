import pickle
from collections import defaultdict

import numpy
import os

from subword.util import make_word_vectors
from util.paths import SUBWORD_MODEL_PATH


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


def load_graph(alias, readable=True):
    if readable:
        r = "readable"
    else:
        r = "all"
    with open(os.path.join(SUBWORD_MODEL_PATH, alias.identifier, f"bigram_graph__{r}.json"), "r") as f:
        return f.read()


def save_vectorspace_model(initial, updated, initial_r, updated_r, words_all, l1=False, modelpath="models",
                           alias_text=""):
    if l1:
        t = "_l1"
    else:
        t = "_l2"
    if not os.path.exists(os.path.join(modelpath, alias_text)):
        os.makedirs(os.path.join(modelpath, alias_text))
    with open(os.path.join(modelpath, alias_text, f"initial_vectors{t}.p"), "wb") as f:
        pickle.dump(dict(initial), f)
    with open(os.path.join(modelpath, alias_text, f"updated_vectors{t}.p"), "wb") as f:
        pickle.dump(dict(updated), f)
    with open(os.path.join(modelpath, alias_text, f"initial_vectors_readable{t}.p"), "wb") as f:
        pickle.dump(dict(initial_r), f)
    with open(os.path.join(modelpath, alias_text, f"updated_vectors_readable{t}.p"), "wb") as f:
        pickle.dump(dict(updated_r), f)
    with open(os.path.join(modelpath, alias_text, f"words_all{t}.p"), "wb") as f:
        pickle.dump(words_all, f)


def save_word_vectors(words_all, updated, m, l1=False, modelpath="models", alias_text=""):
    if l1:
        t = "_l1"
    else:
        t = "_l2"
    word_vectors = {}
    updated = defaultdict(lambda k: numpy.zeros((m,)), updated)
    for word, pronunciations in words_all.items():
        vectors = make_word_vectors(pronunciations, updated)
        word_vectors[word] = vectors
    with open(os.path.join(modelpath, alias_text, f"word_vectors{t}.p"), "wb") as f:
        pickle.dump(word_vectors, f)


def save_bigram_graph(g, modelpath="models", alias_text="", readable=True):
    if readable:
        r = "readable"
    else:
        r = "all"
    p = os.path.join(modelpath, alias_text, f"bigram_graph__{r}.json")
    print(p)
    with open(p, "w") as f:
        f.write(g.to_json())
