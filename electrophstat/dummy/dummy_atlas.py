from __future__ import annotations
import random
from typing import Optional

from ..hardware.interfaces import AtlasSensor


class DummyAtlas(AtlasSensor):
    """
    Fake Atlas I²C sensor.
    • `read()` returns a value that slowly wanders ±2 %.
    • `.calibrate(mode, value)` actually stores low/mid/high.
    • `.clear_cal()` resets stored calibration.
    """
    def __init__(self, address: int = 0x63, kind: str = "pH"):
        self.address = address
        self.kind = kind
        # “true” underlying value
        self._value = 7.00 if kind == "pH" else 25.0

        # store calibration points
        self._cal = {
            "low":  None,
            "mid":  None,
            "high": None
        }

    # life-cycle ---------------------------------------------------
    def connect(self) -> None:         pass
    def disconnect(self) -> None:      pass
    @property
    def connected(self) -> bool:       return True

    # measurement --------------------------------------------------
    def read(self) -> float:
        # wander around whichever calibration point is “active”
        base = self._value
        jitter = 1 + random.uniform(-0.02, 0.02)    # ±2 %
        self._value = base * jitter
        return round(self._value, 3)

    # helpers ------------------------------------------------------
    def set_temp_comp(self, celsius: float) -> None:  pass

    def clear_cal(self) -> None:
        """Clear all stored calibration references."""
        for k in self._cal:
            self._cal[k] = None
        # reset reading value to neutral
        self._value = 7.00 if self.kind == "pH" else 0.0

    def calibrate(self, mode: str, value: float) -> None:
        """
        Simulate a calibration command:
          • mode: "low", "mid", or "high"
          • value: the pH (or other) reference point
        """
        if mode not in ("low", "mid", "high"):
            raise ValueError(f"DummyAtlas: invalid calibrate mode {mode!r}")
        # store the reference
        self._cal[mode] = float(value)
        # jump _value to that reference so read() begins there
        self._value = float(value)
