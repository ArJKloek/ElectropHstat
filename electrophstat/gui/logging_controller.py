# electrophstat/gui/logging_controller.py

from PyQt5.QtCore import QObject, QThread, pyqtSlot
from electrophstat.workers.logging_worker import LoggingWorker
from datetime import datetime
import time

class LoggingController(QObject):
    def __init__(self, window, interval: float = 5.0):
        super().__init__(window)
        self.win = window
        self.interval = interval
        self._thread = None
        self._worker = None
        self.active_labels = set()

    def start(self):
        if self._thread is not None:
            return

        # Capture which labels we want to log right now
        self.active_labels = set(self.win.logger.labels)

        # Kick off a new session on the Logger
        # We pass initial_values=self.win.valueData so each CSV
        # gets a zero‐point row automatically.
        self.win.logger.start_session(
            active_labels   = list(self.active_labels),
            initial_values  = self.win.valueData
        )

        # Create your worker + thread
        self._worker = LoggingWorker(
            logger     = self.win.logger,
            value_data = self.win.valueData,
            interval   = self.interval
        )
        self._worker.active_labels = self.active_labels

        self._thread = QThread(self.win)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.error.connect(self._on_error)
        self.win.destroyed.connect(self.stop)

        self._thread.start()

    @pyqtSlot()
    def stop(self):
        if self._worker and self._thread:
            self._worker.stop()
            self._thread.quit()
            self._thread.wait()
        self._worker = None
        self._thread = None

    @pyqtSlot()
    def reset(self):
        """
        Fully tear down the current session, clear out all CSV state,
        and reset the controller so next start() is a brand-new session.
        """
        # 1) Stop any running worker
        self.stop()

        # 2) Clear the Logger’s session data
        try:
            self.win.logger.reset()
        except Exception as e:
            print(f"[LoggingController] error resetting logger: {e}")

        # 3) Clear our active-labels so next start() picks them fresh
        self.active_labels.clear()

        print("[LoggingController] logging session has been reset.")

    @pyqtSlot(str)
    def _on_error(self, msg: str):
        print(f"[Logging ERROR] {msg}")

    def set_interval(self, new_interval: float):
        self.interval = float(new_interval)
        if self._worker is not None:
            self._worker.interval = self.interval
        print(f"[LoggingController] interval set to {self.interval}s")
