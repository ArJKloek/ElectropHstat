# electrophstat/hardware/__init__.py
from __future__ import annotations
from .voltcraft_pps import VoltcraftPPS
from .dummy_pps import DummyPPS
from ..utils.serial_helpers import find_voltcraft_pps  # your existing finder


def discover_power_supply(prefer_hw: bool = True):
    port = find_voltcraft_pps() if prefer_hw else None
    if port:
        ps = VoltcraftPPS(port)
        ps.connect()
        return ps
    # fallback
    dummy = DummyPPS()
    dummy.connect()
    return dummy
