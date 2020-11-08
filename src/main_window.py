from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QShortcut
from PyQt5.QtGui import QKeySequence
from PyQt5.uic import loadUi
from toolbar import CustomToolbar
from program_manager import ProgramManager
import pickle
import networkx as nx

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # set up ProgramManager
        self.program_manager = ProgramManager()

        loadUi("ui/main.ui", self)
        self.setWindowTitle("JAB Bacteria Network Detector")
        self.toolbar = CustomToolbar(self.MplWidget.canvas, self)
        self.addToolBar(self.toolbar)

        # Set some default options
        self.set_default_enablements()
        self.set_default_visibilities()

        # Connect the buttons to their corresponding actions
        self.actionClear.triggered.connect(self.clear_all_data_and_reset_window)
        self.actionOpenImage.triggered.connect(self.open_image_file_and_display)
        self.actionSave.triggered.connect(self.save)
        self.actionSaveAs.triggered.connect(self.save_as)
        self.actionExportToGephi.triggered.connect(self.convert_to_gephi_and_export)
        self.actionLoadProject.triggered.connect(self.load)

        self.actionViewBoundingBoxes.triggered.connect(self.handle_cell_bounding_boxes_view_press)
        self.actionViewContour.triggered.connect(self.handle_cell_contours_view_press)
        self.actionViewNetworkEdges.triggered.connect(self.handle_network_edges_view_press)
        self.actionRunAll.triggered.connect(self.run_yolo_and_edge_detection_and_display)

        # Keyboard shortcuts for **__POWER USERS__**
        QShortcut(QKeySequence("Ctrl+S"), self).activated.connect(lambda: self.actionSave.isEnabled() and \
                                                                          self.save())
        QShortcut(QKeySequence("Ctrl+R"), self).activated.connect(lambda: self.actionRunAll.isEnabled() and \
                                                                          self.run_yolo_and_edge_detection_and_display())
        QShortcut(QKeySequence("Ctrl+O"), self).activated.connect(lambda: self.actionOpenImage.isEnabled() and \
                                                                          self.open_image_file_and_display())

    def set_default_visibilities(self):
        self.progressBar.setVisible(False)
        self.cellCounter.setVisible(False)

    def set_default_enablements(self):
        self.actionSave.setEnabled(False)
        self.actionSaveAs.setEnabled(False)
        self.actionExportToGephi.setEnabled(False)
        self.actionLoadProject.setEnabled(True)
        self.actionClear.setEnabled(True)

        self.actionOpenImage.setEnabled(True)
        self.actionRunAll.setEnabled(False)

        self.actionViewBoundingBoxes.setEnabled(False)
        self.actionViewBoundingBoxes.setChecked(False)
        self.actionViewContour.setEnabled(False)
        self.actionViewContour.setChecked(False)
        self.actionViewNetworkEdges.setEnabled(False)
        self.actionViewNetworkEdges.setChecked(False)

    def clear_all_data_and_reset_window(self):
        self.program_manager = ProgramManager()
        self.MplWidget.clear_canvas()
        self.set_default_visibilities()
        self.set_default_enablements()

    def open_image_file_and_display(self):
        image_path, _ = QFileDialog.getOpenFileName(None, "Select image", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.tif *.tiff)")
        if not image_path:
            return

        self.program_manager.open_image_file_and_crop_if_necessary(image_path)

        self.MplWidget.draw_image(self.program_manager.image)

        # disable importing new images
        self.actionOpenImage.setEnabled(False)
        # enable finding bboxes
        self.actionRunAll.setEnabled(True)

    def run_yolo_and_edge_detection_and_display(self):
        self.actionRunAll.setEnabled(False)
        self.progressBar.setVisible(True)

        # run yolo
        self.progressBar.setFormat("Computing bounding boxes...")
        self.program_manager.compute_bounding_boxes(self.progressBar.setValue)

        self.MplWidget.draw_image(self.program_manager.image)

        self.program_manager.compute_bbox_overlaps_and_cell_centers()
        self.MplWidget.draw_cell_centers(self.program_manager.bio_objs)

        # run edge_detection
        self.progressBar.setFormat("Computing cell network...")
        self.program_manager.compute_cell_network_edges(self.MplWidget.canvas, self.progressBar.setValue)
        self.program_manager.compute_initial_graph()

        self.cellCounter.setText("Cell Count: " + str(self.program_manager.get_cell_count()))
        self.cellCounter.setVisible(True)

        self.actionViewNetworkEdges.setEnabled(True)
        self.actionViewNetworkEdges.setChecked(True)
        self.MplWidget.draw_network_edges(self.program_manager.bio_objs)
        self.toolbar.add_network_tools()


        self.actionSave.setEnabled(True)
        self.actionSaveAs.setEnabled(True)
        self.actionExportToGephi.setEnabled(True)
        self.actionViewBoundingBoxes.setEnabled(True)
        self.actionViewContour.setEnabled(True)

        self.progressBar.setVisible(False)

    def handle_cell_bounding_boxes_view_press(self):
        if self.actionViewBoundingBoxes.isChecked():
            self.MplWidget.draw_cell_bounding_boxes(self.program_manager.bio_objs)
        else:
            self.MplWidget.remove_cell_bounding_boxes()

    def handle_cell_contours_view_press(self):
        if self.actionViewContour.isChecked():
            self.MplWidget.draw_cell_contours(self.program_manager.bio_objs)
        else:
            self.MplWidget.remove_cell_contours()

    def handle_network_edges_view_press(self):
        if self.actionViewNetworkEdges.isChecked():
            self.MplWidget.draw_network_edges(self.program_manager.bio_objs)
        else:
            self.MplWidget.remove_network_edges()

    """------------------ UTILITIES -----------------------------"""

    def get_save_loc(self, ext):
        path, _ = QFileDialog.getSaveFileName(None, "Save File", "", ext)
        return path

    def convert_to_gephi_and_export(self):
        path = self.get_save_loc("Gephi Graphs (*.gexf)")

        # If they cancelled the operation
        if path is None:
            return

        if not path.endswith(".gexf"):
            path += ".gexf"

        # write the final output to the file
        nx.write_gexf(self.program_manager.graph, path)

    def save(self):
        if self.program_manager.pickle_path == "":
            self.save_as()
        else:
            pickle.dump( self.program_manager, open(self.program_manager.pickle_path, "wb"))

    def save_as(self):
        path = self.get_save_loc("Pickle Files (*.p)")

        if path is None:
            return
        if not path.endswith(".p"):
            path += ".p"

        self.program_manager.pickle_path = path

        self.save()

    def load(self):
        path, _ = QFileDialog.getOpenFileName(None, "Select image", "", "Pickle Files (*.p)")
        if path is None:
            return
        self.program_manager = pickle.load(open(path,"rb"))

        # in order to save, there must have been an image loaded, so load the image
        # allow them to save, etc
        self.MplWidget.draw_image(self.program_manager.image)
        self.actionOpenImage.setEnabled(False)
        self.actionSave.setEnabled(True)
        self.actionSaveAs.setEnabled(True)

        self.actionViewBoundingBoxes.setEnabled(True)
        self.actionViewBoundingBoxes.setChecked(False)

        self.cellCounter.setText("Cell Count: " + str(self.program_manager.get_cell_count()))
        self.cellCounter.setVisible(True)
        self.actionViewContour.setEnabled(True)
        self.actionViewContour.setChecked(False)
        self.MplWidget.draw_cell_centers(self.program_manager.bio_objs)
        self.actionExportToGephi.setEnabled(True)
        self.MplWidget.draw_network_edges(self.program_manager.bio_objs)
