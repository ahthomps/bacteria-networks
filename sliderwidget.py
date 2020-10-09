from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QSlider, QLCDNumber, QLabel, QPushButton)
import sys
from PyQt5.QtCore import Qt

class SliderWidget(QWidget):

    def __init__(self, mgr, parent = None):
        QWidget.__init__(self, parent)
        
        #self.resize(600,600)
        self.setWindowTitle('Fine Tune Image Settings')
        
        self.num_openings = 7
        self.num_dilations = 4
        self.binary_threshold = 50

        self.prgmmgr = mgr
        
        self.l1 = QLabel("# Openings")
        self.l1.setAlignment(Qt.AlignCenter)
        self.openingsLCD = QLCDNumber()
        self.s1 = QSlider(Qt.Horizontal)
        self.s1.setMinimum(0)
        self.s1.setMaximum(20)
        self.s1.setTickPosition(QSlider.TicksBelow)
        self.s1.setValue(self.num_openings)
        self.s1.valueChanged.connect(self.updateOpenings)
        
        self.l2 = QLabel("# Dialations")
        self.l2.setAlignment(Qt.AlignCenter)
        self.dialationsLCD = QLCDNumber()
        self.s2 = QSlider(Qt.Horizontal)
        self.s2.setMinimum(0)
        self.s2.setMaximum(20)
        self.s2.setTickPosition(QSlider.TicksBelow)
        self.s2.setValue(self.num_dilations)
        self.s2.valueChanged.connect(self.updateDialations)

        self.l3 = QLabel("Binary threshold")
        self.l3.setAlignment(Qt.AlignCenter)
        self.thresholdLCD = QLCDNumber()
        self.s3 = QSlider(Qt.Horizontal)
        self.s3.setMinimum(0)
        self.s3.setMaximum(100)
        self.s3.setValue(self.binary_threshold)
        self.s3.valueChanged.connect(self.updatethreshold)

        self.b1 = QPushButton("Update Processing")
        self.b1.clicked.connect(self.reprocess)

        self.layout = QVBoxLayout()

        self.layout.addWidget(self.l1)
        self.layout.addWidget(self.openingsLCD)
        self.layout.addWidget(self.s1)

        self.layout.addWidget(self.l2)
        self.layout.addWidget(self.dialationsLCD)
        self.layout.addWidget(self.s2)

        self.layout.addWidget(self.l3)
        self.layout.addWidget(self.thresholdLCD)
        self.layout.addWidget(self.s3)

        self.layout.addWidget(self.b1)

        

        #self.setLayout(self.layout)

    def updateOpenings(self, event):
        self.openingsLCD.display(event)
        self.prgmmgr.set_openings(event)
        self.prgmmgr.updateBinary()

    def updateDialations(self, event):
        self.dialationsLCD.display(event)
        self.prgmmgr.set_dialations(event)
        self.prgmmgr.updateBinary()

    def updatethreshold(self, event):
        self.thresholdLCD.display(event/100)
        self.prgmmgr.set_threshold(event/100)
        self.prgmmgr.updateBinary()

    def reprocess(self, event):
        self.prgmmgr.updateBinary()


# if __name__ == '__main__':
#     app = QApplication(sys.argv)
    
#     demo = SliderWidget()
#     demo.show()

#     sys.exit(app.exec_())