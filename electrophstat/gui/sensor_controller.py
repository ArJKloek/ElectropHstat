# electrophstat/gui/sensor_controller.py

from PyQt5.QtCore import QObject, QThread
from electrophstat.sensors.atlas_worker import AtlasSensorWorker
from ..dummy.dummy_atlas import DummyAtlas
from electrophstat.sensors import discover_sensor

class SensorController(QObject):
    def __init__(self, window, update_slots: dict, interval: float = 1.0):
        super().__init__(window)
        self.win = window

        for key, slot_or_list in update_slots.items():
            atlas, kind = discover_sensor(key)
            print(kind)
            worker = AtlasSensorWorker(name=key, sensor=atlas, interval=interval)
            thr    = QThread(self.win)
            worker.moveToThread(thr)

            # If dummy color groupbox
            # color the box if we're using the dummy
            #if isinstance(atlas, DummyAtlas):
                # a light orange border to flag “dummy mode”
            #    self.win.phGroupBox.setStyleSheet("""
            #        QGroupBox {
            #            border: 2px solid orange;
            #            background-color: #FFF8E1;
            #        }
            #    """)
            #else:
            #    # reset to default
            #    self.win.phGroupBox.setStyleSheet("")
            # normalize to a list
            if callable(slot_or_list):
                slots = [slot_or_list]
            else:
                slots = list(slot_or_list)

            # connect each slot
            for slot in slots:
                worker.data_signal.connect(slot)

            # (other wiring…)
            thr.started.connect(worker.start)
            thr.start()

            setattr(self, f"{key}_worker", worker)
            setattr(self, f"{key}_thread",   thr)
