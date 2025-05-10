from PyQt5.QtWidgets import QCheckBox, QSizePolicy
from PyQt5.QtCore import Qt, QRectF, QPointF, QSize
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen, QLinearGradient, QPaintEvent, QFont

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
        handle_color = QColor("#6ec06e") if self.isChecked() else QColor("#cccccc")
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
