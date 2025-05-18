# controllers/pps_controller.py
from PyQt5.QtCore    import QObject, pyqtSlot
from PyQt5.QtWidgets import QMessageBox

class PPSController(QObject):
    def __init__(self, window):
        super().__init__(window)
        self.win = window

        # wire up the toggle button
        self.win.powerButton.clicked.connect(self.toggle_output)

        # wire up the “apply” button
        self.win.setButton.clicked.connect(self.apply_ps_settings)

        # you’ll wire up pps disconnect once you have a ppsWorker
        # e.g. in MainWindow after creating the worker:
        # self.ppsWorker.disconnected_signal.connect(self.pps_ctrl.on_pps_disconnect)

    @pyqtSlot(bool)
    def toggle_output(self, checked: bool):
        pps = getattr(self.win, "ppsWorker", None)
        if not pps:
            return
        try:
            pps.set_output(checked)
        except Exception as e:
            print(f"[PPS] Could not change output: {e}")
            self.win.powerButton.setChecked(False)

    @pyqtSlot()
    def on_pps_disconnect(self):
        print("[PPS] Lost connection — disabling controls.")
        self.win._disable_pps_controls()
        self.win.powerButton.setChecked(False)
        self.win._stop_pps()
        self.win.reconnect_pps_action.setEnabled(True)
        QMessageBox.warning(
            self.win,
            "Power Supply Disconnected",
            "The power supply was disconnected."
        )

    @pyqtSlot()
    def apply_ps_settings(self):
        pps = getattr(self.win, "ppsWorker", None)
        if not pps:
            return

        mode = "CC" if self.win.modeToggle.isChecked() else "CV"
        voltage = self.win.voltageDial.value() / 10.0
        current = self.win.currentDial.value() / 10.0

        # apply settings in the correct order
        if mode == "CV":
            pps.set_current(pps.psu.IMAX)
            pps.set_voltage(voltage)
        else:
            pps.set_voltage(pps.psu.VMAX)
            pps.set_current(current)

        print(f"[SET] Mode: {mode}, Voltage: {voltage:.1f} V, Current: {current:.1f} A")
        # if you have a logger on the window
        if getattr(self.win, "logger", None):
            self.win.logger.setting_change(voltage, current, mode)
