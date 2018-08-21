"""Graphs in the dragn graph system."""
from collections import defaultdict

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
import json


class Graph(object):
    """Simple graph with nodes and edges."""
    def __init__(self, *, nodes=None, clean=True):
        """
        Constructor.
        :param nodes: Optional. A list of nodes that make up the graph.
        :param clean: Optional. Default: True. Whether nodes with no connected edges are to be deleted.
        """
        if nodes is not None:
            self.nodes = nodes
        else:
            self.nodes = []
        if clean:
            cleaned = []
            unclean = []
            for node in nodes:
                if not node.edges:
                    unclean.append(node)
                else:
                    cleaned.append(node)
            all_cleaned = []
            for node in cleaned:
                all_cleaned.append(node)
                for edge in node.edges:
                    if edge.end in unclean:
                        all_cleaned.append(edge.end)
            self.nodes = all_cleaned

    def __str__(self, *args, **kwargs):
        out = ""
        for node in self.nodes:
            out += "Node: {}\n".format(node.name)
            for edge in node.edges:
                out += "--- Edge from {} to {}\n".format(edge.start, edge.end)
        return out

    def to_json(self):
        """
        Converts the graph into RFC4627 compliant JSON. 
        The resulting JSON string is intended to be used with 
        Cytoscape.js 3.0.0 (http://js.cytoscape.org/) and can be loaded into
        it to display the graph.
        :return An RFC4627 compliant JSON string for use with Cytoscape.js.
        """
        # separate lists required to have the nodes before the edges,
        # needed for cytoscape, the edges need the id of the node
        nodes = []
        edges = []
        color2shape = defaultdict(lambda: "circle")
        color2shape["lightgreen"] = "pentagon"
        for i, node in enumerate(self.nodes):
            nodes.append({
                "group": "nodes",
                "data": {
                    "id": node.name,
                    "font-size": 20,
                    "size": node.label_size * 3,
                    "width": node.width,
                    "color": node.color
                },
                "position": {
                    "x": i,
                    "y": i
                },
                "grabbable": True,
                "classes": "node-class",
                "style": {
                    "content": node.name,
                    "shape": color2shape[node.color]
                }
            })
            for j, edge in enumerate(node.edges):
                edges.append({
                    "group": "edges",
                    "data": {
                        "id": "e{}-{}".format(i, j),
                        "source": edge.start.name,
                        "target": edge.end.name,
                        "color": edge.color,
                        "provs": list(edge.provs)
                    },
                    "style": {
                        "label": "{0:.2f}".format(edge.val),
                        "color": "black",
                        "curve-style": "bezier",
                        "control-point-step-size": 150,
                        "font-size": 20,
                        "text-valign": "bottom",
                        "text-halign": "right",
                    }
                })
        return json.dumps(nodes + edges)
