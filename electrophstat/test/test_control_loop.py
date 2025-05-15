import pytest
from ..control.control_loop import ControlLoop, PumpAction

@pytest.mark.parametrize("select,target,pH,should_start,expected", [
    (0, 7.0, 7.5, False, PumpAction(pump_on=True,  status=True)),
    (0, 7.0, 6.5, False, PumpAction(pump_on=False, status=False)),
    (1, 7.0, 6.5, False, PumpAction(pump_on=True,  status=True)),
    (1, 7.0, 7.5, False, PumpAction(pump_on=False, status=False)),
    (0, 7.0, 6.5, True,  PumpAction(pump_on=False, status=False)),  # manual override off
    (0, 7.0, 8.0, True,  PumpAction(pump_on=True,  status=True)),   # manual override on
])
def test_control_loop_logic(select, target, pH, should_start, expected):
    loop = ControlLoop(select=select, target_pH=target)
    loop.should_start = should_start
    result = loop.process(pH)
    assert result == expected

def test_control_loop_toggle_start():
    loop = ControlLoop(select=0, target_pH=7.0)
    assert not loop.should_start
    loop.toggle_start()
    assert loop.should_start
    loop.toggle_start()
    assert not loop.should_start
