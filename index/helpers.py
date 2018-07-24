"""Helper methods for index_step."""
from django.db import IntegrityError, transaction

from dragnapp.models import IndexRelation, KbRelation

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
from _collections import defaultdict


def generate_relation_provenance_weights(relations, corpus):
    """Generates the mapping of predicate tuples to provenance with their score therein."""
    relation2prov = defaultdict(lambda: list())
    index = defaultdict(lambda: set())
    for (subject, predicate, objecT, provenance), score in relations.items():
        score = corpus[(subject, predicate, objecT)]
        relation2prov[(subject, predicate, objecT)].append((provenance, score))
        index[subject].add(provenance)
        index[objecT].add(provenance)
    return relation2prov, index


def _relation2prov(alias):
    mapping = defaultdict(lambda: list())
    relations = IndexRelation.objects.filter(alias=alias, paragraph__isnull=False, predicate="close to").select_related("paragraph", "paragraph__text", "alias")
    for r in relations:
        mapping[(r.subject, r.predicate, r.object)].append((r.paragraph, r.value))
    return mapping


def add_related_to_db_fix(alias):
    rel = []
    dictionary = defaultdict(lambda: defaultdict(float))
    relations_d = defaultdict(lambda: set())
    relations = KbRelation.objects.for_alias(alias, all_relations=True)
    relation2prov = defaultdict(lambda: list())
    for r in relations:
        s, p, o, w, pp = r.get_value_triple(paragraph=True)
        relations_d[s].add((p, o))
        if p == "related to":
            rel.append(((s, p, o), w))
        else:
            relation2prov[(s, p, o)].append((pp, w))
    # check all "related to" triples
    for i, ((s, p, o), w) in enumerate(rel):
        print(f"{i} out of {len(rel)}")
        combined_relations = relations_d[s] & relations_d[o]
        prov2relatedscore = defaultdict(lambda: list())
        # get all the overlaps
        for related_p, related in combined_relations:
            triple1 = (s, related_p, related)
            triple2 = (o, related_p, related)
            relations_to_check = []
            if triple1 in relation2prov:
                relations_to_check.append((("SUBJECT", related), relation2prov[triple1]))
            if triple2 in relation2prov:
                relations_to_check.append((("OBJECT", related), relation2prov[triple2]))
            for relation_tuple in relations_to_check:
                rrelated, provs = relation_tuple
                for prov, score in provs:
                    # TODO: check why this happens
                    score = score or 0
                    prov2relatedscore[prov].append((rrelated, score))
        for provenance, tuples in prov2relatedscore.items():
            max_scores = sorted(tuples, key=lambda x: x[1], reverse=True)
            score_prev = None
            max_score_tuple_list = []
            for m_tuple in max_scores:
                _, score = m_tuple
                if not score_prev:
                    score_prev = score
                if score == score_prev:
                    max_score_tuple_list.append(m_tuple)
                else:
                    break
            for max_score_tuple in max_score_tuple_list:
                related_tuple, prov_weight = max_score_tuple
                identifier, actual_related = related_tuple
                if identifier == "SUBJECT":
                    # noinspection PyPep8Naming
                    o = actual_related
                elif identifier == "OBJECT":
                    s = actual_related
                prov_weight *= w
                dictionary[(s, p, o)][provenance] = prov_weight
    tmp = defaultdict(lambda: list())
    for (s, p, o), provs in dictionary.items():
        for prov, score in provs.items():
            tmp[(s, p, o)].append((prov, score))
    return {**tmp, **relation2prov}


def add_related_to_db(alias):
    relations = IndexRelation.objects.for_alias(alias=alias)
    rel = []
    dictionary = defaultdict(lambda: list())
    relations_d = defaultdict(lambda: set())
    new_relations = []
    for relation in relations:
        s, p, o, w, paragraph = relation.get_value_triple(paragraph=True)
        relations_d[s].add((p, o))
        if p == "related to":
            rel.append(((s, p, o), w, paragraph))
    # check all "related to" triples
    print("Loading relation2prov")
    relation2prov = _relation2prov(alias)
    print("Processing related relations")
    for i, ((s, p, o), w, paragraph) in enumerate(rel):
        print(f"Processing {i} out of {len(rel)}")
        combined_relations = relations_d[s] & relations_d[o]
        prov2relatedscore = defaultdict(lambda: list())
        # get all the overlaps
        for related_relation, related in combined_relations:
            relations_to_check = []
            # TODO: find a way to speed this up if possible
            triple1check = relation2prov[(s, related_relation, o)]
            triple2check = relation2prov[(o, related_relation, s)]
            if triple1check:
                for prov, value in triple1check:
                    relations_to_check.append((("SUBJECT", related), (prov, value)))
            if triple2check:
                for prov, value in triple2check:
                    relations_to_check.append((("OBJECT", related), (prov, value)))
            for relation_tuple in relations_to_check:
                rr, provs = relation_tuple
                prov, score = provs
                prov2relatedscore[prov].append((rr, score))
        for provenance, tuples in prov2relatedscore.items():
            max_scores = sorted(tuples, key=lambda x: x[1], reverse=True)
            score_prev = None
            max_score_tuple_list = []
            for m_tuple in max_scores:
                _, score = m_tuple
                if not score_prev:
                    score_prev = score
                if score == score_prev:
                    max_score_tuple_list.append(m_tuple)
            for max_score_tuple in max_score_tuple_list:
                related_tuple, prov_weight = max_score_tuple
                identifier, actual_related = related_tuple
                if identifier == "SUBJECT":
                    # noinspection PyPep8Naming
                    o = actual_related
                elif identifier == "OBJECT":
                    s = actual_related
                prov_weight *= w
                new_relations.append(IndexRelation(alias=alias, subject=s, predicate=p, object=o, value=prov_weight,
                                                   paragraph=paragraph))
    print(new_relations)
    print("SAVING")
    try:
        with transaction.atomic():
            IndexRelation.objects.bulk_create(new_relations)
    except IntegrityError as e:
        print(f"IntegrityError while writing 'related to' relations to db:\n{e}")
    return dictionary


def add_related_to(relations, relation2prov):
    """
    Calculates "related to" relations.

    :param relations: Relations that were already found.
    :param relation2prov: The dictionary mapping relations to the provenance.
    :return: A dictionary containing the "related to" relations.
    """
    # TODO: related is used in 2 loops, this could be wrong
    related = []
    dictionary = defaultdict(lambda: list())
    relations_d = defaultdict(lambda: set())
    for (subject, predicate, objecT), weight in relations.items():
        relations_d[subject].add((predicate, objecT))
        if predicate == "related to":
            related.append(((subject, predicate, objecT), weight))
    # check all "related to" triples
    for (subject, predicate, objecT), weight in related:
        combined_relations = relations_d[subject] & relations_d[objecT]
        prov2relatedscore = defaultdict(lambda: list())
        # get all the overlaps
        for related_relation, related in combined_relations:
            triple1 = (subject, related_relation, related)
            triple2 = (objecT, related_relation, related)
            relations_to_check = []
            if triple1 in relation2prov:
                relations_to_check.append((("SUBJECT", related), relation2prov[triple1]))
            if triple2 in relation2prov:
                relations_to_check.append((("OBJECT", related), relation2prov[triple2]))
            for relation_tuple in relations_to_check:
                related, provs = relation_tuple
                for prov, score in provs:
                    prov2relatedscore[prov].append((related, score))
        for provenance, tuples in prov2relatedscore.items():
            max_scores = sorted(tuples, key=lambda x: x[1], reverse=True)
            score_prev = None
            max_score_tuple_list = []
            for m_tuple in max_scores:
                _, score = m_tuple
                if not score_prev:
                    score_prev = score
                if score == score_prev:
                    max_score_tuple_list.append(m_tuple)
            for max_score_tuple in max_score_tuple_list:
                related_tuple, prov_weight = max_score_tuple
                identifier, actual_related = related_tuple
                if identifier == "SUBJECT":
                    # noinspection PyPep8Naming
                    objecT = actual_related
                elif identifier == "OBJECT":
                    subject = actual_related
                else:
                    raise ValueError("This should never happen unless something goes HORRIBLY wrong. Problematic "
                                     "value: " + identifier)
                prov_weight *= weight
                dictionary[(subject, predicate, objecT)].append((provenance, prov_weight))
    return dictionary


def index_to_db(index):
    """
    Writes the inverted index to the database.

    :param index: The index.
    :return:
    """
    import django
    import os
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dragn.settings")
    django.setup()
    from dataapp.models import InverseIndex

    bulk = []
    for term, provs in index.items():
        bulk.extend([InverseIndex(term=term, index=prov) for prov in provs])
    # noinspection PyBroadException
    try:
        InverseIndex.objects.bulk_create(bulk)
    except:
        print("DUPLICATE INDEX DETECTED. TEXT(S) ALREADY INDEXED.")
        return
    print("MADE {} INDEX OBJECTS".format(len(bulk)))
