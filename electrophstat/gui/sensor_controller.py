# electrophstat/gui/sensor_controller.py

from PyQt5.QtCore import QObject, QThread, QMetaObject, Qt
from electrophstat.workers.atlas_worker import AtlasSensorWorker
from ..dummy.dummy_atlas import DummyAtlas
from electrophstat.hardware import discover_sensor

class SensorController(QObject):
    def __init__(self, window, update_slots: dict, interval: float = 1.0):
        super().__init__(window)
        self.win = window
        self._worker_keys = []

        for sensor_name, slot_info in update_slots.items():
            update_slot_list = slot_info["update_slots"]
            address = slot_info["address"]
            key = slot_info.get("sensor_key", sensor_name)
            # Now pass the correct address for each sensor
            atlas = discover_sensor(key, address=address)
            worker = AtlasSensorWorker(name=key, sensor=atlas, interval=interval)
            thr    = QThread(self.win)
            worker.moveToThread(thr)

            # If dummy color groupbox
            # color the box if we're using the dummy
            if isinstance(atlas, DummyAtlas) and self.win.debug_mode == True:
                group_name = f"{key}Group"
                # grab the widget from your MainWindow
                groupbox = getattr(self.win, group_name, None)
                if groupbox is not None:
                    groupbox.setStyleSheet("""
                        QGroupBox {
                        border: 2px solid orange;
                        background-color: #FFF8E1;
                        }
                    """)
            elif isinstance(atlas, DummyAtlas) and self.win.debug_mode == False:
                # If real power supply, color the groupbox green
                group_name = f"{key}Group"
                groupbox = getattr(self.win, group_name, None)
                if groupbox is not None:
                    groupbox.setTitle(f"⚠️ {key} sensor not found")
                    setattr(self, f"{key}_worker", None)
                    label_name = f"{key}Label"
                    print(f"Disabling {label_name} label")
                    label = getattr(self.win, label_name, None)
                    if label is not None:
                        label.setText(f"xx")
                        label.setEnabled(False)
                    self.win.logging_ctrl.disable_logging([key])
                    if key == "RTD":
                        self.win.graph_ctrl.set_temp_enabled(False)
                continue    
               

            # normalize to a list
            if callable(update_slot_list):
                slots = [update_slot_list]
            else:
                slots = list(update_slot_list)

            # connect each slot
            for slot in slots:
                worker.data_signal.connect(slot)

            # (other wiring…)
            thr.started.connect(worker.start)
            thr.start()

            setattr(self, f"{key}_worker", worker)
            setattr(self, f"{key}_thread",   thr)
            self._worker_keys.append(key)

    def stop(self):
        """Stop all sensor workers and threads cleanly."""
        for key in self._worker_keys:
            worker = getattr(self, f"{key}_worker", None)
            thread = getattr(self, f"{key}_thread", None)
            if worker is not None:
                # Ensure stop() is called in the worker's thread
                QMetaObject.invokeMethod(worker, "stop", Qt.BlockingQueuedConnection)
            if thread is not None:
                thread.quit()
                thread.wait()
            # Optionally delete the worker after thread is finished
            if worker is not None:
                worker.deleteLater()

