import networkx as nx
from scipy.spatial import KDTree

class PostProcessingManager:
    def __init__(self, bio_objs):
        self.graph = nx.MultiGraph()

        # add all nodes
        for bio_object in bio_objs:
            if not bio_object.is_nanowire():
                x, y = bio_object.cell_center
                self.graph.add_node(bio_object.id, x=x, y=y)

        # add all edges
        for bio_object in bio_objs:
            if not bio_object.is_nanowire():
                for edge in bio_object.edge_list:
                    if bio_object.id > edge.head.id:
                        continue
                    self.graph.add_edge(bio_object.id, edge.head.id, type=edge.type)
        self.build_KDTree()

    def build_KDTree(self):
        self.tree = KDTree([[node[1]['x'], node[1]['y']] for node in self.graph.nodes(data=True)])

    def get_cell_count(self):
        return len(self.graph.nodes(data=True)) - 1

    def get_closest_node(self, x, y):
        dist, index = self.tree.query([x,y])
        nodes = list(self.graph.nodes(data=True))
        return nodes[int(index)]
