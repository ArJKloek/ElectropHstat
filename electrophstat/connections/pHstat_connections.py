# electrophstat/gui/connections.py
from PyQt5.QtCore    import QObject, pyqtSlot
from PyQt5.QtWidgets import QAction


class pHStatConnections(QObject):
    """
    Encapsulates the logic for Start / Stop / Reset buttons in the pH-stat GUI.
    """
    def __init__(self, window):
        super().__init__(window)
        self.win = window
   
        # pHStat selector
        self.win.keepSelector.currentIndexChanged.connect(self.handle_select)
        self.win.phSpin.valueChanged.connect(self.handle_pH)
        # Pump calibration
        self.win.actionCalibrate_Pump.triggered.connect(self.openCalibratePumpWindow)

    @pyqtSlot()
    def handle_select(self, select):
            if select == 0:
                self.win.keepSelector.setCurrentIndex(0)
                self.win.statustext = "above"
            else:
                self.keepSelector.setCurrentIndex(1)
                self.win.statustext = "below"
            self.win.keepSelector.setStatusTip(f'Settings of pH Stat, Keep the experiment {self.win.statustext} a pH of {self.win.pHSelect}')
            #ConfigWriter(self)

    @pyqtSlot() 
    def handle_pH(self,pH):

        self.win.phSpin.setValue(pH)
        self.win.pHSelect = float(pH)
        self.win.phSpin.setStatusTip(f'Settings of pH Stat, Keep the experiment {self.win.statustext} a pH of {self.win.pHSelect}')
        #ConfigWriter(self)
        #print(f"Received signal with value: {value}")
        # Handle the change in the main GUI here
    
    @pyqtSlot() 
    def openCalibratePumpWindow(self):
        self.win.time_settings_window.exec_()
