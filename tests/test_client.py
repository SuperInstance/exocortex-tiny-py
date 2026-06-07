"""Tests for ExocortexClient."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest
from unittest.mock import patch, MagicMock
from exocortex_tiny.config import ExocortexConfig
from exocortex_tiny.client import ExocortexClient


class TestExocortexClientInit(unittest.TestCase):
    def test_init_with_config(self):
        config = ExocortexConfig(base_url="https://test.com")
        client = ExocortexClient(config)
        self.assertEqual(client.config.base_url, "https://test.com")

    def test_detects_backend(self):
        config = ExocortexConfig()
        client = ExocortexClient(config)
        # On CPython, should detect urllib at minimum
        self.assertIn(client._backend, ("urequests", "urllib", "requests", None))


class TestExocortexClientRequest(unittest.TestCase):
    def setUp(self):
        self.config = ExocortexConfig(base_url="https://test.com", debug=False)
        self.client = ExocortexClient(self.config)

    def test_request_no_backend_returns_none(self):
        self.client._backend = None
        result = self.client._request("GET", "/test")
        self.assertIsNone(result)

    def test_request_exception_returns_none(self):
        self.client._backend = "urequests"
        self.client._requests = MagicMock()
        self.client._requests.request.side_effect = Exception("fail")
        result = self.client._request("GET", "/test")
        self.assertIsNone(result)

    def test_request_url_construction(self):
        """Verify URL is built correctly from base_url + path."""
        config = ExocortexConfig(base_url="https://example.com/api/")
        client = ExocortexClient(config)
        client._backend = "requests"
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"ok": True}
        mock_requests = MagicMock()
        mock_requests.get.return_value = mock_resp
        client._requests = mock_requests
        result = client._request("GET", "/health")
        mock_requests.get.assert_called_once_with(
            "https://example.com/api/health", json=None, timeout=10.0
        )
        self.assertEqual(result, {"ok": True})


class TestExocortexClientMethods(unittest.TestCase):
    def setUp(self):
        self.config = ExocortexConfig(base_url="https://test.com", notebook_id="nb:test")
        self.client = ExocortexClient(self.config)
        # Mock the _request method
        self.client._request = MagicMock(return_value={"result": "ok"})

    def test_predict(self):
        result = self.client.predict([23.5, 45.0])
        self.assertIsNotNone(result)
        self.client._request.assert_called_once()
        args = self.client._request.call_args
        self.assertEqual(args[0][0], "POST")
        self.assertIn("/api/a2a", args[0][1])

    def test_train(self):
        result = self.client.train("micro_nn", [[1, 2]], ["a"])
        self.assertIsNotNone(result)
        self.client._request.assert_called_once()

    def test_remember(self):
        result = self.client.remember("test memory", ["tag1"])
        self.assertIsNotNone(result)
        self.client._request.assert_called_once()

    def test_recall(self):
        self.client._request.return_value = {"results": ["memory1"]}
        result = self.client.recall("test query")
        self.assertIsNotNone(result)

    def test_recall_with_top_k(self):
        result = self.client.recall("test", top_k=10)
        self.assertIsNotNone(result)
        call_args = self.client._request.call_args
        payload = call_args[0][2] if len(call_args[0]) > 2 else call_args[1].get("data")

    def test_analyze(self):
        result = self.client.analyze([1.0, 2.0, 3.0])
        self.assertIsNotNone(result)

    def test_embed(self):
        result = self.client.embed("hello world")
        self.assertIsNotNone(result)

    def test_health_true(self):
        self.client._request.return_value = {"status": "ok"}
        self.assertTrue(self.client.health())

    def test_health_false(self):
        self.client._request.return_value = None
        self.assertFalse(self.client.health())


class TestExocortexClientErrorHandling(unittest.TestCase):
    def setUp(self):
        self.config = ExocortexConfig(base_url="https://test.com")
        self.client = ExocortexClient(self.config)
        self.client._request = MagicMock(return_value=None)

    def test_predict_returns_none_on_failure(self):
        result = self.client.predict([1.0])
        self.assertIsNone(result)

    def test_train_returns_none_on_failure(self):
        result = self.client.train("nn", [], [])
        self.assertIsNone(result)

    def test_remember_returns_none_on_failure(self):
        result = self.client.remember("text", [])
        self.assertIsNone(result)

    def test_recall_returns_none_on_failure(self):
        result = self.client.recall("query")
        self.assertIsNone(result)

    def test_analyze_returns_none_on_failure(self):
        result = self.client.analyze([])
        self.assertIsNone(result)

    def test_embed_returns_none_on_failure(self):
        result = self.client.embed("text")
        self.assertIsNone(result)

    def test_health_false_on_failure(self):
        self.assertFalse(self.client.health())


if __name__ == "__main__":
    unittest.main()
