#!/usr/bin/env python3
from sys import path
path.append("src")

from main_window import MainWindow
from PyQt5.QtWidgets import QApplication

app = QApplication([])
mainwindow = MainWindow()
mainwindow.show()
app.exec_()
