from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, Union

class Config:
    """
    A JSON-backed config with:
      • built-in defaults
      • load() merges file + defaults
      • save() writes out current state
      • dict-style access (cfg['foo'])
      • attribute-style access (cfg.foo)
    """
    def __init__(self,
                 path: Union[str, Path],
                 defaults: Dict[str, Any]):
        # store path and defaults
        super().__setattr__('path', Path(path))
        super().__setattr__('defaults', defaults.copy())
        super().__setattr__('_data', defaults.copy())
        self.load()

    def load(self) -> None:
        """Read disk (if exists) and merge over defaults."""
        print(f"Loading config from {self.path}")
        if not self.path.exists():
            print("No config file; using defaults.")
            return
        try:
            text = self.path.read_text()
            print(f"Config file contents:\n{text}")
            obj = json.loads(text)
            if isinstance(obj, dict):
                # Merge disk values over defaults
                for k, v in obj.items():
                    print(f"Overriding default: {k}={v}")
                    self._data[k] = v
        except Exception as e:
            print(f"Failed to load config: {e}")

    def save(self) -> None:
        """Dump the current dict to disk (overwriting)."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(self._data, indent=2)
        print(f"Saving config to {self.path}:\n{text}")
        self.path.write_text(text)

    # dict-style
    def __getitem__(self, key: str) -> Any:
        return self._data.get(key, self.defaults.get(key))

    def __setitem__(self, key: str, value: Any) -> None:
        self._data[key] = value
        self.save()

    # attribute-style
    def __getattr__(self, name: str) -> Any:
        # 1) check on-disk or overrides
        if name in self._data:
            return self._data[name]
        # 2) fallback to defaults
        if name in self.defaults:
            return self.defaults[name]
        raise AttributeError(f"{type(self).__name__!r} has no attribute {name!r}")

    def __setattr__(self, name: str, value: Any) -> None:
        # redirect real properties to super, otherwise treat as config key
        if name in ("path", "defaults", "_data"):
            super().__setattr__(name, value)
        else:
            print(f"Setting config[{name}] = {value}")
            self._data[name] = value
            self.save()