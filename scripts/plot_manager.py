from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtGui import QPen, QColor
from PyQt5.QtCore import Qt
import numpy as np
import pyqtgraph as pg
from scripts.pHStat_csv import read_log_data, scale_time_data  # if not already imported in main

class PlotManager:
    def __init__(self, main):
        self.main = main
        self.labelStyle = {'color': 'black', 'font-size': '11pt'}
        self.plotColors = ['r', 'g', 'b']
    
    def addDualGraphTab(self, title):
        tab = QWidget()
        tab.plot_index = 1 
        layout = QVBoxLayout(tab)
        #backgroundColor = self.palette().color(self.backgroundRole())
        backgroundColor = self.main.palette().color(self.main.backgroundRole())

        # Main PlotWidget
        plotWidget = pg.PlotWidget()
        plotWidget.setBackground(backgroundColor)
        layout.addWidget(plotWidget)

        self.main.graphWidgets.append(plotWidget)
        self.main.graphTabs.append(tab)
        self.main.pH_curve = None
        self.main.temp_curve = None

        # Setup main view (left axis)
        plotWidget.showGrid(x=True, y=True)
        plotWidget.setLabel('left', 'pH', color='black', size='11pt')
        plotWidget.setLabel('bottom', 'Time (s)', color='black', size='11pt')
        plotWidget.getAxis('left').setTextPen(QPen(QColor('black')))
        plotWidget.getAxis('bottom').setTextPen(QPen(QColor('black')))

        # Create a second view for Temperature (right axis)
        self.main.tempViewBox = pg.ViewBox()
        plotWidget.scene().addItem(self.main.tempViewBox)
        plotWidget.getAxis('right').linkToView(self.main.tempViewBox)
        plotWidget.showAxis('right')
        plotWidget.setLabel('right', 'Temperature (°C)', color='black', size='11pt')
        plotWidget.getAxis('right').setTextPen(QPen(QColor('black')))

        self.main.tempViewBox.setXLink(plotWidget)

        # Connect resizing
        plotWidget.getViewBox().sigResized.connect(self.updateDualViews)

        # Save special dual-plot references
        self.main.pHViewBox = plotWidget.getViewBox()

        self.main.tabWidget.addTab(tab, title)
        self.main.tabWidget.setStyleSheet("""
            QTabBar::tab {
                font-size: 10pt;
                height: 20px;
                width: 110px;
                padding: 5px;
            }
        """)

    def addPowerGraphTab(self, title):
        tab = QWidget()
        tab.plot_index = 2  # Assign a new index for tracking
        layout = QVBoxLayout(tab)
        #backgroundColor = self.palette().color(self.backgroundRole())
        backgroundColor = self.main.palette().color(self.main.backgroundRole())

        plotWidget = pg.PlotWidget()
        plotWidget.setBackground(backgroundColor)
        layout.addWidget(plotWidget)

        self.main.graphWidgets.append(plotWidget)
        self.main.graphTabs.append(tab)

        plotWidget.showGrid(x=True, y=True)
        plotWidget.setLabel('left', 'Value', color='black', size='11pt')
        plotWidget.setLabel('bottom', 'Time (s)', color='black', size='11pt')
        plotWidget.getAxis('left').setTextPen(QPen(QColor('black')))
        plotWidget.getAxis('bottom').setTextPen(QPen(QColor('black')))

        self.volt_curve = plotWidget.plot([], [], pen=pg.mkPen(QColor('black'), width=2), name="Voltage")
        self.curr_curve = plotWidget.plot([], [], pen=pg.mkPen(QColor('red'), width=2), name="Current")
        #self.coulomb_curve = plotWidget.plot([], [], pen=pg.mkPen(QColor('green'), width=2), name="Coulombs")

        self.main.tabWidget.addTab(tab, title)

    def addCoulombGraphTab(self, title):
        tab = QWidget()
        tab.plot_index = 3  # Assign a new index for tracking
        layout = QVBoxLayout(tab)
        backgroundColor = self.main.palette().color(self.main.backgroundRole())

        plotWidget = pg.PlotWidget()
        plotWidget.setBackground(backgroundColor)
        layout.addWidget(plotWidget)

        self.main.graphWidgets.append(plotWidget)
        self.main.graphTabs.append(tab)

        plotWidget.showGrid(x=True, y=True)
        plotWidget.setLabel('left', 'Value', color='black', size='11pt')
        plotWidget.setLabel('bottom', 'Time (s)', color='black', size='11pt')
        plotWidget.getAxis('left').setTextPen(QPen(QColor('black')))
        plotWidget.getAxis('bottom').setTextPen(QPen(QColor('black')))

        self.coulomb_curve = plotWidget.plot([], [], pen=pg.mkPen(QColor('black'), width=2), name="Coulombs")

        self.main.tabWidget.addTab(tab, title)

        #self.main.updateDualViewstabWidget.addTab(tab, title)

    def updateDualViews(self):
        self.main.tempViewBox.setGeometry(self.main.pHViewBox.sceneBoundingRect())
        self.main.tempViewBox.linkedViewChanged(self.main.pHViewBox, self.main.tempViewBox.XAxis)

    def _is_number(self, value):
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False

    def update(self, tab):
        plot_index = getattr(tab, 'plot_index', None)
        if plot_index == 0:
            self.update_pump_plot()
        elif plot_index == 1:
            self.update_dual_plot()
        elif plot_index == 2:
            self.update_power_plot()

    def update_pump_plot(self):
        time, data = read_log_data(self.main, 0)
        if time and data:
            x, y, time_label, scale = scale_time_data(self.main, time, data)
            self.main.graphWidgets[0].setLabel('bottom', f'Time ({time_label})', **self.labelStyle)

            if not hasattr(self.main, 'pump_curve') or self.main.pump_curve is None:
                self.main.pump_curve = self.main.graphWidgets[0].plot(x, y, pen=pg.mkPen(self.plotColors[0], width=2))
            else:
                self.main.pump_curve.setData(x, y)
    
    def update_plot_from_log(self, plot_index, curve_configs, show_right_axis=False):
        """
        plot_index: index in self.main.graphWidgets
        curve_configs: list of dicts like:
            {
                "log_index": 1,
                "curve_attr": "pH_curve",
                "pen": "g",
                "use_right_axis": False
            }
        show_right_axis: whether to show the right Y-axis (optional)
        """

        widget = self.main.graphWidgets[plot_index]
        max_points = 1000

        for cfg in curve_configs:
            data_time, data_values = read_log_data(self.main, cfg["log_index"])

            # Remove old curve if exists
            curve_attr = cfg["curve_attr"]
            if hasattr(self.main, curve_attr) and getattr(self.main, curve_attr) is not None:
                if cfg.get("use_right_axis"):
                    self.main.tempViewBox.removeItem(getattr(self.main, curve_attr))
                else:
                    widget.removeItem(getattr(self.main, curve_attr))
                setattr(self.main, curve_attr, None)

            if data_time and data_values:
                x_data, y_data, time_label, _ = scale_time_data(self.main, data_time, data_values)

                if len(x_data) > max_points:
                    x_data = x_data[-max_points:]
                    y_data = y_data[-max_points:]

                pen = pg.mkPen(cfg["pen"], width=2)
                curve = pg.PlotCurveItem(x_data, y_data, pen=pen)

                if cfg.get("use_right_axis"):
                    self.main.tempViewBox.addItem(curve)
                    self.main.tempViewBox.enableAutoRange(axis=pg.ViewBox.YAxis)
                else:
                    widget.setLabel('bottom', f'Time ({time_label})', **self.labelStyle)
                    widget.addItem(curve)

                setattr(self.main, curve_attr, curve)

        # Optionally show or hide right axis
        if show_right_axis:
            widget.showAxis('right')
        else:
            widget.hideAxis('right')

    def update_dual_plot(self):
        curve_configs = [
            {
                "log_index": 1,
                "curve_attr": "pH_curve",
                "pen": "g",
                "use_right_axis": False
            }
        ]

        # Only show temperature if enabled
        if self.main.toggleTempAction.isChecked():
            curve_configs.append({
                "log_index": 2,
                "curve_attr": "temp_curve",
                "pen": "r",
                "use_right_axis": True
            })
            show_temp = True
        else:
            show_temp = False

        self.update_plot_from_log(plot_index=1, curve_configs=curve_configs, show_right_axis=show_temp)


    def update_dual_plot_old(self):
        widget = self.main.graphWidgets[1]
        if self.main.temp_curve is not None:
            self.main.tempViewBox.removeItem(self.main.temp_curve)
            self.main.temp_curve = None

        if self.main.pH_curve is not None:
            widget.removeItem(self.main.pH_curve)
            self.main.pH_curve = None

        ph_time, ph_data = read_log_data(self.main, 1)
        temp_time, temp_data = read_log_data(self.main, 2)
        # Filter out "N/A" or invalid data
        
        #ph_data = [(t, float(v)) for t, v in zip(ph_time, ph_data_raw) if isinstance(v, (int, float)) or self._is_number(v)]
        
        #temp_data = [(t, float(v)) for t, v in zip(temp_time, temp_data_raw) if isinstance(v, (int, float)) or self._is_number(v)]
        
        max_points = 1000

        if ph_time and ph_data:
            x_ph, y_ph, time_label, _ = scale_time_data(self.main, ph_time, ph_data)
            widget.setLabel('bottom', f'Time ({time_label})', **self.labelStyle)

            if len(x_ph) > max_points:
                x_ph = x_ph[-max_points:]
                y_ph = y_ph[-max_points:]

            self.main.pH_curve = widget.plot(x_ph, y_ph, pen=pg.mkPen('g', width=2))
        
        if self.main.toggleTempAction.isChecked():
            if temp_time and temp_data:
                x_temp, y_temp, _, _ = scale_time_data(self.main, temp_time, temp_data)

                if len(x_temp) > max_points:
                    x_temp = x_temp[-max_points:]
                    y_temp = y_temp[-max_points:]

                self.main.temp_curve = pg.PlotCurveItem(x_temp, y_temp, pen=pg.mkPen('r', width=2))
                self.main.tempViewBox.addItem(self.main.temp_curve)
                self.main.tempViewBox.enableAutoRange(axis=pg.ViewBox.YAxis)
            self.main.graphWidgets[1].showAxis('right')
        else:
            # Remove temp curve if it's showing
            if self.main.temp_curve:
                self.main.tempViewBox.removeItem(self.main.temp_curve)
                self.main.temp_curve = None

            # Hide the right axis
            self.main.graphWidgets[1].hideAxis('right')

    def update_power_plot(self):
        if hasattr(self.main, 'voltage_log') and self.main.voltage_log:
            times, volts = zip(*self.main.voltage_log)
            times = np.array(times) - times[0]
            self.main.volt_curve.setData(times, volts)

        if hasattr(self.main, 'current_log') and self.main.current_log:
            times, amps = zip(*self.main.current_log)
            times = np.array(times) - times[0]
            self.main.curr_curve.setData(times, amps)

        if hasattr(self.main, 'coulomb_log') and self.main.coulomb_log:
            times, coulombs = zip(*self.main.coulomb_log)
            times = np.array(times) - times[0]
            self.main.coulomb_curve.setData(times, coulombs)
