from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QMessageBox, QInputDialog, QApplication, QDialog
from PyQt5.uic import loadUi
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

from contouring import *
from classes import *
from make_labeled_crops import *
from PIL import Image

import numpy as np
import random
import matplotlib.pyplot as plt
import subprocess
import os

class ProgramManager(QMainWindow):
    def __init__(self):
        self._image = np.asarray([])
        self._binary_image = np.asarray([])
        self._bboxes = []
        self._contours = []

        self._image_filename = ""
        self._label_filename = ""
        self._image_dir = ""
        self._label_ofile = None

        self._crop_dir = ""
        self._tiles = []

        self._plot_show_binary = False
        self._plot_show_bounding_boxes = False
        self._plot_show_contour = False

        # Maps crop names to bounding box lists
        self._crop_boxes = {}

        QMainWindow.__init__(self)
        loadUi("main.ui", self)
        self.setWindowTitle("JAB Bacteria Networks Detector")
        self.addToolBar(NavigationToolbar(self.MplWidget.canvas, self))
        self.actions()

        # deactivate buttons that shouldn't be used yet
        self.reset_data()

    def actions(self):
        # actions in the toolbar FILE
        self.actionImage.triggered.connect(self.get_image)
        self.actionLabel.triggered.connect(self.get_label)
        self.actionImage_Directory.triggered.connect(self.get_image_directory)
        self.actionReunify.triggered.connect(self.reunify)

        # actions in the toolbar EDIT
        self.actionClear.triggered.connect(self.reset_data)

        # actions in the toolbar VIEW
        self.actionBounding_Boxes.triggered.connect(self.display_bounding_boxes)
        self.actionContour_view.triggered.connect(self.display_contour)
        self.actionBinary_Image.triggered.connect(self.display_binary)

        # actions in the toolbar RUN
        self.actionYOLO.triggered.connect(self.run_yolo)
        self.actionContour_run.triggered.connect(self.get_contour)
        self.actionCrop.triggered.connect(self.crop)

    def display(self):
        colors = ['red', 'orange', 'yellow', 'green', 'blue', 'indigo', 'violet']
        self.MplWidget.canvas.axes.cla()
        self.MplWidget.canvas.axes.axis('off')
        if not self._plot_show_binary and self._image_filename:
            self.MplWidget.canvas.axes.imshow(self._image, cmap=plt.cm.gray)
        elif self._plot_show_binary:
            self.MplWidget.canvas.axes.imshow(self._binary_image, cmap=plt.cm.gray)
        if self._plot_show_bounding_boxes:
            for box in self._bboxes:
                self.MplWidget.canvas.axes.plot([box.x1, box.x2], [box.y1, box.y1], color='blue', linestyle='dashed', marker='o')
                self.MplWidget.canvas.axes.plot([box.x1, box.x2], [box.y2, box.y2], color='blue', linestyle='dashed', marker='o')
                self.MplWidget.canvas.axes.plot([box.x1, box.x1], [box.y1, box.y2], color='blue', linestyle='dashed', marker='o')
                self.MplWidget.canvas.axes.plot([box.x2, box.x2], [box.y1, box.y2], color='blue', linestyle='dashed', marker='o')

        if self._plot_show_contour:
            count = 0
            for contour in self._contours:
                self.MplWidget.canvas.axes.contour(contour, [0.75], colors=colors[count % len(colors)])
                count += 1

        self.MplWidget.canvas.draw()

    def reset_data(self):
        self._image = np.asarray([])
        self._binary_image = np.asarray([])
        self._contours = []
        self._bboxes = []

        self._image_filename = ""
        self._label_filename = ""
        self._image_dir = ""
        self._crop_dir = ""
        self._label_ofile = None

        self._plot_show_binary = False
        self._plot_show_bounding_boxes = False
        self._plot_show_contour = False

        # This will need to change. I'm doing this for testing only
        self.actionReunify.setEnabled(True)

        self.actionImage.setEnabled(True)
        self.actionImage_Directory.setEnabled(True)

        self.actionLabel.setEnabled(False)

        self.actionYOLO.setEnabled(False)
        self.actionCrop.setEnabled(False)
        self.actionContour_run.setEnabled(False)

        self.actionBinary_Image.setEnabled(False)
        self.actionBounding_Boxes.setEnabled(False)
        self.actionContour_view.setEnabled(False)

        self._crop_boxes = {}
        self._tiles = []

        self.display()

    def get_image(self):
        filename, _ = QFileDialog.getOpenFileName(None, "Select image", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.tif)")
        if not filename:
            return

        print("using image {}".format(filename))
        self._image_filename = filename
        self._image = plt.imread(self._image_filename)

        # Maybe we should 0 pad if the image is too small, but I can do that later
        if self._image.shape[0] > TILE_SIZE or self._image.shape[1] > TILE_SIZE:
            self.actionCrop.setEnabled(True)

        self.actionLabel.setEnabled(True)
        self.actionYOLO.setEnabled(True)
        self.actionImage.setEnabled(False)
        self.actionImage_Directory.setEnabled(False)
        self.display()

    def get_label(self):
        filename, _ = QFileDialog.getOpenFileName(None, "Select label", "", "Label Files (*.txt)")
        if not filename:
            return

        print("using label {}".format(filename))
        self._label_filename = filename
        self._label_ofile = open(self._label_filename)
        self._bboxes = parse_yolo_input(self._label_ofile)
        for box in self._bboxes:
            box.to_px(len(self._image[0]), len(self._image))
        self._label_ofile = open(self._label_filename)

        self.actionBounding_Boxes.setEnabled(True)
        self.actionLabel.setEnabled(False)
        self.actionContour_run.setEnabled(True)
        self.actionYOLO.setEnabled(False)

        self.actionBounding_Boxes.setChecked(True)
        self.display_bounding_boxes()

    def get_image_directory(self):
        directory = QFileDialog.getExistingDirectory(None, 'Select an image directory', '.', QFileDialog.ShowDirsOnly)
        if not directory:
            return

        self._image_dir = directory
        self.actionImage.setEnabled(False)
        self.actionImage_Directory.setEnabled(False)
        self.actionCrop.setEnabled(True)

    def display_bounding_boxes(self):
        self._plot_show_bounding_boxes = self.actionBounding_Boxes.isChecked()
        self.display()

    def display_contour(self):
        self._plot_show_contour = self.actionContour_view.isChecked()
        self.display()

    def display_binary(self):
        self._plot_show_binary = self.actionBinary_Image.isChecked()
        self.display()

    def get_contour(self):
        print("getting contours...")
        self._binary_image = process_image(self._image)
        self._contours = contour(self._binary_image, self._bboxes)
        print("found contours!")
        self.actionContour_view.setChecked(True)
        self.actionBounding_Boxes.setChecked(True)
        self._plot_show_contour = True
        self._plot_show_bounding_boxes = False
        self.actionBounding_Boxes.setChecked(False)

        self.actionContour_run.setEnabled(False)
        self.actionContour_view.setEnabled(True)
        self.actionBinary_Image.setEnabled(True)

        self.display()

    def run_yolo(self):
        # There's major copy-pasted code in this function. Should probably be cleaned up.
        print("Running YOLO...")

        # Batch of crops
        if self._crop_dir != "":
            self.actionYOLO.setEnabled(False)
            for filename in filter(lambda s: any(s.lower().endswith(ext) for ext in IMAGE_EXTENSIONS), os.listdir(self._crop_dir)):
                filename_no_ext = filename[:filename.rfind(".")]
                x1, y1 = map(int, filename_no_ext.split("_")[-2:])

                output = subprocess.run(["./darknet", "detector", "test", "cells/obj.data", "cells/test.cfg", "backup/yolov3-custom_final.weights",
                                         f"{self._crop_dir}/{filename}"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

                tile = Tile(Image.open(f"{self._crop_dir}/{filename}"), x1, y1, x1 + TILE_SIZE, y1 + TILE_SIZE, filename_no_ext)
                tile.bounding_boxes = parse_yolo_output(str(output.stdout, "UTF-8"))
                self._tiles.append(tile)

                print(f"Processed {self._crop_dir}/{filename}.")
        # Single image
        elif self._image_filename != "":
            self.actionLabel.setEnabled(False)
            self.actionYOLO.setEnabled(False)

            output = subprocess.run(["./darknet", "detector", "test", "cells/obj.data", "cells/test.cfg", "backup/yolov3-custom_final.weights",
                                     self._image_filename], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            self._bboxes = parse_yolo_output(str(output.stdout, "UTF-8"))

            self.actionBounding_Boxes.setEnabled(True)
            self.actionContour_run.setEnabled(True)
            self.actionBounding_Boxes.setChecked(True)

            self.display_bounding_boxes()
        else:
            print("Didn't run YOLO for some reason.")
        print("Done!")

    def crop(self):
        assert self._image_filename is not None or self._image_dir != ""

        # Make the crops directory
        directory = self._image_dir or self._image_filename[:self._image_filename.rfind("/")]
        self._crop_dir = f"{directory}/crops"
        os.makedirs(self._crop_dir, exist_ok=True)

        # Get a list of all the image files we're going to crop
        if self._image_filename:
            input_images = [self._image_filename[self._image_filename.rfind("/") + 1:]]
        else:
            input_images = filter(lambda s: any(s.lower().endswith(ext) for ext in IMAGE_EXTENSIONS),
                                  os.listdir(self._image_dir))

        # Crop each image, and save all the crops in self._crop_dir
        for filename in input_images:
            for tile in make_tiles(Image.open(f"{directory}/{filename}"), filename[:filename.rfind(".")]):
                tile.save(directory=self._crop_dir)

        self.actionYOLO.setEnabled(True)
        self.actionCrop.setEnabled(False)
        print("Made at most", len(os.listdir(self._crop_dir)), "crops.")

    def reunify(self):
        full_tile = reunify_tiles(self._tiles)
        full_tile.save()

app = QApplication([])
window = ProgramManager()
window.show()
app.exec_()
