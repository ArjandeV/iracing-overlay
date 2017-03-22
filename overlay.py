'''
Created on 7 Feb 2014

@author: Daniel
'''

import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (QApplication)

        
class OverlayWindow(QtWidgets.QWidget):
    
    throttle = 0
    brake = 0
    gear = 0
    rpm = 0
    speed = 0
    displayTach = False
    
    def __init__(self, parent=None):
        super(OverlayWindow, self).__init__(parent)
        self.setWindowTitle('iRacing HUD')
        self.drawers = {}
        self.setGeometry(8,30,1280,720)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
    
    def addDrawer(self, drawer, key):
        self.drawers[key] = drawer
        
    def removeDrawer(self, key):
        del self.drawers[key]
        
    def paintEvent(self, event):
        for key, value in self.drawers.items():
            value.draw(self)
        
  
def main():
    app = QApplication([])
    win = OverlayWindow()
    win.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
    