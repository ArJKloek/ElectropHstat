from PyQt5.QtCore import QObject, QThread, pyqtSlot
from electrophstat.workers.adc_worker import ADCWorker

class ADCController(QObject):
    """
    Spins up the ADCWorker and routes its data_ready signal
    into a slot on the main window.
    """
    def __init__(self, win, channel:int=1, interval:float=1.0):
        super().__init__(win)
        self.win = win

        # 1) prepare worker
        self.worker = ADCWorker(channel=channel, interval=interval)

        # 2) move to its own thread
        self.thread = QThread(self.win)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)

        # 3) connect the data signal to a handler
        self.worker.data_ready.connect(self.on_data_ready)

        # 4) stop thread when window closes
        self.win.destroyed.connect(self.stop)

        # 5) start polling
        self.thread.start()

    @pyqtSlot(float)
    def on_data_ready(self, value: float):
        """
        Received a new reading from channel 1.
        Display it or log it as you wish.
        """
        print(f'ADC value {value}')
        # e.g. if you have a QLCDNumber named lcd_adc in your UI:
        try:
            #self.win.lcd_adc.display(value)
            self.win.button_cont.update_gui("turbidity",value)
        except AttributeError:
            pass

    def stop(self):
        # clean shutdown
        self.worker.stop()
        self.thread.quit()
        self.thread.wait()
