# electrophstat/gui/sensor_controller.py

from PyQt5.QtCore import QObject, QThread
from electrophstat.sensors.atlas_worker import AtlasSensorWorker
from electrophstat.sensors import discover_sensor

class SensorController(QObject):
    """
    Launches AtlasSensorWorker instances for each key in your registry,
    and wires their data_signal -> window slots.
    """
    def __init__(self, window, update_slots: dict, interval: float = 1.0):
        """
        window:        your MainWindow instance (for parenting)
        update_slots:  mapping sensor_key -> callback fn, e.g. {"ph": self.handle_pH}
        interval:      polling interval in seconds
        """
        super().__init__(window)
        self.win = window

        # For each sensor name/key, spin up a worker + thread
        for key, slot in update_slots.items():
            # 1) ask the sensors package for the right AtlasSensor
            atlas = discover_sensor(key)  # e.g. "ph" or "temp"
            
            # 2) make the generic worker
            worker = AtlasSensorWorker(
                name=key,
                sensor=atlas,
                interval=interval,
                max_failures=3
            )

            # 3) move it to its own QThread
            thr = QThread(self.win)
            worker.moveToThread(thr)
            thr.started.connect(worker.run)

            # 4) wire its signals
            worker.data_signal.connect(slot)
            #worker.disconnected_signal.connect(self.win.on_sensor_disconnect)

            # 5) hold onto them so Python won’t garbage‐collect
            setattr(self, f"{key}_worker", worker)
            setattr(self, f"{key}_thread", thr)

            # 6) start polling
            thr.start()
