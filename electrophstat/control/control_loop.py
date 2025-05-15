from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class PumpAction:
    """
    Represents what the control loop decided:
      • pump_on: should the pump be running?
      • status:   does the current pH state satisfy the control condition?
    """
    pump_on: bool
    status: bool

@dataclass
class ControlResult:
    """
    Encapsulates the outcome of one control-cycle.
    - `status`: True if pH is outside the target condition.
    - `pump`:   True if the pump should be activated.
    """
    status: bool
    pump: bool

class ControlLoop:
    """
    Core pH-stat dosing logic, extracted from the old StatWorker.
    - select: 0 = dose when pH > target; 1 = dose when pH < target
    - target_pH: desired pH setpoint
    - toggle_auto(): enables/disables automatic pumping
    """
    def __init__(
        self,
        select: int,
        target_pH: float,
    ) -> None:
        self.select = select
        self.target_pH = target_pH
        self.auto_enabled = False

    def toggle_auto(self) -> None:
        """Enable or disable automatic dosing."""
        self.auto_enabled = not self.auto_enabled

    def set_select(self, select: int) -> None:
        """0 = high pH dosing; 1 = low pH dosing."""
        self.select = select

    def set_target_pH(self, pH: float) -> None:
        """Update the pH setpoint."""
        self.target_pH = pH

    def process(self, pH: float) -> Optional[ControlResult]:
        """
        Take a new pH measurement and decide:
        - `status`: whether the condition (pH >/< target) is met
        - `pump`:   whether to keep or stop pumping when no longer met
        Returns a ControlResult or None if nothing changed.
        """
        # Determine if dosing condition is currently true
        condition_met = (pH > self.target_pH) if self.select == 0 else (pH < self.target_pH)

        # Status always reflects the condition
        status = condition_met

        # Pump only turns off when auto-enabled and condition ceases
        pump = False
        if not condition_met and self.auto_enabled:
            pump = False

        return ControlResult(status=status, pump=pump)