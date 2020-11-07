from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QShortcut
from PyQt5.QtGui import QKeySequence
from PyQt5.uic import loadUi
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT
from program_manager import ProgramManager
import pickle
import networkx as nx

class NavigationToolbar(NavigationToolbar2QT):
    def __init__(self, canvas, main_window):
        super().__init__(canvas, main_window)
        for _ in range(5):
            self.removeAction(self.actions()[-1])


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        loadUi("ui/main.ui", self)
        self.setWindowTitle("JAB Bacteria Network Detector")
        self.addToolBar(NavigationToolbar(self.MplWidget.canvas, self))

        self.labeling_buttons = (self.BaddCell, self.BaddEdge, self.BchangeClass)

        # set up ProgramManager
        self.program_manager = ProgramManager()
        self.set_default_enablements()

        # Connect the buttons to their corresponding actions
        self.actionClear.triggered.connect(self.clear_all_data_and_reset_window)
        self.actionImage.triggered.connect(self.open_image_file_and_display)
        self.actionSave.triggered.connect(self.save)
        self.actionSave_As.triggered.connect(self.save_as)
        self.actionExport_to_Gephi.triggered.connect(self.convert_to_gephi_and_export)
        self.actionLoad_Project.triggered.connect(self.load)

        self.actionBounding_Boxes.triggered.connect(self.handle_cell_bounding_boxes_view_press)
        self.actionContour_view.triggered.connect(self.handle_cell_contours_view_press)
        self.actionRun_All.triggered.connect(self.run_yolo_and_edge_detection_and_display)

        self.MplWidget.canvas.mpl_connect("button_press_event", self.on_canvas_press)

        # Keyboard shortcuts for **__POWER USERS__**
        QShortcut(QKeySequence("Ctrl+S"), self).activated.connect(lambda: self.actionSave.isEnabled() and \
                                                                          self.save())
        QShortcut(QKeySequence("Ctrl+R"), self).activated.connect(lambda: self.actionRun_All.isEnabled() and \
                                                                          self.run_yolo_and_edge_detection_and_display())
        QShortcut(QKeySequence("Ctrl+O"), self).activated.connect(lambda: self.actionImage.isEnabled() and \
                                                                          self.open_image_file_and_display())

        # Hide the progress bar
        self.progressBar.setVisible(False)

    def set_default_enablements(self):
        self.actionSave.setEnabled(False)
        self.actionSave_As.setEnabled(False)
        self.actionExport_to_Gephi.setEnabled(False)
        self.actionLoad_Project.setEnabled(True)
        self.actionClear.setEnabled(True)

        self.actionImage.setEnabled(True)
        self.actionRun_All.setEnabled(False)

        self.CellCounter.setVisible(False)
        self.toggle_labeling_buttons(False)

        self.actionBounding_Boxes.setEnabled(False)
        self.actionBounding_Boxes.setChecked(False)
        self.actionContour_view.setEnabled(False)
        self.actionContour_view.setChecked(False)

    def clear_all_data_and_reset_window(self):
        self.program_manager = ProgramManager()
        self.MplWidget.clear_canvas()
        self.set_default_enablements()

    def on_canvas_press(self, event):
        ...
        # print("press")
        # print("event.xdata", event.xdata)
        # print("event.ydata", event.ydata)
        # print("event.inaxes", event.inaxes)
        # print("x", event.x)
        # print("y", event.y)
        # self.MplWidget.draw_point(event.xdata, event.ydata)

    def toggle_labeling_buttons(self, on):
        for button in self.labeling_buttons:
            button.setVisible(on)

    def open_image_file_and_display(self):
        self.program_manager.open_image_file_and_crop_if_necessary()
        if self.program_manager.image_path == "":
            return
        self.MplWidget.draw_image(self.program_manager.image)

        # disable importing new images
        self.actionImage.setEnabled(False)
        # enable finding bboxes
        self.actionRun_All.setEnabled(True)

    def run_yolo_and_edge_detection_and_display(self):
        self.actionRun_All.setEnabled(False)

        self.progressBar.setVisible(True)

        # run yolo
        self.program_manager.compute_bounding_boxes(self.progressBar.setValue)

        self.MplWidget.draw_image(self.program_manager.image)
        self.MplWidget.draw_cell_bounding_boxes(self.program_manager.bio_objs)

        # enable toggling bbox display
        self.actionBounding_Boxes.setEnabled(True)
        self.actionBounding_Boxes.setChecked(True)
        # enable image processing
        # self.actionProcess_Image.setEnabled(True)
        # enable edge detection
        self.actionEdge_Detection.setEnabled(True)

        # allow user to view cell counts
        self.MplWidget.draw_cell_bounding_boxes(self.program_manager.bio_objs)
        self.CellCounter.setText('Cell Count: ' + str(self.get_cell_count()))
        self.CellCounter.setVisible(True)

        self.program_manager.compute_bbox_overlaps_and_cell_centers()
        self.MplWidget.draw_cell_centers(self.program_manager.bio_objs)

        # run edge_detection
        self.program_manager.compute_cell_network_edges(self.MplWidget.canvas)
        self.MplWidget.remove_cell_bounding_boxes()
        self.MplWidget.draw_cell_network_edges(self.program_manager.bio_objs)

        self.toggle_labeling_buttons(True)

        self.actionSave.setEnabled(True)
        self.actionSave_As.setEnabled(True)

        self.progressBar.setVisible(False)

    """ ---------------------- IMAGE PROCESSSING ---------------------------- """

    def handle_cell_bounding_boxes_view_press(self):
        if self.actionBounding_Boxes.isChecked():
            self.MplWidget.draw_cell_bounding_boxes(self.program_manager.bio_objs)
        else:
            self.MplWidget.remove_cell_bounding_boxes()

    def handle_cell_contours_view_press(self):
        if self.actionContour_view.isChecked():
            self.MplWidget.draw_cell_contours(self.program_manager.bio_objs)
        else:
            self.MplWidget.remove_cell_contours()

    """------------------ UTILITIES -----------------------------"""

    def generate_automated_graph(self):
        # initialize graph
        self.graph = nx.Graph()

        # add all nodes
        for bioObject in self.program_manager.bio_objs:
            if bioObject.is_cell():
                x, y = bioObject.center()
                self.graph.add_node(bioObject.id, xpos = x, ypos = y)

        # add all edges
        for bioObject in self.program_manager.bio_objs:
            if bioObject.is_cell():
                for adj_cell in bioObject.adj_list:
                    self.graph.add_edge(bioObject.id, adj_cell.id)

    def get_cell_count(self):
        return sum(bio_object.is_cell() for bio_object in self.program_manager.bio_objs)

    def convert_to_gephi_and_export(self):
        # get the path and make sure it's good
        path = self.program_manager.get_save_loc('Gephi Files (*.gexf)')

        if not path:
            print('somehow the path was none')
            return

        if path[-5:] != ".gexf":
            path = path + ".gexf"

        # write the final output to the file
        nx.write_gexf(self.graph, path)

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
        self.MplWidget.draw_cell_centers(self.program_manager.bio_objs)
        self.actionExport_to_Gephi.setEnabled(True)
        self.MplWidget.draw_cell_network_edges(self.program_manager.bio_objs)
