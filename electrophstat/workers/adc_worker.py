import time
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from electrophstat.vendor.adc_8chan_12bit import Pi_hat_adc

class ADCWorker(QObject):
    """
    Polls a single ADC channel in a background thread and emits its value.
    """
    data_ready = pyqtSignal(float)  # emits the raw or voltage reading

    def __init__(self, channel:int=1, interval:float=1.0):
        super().__init__()
        self.channel   = channel
        self.interval  = interval
        self.adc       = Pi_hat_adc()      # your imported ADC class
        self.is_running = False

    @pyqtSlot()
    def run(self):
        self.is_running = True
        while self.is_running:
            try:
                # read only channel 1 (you can change to get_nchan_…)
                val = self.adc.get_nchan_vol_milli_data(self.channel - 1)
                self.data_ready.emit(val)
            except Exception as e:
                # you could emit an error‐signal here if you like
                pass
            time.sleep(self.interval)

    def stop(self):
        self.is_running = False
