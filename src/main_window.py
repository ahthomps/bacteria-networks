from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QShortcut
from PyQt5.QtGui import QKeySequence
from PyQt5.uic import loadUi

import os
import networkx as nx

from post_processing import PostProcessingManager
from toolbar import CustomToolbar
from program_manager import ProgramManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # set up ProgramManager
        self.program_manager = ProgramManager()
        self.post_processor = None

        # These are for batch processing. It feels wrong to put them in ProgramManager
        # because they need to persist between different images.
        # It also feels wrong to put them here.
        self.is_batch_processing = False
        self.image_directory_path = ""

        loadUi("ui/main.ui", self)
        self.setWindowTitle("JAB Bacteria Network Detector")

        # Set some default options
        self.set_default_enablements()
        self.set_default_visibilities()

        # Connect the buttons to their corresponding actions
        self.actionClear.triggered.connect(self.clear_all_data_and_reset_window)
        self.actionOpenImage.triggered.connect(self.open_image_file_and_display)
        self.actionExportToGephi.triggered.connect(self.export_to_gephi)
        self.actionImportFromGephi.triggered.connect(self.load)
        self.actionOpenImageDirectory.triggered.connect(self.open_image_directory)
        self.actionViewLegend.triggered.connect(self.handle_legend_view_press)

        self.actionViewBoundingBoxes.triggered.connect(self.handle_cell_bounding_boxes_view_press)
        self.actionViewNetworkEdges.triggered.connect(self.handle_network_edges_view_press)
        self.actionRunAll.triggered.connect(lambda: self.run_batch_processing() \
                                                    if self.is_batch_processing else \
                                                    self.run_yolo_and_edge_detection_and_display())
        self.actionManual.triggered.connect(self.allow_manual_labelling)

        # Keyboard shortcuts for **__POWER USERS__**
        QShortcut(QKeySequence("Ctrl+S"), self).activated.connect(lambda: self.actionExportToGephi.isEnabled() and \
                                                                          self.export_to_gephi())
        QShortcut(QKeySequence("Ctrl+R"), self).activated.connect(lambda: self.actionRunAll.isEnabled() and \
                                                                          (self.run_batch_processing() \
                                                                          if self.is_batch_processing else \
                                                                          self.run_yolo_and_edge_detection_and_display()))
        QShortcut(QKeySequence("Ctrl+O"), self).activated.connect(lambda: self.actionOpenImage.isEnabled() and \
                                                                          self.open_image_file_and_display())
        QShortcut(QKeySequence("Ctrl+Shift+O"), self).activated.connect(lambda: self.actionOpenImageDirectory.isEnabled() and \
                                                                                self.open_image_directory())

    def set_default_visibilities(self):
        self.progressBar.setVisible(False)
        self.LegendAndCounts.setVisible(False)
        self.toolbar = CustomToolbar(self.MplWidget, self)
        self.addToolBar(self.toolbar)

    def set_default_enablements(self):
        self.actionExportToGephi.setEnabled(False)
        self.actionImportFromGephi.setEnabled(False)
        self.actionClear.setEnabled(True)

        self.actionOpenImage.setEnabled(True)
        self.actionOpenImageDirectory.setEnabled(True)
        self.actionRunAll.setEnabled(False)
        self.actionManual.setEnabled(False)

        self.actionViewBoundingBoxes.setEnabled(False)
        self.actionViewBoundingBoxes.setChecked(False)
        self.actionViewContour.setEnabled(False)
        self.actionViewContour.setChecked(False)
        self.actionViewNetworkEdges.setEnabled(False)
        self.actionViewNetworkEdges.setChecked(False)
        self.actionViewLegend.setEnabled(False)
        self.actionViewLegend.setChecked(False)

    def clear_all_data_and_reset_window(self):
        self.program_manager = ProgramManager()
        self.MplWidget.clear_canvas()
        self.removeToolBar(self.toolbar)
        self.set_default_visibilities()
        self.set_default_enablements()

        self.is_batch_processing = False
        self.image_directory_path = ""

    def open_image_directory(self):
        directory_path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if not directory_path:
            return
        self.is_batch_processing = True
        self.image_directory_path = directory_path

        self.actionRunAll.setEnabled(True)
        self.actionOpenImage.setEnabled(False)
        self.actionOpenImageDirectory.setEnabled(False)

    def run_batch_processing(self):
        self.progressBar.setVisible(True)
        self.actionRunAll.setEnabled(False)
        images = list(filter(lambda path: any(path.endswith(x) for x in IMAGE_EXTENSIONS), os.listdir(self.image_directory_path)))
        for i, path in enumerate(images):
            self.progressBar.setFormat(f"Processing {path}...")
            image_path = os.path.join(self.image_directory_path, path)
            self.program_manager = ProgramManager()
            self.program_manager.open_image_file_and_crop_if_necessary(image_path)
            self.program_manager.compute_bounding_boxes()
            self.program_manager.compute_bbox_overlaps_and_cell_centers()
            self.program_manager.compute_cell_network_edges()
            self.post_processor = PostProcessingManager(bio_objs=self.program_manager.bio_objs)
            self.export_to_gephi(export_path=image_path[:image_path.rfind(".")] + ".gexf")
            self.progressBar.setValue((i + 1) / len(images) * 100)
        self.progressBar.setVisible(False)
        self.clear_all_data_and_reset_window()

    def open_image_file_and_display(self):
        image_path, _ = QFileDialog.getOpenFileName(None, "Select image", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.tif *.tiff)")
        if not image_path:
            return

        self.program_manager.open_image_file_and_crop_if_necessary(image_path)

        self.MplWidget.draw_image(self.program_manager.image)

        # disable importing new images
        self.actionOpenImage.setEnabled(False)
        self.actionOpenImageDirectory.setEnabled(False)
        # allow loading of saved project
        self.actionImportFromGephi.setEnabled(True)
        # enable running automatic network detection
        self.actionRunAll.setEnabled(True)
        # enable manual labeling option
        self.actionManual.setEnabled(True)

    def run_yolo_and_edge_detection_and_display(self):
        self.actionRunAll.setEnabled(False)
        self.actionManual.setEnabled(False)
        self.progressBar.setVisible(True)
        self.actionImportFromGephi.setEnabled(False)

        # run yolo
        self.progressBar.setFormat("Computing bounding boxes...")
        self.program_manager.compute_bounding_boxes(self.progressBar.setValue)

        self.program_manager.compute_bbox_overlaps_and_cell_centers()

        # run edge_detection
        self.progressBar.setFormat("Computing cell network...")
        self.program_manager.compute_cell_network_edges(self.progressBar.setValue)
        self.toolbar.add_network_tools()

        self.actionExportToGephi.setEnabled(True)
        self.actionViewBoundingBoxes.setEnabled(True)
        self.actionViewBoundingBoxes.setChecked(False)
        self.progressBar.setVisible(False)
        self.actionViewNetworkEdges.setEnabled(True)
        self.actionViewNetworkEdges.setChecked(True)
        self.LegendAndCounts.setVisible(True)
        self.actionViewLegend.setEnabled(True)
        self.actionViewLegend.setChecked(True)

        self.post_processor = PostProcessingManager(bio_objs=self.program_manager.bio_objs)
        self.toolbar.set_post_processor(self.post_processor)

        self.update_cell_counters()

        self.MplWidget.draw_network_nodes(self.post_processor.graph)
        self.MplWidget.draw_network_edges(self.post_processor.graph)

    def allow_manual_labelling(self):
        self.actionRunAll.setEnabled(False)
        self.actionManual.setEnabled(False)
        self.actionImportFromGephi.setEnabled(False)
        self.actionExportToGephi.setEnabled(True)

        self.post_processor = PostProcessingManager(bio_objs=self.program_manager.bio_objs)
        self.toolbar.set_post_processor(self.post_processor)
        self.toolbar.add_network_tools()

        self.update_cell_counters()
        self.LegendAndCounts.setVisible(True)

        self.actionViewNetworkEdges.setEnabled(True)
        self.actionViewNetworkEdges.setChecked(True)

    def handle_cell_bounding_boxes_view_press(self):
        if self.actionViewBoundingBoxes.isChecked():
            self.MplWidget.draw_cell_bounding_boxes(self.program_manager.bio_objs)
        else:
            self.MplWidget.remove_cell_bounding_boxes()

    def handle_network_edges_view_press(self):
        if self.actionViewNetworkEdges.isChecked():
            self.MplWidget.draw_network_edges(self.post_processor.graph)
        else:
            self.MplWidget.remove_network_edges()

    def handle_legend_view_press(self):
        self.LegendAndCounts.setVisible(self.actionViewLegend.isChecked())

    def update_cell_counters(self):
        total_count, normal_count, spheroplast_count, filament_count, curved_count = self.post_processor.get_cell_count()
        self.LegendAndCounts.update_total_count(total_count)
        self.LegendAndCounts.update_normal_count(normal_count)
        self.LegendAndCounts.update_spheroplast_count(spheroplast_count)
        self.LegendAndCounts.update_filament_count(filament_count)
        self.LegendAndCounts.update_curved_count(curved_count)
        self.MplWidget.canvas.draw()

    """------------------ UTILITIES -----------------------------"""

    def export_to_gephi(self, export_path=None):
        if export_path is None:
            export_path, _ = QFileDialog.getSaveFileName(None, 'Save Graph', '', 'Gephi Files (*.gexf')
            if export_path == "":
                return
            if not export_path.endswith('.gexf'):
                export_path += '.gexf'
        nx.write_gexf(self.post_processor.graph, export_path)

    def load(self):
        file_path, _ = QFileDialog.getOpenFileName(None, "Select Gephi File", "", "Gephi Files (*.gexf)")

        if not file_path:
            return

        self.program_manager.open_image_file_and_crop_if_necessary(self.program_manager.image_path)
        self.MplWidget.draw_image(self.program_manager.image)
        self.actionOpenImage.setEnabled(False)
        self.actionImportFromGephi.setEnabled(False)
        self.actionRunAll.setEnabled(False)
        self.actionManual.setEnabled(False)

        graph = nx.read_gexf(file_path)
        self.post_processor = PostProcessingManager(graph=graph)

        for node1, node2, edge_key, edge_data in self.post_processor.graph.edges(data=True, keys=True):
            if node1 != '0' and node2 != '0':
                continue
            surface_point_list = edge_data['surface_point'][1:-1].split(',')
            surface_point = {}
            for attribute in surface_point_list:
                key, value = attribute.split(':')
                surface_point[key[key.index("'") + 1:key.rfind("'")]] = int(value)
            self.post_processor.graph[node1][node2][edge_key]["surface_point"] = surface_point

        self.toolbar.add_network_tools()
        self.toolbar.set_post_processor(self.post_processor)

        self.MplWidget.draw_network_nodes(self.post_processor.graph)

        self.actionViewNetworkEdges.setEnabled(True)
        self.actionViewNetworkEdges.setChecked(True)
        self.MplWidget.draw_network_edges(self.post_processor.graph)

        self.update_cell_counters()
        self.LegendAndCounts.setVisible(True)
        self.actionExportToGephi.setEnabled(True)
