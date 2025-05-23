# electrophstat/gui/phstat_controller.py
from PyQt5.QtCore    import QObject, pyqtSlot
from PyQt5.QtWidgets import QMessageBox 

class PPSConnections(QObject):
    """
    Encapsulates the logic for PPS controllers.
    """
    def __init__(self, window):
        super().__init__(window)
        self.win = window
        self.pps_worker = None
        self.win.powerButton.clicked.connect(self.togglePowerSupply)
        self.win.setButton.clicked.connect(self.apply_ps_settings)
        self.win.actionEnable_PSU_control.toggled.connect(self.on_toggle_psu)
        self.win.reconnect_pps_action.triggered.connect(self.reconnect_PSU)

    def set_worker(self, worker):
        self.pps_worker = worker
    
    @pyqtSlot()
    def reconnect_PSU(self):
        self.win.pps_ctrl.reconnect_psu()
    
    @pyqtSlot(float)
    def update_pps_voltage(self, voltage: float):
        self.win.voltagelabel.setText(f"{voltage:.1f} V")
        self.win.valueData["voltage"] = round(voltage,2)
        
    @pyqtSlot(float)
    def update_pps_current(self, current: float):
        self.win.currentlabel.setText(f"{current:.1f} A")
        self.win.valueData["current"] = round(current,2)
        
    @pyqtSlot(str)
    def update_pps_mode(self, mode: str):
        self.win.modelabel.setText(mode)
        self.win.valueData["mode"] = mode

    @pyqtSlot(float, float, float, str)
    def handle_pps_limits(self, vmax, imax, vmin, model):
        # set dial ranges, etc.
        self.win.voltageDial.setMinimum(int(vmin * 10))
        self.win.voltageDial.setMaximum(int(vmax * 10))
        self.win.currentDial.setMaximum(int(imax * 10))
        # … any other UI work …
    
    @pyqtSlot()
    def apply_ps_settings(self):
        if not self.pps_worker:
            print("[WARNING] PPS worker not initialized.")
            return
        voltage = self.win.voltageDial.value() / 10.0
        current = self.win.currentDial.value() / 10.0
        self.pps_worker.set_voltage(voltage)
        self.pps_worker.set_current(current)

    @pyqtSlot(bool)
    def togglePowerSupply(self, checked:bool):
        print("[CHECK] togglePowerSupply() called")

        if not self.pps_worker:
            QMessageBox.warning(self.win, "PPS Error", "Power supply is not connected.")
            self.win.powerButton.setChecked(False)
            return
        state = self.win.powerButton.isChecked()
        try:
            self.pps_worker.set_output(checked)
            print(f"[OUTPUT] Power Supply set to {'ON' if state else 'OFF'}")
        except Exception as e:
            QMessageBox.critical(self.win, "PPS Error", f"Could not set output: {e}")
            self.win.powerButton.setChecked(False)

    @pyqtSlot()
    def on_pps_disconnect(self):
        QMessageBox.warning(self.win, "PPS Disconnected",
                            "Lost communication with the power supply.")
        self._disable_pps_controls()

    @pyqtSlot()
    def on_checkPPS(self):
        if not self.pps_worker:
            QMessageBox.warning(self.win, "PPS", "Not connected.")
            return

        try:
            # always exists on both real and dummy
            voltage, current, mode = self.pps_worker.psu.read_output()
        except Exception as e:
            QMessageBox.critical(self.win, "PPS Error",
                                f"Failed to read PPS: {e}")
            return

        msg = f"Voltage: {voltage:.2f} V\nCurrent: {current:.2f} A"
        if mode is not None:
            msg += f"\nMode: {mode}"
        QMessageBox.information(self.win, "PPS Status", msg)
    
    @pyqtSlot()
    def _disable_pps_controls(self):
        """Gray-out all PPS widgets and make them inert."""
        gray = "color: gray;"
        for lbl in (self.win.voltagelabel, self.win.currentlabel, self.win.modelabel):
            lbl.setText("N/A" if lbl is self.win.modelabel else lbl.text().split()[0] + ": N/A")
            lbl.setStyleSheet(gray)

        for w in (self.win.voltageDial, self.win.currentDial,
                self.win.setButton, self.win.powerButton):
            w.setDisabled(True)
        self.win.reconnect_pps_action.setEnabled(True)

    
    @pyqtSlot()
    def _enable_pps_controls(self):
        """Undo the gray-out – called after handle_pps_limits()."""
        for lbl in (self.win.voltagelabel, self.win.currentlabel, self.win.modelabel):
            lbl.setStyleSheet("color: black;")
        for w in (self.win.voltageDial, self.win.currentDial,
                self.win.setButton, self.win.powerButton):
            w.setEnabled(True)
        self.win.reconnect_pps_action.setEnabled(False)

    @pyqtSlot(bool)
    def on_toggle_psu(self, checked):
        print(checked)
        if checked:
            print("PSU control & logging ENABLED")
            self._enable_pps_controls()
            self.win.logging_ctrl.enable_logging(["voltage","current","coulomb"])
            self.win.graph_ctrl.set_psu_enabled(True)
            self.win.PowerGroup.setCurrentIndex(0)

        else:
            print("PSU control & logging DISABLED")
            self._disable_pps_controls()
            self.win.logging_ctrl.disable_logging(["voltage","current","coulomb"])
            self.win.graph_ctrl.set_psu_enabled(False)
            self.win.PowerGroup.setCurrentIndex(1)

     