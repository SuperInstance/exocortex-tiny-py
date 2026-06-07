"""Tests for SensorReader."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest
from exocortex_tiny.sensor import SensorReader


class TestSensorReaderInit(unittest.TestCase):
    def test_init_creates_reader(self):
        s = SensorReader()
        self.assertIsNotNone(s)

    def test_init_detects_mock_mode(self):
        """On CPython (no board module), should be in mock mode."""
        s = SensorReader()
        self.assertFalse(s.is_hardware)


class TestSensorReaderMockValues(unittest.TestCase):
    def setUp(self):
        self.sensors = SensorReader()

    def test_read_temperature(self):
        t = self.sensors.read_temperature()
        self.assertIsInstance(t, float)
        self.assertEqual(t, 23.5)

    def test_read_humidity(self):
        h = self.sensors.read_humidity()
        self.assertIsInstance(h, float)
        self.assertEqual(h, 45.0)

    def test_read_soil_moisture(self):
        m = self.sensors.read_soil_moisture()
        self.assertIsInstance(m, float)
        self.assertEqual(m, 0.35)

    def test_read_light(self):
        l = self.sensors.read_light()
        self.assertIsInstance(l, float)
        self.assertEqual(l, 512.0)


class TestSensorReaderReadAll(unittest.TestCase):
    def setUp(self):
        self.sensors = SensorReader()

    def test_read_all_returns_dict(self):
        data = self.sensors.read_all()
        self.assertIsInstance(data, dict)

    def test_read_all_has_temperature(self):
        data = self.sensors.read_all()
        self.assertIn("temperature", data)

    def test_read_all_has_humidity(self):
        data = self.sensors.read_all()
        self.assertIn("humidity", data)

    def test_read_all_has_soil_moisture(self):
        data = self.sensors.read_all()
        self.assertIn("soil_moisture", data)

    def test_read_all_has_light(self):
        data = self.sensors.read_all()
        self.assertIn("light", data)

    def test_read_all_has_four_keys(self):
        data = self.sensors.read_all()
        self.assertEqual(len(data), 4)

    def test_read_all_values_are_float(self):
        data = self.sensors.read_all()
        for key, value in data.items():
            self.assertIsInstance(value, float, "{} should be float".format(key))


if __name__ == "__main__":
    unittest.main()
