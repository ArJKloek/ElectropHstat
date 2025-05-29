from electrophstat.gui.sensor_controller import SensorController
from electrophstat.gui.dialogs import CalibratepHDialog

def init_sensors(self):

    
    slots = {}

    if self.enable_ph_sensor:
        slots["pH"] = [ self.button_cont.update_gui ]
    else:
        self.logging_ctrl.disable_logging(['pH'])

    if self.enable_temp_sensor:
        slots["temperature"] = [ self.button_cont.update_gui ]
    else:
        self.logging_ctrl.disable_logging(['temperature'])

    self.sensor_ctrl = SensorController(self, update_slots=slots, interval=1.0)
    
    
    if self.enable_ph_sensor and self.sensor_ctrl.pH_worker is not None:
        self.pH_calibrate_dialog = CalibratepHDialog(float(self.pH_calibration_low),float(self.pH_calibration_mid),float(self.pH_calibration_high),self)
        pH_worker = self.sensor_ctrl.pH_worker
        # connect your dialog
        self.pH_calibrate_dialog.calibrate_changed.connect(
                lambda mode, val, _: pH_worker.calibrate_signal.emit(mode, val)
            )
    else:
        self.pH_calibrate_dialog = None
        
        
    
    