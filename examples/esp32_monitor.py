"""ESP32 Environmental Monitor — logs and detects anomalies.

Reads environmental sensors, sends data to exocortex for analysis
and anomaly detection. Alerts on unusual readings.

Hardware:
- Temperature/humidity sensor on IO0/IO1
- Light sensor on IO3
- Optional: soil moisture on IO2

Usage (CircuitPython):
    Copy this file to ESP32 as code.py. Update base_url and notebook_id.
"""
from exocortex_tiny import ExocortexClient, SensorReader, ExocortexConfig
import time


config = ExocortexConfig(
    base_url="https://your-codespace.github.dev",
    notebook_id="notebook:env_monitor_001",
    poll_interval_s=60,  # Check every minute for monitoring
    model="micro_nn",
    debug=True,
)

client = ExocortexClient(config)
sensors = SensorReader()

# Anomaly thresholds — adjust for your environment
THRESHOLDS = {
    "temperature": {"min": 5.0, "max": 40.0},
    "humidity": {"min": 10.0, "max": 90.0},
    "soil_moisture": {"min": 0.05, "max": 0.95},
    "light": {"min": 0.0, "max": 1023.0},
}

HISTORY_SIZE = 10
history = []


def check_thresholds(sensor_data):
    """Check if any reading is outside normal thresholds."""
    anomalies = []
    for key, limits in THRESHOLDS.items():
        value = sensor_data.get(key)
        if value is not None:
            if value < limits["min"]:
                anomalies.append("{}={} (below {})".format(key, value, limits["min"]))
            elif value > limits["max"]:
                anomalies.append("{}={} (above {})".format(key, value, limits["max"]))
    return anomalies


def detect_trend(history, key, window=5):
    """Detect if a sensor value is trending up or down."""
    if len(history) < window:
        return "stable"
    recent = [h.get(key, 0) for h in history[-window:]]
    diffs = [recent[i+1] - recent[i] for i in range(len(recent) - 1)]
    avg_diff = sum(diffs) / len(diffs)
    if avg_diff > 0.5:
        return "rising"
    elif avg_diff < -0.5:
        return "falling"
    return "stable"


def monitor_step():
    """Execute one monitoring cycle."""
    # Read sensors
    data = sensors.read_all()
    print("[monitor] {}".format(data))

    # Store in local history
    history.append(data)
    if len(history) > HISTORY_SIZE:
        history.pop(0)

    # Check thresholds
    anomalies = check_thresholds(data)
    if anomalies:
        print("[monitor] ANOMALY: {}".format(", ".join(anomalies)))
        # Remember anomaly in exocortex
        client.remember(
            "Anomaly detected: {}".format("; ".join(anomalies)),
            ["anomaly", "monitor", "alert"]
        )

    # Check trends
    temp_trend = detect_trend(history, "temperature")
    humidity_trend = detect_trend(history, "humidity")
    if temp_trend != "stable" or humidity_trend != "stable":
        print("[monitor] Trends: temp={}, humidity={}".format(temp_trend, humidity_trend))

    # Send to exocortex for analysis
    analysis = client.analyze(list(history))
    if analysis:
        print("[monitor] Analysis received from exocortex")

    # Embed the reading for future recall
    reading_text = "T={:.1f}C H={:.1f}% soil={:.2f} light={:.0f}".format(
        data["temperature"], data["humidity"],
        data["soil_moisture"], data["light"]
    )
    client.embed(reading_text)

    return data


if __name__ == "__main__":
    print("=== ESP32 Environmental Monitor ===")
    print("Config: {} @ {}s interval".format(config.notebook_id, config.poll_interval_s))
    print("Sensors: {}".format("hardware" if sensors.is_hardware else "mock"))
    print("Starting monitor... (Ctrl+C to stop)")

    while True:
        try:
            monitor_step()
        except KeyboardInterrupt:
            print("\n[monitor] Stopped")
            break
        except Exception as e:
            print("[monitor] Error: {}".format(e))

        time.sleep(config.poll_interval_s)
