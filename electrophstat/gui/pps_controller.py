# electrophstat/gui/pps_controller.py
from PyQt5.QtCore    import QObject, QThread, pyqtSlot
from PyQt5.QtWidgets import QMessageBox
from electrophstat.hardware import discover_power_supply
from electrophstat.workers.pps_worker import PPSWorker

class PPSController(QObject):
    """
    Starts a PPSWorker on its own thread, hooks up all of its signals
    back into the MainWindow.
    """
    def __init__(self, window, pps_connections, interval: float = 0.5, reset: bool = True):
        super().__init__(window)
        self.win = window
        self.connections = pps_connections

        # 1) Probe for a real PPS (or get a DummyPPS)
        port = discover_power_supply(reset=reset)
        self.pps_worker = PPSWorker(port, interval, reset=False)

        self.connections.set_worker(self.pps_worker)

        # 2) Move it into its own thread
        self.thread = QThread(window)
        self.pps_worker.moveToThread(self.thread)
        self.thread.started.connect(self.pps_worker.run)

        # 3) Hook all signals back to window methods and the pps_connections
        self.pps_worker.voltage_signal.connect(self.connections.update_pps_voltage)
        self.pps_worker.current_signal.connect(self.connections.update_pps_current)
        self.pps_worker.mode_signal.connect(self.connections.update_pps_mode)
        self.pps_worker.limits_signal.connect(self.connections.handle_pps_limits)
        self.pps_worker.disconnected_signal.connect(self.connections.on_pps_disconnect)

        # 4) Start polling
        self.thread.start()

        # 5) fire one initial limits‐read so the dials get properly ranged
        self.pps_worker.emit_limits()

    @pyqtSlot()
    def stop(self):
        """Call this when you want to shut down cleanly."""
        self.pps_worker.stop()
        self.thread.quit()
        self.thread.wait()
