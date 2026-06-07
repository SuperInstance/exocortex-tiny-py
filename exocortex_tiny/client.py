"""ExocortexClient — HTTP client for the exocortex.

Uses urequests on CircuitPython, urllib on CPython.
Never raises on network failure — returns None instead.
"""

import json


class ExocortexClient:
    """Minimal HTTP client for communicating with the exocortex.

    The client handles predict, train, remember, recall, analyze, and embed
    operations via the exocortex A2A (agent-to-agent) API.

    All methods return result dicts on success or None on failure.
    No exceptions are raised for network errors.
    """

    def __init__(self, config):
        """Initialize client with an ExocortexConfig.

        Args:
            config: ExocortexConfig instance with base_url and settings.
        """
        self.config = config
        self._session = None
        self._detect_http_backend()

    def _detect_http_backend(self):
        """Detect available HTTP library (urequests or urllib)."""
        self._backend = None
        try:
            import urequests  # noqa: F401 — CircuitPython
            self._backend = "urequests"
            self._requests = urequests
            return
        except ImportError:
            pass
        try:
            import urllib.request  # CPython fallback
            self._backend = "urllib"
            self._urllib = urllib.request
            return
        except ImportError:
            pass
        try:
            import requests  # Last resort — if installed
            self._backend = "requests"
            self._requests = requests
        except ImportError:
            self._backend = None

    def _request(self, method, path, data=None):
        """Execute an HTTP request.

        Args:
            method: HTTP method ("GET" or "POST")
            path: URL path (appended to base_url)
            data: Optional dict to send as JSON body

        Returns:
            Parsed JSON response as dict, or None on any failure.
        """
        url = self.config.base_url.rstrip("/") + path
        if self.config.debug:
            print("[exocortex] {} {}".format(method, url))

        try:
            if self._backend == "urequests":
                return self._request_urequests(method, url, data)
            elif self._backend == "urllib":
                return self._request_urllib(method, url, data)
            elif self._backend == "requests":
                return self._request_requests(method, url, data)
            else:
                if self.config.debug:
                    print("[exocortex] No HTTP backend available")
                return None
        except Exception as e:
            if self.config.debug:
                print("[exocortex] Request failed: {}".format(e))
            return None

    def _request_urequests(self, method, url, data):
        """Make request using CircuitPython urequests."""
        import urequests
        headers = {"Content-Type": "application/json"}
        body = json.dumps(data) if data else None
        resp = urequests.request(method, url, data=body, headers=headers)
        result = resp.json()
        try:
            resp.close()
        except Exception:
            pass
        return result

    def _request_urllib(self, method, url, data):
        """Make request using CPython urllib."""
        body = json.dumps(data).encode("utf-8") if data else None
        req = self._urllib.Request(url, data=body, method=method)
        if body:
            req.add_header("Content-Type", "application/json")
        with self._urllib.urlopen(req, timeout=self.config.timeout_s) as resp:
            raw = resp.read()
            return json.loads(raw.decode("utf-8"))

    def _request_requests(self, method, url, data):
        """Make request using requests library (if available)."""
        fn = getattr(self._requests, method.lower())
        resp = fn(url, json=data, timeout=self.config.timeout_s)
        return resp.json()

    def predict(self, input_data):
        """Send sensor data to the exocortex for a prediction.

        Args:
            input_data: List of sensor values or feature vector.

        Returns:
            Dict with prediction result, or None on failure.
        """
        payload = {
            "jsonrpc": "2.0",
            "method": "tasks/send",
            "params": {
                "task": {
                    "id": self.config.notebook_id,
                    "message": {
                        "role": "user",
                        "parts": [
                            {
                                "type": "data",
                                "data": {
                                    "action": "predict",
                                    "model": self.config.model,
                                    "input": input_data,
                                },
                            }
                        ],
                    },
                }
            },
        }
        return self._request("POST", "/api/a2a", payload)

    def train(self, model_type, data, labels):
        """Train a model on the exocortex.

        Args:
            model_type: Type of model to train (e.g. "micro_nn", "knn").
            data: List of training samples.
            labels: List of corresponding labels.

        Returns:
            Dict with training result, or None on failure.
        """
        payload = {
            "jsonrpc": "2.0",
            "method": "tasks/send",
            "params": {
                "task": {
                    "id": self.config.notebook_id,
                    "message": {
                        "role": "user",
                        "parts": [
                            {
                                "type": "data",
                                "data": {
                                    "action": "train",
                                    "model_type": model_type,
                                    "data": data,
                                    "labels": labels,
                                },
                            }
                        ],
                    },
                }
            },
        }
        return self._request("POST", "/api/a2a", payload)

    def remember(self, text, tags):
        """Store a memory in the exocortex.

        Args:
            text: Text content to remember.
            tags: List of tags for categorization.

        Returns:
            Dict with storage confirmation, or None on failure.
        """
        payload = {
            "jsonrpc": "2.0",
            "method": "tasks/send",
            "params": {
                "task": {
                    "id": self.config.notebook_id,
                    "message": {
                        "role": "user",
                        "parts": [
                            {
                                "type": "data",
                                "data": {
                                    "action": "remember",
                                    "text": text,
                                    "tags": tags,
                                },
                            }
                        ],
                    },
                }
            },
        }
        return self._request("POST", "/api/a2a", payload)

    def recall(self, query, top_k=5):
        """Recall memories from the exocortex.

        Args:
            query: Search query string.
            top_k: Maximum number of results to return.

        Returns:
            List of matching memories, or None on failure.
        """
        payload = {
            "jsonrpc": "2.0",
            "method": "tasks/send",
            "params": {
                "task": {
                    "id": self.config.notebook_id,
                    "message": {
                        "role": "user",
                        "parts": [
                            {
                                "type": "data",
                                "data": {
                                    "action": "recall",
                                    "query": query,
                                    "top_k": top_k,
                                },
                            }
                        ],
                    },
                }
            },
        }
        return self._request("POST", "/api/a2a", payload)

    def analyze(self, data):
        """Send data for analysis by the exocortex.

        Args:
            data: List of data points to analyze.

        Returns:
            Dict with analysis results, or None on failure.
        """
        payload = {
            "jsonrpc": "2.0",
            "method": "tasks/send",
            "params": {
                "task": {
                    "id": self.config.notebook_id,
                    "message": {
                        "role": "user",
                        "parts": [
                            {
                                "type": "data",
                                "data": {
                                    "action": "analyze",
                                    "data": data,
                                },
                            }
                        ],
                    },
                }
            },
        }
        return self._request("POST", "/api/a2a", payload)

    def embed(self, text):
        """Get embeddings for text from the exocortex.

        Args:
            text: Text to embed.

        Returns:
            Dict with embedding vector, or None on failure.
        """
        payload = {
            "jsonrpc": "2.0",
            "method": "tasks/send",
            "params": {
                "task": {
                    "id": self.config.notebook_id,
                    "message": {
                        "role": "user",
                        "parts": [
                            {
                                "type": "data",
                                "data": {
                                    "action": "embed",
                                    "text": text,
                                },
                            }
                        ],
                    },
                }
            },
        }
        return self._request("POST", "/api/a2a", payload)

    def health(self):
        """Check if the exocortex server is healthy.

        Returns:
            True if server responds, False otherwise.
        """
        result = self._request("GET", "/health")
        return result is not None
