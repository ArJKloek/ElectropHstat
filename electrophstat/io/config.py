from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, Union

class Config:
    def __init__(self, path: Union[str, Path, None], defaults: Dict[str, Any], parent=None, parent_key=None):
        if path is not None:
            super().__setattr__('path', Path(path))
        else:
            super().__setattr__('path', None)
        super().__setattr__('defaults', defaults.copy())
        super().__setattr__('_data', {})
        super().__setattr__('_parent', parent)
        super().__setattr__('_parent_key', parent_key)
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
            return Config(None, value, parent=self, parent_key=key)
        return value

    def __setitem__(self, key: str, value: Any) -> None:
        self._data[key] = value
        self._bubble_save()

    def __getattr__(self, name: str) -> Any:
        if name in self._data:
            value = self._data[name]
        elif name in self.defaults:
            value = self.defaults[name]
        else:
            raise AttributeError(f"{type(self).__name__!r} has no attribute {name!r}")
        if isinstance(value, dict):
            return Config(None, value, parent=self, parent_key=name)
        return value

    def __setattr__(self, name: str, value: Any) -> None:
        if name in ('path', 'defaults', '_data', '_parent', '_parent_key'):
            super().__setattr__(name, value)
        else:
            self._data[name] = value
            self._bubble_save()

    def _bubble_save(self):
        # Propagate changes up to the root config and save
        if self._parent is not None and self._parent_key is not None:
            # Update parent with our current state
            self._parent._data[self._parent_key] = self._asdict()
            self._parent._bubble_save()
        else:
            self.save()

    def _asdict(self):
        # Recursively convert to dict for saving
        result = self.defaults.copy()
        result.update(self._data)
        for k, v in result.items():
            if isinstance(v, Config):
                result[k] = v._asdict()
        return result

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