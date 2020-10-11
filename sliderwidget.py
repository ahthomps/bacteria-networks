from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSlider, QLCDNumber, QLabel, QPushButton
from PyQt5.QtCore import Qt

DEFAULT_NUM_OPENINGS = 7
MIN_NUM_OPENINGS = 0
MAX_NUM_OPENINGS = 20

DEFAULT_NUM_DILATIONS = 4
MIN_NUM_DILATIONS = 0
MAX_NUM_DILATIONS = 20

DEFAULT_BIN_THRESH = 50
MIN_BIN_THRESH = 0
MAX_BIN_THRESH = 100

class SliderWidget(QWidget):
    def __init__(self, mgr, parent=None):
        QWidget.__init__(self, parent)
        
        self.setWindowTitle('Image Processing Options')
        
        self.num_openings = DEFAULT_NUM_OPENINGS
        self.num_dilations = DEFAULT_NUM_DILATIONS
        self.binary_threshold = DEFAULT_BIN_THRESH

        self.prgmmgr = mgr
        
        self.l1 = QLabel("Openings")
        self.l1.setAlignment(Qt.AlignCenter)
        self.openingsLCD = QLCDNumber()
        self.s1 = QSlider(Qt.Horizontal)
        self.s1.setMinimum(MIN_NUM_OPENINGS)
        self.s1.setMaximum(MAX_NUM_OPENINGS)
        self.s1.setTickPosition(QSlider.TicksBelow)
        self.s1.setValue(self.num_openings)
        self.s1.valueChanged.connect(self.updateOpenings)
        
        self.l2 = QLabel("Dilations")
        self.l2.setAlignment(Qt.AlignCenter)
        self.dilationsLCD = QLCDNumber()
        self.s2 = QSlider(Qt.Horizontal)
        self.s2.setMinimum(MIN_NUM_DILATIONS)
        self.s2.setMaximum(MAX_NUM_DILATIONS)
        self.s2.setTickPosition(QSlider.TicksBelow)
        self.s2.setValue(self.num_dilations)
        self.s2.valueChanged.connect(self.updateDilations)

        self.l3 = QLabel("Binary threshold")
        self.l3.setAlignment(Qt.AlignCenter)
        self.thresholdLCD = QLCDNumber()
        self.s3 = QSlider(Qt.Horizontal)
        self.s3.setMinimum(MIN_BIN_THRESH)
        self.s3.setMaximum(MAX_BIN_THRESH)
        self.s3.setValue(self.binary_threshold)
        self.s3.valueChanged.connect(self.updatethreshold)

        self.b1 = QPushButton("Update Processing")
        self.b1.clicked.connect(self.reprocess)

        self.layout = QVBoxLayout()

        self.layout.addWidget(self.l1)
        self.layout.addWidget(self.openingsLCD)
        self.layout.addWidget(self.s1)

        self.layout.addWidget(self.l2)
        self.layout.addWidget(self.dilationsLCD)
        self.layout.addWidget(self.s2)

        self.layout.addWidget(self.l3)
        self.layout.addWidget(self.thresholdLCD)
        self.layout.addWidget(self.s3)

        self.layout.addWidget(self.b1)

    def updateOpenings(self, event):
        self.openingsLCD.display(event)
        self.prgmmgr.set_openings(event)
        self.prgmmgr.updateBinary()

    def updateDilations(self, event):
        self.dilationsLCD.display(event)
        self.prgmmgr.set_dilations(event)
        self.prgmmgr.updateBinary()

    def updatethreshold(self, event):
        self.thresholdLCD.display(event / 100)
        self.prgmmgr.set_threshold(event / 100)
        self.prgmmgr.updateBinary()

    def reprocess(self, event):
        self.prgmmgr.updateBinary()
