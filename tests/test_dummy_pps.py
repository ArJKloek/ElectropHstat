# tests/test_dummy_pps.py
import pytest
from electrophstat.dummy.dummy_pps import DummyPPS

def test_dummy_pps_basic():
    ps = DummyPPS(); ps.connect()
    ps.set_voltage(5); ps.set_current(0.3); ps.set_output(True)
    v, a, mode = ps.read_output()
    assert abs(v-5) < 0.1 and abs(a-0.3) < 0.05

def test_dummy_pps_output_control():
    ps = DummyPPS(); ps.connect()
    ps.set_output(True)
    assert ps.read_output()[2] == True
    ps.set_output(False)
    assert ps.read_output()[2] == False 