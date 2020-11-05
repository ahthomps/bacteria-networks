from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMainWindow, QFileDialog
from PyQt5.uic import loadUi
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT
from program_manager import ProgramManager
import pickle

class MainWindow(QMainWindow):
    def __init__(self):
        # set up UI window
        QMainWindow.__init__(self)
        loadUi("ui/main.ui", self)
        self.setWindowTitle("JAB Bacteria Networks Detector")
        self.addToolBar(NavigationToolbar2QT(self.MplWidget.canvas, self))

        self.labeling_buttons = [self.BaddCell, self.BaddEdge, self.BchangeClass]

        # set up ProgramManager
        self.program_manager = ProgramManager()
        self.set_default_enablements()

        # set up all button presses
        self.actionClear.triggered.connect(self.clear_all_data_and_reset_window)

        self.actionImage.triggered.connect(self.open_image_file_and_display)
        self.actionLabel.triggered.connect(self.open_label_file_and_display)

        self.actionSave.triggered.connect(self.save)
        self.actionSave_As.triggered.connect(self.save_as)
        self.actionExport_to_Gephi.triggered.connect(self.convert_to_gephi_and_export)
        self.actionLoad_Project.triggered.connect(self.load)

        self.actionBounding_Boxes.triggered.connect(self.handle_cell_bounding_boxes_view_press)
        self.actionContour_view.triggered.connect(self.handle_cell_contours_view_press)
        self.actionRun_All.triggered.connect(self.run_yolo_and_edge_detection_and_display)

        self.MplWidget.canvas.mpl_connect("button_press_event", self.on_canvas_press)

    def set_default_enablements(self):
        self.actionSave.setEnabled(False)
        self.actionSave_As.setEnabled(False)
        self.actionExport_to_Gephi.setEnabled(False)
        self.actionLoad_Project.setEnabled(True)
        self.actionClear.setEnabled(True)

        self.actionImage.setEnabled(True)

        self.SliderWidget.setVisible(False)
        self.CellCounter.setVisible(False)

        self.toggle_labeling_buttons(False)

        self.actionLabel.setEnabled(False)
        self.actionYOLO.setEnabled(False)
        self.actionProcess_Image.setEnabled(False)
        self.actionContour_run.setEnabled(False)
        self.actionEdge_Detection.setEnabled(False)
        self.actionRun_All.setEnabled(False)

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

    def on_canvas_press(self, event):
        print("press")
        print("event.xdata", event.xdata)
        print("event.ydata", event.ydata)
        print("event.inaxes", event.inaxes)
        print("x", event.x)
        print("y", event.y)
        self.MplWidget.draw_point(event.xdata, event.ydata)

    def toggle_labeling_buttons(self, on):
        if on:
            for button in self.labeling_buttons:
                button.setVisible(True)
        else:
            for button in self.labeling_buttons:
                button.setVisible(False)

    def open_image_file_and_display(self):
        self.program_manager.open_image_file_and_crop_if_necessary()
        if self.program_manager.image_path == "":
            return
        self.MplWidget.draw_image(self.program_manager.image)

        # disable importing new images
        self.actionImage.setEnabled(False)
        # enable finding bboxes
        self.actionLabel.setEnabled(True)
        self.actionYOLO.setEnabled(True)
        self.actionRun_All.setEnabled(True)

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
        # self.actionProcess_Image.setEnabled(True)
        # enable edge detection
        self.actionEdge_Detection.setEnabled(True)

        # allow user to view cell counts
        self.CellCounter.setText('Cell Count: ' + str(self.get_cell_count()))
        self.CellCounter.setVisible(True)

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
        # self.actionProcess_Image.setEnabled(True)
        # enable edge detection
        self.actionEdge_Detection.setEnabled(True)

        # allow user to view cell counts
        self.CellCounter.setText('Cell Count: ' + str(self.get_cell_count()))
        self.CellCounter.setVisible(True)

    def run_yolo_and_edge_detection_and_display(self):
        self.run_yolo_and_display()
        # then need to run contouring and edge detection and bring up the option
        # to manually label the image
        self.compute_cell_network_edges_and_display()
        self.toggle_labeling_buttons(True)

        self.actionSave.setEnabled(True)
        self.actionSave_As.setEnabled(True)

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
        self.program_manager.compute_cell_network_edges(self.MplWidget.canvas)
        self.MplWidget.draw_cell_network_edges(self.program_manager.cells)

        # disable edge detection
        self.actionEdge_Detection.setEnabled(False)
        # enable contour viewing
        self.actionContour_view.setEnabled(True)

        # enable export to Gephi!
        self.actionExport_to_Gephi.setEnabled(True)

        # enable manual labeling!
        self.toggle_labeling_buttons(True)

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

    """------------------ UTILITIES -----------------------------"""

    def get_cell_count(self):
        return sum(bio_object.is_cell() for bio_object in self.program_manager.cells)

    def convert_to_gephi_and_export(self):
        # get the path and make sure it's good
        path = self.program_manager.get_save_loc('Gephi Files (*.gexf)')

        if not path:
            print('somehow the path was none')
            return

        if path[-5:] != ".gexf":
            path = path + ".gexf"

        # initialize graph
        G = nx.Graph()
        # snag the cells
        cells = self.program_manager.cells

        # add all nodes
        for bioObject in cells:
            if bioObject.is_cell():
                G.add_node(bioObject.id)
                # add all edges
                for adj_cell in bioObject.adj_list:
                    G.add_edge(bioObject.id, adj_cell.id)

        # write the final output to the file
        nx.write_gexf(G, path)

    def save(self):
        if self.program_manager.filename is None:
            self.save_as()
        else:
            pickle.dump( self.program_manager, open(self.program_manager.filename, "wb"))

    def save_as(self):
        path = self.program_manager.get_save_loc('Pickle Files (*.p)')

        if not path:
            return
        if path[-2:] != '.p':
            path = path +'.p'

        self.program_manager.filename = path

        self.save()

    def load(self):
        path, _ = QFileDialog.getOpenFileName(None, "Select image", "", "Pickle Files (*.p)")
        if not path:
            return
        self.program_manager = pickle.load(open(path,"rb"))

        # in order to save, there must have been an image loaded, so load the image
        # allow them to save, etc
        self.MplWidget.draw_image(self.program_manager.image)
        self.actionImage.setEnabled(False)
        self.actionSave.setEnabled(True)
        self.actionSave_As.setEnabled(True)

        self.actionBounding_Boxes.setEnabled(True)
        self.actionBounding_Boxes.setChecked(False)

        self.CellCounter.setText('Cell Count: ' + str(self.get_cell_count()))
        self.CellCounter.setVisible(True)
        self.actionContour_view.setEnabled(True)
        self.actionContour_view.setChecked(False)
        self.MplWidget.draw_cell_centers(self.program_manager.cells)
        self.actionExport_to_Gephi.setEnabled(True)
        self.MplWidget.draw_cell_network_edges(self.program_manager.cells)
