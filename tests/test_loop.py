"""Tests for ExocortexLoop."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest
from unittest.mock import MagicMock, patch
from exocortex_tiny.config import ExocortexConfig
from exocortex_tiny.client import ExocortexClient
from exocortex_tiny.sensor import SensorReader
from exocortex_tiny.actuator import ActuatorControl
from exocortex_tiny.loop import ExocortexLoop


class TestExocortexLoopInit(unittest.TestCase):
    def test_init_creates_loop(self):
        config = ExocortexConfig(base_url="https://test.com")
        client = ExocortexClient(config)
        sensors = SensorReader()
        actuators = ActuatorControl()
        loop = ExocortexLoop(client, sensors, actuators, config)
        self.assertIsNotNone(loop)

    def test_init_with_custom_decide(self):
        config = ExocortexConfig()
        client = MagicMock()
        sensors = MagicMock()
        actuators = MagicMock()
        decide = MagicMock(return_value={"action": "done"})
        loop = ExocortexLoop(client, sensors, actuators, config, decide_fn=decide)
        self.assertEqual(loop.decide_fn, decide)

    def test_initial_step_count(self):
        loop = ExocortexLoop(MagicMock(), MagicMock(), MagicMock(), ExocortexConfig())
        self.assertEqual(loop.step_count, 0)

    def test_initial_not_running(self):
        loop = ExocortexLoop(MagicMock(), MagicMock(), MagicMock(), ExocortexConfig())
        self.assertFalse(loop.is_running)


class TestExocortexLoopStep(unittest.TestCase):
    def setUp(self):
        self.config = ExocortexConfig(base_url="https://test.com", debug=False)
        self.client = MagicMock()
        self.sensors = MagicMock()
        self.actuators = MagicMock()
        self.sensors.read_all.return_value = {
            "temperature": 25.0,
            "humidity": 50.0,
            "soil_moisture": 0.4,
            "light": 600.0,
        }
        self.client.predict.return_value = {"result": {"message": {"parts": [{"data": {"action": "skip"}}]}}}
        self.client.remember.return_value = {"ok": True}

    def test_step_increments_count(self):
        loop = ExocortexLoop(self.client, self.sensors, self.actuators, self.config)
        loop.step()
        self.assertEqual(loop.step_count, 1)

    def test_step_reads_sensors(self):
        loop = ExocortexLoop(self.client, self.sensors, self.actuators, self.config)
        summary = loop.step()
        self.sensors.read_all.assert_called_once()
        self.assertIsNotNone(summary["sensors"])

    def test_step_sends_predict(self):
        loop = ExocortexLoop(self.client, self.sensors, self.actuators, self.config)
        loop.step()
        self.client.predict.assert_called_once()

    def test_step_remembers(self):
        loop = ExocortexLoop(self.client, self.sensors, self.actuators, self.config)
        summary = loop.step()
        self.client.remember.assert_called_once()
        self.assertTrue(summary["remembered"])

    def test_step_returns_summary(self):
        loop = ExocortexLoop(self.client, self.sensors, self.actuators, self.config)
        summary = loop.step()
        self.assertIn("step", summary)
        self.assertIn("sensors", summary)
        self.assertIn("action", summary)
        self.assertIn("remembered", summary)
        self.assertIn("error", summary)

    def test_step_with_custom_decide(self):
        decide = MagicMock(return_value={"action": "custom"})
        loop = ExocortexLoop(self.client, self.sensors, self.actuators, self.config, decide_fn=decide)
        summary = loop.step()
        decide.assert_called_once()
        self.assertEqual(summary["action"], {"action": "custom"})

    def test_step_sensor_failure(self):
        self.sensors.read_all.side_effect = RuntimeError("sensor fail")
        loop = ExocortexLoop(self.client, self.sensors, self.actuators, self.config)
        summary = loop.step()
        self.assertIsNone(summary["sensors"])
        self.assertIn("sensor_read_failed", summary["error"])

    def test_step_predict_failure_continues(self):
        self.client.predict.return_value = None
        loop = ExocortexLoop(self.client, self.sensors, self.actuators, self.config)
        summary = loop.step()
        # Should still complete the step
        self.assertIsNotNone(summary["sensors"])

    def test_step_remember_failure(self):
        self.client.remember.return_value = None
        loop = ExocortexLoop(self.client, self.sensors, self.actuators, self.config)
        summary = loop.step()
        self.assertFalse(summary["remembered"])


class TestExocortexLoopDefaultDecide(unittest.TestCase):
    def setUp(self):
        self.config = ExocortexConfig()
        self.actuators = MagicMock()
        self.loop = ExocortexLoop(MagicMock(), MagicMock(), self.actuators, self.config)

    def test_default_decide_skip(self):
        result = self.loop._default_decide({"soil_moisture": 0.5}, {"result": {"message": {"parts": [{"data": {"action": "skip"}}]}}})
        self.assertEqual(result["action"], "skip")

    def test_default_decide_water(self):
        result = self.loop._default_decide(
            {"soil_moisture": 0.5},
            {"result": {"message": {"parts": [{"data": {"action": "water", "amount_ml": 100}}]}}}
        )
        self.assertEqual(result["action"], "water")
        self.actuators.water_on.assert_called_once()

    def test_default_decide_no_prediction_dry_soil(self):
        result = self.loop._default_decide({"soil_moisture": 0.2}, None)
        self.assertEqual(result["action"], "water_fallback")

    def test_default_decide_no_prediction_wet_soil(self):
        result = self.loop._default_decide({"soil_moisture": 0.6}, None)
        self.assertEqual(result["action"], "skip")


class TestExocortexLoopControl(unittest.TestCase):
    def test_stop(self):
        loop = ExocortexLoop(MagicMock(), MagicMock(), MagicMock(), ExocortexConfig())
        loop._running = True
        loop.stop()
        self.assertFalse(loop.is_running)

    def test_last_error_initially_none(self):
        loop = ExocortexLoop(MagicMock(), MagicMock(), MagicMock(), ExocortexConfig())
        self.assertIsNone(loop.last_error)


if __name__ == "__main__":
    unittest.main()
