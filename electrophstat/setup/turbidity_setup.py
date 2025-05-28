from electrophstat.gui.adc_controller import ADCController
from electrophstat.gui.dialogs import CalibrateTurbidityDialog
from electrophstat.models.model_calculator import BiExpCalibrator

def init_turbidity(self):
    
    if self.enable_turbidity_sensor:
        
        cal_settings = {
            "params": {
                "PercentFast": float(self.config.PercentFast),
                "KFast": float(self.config.KFast),
                "KSlow": float(self.config.KSlow),
            },
            "errors": None,  # Optional, unless you store errors
            "Y0": int(self.config.NTU_mV_calibration_0),
            "Plateau": int(self.config.NTU_mV_calibration_inf),
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
