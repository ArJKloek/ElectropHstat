
from electrophstat.gui.logging_controller import LoggingController
from electrophstat.io.logger import Logger
from electrophstat.connections.main_connections import find_data_directory


def init_logger(main):
    LOG_BASE  = find_data_directory()       # ...\GitHub\ElectroPHstat\ElectroPHData
        #LOG_BASE=Path.home()/"ElectroPHData",
        
    main.logger = Logger(
        base_dir=LOG_BASE,
        labels=["pump","pH", "temperature","voltage","current", "coulomb"],
        column_names = ["Pumped (ml)", "pH", "Temperature (°C)", "Voltage (V)", "Current (A)", "Coulomb (C)"]

    )
    main.logging_ctrl = LoggingController(main, interval=5.0)
    main.logging_ctrl.active_labels = set(main.logger.labels)
