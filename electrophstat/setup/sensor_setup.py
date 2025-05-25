from electrophstat.gui.sensor_controller import SensorController
from electrophstat.gui.dialogs import CalibratepHDialog

def init_sensors(self):

    self.pH_calibrate_dialog = CalibratepHDialog(float(self.pH_calibration_low),float(self.pH_calibration_mid),float(self.pH_calibration_high),self)

        
    #slots = {
    #        "pH":   [self.button_cont.update_gui],
    #        "temperature": [self.button_cont.update_gui],
    #}

    slots = {
            "pH":   [self.button_cont.update_gui],
    }

    self.sensor_ctrl = SensorController(self, update_slots=slots, interval=1.0)
        
        
    pH_worker = self.sensor_ctrl.pH_worker
        # connect your dialog
    self.pH_calibrate_dialog.calibrate_changed.connect(
            lambda mode, val, _: pH_worker.calibrate_signal.emit(mode, val)
    )