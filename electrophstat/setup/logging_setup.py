
from electrophstat.gui.logging_controller import LoggingController
from electrophstat.io.logger import Logger
from electrophstat.connections.main_connections import find_data_directory


def init_logger(win):
    LOG_BASE  = find_data_directory()       # ...\GitHub\ElectroPHstat\ElectroPHData
        #LOG_BASE=Path.home()/"ElectroPHData",
        
    win.logger = Logger(
        base_dir=LOG_BASE,
        labels=["pump","pH", "temperature","voltage","current", "coulomb", "turbidity"],
        column_names = ["Pumped (ml)", "pH", "Temperature (°C)", "Voltage (V)", "Current (A)", "Coulomb (C)", "Turbidity"]

    )
    win.logging_ctrl = LoggingController(win, interval=5.0)
    win.logging_ctrl.active_labels = set(win.logger.labels)
