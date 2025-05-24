from electrophstat.gui.dialogs import SettingsDialog


def init_settings(self):

    self.settings_dialog =  SettingsDialog(self)
    self.actionSettings.triggered.connect(self.openSettingsDialog)

def openSettingsDialog(self):
    self.settings_dialog.exec_()