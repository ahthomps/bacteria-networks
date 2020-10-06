from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QSlider, QLCDNumber, QLabel)
import sys
from PyQt5.QtCore import Qt

class SliderWidget(QWidget):

    def __init__(self):
        QWidget.__init__(self)
        
        self.resize(600,600)
        self.setWindowTitle('Fine Tune Image Settings')
        
        self.num_erosions = 4
        self.num_dilations = 4
        self.binary_threshhold = 50
        
        self.l1 = QLabel("# Erosions")
        self.l1.setAlignment(Qt.AlignCenter)
        self.erosionsLCD = QLCDNumber()
        self.s1 = QSlider(Qt.Horizontal)
        self.s1.valueChanged.connect(self.updateErosions)
        self.s1.setMinimum(0)
        self.s1.setMaximum(20)
        self.s1.setTickPosition(QSlider.TicksBelow)
        self.s1.setValue(self.num_erosions)
        
        self.l2 = QLabel("# Dialations")
        self.l2.setAlignment(Qt.AlignCenter)
        self.dialationsLCD = QLCDNumber()
        self.s2 = QSlider(Qt.Horizontal)
        self.s2.valueChanged.connect(self.updateDialations)
        self.s2.setMinimum(0)
        self.s2.setMaximum(20)
        self.s2.setTickPosition(QSlider.TicksBelow)
        self.s2.setValue(self.num_dilations)

        self.l3 = QLabel("Binary Threshhold")
        self.l3.setAlignment(Qt.AlignCenter)
        self.threshholdLCD = QLCDNumber()
        self.s3 = QSlider(Qt.Horizontal)
        self.s3.valueChanged.connect(self.updateThreshhold)
        self.s3.setMinimum(0)
        self.s3.setMaximum(100)
        self.s3.setValue(self.binary_threshhold)

        layout = QVBoxLayout()

        layout.addWidget(self.l1)
        layout.addWidget(self.erosionsLCD)
        layout.addWidget(self.s1)

        layout.addWidget(self.l2)
        layout.addWidget(self.dialationsLCD)
        layout.addWidget(self.s2)

        layout.addWidget(self.l3)
        layout.addWidget(self.threshholdLCD)
        layout.addWidget(self.s3)

        self.setLayout(layout)

    def updateErosions(self, event):
        self.erosionsLCD.display(event)

    def updateDialations(self, event):
        self.dialationsLCD.display(event)

    def updateThreshhold(self, event):
        self.threshholdLCD.display(event/100)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    demo = SliderWidget()
    demo.show()

    sys.exit(app.exec_())