from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QMessageBox, QInputDialog, QApplication, QDialog
from PyQt5.uic import loadUi
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

from contouring import *
from classes import *
from make_labeled_crops import *
from sliderwidget import *
from edge_detection import cell_overlaps
from PIL import Image

import numpy as np
import random
import matplotlib.pyplot as plt
import subprocess
import os


class ProgramManager():
    def __init__(self, display):
        self._display = display

        self._image = np.asarray([])
        self._binary_image = np.asarray([])
        self._bboxes = []
        self._cells = []
        self._contours = []
        self._tiles = []
        self._crop_boxes = {}

        self._image_filename = ""
        self._label_filename = ""
        self._image_dir = ""
        self._crop_dir = ""
        
        self.threshold = None
        self.openings = 7
        self.initial_dialations = 4

    def clear(self, display):
        self._image = np.asarray([])
        self._binary_image = np.asarray([])
        self._bboxes = []
        self._contours = []
        self._tiles = []
        self._crop_boxes = {}

        self._image_filename = ""
        self._label_filename = ""
        self._image_dir = ""
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
        self._display.add_image(self._image)

    def get_image_directory(self):
        directory = QFileDialog.getExistingDirectory(None, 'Select an image directory', '.', QFileDialog.ShowDirsOnly)
        if not directory:
            return

        self._image_dir = directory
        self._display.image_success()

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

        self._display.bbox_success()
        self._display.add_bboxes(self._bboxes)

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
                tile.bounding_boxes = parse_yolo_output(str(output.stdout, "UTF-8"))
                self._tiles.append(tile)

                print(f"Processed {self._crop_dir}/{filename}.")
        # Single image
        elif self._image_filename != "":
            output = subprocess.run(["./darknet", "detector", "test", "cells/obj.data", "cells/test.cfg", "backup/yolov3-custom_final.weights",
                                     self._image_filename], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            self._bboxes = parse_yolo_output(str(output.stdout, "UTF-8"))
            self._display.bbox_success()
            self._display.add_bboxes(self._bboxes)
        else:
            print("Didn't run YOLO for some reason.")
        print("Done!")

    def get_processed_image(self):
        print("progessing image...")
        self._binary_image = process_image(self._image, self.threshold, self.openings, self.initial_dialations)
        print("found processed image!")
        self._display.processed_image_success()
        self.toggle_display('binary')

    def get_contour(self):
        print("getting contours...")
        self._contours = contour(self._binary_image, self._bboxes)
        print("found contours!")
        self._display.contour_success()
        self._display.delete('bbox')
        self._display.add_contours(self._contours)
        self.toggle_display('binary')

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

        self._display.crop_success()
        print("Made at most", len(os.listdir(self._crop_dir)), "crops.")

    def reunify(self):
        full_tile = reunify_tiles(self._tiles)
        full_tile.save()
        self._display.reunify_success()

    def get_edges(self):
        self._cells = initialize_cell_objects(self._binary_image, self._bboxes, self._contours)
        cell_overlaps(self._cells)
        for cell in self._cells:
            print(cell._adj_list)
        self._display.add_edges(self._cells)


    def toggle_display(self, action):
        if action == 'bbox':
            if self._display.actionBounding_Boxes.isChecked():
                self._display.add_bboxes(self._bboxes)
            else:
                self._display.delete(action)
        elif action == 'contour':
            if self._display.actionContour_view.isChecked():
                self._display.add_contours(self._contours)
            else:
                self._display.delete(action)
        elif action == 'binary':
            if self._display.actionBinary_Image.isChecked():
                self._display.add_image(self._binary_image)
            else:
                self._display.add_image(self._image)
        elif action == 'customProcessing':
            self._display.show_custom_processing()

    def set_openings(self, num):
        self.openings = num

    def set_dialations(self, num):
        self.initial_dialations = num

    def set_threshold(self, num):
        self.threshold = num

    def updateBinary(self):
        print('updating')
        self._binary_image = process_image(self._image, self.threshold, self.openings, self.initial_dialations)
        self._display.actionBinary_Image.setChecked(True)
        self.toggle_display('binary')

class DisplayManager(QMainWindow):
    def __init__(self):
        # set up UI window
        QMainWindow.__init__(self)
        loadUi("main.ui", self)
        self.setWindowTitle("JAB Bacteria Networks Detector")
        self.addToolBar(NavigationToolbar(self.MplWidget.canvas, self))

        # set up ProgramManager
        self._program_manager = ProgramManager(self)
        self.add_actions()
        self.initialize_enablements()

    def add_actions(self):
        self.actionClear.triggered.connect(self._program_manager.clear)
        self.actionCustom_Processing.triggered.connect(lambda: self._program_manager.toggle_display('customProcessing'))

        self.actionImage.triggered.connect(self._program_manager.get_image)
        self.actionImage_Directory.triggered.connect(self._program_manager.get_image_directory)
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
        self.actionCustom_Processing.setEnabled(True)

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

    def add_image(self, image):
        self.MplWidget.canvas.axes.imshow(image, cmap='gray')
        self.MplWidget.canvas.draw()

    def add_bboxes(self, bboxes):
        if not self.actionBounding_Boxes.isChecked():
            self.actionBounding_Boxes.setChecked(True)
        for box in bboxes:
            self.MplWidget.canvas.axes.plot([box.x1, box.x2], [box.y1, box.y1], color='blue', linestyle='dashed', marker='o', gid='bbox')
            self.MplWidget.canvas.axes.plot([box.x1, box.x2], [box.y2, box.y2], color='blue', linestyle='dashed', marker='o', gid='bbox')
            self.MplWidget.canvas.axes.plot([box.x1, box.x1], [box.y1, box.y2], color='blue', linestyle='dashed', marker='o', gid='bbox')
            self.MplWidget.canvas.axes.plot([box.x2, box.x2], [box.y1, box.y2], color='blue', linestyle='dashed', marker='o', gid='bbox')
        self.MplWidget.canvas.draw()

    def add_contours(self, contours):
        colors = ['red', 'orange', 'yellow', 'green', 'blue', 'indigo', 'violet']
        if not self.actionContour_view.isChecked():
            self.actionContour_view.setChecked(True)
        count = 0
        for contour in contours:
            contour_set = self.MplWidget.canvas.axes.contour(contour, [0.75], colors=colors[count % len(colors)])
            count += 1
            for line_collection in contour_set.collections:
                line_collection.set_gid('contour')
        self.MplWidget.canvas.draw()

    def add_edges(self, cells):
        for i in range(len(cells)):
            cell = cells[i]
            (x1, y1) = cell._cell_center
            for edge in cell._adj_list:
                if edge >= i:
                    (x2, y2) = cells[edge]._cell_center
                    self.MplWidget.canvas.axes.plot([x1, x2], [y1, y2], color='red', marker='o', gid='edge')
        self.MplWidget.canvas.draw()


    def delete(self, plot_item):
        # attributes: bbox, contour\
        for child in self.MplWidget.canvas.axes.get_children():
            if hasattr(child, '_gid') and child._gid == plot_item:
                child.remove()
        self.MplWidget.canvas.draw()

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

    def contour_success(self):
        # disable contouring
        self.actionContour_run.setEnabled(False)
        # enable contour viewing
        self.actionContour_view.setEnabled(True)
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
