"""
knowledge_base_compute_step of the dragn pipeline. Calculates the Cosine Similarity based on the FMI value from
the previous step.
"""
import operator

import re

from django.db import IntegrityError

from sprachatlas import setup
from knowledge_base.tensor import Tensor

setup()
from dragnapp.models import KbRelation, Alias, LexiconEntry

__copyright__ = """
Copyright (C) 2017 Thomas Huber <huber150@stud.uni-passau.de, madjura@gmail.com>
Copyright (C) 2012 Vit Novacek (vit.novacek@deri.org), Digital Enterprise
Research Institute (DERI), National University of Ireland Galway (NUIG)
All rights reserved.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
from knowledge_base.analyser import Analyser
from knowledge_base.neomemstore import NeoMemStore
from util import paths


def sort_lexicon(alias, ignored=None, limit=0):
    """
    Sorts the contents of the lexicon.

    :param ignored: A regex of words to be ignored.
    :param limit: How many elements are to be returned.
    :return: Lexicon, but sorted and with only the specified number of items.
    """
    # format is [(expression, frequency), (expression2, frequency2), ...]
    entries = LexiconEntry.objects.filter(alias=alias)
    lexicon = {}
    for e in entries:
        lexicon[e.token] = e.frequency
    print("LEXICON ENTRIES: ", len(lexicon))
    sorted_by_value = [x for x in sorted(lexicon.items(), key=operator.itemgetter(1), reverse=True)]
    if limit > 0:
        sorted_by_value = sorted_by_value[:limit]  # from 0 to limit
    elif limit <= 0 and ignored:
        sorted_by_value_with_limit = []
        for frequency in sorted_by_value:
            if not re.search(ignored, frequency[0]):
                sorted_by_value_with_limit.append(frequency)
        avg = sum(x[1] for x in sorted_by_value_with_limit) / float(len(sorted_by_value_with_limit))
        sorted_by_value = [x[0] for x in sorted_by_value_with_limit if x[1] >= avg]
    return sorted_by_value


def knowledge_base_compute_db(top=100, alias=None):
    relations = KbRelation.objects.for_alias(alias=alias, related_to=False)
    print("RELATIONS TOTAL NEW SYSTEM, START: ", relations.count())
    tensor = Tensor(rank=3)
    for relation in relations:
        tensor.base_dict[relation.subject, relation.predicate, relation.object] = relation.value
    matrix = tensor.matricise(0)
    analyser = Analyser(matrix=matrix, trace=True)
    tokens = [x for x in sort_lexicon(alias=alias, ignored="(Model).*|.*Paragraph [0-9]+$|.*_[0-9]+$|related to|close to")]
    print("NEW SYSTEM, LEN TOKENS: ", len(tokens))
    similarity_dictionary = {}
    for i, subject in enumerate(tokens):
        print(i, " out of ", len(tokens))
        similar = analyser.similar_to(subject, top=top)
        for objecT, weight in similar:
            triple1 = (subject, "related to", objecT)
            triple2 = (objecT, "related to", subject)
            if not any(triple in similarity_dictionary for triple in [triple1, triple2]):
                similarity_dictionary[(subject, "related to", objecT)] = weight
    relations = []
    for (s, p, o), value in similarity_dictionary.items():
        relations.append(KbRelation(subject=s, predicate=p, object=o, value=value, alias=alias, paragraph=None))
    print("SAVING NOW")
    print(f"TOTAL NUMBER OF KBRELATIONS: {len(relations)}")
    try:
        KbRelation.objects.bulk_create(relations)
    except IntegrityError as e:
        print("INTEGRITYERROR: ", e)


def knowledge_base_compute(top=100, alias=None):
    """
    In this step, expressions related to other expressions are identified and
    stored in the NeoMemStore.
    The format is:
        <expression> related to <other expression>: Value
    This uses the Analyser class to perform the calculations and produce that format.

    Detailed explanation:
        1) The memstore from the previous step (knowledge_base_create())
            is loaded.
        2) The perspective is computed:
            2.1) The corpus is converted to a matrix.
            2.2) The format is:
                token (close to, other_token) -> weight
        3) The Analyser is created. This is used to calculate the "related to"
            relations.
        4) The top memstore lexicon elements are calculated:
            4.1) The lexicon is sorted by frequency values, descending.
            4.2) Frequencies of tokens that are relation statements (close to,
                related to) or provenances are ignored.
            4.3) The average of the remaining frequencies is calculated.
            4.4) All the tokens with above-average frequency are returned in
                a list.
        5) The top elements from 4) are iterated over:
            5.1) For each token, the tokens that are similar are calculated.
                5.1.1) The basis for this are the sparse-representation of the
                    matrix from 2) and the "inverse" of that that is calculated
                    in the same step.
                    The format of the sparse is:
                        {token: {(relation, token): weight, ...} }
                    The format of the inverse is:
                        (relation, token: [tokens]
                5.1.2) The row from the sparse matrix for the token is
                    collected.
                    Example:
                        sparse[Paul] =
                            {(close to, ball): 0.8, (close to, roof): 0.7, ...}
                5.1.3) The length of the row is calculated:
                    sqrt(sum(weights)^2)
                5.1.4) The possibly related tokens are collected from the
                    inverse and iterated over.
                    5.1.4.1) The row for the token is collected from the sparse.
                    5.1.4.2) For each expression ((close to, token)), check
                        if it also appears in the row from 5.1.2).
                    5.1.4.3) If it does, multiply the values from the rows
                        and keep them in a variable and add the statements
                        to a list.
                    5.1.4.4) Add the square of the compared row to a variable.
                    5.1.4.5) After 5.1.4.2), take the square root of the value
                        from 5.1.4.4) to get the length.
                    5.1.4.6) If sum of the products from 5.1.4.3) divided by
                        the length from the previous step multiplied by the sum
                        is above the threshhold, add that value and the current
                        token/expression to a list of results:
                            [(value, token from 5.1.4))]
                        This is used to indicate how closely related the token
                        from 5.1) and the current one are.
                5.1.5) Sort the list from 5.1.4.6) by values, descending, and
                    return a list of tuples of the relation value and the token,
                    relative to the one from step 5.1).
            5.2) For each "related to" relation from 5.1.5), add that
                relation to a dictionary:
                    (token, "related to", other_token): value
            5.3) Finally, add the "related to" relations to the corpus of
                the memstore.
        6) Write the memstore, now containing the "related to" relations,
            to the disk.
    :param top: Optional. Default: 100. How many of the highest scoring relations are to be exmained for similarity.
    :param alias: The Alias of the texts that are being processed.
    :return:
    """
    memstore = NeoMemStore()
    memstore.import_memstore(paths.MEMSTORE_PATH + alias)
    print("RELATIONS TOTAL, OLD SYSTEM, START: ", len(memstore.corpus))
    matrix = memstore.corpus.matricise(0)
    analyser = Analyser(matrix=matrix, trace=True)
    tokens = [x for x in memstore.sorted(ignored=".*_[0-9]+$|related to|close to")]
    print("OLD SYSTEM, LEN TOKENS: ", len(tokens))
    similarity_dictionary = {}
    for i, subject in enumerate(tokens):
        print(i, " out of ", len(tokens))
        similar = analyser.similar_to(subject, top=top)
        for objecT, weight in similar:
            triple1 = (subject, "related to", objecT)
            triple2 = (objecT, "related to", subject)
            if not any(triple in similarity_dictionary for triple in [triple1, triple2]):
                similarity_dictionary[(subject, "related to", objecT)] = weight
    for key, value in similarity_dictionary.items():
        memstore.corpus[key] = value
    print(f"OLD SYSTEM, DICT SIZE: {len(memstore.corpus)}")
    memstore.export(paths.MEMSTORE_PATH + alias + "/")


if __name__ == "__main__":
    alias = Alias.objects.get(identifier="cthulhu.txt")
    knowledge_base_compute_db(alias=alias)
    print("------------------------------------")
    # knowledge_base_compute(alias="/cthulhu.txt")
