import random
from collections import defaultdict
from copy import deepcopy

import numpy
from numpy import array, zeros


def generate_char_vector(m=2000, alpha=250, l1=False):
    """
    Generates a new candidate term vector with randomly distributed values.

    :param m: Optional. Default: 2000. The dimensionality of the vector.
    :param alpha: Optional. Default: 250. Value >= 1. The lower, the more common are non-zero elements in the vector.
    :param l1: Optional. Default: False. Whether the term vector will be used to build an l1-normed vectorspace or
        l2-normed.
    :return: A numpy.ndarray representing the new term vector.
    """
    case1 = 1/(2*alpha)
    case3 = 1 - case1
    data = []
    u1 = 1
    u2 = 1
    if l1:
        u1 = float(numpy.random.uniform())
        u2 = float(numpy.random.uniform())
    for i in range(m):
        r = random.random()
        if r <= case1:
            data.append(float(-1/u1))
        elif case1 < r < case3:
            data.append(float(0))
        else:
            data.append(float(1/u2))
    return array(data)


def vectorspace_from_theutonista(chars, readable, window=3, m=2000, alpha=250, l1=False):
    initial_vectors = defaultdict(lambda: None)
    updated_vectors = defaultdict(lambda: list())
    initial_vectors_readable = defaultdict(lambda: None)
    updated_vectors_readable = defaultdict(lambda: list())
    for i, char in enumerate(chars):
        v = initial_vectors[char]
        readables = readable[char]
        # initialize vectors
        if v is None:
            v = generate_char_vector(m, alpha)
            initial_vectors[char] = v
        for r in readables:
            if initial_vectors_readable[r] is None:
                initial_vectors_readable[r] = generate_char_vector(m, alpha, l1)
        v_update = deepcopy(v)
        # get chars that appear before in window
        prevs = []
        if i > 0:
            prevs = chars[i-1::-1][:window]
        # get chars that appear after in window
        nexts = chars[i+1:i+window+1]
        for in_window in prevs + nexts:
            window_vector = initial_vectors[in_window]
            window_readables = readable[in_window]
            # initialize window vectors if needed
            if window_vector is None:
                window_vector = generate_char_vector(m, alpha)
                initial_vectors[char] = window_vector
            for r in window_readables:
                if initial_vectors_readable[r] is None:
                    initial_vectors_readable[r] = generate_char_vector(m, alpha, l1)
            v_update += window_vector
            for r in readables:
                # NOTE! add initial vector to the sum of the vectors to get the proper result
                for wr in window_readables:
                    updated_vectors_readable[r].append(initial_vectors_readable[wr])
        updated_vectors[char].append(v_update)
    for k, v in updated_vectors.items():
        updated_vectors[k] = sum(v)
    for k, v in updated_vectors_readable.items():
        if initial_vectors_readable[k] is None:
            initial = zeros((m, ))
        else:
            initial = initial_vectors_readable[k]
        updated_vectors_readable[k] = sum(v) + initial
    return initial_vectors, updated_vectors, initial_vectors_readable, updated_vectors_readable
