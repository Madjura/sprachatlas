"""Levenshtein stuff to help find similar words."""
from operator import itemgetter

import Levenshtein


def find_candidates(word, candidates, limit=10):
    """
    Finds words similar to a given one from a list of words, up to a limit, using Levenshtein.
    :param word: The word.
    :param candidates: The words from which the similar words are to be found.
    :param limit: Optional. Default: 10. The number of similar words to be returned, sorted by similarity.
    :return:
    """
    return sorted([(candidate, Levenshtein.ratio(word, candidate)) for candidate in candidates],
                  key=itemgetter(1), reverse=True)[:limit]


def find_candidates_from_db(word, limit=10, texts=None):
    from sprachatlas import setup
    setup()
    from dataapp.models import InverseIndex
    qs = InverseIndex.objects.values_list("term").distinct()
    if texts:
        texts = texts.split(",")
        checked = []
        qs = InverseIndex.objects.all()
        for t in qs:
            if any(x in t.index for x in texts):
                checked.append(t.term)
        checked = set(checked)
        return find_candidates(word, checked, limit=limit)
    return find_candidates(word, qs, limit=limit)


if __name__ == "__main__":
    from dragn import setup
    setup()
    from dataapp.models import InverseIndex
    words = InverseIndex.objects.values_list("term").distinct()
    print(find_candidates("akkredi", words, 100))
