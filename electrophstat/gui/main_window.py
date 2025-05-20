import sys
import time
import os
import getpass
from electrophstat.hardware.dummy_switcher import MockLib8MosInd
#from electrophstat.control.phstat_control import ControlLoop, PumpAction
from electrophstat.io.logger import Logger
from electrophstat.control.pump_control import PumpController
from electrophstat.io.usb_monitor import USBWorker
from electrophstat.gui.dialogs import DatePickerDialog, CalibratepHDialog, CalibratePumpDialog
from electrophstat.gui.widgets import CustomTextWidget, ToggleSwitch
from electrophstat.control.timer_control import monoTimer
from electrophstat.io.power_logger import PowerLogger
from electrophstat.connections.main_connections import setup_mainwindow_signals
from electrophstat.connections.button_connections import ButtonConnections
from electrophstat.connections.pHstat_connections import pHStatConnections
from electrophstat.gui.graph_controller import GraphController
from electrophstat.gui.plot_manager import PlotManager
from electrophstat.gui.sensor_controller import SensorController
from electrophstat.gui.pps_controller import PPSController
from electrophstat.connections.pps_connections import PPSConnections
from electrophstat.gui.phstat_controller import pHStatController
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

from scripts.pHstat_config import ConfigReader, ConfigWriter
#import lib8mosind


lib8mosind = MockLib8MosInd()

class MainWindow(QMainWindow):
    startProcessingSignal = pyqtSignal()
    
    def __init__(self):
        super(MainWindow, self).__init__()




        self.setupVariables()

        self.calibrate_pump_window = CalibratePumpDialog(float(self.ml), float(self.addtime))
        #self.time_settings_window.select_changed.connect(self.handle_time)
        #self.time_settings_window.test_pump.connect(self.pumpInput)

        #self.pH_calibrate_window = CalibratepHDialog(float(self.lowpH), float(self.midpH), float(self.highpH))
        #self.pH_calibrate_window.calibrate_changed.connect(self.handle_calibrate)
        
        

        #self.control_loop = ControlLoop(
        #    select=self.pHSelectMode,   # 0=above-limit, 1=below-limit
        #    target_pH=self.pHSelect
        #)

        home = Path.home()  # or wherever you like
        labels  = ["pH", "temperature", "volume"]
        columns = ["pH", "°C", "mL"]
        self.logger = Logger(home / "ElectroPHData", labels, columns)
        #self.logger = Logger(
        #    filepath="ph_control_log.csv",
        #    fieldnames=["timestamp", "pH", "pump_on", "status"]
        #) 
        self.pump_ctrl = PumpController(
            hw=lib8mosind,
            logger=self.logger,
            duration_s=self.pumpDurationSeconds,
            ml_per_cylce = 10,
            parent=self
        )
        
        uic.loadUi("electrophstat/gui/main_window.ui", self)

         # Map each registry key to the slot you already have
       
        # 1) Load the .ui file

        self.button_cont = ButtonConnections(self)
        self.pHstat_cont = pHStatConnections(self)
        # instantiate controllers (they subclass QObject)
        #self.pps_controller = PPSController(self)
        #self.ppsWorker.disconnected_signal.connect(self.pps_controller.on_pps_disconnect)

        
        self.pps_connections = PPSConnections(self)

        self.pps_ctrl = PPSController(self, self.pps_connections,
                                      interval=1.0,  # poll every second
                                      reset=True)    # whether to reset on open

        # This will spin up worker+thread for each key
        # Initialize PPS Connections for updating the GUI
        slots = {
            "ph":  [ self.button_cont.update_gui,],
            "temp": self.button_cont.update_gui,
            # once you register an "orp" sensor, you could add
            # "orp": self.handle_ORP,
        }
        self.sensor_ctrl = SensorController(self, update_slots=slots, interval=1.0)
        self.phstat_ctrl = pHStatController(self, interval=1.0)

        # Initialize PPS controller with proper interval (e.g., 1 second) and reset condition


        # 2) Now wire up every signal/slot in one place
        setup_mainwindow_signals(self)
        
        self.plot_manager = PlotManager(self)
        self.graph_ctrl = GraphController(self.tabWidget, self.plot_manager)
        self.logging_timer = monoTimer()

        ph_worker = self.sensor_ctrl.ph_worker
        #ph_worker.data_signal.connect(self.phstat_ctrl.on_pH_read)

        
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
        
        self.modeToggle.setH_scale(0.55*scale)
        self.modeToggle.setV_scale(0.55*scale)
        self.modeToggle.setFontSize(9*scale)
        powerButton_width = int(60 * scale)
        powerButton_height = int(40 * scale)
        self.powerButton.setFixedSize(powerButton_width, powerButton_height)
        
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

    def setupVariables(self):
        self.pump_start_time = None  # Initialize a variable to store the start time
        self.elapsed_time = None
        self.totalml = 0
        self.pH_label = []
        self.send_counter = time.time()
        self.read = False
        self.test_time = time.time()
        self.pHdata = 9.9
        self.temp = 20
        #self.dev = 1#atlas_i2c(address=address)
        #self.pHdev = atlas_i2c(address=99)
        #self.RTDdev = atlas_i2c(address=102)
        #self.log_interval = 0
        self.Ref_path = ''
        self.pHSelect = 0.0
        self.Select = 0
        self.ml = 0
        self.injections = 0
        self.addtime = 0
        #self.pHvalue = 0
        #self.RTDvalue = 0
        self.valueData = [0,0,0,0,0,0]
        self.cooldown = 0
        self.currentActiveTabIndex = 0  # Track the current tab index
        self.graphTabs = []
        self.graphWidgets = []
        self.plotindex = ["Pump", "pH" , "RTD", "Volt", "Amp", "Coulomb"]
        self.headerindex = ["Pumped (ml)", "pH", "Temperature (°C)", "Voltage (V)", "Current (A)", "Coulomb (C)"]
        self.Log_file = ["","","","","",""]
        self.Log_date = [0,0,0,0,0,0]
        self.is_logging = False
        self.statustext = ""
        self.lowpH = 0.0
        self.midpH = 0.0
        self.highpH = 0.0
        self.copy_path = ""
        #self.log_interval = 500
        self.viewBoxes = {}  # In __init__ or setupVariables()
        self.rightViewBoxes = {}
        self.PStype = [0,0,0,0]
        self.start = False
        self.pHSelectMode = 1 
        self.pumpDurationSeconds = 1
        ConfigReader(self)

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
    
   
