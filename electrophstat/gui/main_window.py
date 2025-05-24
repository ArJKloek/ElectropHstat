import sys
import time
import os
import getpass
from electrophstat.io.usb_monitor import USBWorker
from electrophstat.gui.dialogs import DatePickerDialog, CalibratepHDialog
from electrophstat.connections.main_connections import setup_mainwindow_signals
from electrophstat.connections.button_connections import ButtonConnections
from electrophstat.connections.config_connections import init_config
from electrophstat.setup.pps_setup import init_psu
from electrophstat.setup.variables_setup import init_variables
from electrophstat.setup.logging_setup import init_logger
from electrophstat.setup.graphs_setup import init_graphs
from electrophstat.setup.phstat_setup import init_phstat
from electrophstat.setup.sensor_setup import init_sensors
from electrophstat.setup.scaling_setup import apply_scaling
from pathlib import Path


if sys.platform.startswith(("linux", "darwin")):
    # Only on UNIX-like systems
    if "XDG_RUNTIME_DIR" not in os.environ:
        os.environ["XDG_RUNTIME_DIR"] = f"/run/user/{os.getuid()}"

from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QMessageBox
from PyQt5.QtCore import pyqtSignal, QSize, QEvent

#import lib8mosind



class MainWindow(QMainWindow):
    startProcessingSignal = pyqtSignal()
    
    def __init__(self):
        super(MainWindow, self).__init__()


        uic.loadUi("electrophstat/gui/main_window.ui", self)


        init_variables(self)
        init_graphs(self)
        init_logger(self)
        init_config(self)
        init_psu(self)
        init_phstat(self)
        init_sensors(self)
         
        self.button_cont = ButtonConnections(self)

        self.date_time_dialog = DatePickerDialog()
        # 2) Now wire up every signal/slot in one place
        setup_mainwindow_signals(self)

        self.show()
        self.apply_scaling = apply_scaling
        self.apply_scaling()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.apply_scaling()
            
    def changeEvent(self, event):
        """
        Catch window‐state changes (maximize / minimize / fullscreen)
        and update your label accordingly.
        """
        super().changeEvent(event)

        if event.type() == QEvent.WindowStateChange:
            if self.isFullScreen():
                self.actionFullscreen.setText("Fullscreen on")
            elif self.isMaximized():
                self.actionFullscreen.setText("Maximized")
            else:
                self.actionFullscreen.setText("Normal")

    def exitApplication(self,event):
        # Create a confirmation dialog
        reply = QMessageBox.question(self, 'Exit?',
                                     "Are you sure you want to quit?",
                                     QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.No)

        if reply == QMessageBox.Yes:
            # Stop the worker
            #self.pHWorker.stop()
            #self.pHThread.quit()

            #self.RTDWorker.stop()
            #self.RTDThread.quit()

            #self.StatWorker.stop()
            #self.StatThread.quit()
            
            #self.USBWorker.stop()
            #self.USBThread.quit()
            
            event.accept()  # Accept the close event

        else:
            event.ignore()
    def closeEvent(self, event):
        # Optionally, you can also use the exitApplication method here
        self.exitApplication(event)
    
   
