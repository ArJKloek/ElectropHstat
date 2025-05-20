from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QDateTimeEdit, QPushButton, 
                            QHBoxLayout, QLabel, QDoubleSpinBox, QLineEdit, QHBoxLayout)
from PyQt5.QtCore import Qt, QDateTime, pyqtSlot, pyqtSignal, QTimer
from PyQt5.QtGui import QCursor
from PyQt5 import uic

import os

class DatePickerDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Date Picker Window')
        self.setGeometry(200, 200, 300, 200)

        layout = QVBoxLayout(self)

        # Create a QDateTimeEdit widget for date selection
        self.date_edit = QDateTimeEdit(self)
        layout.addWidget(self.date_edit)

        # Set the initial date and time to the current date and time
        self.date_edit.setDateTime(QDateTime.currentDateTime())
        # Create a button to confirm date selection
        confirm_button = QPushButton('Confirm Date', self)
        layout.addWidget(confirm_button)
        confirm_button.clicked.connect(self.accept)
    
    def accept(self):
        selected_datetime = self.date_edit.dateTime()
        datetime_str = selected_datetime.toString('yyyy-MM-dd HH:mm:ss')
        #print(date)
        os.system(f'sudo date -s "{datetime_str}"')
        #print(f'Selected Date and Time: {datetime_str}')
        super().accept()  # Close the dialog
    #def getSelectedDate(self):
    #    return self.date_edit.dateTime().toString('yyyy-MM-dd HH:mm:ss')


class CalibratePumpDialog(QDialog):
    select_changed = pyqtSignal(float,float)
    test_pump = pyqtSignal(bool)

    def __init__(self, ml: float, addtime: float):
        super().__init__(flags=Qt.WindowCloseButtonHint)

        self.setWindowTitle('Calibrate pump')
        self.setGeometry(200, 50, 0, 0)

        self._ml = ml
        self._addtime = addtime

        layout = QHBoxLayout(self)
        
        self.setbutton = QPushButton("Set")
        self.setbutton.setStatusTip("Saves all values")
        layout.addWidget(self.setbutton)

        self.testbutton = QPushButton("Test")
        self.testbutton.setStatusTip("Activates pump for inputed time")
        layout.addWidget(self.testbutton)
        
        # Create a Select widget for above or below selection
        mlText = QLabel('ml/inj:')
        layout.addWidget(mlText)
        self.mlwidget = QDoubleSpinBox()
        self.mlwidget.setDecimals(3)
        self.mlwidget.setSingleStep(0.001)
        self.mlwidget.setValue(ml)
        self.mlwidget.setStatusTip("The milimeters added in the selected addition time")
        layout.addWidget(self.mlwidget)
        self.addtimewidget = QDoubleSpinBox()
        self.addtimewidget.setDecimals(2)
        self.addtimewidget.setSingleStep(0.01)
        self.addtimewidget.setValue(self._addtime)
        layout.addWidget(self.addtimewidget)
        sec = QLabel('(s)')
        layout.addWidget(sec)
        
        
        
        self.setbutton.clicked.connect(self.accept)
        self.testbutton.clicked.connect(self.startTest)
    
    @pyqtSlot()
    def startTest(self):
        # disable intil it's done
        self.testbutton.setEnabled(False)
        # tell the world "pump ON"
        self.test_pump.emit(True)

        # Simulate test duration
        QTimer.singleShot(
            int(float(self.addtimewidget.value())*1000), 
            self.endTest)

    def endTest(self):
        self.testbutton.setEnabled(True)
      
    def accept(self):
        newml = self.mlwidget.value()
        newaddtime = self.addtimewidget.value() 
        self.select_changed.emit(newml, newaddtime)
        super().accept()  # Close the dialog

# electrophstat/gui/dialogs.py

class CalibratepHDialog(QDialog):
    calibrate_changed = pyqtSignal(str, float, object)

    def __init__(self, lowpH: float, midpH: float, highpH: float, parent=None):
        super().__init__(parent, flags=Qt.WindowCloseButtonHint)
        uic.loadUi("electrophstat/gui/calibrate_ph_dialog.ui", self)

        # initialize values
        self.sbLowPH.setValue(lowpH)
        self.sbMidPH.setValue(midpH)
        self.sbHighPH.setValue(highpH)

        # connect buttons
        self.btnCalLowPH.clicked .connect(lambda: self.emitCalibration("low",  self.sbLowPH.value()))
        self.btnCalMidPH.clicked .connect(lambda: self.emitCalibration("mid",  self.sbMidPH.value()))
        self.btnCalHighPH.clicked.connect(lambda: self.emitCalibration("high", self.sbHighPH.value()))

    def emitCalibration(self, calibrationType: str, pH: float):
        data = [self.sbLowPH.value(),
                self.sbMidPH.value(),
                self.sbHighPH.value()]
        self.calibrate_changed.emit(calibrationType, pH, data)

    def updateInfo(self, newInfo: str):
        self.leCalStatus.setText(newInfo)
