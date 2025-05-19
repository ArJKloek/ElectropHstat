# electrophstat/sensors/atlas_worker.py

import time
from PyQt5.QtCore import QObject, pyqtSignal

class AtlasSensorWorker(QObject):
    """
    A generic background worker for any AtlasSensor (pH, RTD, ORP, etc).
    
    Emits:
      • data_signal(sensor_name: str, value: float)
      • disconnected_signal(sensor_name: str)
    """
    data_signal         = pyqtSignal(str, float)
    disconnected_signal = pyqtSignal(str)

    def __init__(
        self,
        name: str,
        sensor,             # any AtlasSensor implementing .read()
        interval: float = 1.0,
        max_failures: int = 3,
        parent=None
    ):
        super().__init__(parent)
        self.name         = name
        self.sensor       = sensor
        self.interval     = interval
        self.max_failures = max_failures
        self._failures    = 0
        self._running     = False

    def run(self):
        """Call this on a QThread to start readings."""
        self._running = True
        while self._running:
            try:
                val = self.sensor.read()
                print(val)
                self.data_signal.emit(self.name, val)
                self._failures = 0
            except Exception as e:
                self._failures += 1
                print(f"[{self.name}] read error:", e)
                if self._failures >= self.max_failures:
                    # give up and signal disconnection
                    self.disconnected_signal.emit(self.name)
                    break
            time.sleep(self.interval)

    def stop(self):
        """Signal the loop in run() to exit cleanly."""
        self._running = False
