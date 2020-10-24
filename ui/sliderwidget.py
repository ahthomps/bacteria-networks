# ------------------------------------------------------
# -------------------- sliderwidget.py --------------------
# ------------------------------------------------------
from PyQt5.QtWidgets import *
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

def set_spin_box_defaults(spin_box, minn, maxx, default):
    spin_box.setMinimum(minn)
    spin_box.setMaximum(maxx)
    spin_box.setValue(default)

class SliderWidget(QWidget):
    """ Sliders are used for user-interactive image processing. The binary image
    that's created by default is normally quite good, but this allows for tweaking"""
    def __init__(self, parent = None):
        QWidget.__init__(self, parent)
        loadUi("ui/sliderwidget.ui", self)

        # # Initialize Openings Slider
        self.openingsInfoButton.setIcon(self.style().standardIcon(getattr(QStyle, 'SP_FileDialogInfoView')))
        self.openingsInfoButton.setToolTip("does openings stuff")
        self.openingsInfoButton.setStyleSheet("QToolButton {border: none;}")
        set_spin_box_defaults(self.openingsSpinBox, MIN_OPENINGS, MAX_OPENINGS, MIN_OPENINGS)


        # Initialize Dilations Slider
        self.dilationsInfoButton.setIcon(self.style().standardIcon(getattr(QStyle, 'SP_FileDialogInfoView')))
        self.dilationsInfoButton.setToolTip("does dilations stuff")
        self.dilationsInfoButton.setStyleSheet("QToolButton {border: none;}")
        set_spin_box_defaults(self.dilationsSpinBox, MIN_DILATIONS, MAX_DILATIONS, MIN_DILATIONS)

        # Initialize Threshold Slider
        self.thresholdInfoButton.setIcon(self.style().standardIcon(getattr(QStyle, 'SP_FileDialogInfoView')))
        self.thresholdInfoButton.setToolTip("does threshold stuff")
        self.thresholdInfoButton.setStyleSheet("QToolButton {border: none;}")
        set_spin_box_defaults(self.thresholdSpinBox, MIN_THRESHOLD, MAX_THRESHOLD, MIN_THRESHOLD / 100)
        self.thresholdSpinBox.setSingleStep(0.03)

    def update_openingsSpinBox(self, new_openings):
        self.openingsSpinBox.setValue(new_openings)

    def update_dilationsSpinBox(self, new_dilations):
        self.dilationsSpinBox.setValue(new_dilations)

    def update_thresholdSpinBox(self, new_threshold):
        self.thresholdSpinBox.setValue(new_threshold)
