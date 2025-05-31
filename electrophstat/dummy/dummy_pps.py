# electrophstat/hardware/dummy_pps.py
from __future__ import annotations
import math
import random
from ..hardware.interfaces import PowerSupply


class DummyPPS(PowerSupply):
    """Fake supply for tests – accepts every call and returns plausible numbers."""
    VMAX  = 30.0      # volts
    IMAX  = 16.5      # amps
    VMIN  = 0.0
    MODEL = "DummyPPS v1"

    port = None

    def __init__(self):
        self._t = 0.0
        self._volts = 12.0
        self._amps = 1.5
        self._on = True

    # life-cycle
    def connect(self):     pass
    def disconnect(self):  pass
    @property
    def connected(self):   return True

    # control
    def voltage(self, volts): self._volts = volts
    def current(self, amps):  self._amps = amps
    def output(self, enable): self._on = enable

    # monitor
    def read_output(self):
        # 3-hour period = 10,800 seconds
        self._t += 1.0
        period = 10800
        # Voltage oscillates between 10 and 14 V
        base_v = 12.0 + 2.0 * math.sin(2 * math.pi * (self._t / period))
        # Current oscillates between 1 and 2 A
        base_a = 1.5 + 0.5 * math.sin(2 * math.pi * (self._t / period))
        mode = "CV"
        v = base_v + random.uniform(-0.05, 0.05)
        a = base_a + random.uniform(-0.01, 0.01)
        return v, a, mode
