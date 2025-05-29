from PyQt5.QtWidgets import (QVBoxLayout, QPushButton, 
                             QWidget, QHBoxLayout, QSpinBox, QLabel, QCheckBox, QHBoxLayout, QSizePolicy, QDial, QGridLayout)
from PyQt5.QtCore import Qt, QSize, QPoint, QRectF, QPointF, QPropertyAnimation,QSequentialAnimationGroup,QEasingCurve, pyqtSlot, pyqtSignal, pyqtProperty as Property
from PyQt5.QtGui import QPainter, QColor, QFont, QFontMetrics, QPen, QPaintEvent, QBrush, QLinearGradient

from PyQt5.QtWidgets import QCheckBox, QSizePolicy

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
        # <-- Add these two lines -->
        if not self.isEnabled():
            painter.setOpacity(0.4)
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
        # if pressed, offset everything
        offset = QPointF(1.5, 1.5) if self.isDown() else QPointF(0,0)
        center += offset

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

            
            
            # 1) define the diagonal gradient:
            grad = QLinearGradient(
                QPointF(center.x() - radius, center.y() - radius),  # top-left of circle
                QPointF(center.x() + radius, center.y() + radius)   # bottom-right
            )
            grad.setColorAt(0.0, QColor("#ffffff"))  # highlight at top
            grad.setColorAt(1.0, QColor("#888888"))  # shadow at bottom

            # 2) create a pen that strokes with that gradient
            pen = QPen(QBrush(grad), 2.0)
            painter.setBrush(Qt.NoBrush)
            painter.setPen(pen)

            # 3) draw a true circle (rx == ry)
            painter.drawEllipse(center, radius, radius)
            #border_pen.setColor(QColor("#c8c8c8"))
            #painter.setPen(border_pen)
            #painter.drawArc(rect.adjusted(2, 2, -2, -2), 225 * 16, 180 * 16)
            
        
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
            inner_radius = radius
            painter.drawEllipse(center, inner_radius, inner_radius)

            
            
            #border_pen.setColor(QColor("#c8c8c8"  # 1) define the diagonal gradient:
            grad = QLinearGradient(
                QPointF(center.x() - radius, center.y() - radius),  # top-left of circle
                QPointF(center.x() + radius, center.y() + radius)   # bottom-right
            )
            grad.setColorAt(0.0, QColor("#888888"))  # highlight at top
            grad.setColorAt(1.0, QColor("#ffffff"))  # shadow at bottom

            # 2) create a pen that strokes with that gradient
            pen = QPen(QBrush(grad), 2.0)
            painter.setBrush(Qt.NoBrush)
            painter.setPen(pen)
            painter.drawEllipse(center, radius, radius)
            
            #painter.setPen(border_pen)
            #painter.drawArc(rect.adjusted(4, 4, -4, -4), 45 * 16, 180 * 16)
            

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
        
        if not self.isEnabled():
            painter.setPen(Qt.gray)
        else:
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

    @pyqtSlot(int)
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

class ModeButton(QCheckBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(40, 100)
        self._handle_position = 1 if self.isChecked() else 0
        self.stateChanged.connect(self._handle_state_change)

    def _handle_state_change(self, value):
        self._handle_position = 1 if value else 0
        self.update()

    def sizeHint(self):
        return QSize(40, 100)
    
    def hitButton(self, pos):
        return self.rect().contains(pos)

    def paintEvent(self, e):
        width = self.width()
        height = self.height()

        radius = width / 2
        handle_radius = radius * 0.9
        bar_width = width * 0.5
        bar_height = height * 0.95

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        if not self.isEnabled():
            painter.setOpacity(0.4)

        # Bar background with bevel
        bar_rect = QRectF(0, 0, bar_width, bar_height)
        bar_rect.moveCenter(self.rect().center())

        bar_gradient = QLinearGradient(bar_rect.topLeft(), bar_rect.bottomLeft())
        bar_gradient.setColorAt(0, QColor("#e0e0e0"))  # light top
        bar_gradient.setColorAt(1, QColor("#b0b0b0"))  # dark bottom

        painter.setBrush(bar_gradient)
        painter.setPen(Qt.gray)
        painter.drawRoundedRect(bar_rect, bar_width / 2, bar_width / 2)

        # Handle position (top to bottom)
        trail_len = bar_rect.height() - 2 * handle_radius
        y_pos = bar_rect.top() + handle_radius + trail_len * self._handle_position
        handle_center = QPointF(bar_rect.center().x(), y_pos)

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
        handle_color = QColor("#00897b") if self.isChecked() else QColor("#29b6f6")
        painter.setBrush(handle_color)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(handle_center, handle_radius * 0.8, handle_radius * 0.8)

        # Draw text on handle
        label = "CC" if self.isChecked() else "CV"
        painter.setPen(Qt.white)
        font = painter.font()
        font.setPointSizeF(width * 0.2)
        painter.setFont(font)
        painter.drawText(QRectF(
            handle_center.x() - handle_radius,
            handle_center.y() - handle_radius,
            2 * handle_radius,
            2 * handle_radius),
            Qt.AlignCenter, label)

        painter.end()