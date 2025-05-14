# electrophstat/utils/serial_helpers.py
"""
Utility helpers for serial devices (Voltcraft PPS, pumps, etc.).
"""
from __future__ import annotations
from typing import Optional   
import serial.tools.list_ports

_MATCH_IDS = {
    "0403:6001",   # FTDI FT232R  (many older units)
    "10C4:EA60",   # Silicon Labs CP2102  ← your bridge
}

def find_voltcraft_pps() -> Optional[str]:
    """Return /dev path of the first USB-UART that matches our ID list."""
    for port in lp.comports():
        vidpid = port.hwid.split("VID:PID=")[-1][:9]  # e.g. "10C4:EA60"
        if vidpid in _MATCH_IDS:
            return port.device                        # "/dev/ttyUSB1"
    return None
