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

    def draw_cell_bounding_boxes(self, cells):
        for cell in cells:
            self.canvas.axes.plot([cell.x1, cell.x2], [cell.y1, cell.y1], color='blue', linestyle='dashed', marker='o', gid=self.bbox_gid)
            self.canvas.axes.plot([cell.x1, cell.x2], [cell.y2, cell.y2], color='blue', linestyle='dashed', marker='o', gid=self.bbox_gid)
            self.canvas.axes.plot([cell.x1, cell.x1], [cell.y1, cell.y2], color='blue', linestyle='dashed', marker='o', gid=self.bbox_gid)
            self.canvas.axes.plot([cell.x2, cell.x2], [cell.y1, cell.y2], color='blue', linestyle='dashed', marker='o', gid=self.bbox_gid)
        self.canvas.draw()

    def draw_cell_contours(self, cells):
        colors = ['red', 'orange', 'yellow', 'green', 'blue', 'indigo', 'violet']
        count = 0
        for cell in cells:
            self.canvas.axes.plot(cell._cell_center[0], cell._cell_center[1], color='red', marker='o', gid=self.contour_gid)
            contour = cell._contour
            contour_set = self.canvas.axes.contour(contour, [0.75], colors=colors[count % len(colors)])
            count += 1
            for line_collection in contour_set.collections:
                line_collection.set_gid(self.contour_gid)
        self.canvas.draw()

    def draw_cell_network_edges(self, cells):
        for cell in cells:
            (x1, y1) = cell._cell_center
            for adj_cell in cell._adj_list:
                if adj_cell.id > cell.id:
                    (x2, y2) = adj_cell._cell_center
                    self.canvas.axes.plot([x1, x2], [y1, y2], color='red', marker='o', gid='edge')
        self.canvas.draw()

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
