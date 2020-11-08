# ------------------------------------------------------
# -------------------- mplwidget.py --------------------
# ------------------------------------------------------
from PyQt5.QtWidgets import *
from matplotlib.backends.backend_qt5agg import FigureCanvas
from matplotlib.figure import Figure
from PyQt5 import QtCore

BACKGROUND_COLOR = "#EFEFEF"
CONTOUR_COLORS = ["red", "orange", "yellow", "green", "blue", "indigo", "violet"]
NANOWIRE_BBOX_COLOR = "yellow"
CELL_BBOX_COLOR = "blue"

BBOX_GID = "bbox"
CONTOUR_GID = "contour"
CELL_CENTER_GID = "cell_center"
NETWORK_EDGE = "edge"

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

    def clear_canvas(self):
        self.canvas.axes.cla()
        self.canvas.axes.axis("off")
        self.canvas.draw()

    def draw_image(self, image):
        self.canvas.axes.imshow(image, cmap="gray")
        self.canvas.draw()

    def draw_cell_bounding_boxes(self, bio_objects):
        for obj in bio_objects:
            if obj.is_surface():
                continue
            color = NANOWIRE_BBOX_COLOR if obj.is_nanowire() else CELL_BBOX_COLOR

            self.canvas.axes.plot([obj.x1, obj.x2], [obj.y1, obj.y1], color=color, linestyle="dashed", marker="o", gid=BBOX_GID)
            self.canvas.axes.plot([obj.x1, obj.x2], [obj.y2, obj.y2], color=color, linestyle="dashed", marker="o", gid=BBOX_GID)
            self.canvas.axes.plot([obj.x1, obj.x1], [obj.y1, obj.y2], color=color, linestyle="dashed", marker="o", gid=BBOX_GID)
            self.canvas.axes.plot([obj.x2, obj.x2], [obj.y1, obj.y2], color=color, linestyle="dashed", marker="o", gid=BBOX_GID)
        self.canvas.draw()

    def draw_point(self, x, y):
        self.canvas.axes.plot(x, y, color="red", marker="o", gid=CELL_CENTER_GID)

    def draw_cell_centers(self, bio_objects):
        for obj in bio_objects:
            if obj.is_cell():
                self.draw_point(obj.cell_center[0], obj.cell_center[1])

    def draw_cell_contours(self, cells):
        count = 0
        for cell in cells:
            if not cell.has_contour():
                continue

            self.canvas.axes.plot(cell.cell_center[0], cell.cell_center[1], color="red", marker="o", gid=CONTOUR_GID)
            contour = cell.contour
            contour_set = self.canvas.axes.contour(contour, [0.75], colors=CONTOUR_COLORS[count % len(CONTOUR_COLORS)])
            count += 1
            for line_collection in contour_set.collections:
                line_collection.set_gid(CONTOUR_GID)
        self.canvas.draw()

    def draw_network_edges(self, bio_objects):
        for obj in bio_objects:
            if not obj.is_cell():
                continue
            for edge in obj.edge_list:
                if edge.head is not None and edge.tail.id <= edge.head.id:
                    continue
                elif edge.type_is_cell_to_surface():
                    if edge.nanowire.x2 - edge.nanowire.x1 > edge.nanowire.y2 - edge.nanowire.y1:
                        y_mid = (edge.nanowire.y2 + edge.nanowire.y1) // 2
                        self.canvas.axes.plot([edge.nanowire.x1, edge.nanowire.x2], [y_mid, y_mid], color="blue", marker="o", gid=NETWORK_EDGE)
                    else:
                        x_mid = (edge.nanowire.x2 + edge.nanowire.x1) // 2
                        self.canvas.axes.plot([x_mid, x_mid], [edge.nanowire.y1, edge.nanowire.y2], color="blue", marker="o", gid=NETWORK_EDGE)
                else:
                    x1, y1 = obj.cell_center
                    x2, y2 = edge.head.cell_center
                    plot_kwargs = {"color": "green", "linestyle": "dashed", "marker": "o", "gid": NETWORK_EDGE} if edge.type_is_cell_to_cell() \
                             else {"color": "red", "marker": "o", "gid": NETWORK_EDGE}

                    self.canvas.axes.plot([x1, x2], [y1, y2], **plot_kwargs)

        self.canvas.draw()

    def remove_cell_bounding_boxes(self):
        for child in self.canvas.axes.get_children():
            if hasattr(child, "_gid") and child._gid == BBOX_GID:
                child.remove()
        self.canvas.draw()

    def remove_cell_contours(self):
        for child in self.canvas.axes.get_children():
            if hasattr(child, "_gid") and child._gid == CONTOUR_GID:
                child.remove()
        self.canvas.draw()

    def remove_network_edges(self):
        for child in self.canvas.axes.get_children():
            if hasattr(child, "_gid") and child._gid == NETWORK_EDGE:
                child.remove()
        self.canvas.draw()
