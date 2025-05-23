import json
from pathlib import Path
from typing import Any, Dict, Union


class Section:
    """
    Wraps a nested dict to support attribute-style get/set,
    writing changes back into the parent dict and auto-saving.
    """
    def __init__(self, data: dict, parent: dict, key: str, config: 'Config'):
        # store references
        super(Section, self).__setattr__('_data', data)
        super(Section, self).__setattr__('_parent', parent)
        super(Section, self).__setattr__('_key', key)
        super(Section, self).__setattr__('_config', config)
        # wrap nested dicts
        for k, v in data.items():
            if isinstance(v, dict):
                v = Section(v, data, k, config)
            super(Section, self).__setattr__(k, v)

    def __setattr__(self, name: str, value: Any):
        # update nested data
        self._data[name] = value
        # propagate to parent dict
        self._parent[self._key] = self._data
        # save config
        self._config.save()
        # set as attribute
        super(Section, self).__setattr__(name, value)

    def __getitem__(self, name: str) -> Any:
        return getattr(self, name)


class Config:
    """
    JSON-backed config with nested attribute access via Section.
    """
    def __init__(self,
                 path: Union[str, Path],
                 defaults: Dict[str, Any]):
        super(Config, self).__setattr__('_path', Path(path))
        super(Config, self).__setattr__('_defaults', defaults.copy())
        super(Config, self).__setattr__('_data', defaults.copy())
        self.load()

    def load(self) -> None:
        # merge on-disk over defaults
        if self._path.exists():
            try:
                obj = json.loads(self._path.read_text())
                if isinstance(obj, dict):
                    self._data.update(obj)
            except Exception:
                pass

    def save(self) -> None:
        # write current data to disk
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(self._data, indent=2))

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

    def __setitem__(self, key: str, value: Any) -> None:
        setattr(self, key, value)

    def __getattr__(self, name: str) -> Any:
        # 1) data store
        if name in self._data:
            val = self._data[name]
            if isinstance(val, dict):
                section = Section(val, self._data, name, self)
                super(Config, self).__setattr__(name, section)
                return section
            return val
        # 2) defaults
        if name in self._defaults:
            val = self._defaults[name]
            if isinstance(val, dict):
                # create nested dict in _data if not exist
                nested = self._data.setdefault(name, val.copy())
                section = Section(nested, self._data, name, self)
                super(Config, self).__setattr__(name, section)
                return section
            return val
        # not found
        raise AttributeError(f"Config has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        # internal attributes
        if name in ('_path', '_defaults', '_data'):
            super(Config, self).__setattr__(name, value)
            return
        # simple value or Section
        self._data[name] = value
        super(Config, self).__setattr__(name, value)
        self.save()