from PyQt5.QtCore    import QObject, QTimer, pyqtSlot
from PyQt5.QtWidgets import QWidget
class GraphController(QObject):
    """
    Manages creating/updating the graph tabs on a QTabWidget,
    driving them on a regular QTimer, and delegating to a PlotManager.
    Now with dynamic on/off for Pump vs PSU tabs.
    """
    def __init__(self, tab_widget, plot_manager, parent=None):
        super().__init__(parent)
        self.tabWidget    = tab_widget
        self.plot_manager = plot_manager
        self.win          = parent  # assume parent is your MainWindow
        
        # ←—— Read your config flags here —→
        cfg = self.win.config
        self.pHstat_enabled    = bool(cfg.enable_phstat)
        self.temp_enabled      = bool(cfg.enable_temp_sensor)
        self.psu_enabled       = bool(cfg.enable_psu)
        self.turbidity_enabled = bool(cfg.enable_turbidity_sensor)

        # 1) Build all four tabs (but don't add them yet)
        self._build_all_tabs()

        # 2) Now “refresh” the tabWidget so it shows the right ones
        self.refresh_tabs()

        # 3) Kick off the update timer
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_timeout)
        self._timer.start(1000)

    def _build_all_tabs(self):
        specs = [
            ("Pump",        dict(plot_index=0, left_label="Added (ml)")),
            ("pH/Temp",     dict(plot_index=1, 
                                left_label="pH",
                                right_label="Temperature", right_units="°C")),
            ("Power",       dict(plot_index=2, 
                                left_label="Voltage (V)",
                                right_label="Amperage",     right_units="A")),
            ("Coulomb",     dict(plot_index=3, left_label="Coulomb (C)")),
            ("Turbidity",   dict(plot_index=4, left_label="Turbidity")),
        ]
        self._all_tabs = []
        for title, kwargs in specs:
            # ask PlotManager to build the tab
            #tab = QWidget()
            #tab.plot_index = kwargs["plot_index"]
            self.plot_manager.addGraphTab(title=title, **kwargs)
            # retrieve the newly created tab widget
            tw = self.tabWidget.widget(self.tabWidget.count()-1)
            # remove it immediately; we'll re-insert in refresh_tabs()
            self.tabWidget.removeTab(self.tabWidget.count()-1)

            self._all_tabs.append((title, tw))

    def refresh_tabs(self):
        # 1) clear out everything
        self.tabWidget.clear()

        for title, widget in self._all_tabs:
            if title == "Pump":
                # always show pump?
                self.tabWidget.addTab(widget, title)
            elif title == "pH/Temp":
                if self.pHstat_enabled or self.temp_enabled:
                    self.tabWidget.addTab(widget, title)
            elif title in ("Power", "Coulomb"):
                if self.psu_enabled:
                    self.tabWidget.addTab(widget, title)
            elif title == "Turbidity":
                if self.turbidity_enabled:
                    self.tabWidget.addTab(widget, title)

        # optional: restore the previously‐active tab index if you saved it

    def set_pHstat_enabled(self, on: bool):
        self.pHstat_enabled = on
        self.refresh_tabs()

    def set_psu_enabled(self, on: bool):
        self.psu_enabled = on
        self.refresh_tabs()

    def set_turbidity_enabled(self, on: bool):
        self.turbidity_enabled = on
        self.refresh_tabs()

    @pyqtSlot()
    def _on_timeout(self):
        # your existing update logic
        logger = self.plot_manager.main.logger
        if not getattr(logger, "files", None):
            return
        current = self.tabWidget.currentWidget()
        if current is not None:
            self.plot_manager.update(current)
        self.plot_manager.update_all_plots()
