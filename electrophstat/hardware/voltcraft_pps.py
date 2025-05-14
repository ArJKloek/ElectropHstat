# electrophstat/hardware/voltcraft_pps.py
from __future__ import annotations
import serial
from .interfaces import PowerSupply


class VoltcraftPPS(PowerSupply):
    """Voltcraft PPS — basic SCPI-like serial protocol."""

    def __init__(self, port: str, baud: int = 9600) -> None:
        self.port = port
        self._baud = baud
        self._ser: serial.Serial | None = None

    # ---------- life-cycle ----------
    def connect(self) -> None:
        self._ser = serial.Serial(self.port, self._baud, timeout=1)

    def disconnect(self) -> None:
        if self._ser:
            self._ser.close()
            self._ser = None

    @property
    def connected(self) -> bool:
        return self._ser is not None and self._ser.is_open

    # ---------- control ----------
    def _write(self, cmd: str) -> None:
        assert self._ser, "not connected"
        self._ser.write((cmd + "\n").encode())

    def set_voltage(self, volts: float) -> None: self._write(f"VOLT {volts:.3f}")
    def set_current(self, amps: float) -> None:  self._write(f"CURR {amps:.3f}")
    def set_output(self, enable: bool) -> None:  self._write(f"OUTP {'1' if enable else '0'}")

    # ---------- monitoring ----------
    def read_output(self):
        assert self._ser
        self._write("MEAS:SCAL?")
        resp = self._ser.readline().decode().strip()   # e.g. "12.000,0.320"
        v, a = map(float, resp.split(","))
        return v, a
