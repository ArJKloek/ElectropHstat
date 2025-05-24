# electrophstat/gui/psu_setup.py

from electrophstat.connections.pps_connections import PPSConnections
from electrophstat.gui.pps_controller import PPSController

def init_psu(win):
    """
    Wire up or tear down the PSU subsystem based on window.enable_psu.
    Expects window to have:
      - enable_psu (bool)
      - logging_ctrl (LoggingCtrl)
      - UI elements: PowerGroup, togglePsuButton, actionEnable_PSU_control, reconnect_pps_action
    """
    if win.enable_psu:
        # instantiate hardware & controller
        win.pps_connections = PPSConnections(win)
        win.pps_ctrl = PPSController(
            win,
            win.pps_connections,
            interval=1.0,
            reset=True
        )
        # show & enable all PSU UI
        win.PowerGroup.setVisible(True)
        win.togglePsuButton.setEnabled(True)
        win.actionEnable_PSU_control.setEnabled(True)
        win.reconnect_pps_action.setEnabled(True)
    else:
        # tear it all down
        win.pps_connections = None
        win.pps_ctrl = None
        win.PowerGroup.setVisible(False)
        win.togglePsuButton.setChecked(False)
        win.togglePsuButton.setEnabled(False)
        win.actionEnable_PSU_control.setChecked(False)
        win.actionEnable_PSU_control.setEnabled(False)
        win.reconnect_pps_action.setEnabled(False)
        # disable PSU logging
        win.logging_ctrl.disable_logging(['voltage', 'current', 'coulomb'])
