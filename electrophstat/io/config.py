from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict

class Config:
    """
    A JSON‐backed config with:
      • built-in defaults
      • load() merges file + defaults
      • save() writes out current state
      • dict-style access (cfg['foo'])
      • attribute-style access (cfg.foo)
    """
    def __init__(self,
                 path: str | Path,
                 defaults: Dict[str, Any]):
        self.path     = Path(path)
        self.defaults = defaults.copy()
        self._data    = {}#defaults.copy()
        self.load()

    def load(self) -> None:
        """Read disk (if exists) and merge over defaults."""
        if not self.path.exists():
            return
        try:
            text = self.path.read_text()
            obj  = json.loads(text)
            if isinstance(obj, dict):
                self._data.update(obj)
        except Exception:
            # you might log a warning here
            pass

    def save(self) -> None:
        """Dump the current dict to disk (overwriting)."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._data, indent=2))

    # dict‐style
    def __getitem__(self, key: str) -> Any:
        return self._data.get(key, self.defaults.get(key))

    def __setitem__(self, key: str, value: Any) -> None:
        self._data[key] = value
        self.save()

    # attribute‐style
    def __getattr__(self, name: str) -> Any:
        if name in self._data:
            return self._data[name]
        raise AttributeError(f"{type(self).__name__!r} has no attribute {name!r}")

    def __setattr__(self, name: str, value: Any) -> None:
        # redirect real properties to super, otherwise treat as config key
        if name in ("path", "defaults", "_data"):
            super().__setattr__(name, value)
        else:
            self._data[name] = value
            self.save()