import math
from collections import defaultdict

from graph.edge import Edge
from graph.graph import Graph
from graph.node import CytoNode

parameters = {
    "node width": 0.25,
    "node color": "#020272",
    "max label length": 50,
    "edge color": {
        "related to": "red",
        "close to": "blue"
    }
}


def freqs_to_graph(freqs, readable):
    freqs = readable  # TODO: experimental
    nodes = defaultdict(lambda: None)
    for char, nexts in freqs[2].items():
        start = nodes[char]
        if not start:
            start = CytoNode(name=char, color="#020272", width=25, label_size=int(24*0.25))
            nodes[char] = start
        total = sum(nexts.values())
        for next_char, freq in nexts.items():
            next_node = nodes[next_char]
            if not next_node:
                next_node = CytoNode(name=next_char, color="#020272", width=25, label_size=int(24*0.25))
                nodes[next_char] = next_node
            prob = round(freq/total, 4)
            edge = Edge(start=start, end=next_node, color="blue", val=prob)
            start.add_edge_object(edge)
    nodes = list(nodes.values())
    g = Graph(nodes=nodes, clean=False)
    return g