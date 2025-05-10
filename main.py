import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QStyleFactory
from scripts.pHstat_GUI import MainWindow

def main():
    app = QApplication(sys.argv)
    #print("Available styles:", QStyleFactory.keys())
    app.setStyle(QStyleFactory.create("Fusion"))  # ✅ This line forces a style that respects stylesheets
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()