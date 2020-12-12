from PyQt5.QtWidgets import QWidget
from PyQt5.uic import loadUi

class LegendAndCounts(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self, parent)
        loadUi("ui/legend_and_counts.ui", self)

    def update_normal_count(self, count):
        self.normal_count.setText(str(count))

    def update_filament_count(self, count):
        self.filament_count.setText(str(count))

    def update_curved_count(self, count):
        self.curved_count.setText(str(count))

    def update_spheroplast_count(self, count):
        self.sphereoplast_count.setText(str(count))

    def update_total_count(self, count):
        self.total_count.setText(str(count))

    def update_cell_to_surface_count(self, count):
        self.cell_to_surface_count.setText(str(count))

    def update_cell_to_cell_count(self, count):
        self.cell_to_cell_count.setText(str(count))

    def update_cell_contact_count(self, count):
        self.cell_contact_count.setText(str(count))

    def update_total_edge_count(self, count):
        self.edge_count.setText(str(count))
