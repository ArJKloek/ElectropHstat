from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, Union

class Config:
    """
    JSON-backed config that only persists explicit changes.
    """
    def __init__(self, path, defaults):
        super().__setattr__('_path', Path(path))
        super().__setattr__('_defaults', defaults.copy())
        # _data holds ONLY loaded or set values, never defaults
        super().__setattr__('_data', {})
        self.load()

    def load(self):
        if not self._path.exists():
            return
        try:
            obj = json.loads(self._path.read_text())
            if isinstance(obj, dict):
                # Only load what's in JSON, not defaults
                self._data.update(obj)
        except Exception:
            pass

    def save(self):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        # Only write explicit overrides
        self._path.write_text(json.dumps(self._data, indent=2))

    def __getitem__(self, key):
        if key in self._data:
            return self._data[key]
        return self._defaults.get(key)

    def __setitem__(self, key, value):
        self._data[key] = value
        self.save()

    def __getattr__(self, name):
        if name in self._data:
            return self._data[name]
        if name in self._defaults:
            return self._defaults[name]
        raise AttributeError(f"No attribute {name!r}")

    def __setattr__(self, name, value):
        # avoid clobbering internal attrs
        if name in ('_path', '_defaults', '_data'):
            super().__setattr__(name, value)
        else:
            self._data[name] = value
            self.save()