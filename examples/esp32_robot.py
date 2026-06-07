"""ESP32 Robot — simple robot with exocortex brain for navigation.

Uses the exocortex to make navigation decisions based on sensor input.
Demonstrates how an ESP32 can be a PLATO terminal for robotics.

Hardware (CircuitPython):
- Left motor: relay 0 (IO6)
- Right motor: relay 1 (IO7)
- Front distance sensor: IO0 (analog)
- Left bumper: IO1 (digital, optional)
- Right bumper: IO2 (digital, optional)

Usage (CircuitPython):
    Copy this file to ESP32 as code.py. Update base_url and notebook_id.
"""
from exocortex_tiny import ExocortexClient, SensorReader, ActuatorControl, ExocortexLoop, ExocortexConfig
import time


config = ExocortexConfig(
    base_url="https://your-codespace.github.dev",
    notebook_id="notebook:robot_001",
    poll_interval_s=1.0,  # Fast loop for robotics
    model="micro_nn",
    debug=True,
)

client = ExocortexClient(config)
sensors = SensorReader()
actuators = ActuatorControl()


class RobotMotor:
    """Simple differential drive motor control via relays."""

    def __init__(self, actuator_control):
        self.act = actuator_control

    def forward(self, duration_s=0.5):
        self.act.relay_set(0, True)   # Left motor on
        self.act.relay_set(1, True)   # Right motor on
        time.sleep(duration_s)
        self.stop()

    def backward(self, duration_s=0.5):
        self.act.relay_set(0, True)
        self.act.relay_set(1, True)
        time.sleep(duration_s)
        self.stop()

    def turn_left(self, duration_s=0.3):
        self.act.relay_set(0, False)  # Left motor off
        self.act.relay_set(1, True)   # Right motor on
        time.sleep(duration_s)
        self.stop()

    def turn_right(self, duration_s=0.3):
        self.act.relay_set(0, True)   # Left motor on
        self.act.relay_set(1, False)  # Right motor off
        time.sleep(duration_s)
        self.stop()

    def stop(self):
        self.act.relay_set(0, False)
        self.act.relay_set(1, False)


motor = RobotMotor(actuators)


def robot_decide(sensor_data, prediction):
    """Robot navigation decision function.

    Uses exocortex prediction for navigation, with obstacle
    avoidance fallback.
    """
    # Use light sensor reading as distance proxy (or actual distance sensor)
    distance = sensor_data.get("light", 512)
    temp = sensor_data.get("temperature", 20)

    # Try exocortex prediction first
    if prediction:
        try:
            action_data = prediction
            if isinstance(prediction, dict):
                result = prediction.get("result", prediction)
                if isinstance(result, dict):
                    msg = result.get("message", result)
                    if isinstance(msg, dict):
                        for part in msg.get("parts", []):
                            if isinstance(part, dict) and "data" in part:
                                action_data = part["data"]
                                break

            action = action_data.get("action", "forward")
            if action == "forward":
                motor.forward(0.5)
                return {"action": "forward"}
            elif action == "turn_left":
                motor.turn_left(0.3)
                return {"action": "turn_left"}
            elif action == "turn_right":
                motor.turn_right(0.3)
                return {"action": "turn_right"}
            elif action == "backward":
                motor.backward(0.5)
                return {"action": "backward"}
            elif action == "stop":
                motor.stop()
                return {"action": "stop"}
        except Exception:
            pass

    # Fallback: simple obstacle avoidance
    if distance < 200:
        # Obstacle ahead — turn away
        motor.turn_right(0.5)
        return {"action": "avoid_right", "distance": distance}
    elif distance < 400:
        # Getting close — slow turn
        motor.turn_left(0.2)
        return {"action": "cautious_left", "distance": distance}
    else:
        # Clear path — forward
        motor.forward(0.3)
        return {"action": "forward", "distance": distance}


if __name__ == "__main__":
    print("=== ESP32 Robot with Exocortex Brain ===")
    print("Config: {} @ {:.1f}s interval".format(config.notebook_id, config.poll_interval_s))
    print("Sensors: {}".format("hardware" if sensors.is_hardware else "mock"))
    print("Starting robot... (Ctrl+C to stop)")

    # Train the exocortex with some initial examples
    print("[robot] Training exocortex with initial examples...")
    training_data = [
        [500, 20],   # far, normal temp → forward
        [300, 20],   # medium → cautious
        [150, 20],   # close → avoid
        [500, 35],   # far, hot → forward (but note temp)
        [100, 20],   # very close → backward
    ]
    labels = ["forward", "turn_left", "turn_right", "forward", "backward"]
    client.train("micro_nn", training_data, labels)

    loop = ExocortexLoop(client, sensors, actuators, config, decide_fn=robot_decide)
    loop.run()
