# ------------------------------------------------------
# -------------------- sliderwidget.py --------------------
# ------------------------------------------------------
from PyQt5.QtWidgets import *
from matplotlib.backends.backend_qt5agg import FigureCanvas
from matplotlib.figure import Figure
from PyQt5 import QtCore
from PyQt5.QtCore import Qt
from PyQt5.uic import loadUi

MIN_OPENINGS = 0
MAX_OPENINGS = 20
MIN_DILATIONS = 0
MAX_DILATIONS = 20
MIN_THRESHOLD = 0
MAX_THRESHOLD = 100

def set_slider_defaults(slider, minn, maxx, default):
    slider.setMinimum(minn)
    slider.setMaximum(maxx)
    slider.setTickPosition(QSlider.TicksBelow)
    slider.setValue(default)

class SliderWidget(QWidget):
    """ Sliders are used for user-interactive image processing. The binary image
    that's created by default is normally quite good, but this allows for tweaking"""
    def __init__(self, parent = None):
        QWidget.__init__(self, parent)
        loadUi("sliderwidget.ui", self)

        # # Initialize Openings Slider
        self.openingsInfoButton.setIcon(self.style().standardIcon(getattr(QStyle, 'SP_FileDialogInfoView')))
        self.openingsInfoButton.setToolTip("does openings stuff")
        self.openingsInfoButton.setStyleSheet("QToolButton {border: none;}")
        set_slider_defaults(self.openingsSlider, MIN_OPENINGS, MAX_OPENINGS, MIN_OPENINGS)

        # Initialize Dilations Slider
        self.dilationsInfoButton.setIcon(self.style().standardIcon(getattr(QStyle, 'SP_FileDialogInfoView')))
        self.dilationsInfoButton.setToolTip("does dilations stuff")
        self.dilationsInfoButton.setStyleSheet("QToolButton {border: none;}")
        set_slider_defaults(self.dilationsSlider, MIN_DILATIONS, MAX_DILATIONS, MIN_DILATIONS)

        # Initialize Threshold Slider
        self.thresholdInfoButton.setIcon(self.style().standardIcon(getattr(QStyle, 'SP_FileDialogInfoView')))
        self.thresholdInfoButton.setToolTip("does threshold stuff")
        self.thresholdInfoButton.setStyleSheet("QToolButton {border: none;}")
        set_slider_defaults(self.thresholdSlider, MIN_THRESHOLD, MAX_THRESHOLD, MIN_THRESHOLD)

    def update_openingsLCD(self, new_openings):
        self.openingsLCD.display(new_openings)

    def update_dilationsLCD(self, new_dilations):
        self.dilationsLCD.display(new_dilations)

    def update_thresholdLCD(self, new_threshold):
        self.thresholdLCD.display(new_threshold)

    def move_openings_slider(self, new_openings):
        self.openingsSlider.setValue(new_openings)

    def move_dilations_slider(self, new_dilations):
        self.dilationsSlider.setValue(new_dilations)

    def move_threshold_slider(self, new_threshold):
        self.thresholdSlider.setValue(new_threshold * 100)
