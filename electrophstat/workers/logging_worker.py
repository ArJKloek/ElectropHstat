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
        while self.running:
            start = time.time()
            try:
                # log every channel currently in logger.files
                labels = getattr(self, "active_labels", self.logger.files.keys())
                for label in labels:
                    if label == "pump":
                        continue
                    if label == "turbidity":
                        # pull both values out
                        proc = self.value_data.get("turbidity", 0.0)
                        raw  = self.value_data.get("turbidity_raw", 0.0)
                        # emit both in one go (your Logger._write_turbidity_row handles this)
                        self.logger.log("turbidity", (proc, raw))
                    else:
                        val = self.value_data.get(label, None)
                        if val is not None:
                            self.logger.log(label, val)
            except Exception as e:
                self.error.emit(str(e))
            # Sleep in small increments to allow quick stopping
            elapsed = time.time() - start
            remaining = self.interval - elapsed
            while self.running and remaining > 0:
                time.sleep(min(0.1, remaining))
                remaining -= 0.1

    @pyqtSlot()
    def stop(self):
        self.running = False
