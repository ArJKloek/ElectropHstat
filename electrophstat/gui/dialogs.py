from PyQt5.QtWidgets import QDialog, QMessageBox
from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal, QTimer
from PyQt5 import uic
import pyqtgraph as pg
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

        # stash your config on the instance
        self.cfg = self.parent().config

        # pHstat settings
        self.cb_cfg_pHstatmode.setCurrentIndex(self.cfg.pHstat_mode)
        self.ds_cfg_pHtarget.setValue(self.cfg.pH_target)
        self.ds_cfg_pump_ml.setValue(self.cfg.pump_volume_per_cycle_ml)
        self.ds_cfg_pump_time.setValue(self.cfg.pump_cycle_duration_s)
        self.sp_cfg_cooldown.setValue(self.cfg.pump_cooldown_duration_s)
        
        #pH calibration settings
        self.ds_cfg_pH_low.setValue(self.cfg.pH_calibration_low)
        self.ds_cfg_pH_mid.setValue(self.cfg.pH_calibration_mid)
        self.ds_cfg_pH_high.setValue(self.cfg.pH_calibration_high)
        #Control and sensor enable / Restart needed
        self.cb_enable_psu.setChecked(self.cfg.enable_psu)
        self.cb_enable_phstat.setChecked(self.cfg.enable_phstat)
        self.cb_enable_ph_sensor.setChecked(self.cfg.enable_ph_sensor)
        self.cb_enable_temp_sensor.setChecked(self.cfg.enable_temp_sensor)
        self.cb_enable_turbidity_sensor.setChecked(self.cfg.enable_turbidity_sensor)

        # hook up Ok/Cancel
        self.buttonBox.accepted.connect(self.on_ok_clicked)
        self.buttonBox.rejected.connect(self.reject)

        # make Enter trigger OK
        ok_btn = self.buttonBox.button(self.buttonBox.Ok)
        ok_btn.setDefault(True)
        ok_btn.setAutoDefault(True)
    
    @pyqtSlot()
    def on_ok_clicked(self):
        # read values from the widgets
        phstat_enabled = self.cb_enable_phstat.isChecked()
        ph_sensor_enabled = self.cb_enable_ph_sensor.isChecked()

        if phstat_enabled and not ph_sensor_enabled:
            # show an OK/Cancel box
            reply = QMessageBox.warning(
                self,
                "Invalid Configuration",
                "pH Stat mode requires the pH sensor to be enabled.\n\n"
                "Press OK to enable the pH sensor, or Cancel to go back and adjust.",
                QMessageBox.Ok   | QMessageBox.Cancel,
                QMessageBox.Ok
            )
            if reply == QMessageBox.Cancel:
                return
                # user chose OK → auto–enable the pH sensor checkbox
            self.cb_enable_ph_sensor.setChecked(True)
            
        # read actual checked state, write into config
        self.cfg.pHstat_mode                = int(self.cb_cfg_pHstatmode.currentIndex())
        self.cfg.pH_target                  = round(self.ds_cfg_pHtarget.value(), 2)
        self.cfg.pump_volume_per_cycle_ml   = round(self.ds_cfg_pump_ml.value(), 3)
        self.cfg.pump_cycle_duration_s      = round(self.ds_cfg_pump_time.value(), 2)
        self.cfg.pump_cooldown_duration_s   = round(self.sp_cfg_cooldown.value(), 1)
       
        self.cfg.pH_calibration_low         = round(self.ds_cfg_pH_low.value(), 2)
        self.cfg.pH_calibration_mid         = round(self.ds_cfg_pH_mid.value(), 2)
        self.cfg.pH_calibration_high        = round(self.ds_cfg_pH_high.value(), 2)

        self.cfg.enable_psu                 = self.cb_enable_psu.isChecked()
        self.cfg.enable_phstat              = phstat_enabled
        self.cfg.enable_ph_sensor           = ph_sensor_enabled
        self.cfg.enable_temp_sensor         = self.cb_enable_temp_sensor.isChecked()
        self.cfg.enable_turbidity_sensor    = self.cb_enable_turbidity_sensor.isChecked()
        # close dialog with Accepted
        self.accept()
        
class CalibrateTurbidityDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent, flags=Qt.WindowCloseButtonHint)
        uic.loadUi("electrophstat/gui/calibrate_NTU_dialog.ui", self)
        win = self.parent()
        # stash your config on the instance
        self.cfg = win.config
 
        # Turbidity settings voltage
        self.ds_0_NTU_V.setValue(self.cfg.NTU_V_calibration_0)
        self.ds_low_NTU_V.setValue(self.cfg.NTU_V_calibration_low)
        self.ds_mid_NTU_V.setValue(self.cfg.NTU_V_calibration_mid)
        self.ds_high_NTU_V.setValue(self.cfg.NTU_V_calibration_high)
        self.ds_inf_NTU_V.setValue(self.cfg.NTU_V_calibration_inf)
        # Turbidity settings NTU
        self.sb_low_NTU.setValue(self.cfg.NTU_calibration_low)
        self.sb_mid_NTU.setValue(self.cfg.NTU_calibration_mid)
        self.sb_high_NTU.setValue(self.cfg.NTU_calibration_high)
        

        # hook up Ok/Cancel
        self.buttonBox.accepted.connect(self.on_ok_clicked)
        self.buttonBox.rejected.connect(self.reject)

        # make Enter trigger OK
        ok_btn = self.buttonBox.button(self.buttonBox.Ok)
        ok_btn.setDefault(True)
        ok_btn.setAutoDefault(True)
    #def on_calc_clicked(self):

    def add_plot(self):
        #

    @pyqtSlot()
    def on_ok_clicked(self):
        # read values from the widgets
        # close dialog with Accepted
        self.accept()
        
     