from machine import Pin
import utime

class RotaryEncoder:
    def __init__(self, clk=10, dt=11, button=12, callback=None):
        self.clk = Pin(clk, Pin.IN, Pin.PULL_UP)
        self.dt = Pin(dt, Pin.IN, Pin.PULL_UP)
        self.button = Pin(button, Pin.IN, Pin.PULL_UP) if button is not None else None

        self.last_clk = self.clk.value()
        self.position = 0
        self.callback = callback
        self.last_button = 1
        self.button_pressed = False
        self.last_update = utime.ticks_ms()

    def update(self):
        now = utime.ticks_ms()
        if utime.ticks_diff(now, self.last_update) < 2:
            return  # debounce time ~2ms
        self.last_update = now

        # Read pin states
        current_clk = self.clk.value()
        current_dt = self.dt.value()

        # Rotation detection on falling edge of clk
        if current_clk == 0 and self.last_clk == 1:
            if current_dt == 1:
                self.position += 1
                direction = 1  # clockwise
            else:
                self.position -= 1
                direction = -1  # counterclockwise
            if self.callback:
                self.callback(direction)

        self.last_clk = current_clk

        # Button press detection with simple debounce
        if self.button:
            current_button = self.button.value()
            if self.last_button == 1 and current_button == 0:
                self.button_pressed = True
            self.last_button = current_button

    def get_position(self):
        return self.position

    def was_pressed(self):
        if self.button_pressed:
            self.button_pressed = False
            return True
        return False
