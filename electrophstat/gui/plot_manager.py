from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtGui import QPen, QColor, QFont
from PyQt5.QtCore import Qt
import numpy as np
import pyqtgraph as pg
from datetime import datetime

class PlotManager:
    def __init__(self, main):
        self.main = main
        self.labelStyle = {'color': 'black', 'font-size': '11pt'}
        self.plotColors = ['r', 'g', 'b', 'm', 'c', 'y']
        # in PlotManager.__init__
        self._all_curve_configs = {
            # label: (plot_index, curve_attr, pen, use_right_axis)
            "pump":         (0, "pump_curve",   "r", False),
            "pH":           (1, "ph_curve",     "k", False),
            "temperature":  (1, "temp_curve",   "b", True),
            "voltage":      (2, "volt_curve",   "g", False),
            "current":      (2, "amp_curve",    "b", True),
            "coulomb":      (3, "coulomb_curve","m", False),
        }

    def addGraphTab(
        self,
        title,
        plot_index,
        left_label="Value",
        right_label=None,
        left_units="",
        right_units=""
    ):
        tab = QWidget()
        tab.plot_index = plot_index
        layout = QVBoxLayout(tab)
        backgroundColor = self.main.palette().color(self.main.backgroundRole())

        plotWidget = pg.PlotWidget()
        plotWidget.setBackground(backgroundColor)
        layout.addWidget(plotWidget)

        self.main.graphWidgets.append(plotWidget)
        self.main.graphTabs.append(tab)

        plotWidget.showGrid(x=True, y=True)
        plotWidget.setLabel('left', f'{left_label} {left_units}', **self.labelStyle)
        plotWidget.setLabel('bottom', 'Time (s)', **self.labelStyle)
        plotWidget.getAxis('left').setTextPen(QPen(QColor('black')))
        plotWidget.getAxis('bottom').setTextPen(QPen(QColor('black')))

        if right_label:
            right_vb = pg.ViewBox()
            plotWidget.scene().addItem(right_vb)
            plotWidget.getAxis('right').linkToView(right_vb)
            plotWidget.showAxis('right')
            plotWidget.setLabel('right', f'{right_label} {right_units}', **self.labelStyle)
            plotWidget.getAxis('right').setTextPen(QPen(QColor('black')))
            right_vb.setXLink(plotWidget)
            self.main.rightViewBoxes[plot_index] = right_vb
            plotWidget.getViewBox().sigResized.connect(
                lambda vb=plotWidget.getViewBox(), ri=plot_index: self.updateLinkedViews(ri)
            )

        self.main.viewBoxes[plot_index] = plotWidget.getViewBox()
        self.main.tabWidget.addTab(tab, title)

    def updateLinkedViews(self, plot_index):
        if plot_index not in self.main.rightViewBoxes or plot_index not in self.main.viewBoxes:
            return
        left_vb = self.main.viewBoxes[plot_index]
        right_vb = self.main.rightViewBoxes[plot_index]
        right_vb.setGeometry(left_vb.sceneBoundingRect())
        right_vb.linkedViewChanged(left_vb, right_vb.XAxis)

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

    def update_plot_from_logger(self, plot_index, curves, show_right_axis=False):
        """
        curves: list of dicts:
          {"label": str, "curve_attr": str, "pen": str, "use_right_axis": bool}
        """
        widget = self.main.graphWidgets[plot_index]
        max_points = 1000
        logger = self.main.logger

        for cfg in curves:
            label = cfg["label"]
            times, values = logger.read(label)

            # clear old curve
            attr = cfg["curve_attr"]
            old = getattr(self.main, attr, None)
            if old is not None:
                if cfg.get("use_right_axis"):
                    vb = self.main.rightViewBoxes.get(plot_index)
                    if vb: vb.removeItem(old)
                else:
                    widget.removeItem(old)
                setattr(self.main, attr, None)

            if times and values:
                x = np.array(times)
                y = np.array(values)
                if len(x) > max_points:
                    x = x[-max_points:]
                    y = y[-max_points:]

                pen = pg.mkPen(cfg["pen"], width=2)
                curve = pg.PlotCurveItem(x, y, pen=pen)

                if cfg.get("use_right_axis"):
                    vb = self.main.rightViewBoxes.get(plot_index)
                    if vb:
                        vb.addItem(curve)
                        vb.enableAutoRange(axis=pg.ViewBox.YAxis)
                else:
                    widget.getAxis('bottom').setLabel('Time (s)', **self.labelStyle)
                    widget.addItem(curve)

                setattr(self.main, attr, curve)

        widget.showAxis('right' if show_right_axis else 'left')

    def update_pump_plot(self):
        curves = [{"label": "volume", "curve_attr": "pump_curve", "pen": "r", "use_right_axis": False}]
        self.update_plot_from_logger(0, curves)

    def update_dual_plot(self):
        curves = [{"label": "ph", "curve_attr": "ph_curve", "pen": "k", "use_right_axis": False}]
        if self.main.toggleTempAction.isChecked():
            curves.append({"label": "temperature", "curve_attr": "temp_curve", "pen": "b", "use_right_axis": True})
        self.update_plot_from_logger(1, curves, show_right_axis=self.main.toggleTempAction.isChecked())

    def update_power_plot(self):
        curves = [
            {"label": "voltage", "curve_attr": "volt_curve", "pen": "g", "use_right_axis": False},
            {"label": "current", "curve_attr": "amp_curve", "pen": "b", "use_right_axis": True}
        ]
        self.update_plot_from_logger(2, curves, show_right_axis=True)

    def update_coulomb_plot(self):
        curves = [{"label": "coulomb", "curve_attr": "coulomb_curve", "pen": "m", "use_right_axis": False}]
        self.update_plot_from_logger(3, curves)

    def _scale_graph_fonts(self, widget, label_size, tick_size):
        if widget is None:
            return
        style = {'color': 'black', 'font-size': f'{label_size}pt'}
        for axname in ('left','bottom','right'):
            ax = widget.getAxis(axname)
            if not ax: continue
            old = ax.style.get('tickFont', QFont())
            f = QFont(old)
            f.setPointSize(tick_size)
            ax.setStyle(tickFont=f)
            ax.setTextPen(QPen(QColor('black')))
            if axname in ('left','bottom','right') and ax.labelText:
                ax.setLabel(ax.labelText, **style)
    
    def update_all_plots(self):
        logger = self.main.logger
        # only proceed if we have active files
        if not getattr(logger, "files", None):
            return

        # gather per-tab configs
        configs_by_tab = {}
        for label in logger.files.keys():
            if label not in self._all_curve_configs:
                continue
            plot_index, curve_attr, pen, use_right = self._all_curve_configs[label]
            configs_by_tab.setdefault(plot_index, []).append({
                "label":         label,
                "curve_attr":    curve_attr,
                "pen":           pen,
                "use_right_axis": use_right,
            })

        # now update each tab that has data
        for tab_idx, cfgs in configs_by_tab.items():
            # determine if any curve on this tab uses the right axis
            show_right = any(c["use_right_axis"] for c in cfgs)
            self.update_plot_from_logger(
                plot_index       = tab_idx,
                curves           = cfgs,
                show_right_axis  = show_right
            )
