# electrophstat/gui/phstat_controller.py
from PyQt5.QtCore    import QObject, pyqtSlot
from PyQt5.QtWidgets import QMessageBox, QAction
import os, re, shutil                      

class ButtonConnections(QObject):
    """
    Encapsulates the logic for Start / Stop / Reset buttons in the pH-stat GUI.
    """
    def __init__(self, window):
        super().__init__(window)
        self.win = window

        # Wire the buttons
        self.win.startbutton.clicked.connect(self.start_stat)
        self.win.stopbutton.clicked.connect(self.stop_stat)
        self.win.resetbutton.clicked.connect(self.reset_stat)
        self.win.actionFullscreen.triggered.connect(self.toggle_fullscreen)
        self.win.toggle_pH_control.triggered.connect(self.toggle_pHStat)
        self.win.togglepHAction.toggled.connect(self.updateCurrentTabPlot)
        self.win.toggleTempAction.toggled.connect(self.updateCurrentTabPlot)
        self.win.actionCalibrate_pH.triggered.connect(self.openCalibratepHWindow)
        self.win.action_datewindow.triggered.connect(self.openDateTimeWindow)

    def log_active(self):
        self.win.logging_ctrl.start()

    @pyqtSlot()
    def start_stat(self):
        # 1) Kick off your control loop & logging
        #self.win.control_loop.should_start = True
        #self.win.logging_timer.start()
        if self.win.toggle_pH_control:
            self.win.phstat_ctrl.on_pumpToggle(True)
        # 2) UI tweaks
        self.win.startbutton.setEnabled(False)
        self.win.stopbutton.setEnabled(True)
        self.win.resetbutton.setEnabled(False)
        # 3) (Optionally) show a status message
        self.log_active()
        #self.win.logger.start_session()
        self.win.pps_ctrl.coulombClock.start()
        self.win.pps_ctrl.coulombTimer.start()
        self.win.statusBar().showMessage("pH-stat/logging started")
        

    @pyqtSlot()
    def stop_stat(self):
  
        # 1) UI tweaks
        self.win.startbutton.setEnabled(True)
        self.win.stopbutton.setEnabled(False)
        self.win.resetbutton.setEnabled(True)
        self.win.pps_ctrl.coulombClock.stop()
        self.win.pps_ctrl.coulombTimer.stop()
        #2) Logging and pH pump logic stop
        if self.win.toggle_pH_control:
            self.win.phstat_ctrl.on_pumpToggle(False)
        self.win.logging_ctrl.stop()
        # 3) Status
        self.win.statusBar().showMessage("pH-stat stopped")

    @pyqtSlot()
    def reset_stat(self):
        # 1) Clear any accumulated state
        #self.win.control_loop.reset()   # you might need to add a reset() method
        #self.win.logger.reset()         # or recreate the log
        # 2) UI tweaks
        self.win.startbutton.setEnabled(True)
        self.win.stopbutton.setEnabled(False)
        self.win.resetbutton.setEnabled(False)
        # 3) Status
        self.win.logger.reset()
        self.win.valueData = {
            "pump":             0.0,
            "pH":               0.0,
            "temperature":      0.0,
            "voltage":          0.0,
            "current":          0.0,
            "coulomb":          0.0,
            "mode":             "",
        }
        QMessageBox.information(self.win, "Reset", "pH-stat has been reset")
    
    
    @pyqtSlot()
    def usb_copy(self):
        # 1) grab your first log file path
        logs = getattr(self.win, "Log_file", None)
        if not logs or not logs[0]:
            QMessageBox.warning(self.win, "No logs to copy",
                                "There are no log files available to copy.")
            return

        src = logs[0]
        dir_path = os.path.dirname(src)

        # 2) extract the “DD_MM_YYYY/HH_MM” sub-path via regex
        match = re.search(r"(\d{2}_\d{2}_\d{4}/\d{2}_\d{2})", src)
        if not match:
            QMessageBox.warning(self.win, "Bad log path",
                                f"Can't parse date/time out of\n{src}")
            return
        date_time = match.group(1)

        # 3) figure out where to copy to
        #    assume your window has `copy_path` pointing at e.g. "/media/usb"
        base_dir = os.path.join(self.win.copy_path, "Data")
        folder_path = os.path.join(base_dir, date_time)

        # 4) make the parent directory if needed
        os.makedirs(base_dir, exist_ok=True)

        # 5) (re)create the date_time folder
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
        try:
            shutil.copytree(dir_path, folder_path)
        except Exception as e:
            QMessageBox.critical(self.win, "Copy failed",
                                 f"Could not copy logs:\n{e}")
            return

        QMessageBox.information(self.win, "Copy complete",
                                f"Copied:\n{dir_path}\nto\n{folder_path}")
    @pyqtSlot()
    def openCalibratePumpWindow(self):
        self.win.calibrate_pump_window.exec_()
    
    #@pyqtSlot() 
    #def openCalibratepHWindow(self):
    #    self.win.calibrate_pump_window.exec_()

    @pyqtSlot()
    def toggle_fullscreen(self):
        if self.win.isFullScreen():
            self.win.showNormal()
            self.win.actionFullscreen.setText("Fullscreen on")
        else:
            self.win.showFullScreen()
            self.win.actionFullscreen.setText("Fullscreen off")
    
    @pyqtSlot()
    def updatePlot(self, tab):
        self.win.plot_manager.update(tab)

    @pyqtSlot()    
    def updateCurrentTabPlot(self):
        # Get the current widget (tab)
        current_tab = self.win.tabWidget.currentWidget()
        self.updatePlot(current_tab)
    
    @pyqtSlot(QAction)
    def on_log_option_changed(self, action):
        """action.objectName() tells us which interval to use."""
        ms_map = {
            "option1":  5,
            "option2": 30,
            "option3": 60,
            "option4":  300,
        }
        interval = ms_map.get(action.objectName())
        if interval is not None:
            print("New log interval:", interval)
            # … apply interval to your logging timer …
        self.win.logging_ctrl.set_interval(int(interval))

    
    @pyqtSlot(str, float)
    def update_gui(self, sensor_type: str, received_data: float):
        self.win.current_data = received_data
        # overwrite the right channel
        if sensor_type in self.win.valueData:
            self.win.valueData[sensor_type] = received_data
        else:
            return  # unknown sensor, ignore
        if sensor_type == 'pH':
            self.win.pHNumber.setText(f'{str("pH {:.2f}".format(received_data))}')
        elif sensor_type == 'temperature':
            self.win.RTDlabel.setText(f"{received_data:.2f} °C")
        #elif sensor_type == 'voltage':   
        #    self.win.valueData[3] = received_data 
        #elif sensor_type == 4:   
        #    self.win.valueData[4] = received_data
        #elif sensor_type == 5:   
        #    self.win.valueData[5] = received_data
    
    @pyqtSlot() 
    def openCalibratepHWindow(self):
        self.win.pH_calibrate_dialog.exec_()

    @pyqtSlot() 
    def openDateTimeWindow(self):
        self.win.date_time_dialog.exec_()

    @pyqtSlot(bool)
    def toggle_pHStat(self, checked: bool):
        if checked:
            print("pH-stat logic & logging ENABLED")
            self.win.phstat_ctrl.enable()
            self.win.logging_ctrl.enable_logging(["pump"])
            self.win.graph_ctrl.set_pH_enabled(True)
        else:
            print("pH-stat logic & logging DISABLED")
            self.win.phstat_ctrl.disable()
            self.win.logging_ctrl.disable_logging(["pump"])
            self.win.graph_ctrl.set_pH_enabled(False)
