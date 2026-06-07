"""ExocortexLoop — Main sense-think-act loop for exocortex-tiny.

Reads sensors, sends to exocortex, parses prediction, executes action,
remembers result. Runs forever with configurable poll interval.
Network errors don't crash — skip and retry next cycle.
"""

import time


class ExocortexLoop:
    """Sense-think-act loop connecting ESP32 sensors/actuators to the exocortex.

    The loop embodies the PLATO terminal model: the ESP32 is a thin client
    that senses, asks the exocortex what to do, and acts on the answer.

    Usage:
        loop = ExocortexLoop(client, sensors, actuators, config)
        loop.run()  # Runs forever

    Or with custom decision logic:
        def my_decide(sensor_data, prediction):
            # Custom logic here
            return {"action": "done"}
        loop = ExocortexLoop(..., decide_fn=my_decide)
        loop.run()
    """

    def __init__(self, client, sensors, actuators, config, decide_fn=None):
        """Initialize the sense-think-act loop.

        Args:
            client: ExocortexClient instance.
            sensors: SensorReader instance.
            actuators: ActuatorControl instance.
            config: ExocortexConfig instance.
            decide_fn: Optional callback(sensor_data, prediction) -> dict
                       Override the default predict→act logic.
        """
        self.client = client
        self.sensors = sensors
        self.actuators = actuators
        self.config = config
        self.decide_fn = decide_fn
        self._step_count = 0
        self._last_error = None
        self._running = False

    def step(self):
        """Execute one sense-think-act cycle.

        1. Read all sensors
        2. Send sensor data to exocortex for prediction
        3. Execute decision (custom or default)
        4. Remember the result
        5. Return a summary dict

        Returns:
            Dict with step summary:
            {"step": N, "sensors": {...}, "action": {...},
             "remembered": bool, "error": None|str}
        """
        self._step_count += 1
        summary = {
            "step": self._step_count,
            "sensors": None,
            "action": None,
            "remembered": False,
            "error": None,
        }

        # 1. SENSE — read sensors
        try:
            sensor_data = self.sensors.read_all()
            summary["sensors"] = sensor_data
            if self.config.debug:
                print("[loop] Sensors: {}".format(sensor_data))
        except Exception as e:
            summary["error"] = "sensor_read_failed: {}".format(e)
            self._last_error = summary["error"]
            if self.config.debug:
                print("[loop] Sensor error: {}".format(e))
            return summary

        # 2. THINK — send to exocortex for prediction
        prediction = None
        try:
            input_data = [
                sensor_data.get("temperature", 0),
                sensor_data.get("humidity", 0),
                sensor_data.get("soil_moisture", 0),
                sensor_data.get("light", 0),
            ]
            prediction = self.client.predict(input_data)
            if self.config.debug:
                print("[loop] Prediction: {}".format(prediction))
        except Exception as e:
            summary["error"] = "predict_failed: {}".format(e)
            self._last_error = summary["error"]
            if self.config.debug:
                print("[loop] Predict error: {}".format(e))

        # 3. ACT — execute decision
        try:
            if self.decide_fn:
                action_result = self.decide_fn(sensor_data, prediction)
            else:
                action_result = self._default_decide(sensor_data, prediction)
            summary["action"] = action_result
            if self.config.debug:
                print("[loop] Action: {}".format(action_result))
        except Exception as e:
            summary["error"] = "act_failed: {}".format(e)
            self._last_error = summary["error"]
            if self.config.debug:
                print("[loop] Act error: {}".format(e))

        # 4. REMEMBER — store result in exocortex
        try:
            memory_text = "step {} sensors={} action={}".format(
                self._step_count, sensor_data, summary.get("action")
            )
            tags = ["auto", "step-{}".format(self._step_count)]
            result = self.client.remember(memory_text, tags)
            summary["remembered"] = result is not None
        except Exception as e:
            if self.config.debug:
                print("[loop] Remember error: {}".format(e))

        self._last_error = None
        return summary

    def _default_decide(self, sensor_data, prediction):
        """Default decision logic when no custom function is provided.

        Interprets the prediction response to control actuators.

        Args:
            sensor_data: Dict of current sensor readings.
            prediction: Dict from exocortex predict call (may be None).

        Returns:
            Dict describing the action taken.
        """
        if prediction is None:
            # No prediction available — use simple threshold fallback
            soil = sensor_data.get("soil_moisture", 1.0)
            if soil < 0.3:
                self.actuators.water_on(2.0)
                return {"action": "water_fallback", "reason": "low_soil", "duration_s": 2.0}
            return {"action": "skip", "reason": "no_prediction"}

        # Try to extract action from prediction response
        try:
            # Navigate nested A2A response structure
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
                amount = action_data.get("amount_ml", 100)
                duration = amount / 50.0  # 50ml/s flow rate
                self.actuators.water_on(duration)
                return {"action": "water", "duration_s": duration, "amount_ml": amount}
            elif action == "light_on":
                self.actuators.light_on()
                return {"action": "light_on"}
            elif action == "light_off":
                self.actuators.light_off()
                return {"action": "light_off"}
            else:
                return {"action": "skip"}
        except Exception:
            return {"action": "skip", "reason": "parse_error"}

    def run(self):
        """Run the sense-think-act loop forever.

        Cycles every config.poll_interval_s seconds.
        Network errors are caught and logged — the loop never crashes.
        Press Ctrl+C to stop (KeyboardInterrupt).
        """
        self._running = True
        if self.config.debug:
            print("[loop] Starting exocortex loop (interval={}s)".format(
                self.config.poll_interval_s))

        while self._running:
            try:
                self.step()
            except KeyboardInterrupt:
                if self.config.debug:
                    print("[loop] Stopped by user")
                break
            except Exception as e:
                if self.config.debug:
                    print("[loop] Unexpected error: {}".format(e))
                self._last_error = str(e)

            try:
                time.sleep(self.config.poll_interval_s)
            except KeyboardInterrupt:
                if self.config.debug:
                    print("[loop] Stopped by user")
                break

        self._running = False

    def stop(self):
        """Signal the loop to stop after the current cycle."""
        self._running = False

    @property
    def step_count(self):
        """Number of completed steps."""
        return self._step_count

    @property
    def last_error(self):
        """Last error message, or None if healthy."""
        return self._last_error

    @property
    def is_running(self):
        """Whether the loop is currently running."""
        return self._running
