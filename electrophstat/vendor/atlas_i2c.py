from __future__ import annotations
import time
from typing import Optional

import smbus2
from ..hardware.interfaces import AtlasSensor


class AtlasI2C(AtlasSensor):
    """Atlas Scientific EZO board in I²C mode."""

    def __init__(self, address: int = 0x63, kind: str = "pH", bus: int = 1):
        self.address = address
        self.kind = kind
        self._bus_number = bus
        self._bus: Optional[smbus2.SMBus] = None

    # ---------- life-cycle ----------
    def connect(self) -> None:
        self._bus = smbus2.SMBus(self._bus_number)

    def disconnect(self) -> None:
        if self._bus:
            self._bus.close()
            self._bus = None

    @property
    def connected(self) -> bool:
        return self._bus is not None

    # ---------- measurement ----------
    def read(self) -> float:
        assert self._bus, "not connected"

        # 1. send the 'R' command (0x52) with a null terminator
        self._bus.write_i2c_block_data(self.address, 0x52, [])
        time.sleep(1.0)                       # allow processing (800 ms)

        # 2. read up to 32 bytes
        data = self._bus.read_i2c_block_data(self.address, 0, 32)
        chars = bytes([b for b in data if b != 0]).decode(errors="ignore")
        # response looks like: '\x01+7.02' (leading status byte 1=success)
        if not chars or chars[0] != "\x01":
            raise RuntimeError(f"Bad reply from EZO: {chars!r}")

        return float(chars[1:])               # strip status byte

    # ---------- optional helpers ----------
    def set_temp_comp(self, celsius: float) -> None:
        assert self._bus
        cmd = f"T,{celsius:.2f}"
        self._bus.write_i2c_block_data(self.address, ord(cmd[0]), list(cmd[1:].encode()))

    def clear_cal(self) -> None:
        assert self._bus
        self._bus.write_i2c_block_data(self.address, ord("Cal".encode()[0]),
                                       list("Cal,clear".encode()[1:]))

    def calibrate(self, *args, **kwargs) -> None:
        # implement as needed
        pass
