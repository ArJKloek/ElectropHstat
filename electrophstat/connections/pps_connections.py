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

        
    @pyqtSlot(float)
    def update_pps_voltage(self, voltage: float):
        self.win.voltagelabel.setText(f"{voltage:.1f} V")
        self.win.voltageDial.setValue(int(voltage * 10))

    @pyqtSlot(float)
    def update_pps_current(self, current: float):
        self.win.currentlabel.setText(f"{current:.1f} A")
        self.win.currentDial.setValue(int(current * 10))

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
    def on_pps_disconnect(self):
        QMessageBox.warning(self, "PPS Disconnected",
                            "Lost communication with the power supply.")
        self._disable_pps_controls()
