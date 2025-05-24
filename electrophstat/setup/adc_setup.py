from electrophstat.gui.adc_controller import ADCController

def init_adc(self):
    self.adc_ctrl = ADCController(self, channel=1, interval=1.0)
