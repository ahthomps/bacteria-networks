from PyQt5.QtWidgets import QWidget
from PyQt5.uic import loadUi

class LegendAndCounts(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self, parent)
        loadUi("ui/legend_and_counts.ui", self)

    def update_normal_count(self, count):
        self.normalCount.setText(str(count))

    def update_filament_count(self, count):
        self.filamentCount.setText(str(count))

    def update_curved_count(self, count):
        self.curvedCount.setText(str(count))

    def update_spheroplast_count(self, count):
        self.sphereoplastCount.setText(str(count))

    def update_total_count(self, count):
        self.totalCount.setText(str(count))
