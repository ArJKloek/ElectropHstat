from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel, QPushButton, QWidget, QHBoxLayout
from PyQt5.QtCore import Qt

class CustomTitleBar(QWidget):
    def __init__(self, parent=None):
        super(CustomTitleBar, self).__init__(parent)
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.title_label = QLabel("Custom Title")
        self.title_label.setAlignment(Qt.AlignLeft)  # Align title to the left

        self.close_button = QPushButton("X")
        self.close_button.clicked.connect(self.on_close)

        self.layout.addWidget(self.title_label)
        self.layout.addWidget(self.close_button)
        self.setLayout(self.layout)

    def on_close(self):
        self.parent().close()

class CustomDialog(QDialog):
    def __init__(self, parent=None):
        super(CustomDialog, self).__init__(parent)
        self.setWindowTitle(" ")  # Set an empty title to hide the default title bar

        # Use custom window flags to remove the system title bar and frame but keep the dialog functional
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)

        self.main_layout = QVBoxLayout()
        self.title_bar = CustomTitleBar(self)
        self.main_layout.addWidget(self.title_bar)

        self.content_label = QLabel("Dialog Content Here")
        self.main_layout.addWidget(self.content_label)

        self.setLayout(self.main_layout)

if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    dialog = CustomDialog()
    dialog.show()
    sys.exit(app.exec_())
