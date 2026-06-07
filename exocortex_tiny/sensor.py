"""SensorReader — Hardware sensor abstraction for exocortex-tiny.

CircuitPython: reads from analogio/digitalio on ESP32.
CPython: returns mock data for development and testing.
Detection: tries `import board`, falls back to mock mode.
"""


class SensorReader:
    """Read environmental sensors with automatic hardware detection.

    In mock mode (CPython), returns realistic fake data for development.
    In hardware mode (CircuitPython), reads from actual GPIO pins.

    All readings return floats. All methods are safe to call — no exceptions.
    """

    def __init__(self):
        """Initialize sensor reader, detecting hardware availability."""
        self._hardware = False
        self._mock_values = {
            "temperature": 23.5,
            "humidity": 45.0,
            "soil_moisture": 0.35,
            "light": 512.0,
        }
        try:
            import board
            import analogio
            import digitalio
            self._board = board
            self._analogio = analogio
            self._digitalio = digitalio
            self._hardware = True
            self._init_pins()
        except (ImportError, NotImplementedError, AttributeError):
            self._hardware = False

    def _init_pins(self):
        """Initialize GPIO pins for sensor reading (CircuitPython only)."""
        try:
            # Common ESP32 pin assignments — customize per project
            self._temp_pin = self._analogio.AnalogIn(self._board.IO0)
            self._humidity_pin = self._analogio.AnalogIn(self._board.IO1)
            self._soil_pin = self._analogio.AnalogIn(self._board.IO2)
            self._light_pin = self._analogio.AnalogIn(self._board.IO3)
        except Exception:
            self._hardware = False

    def _read_analog(self, pin):
        """Read an analog pin and return a 0-1 normalized float.

        Args:
            pin: AnalogIn pin instance.

        Returns:
            Float between 0.0 and 1.0.
        """
        try:
            raw = pin.value
            return raw / 65535.0
        except Exception:
            return 0.0

    def read_temperature(self):
        """Read temperature in Celsius.

        Returns:
            Temperature as float (°C). Mock: 23.5°C.
        """
        if self._hardware:
            try:
                raw = self._read_analog(self._temp_pin)
                # Map 0-1 to -10°C to 50°C (typical NTC thermistor range)
                return raw * 60.0 - 10.0
            except Exception:
                return self._mock_values["temperature"]
        return self._mock_values["temperature"]

    def read_humidity(self):
        """Read relative humidity percentage.

        Returns:
            Humidity as float (0-100%). Mock: 45.0%.
        """
        if self._hardware:
            try:
                raw = self._read_analog(self._humidity_pin)
                return raw * 100.0
            except Exception:
                return self._mock_values["humidity"]
        return self._mock_values["humidity"]

    def read_soil_moisture(self):
        """Read soil moisture level.

        Returns:
            Moisture as float (0-1, where 1 = saturated). Mock: 0.35.
        """
        if self._hardware:
            try:
                raw = self._read_analog(self._soil_pin)
                return raw
            except Exception:
                return self._mock_values["soil_moisture"]
        return self._mock_values["soil_moisture"]

    def read_light(self):
        """Read ambient light level.

        Returns:
            Light level as float (0-1023, raw ADC). Mock: 512.0.
        """
        if self._hardware:
            try:
                raw = self._read_analog(self._light_pin)
                return raw * 1023.0
            except Exception:
                return self._mock_values["light"]
        return self._mock_values["light"]

    def read_all(self):
        """Read all sensors at once.

        Returns:
            Dict with all sensor readings:
            {"temperature": 23.5, "humidity": 45.0,
             "soil_moisture": 0.35, "light": 512.0}
        """
        return {
            "temperature": self.read_temperature(),
            "humidity": self.read_humidity(),
            "soil_moisture": self.read_soil_moisture(),
            "light": self.read_light(),
        }

    @property
    def is_hardware(self):
        """Whether real hardware sensors are connected."""
        return self._hardware
