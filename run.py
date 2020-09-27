from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QMessageBox, QInputDialog, QApplication, QDialog
from PyQt5.uic import loadUi
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from cell_overlap_detection import *
import numpy as np
import random
import matplotlib.pyplot as plt
import subprocess

IMAGE_SIZE = 416

class ProgramManager(QMainWindow):
    def __init__(self):
        self._image = np.asarray([])
        self._image_binary = np.asarray([])
        self._bounding_boxes = []
        self._contours = []

        self._image_filename = ""
        self._label_filename = ""
        self._label_ofile = None

        self._plot_show_binary = False
        self._plot_show_bounding_boxes = False
        self._plot_show_contour = False

        QMainWindow.__init__(self)
        loadUi("main.ui", self)
        self.setWindowTitle("JAB Bacteria Networks Detector")
        self.addToolBar(NavigationToolbar(self.MplWidget.canvas, self))
        self.actions()

        # deactivate buttons that shouldn't be used yet
        self.resetData()

    def actions(self):
        # actions in the toolbar FILE
        self.actionImage.triggered.connect(self.getImage)
        self.actionLabel.triggered.connect(self.getLabel)

        # actions in the toolbar EDIT
        self.actionClear.triggered.connect(self.resetData)

        # actions in the toolbar VIEW
        self.actionBounding_Boxes.triggered.connect(self.displayBoundingBoxes)
        self.actionContour_view.triggered.connect(self.displayContour)
        self.actionBinary_Image.triggered.connect(self.displayBinary)

        # actions in the toolbar RUN
        self.actionYOLO.triggered.connect(self.runYolo)
        self.actionContour_run.triggered.connect(self.getContour)

    def display(self):
        self.MplWidget.canvas.axes.cla()
        self.MplWidget.canvas.axes.axis('off')
        if not self._plot_show_binary and self._image_filename:
            self.MplWidget.canvas.axes.imshow(self._image, cmap=plt.cm.gray)
        elif self._plot_show_binary:
            self.MplWidget.canvas.axes.imshow(self._image_binary, cmap=plt.cm.gray)
        if self._plot_show_bounding_boxes:
            for box in self._bounding_boxes:
                self.MplWidget.canvas.axes.plot(box[:, 0], box[:, 1], '--b', lw=3)
        if self._plot_show_contour:
            colors = ['b', 'g', 'r']
            count = 0
            for contour in self._contours:
                self.MplWidget.canvas.axes.contour(contour, [0.75], colors=colors[count % len(colors)])
                count += 1

        self.MplWidget.canvas.draw()

    def resetData(self):
        self._image = np.asarray([])
        self._image_binary = np.asarray([])
        self._bounding_boxes = []
        self._contours = []

        self._image_filename = ""
        self._label_filename = ""
        self._label_ofile = None

        self._plot_show_binary = False
        self._plot_show_bounding_boxes = False
        self._plot_show_contour = False

        self.actionImage.setEnabled(True)
        self.actionYOLO.setEnabled(False)
        self.actionLabel.setEnabled(False)
        self.actionBinary_Image.setEnabled(False)
        self.actionBounding_Boxes.setEnabled(False)
        self.actionContour_view.setEnabled(False)
        self.actionContour_run.setEnabled(False)

        self.display()

    def getImage(self):
        filename, _ = QFileDialog.getOpenFileName(None, "Select Image", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.tif)")
        if filename:
            print("using image {}".format(filename))
            self._image_filename = filename
            self._image = plt.imread(self._image_filename)

            self.actionLabel.setEnabled(True)
            self.actionYOLO.setEnabled(True)
            self.actionImage.setEnabled(False)
            self.display()

    def getLabel(self):
        filename, _ = QFileDialog.getOpenFileName(None, "Select Label", "", "Label Files (*.txt)")
        if filename:
            print("using label {}".format(filename))
            self._label_filename = filename
            self._label_ofile = open(self._label_filename)
            self._bounding_boxes, _, _ = get_bounding_boxes(self._image, self._label_ofile)
            self._label_ofile = open(self._label_filename)

            self.actionBounding_Boxes.setEnabled(True)
            self.actionLabel.setEnabled(False)
            self.actionContour_run.setEnabled(True)
            self.actionYOLO.setEnabled(False)

            self.actionBounding_Boxes.setChecked(True)
            self.displayBoundingBoxes()

    def displayBoundingBoxes(self):
        self._plot_show_bounding_boxes = self.actionBounding_Boxes.isChecked()
        self.display()

    def displayContour(self):
        self._plot_show_contour = self.actionContour_view.isChecked()
        self.display()

    def displayBinary(self):
        self._plot_show_binary = self.actionBinary_Image.isChecked()
        self.display()

    def getContour(self):
        print("getting contours....")
        self._image_binary, self._contours = get_contours(self._image, self._label_ofile)
        print("found contours!")
        self.actionContour_view.setChecked(True)
        self.actionBounding_Boxes.setChecked(True)
        self._plot_show_contour = True
        self._plot_show_bounding_boxes = True

        self.actionContour_run.setEnabled(False)
        self.actionContour_view.setEnabled(True)
        self.actionBinary_Image.setEnabled(True)

        self.display()

    def runYolo(self):
        self.actionLabel.setEnabled(False)
        self.actionYOLO.setEnabled(False)

        output = subprocess.run(["./darknet", "detector", "test", "cells/obj.data", "cells/yolov3-custom.cfg", "backup/yolov3-custom_final.weights",
                                 self._image_filename, "2>/dev/null"], stdout=subprocess.PIPE)

        self._bounding_boxes, _, _ = get_bounding_boxes(self._image, yolo_output=str(output.stdout, "UTF-8"))

        self.actionBounding_Boxes.setEnabled(True)
        self.actionContour_run.setEnabled(True)
        self.actionBounding_Boxes.setChecked(True)

        self.displayBoundingBoxes()



app = QApplication([])
window = ProgramManager()
window.show()
app.exec_()
