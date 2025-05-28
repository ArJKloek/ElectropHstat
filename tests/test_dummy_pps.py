# tests/test_dummy_pps.py
import pytest
from electrophstat.dummy.dummy_pps import DummyPPS
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

def test_dummy_pps_basic():
    ps = DummyPPS(); ps.connect()
    ps.voltage(5); ps.current(0.3); ps.output(True)
    v, a, mode = ps.read_output()
    assert abs(v-5) < 0.1 and abs(a-0.3) < 0.05
