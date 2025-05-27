import pytest
import numpy as np
from electrophstat.models.model_calculator import BiExpCalibrator

class DummyWin:
    pass

@pytest.fixture
def calibrator():
    # Create a calibrator and fit it with some dummy data
    win = DummyWin()
    calibrator = BiExpCalibrator(win)
    xdata = np.array([0, 1000, 2000, 4000])
    ydata = np.array([4800, 3350, 2600, 1650])
    Y0 = 4800
    Plateau = 30
    calibrator.fit(xdata, ydata, Y0, Plateau)
    return calibrator

def test_inverse_out_of_range(calibrator):
    # Pick a voltage outside the model's range (e.g., much higher than Y0)
    voltage_too_high = 6000  # higher than any possible model output
    with pytest.raises(ValueError, match="f\\(a\\) and f\\(b\\) must have different signs"):
        calibrator.inverse(voltage_too_high, x_min=0, x_max=8000)

    # Pick a voltage too low (below Plateau)
    voltage_too_low = -100
    with pytest.raises(ValueError, match="f\\(a\\) and f\\(b\\) must have different signs"):
        calibrator.inverse(voltage_too_low, x_min=0, x_max=8000)