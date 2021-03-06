from sys import path
path.append("ui")

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QShortcut
from PyQt5.QtGui import QKeySequence
from PyQt5.uic import loadUi

import os
import networkx as nx

from post_processing import PostProcessingManager
from crop_processing import IMAGE_EXTENSIONS
from toolbar import CustomToolbar, _Mode
from program_manager import ProgramManager
from mplwidget import MplWidget

UI_FILE = "ui/main.ui"

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
        self.batch_image_filenames = []
        self.batch_index = 0

        # Whether to take into account the surface "node"
        self.surface_node_is_enabled = True

        loadUi("ui/main.ui", self)
        self.menubar.setNativeMenuBar(False)

        # Set the default options
        self.set_default_enablements()
        self.set_default_visibilities()

        self.toolbar = CustomToolbar(self.MplWidget, self)
        self.addToolBar(self.toolbar)

        self.connect_buttons()

    def connect_buttons(self):
        # Connect the buttons to their corresponding actions
        # These are all lambdas because the ones that had keyword args didn't work
        # when they weren't lambdas.
        self.actionOpenImage.triggered.connect(lambda: self.open_image_file_and_display())
        self.actionExportToGephi.triggered.connect(lambda: self.export_to_gephi())
        self.actionImportFromGephi.triggered.connect(lambda: self.load_gexf())
        self.actionOpenImageDirectory.triggered.connect(lambda: self.open_image_directory())
        self.actionEnableSurfaceNode.triggered.connect(lambda: self.toggle_surface_node())

        self.actionViewBoundingBoxes.triggered.connect(lambda: self.handle_cell_bounding_boxes_view_press())
        self.actionViewNetworkEdges.triggered.connect(lambda: self.handle_network_edges_view_press())
        self.actionRunAll.triggered.connect(lambda: self.run_batch_processing() \
                                                    if self.is_batch_processing else \
                                                    self.run_yolo_and_edge_detection_and_display())
        self.actionManual.triggered.connect(lambda: self.allow_manual_labelling())

    def set_default_visibilities(self):
        self.progressBar.setVisible(False)
        self.LegendAndCounts.setVisible(False)

    def set_default_enablements(self):
        self.actionExportToGephi.setEnabled(False)
        self.actionImportFromGephi.setEnabled(False)

        self.actionRunAll.setEnabled(False)
        self.actionManual.setEnabled(False)

        self.actionViewBoundingBoxes.setEnabled(False)
        self.actionViewBoundingBoxes.setChecked(False)
        self.actionViewContour.setEnabled(False)
        self.actionViewContour.setChecked(False)
        self.actionViewNetworkEdges.setEnabled(False)
        self.actionViewNetworkEdges.setChecked(False)
        self.actionEnableSurfaceNode.setEnabled(True)
        self.actionEnableSurfaceNode.setChecked(True)

    def clear_all_data_and_reset_window(self, reset_batch=True):
        self.program_manager = ProgramManager()
        self.post_processor = None

        if reset_batch:
            self.is_batch_processing = False
            self.image_directory_path = ""
            self.batch_image_filenames = []

        loadUi("ui/main.ui", self)
        self.menubar.setNativeMenuBar(False)

        self.set_default_enablements()
        self.set_default_visibilities()

        self.removeToolBar(self.toolbar)
        self.toolbar = CustomToolbar(self.MplWidget, self)
        self.addToolBar(self.toolbar)

        self.connect_buttons()

    def open_image_directory(self):
        self.clear_all_data_and_reset_window()
        directory_path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if not directory_path:
            return
        self.is_batch_processing = True
        self.image_directory_path = directory_path

        self.actionRunAll.setEnabled(True)

    def run_batch_processing(self):
        self.progressBar.setVisible(True)
        self.actionRunAll.setEnabled(False)

        self.batch_image_filenames = list(filter(lambda path: any(path.endswith(x) for x in IMAGE_EXTENSIONS),
                                          os.listdir(self.image_directory_path)))

        if self.batch_image_filenames == []:
            self.clear_all_data_and_reset_window()
            return

        for i, path in enumerate(self.batch_image_filenames):
            self.progressBar.setFormat(f"Processing {path}...")
            image_path = os.path.join(self.image_directory_path, path)
            self.program_manager = ProgramManager()
            self.program_manager.open_image_file(image_path)
            self.program_manager.compute_bounding_boxes()
            self.program_manager.compute_bbox_overlaps_and_cell_centers()
            self.program_manager.compute_cell_network_edges()
            self.post_processor = PostProcessingManager(bio_objs=self.program_manager.bio_objs)
            self.export_to_gephi(export_path=image_path[:image_path.rfind(".")] + ".gexf")
            self.progressBar.setValue((i + 1) / len(self.batch_image_filenames) * 100)

        self.progressBar.setVisible(False)
        self.load_batch_image(0)

    def load_batch_image(self, index):
        if index not in range(len(self.batch_image_filenames)):
            return

        self.batch_index = index

        self.clear_all_data_and_reset_window(reset_batch=False)

        image_path = os.path.join(self.image_directory_path, self.batch_image_filenames[self.batch_index])
        self.program_manager.open_image_file(image_path)
        self.MplWidget.draw_image(self.program_manager.image)
        self.load_gexf(file_path=image_path[:image_path.rfind(".")] + ".gexf")

        self.toolbar.add_file_navigation_buttons()

    def open_image_file_and_display(self):
        self.clear_all_data_and_reset_window()
        image_path, _ = QFileDialog.getOpenFileName(None, "Select image", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.tif *.tiff)")
        if not image_path:
            return

        self.program_manager.open_image_file(image_path)
        self.MplWidget.draw_image(self.program_manager.image)

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

        self.post_processor = PostProcessingManager(bio_objs=self.program_manager.bio_objs)
        self.toolbar.set_post_processor(self.post_processor)

        self.update_cell_counters()
        self.update_edge_counters()

        self.MplWidget.draw_network_nodes(self.post_processor.graph)
        self.MplWidget.draw_network_edges(self.post_processor.graph, self.surface_node_is_enabled)

    def allow_manual_labelling(self):
        self.actionRunAll.setEnabled(False)
        self.actionManual.setEnabled(False)
        self.actionImportFromGephi.setEnabled(False)
        self.actionExportToGephi.setEnabled(True)

        self.post_processor = PostProcessingManager(bio_objs=self.program_manager.bio_objs)
        self.toolbar.set_post_processor(self.post_processor)
        self.toolbar.add_network_tools()

        self.update_cell_counters()
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
            self.MplWidget.draw_network_edges(self.post_processor.graph, self.surface_node_is_enabled)
        else:
            self.MplWidget.remove_network_edges()

    def update_cell_counters(self):
        total_count, normal_count, spheroplast_count, filament_count, curved_count = self.post_processor.get_cell_count()
        self.LegendAndCounts.update_total_count(total_count)
        self.LegendAndCounts.update_normal_count(normal_count)
        self.LegendAndCounts.update_spheroplast_count(spheroplast_count)
        self.LegendAndCounts.update_filament_count(filament_count)
        self.LegendAndCounts.update_curved_count(curved_count)
        self.MplWidget.canvas.draw()

    def update_edge_counters(self):
        total_count, cell_to_cell_count, cell_to_surface_count, cell_contact_count = self.post_processor.get_edge_count()
        self.LegendAndCounts.update_total_edge_count(total_count)
        self.LegendAndCounts.update_cell_to_cell_count(cell_to_cell_count)
        self.LegendAndCounts.update_cell_to_surface_count(cell_to_surface_count)
        self.LegendAndCounts.update_cell_contact_count(cell_contact_count)
        self.MplWidget.canvas.draw()

    def toggle_surface_node(self):
        self.surface_node_is_enabled = not self.surface_node_is_enabled
        if self.post_processor is not None:
            self.MplWidget.draw_network_edges(self.post_processor.graph, self.surface_node_is_enabled)

    """------------------ UTILITIES -----------------------------"""

    def export_to_gephi(self, export_path=""):
        if export_path == "":
            export_path, _ = QFileDialog.getSaveFileName(None, 'Save Graph', '', 'Gephi Files (*.gexf)')
            if not export_path:
                return
            if not export_path.endswith('.gexf'):
                export_path += '.gexf'

        to_export = self.post_processor.graph.copy()
        if self.surface_node_is_enabled:
            for node in to_export.nodes():
                if node != 0:
                    to_export.add_edge(0, node, edge_type="cell_to_surface_contact")
        else:
            to_export.remove_node(0)


        nx.write_gexf(to_export, export_path)

    def load_gexf(self, file_path=None):
        if file_path is None:
            file_path, _ = QFileDialog.getOpenFileName(None, "Select Gephi File", "", "Gephi Files (*.gexf)")

        if not file_path:
            return

        self.actionRunAll.setEnabled(False)
        self.actionManual.setEnabled(False)

        graph = nx.MultiGraph(nx.read_gexf(file_path))
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
        self.actionEnableSurfaceNode.setEnabled(True)
        self.actionEnableSurfaceNode.setChecked(True)
        self.MplWidget.draw_network_edges(self.post_processor.graph, self.surface_node_is_enabled)

        self.update_cell_counters()
        self.update_edge_counters()
        self.LegendAndCounts.setVisible(True)
        self.actionExportToGephi.setEnabled(True)
