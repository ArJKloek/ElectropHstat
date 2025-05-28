from PyQt5.QtCore import QObject, QThread, pyqtSlot
#from electrophstat.workers.adc_worker import ADCWorker
from ..workers.adc_DFRobot_worker import ADCWorker
from electrophstat.hardware import discover_adc
from electrophstat.dummy.dummy_ADS1115 import DummyADS1115
class ADCController(QObject):
    """
    Spins up the ADCWorker and routes its data_ready signal
    into a slot on the main window.
    """
    def __init__(self, win, channel:int=0, interval:float=0.2):
        super().__init__(win)
        self.win = win

        hw = discover_adc(channel=channel)
        if isinstance(hw, DummyADS1115):
            # If dummy power supply, color the groupbox orange
            # to indicate that it is a dummy.
            group_name = "TurbidityGroup"
            # grab the widget from your MainWindow
            groupbox = getattr(self.win, group_name, None)
            if groupbox is not None:
                groupbox.setStyleSheet("""
                    QGroupBox {
                    border: 2px solid orange;
                    background-color: #FFF8E1;
                    }
                """)

        # 1) prepare worker
        self.worker = ADCWorker(channel=channel, interval=interval, prefer_hw=hw)

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
    def on_data_ready(self, value: int):
        """
        Received a new reading from channel 0.
        Display it or log it as you wish.
        """
        # e.g. if you have a QLCDNumber named lcd_adc in your UI:

        try:
            #self.win.lcd_adc.display(value)
            #value_V = value / 1000.0  # convert mV to V
            v_min = self.win.model_calculator.v_min
            v_max = self.win.model_calculator.v_max
            if not (v_min <= value <= v_max):
                ntu = float('inf')  # or np.nan, or show "out of range"
            else:
                ntu = self.win.model_calculator.inverse(value, x_min=0, x_max=200000)
            self.win.button_cont.update_gui("turbidity", round(ntu, 0))
            self.win.button_cont.update_gui("turbidity_raw", round(value, 0))
            self.win.turbidity_dialog.update_raw_label(value)
        except AttributeError as e:
            print("[ADC] AttributeError:", e)
            pass

    def stop(self):
        # clean shutdown
        self.worker.stop()
        self.thread.quit()
        self.thread.wait()
