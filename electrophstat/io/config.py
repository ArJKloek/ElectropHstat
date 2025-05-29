from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, Union

class Config:
    def __init__(self, path: Union[str, Path, None], defaults: Dict[str, Any]):
        if path is not None:
            super().__setattr__('path', Path(path))
        else:
            super().__setattr__('path', None)
        super().__setattr__('defaults', defaults.copy())
        super().__setattr__('_data', {})  # only explicit overrides
        if path is not None:
            self.load()

    def load(self) -> None:
        """Read disk (if exists) and merge over defaults. Prints errors if parse fails."""
        if self.path is None or not self.path.exists():
            print(f"Config file not found at {self.path}, using defaults.")
            return
        try:
            text = self.path.read_text()
            obj  = json.loads(text)
            if isinstance(obj, dict):
                # Only merge explicit file keys
                self._data.update(obj)
        except Exception as e:
            print(f"Error loading config from {self.path}: {e}")
        
    def save(self) -> None:
        # Skip writing when _data is empty or path is None
        if self.path is None or not self._data:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._data, indent=2))

    def __getitem__(self, key: str) -> Any:
        value = self._data[key] if key in self._data else self.defaults.get(key)
        if isinstance(value, dict):
            # Wrap nested dicts as Config for dot notation
            return Config(None, value)
        return value

    def __setitem__(self, key: str, value: Any) -> None:
        self._data[key] = value
        self.save()

    def __getattr__(self, name: str) -> Any:
        if name in self._data:
            value = self._data[name]
        elif name in self.defaults:
            value = self.defaults[name]
        else:
            raise AttributeError(f"{type(self).__name__!r} has no attribute {name!r}")
        if isinstance(value, dict):
            return Config(None, value)
        return value

    def __setattr__(self, name: str, value: Any) -> None:
        if name in ('path', 'defaults', '_data'):
            super().__setattr__(name, value)
        else:
            self._data[name] = value
            self.save()

    def items(self):
        # Allow iteration like a dict
        keys = set(self.defaults) | set(self._data)
        for key in keys:
            yield key, self[key]

    def keys(self):
        return set(self.defaults) | set(self._data)

    def values(self):
        for key in self.keys():
            yield self[key]

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default