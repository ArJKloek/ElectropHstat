# tests/test_dummy_pps.py
from ..hardware.dummy_pps import DummyPPS

def test_dummy_pps_basic():
    ps = DummyPPS(); ps.connect()
    ps.set_voltage(5); ps.set_current(0.3); ps.set_output(True)
    v, a = ps.read_output()
    assert abs(v-5) < 0.1 and abs(a-0.3) < 0.05
