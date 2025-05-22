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
    def __init__(self, window, pps_connections, interval: float = 0.5, reset: bool = True):
        super().__init__(window)
        self.win = window
        self.connections = pps_connections
        self.interval = interval
        self.reset = reset
        self._setup_worker()
        
    def _setup_worker(self):
        # 1) Probe for a real PPS (or get a DummyPPS)
        port = discover_power_supply(reset=self.reset)
        self.pps_worker = PPSWorker(port, self.interval, reset=False)

        self.connections.set_worker(self.pps_worker)

        # 2) Move it into its own thread
        self.thread = QThread(self.win)
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
    
    @pyqtSlot()
    def reconnect_psu(self):
        """Stop the old one and spin up a brand new worker."""
        print(f'Reconnect started')       
        try:
            self.stop()
            print("[PPS] Existing PPSWorker stopped.")
        except Exception as e:
            print(f"[PPS] Error stopping old PPSWorker: {e}")        
        try:
            self._setup_worker()
            print("[PPS] Reconnected.")
            self.win._apply_scaling()
        except Exception as e:
            print(f"[PPS] Reconnect failed: {e}")

    def enable_psu(self):
        """Re‐start polling and re‐enable the UI."""
        if not self.thread.isRunning():
            # restart the worker thread
            self.pps_worker.running = True
            self.thread.start()
        # unfreeze the controls
        self.win.voltageDial.setEnabled(True)
        self.win.currentDial.setEnabled(True)
        self.win.modeToggle  .setEnabled(True)
        self.win.powerButton .setEnabled(True)
        self.win.PowerGroup.setEnabled(True)

    def disable_psu(self):
        """Stop polling and grey‐out the UI."""
        self.pps_worker.stop()
        if self.thread.isRunning():
            self.thread.quit()
            self.thread.wait()
        self.win.voltageDial.setEnabled(False)
        self.win.currentDial.setEnabled(False)
        self.win.modeToggle  .setEnabled(False)
        self.win.powerButton .setEnabled(False)
        self.win.PowerGroup.setEnabled(False)
