"""ActuatorControl — Hardware actuator abstraction for exocortex-tiny.

CircuitPython: controls digitalio pins on ESP32.
CPython: prints actions for development and testing.
Detection: tries `import board`, falls back to mock mode.
"""


class ActuatorControl:
    """Control actuators with automatic hardware detection.

    In mock mode (CPython), prints actions and returns True.
    In hardware mode (CircuitPython), controls GPIO via digitalio.

    All methods return bool (True = success, False = failure).
    """

    def __init__(self):
        """Initialize actuator control, detecting hardware availability."""
        self._hardware = False
        self._relays = {}
        try:
            import board
            import digitalio
            self._board = board
            self._digitalio = digitalio
            self._hardware = True
            self._init_pins()
        except (ImportError, NotImplementedError, AttributeError):
            self._hardware = False

    def _init_pins(self):
        """Initialize GPIO pins for actuator control (CircuitPython only)."""
        try:
            self._water_pin = self._digitalio.DigitalInOut(self._board.IO4)
            self._water_pin.direction = self._digitalio.Direction.OUTPUT
            self._water_pin.value = False

            self._light_pin = self._digitalio.DigitalInOut(self._board.IO5)
            self._light_pin.direction = self._digitalio.Direction.OUTPUT
            self._light_pin.value = False
        except Exception:
            self._hardware = False

    def water_on(self, duration_s=None):
        """Turn on water valve/solenoid.

        Args:
            duration_s: Optional duration in seconds. If set, runs a blocking
                        delay then calls water_off() automatically.

        Returns:
            True if successful, False otherwise.
        """
        if self._hardware:
            try:
                self._water_pin.value = True
                if duration_s is not None:
                    import time
                    time.sleep(duration_s)
                    self.water_off()
                return True
            except Exception:
                return False
        else:
            msg = "[actuator] water ON"
            if duration_s:
                msg += " for {:.1f}s".format(duration_s)
            print(msg)
            if duration_s is not None:
                import time
                time.sleep(min(duration_s, 0.01))  # Don't actually wait in mock
            return True

    def water_off(self):
        """Turn off water valve/solenoid.

        Returns:
            True if successful, False otherwise.
        """
        if self._hardware:
            try:
                self._water_pin.value = False
                return True
            except Exception:
                return False
        else:
            print("[actuator] water OFF")
            return True

    def light_on(self):
        """Turn on grow light.

        Returns:
            True if successful, False otherwise.
        """
        if self._hardware:
            try:
                self._light_pin.value = True
                return True
            except Exception:
                return False
        else:
            print("[actuator] light ON")
            return True

    def light_off(self):
        """Turn off grow light.

        Returns:
            True if successful, False otherwise.
        """
        if self._hardware:
            try:
                self._light_pin.value = False
                return True
            except Exception:
                return False
        else:
            print("[actuator] light OFF")
            return True

    def relay_set(self, relay_id, state):
        """Set a generic relay on or off.

        Args:
            relay_id: Integer relay identifier (0-based).
            state: True to energize, False to de-energize.

        Returns:
            True if successful, False otherwise.
        """
        if self._hardware:
            try:
                if relay_id not in self._relays:
                    # Dynamically allocate relay pins as needed
                    pin_map = {
                        0: self._board.IO6,
                        1: self._board.IO7,
                        2: self._board.IO8,
                        3: self._board.IO9,
                    }
                    if relay_id in pin_map:
                        pin = self._digitalio.DigitalInOut(pin_map[relay_id])
                        pin.direction = self._digitalio.Direction.OUTPUT
                        self._relays[relay_id] = pin
                    else:
                        return False
                self._relays[relay_id].value = bool(state)
                return True
            except Exception:
                return False
        else:
            state_str = "ON" if state else "OFF"
            print("[actuator] relay {} {}".format(relay_id, state_str))
            return True

    @property
    def is_hardware(self):
        """Whether real hardware actuators are connected."""
        return self._hardware
