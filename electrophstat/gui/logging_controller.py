# electrophstat/gui/logging_controller.py

from PyQt5.QtCore import QObject, QThread, pyqtSlot
from electrophstat.workers.logging_worker import LoggingWorker

class LoggingController(QObject):
    """
    Manages a LoggingWorker in its own thread.
    Call `start()` after logger.start_session(...),
    and `stop()` when you want to halt logging.
    """
    def __init__(self, window, interval: float = 5.0):
        super().__init__(window)
        self.win = window
        self.interval = interval

        # placeholders
        self._thread = None
        self._worker = None
        self.active_labels = set()

    def start(self):
        # only start once
        if self._thread is not None:
            return

        # ensure session is ready
        # active_labels & initial_values must have been set already
        logger      = self.win.logger
        value_data  = self.win.valueData
        active      = list(self.active_labels)

        self.active_labels = set(logger.files.keys())
        # 1) create worker+thread
        logger.start_session(
            active_labels    = active,
            initial_values   = value_data   # will zero‐point all active channels
        )
        
        self._worker = LoggingWorker(
            logger     = logger,
            value_data = value_data,
            interval   = self.interval
        )
        self._worker.active_labels = self.active_labels
        
        self._thread = QThread(self.win)
        self._worker.moveToThread(self._thread)

        # 2) wire up start/stop
        self._thread.started.connect(self._worker.run)
        self.win.destroyed.connect(self.stop)        # auto‐cleanup
        self._worker.error.connect(self._on_error)

        # 3) kick it off
        self._thread.start()

    @pyqtSlot()
    def stop(self):
        """Stop logging and tear down the thread."""
        if self._worker and self._thread:
            self._worker.stop()
            self._thread.quit()
            self._thread.wait()
        self._worker = None
        self._thread = None

    @pyqtSlot(str)
    def _on_error(self, msg: str):
        # you can pop up a QMessageBox or print
        print(f"[Logging ERROR] {msg}")

    def set_interval(self, new_interval: float):
        """
        Change the logging interval on the fly by updating the worker's
        interval. We do not stop/restart the thread, avoiding any blocking.
        """
        new_interval = float(new_interval)
        self.interval = new_interval
        print(f"[LoggingController] interval set to {new_interval}s")

        # If the worker is already running, just update its attribute.
        if self._worker is not None:
            self._worker.interval = new_interval
    
    def disable_logging(self, labels):
        """
        Prevent the given labels from being logged:
          • remove them from the active_labels set
          • drop any in-flight CSV file + start time so the worker skips them
        """
        for lbl in labels:
            self.active_labels.discard(lbl)
            self.win.logger.files .pop(lbl, None)
            self.win.logger.starts.pop(lbl, None)

    def enable_logging(self, labels):
        """
        Re-allow the given labels to be logged:
          • add them back to active_labels
          • if the session is running, create fresh CSV files for each
        """
        for lbl in labels:
            self.active_labels.add(lbl)
            # if mid-session and we haven’t made a file yet:
            if self.win.logger.log_dir and lbl not in self.win.logger.files:
                idx  = self.win.logger.labels.index(lbl)
                col  = self.win.logger.columns[idx]
                path = self.win.logger._make_file(lbl, col, datetime.now())
                self.win.logger.files[lbl]  = path
                self.win.logger.starts[lbl] = time.monotonic()