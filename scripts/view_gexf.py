import networkx as nx
from matplotlib import pyplot as plt

graph = nx.read_gexf("demo.gexf")

nx.draw(graph)
plt.show()
