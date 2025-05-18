from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QDateTimeEdit, QPushButton, 
                            QHBoxLayout, QLabel, QDoubleSpinBox, QLineEdit, QHBoxLayout)
from PyQt5.QtCore import Qt, QDateTime, pyqtSignal, QTimer
from PyQt5.QtGui import QCursor
import os

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
