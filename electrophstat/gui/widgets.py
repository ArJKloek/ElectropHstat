from PyQt5.QtWidgets import (QVBoxLayout, QPushButton, 
                             QWidget, QHBoxLayout, QSpinBox, QLabel, QCheckBox, QHBoxLayout, QSizePolicy, QDial, QGridLayout)
from PyQt5.QtCore import Qt, QSize, QPoint, QRectF, QPointF, pyqtSlot as Slot, pyqtProperty as Property
from PyQt5.QtGui import QPainter, QColor, QFont, QFontMetrics, QPen, QPaintEvent, QBrush, QLinearGradient



class CustomTextWidget(QWidget):
    def __init__(self, normalText, shadowText, color, size):#, shadowColor="#000000"):
        super().__init__()
        self.normalText = normalText
        self.shadowText = shadowText
        self.color = color
        self.normalTextColor = Qt.black  # Default normal text color is black

        #self.shadowColor = shadowColor
        self.size = size
        self.font = QFont("Arial", self.size)  # Define the font as a class attribute
        metrics = QFontMetrics(self.font)

        # Precompute maximum expected width
        self.max_normalText = "pH Stat "  # This doesn't change
        self.max_shadowText = "Inactive"  # Assume "Inactive" is the longest shadow text

        # Precompute total width
        normal_size = metrics.size(Qt.TextSingleLine, self.max_normalText)
        shadow_size = metrics.size(Qt.TextSingleLine, self.max_shadowText)
        self.fixed_total_width = normal_size.width() + shadow_size.width()
        self.fixed_total_height = metrics.height()
        
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setFont(self.font)

        metrics = QFontMetrics(self.font)
        normalTextSize = metrics.size(Qt.TextSingleLine, self.normalText)
        shadowTextSize = metrics.size(Qt.TextSingleLine, self.shadowText)

        # Use fixed precomputed width
        x_normal = round((self.width() - self.fixed_total_width) / 2)
        x_shadow = round(x_normal + metrics.size(Qt.TextSingleLine, self.normalText).width())

        y = round((self.height() + self.fixed_total_height) / 2)

        # Draw normal text
        painter.setPen(QColor(self.normalTextColor))
        painter.drawText(x_normal, y, self.normalText)

        # Calculate shadow offset for shadow text
        shadowOffset = QPoint(1, 1)

        # Draw shadow text
        painter.setPen(QColor(0, 0, 0, 100))
        painter.drawText(x_shadow + shadowOffset.x(), y + shadowOffset.y(), self.shadowText)

        # Optionally, draw shadowed text (on top without offset) for stronger effect
        painter.setPen(QColor(self.color))
        painter.drawText(x_shadow, y, self.shadowText)

        painter.end()
    
    def setFlash(self, a0: bool):
        if a0:
            self.setColor("#1E8449")
        else:
            self.setColor("#F1C40F")


    def setEnabled(self, a0: bool) -> None:
        if a0:
            self.setColor("#F1C40F")
        else:
            self.setColor("#DCDCDC")
    
    def setFontsize(self, size):
        self.size = size
        self.font = QFont("Arial", int(self.size))  # update the font

        metrics = QFontMetrics(self.font)
        normal_size = metrics.size(Qt.TextSingleLine, self.max_normalText)
        shadow_size = metrics.size(Qt.TextSingleLine, self.max_shadowText)
        self.fixed_total_width = normal_size.width() + shadow_size.width()
        self.fixed_total_height = metrics.height()

        self.setMinimumHeight(self.fixed_total_height + 10)  # Add a little padding

        self.update()

    
    def setColor(self, color):
        self.color = color
        self.update()  # Trigger a repaint with the new color
    
    def updateText(self, new_shadow_text):
        self.shadowText = new_shadow_text
        self.update()  # Trigger repaint
    def updateNormalColor(self, new_normal_color):
        if new_normal_color is not None:
            self.normalTextColor = new_normal_color  # Normal text color
            self.update()
        
    def sizeHint(self):
        return QSize(self.fixed_total_width, self.fixed_total_height + 10)

class ToggleSwitch(QCheckBox):

    _transparent_pen = QPen(Qt.transparent)
    _light_grey_pen = QPen(Qt.lightGray)
    _black_pen = QPen(Qt.black)

    def __init__(self, 
                 parent=None, 
                 bar_color="#2196F3", 
                 checked_color="#00B0FF",
                 handle_color=Qt.white, 
                 h_scale=1.0,
                 v_scale=1.0,
                 fontSize=10):
             
        super().__init__(parent)

        # Save our properties on the object via self, so we can access them later
        # in the paintEvent.
        self._bar_cv_brush = QBrush(QColor("#BBDEFB"))  # Blue for CV
        self._bar_brush = QBrush(QColor(bar_color))
        self._bar_checked_brush = QBrush(QColor(checked_color).lighter())

        self._handle_brush = QBrush(handle_color)
        self._handle_checked_brush = QBrush(QColor(checked_color))

        # Setup the rest of the widget.

        self.setContentsMargins(8, 0, 8, 0)
        self._handle_position = 0
        self._h_scale = h_scale
        self._v_scale = v_scale
        self._fontSize = fontSize

        self.stateChanged.connect(self.handle_state_change)

    def sizeHint(self):
        return QSize(58, 45)

    def hitButton(self, pos: QPoint):
        return self.contentsRect().contains(pos)

    def paintEvent(self, e: QPaintEvent):
        super().paintEvent(e)
        contRect = self.contentsRect()
        width =  contRect.width() * self._h_scale
        height = contRect.height() * self._v_scale
        #handleRadius = round(0.24 * height)
        
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        p.setPen(self._transparent_pen)
        #barRect = QRectF(0, 0, width - handleRadius, 0.40 * height)
        barRect = QRectF(0, 0, 0.40 * width, height - 10)
        barRect.moveCenter(contRect.center())
        rounding = barRect.width() / 2
        
        handleRadius = round(0.9 * barRect.width())


       
        trailLength = barRect.height() - 2 * handleRadius
        yTop = barRect.top() + handleRadius
        yPos = yTop + trailLength * self._handle_position
        
        
        if not self.isEnabled():
            p.setBrush(QBrush(QColor("#cccccc")))  # Light gray bar
            p.drawRoundedRect(barRect, rounding, rounding)
            p.setBrush(QBrush(QColor("#aaaaaa")))  # Gray handle
            p.drawEllipse(QPointF(barRect.center().x(), yPos), handleRadius, handleRadius)

            # Optional: draw text inside handle
            p.setPen(QColor("white"))
            p.setFont(QFont('Helvetica', int(self._fontSize), 75))
            p.drawText(QRectF(
                barRect.center().x() - handleRadius,
                yPos - handleRadius,
                2 * handleRadius,
                2 * handleRadius),
                Qt.AlignCenter,
                "—"  # or "CV"/"CC", or blank
            )

            p.end()
            return  # Exit early so we don't draw the active version
        
        if self.isChecked():
            p.setBrush(self._bar_checked_brush)
            p.drawRoundedRect(barRect, rounding, rounding)
            p.setBrush(self._handle_checked_brush)

        else:
            p.setBrush(self._bar_cv_brush)
            p.drawRoundedRect(barRect, rounding, rounding)
            p.setBrush(self._handle_brush)
            
            
        if self.isChecked():
            p.setBrush(self._handle_checked_brush)  # green handle
        else:
            p.setBrush(QBrush(QColor("#2196F3")))  # blue handle

        p.setPen(self._light_grey_pen)
        p.drawEllipse(
            QPointF(barRect.center().x(), yPos),
            handleRadius, handleRadius)
        # Draw text on handle
        p.setPen(self._black_pen)
        p.setFont(QFont('Helvetica', int(self._fontSize), 75))

        text = "CC" if self.isChecked() else "CV"
        text_rect = QRectF(
            barRect.center().x() - handleRadius,
            yPos - handleRadius,
            2 * handleRadius,
            2 * handleRadius
        )
        p.drawText(text_rect, Qt.AlignCenter, text)

        p.end()

    @Slot(int)
    def handle_state_change(self, value):
        self._handle_position = 1 if value else 0

    @Property(float)
    def handle_position(self):
        return self._handle_position

    @handle_position.setter
    def handle_position(self, pos):
        """change the property
           we need to trigger QWidget.update() method, either by:
           1- calling it here [ what we're doing ].
           2- connecting the QPropertyAnimation.valueChanged() signal to it.
        """
        self._handle_position = pos
        self.update()

    def setH_scale(self,value):
        self._h_scale = value
        self.update()

    def setV_scale(self,value):
        self._v_scale = value
        self.update()

    def setFontSize(self,value):
        self._fontSize = value
        self.update()

class PHSelectorWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.active_segment = 0  # 0 = whole, 1 = decimal

        # Spinboxes (non-editable)
        self.whole = QSpinBox()
        self.whole.setRange(0, 14)
        self.whole.setSuffix(".")

        self.decimal = QSpinBox()
        self.decimal.setRange(0, 9)

        for box in (self.whole, self.decimal):
            box.setButtonSymbols(QSpinBox.NoButtons)
            box.setAlignment(Qt.AlignCenter)
            box.setWrapping(True)
            box.setFocusPolicy(Qt.NoFocus)  # no keyboard

        # Click to select
        self.whole.mousePressEvent = self._make_activate_handler(0)
        self.decimal.mousePressEvent = self._make_activate_handler(1)

        # Action buttons
        self.btn_up = QPushButton("▲")
        self.btn_down = QPushButton("▼")
        self.btn_up.clicked.connect(lambda: self._adjust_segment(1))
        self.btn_down.clicked.connect(lambda: self._adjust_segment(-1))

        # Layout
        layout = QVBoxLayout()
        top_row = QHBoxLayout()
        top_row.addWidget(QLabel("pH:"))
        top_row.addWidget(self.whole)
        top_row.addWidget(self.decimal)
        layout.addLayout(top_row)

        control_row = QHBoxLayout()
        control_row.addWidget(self.btn_up)
        control_row.addWidget(self.btn_down)
        layout.addLayout(control_row)

        self.setLayout(layout)
        self.select_segment(0)

    def _make_activate_handler(self, segment):
        def handler(event):
            self.select_segment(segment)
        return handler

    def select_segment(self, segment):
        self.active_segment = segment
        self.whole.setStyleSheet("border: 2px solid blue;" if segment == 0 else "")
        self.decimal.setStyleSheet("border: 2px solid blue;" if segment == 1 else "")

    def _adjust_segment(self, step):
        if self.active_segment == 0:
            self.whole.stepBy(step)
        else:
            self.decimal.stepBy(step)

    def value(self):
        return float(f"{self.whole.value()}.{self.decimal.value()}")

class PowerButton(QCheckBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(100, 40)
        self._handle_position = 1 if self.isChecked() else 0
        self.stateChanged.connect(self._handle_state_change)

    def _handle_state_change(self, value):
        self._handle_position = 1 if value else 0
        self.update()

    def sizeHint(self):
        return QSize(100, 40)
    
    def hitButton(self, pos):
        return self.rect().contains(pos)

    def paintEvent(self, e: QPaintEvent):
        width = self.width()
        height = self.height()

        radius = height / 2
        handle_radius = radius * 0.9
        bar_width = width * 0.95
        bar_height = height * 0.5

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Bar background with bevel
        bar_rect = QRectF(0, 0, bar_width, bar_height)
        bar_rect.moveCenter(self.rect().center())

        bar_gradient = QLinearGradient(bar_rect.topLeft(), bar_rect.bottomLeft())
        bar_gradient.setColorAt(0, QColor("#e0e0e0"))  # light top
        bar_gradient.setColorAt(1, QColor("#b0b0b0"))  # dark bottom

        painter.setBrush(bar_gradient)
        painter.setPen(Qt.gray)
        painter.drawRoundedRect(bar_rect, bar_height / 2, bar_height / 2)

        # Handle position
        trail_len = bar_rect.width() - 2 * handle_radius
        x_pos = bar_rect.left() + handle_radius + trail_len * self._handle_position
        handle_center = QPointF(x_pos, bar_rect.center().y())

        # Optional press effect
        offset = 1 if self.isDown() else 0
        handle_center += QPointF(offset, offset)

        # Draw handle shadow
        painter.setBrush(QColor(0, 0, 0, 60))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(handle_center.x() + 2, handle_center.y() + 2),
                            handle_radius, handle_radius)

        # Outer ring
        painter.setBrush(Qt.white)
        painter.setPen(Qt.gray)
        painter.drawEllipse(handle_center, handle_radius, handle_radius)

        # Inner handle circle (colored)
        handle_color = QColor("#6ec06e") if self.isChecked() else QColor("#ec7063")
        painter.setBrush(handle_color)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(handle_center, handle_radius * 0.8, handle_radius * 0.8)

        # Draw text on handle
        label = "ON" if self.isChecked() else "OFF"
        painter.setPen(Qt.white)
        font = painter.font()
        font.setPointSizeF(height * 0.2)
        painter.setFont(font)
        painter.drawText(QRectF(
            handle_center.x() - handle_radius,
            handle_center.y() - handle_radius,
            2 * handle_radius,
            2 * handle_radius),
            Qt.AlignCenter, label)

        painter.end()

class Round3DButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(60, 60)
        self.setFont(QFont("Arial", 11))

    def sizeHint(self):
        side = max(60, self.fontMetrics().height() * 3)
        return QSize(side, side)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()
        size = min(rect.width(), rect.height())
        radius = size / 2 - 2
        center = rect.center()

        # Background color
        
        #gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        #gradient.setColorAt(0, Qt.white)  # top-left
        #gradient.setColorAt(1, QColor("#d3d3d3"))           # bottom-right

        #painter.setBrush(gradient)
        #painter.setPen(Qt.NoPen)
        #painter.drawEllipse(center, radius, radius)
 
        # 3D border effect
        border_pen = QPen()
        border_pen.setWidth(2)

        if not self.isDown():       #ecf0f1
            # Sunken: draw bottom + right highlight
            gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
            gradient.setColorAt(0, QColor("#f7f7f7"))  # top-left
            gradient.setColorAt(1, QColor("#e1e1e1"))           # bottom-right

            painter.setBrush(gradient)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(center, radius, radius)

            bg_color = QColor("#a6a6a6")
            pen = QPen(bg_color, 1)
            painter.setPen(pen)
            inner_radius = radius-1
            painter.drawEllipse(center, inner_radius, inner_radius)

            border_pen.setColor(QColor("#c8c8c8"))
            painter.setPen(border_pen)
            painter.drawArc(rect.adjusted(2, 2, -2, -2), 225 * 16, 180 * 16)
            
        
        else:
            # Raised: draw top + left highlight
            gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
            gradient.setColorAt(0, QColor("#f5f5f5"))  # top-left
            gradient.setColorAt(1, QColor("#dfdfdf"))           # bottom-right

            painter.setBrush(gradient)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(center, radius, radius)
            
            bg_color = QColor("#a6a6a6")
            pen = QPen(bg_color, 1)
            painter.setPen(pen)
            inner_radius = radius-1
            painter.drawEllipse(center, inner_radius, inner_radius)
        
            border_pen.setColor(QColor("#c8c8c8"))
            painter.setPen(border_pen)
            painter.drawArc(rect.adjusted(4, 4, -4, -4), 45 * 16, 180 * 16)
            

        #bg_color = QColor("#a6a6a6")
        #painter.setBrush(QColor("#a6a6a6"))
        #pen = QPen(bg_color, 1)
        #painter.setPen(pen)
        #inner_radius = radius-1
        #painter.drawEllipse(center, inner_radius, inner_radius)
        
        # Draw centered text
        offset = QPointF(1.5, 1.5) if self.isDown() else QPointF(0, 0)
        # Draw text centered, but slightly shifted if pressed
        text_rect = self.rect().translated(offset.toPoint())
        
        painter.setPen(Qt.black)
        font = painter.font()
        font.setPointSizeF(radius * 0.5)
        painter.setFont(font)
        painter.drawText(text_rect, Qt.AlignCenter, self.text())

        painter.end()


class DialWithLabel(QDial):
    """A QDial with a centered QLabel showing its current value."""
    def __init__(self, parent=None, *, font_pt=16):
        super().__init__(parent)

        self.valueChanged.connect(self._on_value_change)
        self.label = QLabel("0", self)
        self.label.setAlignment(Qt.AlignCenter)
        font = self.label.font()
        font.setPointSize(font_pt)
        self.label.setFont(font)

        # Grid‐layout both into the same cell
        #layout = QGridLayout(self)
        #layout.addWidget(self,  0,0, alignment=Qt.AlignCenter)
        #layout.addWidget(self.label, 0,0, alignment=Qt.AlignCenter)
        #layout.setContentsMargins(0,0,0,0)
        #self.setLayout(layout)

    @Slot(int)
    def _on_value_change(self, val):
        num = val / 10.0
        self.label.setText(str(num))
    
    def resizeEvent(self, ev):
            super().resizeEvent(ev)
            # fill the dial’s area with the label
            self.label.setGeometry(self.rect())  

            # ensure label fills the dial area
            self.label.resize(self.size())

            # pick a font size as a fraction of the dial diameter
            diameter = min(self.width(), self.height())
            # tweak this factor until it looks good (0.3 is a starting point)
            pt = max(1, int(diameter * 0.15))

            f = self.label.font()
            f.setPointSize(pt)
            self.label.setFont(f)