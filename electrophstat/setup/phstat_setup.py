from electrophstat.control.pump_control import PumpController
from electrophstat.connections.pHstat_connections import pHStatConnections
from electrophstat.gui.phstat_controller import pHStatController
from electrophstat.gui.dialogs import CalibratePumpDialog

def init_phstat(self):
    self.calibrate_pump_dialog = CalibratePumpDialog(float(self.pump_volume_per_cycle_ml), float(self.pump_cycle_duration_s), self)
    self.pump_ctrl = PumpController(
            hw=lib8mosind,
            logger=self.logger,
            duration_s=float(self.pump_cycle_duration_s),
            ml_per_cylce = float(self.pump_volume_per_cycle_ml),
            parent=self
        )
    self.pHstat_cont = pHStatConnections(self)
    self.phstat_ctrl = pHStatController(self, interval=1.0)
    self.pHstat_cont.handle_select(self.config.pH_control_mode)
    self.pHstat_cont.handle_pH    (self.config.pH_target)
  
    self.calibrate_pump_dialog.test_pump.connect(
            self.pump_ctrl.on_test_pump)
        # wire “Set” → PumpController
    self.calibrate_pump_dialog.select_changed.connect(
            self.pump_ctrl.on_set_calibration)
      
