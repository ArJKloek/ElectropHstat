# electrophstat/gui/connections.py
from PyQt5.QtCore    import pyqtSlot
from PyQt5.QtWidgets import QAction, QActionGroup

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

    
    
    