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
            if select == 0:
                self.win.statustext = "above"
            else:
                self.win.statustext = "below"
            self.win.keepSelector.setStatusTip(f'Settings of pH Stat, Keep the experiment {self.win.statustext} a pH of {self.win.pH_target}')
            self.win.phstat_ctrl.loop.set_select(select)
            self.win.config.pH_control_mode = select
            
    @pyqtSlot(float) 
    def handle_pH(self,pH):

        self.win.phSpin.setValue(pH)
        self.win.pH_target = float(pH)
        self.win.phSpin.setStatusTip(f'Settings of pH Stat, Keep the experiment {self.win.statustext} a pH of {self.win.pH_target}')
        self.win.phstat_ctrl.loop.set_target_pH(pH)
        self.win.config.pH_target = round(pH,2)

       
    @pyqtSlot() 
    def openCalibratePumpWindow(self):
        self.win.calibrate_pump_dialog.exec_()

    
