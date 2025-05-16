# in scripts/pHstat_GUI.py (or a new file scripts/pump_controller.py)
from PyQt5.QtCore import QObject, QTimer
from electrophstat.control.control_loop import PumpAction

class PumpController(QObject):
    """
    Drives the physical pump based on PumpAction.
    Automatically stops it after a set duration.
    """
    def __init__(self, start_fn, stop_fn, duration_s: float = 1.0, parent=None):
        super().__init__(parent)
        self._start = start_fn      # e.g. self.startPump
        self._stop  = stop_fn       # e.g. self.stopPump
        self.duration_ms = int(duration_s * 1000)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._stop)

    def execute(self, action: PumpAction):
        if action.pump_on:
            self._start()
            # restart the timer for auto-stop
            self._timer.start(self.duration_ms)
        else:
            # immediate stop and cancel any pending timeout
            self._stop()
            self._timer.stop()
