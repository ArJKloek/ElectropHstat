# electrophstat/control/__init__.py
"""
Control-loop domain module for pH-stat dosing algorithm.
"""
from .phstat_control import pHStatLoop

__all__ = ["pHStatLoop"]