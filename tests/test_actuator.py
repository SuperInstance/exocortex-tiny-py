"""Tests for ActuatorControl."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest
from exocortex_tiny.actuator import ActuatorControl


class TestActuatorControlInit(unittest.TestCase):
    def test_init_creates_control(self):
        a = ActuatorControl()
        self.assertIsNotNone(a)

    def test_init_detects_mock_mode(self):
        """On CPython (no board module), should be in mock mode."""
        a = ActuatorControl()
        self.assertFalse(a.is_hardware)


class TestActuatorControlMockOperations(unittest.TestCase):
    def setUp(self):
        self.actuators = ActuatorControl()

    def test_water_on_returns_true(self):
        result = self.actuators.water_on()
        self.assertTrue(result)

    def test_water_on_with_duration(self):
        result = self.actuators.water_on(0.5)
        self.assertTrue(result)

    def test_water_off_returns_true(self):
        result = self.actuators.water_off()
        self.assertTrue(result)

    def test_light_on_returns_true(self):
        result = self.actuators.light_on()
        self.assertTrue(result)

    def test_light_off_returns_true(self):
        result = self.actuators.light_off()
        self.assertTrue(result)

    def test_relay_set_on(self):
        result = self.actuators.relay_set(0, True)
        self.assertTrue(result)

    def test_relay_set_off(self):
        result = self.actuators.relay_set(0, False)
        self.assertTrue(result)

    def test_relay_set_different_ids(self):
        for i in range(4):
            result = self.actuators.relay_set(i, True)
            self.assertTrue(result)

    def test_water_cycle(self):
        """Test water on then off cycle."""
        self.assertTrue(self.actuators.water_on())
        self.assertTrue(self.actuators.water_off())

    def test_light_cycle(self):
        """Test light on then off cycle."""
        self.assertTrue(self.actuators.light_on())
        self.assertTrue(self.actuators.light_off())


if __name__ == "__main__":
    unittest.main()
