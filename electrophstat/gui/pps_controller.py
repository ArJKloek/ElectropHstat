# electrophstat/gui/pps_controller.py
from PyQt5.QtCore    import QObject, QTimer, QThread, pyqtSlot
from PyQt5.QtWidgets import QMessageBox, QLabel, QGridLayout
from electrophstat.hardware import discover_power_supply
from electrophstat.workers.PPSWorker import PPSWorker
from electrophstat.control.timer_control import monoTimer
from electrophstat.dummy.dummy_pps import DummyPPS    

class PPSController(QObject):
    """
    Starts a PPSWorker on its own thread, hooks up all of its signals
    back into the MainWindow.
    """
    def __init__(self, window, pps_connections, interval: float = 0.5, reset: bool = True):
        super().__init__(window)
        self.win = window
        self.connections = pps_connections
        self.interval = interval
        self.reset = reset
        self.coulombs = 0.0

        #1) Create worker & thread but do not start it yet.
        self._setup_worker()
        self.initCoulombTimer()

    def _setup_worker(self):
        # 1) Probe for a real PPS (or get a DummyPPS)
        #status, port = discover_power_supply(reset=self.reset)
        psu_debug = getattr(self.win.config.psu, 'debug', False)
        
        if psu_debug:
            port = DummyPPS()
            status = "not connected"  # Simulate a disconnected state for debugging
            print("Debug mode: Using DummyPPS for testing.")
        else:
            status, obj = discover_power_supply(reset=self.reset)
            self.psu_status = status # Store the status for later use
            port = obj  # This is the actual port or DummyPPS instance
        if status == "not_connected":
            print("No power supply detected.")
        elif status == "connected_off":
            print("Power supply detected (USB), but not responding. Is it turned ON?")
        elif status == "connected_on":
            print("Power supply connected and ready!")
        else:
            print(f"Unexpected status: {status}")
            port = None
        
        
        if isinstance(port, DummyPPS) and self.win.debug_mode == True:
            # If dummy power supply, color the groupbox orange
            # to indicate that it is a dummy.
            group_name = "PowerGroup"
            # grab the widget from your MainWindow
            groupbox = getattr(self.win, group_name, None)
            if groupbox is not None:
                groupbox.setStyleSheet("""
                    QGroupBox {
                    border: 2px solid orange;
                    background-color: #FFF8E1;
                    }
                """)
        elif isinstance(port, DummyPPS) and self.win.debug_mode == False:
            # If real power supply, color the groupbox green
            group_name = "PowerGroup"
            groupbox = getattr(self.win, group_name, None)
            if groupbox is not None:
                groupbox.setTitle("⚠️ Power Supply not found")
                self.pps_worker = None
                self.win.pps_connections._disable_pps_controls()
                self.win.reconnect_pps_action.setEnabled(False)
                self.win.actionEnable_PSU_control.setEnabled(False)
                self.win.logging_ctrl.disable_logging(['voltage', 'current', 'coulomb'])
                self.win.graph_ctrl.set_psu_enabled(False)
            return
        
        self.pps_worker = PPSWorker(port, self.interval, reset=False)

        self.connections.set_worker(self.pps_worker)

        # 2) Move it into its own thread
        self.thread = QThread(self.win)
        self.pps_worker.moveToThread(self.thread)
        self.thread.started.connect(self.pps_worker.run)

        if self.psu_status == "connected_on":
            self.start_psu_worker()
        elif self.psu_status == "not_connected" and self.win.debug_mode == True:
            self.start_psu_worker()
        elif self.psu_status == "connected_off":
            self.win.pps_connections._disabe_pps_controls()

        # 3) Hook all signals back to window methods and the pps_connections
        self.pps_worker.voltage_signal.connect(self.connections.update_pps_voltage)
        self.pps_worker.current_signal.connect(self.connections.update_pps_current)
        self.pps_worker.mode_signal.connect(self.connections.update_pps_mode)
        self.pps_worker.limits_signal.connect(self.connections.handle_pps_limits)
        self.pps_worker.disconnected_signal.connect(self.connections.on_pps_disconnect)

        # 4) Start polling
        #self.thread.start()

        # 5) fire one initial limits‐read so the dials get properly ranged
        if self.psu_status == "connected_on":
            self.pps_worker.emit_limits()
        elif self.psu_status == "not_connected" and self.win.debug_mode == True:
            self.pps_worker.emit_limits()


    @pyqtSlot()
    def start_psu_worker(self):
        """Call this to start the PPSWorker thread."""
        if not self.thread.isRunning():
            self.thread.start()
            print("[PPS] PPSWorker started.")
        else:
            print("[PPS] PPSWorker is already running.")    

    @pyqtSlot()
    def stop(self):
        """Call this when you want to shut down cleanly."""
        self.pps_worker.stop()
        self.thread.quit()
        self.thread.wait()
    
    @pyqtSlot()
    def reconnect_psu(self):
        """Stop the old one and spin up a brand new worker."""
        print(f'Reconnect started')       
        try:
            self.stop()
            print("[PPS] Existing PPSWorker stopped.")
        except Exception as e:
            print(f"[PPS] Error stopping old PPSWorker: {e}")        
        try:
            self._setup_worker()
            self.start_psu_worker()
            print("[PPS] Reconnected.")
            self.connections._enable_pps_controls()
            self.win.apply_scaling()
        except Exception as e:
            print(f"[PPS] Reconnect failed: {e}")
    
    def initCoulombTimer(self):
        # Coulomb integration timer
        self.coulombTimer = QTimer(self)
        self.coulombTimer.setInterval(1000)  # 1 second updates
        self.coulombTimer.timeout.connect(self.updateCoulombs)
        
        self.coulombClock = monoTimer()

    def updateCoulombs(self):
        dt = self.coulombClock.lap()  # Time since last update
        amps = self.win.valueData["current"]
        self.coulombs += amps * dt
        self.win.button_cont.update_gui("coulomb",self.coulombs)
        #print(f"Coulombs: {self.coulombs:.2f}")
        #self.coulombLabel.setText(f"Coulombs: {self.coulombs:.2f}")