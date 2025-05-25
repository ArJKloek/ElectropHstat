from typing import Dict
from ..dummy.dummy_atlas import DummyAtlas
from ..vendor.atlas_i2c import AtlasI2C
from ..hardware.interfaces import AtlasSensor

__all__ = [
    "AtlasSensor",
    "DummyAtlas",
    "AtlasI2C",
    "register_sensor",
    "discover_sensor",
   # "discover_ph_sensor",
   # "discover_temp_sensor",
]

# 1) A simple registry: name -> (address, kind)
_SENSOR_REGISTRY: Dict[str, Dict[str, object]] = {}

def register_sensor(name: str, address: int, kind: str) -> None:
    """
    Register a new Atlas‐I2C sensor type.

      name:    logical key, e.g. "ph", "temp", "orp"
      address: I2C address (e.g. 0x63)
      kind:    the string AtlasI2C expects (e.g. "pH", "RTD", "ORP")
    """
    _SENSOR_REGISTRY[name] = {"address": address, "kind": kind}

# 2) Pre-register the defaults:
register_sensor("pH",   address=0x63, kind="pH")
register_sensor("temperature", address=0x66, kind="RTD")


def discover_sensor(name: str, prefer_hw: bool = True) -> AtlasSensor:
    """
    Generic discovery of an Atlas sensor by its registry key.
    Falls back to DummyAtlas if hardware probe fails.
    """
    cfg = _SENSOR_REGISTRY.get(name)
    if cfg is None:
        raise KeyError(f"No sensor registered under name {name!r}")

    address = cfg["address"]
    kind    = cfg["kind"]

    if prefer_hw:
        try:
            s = AtlasI2C(address=address, kind=kind)
            s.read()  # “ping” it
            print(f"[{name}] Detected real Atlas EZO {kind} at 0x{address:02X}")
            return s, kind
        except Exception:
            pass

    # fallback to dummy
    dummy = DummyAtlas(kind=kind)
    dummy.connect()
    print(f"[{name}] Using DummyAtlas ({kind})")
    return dummy, kind


# 3) Backwards‐compatible wrappers:
#def discover_ph_sensor(prefer_hw: bool = True) -> AtlasSensor:
#    return discover_sensor("ph", prefer_hw)

#def discover_temp_sensor(prefer_hw: bool = True) -> AtlasSensor:
#    return discover_sensor("temp", prefer_hw)
