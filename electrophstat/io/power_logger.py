import os
from datetime import datetime

class PowerLogger:
    def __init__(self, log_dir="logs"):
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.filename = os.path.join(log_dir, f"Log_{timestamp}.txt")
        self.file = open(self.filename, "w")

    def log_start(self, voltage, current, mode, output, PStype):
        self.file.write("=== Power Supply Run Started ===\n")
        self.file.write(f"PPS Model: {PStype[0]}, VMAX: {PStype[1]} V, IMAX: {PStype[2]} A, VMIN: {PStype[3]} V\n")
        self.file.write(f"Start Time: {datetime.now()}\n")
        self.file.write(f"Initial Settings: Voltage={voltage:.2f}V, Current={current:.2f}A, Mode={mode}, Power={output}\n")
        self.file.flush()

    def log_change(self, what, value):
        self.file.write(f"[{datetime.now().strftime('%H:%M:%S')}] Changed {what}: {value}\n")
        self.file.flush()
    
    def setting_change(self, voltage, current, mode):
        self.file.write(f"[{datetime.now().strftime('%H:%M:%S')}] Settings set: Voltage={voltage:.2f}V, Current={current:.2f}A, Mode={mode}\n")
        self.file.flush()

    def log_stop(self, voltage, current, coulombs):
        self.file.write("\n=== Power Supply Run Stopped ===\n")
        self.file.write(f"Stop Time: {datetime.now()}\n")
        self.file.write(f"Final Voltage: {voltage:.2f} V\n")
        self.file.write(f"Final Current: {current:.2f} A\n")
        self.file.write(f"Total Coulombs: {coulombs:.2f} C\n")
        self.file.close()
    
    def reset(self):
        self.close()  # close current file
        # Create a new filename with new timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.filename = os.path.join("logs", f"ps_log_{timestamp}.txt")
        self.file = open(self.filename, "w")

    def close(self):
        self.file.close()
