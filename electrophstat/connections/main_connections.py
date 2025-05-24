# electrophstat/gui/connections.py
from PyQt5.QtCore    import pyqtSlot
from PyQt5.QtWidgets import QAction, QActionGroup
import platform, os
from pathlib import Path

def setup_mainwindow_signals(win):

    #Connect exit to the close
    win.actionExit.triggered.connect(win.close) 

    # 1) Create an exclusive group tied to the window
    lg = QActionGroup(win)
    lg.setExclusive(True)

    # 2) Grab each QAction by the objectName you set in Designer
    for act_name in (
        "option1",
        "option2",
        "option3",
        "option4",
    ):
        act: QAction = getattr(win, act_name, None)
        if not act:
            raise RuntimeError(f"Missing QAction {act_name} in UI!")
        act.setCheckable(True)   # make it checkable
        lg.addAction(act)        # add it to the exclusive group

    # 3) Pick a default
    win.option2.setChecked(True)

    # 4) Connect the group's triggered signal back to the window's slot
    lg.triggered.connect(win.button_cont.on_log_option_changed)

    
def find_data_directory():
    # 1) figure out where we’re running
    is_windows = platform.system() == "Windows"
    is_rpi     = (platform.system() == "Linux"
                and Path("/home/pi").exists())
    print(f'Windows {is_windows} and RPI {is_rpi}')

    # 2) build your base‐dir accordingly
    if is_rpi:
        # on a Pi, put it on the Desktop/Data folder
        LOG_BASE = Path.home() / "Desktop" / "Data"
    else:
        # on Windows (or any non‐Pi), use the repo root
        HERE      = Path(__file__).resolve()
        REPO_ROOT = HERE.parents[2]     # .../GitHub/ElectroPHstat
        LOG_BASE  = REPO_ROOT / "ElectroPHData"

    # 3) make sure it exists
    LOG_BASE.mkdir(parents=True, exist_ok=True)

    return LOG_BASE   
    