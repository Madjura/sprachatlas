import random
import pickle
from collections import defaultdict
from copy import deepcopy


from numpy import array, zeros


def generate_char_vector(m=2000, alpha=250, u1=1, u2=1):
    """
    Generates a new candidate term vector with randomly distributed values.

    :param m: Optional. Default: 2000. The dimensionality of the vector.
    :param alpha: Optional. Default: 250. Value >= 1. The lower, the more common are non-zero elements in the vector.
    :return: A numpy.ndarray representing the new term vector.
    """
    case1 = 1/(2*alpha)
    case3 = 1 - case1
    data = []
    c1 = 0
    c2 = 0
    c3 = 0
    for i in range(m):
        r = random.random()
        if r <= case1:
            c1 += 1
            data.append(float((-1/u1)*r))
        elif case1 < r < case3:
            c2 += 1
            data.append(float(0))
        else:
            c3 += 1
            data.append(float((1/u2)*r))
    return array(data)


def vectorspace_from_theutonista(chars, readable, window=3, m=2000, alpha=250, u1=1, u2=1):
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
                initial_vectors_readable[r] = generate_char_vector(m, alpha, u1, u2)
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
                    initial_vectors_readable[r] = generate_char_vector(m, alpha, u1, u2)
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
            print("THIS SHOULD NOT BE POSSIBLE")
        else:
            initial = initial_vectors_readable[k]
        updated_vectors_readable[k] = sum(v) + initial
    return initial_vectors, updated_vectors, initial_vectors_readable, updated_vectors_readable
