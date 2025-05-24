from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, Union

class Config:
    def __init__(self, path: Union[str, Path], defaults: Dict[str, Any]):
        super().__setattr__('path', Path(path))
        super().__setattr__('defaults', defaults.copy())
        super().__setattr__('_data', {})  # only explicit overrides
        self.load()

    def load(self) -> None:
        """Read disk (if exists) and merge over defaults. Prints errors if parse fails."""
        if not self.path.exists():
            print(f"Config file not found at {self.path}, using defaults.")
            return
        try:
            text = self.path.read_text()
            obj  = json.loads(text)
            if isinstance(obj, dict):
                # Only merge explicit file keys
                self._data.update(obj)
                print(f"Loaded config overrides: {obj}")
        except Exception as e:
            print(f"Error loading config from {self.path}: {e}")
        
    def save(self) -> None:
        # Skip writing when _data is empty
        if not self._data:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._data, indent=2))

    def __getitem__(self, key: str) -> Any:
        if key in self._data:
            return self._data[key]
        return self.defaults.get(key)

    def __setitem__(self, key: str, value: Any) -> None:
        self._data[key] = value
        self.save()

    def __getattr__(self, name: str) -> Any:
        if name in self._data:
            return self._data[name]
        if name in self.defaults:
            return self.defaults[name]
        raise AttributeError(f"{type(self).__name__!r} has no attribute {name!r}")

    def __setattr__(self, name: str, value: Any) -> None:
        if name in ('path', 'defaults', '_data'):
            super().__setattr__(name, value)
        else:
            self._data[name] = value
            self.save()