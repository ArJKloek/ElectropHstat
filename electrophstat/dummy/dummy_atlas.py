from __future__ import annotations
import math
import random
from typing import Optional

from ..hardware.interfaces import AtlasSensor


class DummyAtlas(AtlasSensor):
    """
    Fake Atlas I²C sensor.
    • `read()` returns a value that slowly wanders ±2 % or follows a sine wave.
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
        self._t = 0.0  # time counter for sine wave

    # life-cycle ---------------------------------------------------
    def connect(self) -> None:         pass
    def disconnect(self) -> None:      pass
    @property
    def connected(self) -> bool:       return True

    # measurement --------------------------------------------------
    def read(self) -> float:
        # Sine wave: 3-hour period, amplitude 1, offset depends on kind
        self._t += 1.0  # increment time (simulate 1 second per call)
        period = 10800  # 3 hours in seconds
        if self.kind == "pH":
            base = 7.0 + 1.0 * math.sin(2 * math.pi * (self._t / period))  # pH oscillates 6-8
        else:
            base = 25.0 + 5.0 * math.sin(2 * math.pi * (self._t / period)) # temp oscillates 20-30
        noise = random.uniform(-0.02, 0.02) * base
        value = base + noise
        self._value = value
        return round(self._value, 3)

    # helpers ------------------------------------------------------
    def set_temp_comp(self, celsius: float) -> None:  pass

    def clear_cal(self) -> None:
        """Clear all stored calibration references."""
        for k in self._cal:
            self._cal[k] = None
        # reset reading value to neutral
        self._value = 7.00 if self.kind == "pH" else 0.0
        self._t = 0.0

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
