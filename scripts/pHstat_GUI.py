import sys
import time
import os
import getpass
from electrophstat.hardware import discover_power_supply
from electrophstat.hardware.dummy_switcher import MockLib8MosInd
from electrophstat.sensors import discover_ph_sensor
from electrophstat.sensors import discover_temp_sensor
from scripts.ph_sensor_worker import pHSensorWorker
from electrophstat.control.phstat_control import ControlLoop, PumpAction
from electrophstat.io.logger import Logger
from electrophstat.control.pump_control import PumpController
from electrophstat.io.usb_monitor import USBWorker
from electrophstat.gui.dialogs import DatePickerDialog, CalibratepHDialog, CalibratePumpDialog
from electrophstat.gui.widgets import CustomTextWidget, ToggleSwitch
from electrophstat.control.timer_control import monoTimer
from electrophstat.io.power_logger import PowerLogger
from electrophstat.connections.main_connections import setup_mainwindow_signals
from electrophstat.connections.pHstat_connections import setup_pHstat_signals
from electrophstat.controllers.pps_controllers import PPSController
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
from scripts.LedIndicatorWidget import LedIndicator
#from scripts.pHStat_worker import pHWorker, RTDWorker, StatWorker, USBWorker, i2c_mutex
#from scripts.pHStat_worker import USBWorker
from electrophstat.workers.pps_worker import PPSWorker
from scripts.pHstat_config import ConfigReader, ConfigWriter
#from scripts.pHStat_classes import (pumpControl)
import pyqtgraph as pg
#from pyqtgraph.Qt import QtGui, QtWidgets
#import numpy as np
#from scripts.pHStat_csv import create_csv, log_csv, read_log_data, scale_time_data
#from scripts.atlas import atlas_i2c
import datetime
import shutil
import re
#import lib8mosind
import serial.tools.list_ports
#from voltcraft.pps import PPS
from scripts import PlotManager, Fusion3DToggle, RoundSetButton, Push3DButton, Round3DButton #, atlas_i2c


lib8mosind = MockLib8MosInd()


def find_voltcraft_pps() -> str or None:
    ports = serial.tools.list_ports.comports()

    for port in ports:
        if "USB" not in port.device:
            continue  # only ttyUSB*

        try:
            print(f"Trying {port.device}...")
            pps = PPS(port.device, reset=False)  # Don't reset for testing
            # Accessing a property forces communication
            print(f"✓ Found PPS on {port.device} (Model: {pps.MODEL})")
            return port.device
        except Exception as e:
            print(f"✗ {port.device} not PPS: {e}")
            continue

    print("❌ No Voltcraft PPS detected.")
    return None

#from date_window import DatePickerDialog
def scale_graph_fonts(widget, label_size, tick_size):
        if widget is None:
            return

        labelStyle = {'color': 'black', 'font-size': f'{label_size}pt'}
        
        # Axis labels
        for axis in ['left', 'bottom', 'right', 'top']:
            ax = widget.getAxis(axis)
            if ax is not None:
                ax.setStyle(tickFont=QFont('Arial', tick_size))
                ax.setTextPen(QPen(QColor('black')))
                if axis in ['left', 'bottom', 'right']:
                    # Keep original label text
                    label = ax.labelText
                    if label:
                        ax.setLabel(label, **labelStyle)
            

class MainWindow(QMainWindow):
    startProcessingSignal = pyqtSignal()
    
    def __init__(self):
        super(MainWindow, self).__init__()




        self.setupVariables()

        self.time_settings_window = CalibratePumpDialog(float(self.ml), float(self.addtime))
        self.time_settings_window.select_changed.connect(self.handle_time)
        #self.time_settings_window.test_pump.connect(self.pumpInput)

        self.pH_calibrate_window = CalibratepHDialog(float(self.lowpH), float(self.midpH), float(self.highpH))
        self.pH_calibrate_window.calibrate_changed.connect(self.handle_calibrate)
        
        #self.pump_control = pumpControl(self)
        #self.pump_control.pumpActivated.connect(self.pump_activated)
        #self.pump_control.pumpDeactivated.connect(self.pump_deactivated)
        

        self.control_loop = ControlLoop(
            select=self.pHSelectMode,   # 0=above-limit, 1=below-limit
            target_pH=self.pHSelect
        )

        home = Path.home()  # or wherever you like
        labels  = ["pH", "temperature", "volume"]
        columns = ["pH", "°C", "mL"]
        self.logger = Logger(home / "ElectroPHData", labels, columns)
        #self.logger = Logger(
        #    filepath="ph_control_log.csv",
        #    fieldnames=["timestamp", "pH", "pump_on", "status"]
        #) 
        self.pump_controller = PumpController(
            start_fn=self.startPump,
            stop_fn=self.stopPump,
            duration_s=self.pumpDurationSeconds,
            parent=self
        )

        # 1) Load the .ui file
        uic.loadUi("electrophstat/gui/main_window.ui", self)
        self.setupPPSWorker()

        # instantiate controllers (they subclass QObject)
        self.pps_controller = PPSController(self)
        self.ppsWorker.disconnected_signal.connect(self.pps_controller.on_pps_disconnect)

        # 2) Now wire up every signal/slot in one place
        setup_mainwindow_signals(self)
        setup_pHstat_signals(self)
        
        self.plot_manager = PlotManager(self)

        self.initializeGraphTabs()
        self.initializeTabTimer()
        #self.addGraphTab()
        self.handle_select(int(self.Select))#, float(self.pHSelect))
        self.handle_pH(float(self.pHSelect))
        self.handle_time(float(self.ml), float(self.addtime))
        
        self.initpHSensor()
        self.initTempSensor()
        
        self.initTimer()
        self.initWorkerTimer()
        self.initCalcTimer()
        self.logging_timer = monoTimer()
        QTimer.singleShot(0, self.option3.trigger)
        #self.toggle_pHStat(False)
        self.toggle_pH_control.trigger()

        self.show()

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
            scale_graph_fonts(plot, label_size, tick_size)

        
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

    def reconnectPPS(self):
        print("[PPS] Attempting to reconnect power supply...")

        # Stop existing worker if running
        try:
            self._stop_pps()
            print("[PPS] Existing PPSWorker stopped.")
        except Exception as e:
            print(f"[PPS] Error stopping old PPSWorker: {e}")

        # Try to set up again
        try:
            self.setupPPSWorker()
            print("[PPS] Reconnected.")
            self.initializeGraphTabs()
            self._apply_scaling()
        except Exception as e:
            print(f"[PPS] Reconnect failed: {e}")
            QMessageBox.critical(self, "Reconnect Failed", f"Could not reconnect to PPS:\n{e}")
    
    def initTempSensor(self):
        temp = discover_temp_sensor()
        self.tempThread = QThread()
        self.tempWorker = pHSensorWorker(temp, interval=2.0)
        self.tempWorker.moveToThread(self.tempThread)

        # lambda injects “2” so update_gui knows it’s temperature
        self.tempWorker.value_signal.connect(lambda v: self.update_gui(v, 2))
        self.tempWorker.disconnected_signal.connect(
            lambda: self.update_gui(float("nan"), 2)
        )

        self.tempThread.started.connect(self.tempWorker.run)
        self.tempThread.start()

    def on_pH_read(self, pH: float):
        """Pure‐logic handler: run ControlLoop and Logger, update pump/status."""
        action = self.control_loop.process(pH)


            # If not started yet, skip control & logging
        if not self.control_loop.should_start:
            return

        # Run the control logic
        action = self.control_loop.process(pH)

        # Drive the pump & auto-off
        self.pump_controller.execute(action)

        # Update status label
        self.status_label.setText("OK" if action.status else "Out of range")

        # Log the decision
        timestamp = QDateTime.currentDateTime().toString(Qt.ISODate)
        self.logger.log({
            "timestamp": timestamp,
            "pH": pH,
            "pump_on": action.pump_on,
            "status": action.status,
        })

    
    def startPump(self):
        """Turn on the pump via the PPSWorker interface."""
        try:
            lib8mosind.set(0,1,1)
        except Exception as e:
            print(f"Failed to start pump: {e}")

    def stopPump(self):
        """Turn off the pump via the PPSWorker interface."""
        try:
            lib8mosind.set(0,1,0)
        except Exception as e:
            print(f"Failed to stop pump: {e}")


    def initpHSensor(self):
        sensor = discover_ph_sensor()
        self.pHThread = QThread()
        self.pHWorker = pHSensorWorker(sensor, interval=2.0)
        self.pHWorker.moveToThread(self.pHThread)

        self.pHWorker.value_signal.connect(self.update_gui)     # GUI slot
        self.pHWorker.value_signal.connect(self.on_pH_read)     # GUI slot

        self.pHWorker.disconnected_signal.connect(self.on_ph_disconnect)

        self.pHThread.started.connect(self.pHWorker.run)
        self.pHThread.start()

    def on_ph_disconnect(self):
        print("[pH] sensor lost – switching to N/A")
        self.pHLabel.setText("pH: N/A")

    
    
    def toggle_pHStat(self, checked):
        self.pH_control_enabled = checked
        if self.pH_control_enabled:
            print("pH Control enabled")
            try:
                # Connect signals
                #self.startProcessingSignal.connect(self.StatWorker.start_processing)
                #self.pHWorker.value_signal.connect(self.StatWorker.update_pH)
                #self.pH_settings_window.select_changed.connect(self.StatWorker.update_pH_select)
                
                #self.select_settings_window.select_changed.connect(self.StatWorker.update_select)
                
                #self.StatWorker.status_signal.connect(self.handle_Stat)
                #self.StatWorker.pump_signal.connect(self.pumpInput)
                # Update labels
                self.pHstatLabel.setDisabled(False)
                self.pHstatLabel.updateText("Active")
                self.pHstatLabel.updateNormalColor(Qt.black)
                self.pumpLabel.setDisabled(False)
                self.pumpLabel.updateText("Active")
                self.pumpLabel.updateNormalColor(Qt.black)
                # Enable clickalble labels
                self.phSpin.setDisabled(False)
                self.keepSelector.setDisabled(False)
                #self.pHSelectLabel.setEnabled(checked)
                
            except Exception as e:
                print(f"Reconnect error (probably already connected): {e}")
        
             # Re-add Pump plot if missing
            if self.tabWidget.indexOf(self.graphTabs[0]) == -1:
                self.tabWidget.insertTab(0, self.graphTabs[0], "Pump Plot")
        
        else:
            print("pH Control disabled")
            try:
                #Disconnect signals
                #self.startProcessingSignal.disconnect(self.StatWorker.start_processing)
                #self.pHWorker.value_signal.disconnect(self.StatWorker.update_pH)
                #self.select_settings_window.select_changed.disconnect(self.StatWorker.update_select)
                #self.StatWorker.status_signal.disconnect(self.handle_Stat)
                #self.StatWorker.pump_signal.disconnect(self.pumpInput)
                #Update labels
                self.pHstatLabel.setDisabled(True)
                self.pHstatLabel.updateText("Inactive")
                self.pHstatLabel.updateNormalColor(Qt.gray)
                self.pumpLabel.setDisabled(True)
                self.pumpLabel.updateText("Inactive")
                self.pumpLabel.updateNormalColor(Qt.gray)
                #Disable clickable labels
                self.phSpin.setDisabled(True)
                self.keepSelector.setDisabled(True)
                #self.pHSelectLabel.setEnabled(checked)
               
            except Exception as e:
                print(f"Disconnect error (probably already disconnected): {e}")

            # Extra: If pump is running, deactivate it immediately
            self.pump_deactivated(test=False)

            # Also stop the StatWorker if needed
            try:
                self.StatWorker.stop()
                print("StatWorker stopped.")
            except Exception as e:
                print(f"Error stopping StatWorker: {e}")
            # Manage the graph tabs (disable Pump plot, focus on pH+Temp plot)
            pump_index = self.tabWidget.indexOf(self.graphTabs[0])
            if pump_index != -1:
                self.tabWidget.removeTab(pump_index)

            ph_index = self.tabWidget.indexOf(self.graphTabs[1])
            if ph_index != -1:
                self.tabWidget.setCurrentIndex(ph_index)
   
        # Create actions for settings_menu
    def option_selected(self):
        action = self.sender()  # The QAction that triggered the signal
        if action and action.isChecked():
            self.log_interval = action.data()  # Get the attached value
            self.logtimer.setInterval(int(self.log_interval))
            self.logtimer.start(int(self.log_interval))
            #print(f"Log timer interval updated to {self.log_interval} ms")

    def keep_selector_changed(self, index):
        try:
            self.StatWorker.update_select(index)
        except Exception:
            pass   
        self.handle_select(index)

    def pH_selector_changed(self, value):
        pH_select = round(value,1)
        try:
            self.StatWorker.update_pH_select(pH_select)
        except Exception:
            pass
        self.handle_pH(pH_select)        
    
    def force_power_off(self):
        if self.powerButton.isChecked():
            self.powerButton.setChecked(False)  # uncheck the button
            self.ppsWorker.set_output(False)    # turn off power supply
            if self.start:
                self.logger.log_change("Power", "FORCED OFF")

    #def apply_ps_settings(self):
    #    if not hasattr(self, 'ppsWorker'):
    #        return
    #    # Read toggle state (assuming you're using your ToggleSwitch class)
    #    mode = "CC" if self.modeToggle.isChecked() else "CV"

    #    # Get dial values
    #    voltage = self.voltageDial.value() / 10.0  # Assuming 0.1 V steps
    #    current = self.currentDial.value() / 10.0  # Assuming 0.1 A steps

        # Ensure PPS is connected and worker exists
     #   if hasattr(self, 'ppsWorker') and hasattr(self.ppsWorker, 'pps'):
     #       if mode == "CV":
                # Constant Voltage: set voltage, allow max current
      #          self.ppsWorker.set_current(self.ppsWorker.pps.IMAX)
      #          self.ppsWorker.set_voltage(voltage)
      #      else:
                # Constant Current: set current, allow max voltage
       #         self.ppsWorker.set_voltage(self.ppsWorker.pps.VMAX)
        #        self.ppsWorker.set_current(current)

         #   print(f"[SET] Mode: {mode}, Voltage: {voltage:.1f} V, Current: {current:.1f} A")
          #  if self.start: self.logger.setting_change(voltage, current, mode)
           # else: pass

    def update_mode_label(self, state):
        mode = "CC" if state == Qt.Checked else "CV"
        print(f"Mode switched to: {mode}")
   
    def delayed_show_fullscreen(self):
        QTimer.singleShot(100, self.toggle_fullscreen)  # Delayed fullscreen after 100 milliseconds
    
    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            self.actionFullscreen.setText("Fullscreen on")
        else:
            self.showFullScreen()
            self.actionFullscreen.setText("Fullscreen off")

    def pHlabelClicked(self):
        print('pH label clicked')
    #def selectlabelClicked(self):
    #    print("select label clicked")

    def initializeTabTimer(self):
        self.tabtimer = QTimer()
        self.tabtimer.timeout.connect(self.updateCurrentTabPlot)
        self.tabtimer.start(1000)  # Update every second

    def _tab_exists(self, title: str) -> bool:
        """Return True if a tab with *title* is already present."""
        for i in range(self.tabWidget.count()):
            if self.tabWidget.tabText(i) == title:
                return True
        return False
        
    def initializeGraphTabs(self):
           # only create the tab manager once
        if not hasattr(self, "plot_manager"):
            self.plot_manager = PlotManager(self)
        #self.graphWidgets = []
        #self.graphTabs = []

        # Add Pump plot
        #self.addGraphTab("Pump Plot", ("Time (s)", "Added (ml)"))
        specs = [
            ("Pump Plot",       dict(plot_index=0, left_label="Added (ml)")),
            ("pH + Temp Plot",  dict(plot_index=1, left_label="pH",
                                    right_label="Temperature", right_units="°C")),
            ("Power Plot",      dict(plot_index=2, left_label="Voltage (V)",
                                    right_label="Amperage",     right_units="A")),
            ("Coulomb",         dict(plot_index=3, left_label="Coulomb (C)")),
        ]
        for title, kwargs in specs:
            if self._tab_exists(title):
                continue                      # ← already present – skip
            self.plot_manager.addGraphTab(title=title, **kwargs)
        
      
        #self.plot_manager.addPowerGraphTab("Power Plot")
        #self.plot_manager.addCoulombGraphTab("Coulomb Plot")

        # (Optional) Add RTD plot separately if you still want individual
        
    def updatePlot(self, tab):
        self.plot_manager.update(tab)
        
    def updateCurrentTabPlot(self):
        # Get the current widget (tab)
        current_tab = self.tabWidget.currentWidget()
        self.updatePlot(current_tab)
        
   #def updateCurrentTabPlot(self):
        # Update the plot of the current active tab

    def updateCoulombs(self):
        dt = self.coulombClock.lap()  # Time since last update
        amps = getattr(self, 'latest_current', 0)
        self.coulombs += amps * dt
        self.update_gui(self.coulombs,5)
        #print(f"Coulombs: {self.coulombs:.2f}")
        #self.coulombLabel.setText(f"Coulombs: {self.coulombs:.2f}")

    def onTabChanged(self, index):
        self.currentActiveTabIndex = index
        # Optionally reset the timer or perform other actions
        # self.timer.start(1000)  # Restart the timer if needed

    def toggle_logging(self):
        self.is_logging = not self.is_logging  # This is a boolean attribute to keep track of logging status

    def initWorkerTimer(self):
        self.pauzeWorker = QTimer(self)
        self.pauzeWorker.setSingleShot(True)
        self.pauzeWorker.timeout.connect(self.WorkerTimerFinished)
    
    def initCalcTimer(self):
        self.CalcWorker = QTimer(self)
        self.CalcWorker.setSingleShot(True)
        self.CalcWorker.timeout.connect(self.CalcWorkerRead)
    
    def CalcWorkerRead(self):
        retry_count = 5 # Number of times to retry
        retry_delay = 0.01 # Delay between retries in second
        success = False # Flag indicating succes
        
        for attempt in range(retry_count):
            
            try:
                #i2c_mutex.lock()
                pHdata = self.pHdev.read()   
                success = True
                break # Exit the function if succesvol
            except Exception as e:
                print(f"Error during read: {e}")
                pass
            finally:
                try:
                    #i2c_mutex.unlock()
                    print(f"Main unlocking i2c_mutex after attempt {attempt + 1}")
                except Exception as unlock_error:
                    print(f"Error unlocking i2c_mutex: {unlock_error}")
                if not success:
                    time.sleep(retry_delay)	# Wait before retrying
                
        self.pH_calibrate_window.updateInfo(f'{pHdata}')


    def WorkerTimerFinished(self):
        self.pHWorker.resume()
    
    def initTimer(self):
        # Timer setup
        self.logtimer = QTimer(self)
        self.logtimer.setInterval(int(self.log_interval))  # Timer interval set to 5000ms (5 seconds)
        self.logtimer.timeout.connect(self.timerFunction)

        # Coulomb integration timer
        self.coulombTimer = QTimer(self)
        self.coulombTimer.setInterval(1000)  # 1 second updates
        self.coulombTimer.timeout.connect(self.updateCoulombs)
        
        self.coulombClock = monoTimer()

    def startTimer(self):
        self.logtimer.start()  # Start the timer

    def stopTimer(self):
        self.logtimer.stop()  # Stop the timer

    def timerFunction(self):
       
        for i in range(5):
            log_csv(self, self.valueData[i+1], i+1, self.headerindex[i+1])
   
    def start_pHStat(self):
        create_csv(self, self.valueData, self.plotindex, self.headerindex)
        mode = "CC" if self.modeToggle.isChecked() else "CV"
        ouput = "ON" if self.powerButton.isChecked() else "OFF"
        if  hasattr(self, 'ppsWorker'):
            self.logger.log_start(self.voltageDial.value()/10, self.currentDial.value()/10, mode, ouput, self.PStype)
        self.logtimer.start()  # Start the timer
        self.coulombs = 0.0
        self.coulombClock.start()
        self.coulombTimer.start()
        self.logging_timer.start()
        self.pHstatLabel.setEnabled(True)
        self.pumpLabel.setEnabled(True)
        #self.trigger_processing()
        self.startbutton.setEnabled(False)
        self.stopbutton.setEnabled(True)
        self.start = True

    def stop_pHStat(self):
        self.logtimer.stop()  # stop the timer
        self.coulombTimer.stop()
        self.coulombClock.stop()
        self.logging_timer.stop()
        #self.trigger_processing()
        self.startbutton.setEnabled(True)
        self.resetbutton.setEnabled(True)
        self.pHstatLabel.setEnabled(False)
        self.pumpLabel.setEnabled(False)
        self.totalml = 0
        if  hasattr(self, 'ppsWorker'):
            if self.start: self.logger.log_change("Pressed","STOP") 
            else: pass
            self.force_power_off()
            self.logger.log_stop(self.voltageDial.value()/10, self.currentDial.value()/10, self.coulombs)

            
    def reset_pHStat(self):
        # Create a confirmation dialog
        reply = QMessageBox.question(self, 'Reset?',
                                     "Are you sure you want to reset?",
                                     QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.logging_timer.reset()
            self.Log_file = ["","","","","",""]
            self.Log_date = [0,0,0,0,0,0]
            #self.valueData[0] = 0
            self.valueData = [0,0,0,0,0,0]
            self.stopbutton.setEnabled(False)
            self.resetbutton.setEnabled(False)
            self.pumpLabel.setEnabled(False)
            self.start = False
            if  hasattr(self, 'ppsWorker'):
                self.logger.reset()
        else:
            pass
        
    def setupStatusBar(self):
        """Setup the status bar."""
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        status_bar.showMessage("Ready")

   
    #def setuppHWorker(self):
    #     # Initialize the worker and thread
    #    self.pHThread = QThread()
    #    self.pHWorker = pHWorker(self.send_counter, self.test_time, self.read, self.pHdata, self.pHdev, self.temp)
    #    self.pHWorker.moveToThread(self.pHThread)
    #    # Connections
    #    self.pHWorker.update_signal_pH.connect(self.update_gui)#

    #    self.pHThread.started.connect(self.pHWorker.run)
        
    #   self.pHThread.start()

    # --- utilities -------------------------------------------------
    def _disable_pps_controls(self):
        """Gray-out all PPS widgets and make them inert."""
        gray = "color: gray;"
        for lbl in (self.voltagelabel, self.currentlabel, self.modelabel):
            lbl.setText("N/A" if lbl is self.modelabel else lbl.text().split()[0] + ": N/A")
            lbl.setStyleSheet(gray)

        for w in (self.voltageDial, self.currentDial,
                self.setButton, self.modeToggle, self.powerButton):
            w.setDisabled(True)

    def _enable_pps_controls(self):
        """Undo the gray-out – called after handle_pps_limits()."""
        for lbl in (self.voltagelabel, self.currentlabel, self.modelabel):
            lbl.setStyleSheet("color: black;")
        for w in (self.voltageDial, self.currentDial,
                self.setButton, self.modeToggle, self.powerButton):
            w.setEnabled(True)


    def setupPPSWorker(self):
        """Create the PPSWorker (real or dummy) and launch its thread."""
        try:
            psu = discover_power_supply()
            if not psu.connected:
                raise RuntimeError("No PPS detected")
            self.ppsThread = QThread()
            self.ppsWorker = PPSWorker(psu, interval=0.5)
            self.ppsWorker.moveToThread(self.ppsThread)

            self.ppsWorker.voltage_signal.connect(self.update_pps_voltage)
            self.ppsWorker.current_signal.connect(self.update_pps_current)
            self.ppsWorker.mode_signal.connect(self.update_pps_mode)
            self.ppsWorker.limits_signal.connect(self.handle_pps_limits)
            #self.ppsWorker.disconnected_signal.connect(self.on_pps_disconnect)

            self.ppsThread.started.connect(self.ppsWorker.run)
            self.ppsThread.start()
            self.ppsWorker.emit_limits()
    
        except Exception as e:
            print(f"[PPS] Not connected: {e}")
            self._disable_pps_controls()

    def setupRTDWorker(self):
        # Initialize the RTD worker, connections and start thread
        self.RTDThread = QThread()
        self.RTDWorker = RTDWorker(self.send_counter, self.test_time, self.read, 20, self.RTDdev)
        self.RTDWorker.moveToThread(self.RTDThread)
        self.RTDWorker.update_signal_RTD.connect(self.update_gui)
        self.RTDThread.started.connect(self.RTDWorker.run)

        self.RTDThread.start()

   
    def setupStatWorker(self):

        self.StatThread = QThread()
        self.StatWorker = StatWorker(int(self.Select), float(self.pHSelect), self.valueData[0] )
        self.StatWorker.moveToThread(self.StatThread)
        self.StatThread.started.connect(self.StatWorker.run)
        self.startProcessingSignal.connect(self.StatWorker.start_processing)
        self.pHWorker.value_signal.connect(self.StatWorker.update_pH)
        #self.pH_settings_window.select_changed.connect(self.StatWorker.update_pH_select)
        #self.select_settings_window.select_changed.connect(self.StatWorker.update_select)
        
        self.StatWorker.status_signal.connect(self.handle_Stat)
        self.StatWorker.pump_signal.connect(self.pumpInput)
        # Sends the current index (position) of the selected item.
        self.StatThread.start()
    
    def setupUSBWorker(self):

        self.USBThread = QThread()
        self.USBWorker = USBWorker()
        self.USBWorker.moveToThread(self.USBThread)
        self.USBThread.started.connect(self.USBWorker.run)
        
        self.USBWorker.update_usb.connect(self.update_usb)
        # Sends the current index (position) of the selected item.
        self.USBThread.start()
    
    def update_usb(self, result, path):
        if result and self.Log_file[0]:
            self.usb_button.setDisabled(False)
            #self.usb_action.setEnabled(True)
            self.copy_path = path
        else:
            self.usb_button.setDisabled(True)
            #self.usb_action.setEnabled(False) 
    
    #def onUSBButtonClick(self):
        # Handle button click event
    #    self.usb_copy()
    
    def usb_copy(self):
        
        
        dir_path = os.path.dirname(self.Log_file[0])
        pattern = r'(\d{2}_\d{2}_\d{4}/\d{2}_\d{2})'

        # Use re.search to find the matching pattern in the file path
        match = re.search(pattern, self.Log_file[0])
        if match:
            date_time = match.group(1)
           # print("Date and time extracted:", date_time)
        else:
            print("No matching date and time found in the file path.")
        
        # Define the base directory where you want to create the folder
        base_dir = f"{self.copy_path}/Data/"
        #print(base_dir)
        # Combine the base directory and the date string to form the full path
        folder_path = os.path.join(base_dir, date_time)

        # Create the folder if it doesn't exist
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        else:
            pass
        
        # Extract the source_dir, which is the immediate parent directory of the extracted directory path
        #source_dir, _ = os.path.split(dir_path)

        #print("Extracted source_dir:", dir_path)
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
        shutil.copytree(dir_path, folder_path)
        #print(f"Copied {dir_path} to {folder_path}")

        #shutil.copytree(dir_path, folder_path)
        #for log_file in self.Log_file:
        #    try:
        #        shutil.copy(log_file,folder_path)
        #       print(f"{os.path.basename(log_file)}")

                #print(f"Copied {log_file} to {folder_path}")
         #   except Exception as e:
         #       print(f"Error copying {log_file} to {folder_path}: {e}")

    
    def handle_Stat(self, value):
        if value:
            self.Stat_true()
        else:
            self.Stat_false()

    def Stat_true(self):
        #self.pHOK.setText('pH <span style="color:#32CD32;">OK</span>')
        self.pHlabel.setStyleSheet(f'color: #1E8449;')
        self.pHNumber.setStyleSheet(f'color: #1E8449;')

    def Stat_false(self):
        #self.pHOK.setText('pH <span style="color:#DCDCDC;">OK</span>')
        self.pHlabel.setStyleSheet(f'color: #C0392B;')
        self.pHNumber.setStyleSheet(f'color: #C0392B;')

    #def pumpInput(self, test):
    #    if not test:
    #        self.pump_control.activate_feature(int(float(self.addtime) * 1000), int(self.cooldown) * 1000, test)
    #    else:
    #        self.pump_control.activate_feature(int(float(self.addtime) * 1000), 0, test)
    
            
    def pump_activated(self, test):
        self.pumpLabel.setFlash(True)
        #self.pHWorker.pause()
        #self.RTDWorker.pause()
        retry_count = 5 # Number of times to retry
        retry_delay = 0.01 # Delay between retries in second
        success = False # Flag indicating succes
        
        for attempt in range(retry_count):
            
            try:
                #print(f"Main trying to lock i2c_mutex for pump input")
                #print(f"Attempt {attempt + 1}: Trying to lock i2c_mutex for pump input")
                #i2c_mutex.lock()
                #print(f"i2c_mutex locked for pump input")

                #print(f"i2c_mutex locked for pump input")
                lib8mosind.set(0,1,1)
                #print(f"Pump on operation performed successfully on attempt {attempt + 1}")
                #i2c_mutex.unlock()
                #print(f"Pump input operation performed")
                success = True
                self.pump_start_time = time.time()  # Record the start time
                break # Exit the function if succesvol
            except Exception as e:
                print(f"Error during pump on input: {e}")
                pass
            finally:
                try:
                    #i2c_mutex.unlock()
                    print(f"Main unlocking i2c_mutex after pump on on attempt {attempt + 1}")
                except Exception as unlock_error:
                    print(f"Error unlocking i2c_mutex: {unlock_error}")
                if not success:
                    time.sleep(retry_delay)	# Wait before retrying
                
        
    
    def pump_deactivated(self, test):
        
        retry_count = 5 # Number of times to retry
        retry_delay = 0.01 # Delay between retries in second
        success = False
        
        for attempt in range(retry_count):
        
            try:
                #print(f"Attempt {attempt + 1}: Trying to lock i2c_mutex for pump input")
                #i2c_mutex.lock()
                #print(f"i2c_mutex locked for pump input")
                lib8mosind.set(0,1,0)
                #print(f"Pump off operation performed successfully on attempt {attempt + 1}")
                #i2c_mutex.unlock()
                #print(f"Pump input operation performed")
                success = True
                break # Exit the function if succesful
            
            except Exception as e:
                print(f"Error during pump off input: {e}")
                pass
            finally:
                #print(f"Main unlocking i2c_mutex after pump input")
                try:
                    #i2c_mutex.unlock()
                    print(f"Main unlocking i2c_mutex after pump off on attempt {attempt + 1}")
                except Exception as unlock_error:
                    print(f"Error unlocking i2c_mutex: {unlock_error}")
                if not success:
                    time.sleep(retry_delay) # Wait before retrying
        
        
        #if not test:
        #    self.pumpLabel.setFlash(False)
        #else:
        #    self.pumpLabel.setEnabled(False)
        
        if success:
            if self.pump_start_time is not None:
                self.elapsed_time = time.time() - self.pump_start_time
                print(f"Time between pump activation and deactivation: {self.elapsed_time:.4f} seconds")
            
                if not test :
                    self.valueData[0] += 1.0
                    self.totalml = self.totalml + (float(self.ml)/float(self.addtime))*self.elapsed_time
                    print(round(self.totalml,3)) 
                    #data = self.valueData[0] * float(self.ml)
                    log_csv(self, round(self.totalml,3), 0, self.headerindex[0])
       
                self.pump_start_time = None  # Reset the start time
            else:
                print("Warning: Pump was not active, no elapsed time to calculate.")
    
    
    def handle_select(self, select):
        if select == 0:
            self.keepSelector.setCurrentIndex(0)
            self.statustext = "above"
        else:
            self.keepSelector.setCurrentIndex(1)
            self.statustext = "below"
        self.keepSelector.setStatusTip(f'Settings of pH Stat, Keep the experiment {self.statustext} a pH of {self.pHSelect}')
        ConfigWriter(self)
        #print(f"Received signal with value: {value}")
        # Handle the change in the main GUI here
    
    def handle_pH(self,pH):

        self.phSpin.setValue(pH)
        self.pHSelect = float(pH)
        self.phSpin.setStatusTip(f'Settings of pH Stat, Keep the experiment {self.statustext} a pH of {self.pHSelect}')
        ConfigWriter(self)
        #print(f"Received signal with value: {value}")
        # Handle the change in the main GUI here
    
    def _stop_pps(self):
        if getattr(self, "ppsWorker", None):
            self.ppsWorker.stop()
            self.ppsThread.quit()
            self.ppsThread.wait()


    #@pyqtSlot()
    #def togglePowerSupply(self):
    #    if not getattr(self, "ppsWorker", None):
    #        return                              # nothing connected
    #    try:
    #        self.ppsWorker.set_output(self.powerButton.isChecked())
    #    except Exception as e:
    #        print(f"[PPS] Could not change output: {e}")
    #        self.powerButton.setChecked(False)


    #@pyqtSlot()
    #def on_pps_disconnect(self):
    #    print("[PPS] Lost connection — disabling controls.")
    #    self._disable_pps_controls()
    #    self.powerButton.setChecked(False)     # keep toggle in sync
    #    self._stop_pps()
    #    self.reconnect_pps_action.setEnabled(True)
    #    QMessageBox.warning(self, "Power Supply Disconnected",
    #                        "The power supply was disconnected.")


    @pyqtSlot(float, float)
    def handle_time(self,ml,addtime):
        self.ml = ml
        self.addtime = addtime
        ConfigWriter(self)
        #print(f"Received signal with value: {value}")
        # Handle the change in the main GUI here
        
    @pyqtSlot(str, float, object)
    def handle_calibrate(self, calibrationType, pH, data):
        # Pause the worker
        self.pHWorker.pause()
        self.pauzeWorker.start(2000)
        self.CalcWorker.start(1300)

        #print(f"{calibrationType},{pH},{data[0]}")
        QTimer.singleShot(300, lambda: self.queryInstructions(calibrationType, pH))
        

        self.lowpH = data[0]
        self.midpH = data[1]
        self.highpH = data[2]
    
    #@pyqtSlot(float)
    #def update_pps_voltage(self, value):
    #    self.voltagelabel.setText(f"{value:.2f} V")
    @pyqtSlot()
    def f(self):
        print("[PPS] Lost connection — disabling controls.")
        self._disable_pps_controls()
        QMessageBox.warning(self, "Power Supply Disconnected", "The power supply was disconnected.")

    @pyqtSlot(float)
    def update_pps_current(self, value):
        self.latest_current = value
        self.currentlabel.setText(f"{value:.2f} A")
        self.update_gui(value,4)

    @pyqtSlot(str)
    def update_pps_mode(self, value):
        self.modelabel.setText(f"{value}")
    
    @pyqtSlot(float, float, float, str)
    def handle_pps_limits(self, vmax, imax, vmin, model):
        print(f"PPS Model: {model}, VMAX: {vmax} V, IMAX: {imax} A, VMIN: {vmin} V")
        self.PStype[0] = model
        self.PStype[1] = vmax 
        self.PStype[2] = imax
        self.PStype[3] = vmin
        # Re-enable all previously disabled UI elements
        self.voltageDial.setEnabled(True)
        self.currentDial.setEnabled(True)
        self.setButton.setEnabled(True)
        self.powerButton.setEnabled(True)
        self.modeToggle.setEnabled(True)
        
         # Restore label styles
        self.voltagelabel.setStyleSheet("color: black;")
        self.currentlabel.setStyleSheet("color: black;")
        self.modelabel.setStyleSheet("color: black;")
        
        # Restore label text
        self.modelabel.setText("CV")  # or default based on toggle state
    
        self.voltageDial.setMinimum(int(vmin * 10))
        self.voltageDial.setMaximum(int(vmax * 10))

        self.currentDial.setMinimum(0)
        self.currentDial.setMaximum(int(imax * 10))

    @pyqtSlot(int)
    def voltage_dial_changed(self, val):
        voltage = val / 10.0
        #self.voltagelabel.setText(f"{voltage:.1f} V")

        # Show popup tooltip near the dial
        self.voltageDiallabel.setText(f"{voltage:.1f}")
        #QToolTip.showText(
        #    self.voltageDial.mapToGlobal(QPoint(0, -30)),  # Position above dial
        #    f"{voltage:.1f} V",
        #    self.voltageDial,
        #    self.voltageDial.rect(),
        #    1000  # duration in ms
        #)
    @pyqtSlot(int)
    def current_dial_changed(self, val):
        current = val / 10.0
        #self.voltagelabel.setText(f"{voltage:.1f} V")
        self.currentDiallabel.setText(f"{current:.1f}")

        # Show popup tooltip near the dial
        #QToolTip.showText(
        #    self.currentDial.mapToGlobal(QPoint(0, -30)),  # Position above dial
        #    f"{current:.1f} A",
        #    self.currentDial,
        #    self.currentDial.rect(),
        #    1000  # duration in ms
        #)
        #if hasattr(self, 'ppsWorker'):
        #    self.ppsWorker.set_voltage(voltage)

    
  
    @pyqtSlot(float)
    def update_pps_voltage(self, value):
        self.voltagelabel.setText(f"{value:.2f} V")
        self.update_gui(value,3)
        #dial_val = int(value * 10)
        #self.voltageDial.blockSignals(True)         # Prevent feedback loop
        #self.voltageDial.setValue(dial_val)
        #self.voltageDial.blockSignals(False)
    
    def queryInstructions(self, calibrationType, pH):
        command = (f"Cal,{calibrationType},{pH}")
        
        try:
            self.pHdev.query(command)
        except Exception as e:
            print(f"{e}")
        
    def instructions(self, command):
        
        dev_pH.query(command)
        time.sleep(1.5)
        result = dev_pH.read()
        self.input_result.set(result)
        self.update()
        LogGUI.mainloop.set(True)#

    #def trigger_processing(self):
        # Call this method when you want to trigger processing in the processing worker
    #    QMetaObject.invokeMethod(self.StatWorker, "start_processing")
        #self.StatWorker.start_processing
        #self.startProcessingSignal.emit()

    def openDatePicker(self):
        # Create and show the DatePickerDialog as a separate window
        date_picker_dialog = DatePickerDialog()
        date_picker_dialog.exec_()  # This will block until the dialog is closed
    
    def openCalibratePumpWindow(self):
        self.time_settings_window.exec_()

    #def openpHSettingsWindow(self):
    #    # Create and show the Settings window as a separate window
    #    self.pH_settings_window.exec_()
    
    #def openSelectSettingsWindow(self):
    #    # Create and show the Settings window as a separate window
    #    self.select_settings_window.exec_()
    
    def openCalibratepHWindow(self):
        # Create and show the Settings window as a separate window
        self.pH_calibrate_window.exec_()
    

    def update_gui(self, received_data, sensor_type):
        self.current_data = received_data
        if sensor_type == 1:
            self.pHNumber.setText(f'{str("pH {:.2f}".format(received_data))}')
            #self.pHvalue = received_data
            self.valueData[1] = received_data
        elif sensor_type == 2:
            self.temp = received_data
            #if received_data < -200:
            #    self.RTDlabel.setText("N/A °C")
            #else:
            self.RTDlabel.setText(f"{received_data:.2f} °C")
            self.valueData[2] = received_data
            self.pHWorker.pH_temp = round(received_data,1)
        elif sensor_type == 3:   
            self.valueData[3] = received_data 
        elif sensor_type == 4:   
            self.valueData[4] = received_data
        elif sensor_type == 5:   
            self.valueData[5] = received_data
        
    


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
    
   