# electrophstat/utils/serial_helpers.py
"""
Utility helpers for serial devices (Voltcraft PPS, pumps, etc.).
"""
from __future__ import annotations

import serial.tools.list_ports


def find_voltcraft_pps() -> str | None:
    """
    Return the first serial port that looks like a Voltcraft PPS,
    or None if nothing is found.
    """
    for port in serial.tools.list_ports.comports():
        # tweak the VID:PID or string match to whatever your PPS shows
        if "Voltcraft" in port.description or "VID:PID=0403:6001" in port.hwid:
            return port.device          # e.g. 'COM6', '/dev/ttyUSB0'
    return None
