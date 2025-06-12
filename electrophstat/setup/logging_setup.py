
from electrophstat.gui.logging_controller import LoggingController
from electrophstat.io.logger import Logger
from electrophstat.connections.main_connections import find_data_directory


def init_logger(win):
    LOG_BASE  = find_data_directory()       # ...\GitHub\ElectroPHstat\ElectroPHData
        #LOG_BASE=Path.home()/"ElectroPHData",
        
    win.logger = Logger(
        base_dir=LOG_BASE,
        #labels=["pump","pH", "RTD", "voltage", "current", "coulomb", "turbidity"],
        labels = win.config.logger.labels,
        column_names = win.config.logger.column_names
       
    )
    print(f"Logger initialized with labels: {win.config.logger.labels}")
    win.logging_ctrl = LoggingController(win, interval=win.config.logger.interval)
    win.logging_ctrl.active_labels = set(win.logger.labels)
