import networkx as nx
from matplotlib import pyplot as plt
import sys


if len(sys.argv) != 2:
    print("USAGE: python3 view_gexf.py <gexf_file>", file=sys.stderr)
    sys.exit(1)

filename = sys.argv[1]

graph = nx.read_gexf(filename)

nx.draw(graph)
plt.show()
