"""dragn queries."""
from sprachatlas import setup

setup()
from dragnapp.models import Alias

__copyright__ = """
Copyright (C) 2017 Thomas Huber <huber150@stud.uni-passau.de, madjura@gmail.com>
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
from query.queryresult import QueryResult
from pycallgraph.output.graphviz import GraphvizOutput
from pycallgraph.pycallgraph import PyCallGraph


def query(user_query=None, alias=None, lesser_edges=False, a=None):
    """
    Performs a query over texts as specified by the Alias.
    :param user_query: The query of the user.
    :param alias: The Alias of the texts.
    :param lesser_edges: Whether relations between nodes that are not in the query are to be considered.
    :return: A QueryResult object with the query performed.
    """
    if user_query is None:
        user_query = []
    result = QueryResult(alias=alias, lesser_edges=lesser_edges, a=a)
    result.query = user_query
    result.populate_dictionaries()
    # result.populate_dictionaries_db(a)
    # g = result.generate_statement_graph(11, 100, alias=a)
    return result


def query_db(query, alias, lesser_edges=False):
    result = QueryResult(a=alias, lesser_edges=lesser_edges)
    result.query = query
    result.populate_dictionaries_db(alias)
    return result


def with_graphvizoutput():
    """
    Runs query_step with GraphvizOutput, producing a call graph of all functions.
    :return:
    """
    graphviz = GraphvizOutput()
    graphviz.output_file = 'querystep.png'
    with PyCallGraph(output=graphviz):
        query(["cult", "fish", "water", "fear"])


if __name__ == "__main__":
    alias = Alias.objects.get(identifier="cthulhu.txt")
    query(["cult", "fish", "water", "fear"], alias="cthulhu.txt", a=alias)
    # with_graphvizoutput()
