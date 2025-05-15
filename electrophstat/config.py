# electrophstat/config.py
import json
from pathlib import Path

DEFAULT_CONFIG = {
    "target_pH": 7.00,
    "hysteresis": 0.05,
    "pump_volume_per_pH": 0.1,  # mL per pH unit
}


def load_settings(path: Path) -> dict:
    """
    Load JSON settings. Returns DEFAULT_CONFIG if file missing or invalid.
    """
    if not path.exists():
        return DEFAULT_CONFIG.copy()
    try:
        with path.open() as f:
            data = json.load(f)
        return {**DEFAULT_CONFIG, **data}
    except Exception:
        return DEFAULT_CONFIG.copy()


def save_settings(settings: dict, path: Path) -> None:
    """
    Write JSON settings to disk.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(settings, f, indent=2)