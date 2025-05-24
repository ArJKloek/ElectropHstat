from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QDateTimeEdit, QPushButton, 
                            QHBoxLayout, QLabel, QDoubleSpinBox, QLineEdit, QHBoxLayout)
from PyQt5.QtCore import Qt, QDateTime, pyqtSlot, pyqtSignal, QTimer
from PyQt5.QtGui import QCursor
from PyQt5 import uic

import os

class DatePickerDialog(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi("electrophstat/gui/date_time_dialog.ui", self)
        
        self.btnSetDateTime.clicked.connect(self.accept)
    
    def accept(self):
        selected_datetime = self.dateTimeEdit.dateTime()
        datetime_str = selected_datetime.toString('yyyy-MM-dd HH:mm:ss')
        #print(date)
        os.system(f'sudo date -s "{datetime_str}"')
        #print(f'Selected Date and Time: {datetime_str}')
        super().accept()  # Close the dialog
    #def getSelectedDate(self):
    #    return self.date_edit.dateTime().toString('yyyy-MM-dd HH:mm:ss')


class CalibratePumpDialog(QDialog):
    select_changed = pyqtSignal(float,float)
    test_pump = pyqtSignal(bool,float)

    def __init__(self, ml: float, pump_cycle_duration_s: float, parent=None):
        super().__init__(parent, flags=Qt.WindowCloseButtonHint)
        uic.loadUi("electrophstat/gui/calibrate_pump_dialog.ui", self)

        self._ml = ml
        self._pump_cycle_duration_s = pump_cycle_duration_s

        self.dsMlperCycle.setValue(self._ml)
        self.dsTimeInterval.setValue(self._pump_cycle_duration_s)
        
        self.btnSet.clicked.connect(self.accept)
        self.btnTest.clicked.connect(self.startTest)
    
    @pyqtSlot()
    def startTest(self):
        # disable intil it's done
        self.btnTest.setEnabled(False)
        duration = self.dsTimeInterval.value()
        # tell the world "pump ON"
        self.test_pump.emit(True, duration)

        # Simulate test duration
        QTimer.singleShot(
            int(float(self.dsTimeInterval.value())*1000), 
            self.endTest)

    def endTest(self):
        self.btnTest.setEnabled(True)
      
    def accept(self):
         # 1) emit the usual select_changed signal for any existing logic
        new_ml       = float(self.dsMlperCycle.value())
        new_duration = float(self.dsTimeInterval.value())
        self.select_changed.emit(round(new_ml,3), round(new_duration,2))

        # 2) write immediately into MainWindow.config
        mw = self.parent()  # type: MainWindow
        if mw is not None and hasattr(mw, "config"):
            # these keys must match what you named in DEFAULT_CONFIG
            mw.config.pump_volume_per_cycle_ml  = round(new_ml,3)
            mw.config.pump_cycle_duration_s     = round(new_duration,2)
        # 3) close the dialog
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
                # grab main window & its Config
        mw = self.parent()
        cfg = mw.config

        # update the JSON‐backed setting immediately
        if calibrationType == "low":
            cfg.pH_calibration_low = round(pH,2)
        elif calibrationType == "mid":
            cfg.pH_calibration_mid = round(pH,2)
        else:  # "high"
            cfg.pH_calibration_high = round(pH,2)

        data = [self.sbLowPH.value(),
                self.sbMidPH.value(),
                self.sbHighPH.value()]
        self.calibrate_changed.emit(calibrationType, round(pH,2), data)
    
    def updateInfo(self, newInfo: str):
        self.leCalStatus.setText(newInfo)

class SettingsDialog(QDialog):
    
    def __init__(self, parent=None):
        super().__init__(parent, flags=Qt.WindowCloseButtonHint)
        uic.loadUi("electrophstat/gui/settings_dialog.ui", self)
        mw = self.parent()
        cfg = mw.config
        self.cb_enable_psu.setChecked(bool(cfg.enable_psu))

        self.buttonBox.accept(self.setSettings)
    
    def setSettings(self):
       print(f'Settings accepted')
    