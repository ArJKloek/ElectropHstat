# electrophstat/gui/phstat_controller.py
from pathlib import Path
from PyQt5.QtCore    import QObject, pyqtSlot, QTimer
from PyQt5.QtWidgets import QMessageBox, QAction, QLabel
import os, re, shutil                      
import platform

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
        self.win.logging_ctrl.logs_present_signal.connect(self.on_logs_present)
        if not platform.system().lower() == "windows":
            self.win.usb_ctrl.worker.update_usb.connect(self.on_usb_changed)
            self.win.usb_button.clicked.connect(self.usb_copy)

    @pyqtSlot()
    def start_stat(self):
        # 1) Kick off your control loop & logging
        #self.win.control_loop.should_start = True
        #self.win.logging_timer.start()
        if self.win.toggle_pH_control and self.win.enable_phstat and self.win.phstat_ctrl is not None:
            # Start the pH-stat worker
            self.win.phstat_ctrl.on_pumpToggle(True)
        # 2) UI tweaks
        self.win.startbutton.setEnabled(False)
        self.win.stopbutton.setEnabled(True)
        self.win.resetbutton.setEnabled(False)
        # 3) (Optionally) show a status message
        self.log_active()
        #self.win.logger.start_session()
        if self.win.enable_psu:
            self.win.pps_ctrl.coulombClock.start()
            self.win.pps_ctrl.coulombTimer.start()
        self.win.statusBar().showMessage("pH-stat/logging started")
        self.win.logging_started = True
    def log_active(self):
        self.win.logging_ctrl.start()


    @pyqtSlot()
    def stop_stat(self):
  
        # 1) UI tweaks
        self.win.startbutton.setEnabled(True)
        self.win.stopbutton.setEnabled(False)
        self.win.resetbutton.setEnabled(True)
        # 2) Logging and pH pump logic stop
        print("Stopping timers...")
        if self.win.enable_psu:
            self.win.pps_ctrl.coulombClock.stop()
            self.win.pps_ctrl.coulombTimer.stop()
        print("Stopped timers.")

        print("Stopping pH-stat logic...")
        if self.win.toggle_pH_control and self.win.enable_phstat and self.win.phstat_ctrl is not None:
            self.win.phstat_ctrl.on_pumpToggle(False)
        print("Stopped pH-stat logic.")

        print("Deactivating log...")
        self.log_deactive()
        print("Log deactivated.")

        print("Updating status bar...")
        self.win.statusBar().showMessage("pH-stat stopped")
        print("Done.")
    
    
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
        self.win.logging_ctrl.reset()
        
        self.reset_value_data()
       
        QMessageBox.information(self.win, "Reset", "pH-stat has been reset")
    
    
    @pyqtSlot()
    def usb_copy(self):
        # 1) Make sure a USB is actually present
        if not getattr(self.win, "usb_present", False):
            QMessageBox.warning(self.win, "No USB Drive",
                                "No USB storage device detected.\n"
                                "Please insert a USB stick first.")
            return

        # 2) Grab your logger instance & its log_dir/base_dir
        logger = getattr(self.win, "logger", None)
        if logger is None or not hasattr(logger, "log_dir") or not hasattr(logger, "base_dir"):
            QMessageBox.warning(self.win, "No Logs",
                                "Logger not initialized or no log directory found.")
            return

        src_dir = Path(logger.log_dir)
        base_dir = Path(logger.base_dir)
        if not src_dir.exists():
            QMessageBox.warning(self.win, "No Logs",
                                f"No log directory found at:\n{src_dir}")
            return

        # 3) Compute the relative subpath under base_dir
        try:
            rel = src_dir.relative_to(base_dir)
        except Exception:
            # fallback: take just the last two path components (date/time)
            rel = Path(*src_dir.parts[-2:])

        # 4) Build the destination on the USB
        usb_mount = Path(self.win.copy_path)
        dest_base = usb_mount / "Data"
        dest_dir = dest_base / rel

        # 5) Create parent, and remove any old copy
        dest_base.mkdir(parents=True, exist_ok=True)
        if dest_dir.exists():
            shutil.rmtree(dest_dir)

        # 6) Perform the copy
        try:
            shutil.copytree(src_dir, dest_dir)
        except Exception as e:
            QMessageBox.critical(self.win, "Copy Failed",
                                f"Could not copy logs from:\n{src_dir}\nto:\n{dest_dir}\n\nError: {e}")
            return

        # 7) Inform the user
        msg = f'Logs copied to {dest_dir}'
        label = QLabel(msg, self.win)
        # add as a permanent widget so status-tips won’t replace it
        self.win.statusBar().addPermanentWidget(label)
        # remove it after 10 s
        QTimer.singleShot(10_000, lambda: self.win.statusBar().removeWidget(label))
            
    def log_deactive(self):
        self.win.logging_ctrl.stop()
        
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
            "action5_sec":  5,
            "action30_sec": 30,
            "action1_min": 60,
            "action5_min":  300,
        }
        interval = ms_map.get(action.objectName())
        if interval is not None:
            print("New log interval:", interval)
            # … apply interval to your logging timer …
        self.win.logging_ctrl.set_interval(int(interval))
        self.win.config.logger.interval = int(interval)
    
    @pyqtSlot(str, float)
    def update_gui(self, sensor_type: str, received_data: float, raw_data: float = None):
        self.win.current_data = received_data
        # overwrite the right channel
        if sensor_type in self.win.valueData:
            self.win.valueData[sensor_type] = received_data
        else:
            return  # unknown sensor, ignore
        if sensor_type == 'pH':
            self.win.pHLabel.setText(f'{str("pH {:.2f}".format(received_data))}')
        elif sensor_type == 'RTD':
            self.win.RTDLabel.setText(f"{received_data:.2f} °C")
        elif sensor_type == 'turbidity':
            self.win.lb_turbidity.setText(f'{received_data:.0f} NTU')   
    
        
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
            self.win.graph_ctrl.set_pHstat_enabled(False)

    def reset_value_data(self):
        """
        Zero‐out all numeric entries in self.valueData,
        and clear any string entries.
        """
        for key, val in self.win.valueData.items():
            if isinstance(val, str):
                self.win.valueData[key] = ""
            else:
                # assume numeric
                self.win.valueData[key] = 0.0
    
    @pyqtSlot(bool, object)
    def on_usb_changed(self, present, path):
        self.win.usb_present = present
        self.win.copy_path = path
        self._update_usb_button()

    @pyqtSlot(bool)
    def on_logs_present(self, present):
        self.win.logs_present = present
        self._update_usb_button()

    def _update_usb_button(self):
        self.win.usb_button.setEnabled(self.win.usb_present and self.win.logs_present)