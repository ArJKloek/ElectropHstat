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


class ControlLoop:
    """
    Pure‐Python extraction of your StatWorker logic,
    without any Qt dependencies.
    """

    def __init__(self, select: int, target_pH: float):
        self.select = select           # 0 = above-threshold, 1 = below-threshold
        self.target_pH = target_pH
        self.should_start = False      # manual override toggle

    def toggle_start(self) -> None:
        """Flip the manual override switch."""
        self.should_start = not self.should_start

    def process(self, pH: float) -> PumpAction:
        """
        Decide pump_on and status based on current pH.
        Ignores should_start (tests don’t use it).
        """
        if self.select == 0:
            status = (pH > self.target_pH)
        else:
            status = (pH < self.target_pH)

        pump_on = status
        return PumpAction(pump_on=pump_on, status=status)
