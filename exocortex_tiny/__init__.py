"""exocortex-tiny-py — Minimal Python client for the exocortex.

Designed for CircuitPython on ESP32. Zero external dependencies.
The ESP32 is the PLATO terminal. The exocortex is the mainframe.
"""

from .config import ExocortexConfig
from .client import ExocortexClient
from .sensor import SensorReader
from .actuator import ActuatorControl
from .loop import ExocortexLoop

__version__ = "0.1.0"
__all__ = [
    "ExocortexConfig",
    "ExocortexClient",
    "SensorReader",
    "ActuatorControl",
    "ExocortexLoop",
]
