# in scripts/pHstat_GUI.py (or a new file scripts/pump_controller.py)
from PyQt5.QtCore import QObject, QTimer, pyqtSlot, pyqtSignal
from electrophstat.control.phstat_control import PumpAction

class PumpController(QObject):
    dose_finished = pyqtSignal()

    """
    Drives the physical pump based on PumpAction.
    Automatically stops it after a set duration.
    """
    def __init__(self, hw, logger, duration_s: float, ml_per_cylce: float,  parent=None):
        super().__init__(parent)
        self.parent         = parent
        self.hw             = hw
        self.logger         = logger
        self.duration_ms    = int(duration_s * 1000)
        self.ml_per_cycle   = ml_per_cylce
        self.total_ml       = 0
        #Single shot for auto-stop 
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._stop)

        self._dose_timer = QTimer(self)
        self._dose_timer.setSingleShot(True)
        self._dose_timer.timeout.connect(self.dose_finished)
        self._test_timer   = QTimer(self)
        self._test_timer.setSingleShot(True)
        self._test_timer.timeout.connect(self._end_test)

    @pyqtSlot(PumpAction)
    def dose(self, action: PumpAction):
        if action.pump_on:
            self._start()
            # restart the timer for auto-stop
            self._timer.start(self.duration_ms)
            self._dose_timer.start(self.duration_ms)

        else:
            # immediate stop and cancel any pending timeout
            self._stop()
            self._timer.stop()
    
    @pyqtSlot(bool,float)
    def on_test_pump(self, turn_on: bool, duration_s: float):
        """Called when the user clicks ‘Test’ on the dialog."""
        if turn_on:
            # start hardware output
            self.hw.set(0,1,1)
            # schedule turn‐off after the dialog’s interval
            interval_ms = int(duration_s * 1000)
            self._test_timer.start(interval_ms)

    def _end_test(self):
        # stop hardware output
        self.hw.set(0,1,0)

    @pyqtSlot(float, float)
    def on_set_calibration(self, ml_per_cycle: float, interval_s: float):
        """Called when the user clicks ‘Set’ on the dialog."""
        self.ml_per_cycle = ml_per_cycle
        self.duration_ms   = int(interval_s * 1000)
        print(f"[PumpController] Calibrated: {ml_per_cycle} mL per cycle, {interval_s}s interval")
        # Optionally persist to your config here

    def _start(self):
        # 1) activate hardware gate
        self.hw.set(0,1,1)   
        self.total_ml += self.ml_per_cycle
        self.parent.valueData["pump"] = self.total_ml
        print("Pump ON")
        # 2) log the pumped volume
        #self.logger.log({"pump_ml": self.ml_per_cycle})
    
    def _stop(self):
        # 1) Close gate
        self.hw.set(0,1,0)        # replace with your real lib8mosind call
        self.parent.logger.log("pump", self.total_ml)

        print("Pump OFF")

    def _reset(self):
        self.total_ml = 0 

    @pyqtSlot(float, float)
    def set_calibration(self, ml: float, duration_s: float):
        self.ml_per_cycle = ml
        self.duration_ms  = int(duration_s * 1000) 
    
    