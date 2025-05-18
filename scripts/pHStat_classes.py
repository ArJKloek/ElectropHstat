from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QDateTimeEdit, QPushButton, 
                             QWidget, QHBoxLayout, QSpinBox, QLabel, QComboBox, QDoubleSpinBox, QLineEdit, QCheckBox, QHBoxLayout, QSizePolicy)
from PyQt5.QtCore import QEvent, Qt, QDateTime, pyqtSignal, QObject, QTimer, QSize, QPoint, QRectF, QPointF, QRect, pyqtSlot as Slot, pyqtProperty as Property
from PyQt5.QtGui import QPainter, QColor, QFont, QFontMetrics, QCursor, QPen, QPaintEvent, QBrush
#from scripts.pHStat_worker import StatWorker
import os
import math
import time
from datetime import datetime



       


class pumpControl(QObject):
    pumpActivated = pyqtSignal(bool)
    pumpDeactivated = pyqtSignal(bool)
    cooldownEnded = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.test = False
        self.active_timer = QTimer(self)
        self.active_timer.setSingleShot(True)
        self.active_timer.timeout.connect(self.deactivate_feature)

        self.cooldown_timer = QTimer(self)
        self.cooldown_timer.setSingleShot(True)
        self.cooldown_timer.timeout.connect(self.end_cooldown)

    def activate_feature(self, duration_ms, cooldown_ms, test):
        self.test = test
        if not self.active_timer.isActive() and not self.cooldown_timer.isActive():
            self.pumpActivated.emit(self.test)
            
            #PumpON
            self.active_timer.start(duration_ms)
            self.cooldown_duration = cooldown_ms

    def deactivate_feature(self):
        self.pumpDeactivated.emit(self.test)
        #PumpOFF
        self.cooldown_timer.start(self.cooldown_duration)

    def end_cooldown(self):
        self.cooldownEnded.emit()



class ClickableLabel(QLabel):
    clicked = pyqtSignal()  # Define a signal named 'clicked'
    
    def __init__(self, *args, **kwargs):
        super(ClickableLabel, self).__init__(*args, **kwargs)
        self.setMouseTracking(True)
    
    def enterEvent(self, event):
        #Change text color when mouse enters the label
        self.setStyleSheet("color: lightgray;")
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        # Revert text color when mouse leaves the label
        self.setStyleSheet("color: black;")
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        self.clicked.emit()  # Emit the 'clicked' signal