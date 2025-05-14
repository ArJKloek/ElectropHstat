from .dummy_atlas import DummyAtlas
from ..vendor.atlas_i2c import AtlasI2C
from ..hardware.interfaces import AtlasSensor

__all__ = ["AtlasSensor", "DummyAtlas", "AtlasI2C", "discover_ph_sensor"]

def discover_ph_sensor(prefer_hw: bool = True) -> AtlasSensor:
    if prefer_hw:
        try:
            sensor = AtlasI2C(address=0x63, kind="pH")
            sensor.connect()
            # simple ping to confirm board is there
            sensor.read()
            print("[pH] Real Atlas EZO detected at 0x63")
            return sensor
        except Exception as e:
            print(f"[pH] Hardware probe failed: {e} — falling back to dummy")

    dummy = DummyAtlas(kind="pH")
    dummy.connect()
    return dummy
