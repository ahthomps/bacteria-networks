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
import networkx as nx

from image_processing import *
from contouring import compute_cell_contours
from classes import Tile
from make_labeled_crops import *
from edge_detection import compute_cell_contact

CROP_SIZE = 416

class ProgramManager:
    def __init__(self):
        self.image = np.asarray([])
        self.binary_image = np.asarray([])
        self.cells = []

        self.openings = DEFAULT_OPENINGS
        self.dilations = DEFAULT_DILATIONS
        self.threshold = None # This is a hack and should be changed.

        self.image_path = ""
        self.label_path = ""
        self.crop_dir = "" # This should actually be a constant

    def open_image_file(self):
        path, _ = QFileDialog.getOpenFileName(None, "Select image", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.tif)")
        if not path:
            return False

        print("using image {}".format(path))
        self.image_path = path
        self.image = plt.imread(self.image_path)
        return True

    def open_label_file(self):
        path, _ = QFileDialog.getOpenFileName(None, "Select label", "", "Label Files (*.txt)")
        if not path:
            return

        print("using label {}".format(path))
        self.label_path = path
        self.label_ofile = open(self.label_path)
        self.cells = parse_yolo_input(self.label_ofile, self.image)

    def get_export_loc(self):
        path, _ = QFileDialog.getSaveFileName(None, 'Save File', ".gexf", "Gephi Files (*.gexf)")
        if not path:
            return
        return path


    def compute_bounding_boxes(self):
        if self.crop_dir == "":
            image_filename = self.image_path
            slash_index = -1
            if "/" in image_filename:
                slash_index = image_filename.rfind("/")
            elif "\\" in image_filename:
                slash_index = image_filename.rfind("\\")
            image_filename = image_filename[slash_index + 1:]

            filenames = [image_filename]
            paths = [self.image_path]
            top_left_corners = [(0, 0)]
        else:
            filenames = list(filter(lambda s: any(s.lower().endswith(ext) for ext in IMAGE_EXTENSIONS), os.listdir(self.crop_dir)))
            paths = list(map(lambda filename: f"{self.crop_dir}/{filename}", filenames))
            top_left_corners = list(map(int, path[:path.rfind(".")].split("_")[-2:]) for path in paths)

        # This is a list of lists of cells, each list corresponding to a crop.
        cell_lists = parse_yolo_output(run_yolo_on_images(paths))

        if len(cell_lists) > 1:
            tiles = []
            for i in range(len(filenames)):
                xmin, ymin = top_left_corners[i]
                tile = Tile(Image.open(paths[i]), xmin, ymin, xmin + TILE_SIZE, ymin + TILE_SIZE, filenames[i])
                tile.cells = cell_lists[i]
                tiles.append(tile)
            full_tile = reunify_tiles(tiles)
            self.image = np.array(full_tile.img)
            self.cells = full_tile.cells
        else:
            self.cells = cell_lists[0]

    def compute_binary_image(self):
        print("progessing image...")
        self.binary_image, self.threshold = process_image(self.image, self.openings, self.dilations, self.threshold)
        print("found processed image!")

    def compute_cell_contours(self):
        print("getting contours...")
        compute_cell_contours(self.binary_image, self.cells)
        print("found contours!")

    def crop(self):
        # Make the crops directory
        directory = self.image_path[:self.image_path.rfind("/")]
        self.crop_dir = "./.crops"

        os.makedirs(self.crop_dir, exist_ok=True)

        # Remove any clutter in the crop directory
        for file in os.listdir(self.crop_dir):
            os.remove(f"{self.crop_dir}/{file}")

        # Get a list of all the image files we're going to crop
        input_images = [self.image_path[self.image_path.rfind("/") + 1:]]

        # Crop each image, and save all the crops in self.crop_dir
        for filename in input_images:
            for tile in make_tiles(Image.open(f"{directory}/{filename}"), filename[:filename.rfind(".")]):
                tile.save(directory=self.crop_dir)

        print(f"Made {len(os.listdir(self.crop_dir))} crops.")

    def compute_cell_network_edges(self):
        compute_cell_contact(self.cells)


class MainWindow(QMainWindow):
    def __init__(self):
        # set up UI window
        QMainWindow.__init__(self)
        loadUi("ui/main.ui", self)
        self.setWindowTitle("JAB Bacteria Networks Detector")
        self.addToolBar(NavigationToolbar(self.MplWidget.canvas, self))

        # set up ProgramManager
        self.program_manager = ProgramManager()
        self.set_default_enablements()

        # set up all button presses
        self.actionClear.triggered.connect(self.clear_all_data_and_reset_window)

        self.actionImage.triggered.connect(self.open_image_file_and_display)
        self.actionLabel.triggered.connect(self.open_label_file_and_display)

        self.actionExport_to_Gephi.triggered.connect(self.convert_to_gephi_and_export)

        self.actionYOLO.triggered.connect(self.run_yolo_and_display)
        self.actionProcess_Image.triggered.connect(self.compute_binary_image_and_display)
        self.actionContour_run.triggered.connect(self.compute_cell_contours_and_display)
        self.actionEdge_Detection.triggered.connect(self.compute_cell_network_edges_and_display)

        self.actionCrop.triggered.connect(self.compute_image_crops_and_change_enablements)

        self.actionBinary_Image.triggered.connect(self.handle_binary_image_view_press)
        self.actionBounding_Boxes.triggered.connect(self.handle_cell_bounding_boxes_view_press)
        self.actionContour_view.triggered.connect(self.handle_cell_contours_view_press)

        # NEW SliderWidget ones:
        self.SliderWidget.restoreDefaultsButton.clicked.connect(self.set_image_processing_numbers_to_default_and_display_new_binary_image)
        self.SliderWidget.openingsSpinBox.valueChanged.connect(self.update_openings_number_and_display_new_binary_image)
        self.SliderWidget.dilationsSpinBox.valueChanged.connect(self.update_dilations_number_and_display_new_binary_image)
        self.SliderWidget.thresholdSpinBox.valueChanged.connect(self.update_threshold_number_and_display_new_binary_image)

    def set_default_enablements(self):
        self.actionSave.setEnabled(False)
        self.actionSave_As.setEnabled(False)
        self.actionExport_to_Gephi.setEnabled(False)
        self.actionClear.setEnabled(True)

        self.actionImage.setEnabled(True)

        self.actionCustom_Processing.setEnabled(False)
        self.SliderWidget.setVisible(False)

        self.actionLabel.setEnabled(False)
        self.actionYOLO.setEnabled(False)
        self.actionProcess_Image.setEnabled(False)
        self.actionContour_run.setEnabled(False)
        self.actionEdge_Detection.setEnabled(False)

        self.actionCrop.setEnabled(False)

        self.actionBounding_Boxes.setEnabled(False)
        self.actionBounding_Boxes.setChecked(False)
        self.actionBinary_Image.setEnabled(False)
        self.actionBinary_Image.setChecked(False)
        self.actionContour_view.setEnabled(False)
        self.actionContour_view.setChecked(False)

    def clear_all_data_and_reset_window(self):
        self.program_manager = ProgramManager()
        self.MplWidget.clear_canvas()
        self.set_default_enablements()

    def open_image_file_and_display(self):
        self.program_manager.open_image_file()
        if self.program_manager.image_path == "":
            return
        self.MplWidget.draw_image(self.program_manager.image)

        if any(dim > CROP_SIZE for dim in self.program_manager.image.shape):
            self.actionCrop.setEnabled(True)

        # disable importing new images
        self.actionImage.setEnabled(False)
        # enable finding bboxes
        self.actionLabel.setEnabled(True)
        self.actionYOLO.setEnabled(True)

    def open_label_file_and_display(self):
        self.program_manager.open_label_file()
        if self.program_manager.label_path == "":
            return
        self.MplWidget.draw_cell_bounding_boxes(self.program_manager.cells)

        # disable finding bounding boxes
        self.actionLabel.setEnabled(False)
        self.actionYOLO.setEnabled(False)
        # enable toggling bbox display
        self.actionBounding_Boxes.setEnabled(True)
        self.actionBounding_Boxes.setChecked(True)
        # enable image processing
        self.actionProcess_Image.setEnabled(True)

    def run_yolo_and_display(self):
        self.program_manager.compute_bounding_boxes()

        self.MplWidget.draw_image(self.program_manager.image)
        self.MplWidget.draw_cell_bounding_boxes(self.program_manager.cells)

        # disable finding bounding boxes
        self.actionLabel.setEnabled(False)
        self.actionYOLO.setEnabled(False)
        # enable toggling bbox display
        self.actionBounding_Boxes.setEnabled(True)
        self.actionBounding_Boxes.setChecked(True)
        # enable image processing
        self.actionProcess_Image.setEnabled(True)

    """ ---------------------- IMAGE PROCESSSING ---------------------------- """

    def compute_binary_image_and_display(self):
        self.program_manager.compute_binary_image()
        self.MplWidget.draw_image(self.program_manager.binary_image)

        # disable image processing
        self.actionProcess_Image.setEnabled(False)
        # enable binary image viewing
        self.actionBinary_Image.setEnabled(True)
        self.actionBinary_Image.setChecked(True)
        # enable contouring
        self.actionContour_run.setEnabled(True)
        # enable image processing options
        self.set_SliderWidget_defaults_and_display()

    def set_SliderWidget_defaults_and_display(self):
        self.SliderWidget.openingsSpinBox.blockSignals(True)
        self.SliderWidget.dilationsSpinBox.blockSignals(True)
        self.SliderWidget.thresholdSpinBox.blockSignals(True)
        self.SliderWidget.update_openingsSpinBox(self.program_manager.openings)
        self.SliderWidget.update_dilationsSpinBox(self.program_manager.dilations)
        self.SliderWidget.update_thresholdSpinBox(self.program_manager.threshold)
        self.SliderWidget.openingsSpinBox.blockSignals(False)
        self.SliderWidget.dilationsSpinBox.blockSignals(False)
        self.SliderWidget.thresholdSpinBox.blockSignals(False)
        self.SliderWidget.setVisible(True)

    def update_openings_number_and_display_new_binary_image(self, new_openings):
        # update openings attribute in ProgramManager
        self.program_manager.openings = new_openings
        # find new binary image and display
        self.program_manager.compute_binary_image()
        self.MplWidget.draw_image(self.program_manager.binary_image)

    def update_dilations_number_and_display_new_binary_image(self, new_dilations):
        # update openings attribute in ProgramManager
        self.program_manager.dilations = new_dilations
        # find new binary image and display
        self.program_manager.compute_binary_image()
        self.MplWidget.draw_image(self.program_manager.binary_image)

    def update_threshold_number_and_display_new_binary_image(self, new_threshold):
        # update openings attribute in ProgramManager
        self.program_manager.threshold = new_threshold
        # find new binary image and display
        self.program_manager.compute_binary_image()
        self.MplWidget.draw_image(self.program_manager.binary_image)

    def set_image_processing_numbers_to_default_and_display_new_binary_image(self):
        self.program_manager.openings = DEFAULT_OPENINGS
        self.program_manager.dilations = DEFAULT_DILATIONS
        self.program_manager.threshold = None
        self.program_manager.compute_binary_image()
        self.set_SliderWidget_defaults_and_display()
        self.MplWidget.draw_image(self.program_manager.binary_image)

    """ ------------------------- CONTOURING ----------------------------------- """

    def compute_cell_contours_and_display(self):
        self.program_manager.compute_cell_contours()
        self.MplWidget.remove_cell_bounding_boxes()
        self.MplWidget.draw_cell_contours(self.program_manager.cells)
        self.MplWidget.draw_image(self.program_manager.image)

        # disable contouring
        self.actionContour_run.setEnabled(False)
        # disable image processing
        self.SliderWidget.setVisible(False)
        self.actionCustom_Processing.setEnabled(False)
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
        self.program_manager.compute_cell_network_edges()
        self.MplWidget.draw_cell_network_edges(self.program_manager.cells)

        # disable edge detection
        self.actionEdge_Detection.setEnabled(False)
        # enable edges viewing

        # enable export to Gephi!
        self.actionExport_to_Gephi.setEnabled(True)

    def compute_image_crops_and_change_enablements(self):
        self.program_manager.crop()

        # disable cropping
        self.actionCrop.setEnabled(False)
        # enable finding bboxes with YOLO
        self.actionYOLO.setEnabled(True)

    def handle_binary_image_view_press(self):
        if self.actionBinary_Image.isChecked():
            self.MplWidget.draw_image(self.program_manager.binary_image)
        else:
            self.MplWidget.draw_image(self.program_manager.image)

    def handle_cell_bounding_boxes_view_press(self):
        if self.actionBounding_Boxes.isChecked():
            self.MplWidget.draw_cell_bounding_boxes(self.program_manager.cells)
        else:
            self.MplWidget.remove_cell_bounding_boxes()

    def handle_cell_contours_view_press(self):
        if self.actionContour_view.isChecked():
            self.MplWidget.draw_cell_contours(self.program_manager.cells)
        else:
            self.MplWidget.remove_cell_contours()

    def convert_to_gephi_and_export(self):
        # get the path and make sure it's good
        path = self.program_manager.get_export_loc()

        if not path:
            print('somehow the path was none')
            return
        
        if path[-4:] != ".gexf":
            path = path + ".gexf"

        # initialize graph
        G = nx.Graph()
        # snag the cells
        cells = self.program_manager.cells

        # add all nodes
        for cell in cells:
            G.add_node(cell.id)

        # add all edges
        for cell in cells:
            for adj_cell in cell.adj_list:
                G.add_edge(cell.id, adj_cell.id)

        # write the final output to the file
        nx.write_gexf(G, path)


app = QApplication([])
window = MainWindow()
window.show()
app.exec_()
