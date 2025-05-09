from PyQt5.QtWidgets import QDialog, QVBoxLayout, QDateTimeEdit, QPushButton
from PyQt5.QtCore import QDateTime
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
