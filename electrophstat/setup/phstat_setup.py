from electrophstat.control.pump_control import PumpController
from electrophstat.connections.pHstat_connections import pHStatConnections
from electrophstat.gui.phstat_controller import pHStatController
from electrophstat.gui.dialogs import CalibratePumpDialog
from electrophstat.hardware import discover_switcher
from electrophstat.dummy.dummy_switcher import MockLib8MosInd

#lib8mosind = MockLib8MosInd()



def init_phstat(self):
    if self.enable_phstat:
        self.calibrate_pump_dialog = CalibratePumpDialog(float(self.pump_volume_per_cycle_ml), float(self.pump_cycle_duration_s), self)
        
        switcher_debug = getattr(self.config.pHstat, "debug", False)
        if switcher_debug:
            hw = MockLib8MosInd()
            print("Debug mode for switcher: using MockLib8MosInd.")
        else:
            hw = discover_switcher()
        
        if isinstance(hw, MockLib8MosInd)  and self.debug_mode == True:
            # If dummy power supply, color the groupbox orange
            # to indicate that it is a dummy.
            group_name = "pHstatGroup"
            # grab the widget from your MainWindow
            groupbox = getattr(self, group_name, None)
            if groupbox is not None:
                groupbox.setStyleSheet("""
                    QGroupBox {
                    border: 2px solid orange;
                    background-color: #FFF8E1;
                    }
                """)
        elif isinstance(hw, MockLib8MosInd) and self.debug_mode == False:
            # If real power supply, color the groupbox green
            group_name = "pHstatGroup"
            groupbox = getattr(self, group_name, None)
            if groupbox is not None:
                groupbox.setTitle("⚠️ Switcher not found")
                self.calibrate_pump_dialog = None
                self.pump_ctrl = None
                self.pHstat_cont = None
                self.phstat_ctrl = None
                #self.pHstatGroup.setVisible(False)
                self.keepSelector.setEnabled(False) 
                self.phSpin.setEnabled(False)  
                self.actionCalibrate_Pump.setEnabled(False) 
                self.graph_ctrl.set_pHstat_enabled(False)
                self.logging_ctrl.disable_logging(['pump'])
                self.toggle_pH_control.setEnabled(False)
            return
    
               
        self.pump_ctrl = PumpController(
                hw=hw,
                logger=self.logger,
                duration_s=float(self.pump_cycle_duration_s),
                ml_per_cylce = float(self.pump_volume_per_cycle_ml),
                parent=self
            )
        self.pHstat_cont = pHStatConnections(self)
        self.phstat_ctrl = pHStatController(self, interval=1.0)
        self.pHstat_cont.handle_select(self.config.pHstat.mode)
        self.pHstat_cont.handle_pH    (self.config.pHstat.target)
  
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
        self.actionCalibrate_Pump.setEnabled(False)
        self.logging_ctrl.disable_logging(['pump'])
        self.toggle_pH_control.setEnabled(False)
