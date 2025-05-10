from PyQt5.QtWidgets import QCheckBox, QSizePolicy
from PyQt5.QtCore import Qt, QRectF, QPointF, QSize
from PyQt5.QtGui import QColor, QPainter, QBrush, QPen, QPaintEvent, QFont

class Toggle(QCheckBox):
    _transparent_pen = QPen(Qt.transparent)
    _light_grey_pen = QPen(Qt.lightGray)
    _black_pen = QPen(Qt.black)

    def __init__(self, parent=None,
                 bar_color=Qt.gray,
                 checked_color="#00B0FF",
                 handle_color=Qt.white,
                 font_size_ratio=0.4):
        super().__init__(parent)
        self.setCheckable(True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(80, 40)

        # Visual appearance
        self._bar_brush = QBrush(bar_color)
        self._bar_checked_brush = QBrush(QColor(checked_color).lighter())
        self._handle_brush = QBrush(handle_color)
        self._handle_checked_brush = QBrush(QColor(checked_color))

        self._font_size_ratio = font_size_ratio
        self._handle_position = 1 if self.isChecked() else 0

        self.stateChanged.connect(self.handle_state_change)

    def sizeHint(self):
        return QSize(100, 40)

    def handle_state_change(self, value):
        self._handle_position = 1 if value else 0
        self.update()

    def paintEvent(self, e: QPaintEvent):
        width = self.width()
        height = self.height()

        radius = height / 2
        handle_radius = radius * 0.9
        bar_width = width * 0.95
        bar_height = height * 0.5

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Bar rectangle
        bar_rect = QRectF(0, 0, bar_width, bar_height)
        bar_rect.moveCenter(self.rect().center())
        rounding = bar_rect.height() / 2

        # Draw bar
        painter.setPen(self._transparent_pen)
        painter.setBrush(self._bar_checked_brush if self.isChecked() else self._bar_brush)
        painter.drawRoundedRect(bar_rect, rounding, rounding)

        # Handle position (left = 0, right = 1)
        trail_len = bar_rect.width() - 2 * handle_radius
        x_pos = bar_rect.left() + handle_radius + trail_len * self._handle_position
        handle_center = QPointF(x_pos, bar_rect.center().y())

        # Draw handle
        painter.setBrush(self._handle_checked_brush if self.isChecked() else self._handle_brush)
        painter.setPen(self._light_grey_pen)
        painter.drawEllipse(handle_center, handle_radius, handle_radius)

        # Draw label (inside handle)
        label = "ON" if self.isChecked() else "OFF"
        painter.setPen(Qt.white)
        font = painter.font()
        font.setPointSizeF(height * self._font_size_ratio)
        painter.setFont(font)

        painter.drawText(QRectF(
            handle_center.x() - handle_radius,
            handle_center.y() - handle_radius,
            2 * handle_radius,
            2 * handle_radius),
            Qt.AlignCenter, label)

        painter.end()
