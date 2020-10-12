from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSlider, QLCDNumber, QLabel, QPushButton
from PyQt5.QtCore import Qt

MIN_OPENINGS = 0
MAX_OPENINGS = 20
DEFAULT_OPENINGS = 7

MIN_DILATIONS = 0
MAX_DILATIONS = 20
DEFAULT_DILATIONS = 4

MIN_BIN_THRESH = 0
MAX_BIN_THRESH = 100
DEFAULT_BIN_THRESH = 50

def make_slider(action, layout, minn, maxx, default):
    slider = QSlider(Qt.Horizontal)
    slider.setMinimum(minn)
    slider.setMaximum(maxx)
    slider.setTickPosition(QSlider.TicksBelow)
    slider.setValue(default)
    slider.valueChanged.connect(action)

    layout.addWidget(slider)

def make_centered_label(layout, text):
    label = QLabel(text)
    label.setAlignment(Qt.AlignCenter)

    layout.addWidget(label)

class SliderWidget(QWidget):
    def __init__(self, mgr, parent=None):
        QWidget.__init__(self, parent)
        self.setWindowTitle('Image Processing Options')

        self.prgmmgr = mgr

        self.layout = QVBoxLayout()

        make_centered_label(self.layout, "Openings")
        self.openingsLCD = QLCDNumber()
        self.layout.addWidget(self.openingsLCD)
        make_slider(self.update_openings, self.layout, MIN_OPENINGS, MAX_OPENINGS, DEFAULT_OPENINGS)

        make_centered_label(self.layout, "Dilations")
        self.dilationsLCD = QLCDNumber()
        self.layout.addWidget(self.dilationsLCD)
        make_slider(self.update_dilations, self.layout, MIN_DILATIONS, MAX_DILATIONS, DEFAULT_DILATIONS)

        make_centered_label(self.layout, "Binary threshold")
        self.thresholdLCD = QLCDNumber()
        self.layout.addWidget(self.thresholdLCD)
        make_slider(self.update_threshold, self.layout, MIN_BIN_THRESH, MAX_BIN_THRESH, DEFAULT_BIN_THRESH)

        b1 = QPushButton("Update Processing")
        b1.clicked.connect(self.reprocess)
        self.layout.addWidget(b1)

    def update_openings(self, event):
        self.openingsLCD.display(event)
        self.prgmmgr.set_openings(event)
        self.prgmmgr.update_binary()

    def update_dilations(self, event):
        self.dilationsLCD.display(event)
        self.prgmmgr.set_dilations(event)
        self.prgmmgr.update_binary()

    def update_threshold(self, event):
        self.thresholdLCD.display(event / 100)
        self.prgmmgr.set_threshold(event / 100)
        self.prgmmgr.update_binary()

    def reprocess(self, event):
        self.prgmmgr.update_binary()
