from electrophstat.gui.sensor_controller import SensorController
from electrophstat.gui.dialogs import CalibratepHDialog

def init_sensors(self):

    
    slots = {}
    for atlas_name, atlas_info in self.config.atlas.items():
        if atlas_info.get('enable'):
            #slots[sensor_info.get('name')] = [self.button_cont.update_gui]
            slots[atlas_info.get('name')] = {
                "update_slots": [self.button_cont.update_gui],
                "address": int(atlas_info.get('address'),0),
                "sensor_key": atlas_info.get('name')
            }
        else:
            self.logging_ctrl.disable_logging([atlas_info.get('name')])
            continue

    self.sensor_ctrl = SensorController(self, update_slots=slots, interval=1.0)
    
    
    if self.config.atlas.pH.enable and self.sensor_ctrl.pH_worker is not None:
        self.pH_calibrate_dialog = CalibratepHDialog(float(self.pH_calibration_low),float(self.pH_calibration_mid),float(self.pH_calibration_high),self)
        pH_worker = self.sensor_ctrl.pH_worker
        # connect your dialog
        self.pH_calibrate_dialog.calibrate_changed.connect(
                lambda mode, val, _: pH_worker.calibrate_signal.emit(mode, val)
            )
    else:
        self.pH_calibrate_dialog = None
        
    self.plot_manager.update_dual_plot()
  
    
    