from PyQt5.QtWidgets import QCheckBox, QSizePolicy, QPushButton
from PyQt5.QtCore import Qt, QRectF, QPointF, QSize
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen, QLinearGradient, QPaintEvent, QFont, QPainterPath

class Fusion3DToggle(QCheckBox):
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
        font.setPointSizeF(height * 0.3)
        painter.setFont(font)
        painter.drawText(QRectF(
            handle_center.x() - handle_radius,
            handle_center.y() - handle_radius,
            2 * handle_radius,
            2 * handle_radius),
            Qt.AlignCenter, label)

        painter.end()

class RoundSetButton(QPushButton):
    def __init__(self, label="Set", parent=None):
        super().__init__(label, parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(60, 60)  # Enforces a circular shape

    def sizeHint(self):
        side = max(self.fontMetrics().height(), 60)
        return QSize(side, side)

    def paintEvent(self, event):
        size = min(self.width(), self.height())
        center = self.rect().center()
        radius = size / 2 - 2

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Shadow or inset effect
        if self.isDown():
            top_color = QColor("#b0b0b0")  # darker pressed
            bottom_color = QColor("#909090")
        else:
            top_color = QColor("#e0e0e0")
            bottom_color = QColor("#ffffff")

        gradient_brush = QBrush(top_color if self.isDown() else bottom_color)
        painter.setBrush(gradient_brush)
        painter.setPen(QPen(Qt.gray, 2))

        # Draw circle
        painter.drawEllipse(center, radius, radius)

        # Draw text
        painter.setPen(Qt.black)
        font = painter.font()
        font.setBold(True)
        font.setPointSizeF(radius * 0.4)
        painter.setFont(font)

        painter.drawText(self.rect(), Qt.AlignCenter, self.text())

        painter.end()

class Push3DButton(QPushButton):
    def __init__(self, text="Set", parent=None):
        super().__init__(text, parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(80, 30)
        self.setFont(QFont("Arial", 11))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()

        # Background
        bg_color = QColor("#e0e0e0") if not self.isDown() else QColor("#d0d0d0")
        painter.setBrush(bg_color)
        painter.setPen(Qt.NoPen)
        painter.drawRect(rect)

        # Draw 3D effect with lines
        pen = QPen()
        pen.setWidth(2)

        if not self.isDown():
            # Sunken look: bottom and right borders
            pen.setColor(QColor("gray"))
            painter.setPen(pen)
            painter.drawLine(rect.bottomLeft(), rect.bottomRight())  # bottom
            painter.drawLine(rect.topRight(), rect.bottomRight())    # right
        else:
            # Raised look: top and left borders
            pen.setColor(QColor("gray"))
            painter.setPen(pen)
            painter.drawLine(rect.topLeft(), rect.topRight())        # top
            painter.drawLine(rect.topLeft(), rect.bottomLeft())      # left

        # Draw text centered
        painter.setPen(Qt.black)
        font = painter.font()
        font.setPointSizeF(rect.height() * 0.35)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignCenter, self.text())

        painter.end()

    def sizeHint(self):
        return QSize(100, 40)
    
class Round3DButton(QPushButton):
    def __init__(self, text="Set", parent=None):
        super().__init__(text, parent)
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
            
            border_pen.setColor(QColor("#c8c8c8"))
            painter.setPen(border_pen)
            painter.drawArc(rect.adjusted(6, 6, -6, -6), 45 * 16, 180 * 16)
            

        bg_color = QColor("#a6a6a6")
        #painter.setBrush(QColor("#a6a6a6"))
        pen = QPen(bg_color, 1)
        painter.setPen(pen)
        inner_radius = radius-1
        painter.drawEllipse(center, inner_radius, inner_radius)
        
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