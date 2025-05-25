from electrophstat.control.pump_control import PumpController
from electrophstat.connections.pHstat_connections import pHStatConnections
from electrophstat.gui.phstat_controller import pHStatController
from electrophstat.gui.dialogs import CalibratePumpDialog
from electrophstat.dummy.dummy_switcher import MockLib8MosInd

lib8mosind = MockLib8MosInd()

def init_phstat(self):
    if self.enable_phstat:
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
        self.pHstat_cont.handle_select(self.config.pHstat_mode)
        self.pHstat_cont.handle_pH    (self.config.pH_target)
  
        self.calibrate_pump_dialog.test_pump.connect(
            self.pump_ctrl.on_test_pump)
        # wire “Set” → PumpController
        self.calibrate_pump_dialog.select_changed.connect(
            self.pump_ctrl.on_set_calibration)
    else:
        self.calibrate_pump_dialog = None
        self.pump_ctrl = None
        self.pHstat_cont = None
        self.pHstatGroup.setVisible(False)
        self.logging_ctrl.disable_logging(['pump'])
        self.toggle_pH_control.setEnabled(False)
