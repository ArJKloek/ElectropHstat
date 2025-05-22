# electrophstat/gui/phstat_controller.py

from PyQt5.QtCore    import QObject, QThread, pyqtSlot
from PyQt5.QtWidgets import QMessageBox
from electrophstat.control.phstat_control import pHStatLoop
from electrophstat.workers.phstat_worker  import pHstatWorker
from electrophstat.control.pump_control import PumpAction
import time
class pHStatController(QObject):
    """
    Spins up a pHstatWorker in its own thread that polls get_pH().
    Handles the worker.action_signal in on_action().
    """
    def __init__(self, window, interval: float = 1.0, cooldown: float = 5.0):
        super().__init__(window)
        self.win = window
        self.win.pump_ctrl.dose_finished.connect(self._on_dose_finished)
        self.loop = pHStatLoop(
            select=self.win.pHSelectMode,
            target_pH=self.win.pH_target
        )
        self._last_pump_on = False

        # 1) Create the worker (polls window.pHdata) and move to thread
        self.worker = pHstatWorker(
            control_loop  = self.loop,
            get_pH_callable = lambda: float(self.win.valueData["pH"]),
            interval      = interval
        )
        self.thread = QThread(self.win)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)

        # 2) Connect the worker’s action_signal → our slot
        #    Signature must be (pump_on: bool, status: bool)
        self.worker.action_signal.connect(self.on_action)

        # 3) Hook up your “Start/Stop override” toggle to flip the loop
        #    (Make sure you have a checkable QPushButton named pHStatToggle in your UI)
        #self.win.pHStatToggle.clicked.connect(self.loop.toggle_start)

        # 4) Clean up automatically when the window closes
        self.win.destroyed.connect(self.stop)

        # 5) Start the control thread
        self.thread.start()

        # rising‐edge detector + cooldown state
        self._last_pump_on    = False
        self._last_dose_time  = 0.0
        self._cooldown        = cooldown  # seconds

    @pyqtSlot(bool, bool)
    def on_action(self, pump_on: bool, status: bool):
        now = time.monotonic()

        # only consider a new pump pulse on a rising edge...
        if pump_on and not self._last_pump_on:
            # ...and only if cooldown has elapsed
            if now - self._last_dose_time >= self._cooldown:
                action = PumpAction(pump_on=pump_on, status=status)
                self.win.pump_ctrl.dose(action)
                self._last_dose_time = now
                self._last_pump_on = pump_on
            else:
                # still cooling down; skip this pulse
                pass
    
    @pyqtSlot()
    def _on_dose_finished(self):
        # the pump really stopped, so allow the next rising edge to trigger again
        self._last_pump_on = False

    @pyqtSlot(bool)
    def on_pumpToggle(self, checked: bool):
        """
        Called by ButtonConnections.start_stat when the user toggles
        the pH-stat start/stop button.
        """
        # Flip the override in the loop
        self.loop.toggle_start()
        # Reset the rising-edge detector so your next cycle will pulse
        self._last_pump_on = False
    
    @pyqtSlot()
    def stop(self):
        """Cleanly shut down the worker thread."""
        self.worker.stop()
        self.thread.quit()
        self.thread.wait()
    
    def enable(self):
        # 1) Start the control worker again
        if not self.thread.isRunning():
            # reset the flag so run() will loop
            self.worker.running = True
            # (re)start the thread
            self.thread.start()

        # 2) Re-enable the widgets
        self.win.phSpin      .setEnabled(True)
        self.win.keepSelector.setEnabled(True)
        # (leave PPS, sensor, logger alone)

        
    def disable(self):
        # 1) Stop the control worker
        self.worker.stop()
        if self.thread.isRunning():
            self.thread.quit()
            self.thread.wait()

        # 2) Disable the widgets
        self.win.phSpin      .setEnabled(False)
        self.win.keepSelector.setEnabled(False)
       
        