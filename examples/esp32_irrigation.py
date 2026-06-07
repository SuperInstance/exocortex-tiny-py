"""ESP32 Irrigation Controller — waters plants using exocortex predictions.

Reads soil moisture, temperature, humidity, and light. Sends to the
exocortex for a watering decision. Executes and remembers.

Hardware:
- Soil moisture sensor on IO2
- Temperature/humidity on IO0/IO1
- Water solenoid on IO4
- Optional: light sensor on IO3

Usage (CircuitPython):
    Copy this file to ESP32 as code.py. Update base_url and notebook_id.
"""
from exocortex_tiny import ExocortexClient, SensorReader, ActuatorControl, ExocortexLoop, ExocortexConfig

config = ExocortexConfig(
    base_url="https://your-codespace.github.dev",
    notebook_id="notebook:irrigation_001",
    poll_interval_s=300,  # Check every 5 minutes
    model="micro_nn",
    debug=True,
)

client = ExocortexClient(config)
sensors = SensorReader()
actuators = ActuatorControl()


def decide(sensor_data, prediction):
    """Custom irrigation decision logic.

    Uses exocortex prediction when available, falls back to
    simple thresholds for autonomous operation.
    """
    soil = sensor_data.get("soil_moisture", 1.0)
    temp = sensor_data.get("temperature", 20.0)

    # If we got a prediction from the exocortex, use it
    if prediction:
        try:
            action_data = prediction
            if isinstance(prediction, dict):
                result = prediction.get("result", prediction)
                if isinstance(result, dict):
                    msg = result.get("message", result)
                    if isinstance(msg, dict):
                        parts = msg.get("parts", [])
                        for part in parts:
                            if isinstance(part, dict) and "data" in part:
                                action_data = part["data"]
                                break

            action = action_data.get("action", "skip")
            if action == "water":
                duration = action_data.get("amount_ml", 100) / 50.0
                actuators.water_on(duration)
                return {"action": "watered", "duration_s": duration}
        except Exception:
            pass

    # Fallback: simple threshold-based watering
    if soil < 0.3:
        # Dry soil — water for 2 seconds
        duration = 2.0
        if temp > 30:
            duration = 3.0  # More water in hot weather
        actuators.water_on(duration)
        return {"action": "water_fallback", "duration_s": duration, "reason": "low_soil"}

    return {"action": "skip", "soil_moisture": soil}


loop = ExocortexLoop(client, sensors, actuators, config, decide_fn=decide)

if __name__ == "__main__":
    print("=== ESP32 Irrigation Controller ===")
    print("Config: {} @ {}s interval".format(config.notebook_id, config.poll_interval_s))
    print("Sensors: {}".format("hardware" if sensors.is_hardware else "mock"))
    print("Starting loop... (Ctrl+C to stop)")
    loop.run()
