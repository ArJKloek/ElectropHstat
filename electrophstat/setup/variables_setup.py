
def init_variables(main):
        main.Ref_path = ''
        main.pH_target = 0.0
        main.pHstat_mode = 0
        main.pump_volume_per_cycle_ml = 0
        main.injections = 0
        main.pump_cycle_duration_s = 0
        main.valueData = {
            "pump":             0.0,
            "pH":               0.0,
            "RTD":              0.0,
            "voltage":          0.0,
            "current":          0.0,
            "coulomb":          0.0,
            "mode":             "",
            "turbidity":        0.0,
            "turbidity_raw":    0.0,
        }
        main.pump_cooldown_duration_s = 0
        main.currentActiveTabIndex = 0  # Track the current tab index
        main.graphTabs = []
        main.graphWidgets = []
        main.pH_calibration_low = 0.0
        main.pH_calibration_mid = 0.0
        main.pH_calibration_high = 0.0
        main.copy_path = ""
        main.viewBoxes = {}  # In __init__ or setupVariables()
        main.rightViewBoxes = {}
        main.PStype = [0,0,0,0]
        main.start = False
        main.pHSelectMode = 1 
        main.pumpDurationSeconds = 1
        main.enable_psu : bool
        main.enable_phstat : bool
        main.enable_ph_sensor : bool
        main.enable_temp_sensor : bool
        main.enable_turbidity_sensor : bool
        main.usb_present = False
        main.logs_present = False
        main.copy_path = ""
        main.psu_status = False
        main.phstat_status = False
        main.ph_sensor_status = False
        main.temp_sensor_status = False
        main.turbidity_sensor_status = False
        main.debug_mode = False
        