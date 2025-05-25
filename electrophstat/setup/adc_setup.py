from electrophstat.gui.adc_controller import ADCController


def init_adc(self):
    
    if self.enable_turbidity_sensor:
        
        self.adc_ctrl = ADCController(self, channel=1, interval=1.0)
    else:
        self.adc_ctr = None
        self.TurbidityGroup.setVisible(False)
        self.logging_ctrl.disable_logging(['turbidity'])
