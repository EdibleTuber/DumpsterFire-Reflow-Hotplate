# pid.py
import utime

class PID:
    def __init__(self, kp, ki, kd, setpoint=0, output_limits=(0, 100), sample_time=1.0):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.setpoint = setpoint
        self.output_limits = output_limits
        self.sample_time = sample_time

        self._last_time = utime.ticks_ms()
        self._last_input = None
        self._integral = 0

    def compute(self, input_value):
        now = utime.ticks_ms()
        dt = utime.ticks_diff(now, self._last_time) / 1000.0

        if dt < self.sample_time:
            return None  # skip this cycle

        error = self.setpoint - input_value
        d_input = 0 if self._last_input is None else input_value - self._last_input

        self._integral += error * dt
        derivative = -d_input / dt if dt > 0 else 0

        output = (
            self.kp * error +
            self.ki * self._integral +
            self.kd * derivative
        )

        # Clamp output
        output = max(self.output_limits[0], min(output, self.output_limits[1]))

        # Save state
        self._last_input = input_value
        self._last_time = now

        return output

    def reset(self):
        self._last_input = None
        self._last_time = utime.ticks_ms()
        self._integral = 0
