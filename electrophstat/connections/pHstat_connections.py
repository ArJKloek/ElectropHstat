# electrophstat/gui/connections.py
from PyQt5.QtCore    import pyqtSlot
from PyQt5.QtWidgets import QAction

def setup_pHstat_signals(win):
    # pHStat selector
    win.keepSelector.currentIndexChanged.connect(win.handle_select)
    win.phSpin.valueChanged.connect(win.handle_pH)
    # Pump calibration
    win.actionCalibrate_Pump.triggered.connect(win.openCalibratePumpWindow)
    