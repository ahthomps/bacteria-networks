from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QMessageBox, QInputDialog, QApplication, QDialog
from PyQt5.uic import loadUi
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

from PIL import Image
import numpy as np
import random
import matplotlib.pyplot as plt
import subprocess
import os

from image_processing import *
from contouring import compute_cell_contours
from classes import *
from make_labeled_crops import *
from edge_detection import compute_cell_contact


class ProgramManager:
    def __init__(self, display, MplWidget):
        self._display = display
        self._MplWidget = MplWidget

        self._image = np.asarray([])
        self._binary_image = np.asarray([])
        self._cells = []
        self._tiles = []

        self.openings = DEFAULT_OPENINGS
        self.dilations = DEFAULT_DILATIONS
        self.threshold = None # This is a hack and should be changed.

        self._image_filename = ""
        self._label_filename = ""
        self._crop_dir = ""

    def clear(self):
        self._image = np.asarray([])
        self._binary_image = np.asarray([])
        self._cells = []
        self._tiles = []

        self.openings = DEFAULT_OPENINGS
        self.dilations = DEFAULT_DILATIONS
        self.threshold = None # This is a hack and should be changed.

        self._image_filename = ""
        self._label_filename = ""
        self._crop_dir = ""

        self._display.clear()

    def get_image(self):
        filename, _ = QFileDialog.getOpenFileName(None, "Select image", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.tif)")
        if not filename:
            return

        print("using image {}".format(filename))
        self._image_filename = filename
        self._image = plt.imread(self._image_filename)

        # Maybe we should 0 pad if the image is too small, but I can do that later
        if self._image.shape[0] > TILE_SIZE or self._image.shape[1] > TILE_SIZE:
            self._display.image_success(crop=True)
        self._display.image_success()
        self._MplWidget.draw_image(self._image)

    def get_label(self):
        filename, _ = QFileDialog.getOpenFileName(None, "Select label", "", "Label Files (*.txt)")
        if not filename:
            return

        print("using label {}".format(filename))
        self._label_filename = filename
        self._label_ofile = open(self._label_filename)
        self._cells = parse_yolo_input(self._label_ofile, self._image)

        self._display.bbox_success()
        self._MplWidget.draw_cell_bounding_boxes(self._cells)

    def run_yolo(self):
        # There's major copy-pasted code in this function. Should probably be cleaned up.
        print("Running YOLO...")
        # Batch of crops
        if self._crop_dir != "":
            for filename in filter(lambda s: any(s.lower().endswith(ext) for ext in IMAGE_EXTENSIONS), os.listdir(self._crop_dir)):
                filename_no_ext = filename[:filename.rfind(".")]
                x1, y1 = map(int, filename_no_ext.split("_")[-2:])

                output = subprocess.run(["./darknet", "detector", "test", "cells/obj.data", "cells/test.cfg", "backup/yolov3-custom_final.weights",
                                         f"{self._crop_dir}/{filename}"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

                tile = Tile(Image.open(f"{self._crop_dir}/{filename}"), x1, y1, x1 + TILE_SIZE, y1 + TILE_SIZE, filename_no_ext)
                tile.cells = parse_yolo_output(str(output.stdout, "UTF-8"))
                self._tiles.append(tile)

                print(f"Processed {self._crop_dir}/{filename}.")
        # Single image
        elif self._image_filename != "":
            output = subprocess.run(["./darknet", "detector", "test", "cells/obj.data", "cells/test.cfg", "backup/yolov3-custom_final.weights",
                                     self._image_filename], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            self._cells = parse_yolo_output(str(output.stdout, "UTF-8"))
            self._display.bbox_success()
            self._MplWidget.draw_cell_bounding_boxes(self._cells)
        else:
            raise Exception("Didn't run YOLO for some reason.")
        print("Done!")

    def get_processed_image(self):
        print("progessing image...")
        self._binary_image, self.threshold = process_image(self._image, self.openings, self.dilations, self.threshold)
        print("found processed image!")
        self._display.processed_image_success()
        self._MplWidget.draw_image(self._binary_image)

    def get_contour(self):
        print("getting contours...")
        compute_cell_contours(self._binary_image, self._cells)
        print("found contours!")
        self._display.contour_success()
        self._MplWidget.remove_cell_bounding_boxes()
        self._MplWidget.draw_contours(self._cells)
        self._MplWidget.draw_image(self._image)

    def crop(self):
        assert self._image_filename is not None

        # Make the crops directory
        directory = self._image_filename[:self._image_filename.rfind("/")]
        self._crop_dir = f"{directory}/crops"
        os.makedirs(self._crop_dir, exist_ok=True)

        # Get a list of all the image files we're going to crop
        input_images = [self._image_filename[self._image_filename.rfind("/") + 1:]]

        # Crop each image, and save all the crops in self._crop_dir
        for filename in input_images:
            for tile in make_tiles(Image.open(f"{directory}/{filename}"), filename[:filename.rfind(".")]):
                tile.save(directory=self._crop_dir)

        self._display.crop_success()
        print("Made at most", len(os.listdir(self._crop_dir)), "crops.")

    def reunify(self):
        full_tile = reunify_tiles(self._tiles)
        full_tile.save()
        self._display.reunify_success()

    def get_edges(self):
        compute_cell_contact(self._cells)
        self._MplWidget.draw_network_edges(self._cells)

    def toggle_display(self, action):
        if action == 'bbox':
            if self._display.actionBounding_Boxes.isChecked():
                self._MplWidget.draw_cell_bounding_boxes(self._cells)
            else:
                self._MplWidget.remove_cell_bounding_boxes()
        elif action == 'contour':
            if self._display.actionContour_view.isChecked():
                self._MplWidget.draw_contours(self._cells)
            else:
                self._MplWidget.remove_contours()
        elif action == 'binary':
            if self._display.actionBinary_Image.isChecked():
                self._MplWidget.draw_image(self._binary_image)
            else:
                self._MplWidget.draw_image(self._image)
        elif action == 'customProcessing':
            self._display.show_custom_processing()

class DisplayManager(QMainWindow):
    def __init__(self):
        # set up UI window
        QMainWindow.__init__(self)
        loadUi("main.ui", self)
        self.setWindowTitle("JAB Bacteria Networks Detector")
        self.addToolBar(NavigationToolbar(self.MplWidget.canvas, self))

        # set up ProgramManager
        self._program_manager = ProgramManager(self, self.MplWidget)
        self.add_actions()
        self.initialize_enablements()

    def add_actions(self):
        self.actionClear.triggered.connect(self._program_manager.clear)
        self.actionCustom_Processing.triggered.connect(lambda: self._program_manager.toggle_display('customProcessing'))

        self.actionImage.triggered.connect(self._program_manager.get_image)
        self.actionLabel.triggered.connect(self._program_manager.get_label)
        self.actionYOLO.triggered.connect(self._program_manager.run_yolo)
        self.actionProcess_Image.triggered.connect(self._program_manager.get_processed_image)
        self.actionContour_run.triggered.connect(self._program_manager.get_contour)
        self.actionEdge_Detection.triggered.connect(self._program_manager.get_edges)

        self.actionCrop.triggered.connect(self._program_manager.crop)
        self.actionReunify.triggered.connect(self._program_manager.reunify)

        self.actionBinary_Image.triggered.connect(lambda : self._program_manager.toggle_display('binary'))
        self.actionBounding_Boxes.triggered.connect(lambda : self._program_manager.toggle_display('bbox'))
        self.actionContour_view.triggered.connect(lambda : self._program_manager.toggle_display('contour'))

    def initialize_enablements(self):
        self.actionSave.setEnabled(False)
        self.actionSave_As.setEnabled(False)
        self.actionClear.setEnabled(True)

        self.actionImage.setEnabled(True)
        # self.actionImage_Directory.setEnabled(True)
        self.actionImage_Directory.setEnabled(False)
        self.actionCustom_Processing.setEnabled(False)

        self.actionLabel.setEnabled(False)
        self.actionYOLO.setEnabled(False)
        self.actionProcess_Image.setEnabled(False)
        self.actionContour_run.setEnabled(False)
        self.actionEdge_Detection.setEnabled(False)

        self.actionCrop.setEnabled(False)
        self.actionReunify.setEnabled(False)

        self.actionBounding_Boxes.setEnabled(False)
        self.actionBounding_Boxes.setChecked(False)
        self.actionBinary_Image.setEnabled(False)
        self.actionBinary_Image.setChecked(False)
        self.actionContour_view.setEnabled(False)
        self.actionContour_view.setChecked(False)

    def show_custom_processing(self):
        self.sliders = SliderWidget(mgr=self._program_manager)
        self.sliders.setLayout(self.sliders.layout)
        self.sliders.show()

    def clear(self):
        self.MplWidget.canvas.axes.cla()
        self.MplWidget.canvas.axes.axis('off')
        self.MplWidget.canvas.draw()
        self.initialize_enablements()

    # display results of actions
    def image_success(self, crop=False):
        # enable cropping if required
        if crop:
            self.actionCrop.setEnabled(True)
        # disable importing new images
        self.actionImage.setEnabled(False)
        self.actionImage_Directory.setEnabled(False)
        # enable finding bboxes
        self.actionLabel.setEnabled(True)
        self.actionYOLO.setEnabled(True)

    def bbox_success(self):
        # disable finding bounding boxes
        self.actionLabel.setEnabled(False)
        self.actionYOLO.setEnabled(False)
        # enable toggling bbox display
        self.actionBounding_Boxes.setEnabled(True)
        self.actionBounding_Boxes.setChecked(True)
        # enable image processing
        self.actionProcess_Image.setEnabled(True)

    def processed_image_success(self):
        # disable image processing
        self.actionProcess_Image.setEnabled(False)
        # enable binary image viewing
        self.actionBinary_Image.setEnabled(True)
        self.actionBinary_Image.setChecked(True)
        # enable contouring
        self.actionContour_run.setEnabled(True)
        # enable image processing options
        self.actionCustom_Processing.setEnabled(True)

    def contour_success(self):
        # disable contouring
        self.actionContour_run.setEnabled(False)
        # enable contour viewing
        self.actionContour_view.setEnabled(True)
        self.actionContour_view.setChecked(True)
        # uncheck bounding boxes (don't want to view them)
        self.actionBounding_Boxes.setChecked(False)
        # uncheck binary image (want to see original)
        self.actionBinary_Image.setChecked(False)
        # enable edge detection
        self.actionEdge_Detection.setEnabled(True)

    def edge_detection_success(self):
        # disable edge detection
        self.actionEdge_Detection.setEnabled(False)
        # enable edges viewing

    def crop_success(self):
        # disable cropping
        self.actionCrop.setEnabled(False)
        # enable finding bboxes with YOLO
        self.actionYOLO.setEnabled(True)

    def reunify_success(self):
        # disable reunification
        self.actionReunify.setEnabled(False)


app = QApplication([])
window = DisplayManager()
window.show()
app.exec_()
