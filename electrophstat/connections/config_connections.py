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
        "pHstat": {
            "enable": True,
            "target": 7.00,
            "mode": 0,
            "pump": {
                "volume": 0.0,
                "cycle": 1.0,
                "cooldown": 0.0
            }
        },
        "psu": {
            "enable": True
        },
        "debug_mode": True,
        "atlas": {
            "pH": {
                "enable": True,
                "address": "0x63",
                "name": "pH",
                "calibration": {
                    "low": 4.00,
                    "mid": 7.00,
                    "high": 10.00
                }
            },
            "RTD": {
                "enable": True,
                "address": "0x66",
                "name": "RTD"
            }
        },
        "sensors": {
            "turbidity": {
                "enable": True,
                "model": {
                    "PercentFast": 9.1,
                    "KFast": 0.002,
                    "KSlow": 0.00023
                },
                "calibration": {
                    "NTU": {
                        "low": 1000,
                        "mid": 2000,
                        "high": 4000
                    },
                    "mV": {
                        "zero": 4800,
                        "low": 3350,
                        "mid": 2600,
                        "high": 1650,
                        "inf": 30
                    }
                }
            }
        }
    }

    # 2) instantiate & merge any on‐disk overrides
    self.config = Config(cfg_path, DEFAULT_CONFIG)
    # 3) pull them into window attributes
    self.pHstat_mode                    = int(self.config.pHstat.mode)
    self.pH_target                      = float(self.config.pHstat.target)
    self.pump_volume_per_cycle_ml       = float(self.config.pHstat.pump.volume)
    self.pump_cycle_duration_s          = float(self.config.pHstat.pump.cycle)
    self.pump_cooldown_duration_s       = float(self.config.pHstat.pump.cooldown)
    self.pH_calibration_low             = float(self.config.atlas.pH.calibration.low)
    self.pH_calibration_mid             = float(self.config.atlas.pH.calibration.mid)
    self.pH_calibration_high            = float(self.config.atlas.pH.calibration.high)
    self.enable_psu                     = bool(self.config.psu.enable)
    self.enable_phstat                  = bool(self.config.pHstat.enable)
    self.enable_turbidity_sensor        = bool(self.config.sensors.turbidity.enable)
    self.debug_mode                     = bool(self.config.debug_mode)

    # Assuming cfg is your Config instance and supports dict access
    # ...and so on
    # 4) hook UI elements → config so that any user change persists
    #self.keepSelector.currentIndexChanged.connect(self._on_mode_change)
    #self.phSpin.valueChanged.connect(self._on_target_pH_change)
    # …and similarly for any other controls you want to persist…
