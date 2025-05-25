try:
    # Python ≥ 3.8
    from typing import Protocol, Literal, runtime_checkable, Optional, Tuple
except ImportError:                 # Python 3.7 fallback
    from typing_extensions import Protocol, Literal, runtime_checkable
    from typing import Optional, Tuple        # Tuple still comes from stdlib


@runtime_checkable
class PowerSupply(Protocol):
    """High-level contract for any DC bench supply (real or dummy)."""

    port: Optional[str] # e.g. 'COM6' or '/dev/ttyUSB0'

    # ---------- life-cycle ----------
    def connect(self) -> None: ...
    def disconnect(self) -> None: ...
    @property
    def connected(self) -> bool: ...

    # ---------- control ----------
    def voltage(self, volts: float) -> None: ...
    def current(self, amps: float) -> None: ...
    def output(self, enable: bool) -> None: ...

    def reading(self) -> Tuple[float, float, Literal["CC", "CV"]]: ...
        # returns (voltage, current, mode)

@runtime_checkable
class Pump(Protocol):
    """Contract for peristaltic / syringe pumps."""

    address: int  # Modbus or I2C, whatever

    def connect(self) -> None: ...
    def disconnect(self) -> None: ...
    @property
    def connected(self) -> bool: ...

    def set_speed(self, rpm: float) -> None: ...
    def start(self) -> None: ...
    def stop(self) -> None: ...

@runtime_checkable
class AtlasSensor(Protocol):
    """Generic contract for an Atlas I²C sensor board."""

    address: int                      # e.g. 0x63
    kind: str                         # "pH", "EC", …

    # life-cycle ---------------------------------------------------
    def connect(self) -> None: ...
    def disconnect(self) -> None: ...
    @property
    def connected(self) -> bool: ...

    # measurement --------------------------------------------------
    def read(self) -> float: ...
        # returns the primary value (pH units, mS/cm, mg/L, …)

    # optional helpers --------------------------------------------
    def set_temp_comp(self, celsius: float) -> None: ...
    def clear_cal(self) -> None: ...
    def calibrate(self, *args, **kwargs) -> None: ...

@runtime_checkable
class ADCSensor(Protocol):
    """
    High-level contract for any ADS1115-style ADC (real or dummy).
    """

    # optional “where” it lives; not strictly required
    bus: Optional[str]
    address: Optional[int]

    # lifecycle
    def connect(self) -> None: ...
    def disconnect(self) -> None: ...
    @property
    def connected(self) -> bool: ...

    # read one channel, return raw ticks or volts
    def read_voltage(self, channel: int) -> Tuple[float, float]: ...
    #             └─ channel 0–3             └─ (value, timestamp) or just value