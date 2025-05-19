from __future__ import annotations
from PyQt5.QtCore import QObject, pyqtSignal
from electrophstat.hardware.interfaces import PowerSupply
import time

class PPSWorker(QObject):
    limits_signal       = pyqtSignal(float, float, float, str)  # VMAX, IMAX, VMIN, MODEL
    voltage_signal      = pyqtSignal(float)
    current_signal      = pyqtSignal(float)
    mode_signal         = pyqtSignal(str)
    disconnected_signal = pyqtSignal()

    def __init__(self, psu: PowerSupply(), interval:float, reset: bool = True):
        super().__init__()
        self.psu        = psu
        self.interval   = interval
        self.failure_count  = 0
        self.max_failures   = 3  # Number of allowed failures before disconnect
        self.running        = True
        
        if reset:
            self.reset_psu()
            print("Reset")
    
    def run(self):
        while self.running:
            try:
                v, a = self.psu.read_output()
                mode  = "CC" if self.psu.read_output()[1] else "CV"  # or your own logic
                self.voltage_signal.emit(v)
                self.current_signal.emit(a)
                self.mode_signal.emit(mode)
                self.failure_count = 0  # ✅ reset on success
            except Exception as e:
                self.failure_count += 1
                print(f"PPS read error: {e}")
                
                if self.failure_count >= self.max_failures:
                    print("[PPSWorker] Too many failures. Assuming disconnection.")
                    self.disconnected_signal.emit()
                    self.running = False
                    break        
            time.sleep(self.interval)

    def stop(self):
        self.running = False

    def set_voltage(self, value):
        try:
            self.psu.voltage(value)
        except Exception as e:
            print(f"Failed to set voltage: {e}")

    def set_current(self, value):
        try:
            self.psu.current(value)
        except Exception as e:
            print(f"Failed to set current: {e}")

    def set_output(self, enable: bool):
        try:
            self.psu.output(enable)
        except Exception as e:
            print(f"Failed to toggle output: {e}")
    
    def emit_limits(self):
        # If your driver exposes constants, emit them; else send N/A.
        self.limits_signal.emit(
            getattr(self.psu, "VMAX", float("nan")),
            getattr(self.psu, "IMAX", float("nan")),
            getattr(self.psu, "VMIN", float("nan")),
            getattr(self.psu, "MODEL", "Unknown"),
        )

    def is_connected(self) -> bool:
        try:
            # This triggers an initial command ("GMAX") already in __init__
            _ = self.psu.VMAX  # Try accessing a property to force failure if not connected
            return True
        except Exception as e:
            print(f"PPS detection failed: {e}")
            return self.psu.connected
    
    # ---------- helpers ----------
    def _safe(self, fn):
        try:
            fn()
        except Exception as e:
            print(f"[PPSWorker] driver error: {e}")
    
    def reset_psu(self):
        """Reset PPS to known state."""
        try:
            self.psu.output(False)    # Ensure output is OFF
            self.psu.voltage(0)       # Reset voltage to 0V
            self.psu.current(0)       # Reset current limit to 0A or a default value
            print("[PPSWorker] PPS reset completed successfully.")
        except Exception as e:
            print(f"[PPSWorker] Failed to reset PPS: {e}")

