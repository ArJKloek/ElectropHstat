# electrophstat/sensors/atlas_i2c.py
from __future__ import annotations
from typing import Optional
from ..hardware.i2c_transport import I2CDevice
from .interfaces import AtlasSensor


class AtlasI2C(AtlasSensor):
    """Atlas Scientific EZO board in I²C mode (pH, RTD, ORP, …)."""

    def __init__(
        self,
        address: int = 0x63,
        kind: str = "pH",
        bus: int = 1,
    ):
        self.kind = kind
        # transport opens the bus and sets the address
        self._dev = I2CDevice(address, bus)

    def connect(self) -> None:
        # nothing extra to do; device already ready
        pass

    @property
    def connected(self) -> bool:
        # if the file descriptors are open
        return self._dev._rd is not None

    def disconnect(self) -> None:
        self._dev.close()

    def read(self) -> float:
        """
        Perform a measurement read.
        pH / RTD needs the longer timeout; others may not.
        """
        resp = self._dev.query("R", expect_long=True)
        if not resp or resp[0] != "\x01":
            raise RuntimeError(f"Bad reply from {self.kind!r}: {resp!r}")
        # drop the status byte
        return float(resp[1:])

    def set_temp_comp(self, celsius: float) -> None:
        cmd = f"T,{celsius:.2f}"
        self._dev.query(cmd, expect_long=False)

    def clear_cal(self) -> None:
        self._dev.query("Cal,clear", expect_long=True)

    def calibrate(self, *args, **kwargs) -> None:
        # you can parse args like ("mid", 7.00) or similar
        raise NotImplementedError("Calibration not yet implemented")
