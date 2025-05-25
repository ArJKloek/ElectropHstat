# electrophstat/hardware/__init__.py
from __future__ import annotations
from .voltcraft_pps import VoltcraftPPS
from ..dummy.dummy_pps import DummyPPS
from ..utils.serial_helpers import find_voltcraft_pps  # your existing finder
from ..vendor.DFRobot_ADS1115 import ADS1115
from electrophstat.hardware.interfaces import ADCSensor
from ..dummy.dummy_ADS1115 import DummyADS1115

def discover_power_supply(prefer_hw: bool = True, reset: bool= False):
    port = find_voltcraft_pps() if prefer_hw else None
    if port:
        print("[DEBUG] Found real PPS at", port)
        ps = VoltcraftPPS(port, reset=reset)
        ps.connect()
        return ps
    # fallback
    print("[DEBUG] Using dummy PPS")
    dummy = DummyPPS()
    dummy.connect()
    return dummy

def discover_adc(prefer_hw: bool = True, channel: int = 1.0) -> ADCSensor:
    """
    Try to instantiate a real ADS1115 and verify it by a quick read.
    If that fails (or prefer_hw=False), return DummyADS1115 instead.
    """
    if prefer_hw:
        try:
            adc = ADS1115()  # whatever your real constructor is
            adc.set_gain(ADS1115_REG_CONFIG_PGA_4_096V)
            adc.set_addr_ADS1115(ADS1115_IIC_ADDRESS0)
            # perform a “ping” read:
            _ = adc.read_voltage(1)
            print("[ADC] Found real ADS1115")
            return adc
        except Exception as e:
            print(f"[ADC] Real ADS1115 not found ({e}), falling back to Dummy")

    dummy = DummyADS1115()
    dummy.connect()
    print("[ADC] Using DummyADS1115")
    return dummy