# electrophstat/hardware/__init__.py
from __future__ import annotations
from .voltcraft_pps import VoltcraftPPS
from ..utils.serial_helpers import find_voltcraft_pps  # your existing finder
from ..vendor.DFRobot_ADS1115 import ADS1115
from electrophstat.hardware.interfaces import ADCSensor

def discover_power_supply(prefer_hw: bool = True, reset: bool= False):
    port = find_voltcraft_pps() if prefer_hw else None
    if port:
        print("[DEBUG] Found real PPS at", port)
        ps = VoltcraftPPS(port, reset=reset)
        ps.connect()
        return ps
    # fallback
    print("[DEBUG] Using dummy PPS")
    from ..dummy.dummy_pps import DummyPPS

    dummy = DummyPPS()
    dummy.connect()
    return dummy

def discover_adc(prefer_hw: bool = True, channel: int = 1.0) -> ADCSensor:
    """
    Try to instantiate a real ADS1115 and verify it by a quick read.
    If that fails (or prefer_hw=False), return DummyADS1115 instead.
    """
    ADS1115_REG_CONFIG_PGA_6_144V        = 0x00 # 6.144V range = Gain 2/3
    ADS1115_REG_CONFIG_PGA_4_096V        = 0x02 # 4.096V range = Gain 1
    ADS1115_REG_CONFIG_PGA_2_048V        = 0x04 # 2.048V range = Gain 2 (default)
    ADS1115_REG_CONFIG_PGA_1_024V        = 0x06 # 1.024V range = Gain 4
    ADS1115_REG_CONFIG_PGA_0_512V        = 0x08 # 0.512V range = Gain 8
    ADS1115_REG_CONFIG_PGA_0_256V        = 0x0A # 0.256V range = Gain 16
    if prefer_hw:
        try:
            adc = ADS1115()  # whatever your real constructor is
            adc.set_addr_ADS1115(0x48)
            #Sets the gain and input voltage range.
            adc.set_gain(ADS1115_REG_CONFIG_PGA_6_144V) 
            # perform a “ping” read:
            _ = adc.read_voltage(1)
            print("[ADC] Found real ADS1115")
            return adc
        except Exception as e:
            print(f"[ADC] Real ADS1115 not found ({e}), falling back to Dummy")
    from ..dummy.dummy_ADS1115 import DummyADS1115

    dummy = DummyADS1115()
    dummy.connect()
    print("[ADC] Using DummyADS1115")
    return dummy

def discover_switcher(prefer_hw: bool = True):
    """
    Try to import and verify the real lib8mosind hardware.
    If that fails (or prefer_hw=False), return MockLib8MosInd instead.
    """
    if prefer_hw:
        try:
            from electrophstat.vendor import lib8mosind
            # Try a harmless hardware check (e.g., read or write)
            # This assumes you have a check or get function in lib8mosind
            # For example, try to read from the default address:
            try:
                # Replace DEVICE_ADDRESS with the actual address if needed
                if hasattr(lib8mosind, "check"):
                    # If check returns True/False, use that
                    if not lib8mosind.check(None, lib8mosind.DEVICE_ADDRESS):
                        raise IOError("lib8mosind.check() failed")
                else:
                    # Try a harmless read or write as a check
                    lib8mosind.getWord(None, lib8mosind.DEVICE_ADDRESS, lib8mosind.MOSFET8_INPORT_REG_ADD)
            except Exception as hw_exc:
                raise IOError(f"lib8mosind hardware not responding: {hw_exc}")
            print("[MOSFET] Found real lib8mosind and hardware present")
            return lib8mosind
        except Exception as e:
            print(f"[MOSFET] Real lib8mosind not found or hardware not present ({e}), falling back to MockLib8MosInd")

    from electrophstat.dummy.dummy_switcher import MockLib8MosInd
    print("[MOSFET] Using MockLib8MosInd")
    return MockLib8MosInd()