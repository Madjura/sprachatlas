from functools import reduce

from sprachatlas import setup

setup()
from dragnapp.models import IndexRelation

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

// Modifications made to the code of the original system by Vit Novacek
----------------
2017, Thomas Huber
* May: load_suid2stmt renamed to load_token2related
* May: added support for dragn graph system
* May: populate_dictionaries completely rebuilt
* May: prepare_for_query completely rebuilt
* May: filter_relevant completely rebuilt
"""
import gzip
import os
from _collections import defaultdict
from ast import literal_eval
from itertools import combinations
from math import log

import ujson

from graph.edge import Edge
from graph.graph import Graph
from graph.node import CytoNode
from query.fuzzyset import FuzzySet, ProvFuzzySet
from util import paths


class QueryResult(object):
    """
    Wrapper over the processed text files to produce a graph in JSON
    format that can be displayed to the user.
    """

    def __init__(self, min_weight=0.5, alias=None, relation_type="all", lesser_edges=False, a=None):
        """
        Constructor.

        :param min_weight: Optional. Default: 0.5. The minimum weight relations need to have to be considered.
        :param alias: The Alias of the texts being queried.
        :param relation_type: Optional. Default: "all". The type of relations to display.
        :param lesser_edges: Optional. Default: True. Whether or not edges and relations between nodes that are not
            in the query are to be considered.
        """
        self.query = None
        self.lesser_edges = lesser_edges
        self.queried_combined = defaultdict(lambda: set())
        self.aliases = defaultdict(lambda: set())
        self.tokens2weights = defaultdict(int)
        self.relation_set = FuzzySet()
        self.provenance_set = FuzzySet()
        # minimum weight that relations must have to be considered
        self.min_weight = min_weight
        self.visualization_parameters = self.load_parameters()
        if alias:
            print("Loading relation to provenance mapping")
            self.relation2prov = self.load_relation2prov(path=os.path.join(paths.RELATION_PROVENANCES_PATH, alias,
                                                                           "r2p.json"))
            print("Loading related")
            self.relations = self.load_token2related(
                path=os.path.join(paths.RELATIONS_PATH, alias, "relations.tsv.gz"), relation_type=relation_type)
        else:
            self.relation2prov = None
            self.relations = None
        self.alias = alias
        self.provenance_dict = None

    # noinspection PyArgumentList
    @staticmethod
    def load_relation2prov(path=None):
        """
        Loads the mapping of relation tuples to the provenances.
        The format is: (token, related_to, token2): [ (provenance, weight), ...]

        :param path: Optional. Default: paths.RELATION_PROVENANCES_PATH. The path to the file of
            tuple -> provennces mapping, as created in index_step.
        :return: A dictionary of relation tripe -> provenance mappings.
        """
        import time
        start_time = time.time()
        with open(path.replace("provenances.tsv.gz", "r2p.json")) as f:
            relation2prov = ujson.load(f)
        fix = {}
        for key in relation2prov.keys():
            fix[literal_eval(key)] = relation2prov[key]
        relation2prov = fix
        print("--- %s seconds FOR LOADING DICT ---" % (time.time() - start_time))
        start_time = time.time()
        # get the maximum value for each prov
        # this is necessary because in index step we calculate additional triples that are immediately written to file
        # here we eliminate the duplicates and take just the max value
        for key, value in relation2prov.items():
            prov_max = defaultdict(int)
            for l in value:
                tmp = []
                it = iter(l)
                for x in it:
                    tmp.append((x, next(it)))
                for prov, score in tmp:
                    current = prov_max[prov]
                    if score > current:
                        prov_max[prov] = score
            tmp = [(prov, score) for prov, score in prov_max.items()]
            relation2prov[key] = [tmp]
        print("--- %s seconds FOR SECOND HALF ---" % (time.time() - start_time))
        return defaultdict(lambda: list(), relation2prov)

    def prepare_for_query_db(self, alias):
        query_terms = [x for x in self.query]
        query_relevant = FuzzySet()
        for term in self.query:
            # get IndexRelations where term is present
            # fill query_relevant with (related, score)
            # set query_relevant to 1.0 for all queryterms
            # return query_relevant
            relations = IndexRelation.objects.all_relations_for_term(alias=alias, term=term)
            tuple_list = []
            for r in relations:
                if r.subject == term:
                    tuple_list.append((r.object, r.value))
                elif r.object == term:
                    tuple_list.append((r.subject, r.value))
                else:
                    print("ALERT SHOULD NOT BE POSSIBLE")
            query_relevant |= FuzzySet([x for x in tuple_list])
        for x in query_terms:
            query_relevant[x] = 1.0
        return query_relevant

    def prepare_for_query(self):
        """Returns FuzzySet containing tokens relevant to the query."""
        query_terms = [x for x in self.query]
        query_relevant = FuzzySet()
        for term in self.query:
            # x are tuples of (token, weight)
            # keeps the higher value of "close to" and "related to" both present
            triple_list = self.relations[term]
            tuple_list = []
            for spo, score in triple_list:
                s, _, o = spo
                tuple_token = None
                if s == term:
                    tuple_token = o
                elif o == term:
                    tuple_token = s
                tuple_list.append((tuple_token, score))
            query_relevant |= FuzzySet([x for x in tuple_list])
            # legacy stuff that is probably not important but ill keep it just in case everything goes up in flames
            # query_relevant = query_relevant | FuzzySet([x for x in self.relation_sets[term]])
        for x in query_terms:
            query_relevant[x] = 1.0
        # query_relevant = query_relevant | FuzzySet([(x, 1.0) for x in query_terms])
        return query_relevant

    def filter_relevant(self, relevant: FuzzySet):
        """
        Filters the relation tuples by the min_weight specified.
        Relation tuples that are below the specified value will be excluded
        from the result.

        :param relevant: A FuzzySet containing the (token, weight) tuples for the query terms.
        :return: A FuzzySet with the values that were below the min_weight threshhold.
        """
        relevant_cut = FuzzySet()
        for token in relevant.cut(self.min_weight):
            relevant_cut[token] = relevant[token]
        return relevant_cut

    @staticmethod
    def load_relation_sets(path=paths.RELATION_WEIGHT_PATH):
        """
        Loads the processed relationsets from index_step.
        Returns a dictionary mapping tokens to a list of tuples in the format:
            token: [ (token2, weight), ... ]
        This dictionary can be used to access the tokens that are related to
        another token by accessing the dictionary by key.

        :param path: Optional. Default: paths.RELATION_WEIGHT_PATH. The path where the shortform of relation mappings
            is stored.
        """
        relations = defaultdict(lambda: list())
        with gzip.open(os.path.join(path, "relationsets.tsv.gz"), "rb") as f:
            for line in f:
                line_split = line.decode().split("\t")
                token, token2, weight = line_split
                relation_tuple = (token2, float(weight))
                relations[token].append(relation_tuple)
        return relations

    def populate_dictionaries_db(self, alias=None):
        provenance_dict = defaultdict(lambda: [0, set()])
        query_relevant = self.prepare_for_query_db(alias)
        related_tokens = self.filter_relevant(query_relevant)
        # iterate over the tokens relevant to the query
        for possibly_related in related_tokens:
            # get all relation triples in which "possibly_related" appears
            relations = IndexRelation.objects.all_relations_for_term(alias, possibly_related)
            for relation in relations:
                s, p, o, w, pp = relation.get_value_triple(paragraph=True)
                # find the relation triples that contain "possibly_related" and
                # a term from the query
                if not (s in self.query or o in self.query):
                    # random relation that does not have any relevance
                    continue
                # get the membership degree of "possibly related" to the query
                # this is the higher value of "related to" or "close to"
                membership = related_tokens[possibly_related]
                calculated_relation_weight = membership * w
                # add updated score to subject and object
                self.tokens2weights[s] += calculated_relation_weight
                self.tokens2weights[o] += calculated_relation_weight
                flag = True
                provs = IndexRelation.objects.all_provs_for_triple(alias, s, p, o)
                for paragraph, score in provs:
                    if flag:
                        self.relation_set[(s, p, o)] += calculated_relation_weight
                        flag = False
                        provenance_dict[paragraph][0] += calculated_relation_weight * score
                        provenance_dict[paragraph][1].add((score, s, p, o))
        self.provenance_dict = provenance_dict

    def populate_dictionaries(self, alias=None):
        """
        Prepares the ranking of tokens / relations for use with the graph.
        
            1) Get all tokens possibly relevant to the query
            2) Get all triples related to the token in some way
            3) Filter out those that don't have relevance to the query or that token
            4) Get the degree of membership of the token <-> the query
            5) Multiply the membership with the weight from the triple
            6) Add that value to a dict for the related token and the matching queryterm (used to calculate nodes)
            7) Get the provenance, weight tuple for the relation triple
            8) Weight the provenance by the prov weight * relation weight * membership
        """
        provenance_dict = defaultdict(lambda: [0, set()])
        query_relevant = self.prepare_for_query()
        related_tokens = self.filter_relevant(query_relevant)
        # iterate over the tokens relevant to the query
        for possibly_related in related_tokens:
            # get all relation tuples in which "possibly_related" appears
            for relation_triple in self.relations[possibly_related]:
                (subject, predicate, objecT), relation_weight = relation_triple
                # find the relation triples that contain "possibly_related" and
                # a term from the query
                if not (subject in self.query or objecT in self.query):
                    # random relation that does not have any relevance
                    continue
                # get the membership degree of "possibly related" to the query
                # this is the higher value of "related to" or "close to"
                membership = related_tokens[possibly_related]
                calculated_relation_weight = membership * relation_weight
                # add updated score to subject and object
                self.tokens2weights[subject] += calculated_relation_weight
                self.tokens2weights[objecT] += calculated_relation_weight
                flag = True
                for prov_tuple in self.relation2prov[(subject, predicate, objecT)]:
                    if flag:
                        self.relation_set[(subject, predicate, objecT)] += calculated_relation_weight
                        flag = False
                    for provenance, prov_weight in prov_tuple:
                        provenance_dict[provenance][0] += calculated_relation_weight * prov_weight
                        provenance_dict[provenance][1].add((prov_weight, subject, predicate, objecT))
        self.provenance_dict = provenance_dict

    def generate_statement_nodes(self, max_nodes):
        """
        Generates the nodes that exist in the query-graph.

        :param max_nodes: The maximum number of nodes.
        :return: A list of nodes that make up the graph.
        """
        # get and sort the relevant tokens by weight
        token_list = list(self.tokens2weights.items())
        token_list.sort(key=lambda x: x[1], reverse=True)
        tokens = [x[0] for x in token_list[:max_nodes]]
        # weight for normalization
        token_weight = {x: self.tokens2weights[x] for x in tokens}
        norm = 1.0
        graph_nodes = {}
        if token_weight:
            norm = min(token_weight.values())
        for token in token_weight:
            token_weight[token] /= norm
        for token in tokens:
            node_width = log(self.visualization_parameters["node width"] * token_weight[token], 10)
            if node_width < 0.4:
                node_width = 0.4
            font_size = int(24 * node_width)
            node_color = self.visualization_parameters["node color"]
            # if token in self.queried_combined:
            if token in self.query:
                node_color = "lightgreen"
            graph_nodes[token] = CytoNode(name=token,
                                          color=node_color,
                                          width=node_width,
                                          label_size=font_size)
        return graph_nodes

    def generate_statement_graph_db(self, max_nodes, max_edges, alias):
        """
        Generates the graph object for the query.
        Only the top most relevant nodes and edges are in the graph.

        :param max_nodes: The maximum number of nodes in the graph.
        :param max_edges: The maximum number of edges in the graph.
        :return: A Graph object representing the result graph.
        """
        # get all the graph nodes
        nodes = self.generate_statement_nodes(max_nodes)
        token_list = list(self.relation_set.items())
        edge_count = 0
        token_list.sort(key=lambda x: x[1], reverse=True)
        length_dict = defaultdict(lambda: list())
        # get lengths of relations in graph
        for relation_triple, weight in token_list:
            subject, predicate, objecT = relation_triple
            if (subject, predicate, objecT) in length_dict:
                length_dict[(subject, predicate, objecT)].append(weight)
            elif (objecT, predicate, subject) in length_dict:
                length_dict[(objecT, predicate, subject)].append(weight)
            else:
                length_dict[(subject, predicate, objecT)].append(weight)
        for key, value in length_dict.items():
            length_dict[key] = reduce(lambda x, y: x + y, value) / len(value)
        # TODO: check if this double pass through the same loop is needed
        for relation_triple, weight in token_list:
            if edge_count >= max_edges:
                break
            subject, predicate, objecT = relation_triple
            if (subject, predicate, objecT) in length_dict:
                length = length_dict[(subject, predicate, objecT)]
            else:
                length = length_dict[(objecT, predicate, subject)]
            if subject in nodes and objecT in nodes:
                if predicate in self.visualization_parameters["edge color"]:
                    edge_color = self.visualization_parameters["edge color"][predicate]
                else:
                    edge_color = "black"
                # new edge from subject to object
                graph_edge = Edge(start=nodes[subject], end=nodes[objecT], color=edge_color, val=length)
                # back edge from object to subject, needed for cytoscape.js to work properly
                back_edge = Edge(start=nodes[objecT], end=nodes[subject], color=edge_color, val=length)

                # check case for subject to object
                possible_duplicate = nodes[subject].get_edge(end=nodes[objecT])
                if not possible_duplicate:
                    # check if reverse edge exists
                    if nodes[objecT].get_edge(end=nodes[subject]):
                        continue
                if (possible_duplicate and possible_duplicate.color != graph_edge.color) or not possible_duplicate:
                    edge = nodes[objecT].get_edge(end=nodes[subject])
                    if not edge or edge.color != graph_edge.color:
                        s, p, o = relation_triple
                        relations = [x for x, _ in IndexRelation.objects.all_provs_for_triple(alias, s, p, o)]
                        graph_edge.provs |= set(relations)
                        nodes[subject].add_edge_object(graph_edge)
                # check case for object to subject
                if possible_duplicate:
                    continue
                possible_duplicate = nodes[objecT].get_edge(end=nodes[subject])
                if (possible_duplicate and possible_duplicate.color != back_edge.color) or not possible_duplicate:
                    edge = nodes[subject].get_edge(end=nodes[objecT])
                    if not edge or edge.color != back_edge.color:
                        s, p, o = relation_triple
                        relations = [x for x, _ in IndexRelation.objects.all_provs_for_triple(alias, s, p, o)]
                        back_edge.provs |= set(relations)
                        nodes[objecT].add_edge_object(back_edge)
        if self.lesser_edges:
            for combo in list(combinations(nodes.keys(), 2)):
                if edge_count >= max_edges:
                    break
                s, o = combo
                t1 = (s, "close to", o)
                t2 = (o, "close to", s)
                t11 = (s, "related to", o)
                t22 = (o, "related to", s)
                to_check = [t1, t2, t11, t22]
                # possible problem with creating non-existant relations again
                # explanation: example for "devil" and "unto"
                # "unto" appears in the text, "devil" does not
                # graph has unto related to devil, so it adds the relation to the table
                for t in to_check:
                    if any(t_ in self.relation_set for t_ in to_check):
                        break
                    val = self.relation2prov[t]
                    if not val:
                        continue
                    ss, pp, oo = t
                    edge_color = self.visualization_parameters["edge color"][pp]
                    check_edge = nodes[oo].get_edge(end=nodes[ss])
                    if not check_edge:
                        nodes[ss].get_edge(end=nodes[oo])
                    if check_edge and check_edge.color != edge_color:
                        edge_color = "magenta"
                    new_edge = Edge(start=nodes[ss], end=nodes[oo], color=edge_color)
                    nodes[ss].add_edge_object(new_edge)
                    edge_count += 2
                    for pt in val:
                        for prov, weight in pt:
                            self.provenance_dict[prov][0] += weight
                            self.provenance_dict[prov][1].add((weight, ss, pp, oo))
        self.provenance_set = ProvFuzzySet.from_list_dictionary(self.provenance_dict)
        return Graph(nodes=list(nodes.values()), clean=False)

    def generate_statement_graph(self, max_nodes, max_edges, alias=None):
        """
        Generates the graph object for the query.
        Only the top most relevant nodes and edges are in the graph.

        :param max_nodes: The maximum number of nodes in the graph.
        :param max_edges: The maximum number of edges in the graph.
        :return: A Graph object representing the result graph.
        """
        # get all the graph nodes
        nodes = self.generate_statement_nodes(max_nodes)
        token_list = list(self.relation_set.items())
        edge_count = 0
        token_list.sort(key=lambda x: x[1], reverse=True)
        length_dict = defaultdict(lambda: list())
        # get lengths of relations in graph
        for relation_triple, weight in token_list:
            subject, predicate, objecT = relation_triple
            if (subject, predicate, objecT) in length_dict:
                length_dict[(subject, predicate, objecT)].append(weight)
            elif (objecT, predicate, subject) in length_dict:
                length_dict[(objecT, predicate, subject)].append(weight)
            else:
                length_dict[(subject, predicate, objecT)].append(weight)
        for key, value in length_dict.items():
            length_dict[key] = reduce(lambda x, y: x+y, value) / len(value)
        # TODO: check if this double pass through the same loop is needed
        for relation_triple, weight in token_list:
            if edge_count >= max_edges:
                break
            subject, predicate, objecT = relation_triple
            if (subject, predicate, objecT) in length_dict:
                length = length_dict[(subject, predicate, objecT)]
            else:
                length = length_dict[(objecT, predicate, subject)]
            if subject in nodes and objecT in nodes:
                if predicate in self.visualization_parameters["edge color"]:
                    edge_color = self.visualization_parameters["edge color"][predicate]
                else:
                    edge_color = "black"
                # new edge from subject to object
                graph_edge = Edge(start=nodes[subject], end=nodes[objecT], color=edge_color, val=length)
                # back edge from object to subject, needed for cytoscape.js to work properly
                back_edge = Edge(start=nodes[objecT], end=nodes[subject], color=edge_color, val=length)

                # check case for subject to object
                possible_duplicate = nodes[subject].get_edge(end=nodes[objecT])
                if not possible_duplicate:
                    # check if reverse edge exists
                    if nodes[objecT].get_edge(end=nodes[subject]):
                        continue
                if (possible_duplicate and possible_duplicate.color != graph_edge.color) or not possible_duplicate:
                    edge = nodes[objecT].get_edge(end=nodes[subject])
                    if not edge or edge.color != graph_edge.color:
                        # TODO: check if this is always a nested list and if it is, fix it
                        relations = [x for x, _ in self.relation2prov[relation_triple][0]]
                        graph_edge.provs |= set(relations)
                        nodes[subject].add_edge_object(graph_edge)
                # check case for object to subject
                if possible_duplicate:
                    continue
                possible_duplicate = nodes[objecT].get_edge(end=nodes[subject])
                if (possible_duplicate and possible_duplicate.color != back_edge.color) or not possible_duplicate:
                    edge = nodes[subject].get_edge(end=nodes[objecT])
                    if not edge or edge.color != back_edge.color:
                        # TODO: check if this is always a nested list and if it is, fix it
                        relations = [x for x, _ in self.relation2prov[relation_triple][0]]
                        back_edge.provs |= set(relations)
                        nodes[objecT].add_edge_object(back_edge)
        if self.lesser_edges:
            for combo in list(combinations(nodes.keys(), 2)):
                if edge_count >= max_edges:
                    break
                s, o = combo
                t1 = (s, "close to", o)
                t2 = (o, "close to", s)
                t11 = (s, "related to", o)
                t22 = (o, "related to", s)
                to_check = [t1, t2, t11, t22]
                # possible problem with creating non-existant relations again
                # explanation: example for "devil" and "unto"
                # "unto" appears in the text, "devil" does not
                # graph has unto related to devil, so it adds the relation to the table
                for t in to_check:
                    if any(t_ in self.relation_set for t_ in to_check):
                        break
                    val = self.relation2prov[t]
                    if not val:
                        continue
                    ss, pp, oo = t
                    edge_color = self.visualization_parameters["edge color"][pp]
                    check_edge = nodes[oo].get_edge(end=nodes[ss])
                    if not check_edge:
                        nodes[ss].get_edge(end=nodes[oo])
                    if check_edge and check_edge.color != edge_color:
                        edge_color = "magenta"
                    new_edge = Edge(start=nodes[ss], end=nodes[oo], color=edge_color)
                    nodes[ss].add_edge_object(new_edge)
                    edge_count += 2
                    for pt in val:
                        for prov, weight in pt:
                            self.provenance_dict[prov][0] += weight
                            self.provenance_dict[prov][1].add((weight, ss, pp, oo))
        self.provenance_set = ProvFuzzySet.from_list_dictionary(self.provenance_dict)
        return Graph(nodes=list(nodes.values()), clean=False)

    @staticmethod
    def load_token2related(path=os.path.join(paths.RELATIONS_PATH, "relations.tsv.gz"), relation_type="all"):
        """
        Loads the mapping of tokens to the related tokens.

        :param path: Optional. Default: os.path.join(paths.RELATIONS_PATH, "relations.tsv.gz"). The path to where the
            mapping of triples to provenances is stored.
        :param relation_type: Optional. Default: "all". The type of relation to be considered.
        :return: A dictionary containing a mapping of SPO-triples to (provenance, score) tuples.
        """
        token2related = defaultdict(lambda: list())
        with gzip.open(path, "rb") as f:
            for line in f:
                spl = line.decode().split("\t")
                try:
                    relation_triple = literal_eval(spl[0])
                except SyntaxError:
                    continue
                weight = float(spl[1])
                subject, predicate, objecT = relation_triple
                if relation_type == "related to" and predicate != "related to":
                    continue
                elif relation_type == "close to" and predicate != "close to":
                    continue
                token2related[subject].append((relation_triple, weight))
                token2related[objecT].append((relation_triple, weight))
            f.close()
        return token2related

    @staticmethod
    def load_parameters():
        """Returns a dictionary of visualization parameters used for the graph."""
        parameters = {
            "node width": 0.25,
            "node color": "#020272",
            "max label length": 50,
            "edge color": {
                "related to": "red",
                "close to": "blue"
            }
        }
        return parameters

    def get_top_provenances(self, top=10):
        """
        Returns the highest scoring provenances, sorted descendingly.

        :param top: The number of provenances to return.
        :return: A list of the highest scoring provenances, sorted descendingly.
        """
        tops = []
        for item in self.provenance_set.sort(reverse=True, limit=top):
            tops.append(item)
        return tops


if __name__ == "__main__":
    import time
    start = time.time()
    foo = QueryResult()
    print("INIT TOOK: ", time.time() - start)
    foo.query = ["cult", ]
    start = time.time()
    foo.populate_dictionaries()
    print("POPULTATE TOOK: ", time.time() - start)
    foo.generate_statement_graph(50, 100)
    foo.get_top_provenances()
