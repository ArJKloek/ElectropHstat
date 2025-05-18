import os, sys
from PyQt5 import uic, QtWidgets, QtCore
from PyQt5.QtWidgets import QAction
from electrophstat.gui.widgets import (
        ToggleSwitch,
        PowerButton,
        CustomTextWidget,
        Round3DButton
        )

# adjust this to point at your .ui file
UI_PATH = os.path.join(
    os.path.dirname(__file__),
    "electrophstat", "gui", "main_window.ui"
)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    # 1️⃣ Read the header of the .ui to pick the right base class
    with open(UI_PATH, "r", encoding="utf-8") as f:
        header = f.read(200)
    if 'class="QMainWindow"' in header:
        window = QtWidgets.QMainWindow()
    else:
        window = QtWidgets.QWidget()

    # 3️⃣ Load the .ui into that window
    uic.loadUi(UI_PATH, window)

    # 4️⃣ Dump out all child widgets so you can inspect their objectNames
    print("\nAll widget children:")
    for w in window.findChildren(QtWidgets.QWidget):
        print(f"  • {w.objectName():<20s} ({w.__class__.__name__})")

    print("\nAll widget children (name : class):")
    for w in window.findChildren(QtWidgets.QWidget):
        print(f"  • {w.objectName():<25s} : {w.__class__.__name__}")


    # 5️⃣ Check for some keys you know you named
    for name in ("pHNumber", "pHlabel", "RTDlabel", "voltagelabel", 
                 "currentlabel", "modelabel", "voltageDial", "currentDial", 
                 "voltageDiallabel", "currentDiallabel","modeToggle", "setButton",
                  "powerButton","usb_button","pHstatLabel", "pumpLabel", 
                   "keepSelector", "phSpin","tabWidget" ,"startbutton",
                     "stopbutton", "resetbutton"):
        found = window.findChild(QtCore.QObject, name)
        print(f"{name:15s} →", "FOUND" if found else "MISSING")


    expected_actions = [
        "actionFullscreen",
        "reconnect_pps_action",
        "actionExit",
        "datewindow",
        "actionCalibrate_Pump",
        "actionCalibrate_pH",
        "option1",
    ]

    print("\nChecking menu actions:")
    for name in expected_actions:
        act = window.findChild(QAction, name)
        print(f"  • {name:20s} →", "FOUND" if act else "MISSING")


    # 6️⃣ Show the window so you can visually confirm
    window.show()
    sys.exit(app.exec_())
