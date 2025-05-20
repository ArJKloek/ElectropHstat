# scripts/ph_sensor_worker.py
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
import time

class pHstatWorker(QObject):
    action_signal = pyqtSignal(bool, bool)  # pump_on, status

    def __init__(self, control_loop, get_pH_callable, interval=1.0):
        super().__init__()
        self.control_loop = control_loop
        self.get_pH        = get_pH_callable
        self.interval      = interval
        self.running       = True

    @pyqtSlot()
    def run(self):
        while self.running:
            val = self.get_pH()
            action = self.control_loop.process(val)
            self.action_signal.emit(action.pump_on, action.status)
            time.sleep(self.interval)

    def stop(self):
        self.running = False
