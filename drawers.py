'''
Created on 8 Mar 2014

@author: Daniel
'''
from state import State
from PyQt5 import QtGui, QtCore
import math
import constants
import logging
import irsdk
import random

def strFromTime(time, decimal_places = 2):
    time = float(time)
    multiplier = pow(10, decimal_places)
    #print(multiplier, decimal_places)
    s = int(time)
    ms = int((time - s) * multiplier)
    m, s = divmod(s, 60)
    if m > 0:
        result = '{}:{:02d}.{:03d}'.format(m, s, ms)
    else:
        result = '{}.{:03d}'.format(s, ms)
    return result

        
class QualifyingTimeDrawer:
    def __init__(self, ir, state, qual_time): 
        self.ir = ir
        self.state = state
        self.outlap = self.ir['CarIdxLap'][self.state.cam_car_idx]
        self.start_time = -1
        self.voffset = 600
        
        if(len(qual_time) > 0):
            self.lap_time = float(qual_time)
        else:
            self.lap_time = -1

    def draw(self, widget):
        self.paintBackground(widget)
        self.paintText(widget)
        
    def paintBackground(self, widget):
        lap = self.ir['CarIdxLap'][self.state.cam_car_idx]
        if lap == self.outlap:
            color = constants.Color.GREY_TRANSPARENT
        elif lap == self.outlap + 2:
            color = constants.Color.GREEN
        else:
            color = constants.Color.GREY_TRANSPARENT
            
        p = QtGui.QPainter()
        p.begin(widget)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        p.shear(math.radians(-10), 0)
        p.fillRect(130, self.voffset, 240, 25, color)
        p.end()
        
    def paintText(self, widget):
        lap = self.ir['CarIdxLap'][self.state.cam_car_idx]
        if lap == self.outlap:
            str = '-.---'
        elif lap == self.outlap + 2:
            if self.lap_time == -1:
                self.lap_time = self.state.drivers[self.state.my_car_idx]['position_info']['FastestTime'] # self.state.cur_session_time - self.start_time
                
#             time = self.state.drivers[self.state.my_car_idx]['position_info']['FastestTime']
            str = strFromTime(self.lap_time, decimal_places=3)
#             self.state.drivers[self.state.my_car_idx]['position_info']['FastestTime']
        else:
            if self.start_time == -1:
                self.start_time = self.state.cur_session_time
            time = self.state.cur_session_time - self.start_time
            str = strFromTime(time, decimal_places=3)
        
        white_color = constants.Color.WHITE
        pen = QtGui.QPen()
        pen.setColor(white_color)
        p = QtGui.QPainter()
        p.begin(widget)
        p.setPen(pen)        
        p.setRenderHint(QtGui.QPainter.TextAntialiasing)
        p.setFont(QtGui.QFont('Calibri', 14, QtGui.QFont.Bold))
        p.drawText(104,self.voffset,240,25, QtCore.Qt.AlignCenter, str)
        pen.setColor(QtGui.QColor(255, 255, 255, 148))
        p.setPen(pen) 
        p.drawText(34,self.voffset,230,25, QtCore.Qt.AlignLeft, "Lap time:")
        p.end()
        
class InputsDrawer:
    def __init__(self, ir, state):
        self.ir = ir
        self.state = state
        self.voffset = 600
        
    def draw(self, widget):
        self.paintBackground(widget)
        self.paintRelativeText(widget)
        
    def paintBackground(self, widget):
        offset = 100
        voffset = self.voffset
        p = QtGui.QPainter()
        p.begin(widget)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        p.shear(math.radians(-10), 0)
        # speed
        p.fillRect(30+offset, 30+voffset, 100, 55, constants.Color.GREY_TRANSPARENT)
        # throttle 
        p.fillRect(135+offset, 30+voffset, 135, 25, constants.Color.GREY_TRANSPARENT)
        p.fillRect(135+offset, 30+voffset, 135*self.ir['Throttle'], 25, constants.Color.GREEN)
        # brake
        p.fillRect(135+offset, 60+voffset, 135, 25, constants.Color.GREY_TRANSPARENT)
        p.fillRect(135+offset, 60+voffset, 135*self.ir['Brake'], 25, constants.Color.RED)
        # gear
        for i in range(0, 7):
            if i == (self.ir['Gear'] + 1):
                color = constants.Color.GREEN
            else:
                color = constants.Color.GREY_TRANSPARENT
            p.fillRect(30+offset+35*i, 90+voffset, 30, 15, color)
            
        p.end()
        
    def paintRelativeText(self, widget):
        voffset = self.voffset
        offset = 100
        grey_color = constants.Color.GREY_TRANSPARENT
        yellow_color = constants.Color.YELLOW
        white_color = constants.Color.WHITE
        pen = QtGui.QPen()
        pen.setColor(white_color)
        p = QtGui.QPainter()
        p.begin(widget)
        p.setPen(pen)
        p.setRenderHint(QtGui.QPainter.TextAntialiasing)
        # speed
        speed = int(round(self.ir['Speed'] * 2.23693629))
        p.setFont(QtGui.QFont('Calibri', 30, QtGui.QFont.Bold))
        p.drawText(-80+offset,34+voffset,72,55, QtCore.Qt.AlignRight, str(speed))
        #p.drawText(55+offset,55+voffset,155,155, QtCore.Qt.AlignRight, str(speed))
        # throttle
        pen.setColor(QtGui.QColor(255, 255, 255, 148))
        p.setPen(pen)
        p.setFont(QtGui.QFont('Calibri', 12, QtGui.QFont.Bold))
        p.drawText(30+offset,33+voffset,135,25, QtCore.Qt.AlignLeft, 'THROTTLE')
        # brake
        p.drawText(30+offset,63+voffset,135,25, QtCore.Qt.AlignLeft, 'BRAKE')
        # gear
        gear = self.ir['Gear'] + 1
        gear_strs = ('R', 'N', '1', '2', '3', '4', '5')
        p.setFont(QtGui.QFont('Calibri', 10, QtGui.QFont.Bold))
        for i in range(0, len(gear_strs)):
            if i == gear:
                color = white_color
            else:
                color = yellow_color
            pen.setColor(color)
            p.setPen(pen)
            width = 210/len(gear_strs)
            p.drawText(0+((width+5)*i),90+voffset,width,15, QtCore.Qt.AlignCenter, gear_strs[i])
        p.end()
        # mph
        p = QtGui.QPainter()
        p.begin(widget)
        p.setRenderHint(QtGui.QPainter.TextAntialiasing)
        p.rotate(-90)
        pen = QtGui.QPen()
        pen.setColor(white_color)
        p.setPen(pen)
        p.setFont(QtGui.QFont('Calibri', 10, QtGui.QFont.Bold))
        p.drawText(-73+(voffset*-1),95,135,25, QtCore.Qt.AlignLeft, 'MPH')
        p.end()
    
class TachDrawer:
    
    def __init__(self, ir, state):
        self.ir = ir
        self.state = state
        
        self.tach_bg_pm = QtGui.QPixmap()
        self.tach_bg_pm.load('images/tach-back.png')
        self.tach_fg_pm = QtGui.QPixmap()
        self.tach_fg_pm.load('images/tach-fore.png')
        
    def draw(self, widget):
        p = QtGui.QPainter()
        p.begin(widget)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        # draw bg
        p.drawPixmap(50,50,300,300,self.tach_bg_pm)
        
        # draw throttle bar
        tw = round(self.ir['Throttle'] * 126)
        p.fillRect(137,260,tw,25,QtGui.QColor(0,255,0,255))
        
        # draw brake bar
        bw = round(self.ir['Brake'] * 126)
        p.fillRect(137,292,bw,25,QtGui.QColor(255,0,0,255))
        
        # draw rpm arc
        pc = (self.ir['RPM'] - 1000) / 6000
        ra = pc * -270
        pen = QtGui.QPen()
        pen.setColor(QtGui.QColor(0,128,255,255))
        pen.setWidth(10)
        pen.setCapStyle(QtCore.Qt.FlatCap)
        p.setPen(pen)
        p.drawArc(85,83,230,230,(225*16),(ra*16))
        
        # draw foreground
        p.drawPixmap(50,50,300,300,self.tach_fg_pm)
        
        # draw speed
        maxSpeed = 135
        speed = round(self.ir['Speed'] * 2.23693629)
        pen.setColor(self.colorForPercent(speed/maxSpeed))
        p.setPen(pen)
        p.setFont(QtGui.QFont('Arial', 54))
        p.drawText(50,90,300,100, QtCore.Qt.AlignCenter, str(speed))
        
        # draw gear
        pen.setColor(QtGui.QColor(255,255,255,255))
        p.setPen(pen)
        p.setFont(QtGui.QFont('Arial', 40))
        p.drawText(50,176,300,100, QtCore.Qt.AlignCenter, self.gear())
        
        p.end()
        
    def gear(self):
        raw_gear = self.ir['Gear']
        if raw_gear == -1:
            return 'R'
        elif raw_gear == 0:
            return 'N'
        else:
            return str(raw_gear)
        
    def colorForPercent(self, percent):
        if percent < 0.4:
            return QtGui.QColor(0,255,0,255)
        elif percent < 0.6:
            dif = 0.6 - percent
            pc = 1-(dif/0.2)
            return QtGui.QColor(round(pc * 255),255,0,255)
        elif percent < 0.8:
            return QtGui.QColor(255,255,0,255)
        elif percent < 0.95:
            dif = 0.95 - percent
            pc = (dif/0.15)
            return QtGui.QColor(255,round(pc * 255),0,255)
        else:
            return QtGui.QColor(255,0,0,255)
