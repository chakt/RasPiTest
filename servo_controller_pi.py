# servo_controller_pi.py
import pigpio

class ServoControllerPi:
    """
    Raspberry Pi 4 + pigpio servo controller (2 channels).
    Safety:
      - soft limit by angle ranges
      - hard clamp by pulse width (us) to avoid extreme pulses
    """

    def __init__(
        self,
        pan_gpio: int = 18,
        tilt_gpio: int = 19,
        pan_safe=(20, 160),
        tilt_safe=(20, 160),
        min_us: int = 700,
        max_us: int = 2300,
        home=(90, 90),
    ):
        self.pi = pigpio.pi()
        if not self.pi.connected:
            raise RuntimeError(
                "pigpio daemon not running. Run:\n"
                "  sudo systemctl start pigpiod\n"
                "  systemctl status pigpiod"
            )

        self.pan_gpio = int(pan_gpio)
        self.tilt_gpio = int(tilt_gpio)

        self.pan_min, self.pan_max = map(int, pan_safe)
        self.tilt_min, self.tilt_max = map(int, tilt_safe)

        self.min_us = int(min_us)
        self.max_us = int(max_us)

        self.pan_angle = int(home[0])
        self.tilt_angle = int(home[1])

        # go home immediately
        self.set_pan_tilt(self.pan_angle, self.tilt_angle)

    @staticmethod
    def _clamp(v: int, lo: int, hi: int) -> int:
        return lo if v < lo else hi if v > hi else v

    def set_safe_ranges(self, pan_min: int, pan_max: int, tilt_min: int, tilt_max: int):
        self.pan_min, self.pan_max = int(pan_min), int(pan_max)
        self.tilt_min, self.tilt_max = int(tilt_min), int(tilt_max)
        # re-apply current to respect new limits
        self.set_pan_tilt(self.pan_angle, self.tilt_angle)

    def angle_to_pulse_us(self, angle: int) -> int:
        """
        Map 0..180 degrees to 500..2500 us (typical),
        then clamp to [min_us, max_us] for protection.
        """
        angle = self._clamp(int(angle), 0, 180)
        us = int(500 + (angle / 180.0) * 2000)
        us = self._clamp(us, self.min_us, self.max_us)
        return us

    def set_pan_tilt(self, pan: int, tilt: int):
        # soft limit clamp first
        pan = self._clamp(int(pan), self.pan_min, self.pan_max)
        tilt = self._clamp(int(tilt), self.tilt_min, self.tilt_max)

        self.pan_angle = pan
        self.tilt_angle = tilt

        self.pi.set_servo_pulsewidth(self.pan_gpio, self.angle_to_pulse_us(pan))
        self.pi.set_servo_pulsewidth(self.tilt_gpio, self.angle_to_pulse_us(tilt))

    def nudge(self, d_pan: int = 0, d_tilt: int = 0):
        self.set_pan_tilt(self.pan_angle + int(d_pan), self.tilt_angle + int(d_tilt))

    def home(self, pan: int = 90, tilt: int = 90):
        self.set_pan_tilt(pan, tilt)

    def stop_signals(self):
        # stop PWM pulses (servo will stop holding)
        self.pi.set_servo_pulsewidth(self.pan_gpio, 0)
        self.pi.set_servo_pulsewidth(self.tilt_gpio, 0)

    def close(self):
        try:
            self.stop_signals()
        finally:
            self.pi.stop()
