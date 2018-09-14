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
    # freqs = readable  # TODO: experimental
    nodes = [defaultdict(lambda: None), defaultdict(lambda: None)]
    # nodes = defaultdict(lambda: None)
    for i, f in enumerate([freqs, readable]):
        for char, nexts in f[2].items():
            start = nodes[i][char]
            if not start:
                start = CytoNode(name=char, color="#020272", width=25, label_size=int(24*0.25))
                nodes[i][char] = start
            total = sum(nexts.values())
            for next_char, freq in nexts.items():
                next_node = nodes[i][next_char]
                if not next_node:
                    next_node = CytoNode(name=next_char, color="#020272", width=25, label_size=int(24*0.25))
                    nodes[i][next_char] = next_node
                prob = round(freq/total, 4)
                edge = Edge(start=start, end=next_node, color="blue", val=prob)
                start.add_edge_object(edge)
    nodes_all = list(nodes[0].values())
    nodes_readable = list(nodes[1].values())
    g_readable = Graph(nodes=nodes_readable, clean=False)
    g_all = Graph(nodes=nodes_all, clean=False)
    return g_readable, g_all
