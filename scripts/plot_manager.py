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
    
    def addGraphTab(
        self,
        title,
        plot_index,
        left_label="Value",
        right_label=None,  # None disables right Y-axis
        left_units="",
        right_units=""
        #left_curve="",
        #right_curve=""
    ):
        tab = QWidget()
        tab.plot_index = plot_index
        layout = QVBoxLayout(tab)
        backgroundColor = self.main.palette().color(self.main.backgroundRole())

        # Create main PlotWidget
        plotWidget = pg.PlotWidget()
        plotWidget.setBackground(backgroundColor)
        layout.addWidget(plotWidget)

        self.main.graphWidgets.append(plotWidget)
        self.main.graphTabs.append(tab)

        # Optional curve handles (naming is up to you)
        #if plot_index == 1:
        #self.main.{left_curve}_curve = None
        #self.main.{right_curve}_curve = None

        # Setup main view (left axis)
        plotWidget.showGrid(x=True, y=True)
        plotWidget.setLabel('left', f'{left_label} {left_units}', color='black', size='11pt')
        plotWidget.setLabel('bottom', 'Time (s)', color='black', size='11pt')
        plotWidget.getAxis('left').setTextPen(QPen(QColor('black')))
        plotWidget.getAxis('bottom').setTextPen(QPen(QColor('black')))

        # Optionally setup right axis (e.g., for temperature)
        if right_label:
            right_viewbox = pg.ViewBox()
            plotWidget.scene().addItem(right_viewbox)
            plotWidget.getAxis('right').linkToView(right_viewbox)
            plotWidget.showAxis('right')
            plotWidget.setLabel('right', f'{right_label} {right_units}', color='black', size='11pt')
            plotWidget.getAxis('right').setTextPen(QPen(QColor('black')))
            right_viewbox.setXLink(plotWidget)
        
        # Store ViewBoxes for alignment
        self.main.viewBoxes[plot_index] = plotWidget.getViewBox()
        
        if right_label:
            self.main.rightViewBoxes[plot_index] = right_viewbox

            # Connect update signal to generalized handler
            plotWidget.getViewBox().sigResized.connect(
                lambda vb=plotWidget.getViewBox(), ri=plot_index: self.updateLinkedViews(ri)
            )

        self.main.tabWidget.addTab(tab, title)

        # Optional tab styling
        self.main.tabWidget.setStyleSheet("""
            QTabBar::tab {
                font-size: 10pt;
                height: 20px;
                width: 110px;
                padding: 5px;
            }
        """)
    def updateLinkedViews(self, plot_index):
        if plot_index not in self.main.rightViewBoxes or plot_index not in self.main.viewBoxes:
            return

        right_vb = self.main.rightViewBoxes[plot_index]
        left_vb = self.main.viewBoxes[plot_index]

        right_vb.setGeometry(left_vb.sceneBoundingRect())
        right_vb.linkedViewChanged(left_vb, right_vb.XAxis)

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
        elif plot_index == 3:
            self.update_coulomb_plot()


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
                    right_vb = self.main.rightViewBoxes.get(plot_index)
                    if right_vb:
                        right_vb.removeItem(getattr(self.main, curve_attr))
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
                    right_vb = self.main.rightViewBoxes.get(plot_index)
                    if right_vb:
                        right_vb.addItem(curve)
                        right_vb.enableAutoRange(axis=pg.ViewBox.YAxis)
                    #self.main.tempViewBox.addItem(curve)
                    #self.main.tempViewBox.enableAutoRange(axis=pg.ViewBox.YAxis)
                else:
                    widget.setLabel('bottom', f'Time ({time_label})', **self.labelStyle)
                    widget.addItem(curve)

                setattr(self.main, curve_attr, curve)

        # Optionally show or hide right axis
        if show_right_axis:
            widget.showAxis('right')
        else:
            widget.hideAxis('right')

    def update_pump_plot(self):
        curve_configs = [
            {
                "log_index": 0,
                "curve_attr": "pump_curve",
                "pen": "r",
                "use_right_axis": False
            }
        ]
        self.update_plot_from_log(plot_index=0, curve_configs=curve_configs, show_right_axis=False)


    def update_dual_plot(self):
        curve_configs = [
            {
                "log_index": 1,
                "curve_attr": "pH_curve",
                "pen": "k",
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


    def update_power_plot(self):
        curve_configs = [
            {
                "log_index": 3,
                "curve_attr": "Volt_curve",
                "pen": "k",
                "use_right_axis": False
            }
        ]

        # Only show temperature if enabled
        #if self.main.toggleTempAction.isChecked():
        curve_configs.append({
            "log_index": 4,
            "curve_attr": "amp_curve",
            "pen": "r",
            "use_right_axis": True
        })
        show_amp = True
        self.update_plot_from_log(plot_index=2, curve_configs=curve_configs, show_right_axis=show_amp)


    def update_coulomb_plot(self):
        curve_configs = [
            {
                "log_index": 5,
                "curve_attr": "Coulomb_curve",
                "pen": "b",
                "use_right_axis": False
            }
        ]
       
        self.update_plot_from_log(plot_index=3, curve_configs=curve_configs, show_right_axis=False)


        if hasattr(self.main, 'current_log') and self.main.current_log:
            times, amps = zip(*self.main.current_log)
            times = np.array(times) - times[0]
            self.main.curr_curve.setData(times, amps)

        if hasattr(self.main, 'coulomb_log') and self.main.coulomb_log:
            times, coulombs = zip(*self.main.coulomb_log)
            times = np.array(times) - times[0]
            self.main.coulomb_curve.setData(times, coulombs)
