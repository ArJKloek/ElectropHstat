from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtGui import QPen, QColor, QFont
from PyQt5.QtCore import Qt
import numpy as np
import pyqtgraph as pg
from datetime import datetime

class PlotManager:
    def __init__(self, main):
        self.main = main
        self.cfg = main.config
        self.labelStyle = {'color': 'black', 'font-size': '11pt'}
        self.plotColors = ['r', 'g', 'b', 'm', 'c', 'y']
        # in PlotManager.__init__
        self._all_curve_configs = {
            # label: (plot_index, curve_attr, pen, use_right_axis)
            "pump":         (0, "pump_curve",       "r", False),
            "pH":           (1, "ph_curve",         "k", False),
            "RTD":          (1, "temp_curve",       "b", True),
            "voltage":      (2, "volt_curve",       "g", False),
            "current":      (2, "amp_curve",        "b", True),
            "coulomb":      (3, "coulomb_curve",    "m", False),
            "turbidity":    (4, "turbidity_curve",  "b", False)
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
        elif plot_index ==4:
            self.update_turbidity_plot()

    def update_plot_from_logger(self, plot_index, curves, show_right_axis=False):
        widget = self.main.graphWidgets[plot_index]
        logger = self.main.logger

        # We'll set the bottom label exactly once, based on the first curve's data
        bottom_labeled = False

        for cfg in curves:
            label = cfg["label"]
            #times, values = logger.read(label)
            try:
                data = logger.read(label)
                times  = data[0]
                values = data[1]
            except Exception as e:
                print(f'Error for {label} as {e}')
            # remove any old curve
            old = getattr(self.main, cfg["curve_attr"], None)
            if old:
                container = ( self.main.rightViewBoxes[plot_index]
                              if cfg["use_right_axis"] else widget )
                container.removeItem(old)
                setattr(self.main, cfg["curve_attr"], None)

            if not times:
                continue

            # scale & get unit label
            x, y, time_label = self.scale_time_data(times, values)
            pen = pg.mkPen(cfg["pen"], width=2)
            curve = pg.PlotCurveItem(x, y, pen=pen)

            # set bottom label once
            if not bottom_labeled:
                widget.getAxis('bottom').setLabel(time_label, **self.labelStyle)
                bottom_labeled = True

            # draw on the correct axis
            if cfg["use_right_axis"]:
                vb = self.main.rightViewBoxes.get(plot_index)
                vb.addItem(curve)
                vb.enableAutoRange(axis=pg.ViewBox.YAxis)
            else:
                widget.addItem(curve)

            setattr(self.main, cfg["curve_attr"], curve)

        # show/hide right axis
        widget.showAxis('right', show_right_axis)
        #widget.showAxis('right' if show_right_axis else 'left')

    def update_pump_plot(self):
        curves = [{"label": "volume", "curve_attr": "pump_curve", "pen": "r", "use_right_axis": False}]
        self.update_plot_from_logger(0, curves)

    def update_dual_plot(self):
        curves = [{"label": "ph", "curve_attr": "ph_curve", "pen": "k", "use_right_axis": False}]
        # Only show temperature if BOTH config and toggle are True
        show_temp = self.main.toggleTempAction.isChecked() and self.cfg.atlas.RTD.enable
        if show_temp:
            curves.append({"label": "temperature", "curve_attr": "temp_curve", "pen": "b", "use_right_axis": True})
        self.update_plot_from_logger(1, curves, show_right_axis=show_temp)

    def update_power_plot(self):
        curves = [
            {"label": "voltage", "curve_attr": "volt_curve", "pen": "g", "use_right_axis": False},
            {"label": "current", "curve_attr": "amp_curve", "pen": "b", "use_right_axis": True}
        ]
        self.update_plot_from_logger(2, curves, show_right_axis=True)

    def update_coulomb_plot(self):
        curves = [{"label": "coulomb", "curve_attr": "coulomb_curve", "pen": "m", "use_right_axis": False}]
        self.update_plot_from_logger(3, curves)

    def update_turbidity_plot(self):
        curves = [{"label": "turbidity", "curve_attr": "turbidity_curve", "pen": "b", "use_right_axis": False}]
        self.update_plot_from_logger(4, curves)

    
    def _scale_graph_fonts(self, widget, label_size, tick_size):
        if widget is None:
            return
        style = {'color': 'black', 'font-size': f'{label_size}pt'}
        # Get the main window number font (fallback to default if not available)
        try:
            main_font = self.main.pHLabel.font()
        except AttributeError:
            main_font = QFont()
        main_font.setPointSize(tick_size)
        for axname in ('left','bottom','right'):
            ax = widget.getAxis(axname)
            if not ax: continue
            ax.setStyle(tickFont=main_font)
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
    
    @staticmethod
    def scale_time_data(times, values, max_points=1000):
        """
        times: list[float] in seconds
        values: list[float]
        returns: (x_scaled, y, time_label)
        """
        if not times:
            return [], [], "Time (s)"
        # truncate
        if len(times) > max_points:
            times  = times[-max_points:]
            values = values[-max_points:]
        t_max = times[-1]
        if t_max >= 3600:
            scale, time_label = 3600.0, "Time (hr)"
        elif t_max >= 60:
            scale, time_label = 60.0,   "Time (min)"
        else:
            scale, time_label = 1.0,    "Time (s)"
        x = [t/scale for t in times]
        return x, values, time_label

