# electrophstat/hardware/voltcraft_pps.py
from __future__ import annotations
import serial
from .interfaces import PowerSupply
from electrophstat.vendor.pps import PPS
try:
    # Python ≥ 3.8
    from typing import Optional#, runtime_checkable
except ImportError:                 # Python 3.7 fallback
    from typing_extensions import Optional#, runtime_checkable

#try:
#    from typing import runtime_checkable
#except ImportError:           # Python 3.7 fallback
#    from typing_extensions import runtime_checkable
#@runtime_checkable

class VoltcraftPPS(PowerSupply):
    """Adapter over the original PPS class, exposing a clean interface."""

    def __init__(self, port: str, *, reset: bool = False, timeout: float = 1.0):
        self.port = port
        self._reset = reset
        self._timeout = timeout
        self._pps: Optional[PPS] = None     # real object created in connect()

        # limits populated in connect()
        self.VMAX = float("nan")
        self.IMAX = float("nan")
        self.VMIN = float("nan")
        self.MODEL = "Unknown"

    # ── PowerSupply API ─────────────────────────────────────────────
    def connect(self) -> None:
        self._pps = PPS(
            port=self.port,
            reset=self._reset,
            timeout=self._timeout,
            debug=False,
        )
        # copy constants for GUI
        self.VMAX = self._pps.VMAX
        self.IMAX = self._pps.IMAX
        self.VMIN = self._pps.VMIN
        self.MODEL = self._pps.MODEL

    def disconnect(self) -> None:
        if self._pps is not None:
            self._pps._serial.close()       # noqa: protected-member
            self._pps = None

    @property
    def connected(self) -> bool:
        return self._pps is not None

    # control -------------------------------------------------------
    def set_voltage(self, volts: float) -> None:
        assert self._pps
        self._pps.voltage(volts)

    def set_current(self, amps: float) -> None:
        assert self._pps
        self._pps.current(amps)

    def set_output(self, enable: bool) -> None:
        assert self._pps
        # PPS.output(0)=ON, 1=OFF   (inverted)
        self._pps.output(0 if enable else 1)

    # monitoring ----------------------------------------------------
    def read_output(self):
        assert self._pps
        v, a, _mode = self._pps.reading()
        return v, a
