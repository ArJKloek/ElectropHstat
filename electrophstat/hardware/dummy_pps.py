# electrophstat/hardware/dummy_pps.py
from __future__ import annotations
import random
from .interfaces import PowerSupply


class DummyPPS(PowerSupply):
    """Fake supply for tests – accepts every call and returns plausible numbers."""
    VMAX  = 30.0      # volts
    IMAX  = 3.0       # amps
    VMIN  = 0.0
    MODEL = "DummyPPS v1"

    port = None

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
        base_v = getattr(self, "_volts", 12.0)
        base_a = getattr(self, "_amps", 1.5)
        mode = "CV"
        return base_v + random.uniform(-0.02, 0.02), base_a + random.uniform(-0.01, 0.01), mode
