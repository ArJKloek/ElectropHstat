from __future__ import annotations
import random
from typing import Optional

from .interfaces import AtlasSensor


class DummyAtlas(AtlasSensor):
    """
    Fake Atlas I²C sensor.
    • `read()` returns a value that slowly wanders ±2 %.
    • All other methods are no-ops so GUI / control code can’t crash.
    """

    def __init__(self, address: int = 0x63, kind: str = "pH"):
        self.address = address
        self.kind = kind
        self._value = 7.00 if kind == "pH" else 0.0

    # life-cycle ---------------------------------------------------
    def connect(self) -> None:         pass
    def disconnect(self) -> None:      pass
    @property
    def connected(self) -> bool:       return True

    # measurement --------------------------------------------------
    def read(self) -> float:
        jitter = 1 + random.uniform(-0.02, 0.02)    # ±2 %
        self._value *= jitter
        return round(self._value, 3)

    # helpers ------------------------------------------------------
    def set_temp_comp(self, celsius: float) -> None:  pass
    def clear_cal(self) -> None:                      pass
    def calibrate(self, *_, **__) -> None:            pass
