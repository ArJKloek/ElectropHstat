from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict

DEFAULT_CONFIG: Dict[str, Any] = {
    "select": 0,
    "target_pH": 7.00,
}


def load_settings(config_path: str) -> Dict[str, Any]:
    path = Path(config_path)
    if not path.exists():
        return DEFAULT_CONFIG.copy()
    return json.loads(path.read_text())


def save_settings(config_path: str, settings: Dict[str, Any]) -> None:
    path = Path(config_path)
    path.write_text(json.dumps(settings, indent=2))