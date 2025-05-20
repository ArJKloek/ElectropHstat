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
        # update the loop whenever the user flips the selector
 
    @pyqtSlot(int)
    def handle_select(self, select):
            print(select)
            if select == 0:
                self.win.statustext = "above"
            else:
                self.win.statustext = "below"
            self.win.keepSelector.setStatusTip(f'Settings of pH Stat, Keep the experiment {self.win.statustext} a pH of {self.win.pHSelect}')
            self.win.phstat_ctrl.loop.set_select(select)

            #ConfigWriter(self)

    @pyqtSlot(float) 
    def handle_pH(self,pH):

        self.win.phSpin.setValue(pH)
        self.win.pHSelect = float(pH)
        self.win.phSpin.setStatusTip(f'Settings of pH Stat, Keep the experiment {self.win.statustext} a pH of {self.win.pHSelect}')
        self.win.phstat_ctrl.loop.set_target_pH(pH)

        #ConfigWriter(self)
        #print(f"Received signal with value: {value}")
        # Handle the change in the main GUI here
    
    @pyqtSlot() 
    def openCalibratePumpWindow(self):
        self.win.time_settings_window.exec_()
