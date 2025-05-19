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
        self.win.powerButton.clicked.connect(self.on_checkPPS)
        self.win.setButton.clicked.connect(self.apply_ps_settings)

    def set_worker(self, worker):
        self.pps_worker = worker

    @pyqtSlot(float)
    def update_pps_voltage(self, voltage: float):
        self.win.voltagelabel.setText(f"{voltage:.1f} V")
        
    @pyqtSlot(float)
    def update_pps_current(self, current: float):
        self.win.currentlabel.setText(f"{current:.1f} A")
        
    @pyqtSlot(str)
    def update_pps_mode(self, mode: str):
        self.win.modelabel.setText(mode)

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

        mode = "CC" if self.win.modeToggle.isChecked() else "CV"
        voltage = self.win.voltageDial.value() / 10.0
        current = self.win.currentDial.value() / 10.0

        if mode == "CV":
            self.pps_worker.set_current(self.pps_worker.psu.IMAX)
            self.pps_worker.set_voltage(voltage)
        else:  # "CC"
            self.pps_worker.set_voltage(self.pps_worker.psu.VMAX)
            self.pps_worker.set_current(current)

        print(f"[SET] Mode: {mode}, Voltage: {voltage:.1f} V, Current: {current:.1f} A")

    @pyqtSlot()
    def togglePowerSupply(self):
        print("[CHECK] togglePowerSupply() called")

        if not self.pps_worker:
            QMessageBox.warning(self.win, "PPS Error", "Power supply is not connected.")
            self.win.powerButton.setChecked(False)
            return
        state = self.win.powerButton.isChecked()
        try:
            self.pps_worker.set_output(state)
            print(f"[OUTPUT] Power Supply set to {'ON' if state else 'OFF'}")
        except Exception as e:
            QMessageBox.critical(self.win, "PPS Error", f"Could not set output: {e}")
            self.win.powerButton.setChecked(False)

    @pyqtSlot()
    def on_pps_disconnect(self):
        QMessageBox.warning(self, "PPS Disconnected",
                            "Lost communication with the power supply.")
        self._disable_pps_controls()

    @pyqtSlot()
    def on_checkPPS(self):
        v, a, mode = self.pps_worker.psu.reading()
        QMessageBox.information(self.win, "PPS Status",
            f"Voltage: {v:.2f} V\nCurrent: {a:.2f} A\nMode: {mode}")