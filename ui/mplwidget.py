# ------------------------------------------------------
# -------------------- mplwidget.py --------------------
# ------------------------------------------------------
from sys import path
path.append("src")

from PyQt5.QtWidgets import *
from matplotlib.backends.backend_qt5agg import FigureCanvas
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from PyQt5 import QtCore
from edge_detection import CELL_TO_CELL_EDGE, CELL_TO_SURFACE_EDGE, CELL_CONTACT_EDGE

BACKGROUND_COLOR = "#EFEFEF"
CONTOUR_COLORS = ["red", "orange", "yellow", "green", "blue", "indigo", "violet"]
NANOWIRE_BBOX_COLOR = "yellow"
CELL_BBOX_COLOR = "blue"
CELL_CONTACT_COLOR = "red"
CELL_TO_CELL_COLOR = "green"
CELL_TO_SURFACE_COLOR = "blue"

BBOX_GID = "bbox"
CONTOUR_GID = "contour"
NETWORK_NODE_GID = "node"
NETWORK_EDGE_GID = "edge"

class MplWidget(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self, parent)

        self.canvas = FigureCanvas(Figure(facecolor=BACKGROUND_COLOR))

        vertical_layout = QVBoxLayout()
        vertical_layout.setContentsMargins(0, 0, 0, 0)
        vertical_layout.addWidget(self.canvas)

        self.canvas.axes = self.canvas.figure.add_subplot(111)
        self.canvas.figure.tight_layout()
        self.setLayout(vertical_layout)
        self.canvas.axes.axis("off")

        self.current_gid = 0
        # cells have {"network_type": "node", "node_id": <their graph node id>}
        # edges have {"network_type": "edge", "edge_head": <first node of edge>, "edge_tail": <second node of edge>, "edge_key": <unique key for edge>}
        self.artist_data = {}

    def clear_canvas(self):
        self.canvas.axes.cla()
        self.canvas.axes.axis("off")
        self.canvas.draw()

    def return_artist_data(self, gid):
        return self.artist_data[gid]

    def draw_line(self, point1, point2, type=CELL_TO_CELL_EDGE):
        color = CELL_CONTACT_COLOR if type == CELL_CONTACT_EDGE else \
                CELL_TO_CELL_COLOR if type == CELL_TO_CELL_EDGE else \
                CELL_TO_SURFACE_COLOR
        line_obj = Line2D([point1[0], point2[0]], [point1[1], point2[1]], color=color, linestyle="dashed")
        self.canvas.axes.add_line(line_obj)
        self.canvas.draw()

        return line_obj

    def draw_image(self, image):
        self.canvas.axes.imshow(image, cmap="gray")
        self.canvas.draw()

    def draw_cell_bounding_boxes(self, bio_objects):
        for obj in bio_objects:
            if obj.is_surface():
                continue
            color = NANOWIRE_BBOX_COLOR if obj.is_nanowire() else CELL_BBOX_COLOR
            self.artist_data[str(self.current_gid)] = {"network_type": BBOX_GID}
            bbox = Rectangle((obj.x1, obj.y2), obj.x2 - obj.x1, obj.y1 - obj.y2, edgecolor=color, facecolor='none', linestyle="dashed", gid=str(self.current_gid))
            self.canvas.axes.add_patch(bbox)
            self.current_gid += 1

        self.canvas.draw()

    def draw_node(self, node_id, node_data):
        self.artist_data[str(self.current_gid)] = {"network_type": NETWORK_NODE_GID, "node_id": node_id}
        point_obj = Line2D([node_data['x']], [node_data['y']], color="red", marker="o", gid=str(self.current_gid))
        self.current_gid += 1
        point_obj.set_picker(True)
        self.canvas.axes.add_line(point_obj)
        self.canvas.draw()

        return point_obj

    def draw_edge(self, node1, node2, node1_data, node2_data, edge_key, edge_data):
        color = CELL_CONTACT_COLOR if edge_data["type"] == CELL_CONTACT_EDGE \
                else CELL_TO_CELL_COLOR if edge_data["type"] == CELL_TO_CELL_EDGE \
                else CELL_TO_SURFACE_COLOR
        edge_start = edge_data['surface_point'] if node1 == 0 else node1_data
        edge_end = edge_data['surface_point'] if node2 == 0 else node2_data
        self.artist_data[str(self.current_gid)] = {"network_type": NETWORK_EDGE_GID, "edge_head": node1, "edge_tail": node2, "edge_key": edge_key}
        line_obj = Line2D([edge_start['x'], edge_end['x']], [edge_start['y'], edge_end['y']], color=color, linestyle="dashed", gid=str(self.current_gid))
        line_obj.set_picker(True)
        self.current_gid += 1
        self.canvas.axes.add_line(line_obj)
        self.canvas.draw()

        return line_obj

    def draw_network_nodes(self, graph):
        for node_id, node_data in graph.nodes(data=True):
            if node_data['x'] == 0 and node_data['y'] == 0:
                continue
            self.draw_node(node_id, node_data)

    def draw_network_edges(self, graph):
        for node1,node2,edge_key,edge_data in graph.edges(data=True, keys=True):
            self.draw_edge(node1, node2, graph.nodes[node1], graph.nodes[node2], edge_key, edge_data)

    def remove_cell_bounding_boxes(self):
        for child in self.canvas.axes.get_children():
            if hasattr(child, "_gid") and child._gid is not None and self.artist_data[child._gid]["network_type"] == BBOX_GID:
                child.remove()
        self.canvas.draw()

    def remove_network_edges(self):
        for child in self.canvas.axes.get_children():
            if hasattr(child, "_gid") and child._gid is not None and self.artist_data[child._gid]["network_type"] == NETWORK_EDGE_GID:
                child.remove()
        self.canvas.draw()
