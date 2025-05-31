from PyQt5.QtWidgets import QDialog, QMessageBox, QVBoxLayout, QPushButton, QSpinBox, QDoubleSpinBox
from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal, QTimer
from PyQt5 import uic
import pyqtgraph as pg
import numpy as np
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
            cfg.atlas.pH.calibration.low = round(pH,2)

        elif calibrationType == "mid":
            cfg.atlas.pH.calibration.mid = round(pH,2)
        else:  # "high"
            cfg.atlas.pH.calibration.high = round(pH,2)

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
        self.cb_cfg_pHstatmode.setCurrentIndex(self.cfg.pHstat.mode)
        self.ds_cfg_pHtarget.setValue(self.cfg.pHstat.target)
        self.ds_cfg_pump_ml.setValue(self.cfg.pHstat.pump.volume)
        self.ds_cfg_pump_time.setValue(self.cfg.pHstat.pump.cycle)
        self.sp_cfg_cooldown.setValue(int(self.cfg.pHstat.pump.cooldown))
        
        #pH calibration settings
        self.ds_cfg_pH_low.setValue(self.cfg.atlas.pH.calibration.low)
        self.ds_cfg_pH_mid.setValue(self.cfg.atlas.pH.calibration.mid)
        self.ds_cfg_pH_high.setValue(self.cfg.atlas.pH.calibration.high)
        #Control and sensor enable / Restart needed
        self.cb_enable_psu.setChecked(self.cfg.psu.enable)
        self.cb_enable_phstat.setChecked(self.cfg.pHstat.enable)
        self.cb_enable_ph_sensor.setChecked(self.cfg.atlas.pH.enable)
        self.cb_enable_temp_sensor.setChecked(self.cfg.atlas.RTD.enable)
        self.cb_enable_turbidity_sensor.setChecked(self.cfg.sensors.turbidity.enable)
        # hookup the debug mode checkbox
        self.cb_debug_mode.setChecked(self.cfg.debug_mode)
        self.cb_debug_PSU.setChecked(self.cfg.psu.debug)
        self.cb_debug_pHstat.setChecked(self.cfg.pHstat.debug)
        self.cb_debug_pH.setChecked(self.cfg.atlas.pH.debug)
        self.cb_debug_RTD.setChecked(self.cfg.atlas.RTD.debug)
        self.cb_debug_turbidity.setChecked(self.cfg.sensors.turbidity.debug)


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
        self.cfg.pHstat.mode                = int(self.cb_cfg_pHstatmode.currentIndex())
        self.cfg.pHstat.target              = round(self.ds_cfg_pHtarget.value(), 2)
        self.cfg.pHstat.pump.volume         = round(self.ds_cfg_pump_ml.value(), 3)
        self.cfg.pHstat.pump.cycle          = round(self.ds_cfg_pump_time.value(), 2)
        self.cfg.pHstat.pump.cooldown       = round(self.sp_cfg_cooldown.value(), 1)
       
        self.cfg.atlas.pH.calibration.low   = round(self.ds_cfg_pH_low.value(), 2)
        self.cfg.atlas.pH.calibration.mid   = round(self.ds_cfg_pH_mid.value(), 2)
        self.cfg.atlas.pH.calibration.high  = round(self.ds_cfg_pH_high.value(), 2)

        self.cfg.psu.enable                 = self.cb_enable_psu.isChecked()
        self.cfg.pHstat.enable              = phstat_enabled
        self.cfg.atlas.pH.enable            = ph_sensor_enabled
        self.cfg.atlas.RTD.enable           = self.cb_enable_temp_sensor.isChecked()
        self.cfg.sensors.turbidity.enable   = self.cb_enable_turbidity_sensor.isChecked()
        
        self.cfg.debug_mode = self.cb_debug_mode.isChecked()
        self.cfg.psu.debug = self.cb_debug_PSU.isChecked()
        self.cfg.pHstat.debug = self.cb_debug_pHstat.isChecked()
        self.cfg.atlas.pH.debug = self.cb_debug_pH.isChecked()
        self.cfg.atlas.RTD.debug = self.cb_debug_RTD.isChecked()
        self.cfg.sensors.turbidity.debug = self.cb_debug_turbidity.isChecked()
        # close dialog with Accepted
        self.accept()
        
class CalibrateTurbidityDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent, flags=Qt.WindowCloseButtonHint)
        uic.loadUi("electrophstat/gui/calibrate_NTU_dialog.ui", self)
        self.win = self.parent()
        # stash your config on the instance
        self.cfg = self.win.config
        self.value = 0

        self.lb_raw_data.setText(f"{self.value:.0f} mV")
        # Turbidity settings voltage
        self.sp_zero_NTU_mV.setValue(self.cfg.sensors.turbidity.calibration.mV.zero)
        self.sp_low_NTU_mV.setValue(self.cfg.sensors.turbidity.calibration.mV.low)
        self.sp_mid_NTU_mV.setValue(self.cfg.sensors.turbidity.calibration.mV.mid)
        self.sp_high_NTU_mV.setValue(self.cfg.sensors.turbidity.calibration.mV.high)
        self.sp_inf_NTU_mV.setValue(self.cfg.sensors.turbidity.calibration.mV.inf)
        # Turbidity settings NTU
        self.sb_low_NTU.setValue(self.cfg.sensors.turbidity.calibration.NTU.low)
        self.sb_mid_NTU.setValue(self.cfg.sensors.turbidity.calibration.NTU.mid)
        self.sb_high_NTU.setValue(self.cfg.sensors.turbidity.calibration.NTU.high)
        
        self._init_plot()

        # hook up Ok/Cancel
        self.buttonBox.accepted.connect(self.on_ok_clicked)
        self.buttonBox.rejected.connect(self.reject)
        self.pb_calc.clicked.connect(self._update_model)
        # make Enter trigger OK
        ok_btn = self.buttonBox.button(self.buttonBox.Ok)
        ok_btn.setDefault(True)
        ok_btn.setAutoDefault(True)

        #self.pb_add_0.clicked.connect(self._add_0_NTU)

        self._update_plot()
        self._init_model(self.win)
        self.pb_add_zero.clicked.connect(lambda: self._copy_data("zero"))
        self.pb_add_low.clicked.connect(lambda: self._copy_data("low"))
        self.pb_add_mid.clicked.connect(lambda: self._copy_data("mid"))
        self.pb_add_high.clicked.connect(lambda: self._copy_data("high"))
        self.pb_add_inf.clicked.connect(lambda: self._copy_data("inf"))
        self.sp_zero_NTU_mV.valueChanged.connect(self._update_plot)
        self.sp_low_NTU_mV.valueChanged.connect(self._update_plot)
        self.sp_mid_NTU_mV.valueChanged.connect(self._update_plot)
        self.sp_high_NTU_mV.valueChanged.connect(self._update_plot)
        self.sp_inf_NTU_mV.valueChanged.connect(self._update_plot)
        self.sb_low_NTU.valueChanged.connect(self._update_plot)
        self.sb_mid_NTU.valueChanged.connect(self._update_plot)
        self.sb_high_NTU.valueChanged.connect(self._update_plot)


        # Add buttons for each SpinBox        
        self._original_calibration = {
            "mV": {
                "zero": self.cfg.sensors.turbidity.calibration.mV.zero,
                "low": self.cfg.sensors.turbidity.calibration.mV.low,
                "mid": self.cfg.sensors.turbidity.calibration.mV.mid,
                "high": self.cfg.sensors.turbidity.calibration.mV.high,
                "inf": self.cfg.sensors.turbidity.calibration.mV.inf,
            },
            "NTU": {
                "low": self.cfg.sensors.turbidity.calibration.NTU.low,
                "mid": self.cfg.sensors.turbidity.calibration.NTU.mid,
                "high": self.cfg.sensors.turbidity.calibration.NTU.high,
            },
            "model_settings": self.win.model_calculator.get_settings()
        }

    def reject(self):
        # Restore model parameters
        self.win.model_calculator.set_settings(self._original_calibration["model_settings"])
        super().reject()

    def _copy_data(self, target):
        """Copy data from one SpinBox to another."""
        add_target = self.findChild(QSpinBox, f"sp_{target}_NTU_mV")
        if add_target:
            add_target.setValue(int(self.value))


    def _init_plot(self):
        # Create a PlotWidget and add it into the placeholder QWidget's layout
        container = self.plotwidget  # this is your placeholder QWidget
        layout = container.layout() or QVBoxLayout(container)
        container.setLayout(layout)

        # Create & configure the plot
        self._plot = pg.PlotWidget(background=self.palette().color(self.backgroundRole()))
        layout.addWidget(self._plot)

        # Create the model curve item
        self._model_curve = self._plot.plot(
            pen=pg.mkPen('g', width=2),  # green for model curve
            name='Model Curve'
        )
        # Create the curve item once and keep it around
        self._curve = self._plot.plot(
            pen=None,
            symbol='o',
            symbolBrush=pg.mkBrush('r'),
        )
        self._plot.setLabel('left', 'Voltage (V)')
        self._plot.setLabel('bottom',   'Turbidity (NTU)')
        
    def _update_plot(self):
        # grab the six points
        Vs = [
            self.sp_zero_NTU_mV.value(),
            self.sp_low_NTU_mV.value(),
            self.sp_mid_NTU_mV.value(),
            self.sp_high_NTU_mV.value(),
            #self.ds_inf_NTU_V.value()
        ]
        NTUs = [
            0.0,
            self.sb_low_NTU.value(),
            self.sb_mid_NTU.value(),
            self.sb_high_NTU.value(),
            #float('inf')  # or some large sentinel you choose
        ]
        # For plotting, replace inf with a large number
        #xs = [n if n != float('inf') else max(n for n in NTUs if n != float('inf'))*1.1 for n in NTUs]
        xs = [n for n in NTUs]    
        ys = [v for v in Vs]
        self._curve.setData(xs, ys)
        self._plot.setLabel('left', 'Voltage (V)')
        self._plot.setLabel('bottom', 'Turbidity (NTU)')
        self._plot.setXRange(0, 8000)  # adjust X range
        self._plot.setYRange(0, 5500)  # adjust Y range

    def _init_model(self, win):
        self.win = win  
        """Initialize the model curve with the current calibration points."""
        self.params_ = self.win.model_calculator.get_settings()["params"]
        print("Model parameters:", self.params_)
        
        # grab the same data arrays used above:
        
        x_model = np.linspace(0, 8000, 200)
        # compute the model curve
        y_model = self.win.model_calculator.predict(x_model)
        
        # update the model curve
        #self._curve.setData(x_model, y_model)
        self._model_curve.setData(x_model, y_model)
        self._model_curve.setPen(pg.mkPen('g', width=2))  
        
           

    def _update_model(self):
        """Fit a degree‐`degree` poly to the calibration points and draw it."""
        # grab the same data arrays used above:
        
        self. params, self.errors = self.win.model_calculator.fit(
            xdata=np.array([0.0, self.sb_low_NTU.value(), self.sb_mid_NTU.value(), self.sb_high_NTU.value()]),
            ydata=np.array([self.sp_zero_NTU_mV.value(), self.sp_low_NTU_mV.value(), self.sp_mid_NTU_mV.value(), self.sp_high_NTU_mV.value()]),
            Y0=self.sp_zero_NTU_mV.value(),
            Plateau=self.sp_inf_NTU_mV.value(),
            p0=(50.0, 0.001, 0.0001),
            bounds=([0.0, 0.0, 0.0], [100.0, np.inf, np.inf])
        )
        
        #print("Fitted parameters:", self.params)
        #print("Fitting errors:", self.errors)
        Kfast = self.params["KFast"]
        Kslow = self.params["KSlow"]
        PercentFast = self.params["PercentFast"]
        #print(f"Percent Fast: {PercentFast:.2f}%, KFast: {Kfast:.4f}, KSlow: {Kslow:.4f}")
        # generate a smooth X axis  
        x_model = np.linspace(0, 8000, 200)
        # compute the model curve
        y_model = self.win.model_calculator.predict(x_model)
        # update the model curve
        #self._curve.setData(x_model, y_model)
        self._model_curve.setData(x_model, y_model)
        self._model_curve.setPen(pg.mkPen('g', width=2))  # green for model curve



    @pyqtSlot()
    def on_ok_clicked(self):
        # read values from the widgets
        # close dialog with Accepted
        self.cfg.sensors.turbidity.calibration.mV.zero = self.sp_zero_NTU_mV.value()
        self.cfg.sensors.turbidity.calibration.mV.low = self.sp_low_NTU_mV.value()
        self.cfg.sensors.turbidity.calibration.mV.mid = self.sp_mid_NTU_mV.value()
        self.cfg.sensors.turbidity.calibration.mV.high = self.sp_high_NTU_mV.value()
        self.cfg.sensors.turbidity.calibration.mV.inf = self.sp_inf_NTU_mV.value()
        self.cfg.sensors.turbidity.calibration.NTU.low = self.sb_low_NTU.value()
        self.cfg.sensors.turbidity.calibration.NTU.mid = self.sb_mid_NTU.value()
        self.cfg.sensors.turbidity.calibration.NTU.high = self.sb_high_NTU.value()

        self.accept()

    def update_raw_label(self, value):
        """Update the raw data label with the latest turbidity_raw value."""
        self.lb_raw_data.setText(f"{value:.0f} mV")
        self.value = value
