# electrophstat/sensors/atlas_worker.py

import time
from PyQt5.QtCore import QObject, QTimer, pyqtSignal, pyqtSlot

class AtlasSensorWorker(QObject):
    """
    A background worker for any AtlasSensor.
    Emits:
      • data_signal(name: str, value: float)
      • disconnected_signal(name: str)
    """
    data_signal         = pyqtSignal(str, float)
    disconnected_signal = pyqtSignal(str)
    calibrate_signal    = pyqtSignal(str, float)

    def __init__(
        self,
        name: str,
        sensor,             # AtlasSensor
        interval: float = 1.0,
        max_failures: int = 3,
        parent=None
    ):
        super().__init__(parent)
        self.name         = name
        self.sensor       = sensor
        self.interval     = int(interval * 1000)  # ms
        self.max_failures = max_failures
        self._failures    = 0

        # timer for regular reads
        self._timer = QTimer(self)
        self._timer.setInterval(self.interval)
        self._timer.timeout.connect(self._do_read)

        # calibration comes here
        self.calibrate_signal.connect(self._do_calibrate)

    @pyqtSlot()
    def start(self):
        """Kick off the polling timer."""
        self._failures = 0
        self._timer.start()

    @pyqtSlot()
    def stop(self):
        """Halt polling."""
        self._timer.stop()

    @pyqtSlot()
    def _do_read(self):
        """One cycle of reading; called by the timer."""
        try:
            val = self.sensor.read()
            self.data_signal.emit(self.name, val)
            self._failures = 0
        except Exception as e:
            self._failures += 1
            print(f"[{self.name}] read error:", e)
            if self._failures >= self.max_failures:
                self._timer.stop()
                self.disconnected_signal.emit(self.name)

    @pyqtSlot(str, float)
    def _do_calibrate(self, mode: str, value: float):
        """
        Pause polling, send the Cal,<mode>,<value> command,
        wait one full interval for the sensor to settle, then resume.
        """
        #print(f"[{self.name}] calibrate {mode} → {value}")
        # 1) stop regular reads
        self._timer.stop()

        try:
            self.sensor.calibrate(mode, value)
        except Exception as e:
            print(f"[{self.name}] calibration failed:", e)

        # 2) after one interval, restart reads so the next poll sees the new pH
        QTimer.singleShot(self.interval, self._timer.start)
