import networkx as nx
from scipy.spatial import KDTree
from edge_detection import CELL_TO_CELL_EDGE, CELL_TO_SURFACE_EDGE, CELL_CONTACT_EDGE

NORMAL = "normal"
SPHEROPLAST = "spheroplast"
CURVED = "curved"
FILAMENT = "filament"

EDGE_RELEASE_DISTANCE_THRESHOLD = 50 # px

class PostProcessingManager:
    def __init__(self, bio_objs=None, graph=None):
        if graph is not None:
            self.graph = graph
        else:
            self.graph = nx.MultiGraph()

            # Note: We tried using a filter below, but for some reason it removed all the edges from the cells.
            #       We have no idea why this happened.

            # add all nodes
            for bio_object in bio_objs:
                if not bio_object.is_nanowire():
                    x, y = bio_object.cell_center
                    self.graph.add_node(bio_object.id, x=x, y=y, node_type=NORMAL)

            # add all edges
            for bio_object in bio_objs:
                if not bio_object.is_nanowire():
                    for edge in bio_object.edge_list:
                        if bio_object.id > edge.head.id:
                            continue
                        key = self.graph.new_edge_key(bio_object.id, edge.head.id)
                        if bio_object.id == 0 or edge.head.id == 0: # If cell-to-surface
                            surface_point = {'x': (edge.nanowire.x1 + edge.nanowire.x2) // 2, 'y': (edge.nanowire.y1 + edge.nanowire.y2) // 2}
                            self.graph.add_edge(bio_object.id, edge.head.id, key=key, edge_type=edge.type, surface_point=surface_point)
                        else:
                            self.graph.add_edge(bio_object.id, edge.head.id, key=key, edge_type=edge.type)

        self.tree = self.build_KDTree()

    def build_KDTree(self):
        self.tree = KDTree([(node[1]['x'], node[1]['y']) for node in self.graph.nodes(data=True)])
        return self.tree

    def get_cell_count(self):
        normal_count = 0
        spheroplast_count = 0
        filament_count = 0
        curved_count = 0
        for node_id, node_data in self.graph.nodes(data=True):
            if int(node_id) == 0:
                continue
            if node_data["node_type"] == NORMAL:
                normal_count += 1
            elif node_data["node_type"] == SPHEROPLAST:
                spheroplast_count += 1
            elif node_data["node_type"] == FILAMENT:
                filament_count += 1
            elif node_data["node_type"] == CURVED:
                curved_count += 1

        total_count = normal_count + spheroplast_count + filament_count + curved_count
        return total_count, normal_count, spheroplast_count, filament_count, curved_count

    def get_edge_count(self):
        cell_to_cell_count = 0
        cell_to_surface_count = 0
        cell_contact_count = 0
        for _, _, edge_data in self.graph.edges(data=True):
            if edge_data["edge_type"] == CELL_CONTACT_EDGE:
                cell_contact_count += 1
            elif edge_data["edge_type"] == CELL_TO_CELL_EDGE:
                cell_contact_count += 1
            elif edge_data["edge_type"] == CELL_TO_SURFACE_EDGE:
                cell_to_surface_count += 1

        total_edge_count = cell_to_cell_count + cell_to_surface_count + cell_contact_count
        return total_edge_count, cell_to_cell_count, cell_to_surface_count, cell_contact_count

    def get_closest_node(self, x, y):
        if x is None or y is None:
            return

        dist, index = self.tree.query([x,y])
        if dist > EDGE_RELEASE_DISTANCE_THRESHOLD:
            return
        return list(self.graph.nodes(data=True))[int(index)]
