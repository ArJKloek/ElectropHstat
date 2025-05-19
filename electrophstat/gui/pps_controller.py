# electrophstat/gui/pps_controller.py
from PyQt5.QtCore    import QObject, QThread, pyqtSlot
from PyQt5.QtWidgets import QMessageBox
from electrophstat.hardware import discover_power_supply
from electrophstat.hardware.PPSWorker import PPSWorker

class PPSController(QObject):
    """
    Starts a PPSWorker on its own thread, hooks up all of its signals
    back into the MainWindow.
    """
    def __init__(self, window, interval: float = 0.5, reset: bool = True):
        super().__init__(window)
        self.win = window


        # 1) Probe for a real PPS (or get a DummyPPS)
        port = discover_power_supply(reset=reset)
        self.worker = PPSWorker(port, interval, reset=False)

        # 2) Move it into its own thread
        self.thread = QThread(window)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)

        # 3) Hook all signals back to window methods and the pps_connections
        self.worker.voltage_signal.connect(window.pps_connections.update_pps_voltage)
        self.worker.current_signal.connect(window.pps_connections.update_pps_current)
        self.worker.mode_signal.connect(window.pps_connections.update_pps_mode)
        self.worker.limits_signal.connect(window.pps_connections.handle_pps_limits)
        self.worker.disconnected_signal.connect(window.pps_connections.on_pps_disconnect)

        # 4) Start polling
        self.thread.start()

        # 5) fire one initial limits‐read so the dials get properly ranged
        self.worker.emit_limits()

    @pyqtSlot()
    def stop(self):
        """Call this when you want to shut down cleanly."""
        self.worker.stop()
        self.thread.quit()
        self.thread.wait()
