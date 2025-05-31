import math, random, time
from ..hardware.interfaces import ADCSensor

class DummyADS1115(ADCSensor):
    """
    A dummy ADS1115-style driver that returns a synthetic
    voltage reading on channel 1 (and ignores other channels).
    """

    def __init__(self):
        self._t = 0.0

    def set_gain(self, gain):
        # no-op in dummy
        pass

    def set_addr_ADS1115(self, addr):
        # no-op in dummy
        pass

    def read_voltage(self, channel: int) -> dict:
        """
        Simulate a voltage reading for `channel`. Only channel 0 varies
        as a sine wave with a 3-hour period, everything else returns 0.0.
        Returns a dict with key 'r' to mimic the real API.
        """
        # advance time (assuming 1 second per call)
        self._t += 1.0
        if channel == 0:
            # 3-hour period = 10,800 seconds
            period = 10800
            # sine wave between 1000 and 3000 plus some random noise
            base = 2000 + 1000 * math.sin(2 * math.pi * (self._t / period))
            noise = random.uniform(-2, 2)
            val = base + noise
        else:
            val = 0.0
        # emulate dict API
        return {'r': int(val)}