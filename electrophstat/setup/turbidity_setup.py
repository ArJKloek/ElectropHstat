from electrophstat.gui.adc_controller import ADCController
from electrophstat.gui.dialogs import CalibrateTurbidityDialog
from electrophstat.models.model_calculator import BiExpCalibrator

def init_turbidity(self):
    
    if self.enable_turbidity_sensor:
        cfg = self.config 
        cal_settings = {
            "params": {
                "PercentFast": float(cfg.sensors.turbidity.model.PercentFast),
                "KFast": float(cfg.sensors.turbidity.model.KFast),
                "KSlow": float(cfg.sensors.turbidity.model.KSlow),
            },
            "errors": None,  # Optional, unless you store errors
            "Y0": int(cfg.sensors.turbidity.calibration.mV.zero),
            "Plateau": int(cfg.sensors.turbidity.calibration.mV.inf),
        }

        self.model_calculator = BiExpCalibrator(self)
        self.model_calculator.set_settings(cal_settings)
        
        self.turbidity_dialog =  CalibrateTurbidityDialog(self)
        self.actionCalibrate_Turbidity.triggered.connect(lambda: self.turbidity_dialog.exec_())

        self.adc_ctrl = ADCController(self, channel=0, interval=0.2)
       
    else:
        self.adc_ctr = None
        self.model_calculator = None
        self.turbidity_dialog = None
        self.TurbidityGroup.setVisible(False)
        self.actionCalibrate_Turbidity.setEnabled(False)
        self.logging_ctrl.disable_logging(['turbidity'])
