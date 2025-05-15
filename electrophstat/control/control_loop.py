# electrophstat/control/control_loop.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class PumpAction:
    pump_id: str        # e.g. "acid", "base"
    volume_ml: float    # positive to add, negative to remove

class ControlLoop:
    """
    Encapsulates the pH-stat dosing algorithm.

    Usage:
        loop = ControlLoop(pumps, sensor, settings)
        loop.start()
        action = loop.process(current_pH)
        loop.stop()
    """
    def __init__(
        self,
        pumps: dict[str, object],    # mapping pump_id -> pump interface
        sensor: object,              # AtlasSensor or similar
        settings: dict              # loaded from config
    ):
        self.pumps = pumps
        self.sensor = sensor
        self.settings = settings
        self.running = False

    def start(self) -> None:
        """Initialize any state before dosing."""
        self.running = True

    def stop(self) -> None:
        """Clean up any running timers or state."""
        self.running = False

    def process(self, pH: float) -> Optional[PumpAction]:
        """
        Given the latest pH reading, decide on a pump action.
        Returns a PumpAction if dosing is needed, else None.
        """
        if not self.running:
            return None
        # TODO: implement control logic based on self.settings
        return None