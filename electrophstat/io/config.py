from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, Union


class Section:
    """
    Wraps a nested dict to support attribute-style get/set,
    writing changes back into the parent dict.
    """
    def __init__(self, data: dict, parent: dict, key: str):
        # Keep references to the nested data and its parent
        super().__setattr__('_data', data)
        super().__setattr__('_parent', parent)
        super().__setattr__('_key', key)
        # Wrap deeper dicts recursively
        for k, v in data.items():
            if isinstance(v, dict):
                v = Section(v, data, k)
            setattr(self, k, v)

    def __setattr__(self, name: str, value: Any):
        # Update the nested dict
        self._data[name] = value
        # Propagate update to parent dict
        self._parent[self._key] = self._data

    def __getitem__(self, name: str) -> Any:
        return getattr(self, name)


class Config:
    """
    A JSON-backed config with:
      • built-in defaults
      • load() merges file + defaults
      • save() writes out current state
      • dict-style access (cfg['foo'])
      • attribute-style access (cfg.foo)
      • nested dicts support cfg.foo.bar access
    """
    def __init__(self,
                 path: Union[str, Path],
                 defaults: Dict[str, Any]):
        # store path and defaults
        super(Config, self).__setattr__('path', Path(path))
        super(Config, self).__setattr__('defaults', defaults.copy())
        # internal data store
        super(Config, self).__setattr__('_data', defaults.copy())
        self.load()

    def load(self) -> None:
        """Read disk (if exists) and merge over defaults."""
        if not self.path.exists():
            return
        try:
            obj = json.loads(self.path.read_text())
            if isinstance(obj, dict):
                self._data.update(obj)
        except Exception:
            # Optional: log warning
            pass

    def save(self) -> None:
        """Write the current config dict to disk."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._data, indent=2))

    def __getitem__(self, key: str) -> Any:
        return self._wrap(self._data.get(key, self.defaults.get(key)))

    def __setitem__(self, key: str, value: Any) -> None:
        self._data[key] = value
        self.save()

    def __getattr__(self, name: str) -> Any:
        # 1) Check loaded data
        if name in self._data:
            val = self._data[name]
            if isinstance(val, dict):
                return Section(val, self._data, name)
            return val
        # 2) Fallback to defaults
        if name in self.defaults:
            val = self.defaults[name]
            if isinstance(val, dict):
                return Section(val, self._data, name)
            return val
        # 3) Not found
        raise AttributeError(f"{type(self).__name__!r} has no attribute {name!r}")

    def __setattr__(self, name: str, value: Any) -> None:
        if name in ('path', 'defaults', '_data'):
            super(Config, self).__setattr__(name, value)
        else:
            self._data[name] = value
            self.save()

    @staticmethod
    def _wrap(value: Any) -> Any:
        """
        Wrap dicts in Section, leave other types unchanged.
        """
        if isinstance(value, dict):
            # Should not normally be called here for nested dicts,
            # but kept for safety.
            return Section(value, {}, '')
        return value
