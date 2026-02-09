# servo_controller_mock.py
class ServoControllerMock:
    """
    Mock servo controller for PC development.
    Behaves like the real controller but does NOT touch hardware.
    """

    def __init__(
        self,
        pan_gpio=18,
        tilt_gpio=19,
        pan_safe=(20, 160),
        tilt_safe=(20, 160),
        home=(90, 90),
        **kwargs
    ):
        self.pan_gpio = pan_gpio
        self.tilt_gpio = tilt_gpio

        self.pan_min, self.pan_max = pan_safe
        self.tilt_min, self.tilt_max = tilt_safe

        self.pan_angle = home[0]
        self.tilt_angle = home[1]

        print("🧪 [MOCK] ServoControllerMock initialized")
        self._log_state()

    def _clamp(self, v, lo, hi):
        return lo if v < lo else hi if v > hi else v

    def set_pan_tilt(self, pan, tilt):
        pan = self._clamp(int(pan), self.pan_min, self.pan_max)
        tilt = self._clamp(int(tilt), self.tilt_min, self.tilt_max)

        self.pan_angle = pan
        self.tilt_angle = tilt
        self._log_state()

    def nudge(self, d_pan=0, d_tilt=0):
        self.set_pan_tilt(self.pan_angle + d_pan, self.tilt_angle + d_tilt)

    def home(self, pan=90, tilt=90):
        self.set_pan_tilt(pan, tilt)

    def close(self):
        print("🧪 [MOCK] ServoController closed")

    def _log_state(self):
        print(f"🧪 [MOCK] Pan={self.pan_angle}°, Tilt={self.tilt_angle}°")
