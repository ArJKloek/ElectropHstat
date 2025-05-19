# in scripts/pHstat_GUI.py (or a new file scripts/pump_controller.py)
from PyQt5.QtCore import QObject, QTimer, pyqtSlot
from electrophstat.control.control_loop import PumpAction

class PumpController(QObject):
    """
    Drives the physical pump based on PumpAction.
    Automatically stops it after a set duration.
    """
    def __init__(self, hw, logger, duration_s: float, ml_per_cylce: float,  parent=None):
        super().__init__(parent)
        
        self.hw             = hw
        self.logger         = logger
        self.duration_ms    = int(duration_s * 1000)
        self.ml_per_cycle   = ml_per_cylce
        
        #Single shot for auto-stop 
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._stop)
    
    @pyqtSlot(PumpAction)
    def execute(self, action: PumpAction):
        if action.pump_on:
            self._start()
            # restart the timer for auto-stop
            self._timer.start(self.duration_ms)
        else:
            # immediate stop and cancel any pending timeout
            self._stop()
            self._timer.stop()

    def _start(self):
        # 1) activate hardware gate
        self.hw.open_gate()      # replace with your real lib8mosind call
        # 2) log the pumped volume
        self.logger.log({"pump_ml": self.ml_per_cycle})
    
    def _stop(self):
        # 1) Close gate
        self.hw.close_gate()      # replace with your real lib8mosind call

    @pyqtSlot(float, float)
    def set_calibration(self, ml: float, duration_s: float):
        self.ml_per_cycle = ml
        self.duration_ms  = int(duration_s * 1000) 