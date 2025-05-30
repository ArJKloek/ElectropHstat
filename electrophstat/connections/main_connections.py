# electrophstat/gui/connections.py
from PyQt5.QtCore    import pyqtSlot
from PyQt5.QtWidgets import QAction, QActionGroup
import platform, os
from pathlib import Path

def is_raspberry_pi() -> bool:
    """
    Return True if we appear to be running on a Raspberry Pi.
    Checks:
      1) Linux OS
      2) ARM CPU
      3) /proc/device-tree/model contains “Raspberry Pi”
    """
    if platform.system() != "Linux":
        return False

    # Most Pis report an 'arm' machine type
    if not platform.machine().startswith("arm"):
        return False

    model_path = Path("/proc/device-tree/model")
    if model_path.exists():
        try:
            content = model_path.read_text(errors="ignore")
            return "Raspberry Pi" in content
        except Exception:
            return False

    return False


def setup_mainwindow_signals(win):

    #Connect exit to the close
    win.actionExit.triggered.connect(win.close) 

    # 1) Create an exclusive group tied to the window
    lg = QActionGroup(win)
    lg.setExclusive(True)

    # 2) Grab each QAction by the objectName you set in Designer
    for act_name in (
        "action5_sec",
        "action30_sec",
        "action1_min",
        "action5_min",
    ):
        act: QAction = getattr(win, act_name, None)
        if not act:
            raise RuntimeError(f"Missing QAction {act_name} in UI!")
        act.setCheckable(True)   # make it checkable
        lg.addAction(act)        # add it to the exclusive group

    # Map interval to QAction name
    interval_to_action = {
        5: "action5_sec",
        30: "action30_sec",
        60: "action1_min",
        300: "action5_min"
    }
    interval = getattr(win.config.logger, "interval", 30)
    action_name = interval_to_action.get(interval, "action30_sec")
    action = getattr(win, action_name, None)
    if action:
        action.setChecked(True)
    else:
        win.action30_sec.setChecked(True)

    # 4) Connect the group's triggered signal back to the window's slot
    lg.triggered.connect(win.button_cont.on_log_option_changed)
    
def find_data_directory() -> Path:
    """
    Choose a base directory for logs:
      • On Pi: ~/Desktop/Data
      • On Windows: ~/Data
      • Otherwise (e.g. macOS/Linux dev): <repo-root>/ElectroPHData
    """
    is_windows = platform.system() == "Windows"
    is_rpi     = is_raspberry_pi()
    print(f"Windows {is_windows} and RPI {is_rpi}")

    if is_rpi:
        log_base = Path.home() / "Desktop" / "Data"
    elif is_windows:
        log_base = Path.home() / "Data"
    else:
        here      = Path(__file__).resolve()
        repo_root = here.parents[2]      # adjust if your layout differs
        log_base  = repo_root / "ElectroPHData"

    log_base.mkdir(parents=True, exist_ok=True)
    return log_base
