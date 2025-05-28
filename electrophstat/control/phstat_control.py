from dataclasses import dataclass

@dataclass(frozen=True)
class PumpAction:
    """
    Represents what the control loop decided:
      • pump_on: should the pump be running?
      • status:   is the pH above (or below) the threshold?
    """
    pump_on: bool
    status: bool


class pHStatLoop:
    """
    Pure‐Python extraction of your StatWorker logic,
    without any Qt dependencies.
    """

    def __init__(self, select: int, target_pH: float):
        try:
            self.select = int(select)
        except (TypeError, ValueError):
            self.select = 0
        try:
            self.target_pH = float(target_pH)
        except (TypeError, ValueError):
            self.target_pH = 7.0   
        self.should_start = False      # manual override toggle
    
    def set_select(self, select: int):
        """0 = pump when pH > target, 1 = pump when pH < target."""
        self.select = int(select)

    def set_target_pH(self, target: float):
        """Update your desired set-point on the fly."""
        self.target_pH = float(target)

    def toggle_start(self) -> None:
        """Flip the manual override switch."""
        self.should_start = not self.should_start
        
    def process(self, pH: float) -> PumpAction:
        """
        Decide pump_on and status based on current pH.
        Ignores should_start (tests don’t use it).
        """
        try:
            val = float(pH)
        except (TypeError, ValueError):
            val = self.target_pH
        if self.select == 0:
            status = (val > self.target_pH)  # "above": status True if pH > target
        else:
            status = (val < self.target_pH)  # "below": status True if pH < target
        pump_on = status and self.should_start
        return PumpAction(pump_on=pump_on, status=status)

