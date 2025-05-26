from electrophstat.gui.adc_controller import ADCController
from electrophstat.gui.dialogs import CalibrateTurbidityDialog
from electrophstat.models.model_calculator import BiExpCalibrator
def init_turbidity(self):
    
    if self.enable_turbidity_sensor:
        
        self.adc_ctrl = ADCController(self, channel=1, interval=1.0)
        self.turbidity_dialog =  CalibrateTurbidityDialog(self)
        self.model_calculator = BiExpCalibrator(self)
        self.actionCalibrate_Turbidity.triggered.connect(lambda: self.turbidity_dialog.exec_())

        
    else:
        self.adc_ctr = None
        self.TurbidityGroup.setVisible(False)
        self.logging_ctrl.disable_logging(['turbidity'])
