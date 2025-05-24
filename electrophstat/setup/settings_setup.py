from electrophstat.gui.dialogs import SettingsDialog


def init_settings(win):

    win.settings_dialog =  SettingsDialog(win)
    win.actionSettings.triggered.connect(win.openSettingsDialog)

def openSettingsDialog(self):
    self.win.settings_dialog.exec_()