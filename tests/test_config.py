"""Tests for ExocortexConfig."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest
from exocortex_tiny.config import ExocortexConfig


class TestExocortexConfigDefaults(unittest.TestCase):
    def test_default_base_url(self):
        c = ExocortexConfig()
        self.assertEqual(c.base_url, "")

    def test_default_notebook_id(self):
        c = ExocortexConfig()
        self.assertEqual(c.notebook_id, "")

    def test_default_poll_interval(self):
        c = ExocortexConfig()
        self.assertEqual(c.poll_interval_s, 300.0)

    def test_default_timeout(self):
        c = ExocortexConfig()
        self.assertEqual(c.timeout_s, 10.0)

    def test_default_model(self):
        c = ExocortexConfig()
        self.assertEqual(c.model, "micro_nn")

    def test_default_debug(self):
        c = ExocortexConfig()
        self.assertFalse(c.debug)


class TestExocortexConfigCustom(unittest.TestCase):
    def test_custom_base_url(self):
        c = ExocortexConfig(base_url="https://example.com")
        self.assertEqual(c.base_url, "https://example.com")

    def test_custom_notebook_id(self):
        c = ExocortexConfig(notebook_id="nb:001")
        self.assertEqual(c.notebook_id, "nb:001")

    def test_custom_poll_interval(self):
        c = ExocortexConfig(poll_interval_s=60.0)
        self.assertEqual(c.poll_interval_s, 60.0)

    def test_custom_timeout(self):
        c = ExocortexConfig(timeout_s=30.0)
        self.assertEqual(c.timeout_s, 30.0)

    def test_custom_model(self):
        c = ExocortexConfig(model="knn")
        self.assertEqual(c.model, "knn")

    def test_custom_debug(self):
        c = ExocortexConfig(debug=True)
        self.assertTrue(c.debug)


class TestExocortexConfigFromDict(unittest.TestCase):
    def test_from_dict_all_fields(self):
        d = {
            "base_url": "https://test.com",
            "notebook_id": "nb:test",
            "poll_interval_s": 120.0,
            "timeout_s": 5.0,
            "model": "knn",
            "debug": True,
        }
        c = ExocortexConfig.from_dict(d)
        self.assertEqual(c.base_url, "https://test.com")
        self.assertEqual(c.notebook_id, "nb:test")
        self.assertEqual(c.poll_interval_s, 120.0)
        self.assertEqual(c.timeout_s, 5.0)
        self.assertEqual(c.model, "knn")
        self.assertTrue(c.debug)

    def test_from_dict_partial(self):
        c = ExocortexConfig.from_dict({"base_url": "https://partial.com"})
        self.assertEqual(c.base_url, "https://partial.com")
        self.assertEqual(c.poll_interval_s, 300.0)  # default

    def test_from_dict_ignores_unknown_keys(self):
        c = ExocortexConfig.from_dict({"base_url": "https://test.com", "unknown": 42})
        self.assertEqual(c.base_url, "https://test.com")

    def test_from_dict_empty(self):
        c = ExocortexConfig.from_dict({})
        self.assertEqual(c.base_url, "")


class TestExocortexConfigToDict(unittest.TestCase):
    def test_to_dict_roundtrip(self):
        original = ExocortexConfig(
            base_url="https://rt.com",
            notebook_id="nb:rt",
            poll_interval_s=45.0,
            timeout_s=7.0,
            model="svm",
            debug=True,
        )
        d = original.to_dict()
        restored = ExocortexConfig.from_dict(d)
        self.assertEqual(restored.base_url, original.base_url)
        self.assertEqual(restored.notebook_id, original.notebook_id)
        self.assertEqual(restored.poll_interval_s, original.poll_interval_s)
        self.assertEqual(restored.timeout_s, original.timeout_s)
        self.assertEqual(restored.model, original.model)
        self.assertEqual(restored.debug, original.debug)

    def test_to_dict_has_all_keys(self):
        c = ExocortexConfig()
        d = c.to_dict()
        expected_keys = {"base_url", "notebook_id", "poll_interval_s",
                         "timeout_s", "model", "debug"}
        self.assertEqual(set(d.keys()), expected_keys)


if __name__ == "__main__":
    unittest.main()
