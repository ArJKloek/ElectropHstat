from electrophstat.gui.sensor_controller import SensorController
from electrophstat.gui.dialogs import CalibratepHDialog

def init_sensors(self):

    
    slots = {}
    for sensor_name, sensor_info in self.config.sensors.items():
        if sensor_info.get('enable'):
            address = sensor_info.get('address')
            slots[sensor_info.get('name')] = [self.button_cont.update_gui]
        else:
            self.logging_ctrl.disable_logging([sensor_info.get('name')])
            continue

    self.sensor_ctrl = SensorController(self, update_slots=slots, address=address, interval=1.0)
    
    
    if self.enable_ph_sensor and self.sensor_ctrl.pH_worker is not None:
        self.pH_calibrate_dialog = CalibratepHDialog(float(self.pH_calibration_low),float(self.pH_calibration_mid),float(self.pH_calibration_high),self)
        pH_worker = self.sensor_ctrl.pH_worker
        # connect your dialog
        self.pH_calibrate_dialog.calibrate_changed.connect(
                lambda mode, val, _: pH_worker.calibrate_signal.emit(mode, val)
            )
    else:
        self.pH_calibrate_dialog = None
        
        
    
    