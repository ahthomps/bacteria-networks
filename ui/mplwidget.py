# ------------------------------------------------------
# -------------------- mplwidget.py --------------------
# ------------------------------------------------------
from PyQt5.QtWidgets import *
from matplotlib.backends.backend_qt5agg import FigureCanvas
from matplotlib.figure import Figure
from PyQt5 import QtCore

class MplWidget(QWidget):
    def __init__(self, parent = None):
        QWidget.__init__(self, parent)

        self.canvas = FigureCanvas(Figure())

        vertical_layout = QVBoxLayout()
        vertical_layout.setContentsMargins(0, 0, 0, 0)
        vertical_layout.addWidget(self.canvas)

        self.canvas.axes = self.canvas.figure.add_subplot(111)
        self.canvas.figure.tight_layout()
        self.setLayout(vertical_layout)
        self.canvas.axes.axis('off')

        self.bbox_gid = 'bbox'
        self.contour_gid = 'contour'

    def clear_canvas(self):
        self.canvas.axes.cla()
        self.canvas.axes.axis('off')
        self.canvas.draw()

    def draw_image(self, image):
        self.canvas.axes.imshow(image, cmap='gray')
        self.canvas.draw()

    def draw_cell_bounding_boxes(self, bio_objects):
        for obj in bio_objects:
            if obj.is_surface():
                continue
            color = "blue"
            if obj.is_nanowire():
                color = "yellow"
            self.canvas.axes.plot([obj.x1, obj.x2], [obj.y1, obj.y1], color=color, linestyle='dashed', marker='o', gid=self.bbox_gid)
            self.canvas.axes.plot([obj.x1, obj.x2], [obj.y2, obj.y2], color=color, linestyle='dashed', marker='o', gid=self.bbox_gid)
            self.canvas.axes.plot([obj.x1, obj.x1], [obj.y1, obj.y2], color=color, linestyle='dashed', marker='o', gid=self.bbox_gid)
            self.canvas.axes.plot([obj.x2, obj.x2], [obj.y1, obj.y2], color=color, linestyle='dashed', marker='o', gid=self.bbox_gid)
        self.canvas.draw()

    def draw_cell_contours(self, cells):
        colors = ['red', 'orange', 'yellow', 'green', 'blue', 'indigo', 'violet']
        count = 0
        for cell in cells:
            if not cell.has_contour():
                continue
            self.canvas.axes.plot(cell.cell_center[0], cell.cell_center[1], color='red', marker='o', gid=self.contour_gid)
            contour = cell.contour
            contour_set = self.canvas.axes.contour(contour, [0.75], colors=colors[count % len(colors)])
            count += 1
            for line_collection in contour_set.collections:
                line_collection.set_gid(self.contour_gid)
        self.canvas.draw()

    def draw_cell_network_edges(self, bio_objects):
        for obj in bio_objects:
            if not obj.is_cell():
                continue
            for edge in obj.edge_list:
                if (edge.head is not None) and (edge.tail.id <= edge.head.id):
                    continue
                elif edge.type_is_cell_to_surface():
                    if (edge.nanowire.x2 - edge.nanowire.x1) > (edge.nanowire.y2 - edge.nanowire.y1):
                        y_mid = (edge.nanowire.y2 + edge.nanowire.y1) // 2
                        self.canvas.axes.plot([edge.nanowire.x1, edge.nanowire.x2], [y_mid, y_mid], color="blue", marker='o', gid='edge')
                    else:
                        x_mid = (edge.nanowire.x2 + edge.nanowire.x1) // 2
                        self.canvas.axes.plot([x_mid, x_mid], [edge.nanowire.y1, edge.nanowire.y2], color="blue", marker='o', gid='edge')
                else:
                    (x1, y1) = obj.cell_center
                    (x2, y2) = edge.head.cell_center
                    if edge.type_is_cell_to_cell():
                        self.canvas.axes.plot([x1, x2], [y1, y2], color='green', linestyle="dashed", marker='o', gid='edge')
                    else:
                        self.canvas.axes.plot([x1, x2], [y1, y2], color='red', marker='o', gid='edge')
        self.canvas.draw()

        # for obj in bio_objects:
        #     if obj.is_nanowire() or obj.is_surface():
        #         continue
        #     cell = obj
        #     (x1, y1) = cell.cell_center
        #     for adj_cell in cell.adj_list:
        #         if adj_cell.id > cell.id:
        #             (x2, y2) = adj_cell.cell_center
        #             self.canvas.axes.plot([x1, x2], [y1, y2], color='red', marker='o', gid='edge')
        # self.canvas.draw()

    def remove_cell_bounding_boxes(self):
        for child in self.canvas.axes.get_children():
            if hasattr(child, '_gid') and child._gid == self.bbox_gid:
                child.remove()
        self.canvas.draw()

    def remove_cell_contours(self):
        for child in self.canvas.axes.get_children():
            if hasattr(child, '_gid') and child._gid == self.contour_gid:
                child.remove()
        self.canvas.draw()
