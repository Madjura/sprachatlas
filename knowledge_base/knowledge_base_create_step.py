"""
knowledge_base_create_step of the dragn pipeline. Calculates the FMI between the extracted tokens from the previous
step.
"""
from sprachatlas import setup

setup()
from dragnapp.models import Text, Closeness, Alias, LexiconEntry

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
import pickle

from knowledge_base.neomemstore import NeoMemStore
from util import paths
from pycallgraph.output.graphviz import GraphvizOutput
from pycallgraph.pycallgraph import PyCallGraph


def knowledge_base_create_db(alias):
    memstore = NeoMemStore()
    closenesses = Closeness.objects.for_alias(alias)
    print(f"FOUND {closenesses.count()} CLOSENESSES")
    # closenesses are calculcated in extract_step
    # closenesses = pickle.load(open(paths.CLOSENESS_PATH + alias + "/closeness.p", "rb"))
    memstore.incorporate_db(closenesses)
    print("CALCULATE")
    memstore.compute_corpus()
    print("NORMALISE")
    memstore.normalise_corpus()
    memstore.to_db(alias)


def knowledge_base_create(alias=None):
    """
    NeoMemStore is built in this step, based on the texts from the text_extract
    step.
    After this step, NeoMemStore holds normalised "closeness values":
        <expression> close to <other expression>: normalised value
    For details regarding the normalization, see the compute_corpus() and
    normalise_corpus() methods.

    Detailed explanation of steps:
        1) Load the Closeness objects from extract_step() into the memstore.
            1.1) The lexicon is updated with the frequencies of each relation
                statement.
                The lexicon is just a simple index that holds the frequencies
                of the tokens.
                Example:
                    "Paul" close to "ball"
                    Would update the lexicon like so:
                    lexicon["Paul"] += 1
                    lexicon["close to"] += 1
                    (the frequency for "close to" is not relevant)
                    lexicon["ball"] += 1
            1.2) Update the sources with tuples of the tokens, their relation,
                and the paragraph ID. The value is Closeness.closeness, as
                calculcated in extract_step().
                All the values are taken from the Closeness objects.
                Example:
                    Closeness:
                        term = Paul
                        close_to = ball
                        closeness = 0.8
                        paragraph_id = ball_3.txt
                Would update the sources like so:
                    corpus[("Paul", "close to", "ball", "ball_3.txt")] = 0.8
        2) Computation of the corpus:
            2.1) Get the number of relation tuples from sources, as calculated
                in 1.2).
            2.2) Calculate the independent frequency of each token in the
                tuples.
            2.3) Calculate the joint frequency of each pair of tokens.
            2.4) For each tuple:
                2.4.1) Get all the Closeness.closeness values.
                2.4.2) Calculate the combined joint frequency of the tokens.
                2.4.3) Calculate the mutual information score, multiplied
                    by the joint frequency from 2.3).
                2.4.4) Update the corpus with the tuple of
                    (token, relation, token)
                    Example: ("Paul", "close to", "ball")
                    and the value as the score from 2.4.3), normalized
                    by multiplying it with the sum of sum of frequencies from
                    2.3), divided by the number of frequencies from 2.3).
        3) Normalization of the corpus:
            3.1) Get the calculated corpus weights from compute_corpus()
            3.2) Get the top (1-X)*100% of weights.
                X is based on cut_off, default is 0.95.
                For that value, the top 5% weights are considered.
            3.3) Get the lowest weight value from step 2).
                Example:
                    Assume the weights are a list from 1 to 100.
                    Step 2 would get a list from 96 to 100:
                    [96, 97, 98, 99, 100], the 5% top values.
                    The lowest value would be 96.
            3.4) Get the lowest, non-negative weight and multiply it by min_quo.
            3.5) Then, for each corpus weight:
                3.5.1) Divide by the value from 3).
                3.5.2) If the new weight is negative, set it instead to the
                    value from 4).
                3.5.3) If the new weight is greater or equal 1, set it to 1.0.
                3.5.4) Replace the old weight with the new one from step 5.
        4) Then write the memstore object to the disk.
    :param alias: The Alias of the texts that are being processed.
    """
    memstore = NeoMemStore()
    # closenesses are calculcated in extract_step
    closenesses = pickle.load(open(paths.CLOSENESS_PATH + alias + "/closeness.p", "rb"))
    memstore.incorporate(closenesses)
    memstore.compute_corpus()
    memstore.normalise_corpus()
    memstore.export(paths.MEMSTORE_PATH + alias + "/")


def with_graphvizoutput():
    """Runs index_step with GraphvizOutput, producing a call graph of all functions."""
    graphviz = GraphvizOutput()
    graphviz.output_file = 'knowledge_base_create.png'

    with PyCallGraph(output=graphviz):
        knowledge_base_create()


if __name__ == "__main__":
    alias = Alias.objects.get(identifier="cthulhu.txt")
    LexiconEntry.objects.filter(alias=alias).delete()
    knowledge_base_create_db(alias)
    print("----------------------------------------------------------------")
    # 68150 closeness for cthulhu
    # checked 9 april, same for new and old system
    # knowledge_base_create(alias="/cthulhu.txt")
    # with_graphvizoutput()
