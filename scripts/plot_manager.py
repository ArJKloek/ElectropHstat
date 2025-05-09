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
        plotWidget.getViewBox().sigResized.connect(self.main.updateDualViews)

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

    def update_dual_plot(self):
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
