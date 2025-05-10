import sys
import time
import os
import getpass

if 'XDG_RUNTIME_DIR' not in os.environ:
    os.environ['XDG_RUNTIME_DIR'] = f"/run/user/{os.getuid()}"

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QGridLayout, 
                             QLabel, QMenuBar, QAction, QStatusBar, 
                             QComboBox, QDoubleSpinBox, QHBoxLayout, QVBoxLayout, 
                             QPushButton, QTabWidget, QFrame, QMenu, QMessageBox, QActionGroup, QDial, QToolTip, QCheckBox, QSizePolicy, QToolButton)
from PyQt5.QtGui import QFont, QColor, QIcon, QPen, QTransform, QPalette
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QMetaObject, pyqtSlot, QTimer, QMutex, QSize, QPoint
from scripts.LedIndicatorWidget import LedIndicator
from scripts.pHStat_worker import pHWorker, RTDWorker, StatWorker, USBWorker, i2c_mutex
from scripts.PPSWorker import PPSWorker
from scripts.pHstat_config import ConfigReader, ConfigWriter
from scripts.pHStat_classes import (pHPickerDialog, SelectPickerDialog, pumpControl, 
                            DatePickerDialog, CustomTextWidget, ClickableLabel, CalibratePumpDialog,CalibratepHDialog, monoTimer, ToggleSwitch, horizontalToggleSwitch)
import pyqtgraph as pg
#from pyqtgraph.Qt import QtGui, QtWidgets
#import numpy as np
from scripts.pHStat_csv import create_csv, log_csv, read_log_data, scale_time_data
#from scripts.atlas import atlas_i2c
import datetime
import shutil
import re
#import lib8mosind
from scripts.pHStat_classes import MockLib8MosInd
import serial.tools.list_ports
from voltcraft.pps import PPS
from scripts import PlotManager, atlas_i2c, Fusion3DToggle, RoundSetButton


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

        self.pH_settings_window = pHPickerDialog(float(self.pHSelect))
        self.pH_settings_window.select_changed.connect(self.handle_pH)
        
        self.select_settings_window = SelectPickerDialog(self.Select)
        self.select_settings_window.select_changed.connect(self.handle_select)
        
        self.time_settings_window = CalibratePumpDialog(float(self.ml), float(self.addtime))
        self.time_settings_window.select_changed.connect(self.handle_time)
        self.time_settings_window.test_pump.connect(self.pumpInput)

        self.pH_calibrate_window = CalibratepHDialog(float(self.lowpH), float(self.midpH), float(self.highpH))
        self.pH_calibrate_window.calibrate_changed.connect(self.handle_calibrate)
        
        self.pump_control = pumpControl(self)
        self.pump_control.pumpActivated.connect(self.pump_activated)
        self.pump_control.pumpDeactivated.connect(self.pump_deactivated)
        
        self.initializeUI()
        #self.delayed_show_fullscreen()

    def initializeUI(self):
        
        """Initialize the window and display its contents to the screen."""
        self.setWindowTitle('pHStat Qt.Mosfet V1.2')
        self.setWindowFlags(self.windowFlags() | Qt.WindowTitleHint)

        self.setWindowIcon(QIcon('path/to/your/app/icon.png'))  # Set the window icon
        self.setGeometry(200, 200, 700, 500)  # Set the size of the window (x_pos, y_pos, width, height)
        #self.setupVariables()
        self.setupMenu()
        self.setupWidgets()
        self.setupStatusBar()

        self.setuppHWorker()
        self.setupRTDWorker()
        self.setupStatWorker()
        self.setupUSBWorker()
        self.setupPPSWorker()
        
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

        # Get current window size
        width = self.width()
        height = self.height()

        # Base scaling factor
        scale = min(width / 800, height / 600)
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
        

        #self.powerButton.setH_scale(0.55*scale)
        #self.powerButton.setV_scale(0.55*scale)
        #self.powerButton.setFontSize(9*scale)
        
        self.modeToggle.setH_scale(0.55*scale)
        self.modeToggle.setV_scale(0.55*scale)
        self.modeToggle.setFontSize(9*scale)
        powerButton_width = int(60 * scale)
        powerButton_height = int(40 * scale)
        self.powerButton.setFixedSize(powerButton_width, powerButton_height)
        #self.powerButton.setH_scale(0.55*scale)
        #self.powerButton.setW_scale(0.55*scale)
        #self.powerButton.setFontSize(9*scale)
        
        button_size = int(60 * scale)  # scale from window size
        self.setButton.setFixedSize(button_size, button_size)
        #self.setButton.setStyleSheet(f"""
        #    QPushButton {{
        #        background-color: #DCDCDC;
        #        color: black;
        #        font-weight: bold;
        #        font-size: {int(14 * scale)}pt;
        #        border-radius: {button_size // 2}px;
        #        border: 2px solid #A9A9A9;
        #    }}
        #    QPushButton:pressed {{
        #        background-color: #B0B0B0;
         #   }}
       
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
        self.pHdev = atlas_i2c(address=99)
        self.RTDdev = atlas_i2c(address=102)
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

        ConfigReader(self)
    
    def setupMenu(self):
        """Setup the menu bar."""
        menu_bar = self.menuBar()  # Get the menu bar
        
        # Create top-level menus
        file_menu = menu_bar.addMenu('File')
        setting_menu = menu_bar.addMenu('Settings')
        
        # Create actions for file_menu
        self.exit_action = QAction('Exit', self)
        self.exit_action.triggered.connect(self.close)  # Connect the triggered signal to the close method
        self.exit_action.setStatusTip("Exit the program")

        #self.start_action = QAction('Start',self)
        #self.start_action.triggered.connect(self.trigger_processing)
        self.screenchange = QAction('Change screen', self)
        self.screenchange.triggered.connect(self.toggle_fullscreen)
        self.datewindow = QAction('Change date/time', self)
        self.datewindow.triggered.connect(self.openDatePicker)
        
        self.reconnect_pps_action = QAction('Reconnect Power Supply', self)
        self.reconnect_pps_action.setStatusTip("Try to reconnect the PPS power supply")
        self.reconnect_pps_action.triggered.connect(self.reconnectPPS)
        setting_menu.addAction(self.reconnect_pps_action)

        
        
        # In setupMenu()
        self.pH_control_enabled = True  # Default: enabled

        self.toggle_pH_control = QAction('Enable pH Control', self, checkable=True)
        #self.toggle_pH_control.setChecked(True)
        self.toggle_pH_control.triggered.connect(self.toggle_pHStat)

        setting_menu.addAction(self.toggle_pH_control)
        
        
        
        pHstatMenu = QMenu("pHStat settings", self)

        calibrate = QAction('Calibrate pump', self)
        calibrate.triggered.connect(self.openCalibratePumpWindow)
        calibratepH = QAction('Calibrate pH', self)
        calibratepH.triggered.connect(self.openCalibratepHWindow)
        pHstatMenu.addAction(calibrate)
        pHstatMenu.addAction(calibratepH)
                 
        log_options_submenu = QMenu("Log Options", self)
        # Create an action group for exclusive selection
        action_group = QActionGroup(self)
        action_group.setExclusive(True)
        
        # Create checkable actions
        self.option1 = QAction("5 sec", self)
        self.option1.setCheckable(True)
        self.option1.setData(5000)  # <-- Attach 5000 milliseconds

        self.option2 = QAction("30 sec", self)
        self.option2.setCheckable(True)
        self.option2.setData(30000)  # <-- Attach 30000 milliseconds

        self.option3 = QAction("60 sec",self)
        self.option3.setCheckable(True)
        self.option3.setData(60000)  # <-- Attach 60000 milliseconds

        self.option4 = QAction("5 min", self)
        self.option4.setCheckable(True)
        self.option4.setData(300000)  # <-- Attach 300000 milliseconds

        # Add actions to the group
        action_group.addAction(self.option1)
        action_group.addAction(self.option2)
        action_group.addAction(self.option3)
        action_group.addAction(self.option4)
        
        # Add actions to the submenu
        log_options_submenu.addAction(self.option1)
        log_options_submenu.addAction(self.option2)
        log_options_submenu.addAction(self.option3)
        log_options_submenu.addAction(self.option4)
        
        # Add the submenu to the settings menu
        pHstatMenu.addMenu(log_options_submenu)
        
        # Optional: connect to a method
        self.option1.triggered.connect(self.option_selected)
        self.option2.triggered.connect(self.option_selected)
        self.option3.triggered.connect(self.option_selected)
        self.option3.triggered.connect(self.option_selected)
        
        self.view_menu = self.menuBar().addMenu("View")

        self.togglepHAction = QAction("Show pH Curve", self, checkable=True)
        self.togglepHAction.setChecked(True)  # Default is ON
        self.togglepHAction.setStatusTip("Toggle visibility of pH curve")
        self.togglepHAction.toggled.connect(self.updateCurrentTabPlot)

        self.toggleTempAction = QAction("Show Temperature Curve", self, checkable=True)
        self.toggleTempAction.setChecked(True)  # Default is ON
        self.toggleTempAction.setStatusTip("Toggle visibility of temperature curve")
        self.toggleTempAction.toggled.connect(self.updateCurrentTabPlot)
        
        self.view_menu.addAction(self.togglepHAction)
        self.view_menu.addAction(self.toggleTempAction)

        # Pre-select option3

        # Call the same function manually
        #self.option_selected()
        
        #self.settingswindow_action = QAction('pH Stat settings',self)
        #self.settingswindow_action.triggered.connect(self.openSettingsWindow)
        
        
        file_menu.addAction(self.exit_action)
        setting_menu.addAction(self.screenchange)
        setting_menu.addAction(self.datewindow)
        setting_menu.addMenu(pHstatMenu)
    
    def reconnectPPS(self):
        print("[PPS] Attempting to reconnect power supply...")

        # Stop existing worker if running
        try:
            self.ppsWorker.stop()
            self.ppsThread.quit()
            self.ppsThread.wait()
            print("[PPS] Existing PPSWorker stopped.")
        except Exception as e:
            print(f"[PPS] Error stopping old PPSWorker: {e}")

        # Try to set up again
        try:
            self.setupPPSWorker()
            print("[PPS] Reconnected.")
        except Exception as e:
            print(f"[PPS] Reconnect failed: {e}")
            QMessageBox.critical(self, "Reconnect Failed", f"Could not reconnect to PPS:\n{e}")

    
    
    
    def toggle_pHStat(self, checked):
        self.pH_control_enabled = checked
        if self.pH_control_enabled:
            print("pH Control enabled")
            try:
                # Connect signals
                self.startProcessingSignal.connect(self.StatWorker.start_processing)
                self.pHWorker.update_signal_pH.connect(self.StatWorker.update_pH)
                self.pH_settings_window.select_changed.connect(self.StatWorker.update_pH_select)
                self.select_settings_window.select_changed.connect(self.StatWorker.update_select)
                self.StatWorker.status_signal.connect(self.handle_Stat)
                self.StatWorker.pump_signal.connect(self.pumpInput)
                # Update labels
                self.pHstatLabel.setDisabled(False)
                self.pHstatLabel.updateText("Active")
                self.pHstatLabel.updateNormalColor(Qt.black)
                self.pumpLabel.setDisabled(False)
                self.pumpLabel.updateText("Active")
                self.pumpLabel.updateNormalColor(Qt.black)
                # Enable clickalble labels
                self.pHText.setEnabled(checked)
                self.selectlabel.setEnabled(checked)
                self.pHSelectLabel.setEnabled(checked)
                
            except Exception as e:
                print(f"Reconnect error (probably already connected): {e}")
        
             # Re-add Pump plot if missing
            if self.tabWidget.indexOf(self.graphTabs[0]) == -1:
                self.tabWidget.insertTab(0, self.graphTabs[0], "Pump Plot")
        
        else:
            print("pH Control disabled")
            try:
                #Disconnect signals
                self.startProcessingSignal.disconnect(self.StatWorker.start_processing)
                self.pHWorker.update_signal_pH.disconnect(self.StatWorker.update_pH)
                self.pH_settings_window.select_changed.disconnect(self.StatWorker.update_pH_select)
                self.select_settings_window.select_changed.disconnect(self.StatWorker.update_select)
                self.StatWorker.status_signal.disconnect(self.handle_Stat)
                self.StatWorker.pump_signal.disconnect(self.pumpInput)
                #Update labels
                self.pHstatLabel.setDisabled(True)
                self.pHstatLabel.updateText("Inactive")
                self.pHstatLabel.updateNormalColor(Qt.gray)
                self.pumpLabel.setDisabled(True)
                self.pumpLabel.updateText("Inactive")
                self.pumpLabel.updateNormalColor(Qt.gray)
                #Disable clickable labels
                self.pHText.setEnabled(checked)
                self.selectlabel.setEnabled(checked)
                self.pHSelectLabel.setEnabled(checked)
               
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

    def setupWidgets(self):
        """Setup widgets and layouts here."""
        central_widget = QWidget()  # Create a central widget
        self.setCentralWidget(central_widget)  # Set the central widget
        # Create a QGridLayout on the central widget
        grid = QGridLayout(central_widget)  # Create a QGridLayout
        
        # Layout of the pH and Select label
        pHWidget = QWidget()
        pHLayout = QGridLayout(pHWidget)

        # Main pH label
        self.pHlabel = QLabel("pH")  # Create a label
        self.pHlabel.setStatusTip("Current pH measured")
        pHfont = self.pHlabel.font()
        pHfont.setPointSize(35)  # Set the font size to 40 points
        self.pHlabel.setFont(pHfont)
        self.pHNumber = QLabel("pH 0.0")
        self.pHNumber.setStatusTip("Current pH measured")
        self.pHNumber.setFont(pHfont)
        # Main Temperature label
        self.RTDlabel = QLabel("RTD")  # Create a 
        self.RTDlabel.setStatusTip("Current temperature measured")

        RTDfont = self.RTDlabel.font()
        RTDfont.setPointSize(20)  # Set the font size to 20 points
        self.RTDlabel.setFont(RTDfont)
        
        
        self.voltagelabel = QLabel("0.00 V")
        self.voltagelabel.setStatusTip("Current Voltage measured")
        Voltfont = self.voltagelabel.font()
        Voltfont.setPointSize(20)  # Set the font size to 20 points
        
        self.currentlabel = QLabel("0.00 A")
        self.currentlabel.setStatusTip("Current Amperage measured")
        Ampfont = self.currentlabel.font()
        Ampfont.setPointSize(20)  # Set the font size to 20 points
        
        self.modelabel = QLabel("CV")
        self.modelabel.setStatusTip("Current mode")
        modefont = self.modelabel.font()
        modefont.setPointSize(20)  # Set the font size to 20 points
    
        self.voltageDial = QDial()
        self.voltageDial.setMinimum(0)          # e.g., 0 V
        self.voltageDial.setMaximum(300)        # e.g., 30.0 V in 0.1V steps
        self.voltageDial.setSingleStep(1)       # One step = 0.1V
        self.voltageDial.setPageStep(5)         # Larger jumps
        self.voltageDial.setNotchesVisible(True)
        self.voltageDial.valueChanged.connect(self.voltage_dial_changed)    
        
        self.currentDial = QDial()
        self.currentDial.setMinimum(0)          # e.g., 0 V
        self.currentDial.setMaximum(300)        # e.g., 30.0 V in 0.1V steps
        self.currentDial.setSingleStep(1)       # One step = 0.1V
        self.currentDial.setPageStep(5)         # Larger jumps
        self.currentDial.setNotchesVisible(True)
        self.currentDial.valueChanged.connect(self.current_dial_changed)    
        
        #self.modeSelector = QComboBox()
        #self.modeSelector.addItems(["CV", "CC"])
        #grid.addWidget(self.modeSelector, 3, 0)
        self.modeToggle = ToggleSwitch(
            bar_color=Qt.gray,
            checked_color="#27ae60",  # Green for ON
            handle_color=Qt.white,
            h_scale=1.0,
            v_scale=1.0,
            fontSize=10
            )
        self.modeToggle.setChecked(False)  # Default to CV mode
        self.modeToggle.setMinimumSize(80, 120)
        
        self.toolButton = QToolButton() 
        self.toolButton.setFixedSize(80,80)
        self.toolButton.setStyleSheet("""
                QPushButton {
                    background-color: #e0e0e0;
                    border: 2px outset lightgray;
                    padding: 6px;
                }
                QPushButton:pressed {
                    border: 2px inset gray;
                    background-color: #d0d0d0;
                }
            """)



        self.setButton = RoundSetButton("Set")
        self.setButton.clicked.connect(self.apply_ps_settings)
        self.setButton.setFixedSize(80, 80)  # Makes it a square (round via radius below)
        self.setButton.setStyleSheet("""
            QPushButton {
                background-color: #DCDCDC;      /* light gray */
                color: black;
                font-weight: bold;
                font-size: 14pt;
                border-radius: 40px;            /* round shape */
                border: 2px solid #A9A9A9;      /* darker gray border */
            }
            QPushButton:pressed {
                background-color: #B0B0B0;      /* slightly darker on press */
            }
            QPushButton:disabled {
                background-color: #E0E0E0;
                color: #888888;
                border: 2px solid #CCCCCC;
            }
        """)

        #self.powerButton = QPushButton("Power ON")
        self.powerButton = Fusion3DToggle()
        #self.powerButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.powerButton.setCheckable(True)
        self.powerButton.setChecked(False)
        self.powerButton.setToolTip("Toggle power supply output ON/OFF")
        self.powerButton.clicked.connect(self.togglePowerSupply)  # Connect the button to a method

        pHLayout.addWidget(self.pHNumber,0,0,1,2, alignment=Qt.AlignLeft)
        pHLayout.addWidget(self.RTDlabel,0,3,alignment=Qt.AlignRight)
        pHLayout.addWidget(self.voltageDial, 1, 0,alignment= Qt.AlignCenter) 
        pHLayout.addWidget(self.currentDial, 1, 1,alignment= Qt.AlignCenter)  
        pHLayout.addWidget(self.modeToggle, 1, 2,alignment= Qt.AlignCenter)
        pHLayout.addWidget(self.toolButton, 1, 3,alignment= Qt.AlignCenter)
        pHLayout.addWidget(self.voltagelabel,2,0,alignment= Qt.AlignCenter)
        pHLayout.addWidget(self.currentlabel,2,1,alignment= Qt.AlignCenter)
        pHLayout.addWidget(self.modelabel,2,2,alignment= Qt.AlignCenter)
        pHLayout.addWidget(self.powerButton,2,3,alignment= Qt.AlignCenter)
        
        #USB Button
        self.usb_button = QPushButton(self)
        self.usb_button.setDisabled(True)
        self.usb_button.clicked.connect(self.usb_copy)  # Connect the button to a method
        self.usb_button.setMinimumSize(50, 50)  # minimum width = 100, minimum height = 50
        self.usb_button.setStatusTip('Copy current data to USB drive')
        # Set an icon on the button
        self.usb_button.setIcon(QIcon('flashcard-usb.svg'))  # Provide the correct path to your icon image file
        # Set the icon size
        self.usb_button.setIconSize(QSize(50, 50))  # Set icon width and height
        # Create and configure a button
        
        
        # Above/below
        selectWidget = QWidget()
        selectLayout = QGridLayout(selectWidget)
        self.selectlabel = ClickableLabel("select")
        self.selectlabel.clicked.connect(self.openSelectSettingsWindow)
        # Set the frame shape to be a box
        self.selectlabel.setFrameShape(QLabel.Panel)

        # Set the frame shadow to be raised
        self.selectlabel.setFrameShadow(QLabel.Raised)
    
        # Optionally, set the border width
        self.selectlabel.setLineWidth(2)
        self.selectlabel.setMidLineWidth(2)

        selectfont = self.selectlabel.font()
        selectfont.setPointSize(20) 
        # Use ClickableLabel
        self.pHText = QLabel('pH')
        self.pHText.setFont(selectfont)
        self.pHSelectLabel = ClickableLabel("0.0")
        self.pHSelectLabel.clicked.connect(self.openpHSettingsWindow)
        self.pHSelectLabel.setFont(selectfont)
        self.selectlabel.setFont(selectfont)
        # Set the frame shape to be a box
        self.pHSelectLabel.setFrameShape(QLabel.Panel)

        # Set the frame shadow to be raised
        self.pHSelectLabel.setFrameShadow(QLabel.Raised)
    
        # Optionally, set the border width
        self.pHSelectLabel.setLineWidth(2)
        self.pHSelectLabel.setMidLineWidth(2)

        self.pHstatLabel = CustomTextWidget("pH Stat ", "Active", "#DCDCDC", 13)
        self.pHstatLabel.setStatusTip("Activity of pH Stat, grey (inactive), yellow (active)")
        self.pumpLabel = CustomTextWidget("Pump ", "Active", "#DCDCDC", 13)
        self.pumpLabel.setStatusTip("Activity of pump, grey (inactive), yellow (standby), green (pumping)")

        #self.pHstatActive = CustomTextWidget("Active", "#F1C40F", 13)
        #self.pumpActive = CustomTextWidget("Active", "#F1C40F", 13)
        #F1C40F

        selectLayout.addWidget(self.selectlabel,0,0)
        selectLayout.addWidget(self.pHText, 0,1, alignment= Qt.AlignRight)
        selectLayout.addWidget(self.pHSelectLabel,0,2, alignment=Qt.AlignLeft)
        selectLayout.addWidget(self.pHstatLabel,1,0,1,2, alignment= Qt.AlignLeft )
        selectLayout.addWidget(self.pumpLabel,1,0,1,3,alignment= Qt.AlignRight )

        selectWidget.setLayout(selectLayout)

        # Text Layout of the pump ON and pH OK
        self.pumpon = QLabel('PUMP <span style="color:#DCDCDC;">ON</span>')
        pumpfont = self.pumpon.font()
        pumpfont.setPointSize(30)
        self.pumpon.setFont(pumpfont)

        self.pHOK = QLabel('pH <span style="color:#DCDCDC;">OK</span>')
        self.pHOK.setFont(pumpfont)

        textLayout = QVBoxLayout()
        textLayout.addWidget(self.pumpon, alignment=Qt.AlignRight)
        textLayout.addWidget(self.pHOK,alignment=Qt.AlignRight)
        textContainer = QWidget()
        textContainer.setLayout(textLayout)

        
        # Create and configure LED widget                                      
        self.led_logging = LedIndicator("yellow")
        self.led_logging.setDisabled(True)  # Make the led non clickable
        self.led_start = LedIndicator("green")
        self.led_start.setDisabled(True)  # Make the led non clickable
        ledLayout = QVBoxLayout()
        ledLayout.addWidget(self.led_logging)
        ledLayout.addWidget(self.led_start)
        ledContainer = QWidget()
        ledContainer.setLayout(ledLayout)


        # Add the tab widghet
        self.tabWidget = QTabWidget()
        self.tabWidget.setStatusTip("Plots of total ml added (Pump plot), pH (pH plot) and temperature (RTD plot)")

        self.tabWidget.currentChanged.connect(self.onTabChanged)

        #Add the plotwidget
        # Create a PlotWidget
        #self.graphWidget = pg.PlotWidget()
        # Set the background color to semi-transparent white (RGBA)
        
        #Add the buttons
        # Main button widget
        buttonWidget = QWidget()
        # Create the grid layout for the buttons
        buttonLayout = QVBoxLayout(buttonWidget)
        buttonFont = QFont("Arial", 12, QFont.Bold)

        # Start button
        self.startbutton =QPushButton("Start",self)
        self.startbutton.setStatusTip("Starts pH Stat and logging")
        #self.startbutton.setStyleSheet("QPushButton {background-color: #52BE80;}"
        #                     "QPushButton:pressed {background-color: #229954;}"
        #                     "QPushButton:disabled {background-color: #D4EFDF;}")
        #self.startbutton.setFont(buttonFont)
        self.startbutton.setMinimumSize(100, 70)  # Minimum width = 100, Minimum height = 50
        self.startbutton.clicked.connect(self.start_pHStat)
        # Stop button
        self.stopbutton =QPushButton("Stop",self)
        self.stopbutton.setStatusTip("Stops pH Stat and logging")

        self.stopbutton.setStyleSheet("QPushButton {background-color: #C0392B;}"
                             "QPushButton:pressed {background-color: #922B21;}"
                             "QPushButton:disabled {background-color: #F2D7D5;}")
        self.stopbutton.setFont(buttonFont)

        self.stopbutton.clicked.connect(self.stop_pHStat)
        self.stopbutton.setMinimumSize(100, 50)  # Minimum width = 100, Minimum height = 50
        self.stopbutton.setEnabled(False)
        # Reset button
        self.resetbutton =QPushButton("Reset", self)
        self.resetbutton.setStatusTip("Resets pH Stat for new experiment")

        self.resetbutton.setFont(buttonFont)
        self.resetbutton.clicked.connect(self.reset_pHStat)
        self.resetbutton.setEnabled(False)

        # Add buttons to buttonLayout
        buttonLayout.addWidget(self.startbutton)
        buttonLayout.addWidget(self.stopbutton)
        buttonLayout.addWidget(self.resetbutton)
        # Add buttonLayout to the buttonWidget

        buttonWidget.setLayout(buttonLayout)
        #filler = QWidget()
        # Add widgets to the grid
        #grid.addWidget(self.led_logging, 0, 0, Qt.AlignTop)  # Place LED on the top-left
        #grid.addWidget(ledContainer, 0, 2)  # Place LED on the top-left
        
        
        grid.addWidget(pHWidget, 0, 0,2,1)  # Place label next to the LED
        
        grid.addWidget(selectWidget, 0, 1)
        grid.addWidget(self.usb_button, 0, 2, Qt.AlignRight)
        
        grid.addWidget(buttonWidget,2,0,2,1)
        grid.addWidget(selectWidget, 0, 1)
        grid.addWidget(self.tabWidget, 1,1,3,2)
        
        self.plot_manager = PlotManager(self)

        self.initializeGraphTabs()
        self.initializeTabTimer()
        #self.addGraphTab()
        self.handle_select(int(self.Select))#, float(self.pHSelect))
        self.handle_pH(float(self.pHSelect))
        self.handle_time(float(self.ml), float(self.addtime))
        #self.handle_pHselect(float(self.pHSelect))
   
    def togglePowerSupply(self):
        if self.powerButton.isChecked():
            self.ppsWorker.set_output(True)  # Replace with your actual PPS control
        else:
            self.ppsWorker.set_output(False)

    def apply_ps_settings(self):
        # Read toggle state (assuming you're using your ToggleSwitch class)
        mode = "CC" if self.modeToggle.isChecked() else "CV"

        # Get dial values
        voltage = self.voltageDial.value() / 10.0  # Assuming 0.1 V steps
        current = self.currentDial.value() / 10.0  # Assuming 0.1 A steps

        # Ensure PPS is connected and worker exists
        if hasattr(self, 'ppsWorker') and hasattr(self.ppsWorker, 'pps'):
            if mode == "CV":
                # Constant Voltage: set voltage, allow max current
                self.ppsWorker.set_current(self.ppsWorker.pps.IMAX)
                self.ppsWorker.set_voltage(voltage)
            else:
                # Constant Current: set current, allow max voltage
                self.ppsWorker.set_voltage(self.ppsWorker.pps.VMAX)
                self.ppsWorker.set_current(current)

            print(f"[SET] Mode: {mode}, Voltage: {voltage:.1f} V, Current: {current:.1f} A")

    def update_mode_label(self, state):
        mode = "CC" if state == Qt.Checked else "CV"
        print(f"Mode switched to: {mode}")
   
    def delayed_show_fullscreen(self):
        QTimer.singleShot(100, self.toggle_fullscreen)  # Delayed fullscreen after 100 milliseconds
    
    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            self.screenchange.setText("Fullscreen on")
        else:
            self.showFullScreen()
            self.screenchange.setText("Fullscreen off")

    def pHlabelClicked(self):
        print('pH label clicked')
    def selectlabelClicked(self):
        print("select label clicked")

    def initializeTabTimer(self):
        self.tabtimer = QTimer()
        self.tabtimer.timeout.connect(self.updateCurrentTabPlot)
        self.tabtimer.start(1000)  # Update every second

    
    def initializeGraphTabs(self):
        self.graphWidgets = []
        self.graphTabs = []

        # Add Pump plot
        #self.addGraphTab("Pump Plot", ("Time (s)", "Added (ml)"))
        
        self.plot_manager.addGraphTab(
            title="Pump Plot",
            plot_index=0,
            left_label="Added (ml)",
            right_label=None,
            right_units=None
        )
        
        # Add Dual pH+Temperature plot
        #self.plot_manager.addDualGraphTab("pH + Temp Plot")
        self.plot_manager.addGraphTab(
            title="pH + Temp Plot",
            plot_index=1,
            left_label="pH",
            right_label="Temperature",
            right_units="°C"
        )
        
        self.plot_manager.addGraphTab(
            title="Power Plot",
            plot_index=2,
            left_label="Voltage (V)",
            right_label="Amperage",
            right_units="A"
        )
        
        self.plot_manager.addGraphTab(
            title="Coulomb",
            plot_index=3,
            left_label="Coulomb (C)",
            right_label=None,
            right_units=None
        )
        
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
                i2c_mutex.lock()
                pHdata = self.pHdev.read()   
                success = True
                break # Exit the function if succesvol
            except Exception as e:
                print(f"Error during read: {e}")
                pass
            finally:
                try:
                    i2c_mutex.unlock()
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
        self.logtimer.start()  # Start the timer
        self.coulombs = 0.0
        self.coulombClock.start()
        self.coulombTimer.start()
        self.logging_timer.start()
        self.pHstatLabel.setEnabled(True)
        self.pumpLabel.setEnabled(True)
        self.trigger_processing()
        self.startbutton.setEnabled(False)
        self.stopbutton.setEnabled(True)

    def stop_pHStat(self):
        self.logtimer.stop()  # stop the timer
        self.coulombTimer.stop()
        self.coulombClock.stop()
        self.logging_timer.stop()
        self.trigger_processing()
        self.startbutton.setEnabled(True)
        self.resetbutton.setEnabled(True)
        self.pHstatLabel.setEnabled(False)
        self.pumpLabel.setEnabled(False)
        self.totalml = 0

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

        else:
            pass
        
    def setupStatusBar(self):
        """Setup the status bar."""
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        status_bar.showMessage("Ready")

   
    def setuppHWorker(self):
         # Initialize the worker and thread
        self.pHThread = QThread()
        self.pHWorker = pHWorker(self.send_counter, self.test_time, self.read, self.pHdata, self.pHdev, self.temp)
        self.pHWorker.moveToThread(self.pHThread)
        # Connections
        self.pHWorker.update_signal_pH.connect(self.update_gui)

        self.pHThread.started.connect(self.pHWorker.run)
        
        self.pHThread.start()
    
    def setupPPSWorker(self):
        
        port = find_voltcraft_pps()
        if not port:
            raise RuntimeError("No PPS found on any ttyUSB port")
        #self.ppsWorker = PPSWorker(port, 0.5, reset=False)
        try:
            temp_worker = PPSWorker(port, 0.5, reset=True)
            if not temp_worker.is_connected():
                raise RuntimeError("No PPS detected")
            
            self.ppsThread = QThread()
            self.ppsWorker = temp_worker
            self.ppsWorker.moveToThread(self.ppsThread)

            self.ppsWorker.voltage_signal.connect(self.update_pps_voltage)
            self.ppsWorker.current_signal.connect(self.update_pps_current)
            self.ppsWorker.mode_signal.connect(self.update_pps_mode)
            self.ppsWorker.limits_signal.connect(self.handle_pps_limits)
            self.ppsWorker.disconnected_signal.connect(self.handle_pps_disconnect)

            self.ppsThread.started.connect(self.ppsWorker.run)
            self.ppsThread.start()
            self.ppsWorker.emit_limits()
    
        except Exception as e:
            print(f"[PPS] Not connected: {e}")
            self.voltagelabel.setText("V: N/A")
            self.currentlabel.setText("A: N/A")
            self.modelabel.setText("N/A")
            gray_style = "color: gray;"
            self.voltagelabel.setStyleSheet(gray_style)
            self.currentlabel.setStyleSheet(gray_style)
            self.modelabel.setStyleSheet(gray_style)
            
            self.voltageDial.setDisabled(True)
            self.currentDial.setDisabled(True)
            self.setButton.setDisabled(True)
            self.modeToggle.setDisabled(True)

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
        self.pHWorker.update_signal_pH.connect(self.StatWorker.update_pH)
        self.pH_settings_window.select_changed.connect(self.StatWorker.update_pH_select)
        self.select_settings_window.select_changed.connect(self.StatWorker.update_select)
        
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

    def pumpInput(self, test):
        if not test:
            self.pump_control.activate_feature(int(float(self.addtime) * 1000), int(self.cooldown) * 1000, test)
        else:
            self.pump_control.activate_feature(int(float(self.addtime) * 1000), 0, test)
    
            
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
                i2c_mutex.lock()
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
                    i2c_mutex.unlock()
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
                i2c_mutex.lock()
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
                    i2c_mutex.unlock()
                    print(f"Main unlocking i2c_mutex after pump off on attempt {attempt + 1}")
                except Exception as unlock_error:
                    print(f"Error unlocking i2c_mutex: {unlock_error}")
                if not success:
                    time.sleep(retry_delay) # Wait before retrying
        
        
        if not test:
            self.pumpLabel.setFlash(False)
        else:
            self.pumpLabel.setEnabled(False)
        
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
    @pyqtSlot(int)
    def handle_select(self, select):
        if select == 0:
            text = "Keep above"
            self.statustext = "above"
        else:
            text = "Keep below"
            self.statustext = "below"
        self.selectlabel.setText(f'{text}')
        self.selectlabel.setStatusTip(f'Settings of pH Stat, Keep the experiment {self.statustext} a pH of {self.pHSelect}')
        ConfigWriter(self)
        #print(f"Received signal with value: {value}")
        # Handle the change in the main GUI here
    
    @pyqtSlot(float)
    def handle_pH(self,pH):

        self.pHSelectLabel.setText(f'{pH}')
        self.pHSelect = float(pH)
        self.pHSelectLabel.setStatusTip(f'Settings of pH Stat, Keep the experiment {self.statustext} a pH of {self.pHSelect}')
        ConfigWriter(self)
        #print(f"Received signal with value: {value}")
        # Handle the change in the main GUI here
    
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
    def handle_pps_disconnect(self):
        print("[PPS] Lost connection — disabling controls.")

        self.voltageDial.setDisabled(True)
        self.currentDial.setDisabled(True)
        self.setButton.setDisabled(True)
        self.modeToggle.setDisabled(True)

        self.voltagelabel.setText("V: N/A")
        self.currentlabel.setText("A: N/A")
        self.modelabel.setText("N/A")

        gray_style = "color: gray;"
        self.voltagelabel.setStyleSheet(gray_style)
        self.currentlabel.setStyleSheet(gray_style)
        self.modelabel.setStyleSheet(gray_style)

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
        # Re-enable all previously disabled UI elements
        self.voltageDial.setEnabled(True)
        self.currentDial.setEnabled(True)
        self.setButton.setEnabled(True)
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
        QToolTip.showText(
            self.voltageDial.mapToGlobal(QPoint(0, -30)),  # Position above dial
            f"{voltage:.1f} V",
            self.voltageDial,
            self.voltageDial.rect(),
            1000  # duration in ms
        )
    @pyqtSlot(int)
    def current_dial_changed(self, val):
        current = val / 10.0
        #self.voltagelabel.setText(f"{voltage:.1f} V")

        # Show popup tooltip near the dial
        QToolTip.showText(
            self.currentDial.mapToGlobal(QPoint(0, -30)),  # Position above dial
            f"{current:.1f} A",
            self.currentDial,
            self.currentDial.rect(),
            1000  # duration in ms
        )
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

    def trigger_processing(self):
        # Call this method when you want to trigger processing in the processing worker
        QMetaObject.invokeMethod(self.StatWorker, "start_processing")
        #self.StatWorker.start_processing
        #self.startProcessingSignal.emit()

    def openDatePicker(self):
        # Create and show the DatePickerDialog as a separate window
        date_picker_dialog = DatePickerDialog()
        date_picker_dialog.exec_()  # This will block until the dialog is closed
    
    def openCalibratePumpWindow(self):
        self.time_settings_window.exec_()

    def openpHSettingsWindow(self):
        # Create and show the Settings window as a separate window
        self.pH_settings_window.exec_()
    
    def openSelectSettingsWindow(self):
        # Create and show the Settings window as a separate window
        self.select_settings_window.exec_()
    
    def openCalibratepHWindow(self):
        # Create and show the Settings window as a separate window
        self.pH_calibrate_window.exec_()
    

    def update_gui(self, received_data, type):
        self.current_data = received_data
        if type == 1:
            self.pHNumber.setText(f'{str("pH {:.2f}".format(received_data))}')
            #self.pHvalue = received_data
            self.valueData[1] = received_data
        elif type == 2:
            self.temp = received_data
            if received_data < -200:
                self.RTDlabel.setText("N/A °C")
            else:
                self.RTDlabel.setText(f"{received_data:.2f} °C")
            self.valueData[2] = received_data
            self.pHWorker.pH_temp = round(received_data,1)
        elif type == 3:   
            self.valueData[3] = received_data 
        elif type == 4:   
            self.valueData[4] = received_data
        elif type == 5:   
            self.valueData[5] = received_data
        
    


    def exitApplication(self,event):
        # Create a confirmation dialog
        reply = QMessageBox.question(self, 'Exit?',
                                     "Are you sure you want to quit?",
                                     QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.No)

        if reply == QMessageBox.Yes:
            # Stop the worker
            self.pHWorker.stop()
            self.pHThread.quit()

            self.RTDWorker.stop()
            self.RTDThread.quit()

            self.StatWorker.stop()
            self.StatThread.quit()
            
            self.USBWorker.stop()
            self.USBThread.quit()
            
            event.accept()  # Accept the close event

        else:
            event.ignore()
    def closeEvent(self, event):
        # Optionally, you can also use the exitApplication method here
        self.exitApplication(event)
    
   