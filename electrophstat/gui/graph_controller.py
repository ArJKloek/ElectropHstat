from PyQt5.QtCore    import QObject, QTimer, pyqtSlot

class GraphController(QObject):
    """
    Manages creating/updating the graph tabs on a QTabWidget,
    driving them on a regular QTimer, and delegating to a PlotManager.
    """
    def __init__(self, tab_widget, plot_manager, parent=None):
        super().__init__(parent)
        self.tabWidget    = tab_widget
        self.plot_manager = plot_manager

        # 1) Create the tabs once
        self._create_tabs()

        # 2) Kick off the update timer
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_timeout)
        self._timer.start(1000)   # once a second

    def _tab_exists(self, title: str) -> bool:
        for i in range(self.tabWidget.count()):
            if self.tabWidget.tabText(i) == title:
                return True
        return False

    def _create_tabs(self):
        specs = [
            ("Pump Plot",       dict(plot_index=0, left_label="Added (ml)")),
            ("pH + Temp Plot",  dict(plot_index=1, left_label="pH",
                                     right_label="Temperature", right_units="°C")),
            ("Power Plot",      dict(plot_index=2, left_label="Voltage (V)",
                                     right_label="Amperage",     right_units="A")),
            ("Coulomb",         dict(plot_index=3, left_label="Coulomb (C)")),
        ]
        for title, kwargs in specs:
            if not self._tab_exists(title):
                self.plot_manager.addGraphTab(title=title, **kwargs)

    @pyqtSlot()
    def _on_timeout(self):
        # update whatever tab is currently visible
        logger = self.plot_manager.main.logger
        if not getattr(logger, "files", None):
            return
        
        current = self.tabWidget.currentWidget()
        if current is not None:
            self.plot_manager.update(current)
        
        self.plot_manager.update_all_plots()

