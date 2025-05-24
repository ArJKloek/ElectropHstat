from pathlib import Path
from PyQt5.QtCore import pyqtSlot
from electrophstat.io.config import Config

def init_config(self):
    """Load JSON settings, apply to attrs, and hook up UI → config slots."""
    # 1) define where the JSON lives & what the defaults are
    HERE      = Path(__file__).resolve()
    REPO_ROOT = HERE.parents[2]     # .../GitHub/ElectroPHstat
    #LOG_BASE  = REPO_ROOT / "ElectroPHData"
    
    cfg_path = REPO_ROOT / "settings.json"
    DEFAULT_CONFIG = {
        "pHstat_mode":           0,
        "pH_target":                 7.00,
        "pump_volume_per_cycle_ml":  0.0,
        "pump_cycle_duration_s":     1.0,
        "pump_cooldown_duration_s":  0.0,
        "pH_calibration_low":        4.00,
        "pH_calibration_mid":        7.00,
        "pH_calibration_high":       10.00,
        "reference_file_path":       "",
        "enable_psu":               True,
        "enable_ph":                True,
        "enable_temp":              True,
        "enable_turbidity":         True
    }

    # 2) instantiate & merge any on‐disk overrides
    self.config = Config(cfg_path, DEFAULT_CONFIG)

    # 3) pull them into window attributes
    self.pHstat_mode                    = int(self.config.pHstat_mode)
    self.pH_target                      = float(self.config.pH_target)
    self.pump_volume_per_cycle_ml       = float(self.config.pump_volume_per_cycle_ml)
    self.pump_cycle_duration_s          = float(self.config.pump_cycle_duration_s)
    self.pump_cooldown_duration_s       = float(self.config.pump_cooldown_duration_s)
    self.pH_calibration_low             = float(self.config.pH_calibration_low)
    self.pH_calibration_mid             = float(self.config.pH_calibration_mid)
    self.pH_calibration_high            = float(self.config.pH_calibration_high)
    self.Ref_path                       = self.config.reference_file_path
    self.enable_psu                     = bool(self.config.enable_psu)
    self.enable_phstat                 = bool(self.config.enable_phstat)
    # 4) hook UI elements → config so that any user change persists
    #self.keepSelector.currentIndexChanged.connect(self._on_mode_change)
    #self.phSpin.valueChanged.connect(self._on_target_pH_change)
    # …and similarly for any other controls you want to persist…

@pyqtSlot(int)
def _on_mode_change(self, idx: int):
    self.pHstat_mode = idx
    self.config.pHstat_mode = idx  # auto‐saves

@pyqtSlot(float)
def _on_target_pH_change(self, val: float):
    self.pH_target = val
    self.config.pH_target = val       # auto‐saves