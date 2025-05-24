import sys
import time
import os
import getpass
from electrophstat.hardware.dummy_switcher import MockLib8MosInd
from electrophstat.io.logger import Logger
from electrophstat.control.pump_control import PumpController
from electrophstat.io.usb_monitor import USBWorker
from electrophstat.gui.dialogs import DatePickerDialog, CalibratepHDialog, CalibratePumpDialog
from electrophstat.control.timer_control import monoTimer
from electrophstat.io.power_logger import PowerLogger
from electrophstat.connections.main_connections import setup_mainwindow_signals, find_data_directory
from electrophstat.connections.button_connections import ButtonConnections
from electrophstat.connections.pHstat_connections import pHStatConnections
from electrophstat.gui.graph_controller import GraphController
from electrophstat.gui.plot_manager import PlotManager
from electrophstat.gui.sensor_controller import SensorController
from electrophstat.gui.phstat_controller import pHStatController
from electrophstat.gui.logging_controller import LoggingController
#from electrophstat.io.config import Config
from electrophstat.connections.config_connections import init_config
from electrophstat.setup.pps_setup import init_psu
from electrophstat.setup.variables_setup import init_variables
from electrophstat.setup.logging_setup import init_logger
from electrophstat.setup.graphs_setup import init_graphs
from pathlib import Path


if sys.platform.startswith(("linux", "darwin")):
    # Only on UNIX-like systems
    if "XDG_RUNTIME_DIR" not in os.environ:
        os.environ["XDG_RUNTIME_DIR"] = f"/run/user/{os.getuid()}"

from PyQt5 import uic
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QGridLayout, 
                             QLabel, QMenuBar, QAction, QStatusBar, 
                             QComboBox, QDoubleSpinBox, QHBoxLayout, QVBoxLayout, 
                             QPushButton, QTabWidget, QFrame, QMenu, QMessageBox, QActionGroup, QDial, QToolTip, QCheckBox, QSizePolicy, QToolButton)
from PyQt5.QtGui import QFont, QColor, QIcon, QPen, QTransform, QPalette
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QMetaObject, pyqtSlot, QTimer, QMutex, QSize, QPoint, QDateTime, QEvent

#import lib8mosind


lib8mosind = MockLib8MosInd()

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

        self.calibrate_pump_dialog = CalibratePumpDialog(float(self.pump_volume_per_cycle_ml), float(self.pump_cycle_duration_s), self)
        self.pH_calibrate_dialog = CalibratepHDialog(float(self.pH_calibration_low),float(self.pH_calibration_mid),float(self.pH_calibration_high),self)
        self.date_time_dialog = DatePickerDialog()
        
        #self.time_settings_window.select_changed.connect(self.handle_time)
        #self.time_settings_window.test_pump.connect(self.pumpInput)

        #self.pH_calibrate_window = CalibratepHDialog(float(self.lowpH), float(self.midpH), float(self.highpH))
        #self.pH_calibrate_window.calibrate_changed.connect(self.handle_calibrate)
        
        

        #self.control_loop = ControlLoop(
        #    select=self.pHSelectMode,   # 0=above-limit, 1=below-limit
        #    target_pH=self.pHSelect
        #)

        
    
        #self.logger = Logger(
        #    filepath="ph_control_log.csv",
        #    fieldnames=["timestamp", "pH", "pump_on", "status"]
        #) 
        self.pump_ctrl = PumpController(
            hw=lib8mosind,
            logger=self.logger,
            duration_s=float(self.pump_cycle_duration_s),
            ml_per_cylce = float(self.pump_volume_per_cycle_ml),
            parent=self
        )
        

         # Map each registry key to the slot you already have
       
        # 1) Load the .ui file

        self.button_cont = ButtonConnections(self)
        self.pHstat_cont = pHStatConnections(self)
       # instantiate controllers (they subclass QObject)
        #self.pps_controller = PPSController(self)
        #self.ppsWorker.disconnected_signal.connect(self.pps_controller.on_pps_disconnect)

        # This will spin up worker+thread for each key
        # Initialize PPS Connections for updating the GUI
        self.phstat_ctrl = pHStatController(self, interval=1.0)
        
        slots = {
            "pH":   [self.button_cont.update_gui],
            "temperature": [self.button_cont.update_gui],
        }

        self.sensor_ctrl = SensorController(self, update_slots=slots, interval=1.0)
        self.phstat_ctrl = pHStatController(self, interval=1.0, cooldown=self.pump_cooldown_duration_s)
        self.pHstat_cont.handle_select(self.config.pH_control_mode)
        self.pHstat_cont.handle_pH    (self.config.pH_target)
        
        
        pH_worker = self.sensor_ctrl.pH_worker
        # connect your dialog
        self.pH_calibrate_dialog.calibrate_changed.connect(
            lambda mode, val, _: pH_worker.calibrate_signal.emit(mode, val)
        )
        # Initialize PPS controller with proper interval (e.g., 1 second) and reset condition

        self.calibrate_pump_dialog.test_pump.connect(
            self.pump_ctrl.on_test_pump
        )

        # wire “Set” → PumpController
        self.calibrate_pump_dialog.select_changed.connect(
            self.pump_ctrl.on_set_calibration
        )
        # 2) Now wire up every signal/slot in one place
        setup_mainwindow_signals(self)
        
        #ph_worker = self.sensor_ctrl.ph_worker
        #ph_worker.data_signal.connect(self.phstat_ctrl.on_pH_read)

        #self.logger = Logger(
        #    base_dir=Path.home()/"ElectroPHData",
        #    labels=["pH","temperature","volume"],
        #    column_names=["pH","°C","mL"]
        #)

        #self.initTimer()
        #self.initWorkerTimer()
        #self.initCalcTimer()
        #self.logging_timer = monoTimer()
        #QTimer.singleShot(0, self.option3.trigger)
        #self.toggle_pHStat(False)
        #self.toggle_pH_control.trigger()

        self.show()
        self._apply_scaling()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._apply_scaling()
        
    def _apply_scaling(self):
        # Get current window size
        width = self.width()
        height = self.height()

        # Base scaling factor
        scale = min(width / 960, height / 600)
        font_size = (18 * scale)
        
        border_size = (2 *scale)
        
        start_padding = int(12 * scale)
        stop_padding = int(10 * scale)
        reset_padding = int(8 * scale)
        
        start_width = int(120 * scale)
        stop_width = int(100 * scale)
        reset_width = int(90 * scale)

        start_height = int(70 * scale)
        stop_height = int(55 * scale)
        reset_height = int(40 * scale)
        
        
        label_size = int(13 * scale)
        tick_size = int(11 * scale)

        for plot in self.graphWidgets:
            self.plot_manager._scale_graph_fonts(plot, label_size, tick_size)

        
        dial_size = int(70 * scale)
        self.voltageDial.setFixedSize(dial_size, dial_size)
        self.currentDial.setFixedSize(dial_size, dial_size)
        
        #self.modeToggle.setH_scale(0.55*scale)
        #self.modeToggle.setV_scale(0.55*scale)
        modeToggle_size = (0,55*scale)
        #self.modeToggle.setHitSize(modeToggle_size,modeToggle_size)
        
        #self.modeToggle.setFontSize(9*scale)

        powerButton_width = int(60 * scale)
        powerButton_height = int(40 * scale)
        self.powerButton.setFixedSize(powerButton_width, powerButton_height)
        

        usb_button_size = int(60 * scale)
        usb_button_icon = int(55 * scale)
        self.usb_button.setMinimumSize(usb_button_size, usb_button_size)
        self.usb_button.setIconSize(QSize(usb_button_icon, usb_button_icon))
        
        button_size = int(60 * scale)  # scale from window size
        #self.toolButton.setFixedSize(button_size,button_size)
        
        self.setButton.setFixedSize(button_size, button_size)


        def set_font(widget, base_size):
            if widget is not None:
                font = widget.font()
                font.setPointSizeF(base_size * scale)
                widget.setFont(font)
        
        #self.pHstatLabel.setFontsize(13 * scale)
        #self.pumpLabel.setFontsize(13 * scale)

        # Adjust fonts on key widgets
        #set_font(self.pHNumber, 35)
        set_font(self.pHNumber, 25)
        set_font(self.RTDlabel, 18)
        #set_font(self.selectlabel, 20)
        set_font(self.phSpin, 10)
        set_font(self.keepSelector, 10)
        set_font(self.voltagelabel, 16)
        set_font(self.currentlabel, 16)
        set_font(self.modelabel, 16)
        #set_font(self.voltageDiallabel, 10)
        # Update Start button stylesheet with dynamic font size
        start_style = f"""
            QPushButton {{
                background-color: #52BE80;
                font-size: {font_size}pt;
                font-weight: bold;
                padding: {start_padding}px;
                min-width: {start_width}px;
                min-height: {start_height}px;
                border: {border_size}px solid #229954;  
                border-radius: 12px; 
            }}
            QPushButton:pressed {{
                background-color: #229954;
                border: {border_size}px solid #1A7F42;

            }}
            QPushButton:disabled {{
                background-color: #D4EFDF;
                border: {border_size}px solid #A9DFBF;

            }}
        """
        stop_style = f"""
            QPushButton {{
                background-color: #C0392B;
                color: white;
                font-size: {font_size}pt;
                font-weight: bold;
                padding: {stop_padding}px;
                min-width: {stop_width}px;
                min-height: {stop_height}px;
                border: {border_size}px solid #922B21;
                border-radius: 12px; 

            }}
            QPushButton:pressed {{
                background-color: #922B21;
                border: {border_size}px solid #641E16;
            }}
            QPushButton:disabled {{
                color: lightGray;
                background-color: #FDEDEC;
                border: {border_size}px solid #FADBD8;
            }}
        """
        reset_style = f"""
            QPushButton {{
                background-color: #F1C40F;
                color: black;
                font-size: {font_size}pt;
                font-weight: bold;
                padding: {reset_padding}px;
                min-width: {reset_width}px;
                min-height: {reset_height}px;
                border: {border_size}px solid #B7950B; 
                border-radius: 12px; 

            }}
            QPushButton:pressed {{
                background-color: #B7950B;
                border: {border_size}px solid #9A7D0A;

            }}
            QPushButton:disabled {{
                color: lightGray;
                background-color: #FEF9E7;
                border: {border_size}px solid #FCF3CF;

            }}
        """

        self.startbutton.setStyleSheet(start_style)
        self.stopbutton.setStyleSheet(stop_style)
        self.resetbutton.setStyleSheet(reset_style)
    
        tab_font_size = int(10 * scale)
        tab_height = int(20 * scale)
        tab_width = int(110 * scale)
        tab_padding = int(5 * scale)

        tab_style = f"""
            QTabBar::tab {{
                font-size: {tab_font_size}pt;
                height: {tab_height}px;
                width: {tab_width}px;
                padding: {tab_padding}px;
            }}
        """
        self.tabWidget.setStyleSheet(tab_style)

    
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
    
   
