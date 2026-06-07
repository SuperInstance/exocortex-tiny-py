"""Configuration for exocortex-tiny client."""

try:
    from dataclasses import dataclass, field, asdict
except ImportError:
    # CircuitPython fallback — minimal dataclass-like
    def dataclass(cls):
        return cls
    def field(default=None, **kw):
        return default
    def asdict(obj):
        return {k: v for k, v in obj.__dict__.items()}


@dataclass
class ExocortexConfig:
    """Configuration for connecting to an exocortex server.

    Attributes:
        base_url: Exocortex server URL (e.g. "https://codespace-xxx.github.dev")
        notebook_id: Unique identifier for this device/notebook
        poll_interval_s: Seconds between sense-think-act cycles (default 300 = 5 min)
        timeout_s: HTTP request timeout in seconds
        model: Model name to use for predictions (default "micro_nn")
        debug: Enable verbose debug logging
    """
    base_url: str = ""
    notebook_id: str = ""
    poll_interval_s: float = 300.0
    timeout_s: float = 10.0
    model: str = "micro_nn"
    debug: bool = False

    @classmethod
    def from_dict(cls, d):
        """Create config from a dictionary, ignoring unknown keys."""
        known = {
            "base_url", "notebook_id", "poll_interval_s",
            "timeout_s", "model", "debug",
        }
        filtered = {k: v for k, v in d.items() if k in known}
        return cls(**filtered)

    def to_dict(self):
        """Serialize config to a dictionary."""
        try:
            return asdict(self)
        except Exception:
            return {
                "base_url": self.base_url,
                "notebook_id": self.notebook_id,
                "poll_interval_s": self.poll_interval_s,
                "timeout_s": self.timeout_s,
                "model": self.model,
                "debug": self.debug,
            }
