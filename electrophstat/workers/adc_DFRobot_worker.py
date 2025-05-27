# electrophstat/workers/adc_worker.py

import time
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

class ADCWorker(QObject):
    data_ready = pyqtSignal(float)

    def __init__(self,
                 channel:  int   = 0,
                 interval: float = 1.0,
                 prefer_hw: bool  = True):
        super().__init__()
        self.channel   = channel
        self.interval  = interval
        self.adc       = prefer_hw
        # use our discovery routine
        #self.adc       = discover_adc(prefer_hw=prefer_hw,
        #                              channel=channel)
        self.is_running = False

    @pyqtSlot()
    def run(self):
        self.is_running = True
        while self.is_running:
            try:
                resp = self.adc.read_voltage(self.channel)
                print(f'response: {resp}')  
                raw  = resp['r']
                print(f'RAW ADC value: {raw}')
                self.data_ready.emit(raw)
            except Exception:
                pass
            time.sleep(self.interval)

    def stop(self):
        self.is_running = False
