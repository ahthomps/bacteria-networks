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
from classes import Tile
from make_labeled_crops import *
from edge_detection import compute_cell_contact

CROP_SIZE = 416

class ProgramManager:
    def __init__(self):
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

    def clear_data(self):
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

    def open_image_file(self):
        filename, _ = QFileDialog.getOpenFileName(None, "Select image", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.tif)")
        if not filename:
            return False

        print("using image {}".format(filename))
        self._image_filename = filename
        self._image = plt.imread(self._image_filename)
        return True

    def open_label_file(self):
        filename, _ = QFileDialog.getOpenFileName(None, "Select label", "", "Label Files (*.txt)")
        if not filename:
            return False

        print("using label {}".format(filename))
        self._label_filename = filename
        self._label_ofile = open(self._label_filename)
        self._cells = parse_yolo_input(self._label_ofile, self._image)
        return True

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
            # self._display.bbox_success()
            # self._MplWidget.draw_cell_bounding_boxes(self._cells)
        else:
            raise Exception("Didn't run YOLO for some reason.")
        print("Done!")

    def compute_binary_image(self):
        print("progessing image...")
        self._binary_image, self.threshold = process_image(self._image, self.openings, self.dilations, self.threshold)
        print("found processed image!")

    def compute_cell_contours(self):
        print("getting contours...")
        compute_cell_contours(self._binary_image, self._cells)
        print("found contours!")

    def crop(self):
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

        print("Made at most", len(os.listdir(self._crop_dir)), "crops.")

    def reunify(self):
        full_tile = reunify_tiles(self._tiles)
        self._image = np.array(full_tile.img)
        self._cells = full_tile.cells
        return full_tile

    def compute_cell_network_edges(self):
        compute_cell_contact(self._cells)


class MainWindow(QMainWindow):
    def __init__(self):
        # set up UI window
        QMainWindow.__init__(self)
        loadUi("main.ui", self)
        self.setWindowTitle("JAB Bacteria Networks Detector")
        self.addToolBar(NavigationToolbar(self.MplWidget.canvas, self))

        # set up ProgramManager
        self._program_manager = ProgramManager()
        self.set_default_enablements()

        # set up all button presses
        self.actionClear.triggered.connect(self.clear_all_data_and_reset_window)
        self.actionCustom_Processing.triggered.connect(self.create_binary_image_processing_window_and_display)

        self.actionImage.triggered.connect(self.open_image_file_and_display)
        self.actionLabel.triggered.connect(self.open_label_file_and_display)
        self.actionYOLO.triggered.connect(self.run_yolo_and_display)
        self.actionProcess_Image.triggered.connect(self.compute_binary_image_and_display)
        self.actionContour_run.triggered.connect(self.compute_cell_contours_and_display)
        self.actionEdge_Detection.triggered.connect(self.compute_cell_network_edges_and_display)

        self.actionCrop.triggered.connect(self.compute_image_crops_and_change_enablements)
        self.actionReunify.triggered.connect(self.compute_reunified_image_and_change_enablements)

        self.actionBinary_Image.triggered.connect(self.handle_binary_image_view_press)
        self.actionBounding_Boxes.triggered.connect(self.handle_cell_bounding_boxes_view_press)
        self.actionContour_view.triggered.connect(self.handle_cell_contours_view_press)

    def set_default_enablements(self):
        self.actionSave.setEnabled(False)
        self.actionSave_As.setEnabled(False)
        self.actionClear.setEnabled(True)

        self.actionImage.setEnabled(True)

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

    def clear_all_data_and_reset_window(self):
        self._program_manager.clear_data()
        self.MplWidget.clear_canvas()
        self.set_default_enablements()

    def open_image_file_and_display(self):
        image_file_was_opened = self._program_manager.open_image_file()
        if not image_file_was_opened:
            return
        self.MplWidget.draw_image(self._program_manager._image)

        if any(dim > CROP_SIZE for dim in self._program_manager._image.shape):
            self.actionCrop.setEnabled(True)

        # disable importing new images
        self.actionImage.setEnabled(False)
        self.actionImage_Directory.setEnabled(False)
        # enable finding bboxes
        self.actionLabel.setEnabled(True)
        self.actionYOLO.setEnabled(True)

    def open_label_file_and_display(self):
        label_file_was_opened = self._program_manager.open_label_file()
        if not label_file_was_opened:
            return
        self.MplWidget.draw_cell_bounding_boxes(self._program_manager._cells)

        # disable finding bounding boxes
        self.actionLabel.setEnabled(False)
        self.actionYOLO.setEnabled(False)
        # enable toggling bbox display
        self.actionBounding_Boxes.setEnabled(True)
        self.actionBounding_Boxes.setChecked(True)
        # enable image processing
        self.actionProcess_Image.setEnabled(True)

    def run_yolo_and_display(self):
        self._program_manager.run_yolo()
        self.MplWidget.draw_cell_bounding_boxes(self._program_manager._cells) # This does nothing when we run YOLO on crops

        # disable finding bounding boxes
        self.actionLabel.setEnabled(False)
        self.actionYOLO.setEnabled(False)
        # enable toggling bbox display
        self.actionBounding_Boxes.setEnabled(True)
        self.actionBounding_Boxes.setChecked(True)
        # enable image processing
        self.actionProcess_Image.setEnabled(True)

    def compute_binary_image_and_display(self):
        self._program_manager.compute_binary_image()
        self.MplWidget.draw_image(self._program_manager._binary_image)

        # disable image processing
        self.actionProcess_Image.setEnabled(False)
        # enable binary image viewing
        self.actionBinary_Image.setEnabled(True)
        self.actionBinary_Image.setChecked(True)
        # enable contouring
        self.actionContour_run.setEnabled(True)
        # enable image processing options
        self.actionCustom_Processing.setEnabled(True)

    def create_binary_image_processing_window_and_display(self):
        self.sliders = SliderWidget(mgr=self._program_manager)
        self.sliders.setLayout(self.sliders.layout)
        self.sliders.show()

    def compute_cell_contours_and_display(self):
        self._program_manager.compute_cell_contours()
        self.MplWidget.remove_cell_bounding_boxes()
        self.MplWidget.draw_cell_contours(self._program_manager._cells)
        self.MplWidget.draw_image(self._program_manager._image)

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

    def compute_cell_network_edges_and_display(self):
        self._program_manager.compute_cell_network_edges()
        self.MplWidget.draw_cell_network_edges(self._program_manager._cells)

        # disable edge detection
        self.actionEdge_Detection.setEnabled(False)
        # enable edges viewing

    def compute_image_crops_and_change_enablements(self):
        self._program_manager.crop()

        # disable cropping
        self.actionCrop.setEnabled(False)
        # enable finding bboxes with YOLO
        self.actionYOLO.setEnabled(True)
        # enable reunification of the crops
        self.actionReunify.setEnabled(True)

    def compute_reunified_image_and_change_enablements(self):
        full_tile = self._program_manager.reunify()

        self.MplWidget.draw_image(self._program_manager._image)
        self.MplWidget.draw_cell_bounding_boxes(full_tile.cells)

        # disable reunification
        self.actionReunify.setEnabled(False)

    def handle_binary_image_view_press(self):
        if self.actionBinary_Image.isChecked():
            self.MplWidget.draw_image(self._program_manager._binary_image)
        else:
            self.MplWidget.draw_image(self._program_manager._image)

    def handle_cell_bounding_boxes_view_press(self):
        if self.actionBounding_Boxes.isChecked():
            self.MplWidget.draw_cell_bounding_boxes(self._program_manager._cells)
        else:
            self.MplWidget.remove_cell_bounding_boxes()

    def handle_cell_contours_view_press(self):
        if self.actionContour_view.isChecked():
            self.MplWidget.draw_cell_contours(self._program_manager._cells)
        else:
            self.MplWidget.remove_cell_contours()


app = QApplication([])
window = MainWindow()
window.show()
app.exec_()
