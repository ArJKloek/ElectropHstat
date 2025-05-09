from PyQt5.QtCore import QObject, pyqtSignal
from voltcraft.pps import PPS
import time

class PPSWorker(QObject):
    limits_signal = pyqtSignal(float, float, float, str)  # VMAX, IMAX, VMIN, MODEL
    voltage_signal = pyqtSignal(float)
    current_signal = pyqtSignal(float)
    mode_signal = pyqtSignal(str)
    disconnected_signal = pyqtSignal()

    def __init__(self, port, interval, reset):
        super().__init__()
        print(port)
        self.pps = PPS(port,reset)
        self.interval = interval
        self.failure_count = 0
        self.max_failures = 3  # Number of allowed failures before disconnect
        self.running = True
        
    def run(self):
        while self.running:
            try:
                v, a, mode = self.pps.reading()
                #voltage = self.pps.get_voltage()
                #current = self.pps.get_current()
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
            self.pps.voltage(value)
        except Exception as e:
            print(f"Failed to set voltage: {e}")

    def set_current(self, value):
        try:
            self.pps.current(value)
        except Exception as e:
            print(f"Failed to set current: {e}")

    def set_output(self, enable: bool):
        try:
            self.pps.output(enable)
        except Exception as e:
            print(f"Failed to toggle output: {e}")
    
    def emit_limits(self):
        self.limits_signal.emit(
            self.pps.VMAX,
            self.pps.IMAX,
            self.pps.VMIN,
            self.pps.MODEL
        )
    def is_connected(self) -> bool:
        try:
            # This triggers an initial command ("GMAX") already in __init__
            _ = self.pps.VMAX  # Try accessing a property to force failure if not connected
            return True
        except Exception as e:
            print(f"PPS detection failed: {e}")
            return False
