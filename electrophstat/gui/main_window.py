import sys
import time
import os
import getpass
from electrophstat.gui.dialogs import DatePickerDialog
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
from electrophstat.setup.settings_setup import init_settings
from electrophstat.setup.turbidity_setup import init_turbidity
from electrophstat.setup.usb_setup import init_usb

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
        init_config(self)
        init_graphs(self)
        init_logger(self)
        print(f"Logger initialized with labels: {self.logger.labels}")

        init_psu(self)
        init_phstat(self)
        init_settings(self) 
        init_turbidity(self)
        init_usb(self)

        self.button_cont = ButtonConnections(self)
        
        init_sensors(self)

        self.date_time_dialog = DatePickerDialog()
        # 2) Now wire up every signal/slot in one place
        setup_mainwindow_signals(self)
        

        self.show()
        apply_scaling(self)
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        apply_scaling(self)
            
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

    
    
    def stop_all_workers(self):
        # Stop Graphs
        if hasattr(self, "graphs_ctrl"):
            self.graphs_ctrl.stop()
        # Stop Sensor workers
        if hasattr(self, "sensor_ctrl"):
            self.sensor_ctrl.stop() 
        # Stop pHStat worker
        if hasattr(self, "phstat_ctrl"):
            if self.phstat_ctrl is not None:
                self.phstat_ctrl.stop()
        # Stop PSU worker
        if hasattr(self, "pps_ctrl"):
            if self.pps_ctrl is not None:
                if self.pps_ctrl.pps_worker is not None:
                    self.pps_ctrl.stop()
        # Stop Loggin worker
        if hasattr(self, "logging_ctrl"):
            self.logging_ctrl.stop()
        # Stop USB worker
        if hasattr(self, "usb_ctrl"):
            self.usb_ctrl.stop()

        
    
    
    def closeEvent(self, event):
        # Ask for confirmation first
        reply = QMessageBox.question(
            self, 'Exit?',
            "Are you sure you want to quit?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.stop_all_workers()
            event.accept()
        else:
            event.ignore()


