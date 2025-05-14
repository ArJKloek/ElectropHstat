from .dummy_atlas import DummyAtlas
from ..vendor.atlas_i2c import AtlasI2C
from ..hardware.interfaces import AtlasSensor

__all__ = [
    "AtlasSensor",
    "DummyAtlas",
    "AtlasI2C",
    "discover_ph_sensor",
    "discover_temp_sensor",
]

def discover_ph_sensor(prefer_hw: bool = True) -> AtlasSensor:
    if prefer_hw:
        try:
            s = AtlasI2C(address=0x63, kind="pH")
            # ping to verify
            s.read()
            print("[pH] Detected real Atlas EZO pH at 0x63")
            return s
        except Exception:
            pass
    dummy = DummyAtlas(kind="pH")
    dummy.connect()
    return dummy

def discover_temp_sensor(prefer_hw: bool = True) -> AtlasSensor:
    if prefer_hw:
        try:
            s = AtlasI2C(address=0x66, kind="RTD")
            s.read()
            print("[RTD] Detected real Atlas EZO RTD at 0x66")
            return s
        except Exception:
            pass
    dummy = DummyAtlas(kind="RTD")
    dummy.connect()
    return dummy