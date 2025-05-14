# scripts/ph_sensor_worker.py  (new file)
from PyQt5.QtCore import QObject, pyqtSignal
import time

class pHSensorWorker(QObject):
    value_signal = pyqtSignal(float)
    disconnected_signal = pyqtSignal()

    def __init__(self, sensor, interval: float = 1.0):
        super().__init__()
        self.sensor = sensor          # AtlasSensor
        self.interval = interval
        self.running = True
        self.fail = 0

    def run(self):
        while self.running:
            try:
                self.value_signal.emit(self.sensor.read())
                self.fail = 0
            except Exception as e:
                print("pH read error:", e)
                self.fail += 1
                if self.fail >= 3:
                    self.disconnected_signal.emit()
                    self.running = False
                    break
            time.sleep(self.interval)

    def stop(self):
        self.running = False
