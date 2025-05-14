# electrophstat/hardware/i2c_transport.py
from __future__ import annotations
import io
import fcntl
import time
from typing import Optional


class I2CDevice:
    """
    Generic I²C device access via /dev/i2c-N and ioctl.
    Provides write, read, and query() with selectable timeouts.
    """

    # default delays in seconds
    long_timeout  = 1.5
    short_timeout = 0.3

    def __init__(
        self,
        address: int,
        bus: int = 1,
        long_timeout: float = None,
        short_timeout: float = None,
    ):
        self.address = address
        self.bus = bus
        self._timeout_long  = long_timeout  or self.long_timeout
        self._timeout_short = short_timeout or self.short_timeout

        path = f"/dev/i2c-{self.bus}"
        self._rd = io.open(path, "rb", buffering=0)
        self._wr = io.open(path, "wb", buffering=0)
        self._set_addr(self.address)

    def _set_addr(self, addr: int):
        # 0x0703 is I2C_SLAVE
        I2C_SLAVE = 0x0703
        fcntl.ioctl(self._rd, I2C_SLAVE, addr)
        fcntl.ioctl(self._wr, I2C_SLAVE, addr)

    def write(self, cmd: str) -> None:
        # Atlas boards expect a null-terminator
        data = (cmd + "\0").encode("utf-8")
        self._wr.write(data)

    def read(self, length: int = 32) -> str:
        raw = self._rd.read(length)
        # strip trailing nulls and leading status byte
        return raw.decode("utf-8", errors="ignore").strip("\x00")

    def query(
        self,
        cmd: str,
        *,
        expect_long: bool = False,
        read_length: int = 32,
    ) -> str:
        """
        Write `cmd`, wait the appropriate timeout, then read `read_length` bytes.
        If expect_long=True use the longer delay.
        """
        self.write(cmd)
        to = self._timeout_long if expect_long else self._timeout_short
        time.sleep(to)
        return self.read(read_length)

    def close(self) -> None:
        self._rd.close()
        self._wr.close()
