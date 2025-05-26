from electrophstat.gui.adc_controller import ADCController
from electrophstat.gui.dialogs import CalibrateTurbidityDialog
from electrophstat.models.model_calculator import BiExpCalibrator

def init_turbidity(self):
    
    if self.enable_turbidity_sensor:
        
        self.adc_ctrl = ADCController(self, channel=1, interval=1.0)
        cal_settings = {
            "params": {
                "PercentFast": float(self.config.PercentFast),
                "KFast": float(self.config.KFast),
                "KSlow": float(self.config.KSlow),
            },
            "errors": None,  # Optional, unless you store errors
            "Y0": float(self.config.NTU_V_calibration_0),
            "Plateau": float(self.config.NTU_V_calibration_inf),
        }
        
        
        self.turbidity_dialog =  CalibrateTurbidityDialog(self)
        
        self.model_calculator = BiExpCalibrator(self)
        self.model_calculator.set_settings(cal_settings)
        self.actionCalibrate_Turbidity.triggered.connect(lambda: self.turbidity_dialog.exec_())

        
    else:
        self.adc_ctr = None
        self.TurbidityGroup.setVisible(False)
        self.logging_ctrl.disable_logging(['turbidity'])
