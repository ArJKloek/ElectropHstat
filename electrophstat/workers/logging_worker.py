# scripts/logging_worker.py
import time
from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal

class LoggingWorker(QObject):
    """
    Calls logger.log(label, value) on every interval for each active channel.
    """
    error = pyqtSignal(str)

    def __init__(self, logger, value_data: dict, interval: float = 1.0):
        super().__init__()
        self.logger     = logger
        self.value_data = value_data     # your dict of latest values
        self.interval   = interval
        self.running    = False

    @pyqtSlot()
    def run(self):
        self.running = True
        time.sleep(self.interval)
        while self.running:
            try:
                # log every channel currently in logger.files
                for label in self.logger.files:
                    if label == "pump":
                        continue
                    val = self.value_data.get(label, None)
                    if val is not None:
                        self.logger.log(label, val)
            except Exception as e:
                self.error.emit(str(e))
            time.sleep(self.interval)

    @pyqtSlot()
    def stop(self):
        self.running = False
