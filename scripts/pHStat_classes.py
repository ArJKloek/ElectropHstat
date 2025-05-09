from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QDateTimeEdit, QPushButton, 
                             QWidget, QHBoxLayout, QSpinBox, QLabel, QComboBox, QDoubleSpinBox, QLineEdit, QCheckBox, QSizePolicy)
from PyQt5.QtCore import QEvent, Qt, QDateTime, pyqtSignal, QObject, QTimer, QSize, QPoint, QRectF, QPointF, QRect, pyqtSlot as Slot, pyqtProperty as Property
from PyQt5.QtGui import QPainter, QColor, QFont, QFontMetrics, QCursor, QPen, QPaintEvent, QBrush
from scripts.pHStat_worker import StatWorker
import os
import math
import time

class monoTimer:
    def __init__(self):
        self.start_time = None
        self.last_lap_time = None
        self.running = False

    def start(self):
        """Start or restart the timer."""
        now = time.monotonic()
        self.start_time = now
        self.last_lap_time = now
        self.running = True
        print("Timer started.")

    def stop(self):
        """Stop the timer and return the elapsed time in seconds."""
        if self.start_time is None:
            print("Warning: Timer was never started.")
            return 0
        if not self.running:
            print("Warning: Timer was already stopped.")
            return 0
        elapsed = time.monotonic() - self.start_time
        self.running = False
        print(f"Timer stopped. Elapsed: {elapsed:.4f} seconds")
        return elapsed

    def elapsed(self):
        """Get the current elapsed time without stopping."""
        if self.start_time is None:
            return 0
        if not self.running:
            return 0
        return time.monotonic() - self.start_time
    
    def lap(self):
        """Return time since last lap, and update lap time."""
        if not self.running:
            return 0
        now = time.monotonic()
        dt = now - self.last_lap_time
        self.last_lap_time = now
        return dt
    
    def reset(self):
        """Reset the timer."""
        self.start_time = None
        self.last_lap_time = None
        self.running = False
        print("Timer reset.")

class DatePickerDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Date Picker Window')
        self.setGeometry(200, 200, 300, 200)

        layout = QVBoxLayout(self)

        # Create a QDateTimeEdit widget for date selection
        self.date_edit = QDateTimeEdit(self)
        layout.addWidget(self.date_edit)

        # Set the initial date and time to the current date and time
        self.date_edit.setDateTime(QDateTime.currentDateTime())
        # Create a button to confirm date selection
        confirm_button = QPushButton('Confirm Date', self)
        layout.addWidget(confirm_button)
        confirm_button.clicked.connect(self.accept)
    
    def accept(self):
        selected_datetime = self.date_edit.dateTime()
        datetime_str = selected_datetime.toString('yyyy-MM-dd HH:mm:ss')
        #print(date)
        os.system(f'sudo date -s "{datetime_str}"')
        #print(f'Selected Date and Time: {datetime_str}')
        super().accept()  # Close the dialog
    #def getSelectedDate(self):
    #    return self.date_edit.dateTime().toString('yyyy-MM-dd HH:mm:ss')


class SelectPickerDialog(QDialog):
    select_changed = pyqtSignal(int)

    def __init__(self, select):
        super().__init__(flags=Qt.WindowCloseButtonHint)

        self.setWindowTitle('pHStat settings')
        self.setGeometry(QCursor.pos().x(), QCursor.pos().y(), 50, 50)

        
        layout = QHBoxLayout(self)
        
        self.setbutton = QPushButton("Set")
        layout.addWidget(self.setbutton)
        
        # Create a Select widget for above or below selection
        self.selectwidget = QComboBox()
        self.selectwidget.addItems(["Keep above", "Keep below"])
        self.selectwidget.setCurrentIndex(int(select))
        layout.addWidget(self.selectwidget)
        
        self.setbutton.clicked.connect(self.accept)

       
    def accept(self):
        select = self.selectwidget.currentIndex() 
        self.select_changed.emit(select)
        super().accept()  # Close the dialog
    
        
class pHPickerDialog(QDialog):
    select_changed = pyqtSignal(float)

    def __init__(self, pHSelect):
        super().__init__(flags=Qt.WindowCloseButtonHint)

        self.setWindowTitle('pHStat settings')
        self.setGeometry(QCursor.pos().x(), QCursor.pos().y(), 50, 50)
        
        layout = QHBoxLayout(self)
        
        self.setbutton = QPushButton("Set")
        layout.addWidget(self.setbutton)
        self.pHdec, self.pHint = math.modf(pHSelect)
        
        # Create a Select widget for above or below selection
        pH = QLabel('pH')
        layout.addWidget(pH)
        self.pHintwidget = QComboBox()
        self.pHintwidget.addItems(["0","1","2","3","4","5","6","7","8","9","10","11","12","13","14"])
        self.pHintwidget.setCurrentIndex(int(self.pHint))
        layout.addWidget(self.pHintwidget)
        period = QLabel('.')
        layout.addWidget(period)
        self.pHdecwidget = QComboBox()
        self.pHdecwidget.addItems(["0","1","2","3","4","5","6","7","8","9"])
        self.pHdecwidget.setCurrentIndex(int((self.pHdec*10)))
        layout.addWidget(self.pHdecwidget)
        self.setbutton.clicked.connect(self.accept)
    
    def accept(self):
        pH_select = self.pHintwidget.currentIndex() + (self.pHdecwidget.currentIndex()/10)
        self.select_changed.emit(pH_select)
        super().accept()  # Close the dialog

class CalibratePumpDialog(QDialog):
    select_changed = pyqtSignal(float,float)
    test_pump = pyqtSignal(bool)

    def __init__(self, ml, addtime):
        super().__init__(flags=Qt.WindowCloseButtonHint)

        self.setWindowTitle('Calibrate pump')
        self.setGeometry(200, 50, 0, 0)

        layout = QHBoxLayout(self)
        
        self.setbutton = QPushButton("Set")
        self.setbutton.setStatusTip("Saves all values")
        layout.addWidget(self.setbutton)

        self.testbutton = QPushButton("Test")
        self.testbutton.setStatusTip("Activates pump for inputed time")
        layout.addWidget(self.testbutton)
        
        # Create a Select widget for above or below selection
        mlText = QLabel('ml/inj:')
        layout.addWidget(mlText)
        self.mlwidget = QDoubleSpinBox()
        self.mlwidget.setDecimals(3)
        self.mlwidget.setSingleStep(0.001)
        self.mlwidget.setValue(ml)
        self.mlwidget.setStatusTip("The milimeters added in the selected addition time")
        layout.addWidget(self.mlwidget)
        self.addtimewidget = QDoubleSpinBox()
        self.addtimewidget.setDecimals(2)
        self.addtimewidget.setSingleStep(0.01)
        self.addtimewidget.setValue(addtime)
        layout.addWidget(self.addtimewidget)
        sec = QLabel('(s)')
        layout.addWidget(sec)
        
        
        
        self.setbutton.clicked.connect(self.accept)
        self.testbutton.clicked.connect(self.startTest)
    def startTest(self):
        self.testbutton.setEnabled(False)
        self.test_pump.emit(True)

        # Simulate test duration
        QTimer.singleShot(int(float(self.addtimewidget.value())*1000), self.endTest)

    def endTest(self):
        self.testbutton.setEnabled(True)
      
    def accept(self):
        newml = self.mlwidget.value()
        newaddtime = self.addtimewidget.value() 
        self.select_changed.emit(newml, newaddtime)
        super().accept()  # Close the dialog
       

class CalibratepHDialog(QDialog):
    calibrate_changed = pyqtSignal(str, float, object)

    def __init__(self, lowpH, midpH, highpH):
        super().__init__(flags=Qt.WindowCloseButtonHint)
        self.setWindowTitle('Calibrate pH')
        #self.move(200, 50)  # Position the dialog
        self.setGeometry(QCursor.pos().x(), QCursor.pos().y(), 50, 50)
        mainlayout = QVBoxLayout()

        # Low pH calibration
        lowLayout = QHBoxLayout()
        self.lowbutton = QPushButton("Cal. low")
        self.lowbutton.setStatusTip("Calibrate for low pH")
        self.lowpHwidget = QDoubleSpinBox()
        self.lowpHwidget.setDecimals(2)
        self.lowpHwidget.setSingleStep(0.01)
        self.lowpHwidget.setValue(lowpH)
        self.lowbutton.clicked.connect(lambda: self.emitCalibration("low", self.lowpHwidget.value()))
        lowLayout.addWidget(self.lowbutton)
        lowLayout.addWidget(self.lowpHwidget)

        # Mid pH calibration
        midLayout = QHBoxLayout()
        self.midbutton = QPushButton("Cal. mid")
        self.midbutton.setStatusTip("Calibrate for mid pH")
        self.midpHwidget = QDoubleSpinBox()
        self.midpHwidget.setDecimals(2)
        self.midpHwidget.setSingleStep(0.01)
        self.midpHwidget.setValue(midpH)
        self.midbutton.clicked.connect(lambda: self.emitCalibration("mid", self.midpHwidget.value()))
        midLayout.addWidget(self.midbutton)
        midLayout.addWidget(self.midpHwidget)
        # High pH calibration
        highLayout = QHBoxLayout()
        self.highbutton = QPushButton("Cal. high")
        self.highbutton.setStatusTip("Calibrate for high pH")
        self.highpHwidget = QDoubleSpinBox()
        self.highpHwidget.setDecimals(2)
        self.highpHwidget.setSingleStep(0.01)
        self.highpHwidget.setValue(highpH)
        self.highbutton.clicked.connect(lambda: self.emitCalibration("high", self.highpHwidget.value()))
        highLayout.addWidget(self.highbutton)
        highLayout.addWidget(self.highpHwidget)
        
        lineLayout = QHBoxLayout()
        self.commandline = QLineEdit()
        self.commandline.setEnabled(False)
        self.commandline.setStyleSheet("color : black;")

        lineLayout.addWidget(self.commandline)
        
        mainlayout.addLayout(midLayout)
        mainlayout.addLayout(lowLayout)
        mainlayout.addLayout(highLayout)
        mainlayout.addLayout(lineLayout)

        self.setLayout(mainlayout)  # Set the main layout on the dialog

    def emitCalibration(self, calibrationType, pH):
        data = [self.lowpHwidget.value(), self.midpHwidget.value(), self.highpHwidget.value()]  # Example data, adjust as needed
        self.calibrate_changed.emit(calibrationType, pH, data)
        # Consider closing the dialog or other actions here if needed
    
    def updateInfo(self, newInfo):
        self.commandline.setText(newInfo)

class pumpControl(QObject):
    pumpActivated = pyqtSignal(bool)
    pumpDeactivated = pyqtSignal(bool)
    cooldownEnded = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.test = False
        self.active_timer = QTimer(self)
        self.active_timer.setSingleShot(True)
        self.active_timer.timeout.connect(self.deactivate_feature)

        self.cooldown_timer = QTimer(self)
        self.cooldown_timer.setSingleShot(True)
        self.cooldown_timer.timeout.connect(self.end_cooldown)

    def activate_feature(self, duration_ms, cooldown_ms, test):
        self.test = test
        if not self.active_timer.isActive() and not self.cooldown_timer.isActive():
            self.pumpActivated.emit(self.test)
            
            #PumpON
            self.active_timer.start(duration_ms)
            self.cooldown_duration = cooldown_ms

    def deactivate_feature(self):
        self.pumpDeactivated.emit(self.test)
        #PumpOFF
        self.cooldown_timer.start(self.cooldown_duration)

    def end_cooldown(self):
        self.cooldownEnded.emit()


class DatePickerDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Date Picker Window')
        self.setGeometry(200, 200, 300, 200)

        layout = QVBoxLayout(self)

        # Create a QDateTimeEdit widget for date selection
        self.date_edit = QDateTimeEdit(self)
        layout.addWidget(self.date_edit)

        # Set the initial date and time to the current date and time
        self.date_edit.setDateTime(QDateTime.currentDateTime())
        # Create a button to confirm date selection
        confirm_button = QPushButton('Confirm Date', self)
        layout.addWidget(confirm_button)
        confirm_button.clicked.connect(self.accept)
    
    def accept(self):
        selected_datetime = self.date_edit.dateTime()
        datetime_str = selected_datetime.toString('yyyy-MM-dd HH:mm:ss')
        #print(date)
        os.system(f'sudo date -s "{datetime_str}"')
        #print(f'Selected Date and Time: {datetime_str}')
        super().accept()  # Close the dialog
    #def getSelectedDate(self):
    #    return self.date_edit.dateTime().toString('yyyy-MM-dd HH:mm:ss')

class ClickableLabel(QLabel):
    clicked = pyqtSignal()  # Define a signal named 'clicked'
    
    def __init__(self, *args, **kwargs):
        super(ClickableLabel, self).__init__(*args, **kwargs)
        self.setMouseTracking(True)
    
    def enterEvent(self, event):
        #Change text color when mouse enters the label
        self.setStyleSheet("color: lightgray;")
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        # Revert text color when mouse leaves the label
        self.setStyleSheet("color: black;")
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        self.clicked.emit()  # Emit the 'clicked' signal

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

        
        
        
        # Starting X positions for normal and shadow text
        #x_normal = round((self.width() - (normalTextSize.width() + shadowTextSize.width())) / 2)
        #x_shadow = round(x_normal + normalTextSize.width())

        # Y position (vertical center)
        #y = round((self.height() + metrics.height()) / 2)

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
        # Provide a size hint that accounts for the font size and shadow offset
        metrics = QFontMetrics(self.font)
        textSize = metrics.size(Qt.TextSingleLine,  self.normalText + self.shadowText)
        # Add some extra space for the shadow offset and padding
        return QSize(self.fixed_total_width + 10, self.fixed_total_height + 10)
        #return QSize(80, 160)  # Width, Height (taller than before)


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
        self._bar_brush = QBrush(bar_color)
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
            p.setFont(QFont('Helvetica', self._fontSize, 75))
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
        p.setFont(QFont('Helvetica', self._fontSize, 75))

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

class MockLib8MosInd:
    def __init__(self):
        self.state = [0] * 8  # simulate 8 MOSFETs
        self.pwm = [0] * 8
        print("[MOCK] Initialized MockLib8MosInd")

    def set(self, stack, mosfet, value):
        self.state[mosfet] = value
        print(f"[MOCK] set(stack={stack}, mosfet={mosfet}, value={value})")

    def get(self, stack, mosfet):
        print(f"[MOCK] get(stack={stack}, mosfet={mosfet}) => {self.state[mosfet]}")
        return self.state[mosfet]

    def set_all(self, stack, value):
        val = 1 if value else 0
        self.state = [val] * 8
        print(f"[MOCK] set_all(stack={stack}, value={value})")

    def get_all(self, stack):
        result = sum((1 << i) if val else 0 for i, val in enumerate(self.state))
        print(f"[MOCK] get_all(stack={stack}) => {result}")
        return result

    def set_pwm(self, stack, mosfet, value):
        self.pwm[mosfet] = value
        print(f"[MOCK] set_pwm(stack={stack}, mosfet={mosfet}, value={value})")

    def get_pwm(self, stack, mosfet):
        print(f"[MOCK] get_pwm(stack={stack}, mosfet={mosfet}) => {self.pwm[mosfet]}")
        return self.pwm[mosfet]

class horizontalToggleSwitch(QCheckBox):

    _transparent_pen = QPen(Qt.transparent)
    _light_grey_pen = QPen(Qt.lightGray)
    _black_pen = QPen(Qt.black)

    def __init__(self, 
                 parent=None, 
                 bar_color=Qt.gray, 
                 checked_color="#00B0FF",
                 handle_color=Qt.white, 
                 h_scale=1.0,
                 v_scale=1.0,
                 fontSize=10):
             
        super().__init__(parent)
        
        # Save our properties on the object via self, so we can access them later
        # in the paintEvent.
        self._bar_brush = QBrush(bar_color)
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
        return QSize(100, 45)

    def hitButton(self, pos: QPoint):
        return self.contentsRect().contains(pos)

    def paintEvent(self, e: QPaintEvent):

        contRect = self.contentsRect()
        width =  contRect.width() * self._h_scale
        height = contRect.height() * self._v_scale
        #handleRadius = round(0.35 * height)

        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        p.setPen(self._transparent_pen)
        bar_height_ratio = 0.7  # Increase this to make the bar taller
        bar_width = width * 0.95  # Wider bar
        barRect = QRectF(0, 0, bar_width, bar_height_ratio * height)
        #barRect = QRectF(0, 0, width - handleRadius, 0.40 * height)
        barRect.moveCenter(contRect.center())
        rounding = barRect.height() / 2
        handleRadius = round(0.9 * barRect.height() / 2)

        # the handle will move along this line
        trailLength = contRect.width() - 2 * handleRadius
        xLeft = contRect.center().x() - (trailLength + handleRadius)/2 
        #xPos = xLeft + handleRadius + trailLength * self._handle_position
        xPos = barRect.left() + handleRadius + (barRect.width() - 2 * handleRadius) * self._handle_position

        if self.isChecked():
            p.setBrush(self._bar_checked_brush)
            p.drawRoundedRect(barRect, rounding, rounding)
            p.setBrush(self._handle_checked_brush)

            p.setPen(self._black_pen)
            p.setFont(QFont('Helvetica', self._fontSize, 75))
            p.drawText(contRect.center(),"ON")

        else:
            p.setBrush(self._bar_brush)
            p.drawRoundedRect(barRect, rounding, rounding)
            p.setPen(self._light_grey_pen)
            p.setBrush(self._handle_brush)

        p.setPen(self._light_grey_pen)
        p.drawEllipse(
            QPointF(xPos, barRect.center().y()),
            handleRadius, handleRadius)

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